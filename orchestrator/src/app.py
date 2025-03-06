import sys
import os
import requests
from concurrent.futures import ThreadPoolExecutor
import grpc
import json
from flask import jsonify
from flask import Flask, request, render_template
from flask_cors import CORS
from google.protobuf.json_format import ParseDict
import uuid

# Import gRPC stubs
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
transaction_verification_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/transaction_verification'))
suggestions_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/suggestions'))
sys.path.insert(0, fraud_detection_grpc_path)
sys.path.insert(0, transaction_verification_grpc_path)
sys.path.insert(0, suggestions_grpc_path)

import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc
import transaction_verification_pb2 as transaction_verification
import transaction_verification_pb2_grpc as transaction_verification_grpc
import suggestions_pb2 as suggestions
import suggestions_pb2_grpc as suggestions_grpc

# Create Flask app
app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})

# Define gRPC service addresses
GRPC_SERVICES = {
    "fraud_detection": "fraud_detection:50051",
    "transaction_verification": "transaction_verification:50052",
    "suggestions": "suggestions:50053"
}

def check_fraud(request_data):
    with grpc.insecure_channel(GRPC_SERVICES["fraud_detection"]) as channel:
        stub = fraud_detection_grpc.FraudDetectionStub(channel)
        request = fraud_detection.FraudCheckRequest(
            transaction_id=request_data.get("transactionId", "12345"),
            payment=fraud_detection.PaymentInfo(
                credit_card_number=request_data.get("creditCard", {}).get("number", ""),
                expiration_date=request_data.get("creditCard", {}).get("expirationDate", ""),
                cvv=request_data.get("creditCard", {}).get("cvv", "")),
            amount=request_data.get("amount", 100)
        )
        return stub.CheckFraud(request)


def validate_transaction(transaction_data):
    with grpc.insecure_channel(GRPC_SERVICES["transaction_verification"]) as channel:
        stub = transaction_verification_grpc.TransactionVerificationStub(channel)

        # Ensure `creditCard` remains a dictionary and correctly maps to the expected gRPC structure
        if "creditCard" in transaction_data and isinstance(transaction_data["creditCard"], dict):
            # Map fields correctly
            transaction_data["payment"] = {
                "credit_card_number": transaction_data["creditCard"].get("number", ""),
                "expiration_date": transaction_data["creditCard"].get("expirationDate", ""),
                "cvv": transaction_data["creditCard"].get("cvv", "")
            }
            # Remove `creditCard` key to avoid conflicts
            del transaction_data["creditCard"]

        # Convert dictionary to gRPC request object
        request = ParseDict(transaction_data, transaction_verification.TransactionValidationRequest())

        return stub.ValidateTransaction(request)


def get_suggestions(num_books):
    with grpc.insecure_channel(GRPC_SERVICES["suggestions"]) as channel:
        stub = suggestions_grpc.BookSuggestionsStub(channel)
        request = suggestions.BookSuggestionsRequest(num_books=num_books)
        response = stub.GetSuggestions(request)
        return [{"title": book.title, "author": book.author} for book in response.books]


@app.route('/checkout', methods=['POST'])
def checkout():
    request_data = json.loads(request.data)
    transaction_id = request_data.get("transactionId", "12345")
    #transaction_id = request_data.get("transactionId", str(uuid.uuid4()))
    amount = request_data.get("amount", 100)
    num_books = request_data.get("numBooks", 3)

    with ThreadPoolExecutor() as executor:
        future_fraud = executor.submit(check_fraud, request_data)
        future_validation = executor.submit(validate_transaction, request_data)
        future_suggestions = executor.submit(get_suggestions, num_books)

        fraud_result = future_fraud.result()
        validation_result = future_validation.result()
        suggestions_result = future_suggestions.result()

    # Approve order only if fraud check is False AND validation is True
    if fraud_result.is_fraudulent:
        order_status = "Order Rejected - Fraudulent Transaction"
        suggested_books = []
    elif not validation_result.valid:
        order_status = "Order Rejected - Invalid Transaction Data"
        suggested_books = []
    else:
        order_status = "Order Approved"
        suggested_books = suggestions_result

    response = {
        "orderId": transaction_id,
        "status": order_status,
        "suggestedBooks": suggested_books
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)