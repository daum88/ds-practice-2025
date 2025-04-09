# order_executor/src/executor_service.py
import grpc
import time
import threading
import socket
import json
import os
from concurrent import futures
from queue import PriorityQueue

from google.protobuf.json_format import ParseDict
import order_executor_pb2 as executor_pb2
import order_executor_pb2_grpc as executor_pb2_grpc
import order_queue_pb2 as order_queue_pb2
import order_queue_pb2_grpc as order_queue_pb2_grpc

ORDER_QUEUE_ADDRESS = os.getenv("ORDER_QUEUE_ADDRESS", "order_queue:50054")
REPLICA_PORT = int(os.getenv("EXECUTOR_PORT", "6000"))
ALL_REPLICAS = os.getenv("REPLICA_LIST", "executor_1:6000,executor_2:6001").split(',')

# For leader election
leader_lock = threading.Lock()
is_leader = False
replica_id = socket.gethostname()

class ExecutorService(executor_pb2_grpc.OrderExecutorServicer):
    def __init__(self):
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_monitor)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        self.execution_thread = threading.Thread(target=self.execute_loop)
        self.execution_thread.daemon = True
        self.execution_thread.start()

    def heartbeat_monitor(self):
        while True:
            self.perform_leader_election()
            time.sleep(5)

    def perform_leader_election(self):
        global is_leader
        sorted_replicas = sorted(ALL_REPLICAS)
        if f"{replica_id}:{REPLICA_PORT}" == sorted_replicas[0]:
            with leader_lock:
                is_leader = True
        else:
            with leader_lock:
                is_leader = False

    def execute_loop(self):
        while self.running:
            with leader_lock:
                if is_leader:
                    try:
                        with grpc.insecure_channel(ORDER_QUEUE_ADDRESS) as ch:
                            stub = order_queue_pb2_grpc.OrderQueueStub(ch)
                            empty = order_queue_pb2.Empty()
                            order = stub.Dequeue(empty)
                            print(f"👑 [Leader {replica_id}] Executing order {order.order_id} with priority {order.priority}: {order.order_data}")
                            time.sleep(3)
                    except grpc.RpcError as e:
                        print(f"⚠️ Leader failed to dequeue: {e}")
            time.sleep(2)

    def HealthCheck(self, request, context):
        return executor_pb2.HealthResponse(status="alive")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    executor_pb2_grpc.add_OrderExecutorServicer_to_server(ExecutorService(), server)
    server.add_insecure_port(f"[::]:{REPLICA_PORT}")
    server.start()
    print(f"✅ Executor running at port {REPLICA_PORT} with ID {replica_id}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
