import os
import sys
import time
import grpc
import threading
from concurrent import futures

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
executor_grpc_path = os.path.abspath(os.path.join(FILE, "../../../utils/pb/order_executor"))
order_queue_grpc_path = os.path.abspath(os.path.join(FILE, "../../../utils/pb/order_queue"))
sys.path.insert(0, executor_grpc_path)
sys.path.insert(0, order_queue_grpc_path)

import order_executor_pb2 as executor_pb2
import order_executor_pb2_grpc as executor_pb2_grpc
import order_queue_pb2 as queue_pb
import order_queue_pb2_grpc as queue_grpc

from google.protobuf.empty_pb2 import Empty

def parse_int_list(env_value):
    return [int(x.strip()) for x in env_value.split(",") if x.strip()]

# ----------------------------------------------------------------
# Service Implementation
# ----------------------------------------------------------------
class OrderExecutorServicer(executor_pb2_grpc.OrderExecutorServicer):
    """
    Implements the Bully RPC endpoints for other executors to call:
      - Election
      - Coordinator
      - Heartbeat
    Also includes a HealthCheck method if needed.
    """

    def __init__(self, main_service):
        self.main_service = main_service

    # Bully: Election
    def Election(self, request, context):
        candidate_id = request.candidate_id
        my_id = self.main_service.my_id
        if my_id > candidate_id:
            print(f"[Executor {my_id}] Received ELECTION from {candidate_id}; I'm bigger => ok=true => I'll start an election.")
            threading.Thread(target=self.main_service.start_election, daemon=True).start()
            return executor_pb2.ElectionResponse(ok=True)
        else:
            print(f"[Executor {my_id}] Received ELECTION from {candidate_id}; I'm smaller => ok=false.")
            return executor_pb2.ElectionResponse(ok=False)

    # Bully: Coordinator
    def Coordinator(self, request, context):
        coord_id = request.coordinator_id
        self.main_service.leader_id = coord_id
        if self.main_service.my_id != coord_id:
            print(f"[Executor {self.main_service.my_id}] Acknowledging new leader => {coord_id}")
        else:
            print(f"[Executor {coord_id}] I am confirmed leader.")
        return Empty()

    # Bully: Heartbeat
    def Heartbeat(self, request, context):
        return executor_pb2.HeartbeatResponse(
            alive=True,
            leader_status=f"Leader is {self.main_service.leader_id}"
        )

    # Example: HealthCheck
    def HealthCheck(self, request, context):
        return executor_pb2.HealthResponse(status="OK from Executor")


