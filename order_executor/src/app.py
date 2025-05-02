import os
import sys
import time
import grpc
import threading
import json
from concurrent import futures

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
executor_grpc_path     = os.path.abspath(os.path.join(FILE, "../../../utils/pb/order_executor"))
order_queue_grpc_path  = os.path.abspath(os.path.join(FILE, "../../../utils/pb/order_queue"))
books_db_grpc_path     = os.path.abspath(os.path.join(FILE, "../../../utils/pb/books_database"))

# make sure proto folders are on the path
sys.path.insert(0, executor_grpc_path)
sys.path.insert(0, order_queue_grpc_path)
sys.path.insert(0, books_db_grpc_path)

import order_executor_pb2      as executor_pb2
import order_executor_pb2_grpc as executor_pb2_grpc
import order_queue_pb2         as queue_pb
import order_queue_pb2_grpc    as queue_grpc
import books_database_pb2      as book_pb
import books_database_pb2_grpc as book_grpc

from google.protobuf.empty_pb2 import Empty

def parse_int_list(env_value):
    return [int(x.strip()) for x in env_value.split(",") if x.strip()]



class OrderExecutorServicer(executor_pb2_grpc.OrderExecutorServicer):
    """
    Implements the Bully RPC endpoints for:
      - Election
      - Coordinator
      - Heartbeat
      - HealthCheck
    """
    def __init__(self, main_service):
        self.main_service = main_service

    def Election(self, request, context):
        cid = request.candidate_id
        me  = self.main_service.my_id
        if me > cid:
            print(f"[Executor {me}] Received ELECTION from {cid}; I'm bigger → ok, starting new election")
            threading.Thread(target=self.main_service.start_election, daemon=True).start()
            return executor_pb2.ElectionResponse(ok=True)
        else:
            print(f"[Executor {me}] Received ELECTION from {cid}; I'm smaller → ok=false")
            return executor_pb2.ElectionResponse(ok=False)

    def Coordinator(self, request, context):
        new_leader = request.coordinator_id
        self.main_service.leader_id = new_leader
        if self.main_service.my_id != new_leader:
            print(f"[Executor {self.main_service.my_id}] Acknowledging new leader → {new_leader}")
        else:
            print(f"[Executor {new_leader}] I am confirmed leader")
        return Empty()

    def Heartbeat(self, request, context):
        return executor_pb2.HeartbeatResponse(
            alive=True,
            leader_status=f"Leader={self.main_service.leader_id}"
        )

    def HealthCheck(self, request, context):
        return executor_pb2.HealthResponse(status="OK")



