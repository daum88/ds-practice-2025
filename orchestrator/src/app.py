import sys
import os
import json
import grpc
import threading
import logging
from flask import Flask, request
from flask_cors import CORS

# Configure logging for the orchestrator with timestamps and log levels.
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Append the shared protobuf directory and the fraud_detection subdirectory to sys.path.
# This allows us to import the generated gRPC modules for our backend services.
base_pb = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../utils/pb"))
sys.path.append(base_pb)
sys.path.append(os.path.join(base_pb, "fraud_detection"))

# Import gRPC modules for fraud detection, transaction verification, and suggestions.
from fraud_detection import fraud_detection_pb2 as fraud_pb
from fraud_detection import fraud_detection_pb2_grpc as fraud_grpc
import transaction_verification_pb2 as txn_pb
import transaction_verification_pb2_grpc as txn_grpc
import suggestions_pb2 as suggest_pb
import suggestions_pb2_grpc as suggest_grpc

# Initialize the Flask app with CORS support to allow cross-origin requests.
# This REST API endpoint is used to connect the frontend to the backend services.
app = Flask(__name__)
CORS(app)

def check_fraud(order_data):
    """
    Establishes a gRPC connection to the Fraud Detection service (running on port 50051)
    and calls its CheckFraud method with the order data. The service returns a boolean
    indicating if the order is fraudulent.
    """
    logging.info("Calling Fraud Detection Service")
    with grpc.insecure_channel("fraud_detection:50051") as channel:
        stub = fraud_grpc.FraudDetectionStub(channel)
        response = stub.CheckFraud(fraud_pb.FraudRequest(order_json=json.dumps(order_data)))
    logging.info(f"Fraud check returned: {response.is_fraudulent}")
    return response.is_fraudulent

def verify_transaction(order_data):
    """
    Establishes a gRPC connection to the Transaction Verification service (running on port 50052)
    and calls its VerifyTransaction method to validate the order details (e.g., items present).
    Returns a boolean indicating whether the transaction is valid.
    """
    logging.info("Calling Transaction Verification Service")
    with grpc.insecure_channel("transaction_verification:50052") as channel:
        stub = txn_grpc.TransactionVerificationStub(channel)
        response = stub.VerifyTransaction(txn_pb.TransactionRequest(order_json=json.dumps(order_data)))
    logging.info(f"Transaction verification returned: {response.is_valid}")
    return response.is_valid

def get_suggestions(order_data):
    """
    Establishes a gRPC connection to the Suggestions service (running on port 50053)
    and calls its GetSuggestions method to get book recommendations based on the order.
    Parses and returns the suggestions as a list of suggestion objects.
    """
    logging.info("Calling Suggestions Service")
    with grpc.insecure_channel("suggestions:50053") as channel:
        stub = suggest_grpc.SuggestionsStub(channel)
        response = stub.GetSuggestions(suggest_pb.SuggestionsRequest(order_json=json.dumps(order_data)))
    suggestions = json.loads(response.suggestions_json)
    logging.info(f"Suggestions received: {suggestions}")
    return suggestions

@app.route('/checkout', methods=['POST'])
def checkout():
    """
    REST endpoint for handling the checkout process. This endpoint:
      - Receives an HTTP POST request from the frontend with order data (in JSON format).
      - Parses the order data.
      - Concurrently calls three backend microservices via gRPC (fraud detection, transaction verification, and suggestions).
      - Uses threading to execute these calls in parallel for improved response time.
      - Consolidates the responses and determines the final order status.
      - Returns a JSON response to the frontend with the order ID, status, and book suggestions.

    This RESTful connection is the main entry point for the frontend to interact with the backend.
    """
    logging.info("Received /checkout request")
    request_data = json.loads(request.data)

    # Initialize variables to store results from each backend service.
    fraud_result, txn_result, suggestions = None, None, None

    # Define helper functions to call each service. These functions update the
    # corresponding variables using the 'nonlocal' keyword to modify variables
    # defined in the enclosing scope.
    def set_fraud_result():
        nonlocal fraud_result
        fraud_result = check_fraud(request_data)

    def set_txn_result():
        nonlocal txn_result
        txn_result = verify_transaction(request_data)

    def set_suggestions():
        nonlocal suggestions
        suggestions = get_suggestions(request_data)

    # Create a list of threads, one for each service call.
    # Threading allows the orchestrator to call all backend services concurrently,
    # reducing overall processing time and improving responsiveness.
    threads = []
    for func in (set_fraud_result, set_txn_result, set_suggestions):
        t = threading.Thread(target=func)
        threads.append(t)
        t.start()
    # Wait for all threads to complete before proceeding.
    for t in threads:
        t.join()

    # Consolidate results:
    # If fraud is detected or transaction verification fails, the order is rejected.
    # Otherwise, the order is approved, and suggestions are provided.
    if fraud_result or not txn_result:
        status = "Order Rejected"
        suggestions = []
    else:
        status = "Order Approved"

    response = {
        "orderId": request_data.get("orderId", "00000"),
        "status": status,
        "suggestedBooks": suggestions
    }
    logging.info(f"Checkout response: {response}")
    return json.dumps(response), 200

if __name__ == "__main__":
    logging.info("Starting orchestrator service on port 5000")
    # Run the Flask app on all interfaces (0.0.0.0) so that it is accessible from other containers.
    app.run(host="0.0.0.0", port=5000)