# ----------------------------------------------------------------
# Main Bully Executor
# ----------------------------------------------------------------
class ExecutorService:
    def __init__(self, instance_id, all_ids_str, queue_addr):
        """
        :param instance_id: e.g. "2" (string). We'll parse it as int.
        :param all_ids_str: e.g. "1,2,3"
        :param queue_addr: e.g. "order_queue:50054"
        """
        self.my_id = int(instance_id)
        self.all_ids = parse_int_list(all_ids_str)
        if self.my_id not in self.all_ids:
            self.all_ids.append(self.my_id)
        self.max_id = max(self.all_ids)

        self.queue_addr = queue_addr
        self.leader_id = -1
        self.in_election = False
        self.lock = threading.Lock()

        # Connect to order queue
        channel = grpc.insecure_channel(self.queue_addr)
        self.queue_stub = queue_grpc.OrderQueueStub(channel)

    def run_server(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        # Use OrderExecutorServicer
        servicer = OrderExecutorServicer(self)
        executor_pb2_grpc.add_OrderExecutorServicer_to_server(servicer, server)

        # Start listening on 50056
        server.add_insecure_port("[::]:50056")
        server.start()
        print(f"[Executor {self.my_id}] Bully server started on port 50056.")

        print(f"[Executor {self.my_id}] Waiting 5s to allow others to start...")
        time.sleep(5)

        if self.leader_id == -1:
            threading.Thread(target=self.start_election, daemon=True).start()

        threading.Thread(target=self.poll_queue_as_leader, daemon=True).start()
        threading.Thread(target=self.check_leader_liveness, daemon=True).start()

        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            server.stop(0)
            print(f"[Executor {self.my_id}] Shutting down...")

    # ----------------------------------------------------------------
    # Bully logic
    # ----------------------------------------------------------------
    def start_election(self):
        with self.lock:
            if self.in_election:
                return
            self.in_election = True

        print(f"[Executor {self.my_id}] Starting election...")
        higher_ids = [pid for pid in self.all_ids if pid > self.my_id]
        got_ok = False
        for hid in higher_ids:
            if self.try_election_call(hid):
                got_ok = True
                print(f"[Executor {self.my_id}] ID={hid} responded ok => might become leader.")

        if not got_ok:
            # I'm the biggest among reachable => I'm the leader
            self.leader_id = self.my_id
            print(f"[Executor {self.my_id}] I am now the leader (no bigger ID responded).")
            self.announce_coordinator()
        else:
            print(f"[Executor {self.my_id}] Wait for new leader's Coordinator message...")

        with self.lock:
            self.in_election = False

    def try_election_call(self, hid, retries=3, delay=2):
        for attempt in range(retries):
            try:
                channel = grpc.insecure_channel(f"order_executor{hid}:50056")
                stub = executor_pb2_grpc.OrderExecutorStub(channel)
                resp = stub.Election(executor_pb2.ElectionRequest(candidate_id=self.my_id))
                return resp.ok
            except Exception as e:
                print(f"[Executor {self.my_id}] Can't contact {hid} (attempt {attempt+1}/{retries}): {e}")
                time.sleep(delay)
        return False

    def announce_coordinator(self):
        for pid in self.all_ids:
            if pid == self.my_id:
                continue
            self.try_coordinator_call(pid)

    def try_coordinator_call(self, pid, retries=3, delay=2):
        for attempt in range(retries):
            try:
                channel = grpc.insecure_channel(f"order_executor{pid}:50056")
                stub = executor_pb2_grpc.OrderExecutorStub(channel)
                stub.Coordinator(executor_pb2.CoordinatorRequest(coordinator_id=self.my_id))
                return
            except Exception as e:
                print(f"[Executor {self.my_id}] Can't send Coordinator to {pid} (attempt {attempt+1}/{retries}): {e}")
                time.sleep(delay)

    def poll_queue_as_leader(self):
        while True:
            if self.leader_id == self.my_id:
                try:
                    req = queue_pb.OrderDequeueRequest(executor_id=str(self.my_id))
                    resp = self.queue_stub.Dequeue(req)
                    if not resp.success:
                        print(f"[Leader {self.my_id}] Queue is empty => waiting.")
                        time.sleep(5)
                        continue
                    print(f"[Leader {self.my_id}] Executing order {resp.order_id} with data: {resp.order_data}")
                    time.sleep(2)
                except Exception as e:
                    print(f"[Leader {self.my_id}] Dequeue error: {e}")
                    time.sleep(5)
            else:
                time.sleep(5)

    def check_leader_liveness(self):
        while True:
            if self.leader_id == -1:
                self.start_election()
            elif self.leader_id != self.my_id:
                # check heartbeat on leader
                try:
                    channel = grpc.insecure_channel(f"order_executor{self.leader_id}:50056")
                    stub = executor_pb2_grpc.OrderExecutorStub(channel)
                    # We need a HeartbeatRequest message (we can also use Empty)
                    stub.Heartbeat(executor_pb2.HeartbeatRequest())
                except Exception:
                    print(f"[Executor {self.my_id}] Leader {self.leader_id} not responding => start election.")
                    self.start_election()
            time.sleep(10)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance_id", required=True, help="Numeric ID for this executor")
    parser.add_argument("--executor_ids", required=True, help="Comma-separated list of numeric IDs")
    parser.add_argument("--order_queue_addr", default="order_queue:50054", help="Address of the Order Queue")
    args = parser.parse_args()

    svc = ExecutorService(args.instance_id, args.executor_ids, args.order_queue_addr)
    svc.run_server()

if __name__ == "__main__":
    main()