class ExecutorService:
    def __init__(self, instance_id, all_ids_str, queue_addr):
        # parse IDs
        self.my_id    = int(instance_id)
        self.all_ids  = parse_int_list(all_ids_str)
        if self.my_id not in self.all_ids:
            self.all_ids.append(self.my_id)
        self.max_id   = max(self.all_ids)

        # queue stub
        self.queue_addr = queue_addr
        qch = grpc.insecure_channel(self.queue_addr)
        self.queue_stub = queue_grpc.OrderQueueStub(qch)

        # books‐db stub (always talk to primary)
        db_ch = grpc.insecure_channel("books_primary:50055")
        self.db_stub = book_grpc.BooksDatabaseStub(db_ch)

        # bully state
        self.leader_id   = -1
        self.in_election = False
        self.lock        = threading.Lock()

    def run_server(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        servicer = OrderExecutorServicer(self)
        executor_pb2_grpc.add_OrderExecutorServicer_to_server(servicer, server)
        server.add_insecure_port("[::]:50056")
        server.start()
        print(f"[Executor {self.my_id}] Server up on 50056")

        # give everyone a moment to come up
        print(f"[Executor {self.my_id}] Sleeping 5s before election…")
        time.sleep(5)
        if self.leader_id == -1:
            threading.Thread(target=self.start_election, daemon=True).start()

        # leader duties & liveness checks
        threading.Thread(target=self.poll_queue_as_leader, daemon=True).start()
        threading.Thread(target=self.check_leader_liveness, daemon=True).start()

        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            server.stop(0)
            print(f"[Executor {self.my_id}] Shutdown")

    # ──────────────────────────────────────────────────────────────────────────

    def start_election(self):
        with self.lock:
            if self.in_election:
                return
            self.in_election = True

        print(f"[Executor {self.my_id}] ⇒ Starting election…")
        higher = [pid for pid in self.all_ids if pid > self.my_id]
        got_ok = False

        for hid in higher:
            if self.try_election_call(hid):
                got_ok = True
                print(f"[Executor {self.my_id}] → {hid} will handle leadership")

        if not got_ok:
            # no one above responded → I win
            self.leader_id = self.my_id
            print(f"[Executor {self.my_id}] ⇒ I am the new leader")
            self.announce_coordinator()
        else:
            print(f"[Executor {self.my_id}] ⇒ Waiting for coordinator announcement")

        with self.lock:
            self.in_election = False

    def try_election_call(self, hid, retries=3, delay=2):
        for i in range(retries):
            try:
                ch   = grpc.insecure_channel(f"order_executor{hid}:50056")
                stub = executor_pb2_grpc.OrderExecutorStub(ch)
                resp = stub.Election(executor_pb2.ElectionRequest(candidate_id=self.my_id),
                                     timeout=2.0)
                return resp.ok
            except Exception as e:
                print(f"[Executor {self.my_id}] ELECTION→{hid} failed ({i+1}/{retries}): {e}")
                time.sleep(delay)
        return False

    def announce_coordinator(self):
        for pid in self.all_ids:
            if pid == self.my_id:
                continue
            self.try_coordinator_call(pid)

    def try_coordinator_call(self, pid, retries=3, delay=2):
        for i in range(retries):
            try:
                ch   = grpc.insecure_channel(f"order_executor{pid}:50056")
                stub = executor_pb2_grpc.OrderExecutorStub(ch)
                stub.Coordinator(executor_pb2.CoordinatorRequest(coordinator_id=self.my_id),
                                 timeout=2.0)
                return
            except Exception as e:
                print(f"[Executor {self.my_id}] COORD→{pid} failed ({i+1}/{retries}): {e}")
                time.sleep(delay)

    # ──────────────────────────────────────────────────────────────────────────

    def poll_queue_as_leader(self):
        while True:
            if self.leader_id == self.my_id:
                try:
                    req  = queue_pb.OrderDequeueRequest(executor_id=str(self.my_id))
                    resp = self.queue_stub.Dequeue(req, timeout=5.0)
                    if not resp.success:
                        print(f"[Leader {self.my_id}] Queue empty → retrying in 5s")
                        time.sleep(5)
                        continue

                    # got an order: decode and update stock on primary
                    data = json.loads(resp.order_data)
                    items = data.get("items", [])
                    for it in items:
                        title = it.get("name") or it.get("title")
                        qty   = it.get("quantity", 1)

                        # 1) read
                        r = self.db_stub.Read(book_pb.ReadRequest(title=title))
                        if r.stock >= qty:
                            new_stock = r.stock - qty
                            w = self.db_stub.Write(book_pb.WriteRequest(
                                title=title,
                                new_stock=new_stock
                            ))
                            if w.success:
                                print(f"[Leader {self.my_id}] {title}: {r.stock}→{new_stock}")
                            else:
                                print(f"[Leader {self.my_id}] ERROR writing {title}")
                        else:
                            print(f"[Leader {self.my_id}] INSufficient stock {title}: have={r.stock}, need={qty}")

                    # simulate execution time
                    time.sleep(2)

                except Exception as e:
                    print(f"[Leader {self.my_id}] Dequeue/DB error: {e}")
                    time.sleep(5)
            else:
                time.sleep(5)

    def check_leader_liveness(self):
        while True:
            if self.leader_id == -1:
                self.start_election()
            elif self.leader_id != self.my_id:
                try:
                    ch   = grpc.insecure_channel(f"order_executor{self.leader_id}:50056")
                    stub = executor_pb2_grpc.OrderExecutorStub(ch)
                    stub.Heartbeat(executor_pb2.HeartbeatRequest(), timeout=3.0)
                except Exception:
                    print(f"[Executor {self.my_id}] Leader {self.leader_id} down → restarting election")
                    self.start_election()
            time.sleep(10)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--instance_id",   required=True)
    p.add_argument("--executor_ids",  required=True)
    p.add_argument("--order_queue_addr", default="order_queue:50054")
    args = p.parse_args()

    svc = ExecutorService(args.instance_id, args.executor_ids, args.order_queue_addr)
    svc.run_server()

if __name__ == "__main__":
    main()
