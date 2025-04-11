import os
import sys
import time
import grpc
import threading
from concurrent import futures

# Import the Bully stubs
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
    # e.g. "1,2,3" => [1,2,3]
    return [int(x.strip()) for x in env_value.split(",") if x.strip()]


class ExecutorServicer(executor_pb2_grpc.ExecutorServicer):
    """
    Implements the Bully RPC endpoints for other executors to call:
    1) Election
    2) Coordinator
    3) Heartbeat
    """
    def __init__(self, main_service):
        self.main_service = main_service

    def Election(self, request, context):
        """
        Called by a lower-ID candidate. If our ID is higher, we respond ok=true,
        then we start our own election. If our ID is lower, respond ok=false.
        """
        candidate_id = request.candidate_id
        my_id = self.main_service.my_id
        if my_id > candidate_id:
            print(f"[Executor {my_id}] Received ELECTION from {candidate_id}; I'm bigger => ok=true, starting my own election.")
            threading.Thread(target=self.main_service.start_election, daemon=True).start()
            return executor_pb2.ElectionResponse(ok=True)
        else:
            print(f"[Executor {my_id}] Received ELECTION from {candidate_id}; I'm smaller => ok=false.")
            return executor_pb2.ElectionResponse(ok=False)

    def Coordinator(self, request, context):
        """
        Called by the new leader to announce they are coordinator.
        We set 'leader_id' to them.
        """
        coord_id = request.coordinator_id
        self.main_service.leader_id = coord_id
        if self.main_service.my_id != coord_id:
            print(f"[Executor {self.main_service.my_id}] Acknowledging new leader: {coord_id}")
        else:
            print(f"[Executor {coord_id}] I am confirmed as leader.")
        return Empty()

    def Heartbeat(self, request, context):
        """Optional heartbeat to check if leader is alive."""
        return executor_pb2.HeartbeatResponse(
            alive=True,
            leader_status=f"Leader is {self.main_service.leader_id}"
        )


