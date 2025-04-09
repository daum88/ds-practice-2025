import sys
import os
import json
import random
import grpc
from concurrent import futures

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)
import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc

# In-memory store for caching orders and tracking vector clocks
orders = {}

class FraudDetectionService(fraud_detection_grpc.FraudDetectionServicer):
    def InitOrder(self, request, context):
        orders[request.order_id] = {
            'data': json.loads(request.order_data),
            'vector_clock': {'fraud_detection': 0}
        }
        print(f"Initialized order {request.order_id} with vector clock {orders[request.order_id]['vector_clock']}")
        return fraud_detection.OrderInitResponse(success=True, message='Order initialized')

    def CheckFraud(self, request, context):
        order_id = request.order_id
        if order_id in orders:
            orders[order_id]['vector_clock']['fraud_detection'] += 1
            print(f"Vector clock for {order_id}: {orders[order_id]['vector_clock']}")
        response = fraud_detection.FraudCheckResponse()
        print("Checking transaction for fraud...")

        if request.amount > 1000 or random.random() < 0.1:
            response.is_fraudulent = True
            response.message = "Transaction flagged as fraudulent."        
        elif len(request.payment.credit_card_number) != 16:
            response.is_fraudulent = True
            response.message = "Invalid credit card number."        
        elif len(request.payment.expiration_date) == 5 and (int(request.payment.expiration_date[:2]) > 12 or int(request.payment.expiration_date[3:]) < 25):
            response.is_fraudulent = True
            response.message = "Credit card expired."        
        elif request.payment.cvv == "000" or len(request.payment.cvv) != 3:
            response.is_fraudulent = True
            response.message = "Invalid CVV."        
        else:
            response.is_fraudulent = False
            response.message = "✅ Transaction is legitimate."
        print(f"Transaction Verified: {response.message}")
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    fraud_detection_grpc.add_FraudDetectionServicer_to_server(FraudDetectionService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Fraud Detection Server started on port 50051.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
