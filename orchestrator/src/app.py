
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
order_queue_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/order_queue'))
sys.path.insert(0, fraud_detection_grpc_path)
sys.path.insert(0, transaction_verification_grpc_path)
sys.path.insert(0, suggestions_grpc_path)
sys.path.insert(0, order_queue_grpc_path)

import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc
import transaction_verification_pb2 as transaction_verification
import transaction_verification_pb2_grpc as transaction_verification_grpc
import suggestions_pb2 as suggestions
import suggestions_pb2_grpc as suggestions_grpc
import order_queue_pb2 as order_queue
import order_queue_pb2_grpc as order_queue_grpc

# Create Flask app
app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})

# Define gRPC service addresses
GRPC_SERVICES = {
    "fraud_detection": "fraud_detection:50051",
    "transaction_verification": "transaction_verification:50052",
    "suggestions": "suggestions:50053",
    "order_queue": "order_queue:50054"
}

# Initialize in-memory store for orders
orders = {}
# Function to initialize order in each service
def init_order(order_id, data):
    orders[order_id] = {
        'data': data,
        'vector_clock': {
            'fraud_detection': 0,
            'transaction_verification': 0,
            'suggestions': 0
        }
    }
    print(f"Initialized order {order_id} with vector clock {orders[order_id]['vector_clock']}")
    return orders[order_id]

# Function to update vector clock for each service
def update_vector_clock(order_id, service):
    if order_id in orders:
        orders[order_id]['vector_clock'][service] += 1
        print(f"Vector clock for {order_id}: {orders[order_id]['vector_clock']}")
    else:
        print(f"Order {order_id} not found in vector clock store.")

# Function to initialize order in each service
def init_order_fraud(order_id, data):
    with grpc.insecure_channel(GRPC_SERVICES['fraud_detection']) as ch:
        stub = fraud_detection_grpc.FraudDetectionStub(ch)
        stub.InitOrder(fraud_detection.OrderInitRequest(order_id=order_id, order_data=json.dumps(data)))

def init_order_transaction(order_id, data):
    with grpc.insecure_channel(GRPC_SERVICES['transaction_verification']) as ch:
        stub = transaction_verification_grpc.TransactionVerificationStub(ch)
        stub.InitOrder(transaction_verification.OrderInitRequest(order_id=order_id, order_data=json.dumps(data)))

def init_order_suggestions(order_id, data):
    with grpc.insecure_channel(GRPC_SERVICES['suggestions']) as ch:
        stub = suggestions_grpc.BookSuggestionsStub(ch)
        stub.InitOrder(suggestions.OrderInitRequest(order_id=order_id, order_data=json.dumps(data)))


def enqueue_order(order_id, data, priority=5):
    with grpc.insecure_channel(GRPC_SERVICES["order_queue"]) as channel:
        stub = order_queue_grpc.OrderQueueStub(channel)
        req = order_queue.OrderQueueRequest(
            order_id=order_id,
            priority=priority,
            order_data=json.dumps(data)
        )
        return stub.Enqueue(req)

def check_fraud(request_data):
    with grpc.insecure_channel(GRPC_SERVICES["fraud_detection"]) as channel:
        stub = fraud_detection_grpc.FraudDetectionStub(channel)
        req = fraud_detection.FraudCheckRequest(
            order_id=request_data.get("order_id", "12345"),  # Pass the order_id here
            transaction_id=request_data.get("transactionId", "12345"),
            payment=fraud_detection.PaymentInfo(
                credit_card_number=request_data.get("creditCard", {}).get("number", ""),
                expiration_date=request_data.get("creditCard", {}).get("expirationDate", ""),
                cvv=request_data.get("creditCard", {}).get("cvv", "")
            ),
            amount=request_data.get("amount", 100)
        )
        return stub.CheckFraud(req)


def validate_transaction(transaction_data):
    # Ensure 'order_id' is present in the request data
    if "order_id" not in transaction_data:
        # Use the transactionId from the request or generate one
        transaction_data["order_id"] = transaction_data.get("transactionId", "12345")
    
    # Ensure `creditCard` remains a dictionary and correctly maps to the expected gRPC structure
    if "creditCard" in transaction_data and isinstance(transaction_data["creditCard"], dict):
        transaction_data["payment"] = {
            "credit_card_number": transaction_data["creditCard"].get("number", ""),
            "expiration_date": transaction_data["creditCard"].get("expirationDate", ""),
            "cvv": transaction_data["creditCard"].get("cvv", "")
        }
        del transaction_data["creditCard"]

    # Convert dictionary to gRPC request object
    request = ParseDict(transaction_data, transaction_verification.TransactionValidationRequest())
    with grpc.insecure_channel(GRPC_SERVICES["transaction_verification"]) as channel:
        stub = transaction_verification_grpc.TransactionVerificationStub(channel)
        return stub.ValidateTransaction(request)


def get_suggestions(num_books, order_id):
    with grpc.insecure_channel(GRPC_SERVICES["suggestions"]) as channel:
        stub = suggestions_grpc.BookSuggestionsStub(channel)
        req = suggestions.BookSuggestionsRequest(order_id=order_id, num_books=num_books)
        response = stub.GetSuggestions(req)
        return [{"title": book.title, "author": book.author} for book in response.books]


@app.route('/checkout', methods=['POST'])
def checkout():
    request_data = json.loads(request.data)
    #print(request_data)
    transaction_id =  str(uuid.uuid4())  # Generate a unique transaction ID
    request_data["transactionId"] = transaction_id  # Add transactionId to the request data
    order_id = transaction_id  # Using transactionId as order_id
    num_books = len(request_data.get("items", []))
    
    # Inject order_id into the request_data for ValidateTransaction as well
    request_data["order_id"] = order_id

    # Initialize order in each service
    init_order(order_id, request_data)
    with ThreadPoolExecutor() as init_executor:
        init_futures = [
            init_executor.submit(init_order_fraud, order_id, request_data),
            init_executor.submit(init_order_transaction, order_id, request_data),
            init_executor.submit(init_order_suggestions, order_id, request_data)
        ]
        for future in init_futures:
            future.result()

    # Execute business logic in parallel
    with ThreadPoolExecutor() as executor:
        future_fraud = executor.submit(check_fraud, request_data)
        future_validation = executor.submit(validate_transaction, request_data)
        future_suggestions = executor.submit(get_suggestions, num_books, order_id)

        fraud_result = future_fraud.result()
        validation_result = future_validation.result()
        suggestions_result = future_suggestions.result()

    if fraud_result.is_fraudulent:
        status = 'Order Rejected - Fraudulent Transaction'
        suggested_books = []
    elif not validation_result.valid:
        status = 'Order Rejected - Invalid Transaction Data'
        suggested_books = []
    else:
        status = 'Order Approved'
        suggested_books = suggestions_result

        #simple logic: if numbooks>2 => priority=1, else=5
        priority = 1 if len(request_data.get("items", [])) > 2 else 5
        queue_response = enqueue_order(order_id, request_data, priority)
        if not queue_response.success:
            print(f"[Orchestrator] Could not enqueue order {order_id}. Reason: {queue_response.message}")
        else:
            print(f"[Orchestrator] Order {order_id} enqueued with priority {priority}.")

    return jsonify({
        'orderId': order_id,
        'status': status,
        'suggestedBooks': suggested_books
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)