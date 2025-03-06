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
            response.message = "Transaction flagged as fraudulent. Invalid transaction data."

        if len(request.payment.credit_card_number) != 16:
            response.is_fraudulent = True
            response.message = "Transaction flagged as fraudulent. Invalid credit card number."

        if len(request.payment.expiration_date) == 5 and (int(request.payment.expiration_date[0:2]) > 12 or int(request.payment.expiration_date[3:5]) < 25):
            response.is_fraudulent = True
            response.message = "Transaction flagged as fraudulent. Credit card has been expired."
            print(f"Transaction {request.transaction_id}: {response.message}")
            return response

        if request.payment.cvv == "000" or not len(request.payment.cvv) == 3:
            response.is_fraudulent = True
            response.message = "Transaction flagged as fraudulent. CVV is invalid."

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