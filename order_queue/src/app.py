import sys
import os
import threading
import heapq
import grpc
from concurrent import futures

# Adjust import paths if needed
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
order_queue_grpc_path = os.path.abspath(os.path.join(FILE, "../../../utils/pb/order_queue"))
sys.path.insert(0, order_queue_grpc_path)

import order_queue_pb2 as queue_pb
import order_queue_pb2_grpc as queue_grpc

class OrderQueueService(queue_grpc.OrderQueueServicer):
    def __init__(self):
        self._lock = threading.Lock()
        # We'll store (negativePriority, orderId, orderData) so that the
        # highest actual priority is popped first
        self._queue = []  

    def Enqueue(self, request, context):
        """
        Insert the new order (with priority) into our heap.
        """
        with self._lock:
            # Python heapq is a min-heap, so store negative priority if you want "max-heap" behavior
            priority = request.priority
            heapq.heappush(self._queue, (-priority, request.order_id, request.order_data))

        return queue_pb.OrderQueueResponse(
            success=True,
            message=f"Order {request.order_id} enqueued with priority {priority}."
        )

    def Dequeue(self, request, context):
        """
        Pop the top order if available, else indicate that queue is empty.
        """
        with self._lock:
            if not self._queue:
                return queue_pb.OrderDequeueResponse(
                    success=False,
                    order_id="",
                    order_data="",
                    message="Queue is empty."
                )
            top = heapq.heappop(self._queue)
            # top = (negPriority, order_id, order_data)
            neg_priority, order_id, order_data = top
            return queue_pb.OrderDequeueResponse(
                success=True,
                order_id=order_id,
                order_data=order_data,
                message="Dequeued OK"
            )

def serve_queue_service():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    queue_grpc.add_OrderQueueServicer_to_server(OrderQueueService(), server)
    server.add_insecure_port('[::]:50054')  # or whichever port you like
    server.start()
    print("Order Queue Server started on port 50054.")
    server.wait_for_termination()

if __name__ == "__main__":
    serve_queue_service()
