import sys
import os
import json
import grpc
from concurrent import futures
from queue import Queue

# Add both pb and pb/order_queue to sys.path
sys.path.insert(0, os.path.abspath("/app/utils"))
sys.path.insert(0, os.path.abspath("/app/utils/pb"))


# Import the gRPC stubs
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
order_queue_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/order_queue'))
sys.path.insert(0, order_queue_grpc_path)
import order_queue_pb2 as order_queue
import order_queue_pb2_grpc as order_queue_grpc


# In-memory queue
order_queue_instance = Queue()

class OrderQueueService(order_queue_grpc.OrderQueueServicer):
    def Enqueue(self, request, context):
        order = {
            'order_id': request.order_id,
            'order_data': request.order_data
        }
        order_queue_instance.put(order)
        print(f"✅ Enqueued order {request.order_id}")
        return order_queue.QueueResponse(success=True, message="Order enqueued")

    def Dequeue(self, request, context):
        if order_queue_instance.empty():
            context.set_details("Queue is empty")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return order_queue.Order()
        
        order = order_queue_instance.get()
        print(f"📤 Dequeued order {order['order_id']}")
        return order_queue.Order(order_id=order['order_id'], order_data=order['order_data'])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    order_queue_grpc.add_OrderQueueServicer_to_server(OrderQueueService(), server)
    server.add_insecure_port('[::]:50054')
    server.start()
    print("📦 Order Queue Server started on port 50054.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
