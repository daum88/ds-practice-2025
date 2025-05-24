import os
import sys
import time
import grpc
import threading
import json
from concurrent import futures
from google.protobuf.empty_pb2 import Empty

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
executor_pb_path   = os.path.abspath(os.path.join(FILE, "../../../utils/pb/order_executor"))
queue_pb_path      = os.path.abspath(os.path.join(FILE, "../../../utils/pb/order_queue"))
payment_pb_path    = os.path.abspath(os.path.join(FILE, "../../../utils/pb/payment"))
booksdb_pb_path    = os.path.abspath(os.path.join(FILE, "../../../utils/pb/books_database"))
for p in (executor_pb_path, queue_pb_path, payment_pb_path, booksdb_pb_path):
    sys.path.insert(0, p)

import order_executor_pb2      as executor_pb2
import order_executor_pb2_grpc as executor_grpc
import order_queue_pb2         as queue_pb
import order_queue_pb2_grpc    as queue_grpc
import payment_pb2             as payment_pb
import payment_pb2_grpc        as payment_grpc
import books_database_pb2      as books_pb
import books_database_pb2_grpc as books_grpc



def parse_int_list(env_value):
    return [int(x.strip()) for x in env_value.split(",") if x.strip()]

class OrderExecutorServicer(executor_grpc.OrderExecutorServicer):
    def __init__(self, svc):
        self.svc = svc

    def Election(self, req, ctx):
        return self.svc.handle_election(req)

    def Coordinator(self, req, ctx):
        return self.svc.handle_coordinator(req)

    def Heartbeat(self, req, ctx):
        return self.svc.handle_heartbeat(req)

    def HealthCheck(self, req, ctx):
        return executor_pb2.HealthResponse(status="OK")

class ExecutorService:
    def __init__(self, instance_id, executor_ids, queue_addr):
        self.my_id    = int(instance_id)
        self.all_ids  = parse_int_list(executor_ids)
        if self.my_id not in self.all_ids:
            self.all_ids.append(self.my_id)
        self.leader_id   = -1
        self.in_election = False
        self.lock        = threading.Lock()

        # queue stub
        self.queue   = queue_grpc.OrderQueueStub(grpc.insecure_channel(queue_addr))
        # payment stub
        self.payment = payment_grpc.PaymentServiceStub(grpc.insecure_channel("payment:50055"))
        # books-db stub
        self.db      = books_grpc.BooksDatabaseStub(grpc.insecure_channel("books_primary:50055"))

    #  gRPC handlers 
    def handle_election(self, req):
        cid, me = req.candidate_id, self.my_id
        if me > cid:
            threading.Thread(target=self.start_election, daemon=True).start()
            return executor_pb2.ElectionResponse(ok=True)
        else:
            return executor_pb2.ElectionResponse(ok=False)

    def handle_coordinator(self, req):
        self.leader_id = req.coordinator_id
        return Empty()

    def handle_heartbeat(self, req):
        return executor_pb2.HeartbeatResponse(
            alive=True,
            leader_status=f"Leader={self.leader_id}"
        )

    # run everything 
    def run(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        executor_grpc.add_OrderExecutorServicer_to_server(
            OrderExecutorServicer(self), server
        )
        server.add_insecure_port("[::]:50056")
        server.start()

        # let all executors spin up before electing
        time.sleep(5)
        threading.Thread(target=self.start_election, daemon=True).start()
        threading.Thread(target=self.poll_loop,      daemon=True).start()
        threading.Thread(target=self.liveness_loop, daemon=True).start()
        server.wait_for_termination()

    # Bully election 
    def start_election(self):
        with self.lock:
            if self.in_election:
                return
            self.in_election = True

        higher = [i for i in self.all_ids if i > self.my_id]
        got_ok = False
        for hid in higher:
            try:
                stub = executor_grpc.OrderExecutorStub(
                    grpc.insecure_channel(f"order_executor{hid}:50056"))
                if stub.Election(
                    executor_pb2.ElectionRequest(candidate_id=self.my_id),
                    timeout=2
                ).ok:
                    got_ok = True
            except:
                pass

        if not got_ok:
            self.leader_id = self.my_id
            for pid in self.all_ids:
                if pid == self.my_id:
                    continue
                try:
                    stub = executor_grpc.OrderExecutiveStub(
                        grpc.insecure_channel(f"order_executor{pid}:50056"))
                    stub.Coordinator(
                        executor_pb2.CoordinatorRequest(coordinator_id=self.my_id),
                        timeout=2
                    )
                except:
                    pass

        with self.lock:
            self.in_election = False

    # Leader polling & 2PC 
    def poll_loop(self):
        while True:
            if self.leader_id == self.my_id:
                try:
                    # 1) dequeue
                    resp = self.queue.Dequeue(
                        queue_pb.OrderDequeueRequest(executor_id=str(self.my_id)),
                        timeout=5
                    )
                    if not resp.success:
                        time.sleep(5)
                        continue

                    order_id = resp.order_id
                    data     = json.loads(resp.order_data)
                    items    = data.get("items", [])

                    print(f"[Leader] Dequeued {order_id}")

                    # PHASE 1: prepare
                    #  a) payment
                    pay_amount = sum(it.get("quantity", 1) * 10 for it in items)
                    pay_req = payment_pb.PreparePaymentRequest(
                        id=order_id,
                        user_name=data["user"]["name"],
                        user_contact=data["user"]["contact"],
                        amount=pay_amount
                    )
                    pay_resp = self.payment.PreparePayment(pay_req)
                    print(f"[Leader] Payment Prepare → ready={pay_resp.ready}")

                    #  b) database check stock
                    db_ok = True
                    for it in items:
                        cmp = self.db.CompareStock(
                            books_pb.CompareRequest(
                                title=it["name"],
                                threshold=it["quantity"]
                            )
                        )
                        print(f"[Leader] DB Compare {it['name']} ≥{it['quantity']}? {cmp.enough}")
                        if not cmp.enough:
                            db_ok = False

                    all_ready = pay_resp.ready and db_ok

                    # PHASE 2: commit or abort
                    #  a) payment finalize
                    fin_req = payment_pb.FinalizePaymentRequest(
                        id=order_id,
                        abort=(not all_ready)
                    )
                    self.payment.FinalizePayment(fin_req)
                    print(f"[Leader] Payment Finalize abort={(not all_ready)}")

                    #  b) if commit, update stock
                    if all_ready:
                        for it in items:
                            dec = self.db.DecrementStock(
                                books_pb.DecrementRequest(
                                    title=it["name"],
                                    amount=it["quantity"]
                                )
                            )
                            print(f"[Leader] DB Decrement {it['name']} → success={dec.success}, stock={dec.stock}")
                        print(f"[Leader] Order {order_id} committed")
                    else:
                        print(f"[Leader] Order {order_id} aborted (no DB change)")

                except Exception as e:
                    print(f"[Leader] error: {e}")
                finally:
                    time.sleep(2)
            else:
                time.sleep(5)


    def liveness_loop(self):
        while True:
            if self.leader_id > 0 and self.leader_id != self.my_id:
                try:
                    stub = executor_grpc.OrderExecutorStub(
                        grpc.insecure_channel(f"order_executor{self.leader_id}:50056"))
                    stub.Heartbeat(Empty(), timeout=3)
                except:
                    self.start_election()
            time.sleep(10)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--instance_id",  required=True)
    p.add_argument("--executor_ids", required=True)
    p.add_argument("--order_queue_addr", default="order_queue:50054")
    args = p.parse_args()

    ExecutorService(
        args.instance_id,
        args.executor_ids,
        args.order_queue_addr
    ).run()
