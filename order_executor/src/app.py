import sys
import os
import time
import grpc
import threading

# Import the OrderQueue stubs
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
order_queue_grpc_path = os.path.abspath(os.path.join(FILE, "../../../utils/pb/order_queue"))
sys.path.insert(0, order_queue_grpc_path)

import order_queue_pb2 as queue_pb
import order_queue_pb2_grpc as queue_grpc

class ExecutorService:
    def __init__(self, instance_id, executor_ids, queue_addr):
        """
        :param instance_id: Unique identifier for this executor.
        :param executor_ids: List of all known executor instance IDs (strings).
        :param queue_addr: Order Queue address in the format "host:port".
        """
        self.instance_id = instance_id
        self.executor_ids = executor_ids  # e.g., ['executor1', 'executor2']
        self.queue_addr = queue_addr
        self.leader_id = None
        self.queue_stub = None

        # Connect to the Order Queue service.
        channel = grpc.insecure_channel(self.queue_addr)
        self.queue_stub = queue_grpc.OrderQueueStub(channel)

    def start_leader_election(self):
        """
        Simple election: The executor with the largest ID (lexicographically) becomes the leader.
        """
        all_ids = list(self.executor_ids)
        if self.instance_id not in all_ids:
            all_ids.append(self.instance_id)
        self.leader_id = max(all_ids)
        print(f"[Executor {self.instance_id}] Leader election complete. Leader is {self.leader_id}.")

    def run(self):
        """
        If this instance is the leader, repeatedly dequeue orders and simulate execution.
        Otherwise, idle.
        """
        if self.instance_id != self.leader_id:
            print(f"[Executor {self.instance_id}] Not the leader. Idling.")
            while True:
                time.sleep(10)
        else:
            print(f"[Executor {self.instance_id}] I am the leader. Beginning order execution.")
            while True:
                try:
                    req = queue_pb.OrderDequeueRequest(executor_id=self.instance_id)
                    resp = self.queue_stub.Dequeue(req)
                    if not resp.success:
                        print(f"[Leader {self.instance_id}] Queue is empty. Waiting...")
                        time.sleep(5)
                        continue
                    order_id = resp.order_id
                    order_data = resp.order_data
                    print(f"[Leader {self.instance_id}] Executing order {order_id} with data: {order_data}")
                    # Simulate execution work.
                    time.sleep(2)
                except Exception as e:
                    print(f"[Leader {self.instance_id}] Error during order execution: {e}")
                    time.sleep(5)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance_id", required=True, help="Unique ID for this executor")
    parser.add_argument("--executor_ids", required=True, help="Comma-separated list of known executor IDs")
    parser.add_argument("--order_queue_addr", default="order_queue:50054", help="Address of the Order Queue service")
    args = parser.parse_args()

    executor_ids = [x.strip() for x in args.executor_ids.split(",") if x.strip()]
    service = ExecutorService(args.instance_id, executor_ids, args.order_queue_addr)
    service.start_leader_election()
    service.run()