class ExecutorService:
    def __init__(self, instance_id, all_ids_str, queue_addr):
        """
        :param instance_id: e.g. "2" (string). We'll parse it as int.
        :param all_ids_str: e.g. "1,2,3"
        :param queue_addr: e.g. "order_queue:50054"
        """
        self.my_id = int(instance_id)
        self.all_ids = parse_int_list(all_ids_str)  # e.g. [1,2,3]
        if self.my_id not in self.all_ids:
            self.all_ids.append(self.my_id)
        self.max_id = max(self.all_ids)

        self.queue_addr = queue_addr
        self.leader_id = -1  # unknown at start
        self.in_election = False
        self.lock = threading.Lock()  # protect in_election, leader_id

        # Connect to order queue
        channel = grpc.insecure_channel(self.queue_addr)
        self.queue_stub = queue_grpc.OrderQueueStub(channel)

    def run_server(self):
        """
        Start a gRPC server on port 50056.
        Then spawn threads:
          - poll_queue_as_leader
          - check_leader_liveness
        Possibly start an election on startup.
        """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        executor_servicer = ExecutorServicer(self)
        executor_pb2_grpc.add_ExecutorServicer_to_server(executor_servicer, server)

        server.add_insecure_port('[::]:50056')
        server.start()
        print(f"[Executor {self.my_id}] Bully server started on port 50056.")

        # Delay to let other executors come up before we do an election
        print(f"[Executor {self.my_id}] Waiting 5s to allow others to start...")
        time.sleep(5)

        # If we still don't know a leader, start an election
        if self.leader_id == -1:
            threading.Thread(target=self.start_election, daemon=True).start()

        # Start background threads
        threading.Thread(target=self.poll_queue_as_leader, daemon=True).start()
        threading.Thread(target=self.check_leader_liveness, daemon=True).start()

        # Keep main thread alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            server.stop(0)
            print(f"[Executor {self.my_id}] Shutting down...")

    def start_election(self):
        """
        Bully Algorithm steps:
        1) Mark in_election = True
        2) Send Election(...) to all processes with ID > my_id
        3) If no one with higher ID responds ok=true, we are leader => send Coordinator
        4) If any respond ok=true, we wait for their coordinator message
        """
        with self.lock:
            if self.in_election:
                return
            self.in_election = True

        print(f"[Executor {self.my_id}] Starting election...")

        higher_ids = [pid for pid in self.all_ids if pid > self.my_id]
        got_ok = False
        for hid in higher_ids:
            # We try multiple times in case the other container is still starting
            if self.try_election_call(hid):
                got_ok = True
                print(f"[Executor {self.my_id}] ID={hid} responded ok => they might become leader.")

        if not got_ok:
            # I'm the biggest among reachable => I'm the leader
            self.leader_id = self.my_id
            print(f"[Executor {self.my_id}] I am now the leader (no bigger ID responded).")
            self.announce_coordinator()
        else:
            # Wait to receive a Coordinator call from that bigger ID
            print(f"[Executor {self.my_id}] Wait for new leader's Coordinator message...")

        with self.lock:
            self.in_election = False

    def try_election_call(self, hid, retries=3, delay=2):
        """
        Attempt to contact the higher process hid for an Election call,
        up to 'retries' times. Return True if resp.ok==True, else False.
        """
        for attempt in range(retries):
            try:
                channel = grpc.insecure_channel(f"order_executor{hid}:50056")
                stub = executor_pb2_grpc.ExecutorStub(channel)
                resp = stub.Election(executor_pb2.ElectionRequest(candidate_id=self.my_id))
                return resp.ok
            except Exception as e:
                print(f"[Executor {self.my_id}] Could not contact {hid} (attempt {attempt+1}/{retries}): {e}")
                time.sleep(delay)
        return False

    def announce_coordinator(self):
        """
        Called by the winner. We send Coordinator(...) to all processes.
        """
        for pid in self.all_ids:
            if pid == self.my_id:
                continue
            self.try_coordinator_call(pid)

    def try_coordinator_call(self, pid, retries=3, delay=2):
        """
        Attempt to call Coordinator(...) on a given pid, with multiple retries.
        """
        for attempt in range(retries):
            try:
                channel = grpc.insecure_channel(f"order_executor{pid}:50056")
                stub = executor_pb2_grpc.ExecutorStub(channel)
                stub.Coordinator(executor_pb2.CoordinatorRequest(coordinator_id=self.my_id))
                return
            except Exception as e:
                print(f"[Executor {self.my_id}] Could not send Coordinator to {pid} (attempt {attempt+1}/{retries}): {e}")
                time.sleep(delay)

    def poll_queue_as_leader(self):
        """
        If I'm leader, repeatedly Dequeue an order from the queue and 'execute' it.
        If I'm not leader, do nothing but sleep.
        """
        while True:
            if self.leader_id == self.my_id:
                try:
                    req = queue_pb.OrderDequeueRequest(executor_id=str(self.my_id))
                    resp = self.queue_stub.Dequeue(req)
                    if not resp.success:
                        print(f"[Leader {self.my_id}] Queue is empty; waiting...")
                        time.sleep(5)
                        continue
                    # We got an order
                    print(f"[Leader {self.my_id}] Executing order {resp.order_id} with data: {resp.order_data}")
                    time.sleep(2)  # simulate actual work
                except Exception as e:
                    print(f"[Leader {self.my_id}] Dequeue error: {e}")
                    time.sleep(5)
            else:
                time.sleep(5)

    def check_leader_liveness(self):
        """
        Periodically check if the leader is alive.
        If no response => start_election.
        """
        while True:
            if self.leader_id == -1:
                # no known leader => start an election
                self.start_election()
            elif self.leader_id != self.my_id:
                # attempt a heartbeat on the known leader
                try:
                    channel = grpc.insecure_channel(f"order_executor{self.leader_id}:50056")
                    stub = executor_pb2_grpc.ExecutorStub(channel)
                    stub.Heartbeat(Empty())
                    # If we get an exception => leader might be dead
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
