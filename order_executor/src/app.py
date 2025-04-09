import os
import time
import sys
import threading
import grpc
from concurrent import futures

# Adjust paths so we can import the compiled gRPC stubs
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
order_queue_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/order_queue'))
sys.path.insert(0, order_queue_grpc_path)

import order_queue_pb2 as order_queue
import order_queue_pb2_grpc as order_queue_grpc

from google.protobuf.empty_pb2 import Empty


# Environment variables
ORDER_QUEUE_ADDR = os.getenv("ORDER_QUEUE_ADDR", "order_queue:50054")
INSTANCE_ID = os.getenv("INSTANCE_ID", "executor1")
EXECUTOR_IDS = os.getenv("EXECUTOR_IDS", "executor1,executor2").split(",")


class ExecutorService:
    """
    A gRPC-based executor that can be replicated. Only the chosen leader
    actually dequeues and executes orders. Others wait until they become leader.
    """

    def __init__(self, executor_id, known_ids):
        self.executor_id = executor_id
        self.known_ids = known_ids

        # We'll create a gRPC channel to the Order Queue service
        self.channel = grpc.insecure_channel(ORDER_QUEUE_ADDR)
        self.queue_stub = order_queue_grpc.OrderQueueStub(self.channel)

        # We track which ID is the leader. We'll set it in start_leader_election().
        self.leader_id = None

        # This can be used to stop the polling thread gracefully
        self.running = True

    def start_leader_election(self):
        """
        Simple leader election:
        The instance with the lexicographically smallest ID is considered the leader.
        """
        cleaned_ids = [x.strip() for x in self.known_ids]
        self.leader_id = sorted(cleaned_ids)[0]
        print(f"[Executor {self.executor_id}] Leader determined to be {self.leader_id}")

    def execute_order(self, order):
        """
        Log and simulate actual 'execution' of an order.
        """
        print(f"[Executor {self.executor_id}] Executing order {order.order_id} (priority={order.priority})...")
        time.sleep(2)  # simulate some real work
        print(f"[Executor {self.executor_id}] Finished executing order {order.order_id}.")

    def poll_queue(self):
        """
        If I'm the leader, repeatedly attempt to dequeue an order from the
        OrderQueue service. If there's an order, execute it. If queue is empty,
        wait. Non-leaders do nothing but log that they aren't the leader.
        """
        while self.running:
            if self.executor_id == self.leader_id:
                try:
                    # Dequeue from the priority queue
                    order = self.queue_stub.Dequeue(Empty())
                    # If successful, we have an order to execute
                    self.execute_order(order)
                except grpc.RpcError as e:
                    if e.code() == grpc.StatusCode.NOT_FOUND:
                        print(f"[Executor {self.executor_id}] Queue empty; waiting...")
                    else:
                        print(f"[Executor {self.executor_id}] Dequeue error: {e.details()}")
            else:
                print(f"[Executor {self.executor_id}] Not leader; skipping dequeue.")
            time.sleep(5)

    def run(self):
        """
        Start the background polling thread, and optionally start
        a gRPC server to confirm we are a 'service'.
        """
        # Start the polling thread
        polling_thread = threading.Thread(target=self.poll_queue, daemon=True)
        polling_thread.start()

        # Optionally, define a minimal gRPC server for this Executor
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        # If you had an 'Executor.proto' with actual RPCs, you would add them here, e.g.:
        # executor_pb2_grpc.add_ExecutorServicer_to_server(ExecutorServicerImpl(...), server)
        # For now, we won't define new RPCs, just show that we can run as a service
        executor_port = 50055  # or any free port
        server.add_insecure_port(f"[::]:{executor_port}")
        server.start()

        print(f"[Executor {self.executor_id}] Service started on port {executor_port}. "
              f"Leader is {self.leader_id}. Known IDs: {self.known_ids}")

        # Keep main thread alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self.running = False
            server.stop(0)
            print(f"[Executor {self.executor_id}] shutting down...")


def launch_executor(executor_id, known_ids):
    """
    In practice, your Docker entrypoint calls this function.
    """
    svc = ExecutorService(executor_id, known_ids)
    svc.start_leader_election()
    svc.run()


def serve():
    """
    Entry point if called from __main__.
    Reads environment variables, launches the ExecutorService.
    """
    print(f"[Executor] Starting up. ID={INSTANCE_ID}, all IDs={EXECUTOR_IDS}")
    launch_executor(INSTANCE_ID, EXECUTOR_IDS)


if __name__ == '__main__':
    serve()
