import sys
import os
import grpc
import json
import threading
import logging
from flask import Flask, request
from flask_cors import CORS

# Configure logging for the orchestrator
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Append the shared pb directory and fraud_detection subdirectory to sys.path
base_pb = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../utils/pb"))
sys.path.append(base_pb)
sys.path.append(os.path.join(base_pb, "fraud_detection"))

# Import gRPC modules from the shared folder
from fraud_detection import fraud_detection_pb2 as fraud_pb
from fraud_detection import fraud_detection_pb2_grpc as fraud_grpc
import transaction_verification_pb2 as txn_pb
import transaction_verification_pb2_grpc as txn_grpc
import suggestions_pb2 as suggest_pb
import suggestions_pb2_grpc as suggest_grpc

# Initialize Flask app with CORS support.
app = Flask(__name__)
CORS(app)

def check_fraud(order_data):
    """
    Calls the Fraud Detection gRPC service to determine if the order is fraudulent.
    """
    logging.info("Calling Fraud Detection Service")
    with grpc.insecure_channel("fraud_detection:50051") as channel:
        stub = fraud_grpc.FraudDetectionStub(channel)
        response = stub.CheckFraud(fraud_pb.FraudRequest(order_json=json.dumps(order_data)))
    logging.info(f"Fraud check returned: {response.is_fraudulent}")
    return response.is_fraudulent

def verify_transaction(order_data):
    """
    Calls the Transaction Verification gRPC service to validate the transaction.
    """
    logging.info("Calling Transaction Verification Service")
    with grpc.insecure_channel("transaction_verification:50052") as channel:
        stub = txn_grpc.TransactionVerificationStub(channel)
        response = stub.VerifyTransaction(txn_pb.TransactionRequest(order_json=json.dumps(order_data)))
    logging.info(f"Transaction verification returned: {response.is_valid}")
    return response.is_valid

def get_suggestions(order_data):
    """
    Calls the Suggestions gRPC service to get product suggestions based on the order.
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
    REST endpoint for handling order checkout.
    It delegates processing to fraud detection, transaction verification,
    and suggestions services concurrently.
    """
    logging.info("Received /checkout request")
    request_data = json.loads(request.data)
    fraud_result, txn_result, suggestions = None, None, None

    def set_fraud_result():
        nonlocal fraud_result
        fraud_result = check_fraud(request_data)

    def set_txn_result():
        nonlocal txn_result
        txn_result = verify_transaction(request_data)

    def set_suggestions():
        nonlocal suggestions
        suggestions = get_suggestions(request_data)

    threads = []
    for func in (set_fraud_result, set_txn_result, set_suggestions):
        t = threading.Thread(target=func)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # Consolidate results and determine final status.
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
    app.run(host="0.0.0.0", port=5000)
