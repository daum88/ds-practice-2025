import sys
import os
import random

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)
import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc

import grpc
from concurrent import futures

class FraudDetectionService(fraud_detection_grpc.FraudDetectionServicer):
    def CheckFraud(self, request, context):
        response = fraud_detection.FraudCheckResponse()
        print("Checking transaction for fraud...")
        
        # Dummy fraud detection logic
        if request.amount > 1000 or random.random() < 0.1:
            response.is_fraudulent = True
            response.message = "Transaction flagged as fraudulent."
        else:
            response.is_fraudulent = False
            response.message = "✅ Transaction is legitimate."
        
        print(f"Transaction {request.transaction_id}: {response.message}")
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    fraud_detection_grpc.add_FraudDetectionServicer_to_server(FraudDetectionService(), server)
    # Listen on port 50051
    port = "50051"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Server started. Listening on port 50051.")
    # Keep thread alive
    server.wait_for_termination()

if __name__ == '__main__':
    serve()