import grpc
from concurrent import futures
import heapq
import threading
import os
import sys

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
order_queue_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/order_queue'))
sys.path.insert(0, order_queue_grpc_path)

import order_queue_pb2 as order_queue
import order_queue_pb2_grpc as order_queue_grpc

from google.protobuf.empty_pb2 import Empty

class OrderQueueService(order_queue_grpc.OrderQueueServicer):
    def __init__(self):
        # We'll store tuples in a min-heap: (priority, increment, dict)
        self.queue = []
        self.lock = threading.Lock()
        self.counter = 0  # helps maintain FIFO for same priority

    def Enqueue(self, request, context):
        with self.lock:
            heapq.heappush(self.queue, (
                request.priority,
                self.counter,
                {
                    'order_id': request.order_id,
                    'priority': request.priority,
                    'order_data': request.order_data
                }
            ))
            self.counter += 1
        print(f"[OrderQueue] Enqueued order {request.order_id} (priority {request.priority})")
        return order_queue.OrderQueueResponse(
            success=True,
            message="Order enqueued successfully."
        )

    def Dequeue(self, request, context):
        with self.lock:
            if not self.queue:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Queue is empty")
                return order_queue.OrderQueueOrder()

            priority, _, order_info = heapq.heappop(self.queue)

        print(f"[OrderQueue] Dequeued order {order_info['order_id']} (priority {priority})")
        return order_queue.OrderQueueOrder(
            order_id=order_info['order_id'],
            priority=order_info['priority'],
            order_data=order_info['order_data']
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_queue_grpc.add_OrderQueueServicer_to_server(OrderQueueService(), server)
    server.add_insecure_port("[::]:50054")
    server.start()
    print("[OrderQueue] Service started on port 50054")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
