import sys
import os
import json
import uuid
import grpc
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.protobuf.json_format import ParseDict

# --- Setup sys.path for gRPC stub imports ---
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")

# Add base `pb` directory to sys.path
pb_base_path = os.path.abspath(os.path.join(FILE, "../../../utils/pb"))
sys.path.insert(0, pb_base_path)

# Add individual service directories (optional but may help in some cases)
sys.path.insert(0, os.path.join(pb_base_path, "fraud_detection"))
sys.path.insert(0, os.path.join(pb_base_path, "transaction_verification"))
sys.path.insert(0, os.path.join(pb_base_path, "suggestions"))

# --- Import gRPC generated modules ---
import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc
import transaction_verification_pb2 as transaction_verification
import transaction_verification_pb2_grpc as transaction_verification_grpc
import suggestions_pb2 as suggestions
import suggestions_pb2_grpc as suggestions_grpc

# ✅ Correct imports for order_queue
from order_queue import order_queue_pb2 as order_queue
from order_queue import order_queue_pb2_grpc as order_queue_grpc

# --- Flask app setup ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# gRPC services location (Docker service names)
GRPC_SERVICES = {
    "fraud_detection": "fraud_detection:50051",
    "transaction_verification": "transaction_verification:50052",
    "suggestions": "suggestions:50053",
    "order_queue": "order_queue:50054"
}

# In-memory store for vector clocks
orders = {}

# --- Init helpers ---
def init_order(order_id, data):
    orders[order_id] = {
        "data": data,
        "vector_clock": {
            "fraud_detection": 0,
            "transaction_verification": 0,
            "suggestions": 0
        }
    }
    print(f"[Init] Order {order_id} vector clock: {orders[order_id]['vector_clock']}")
    return orders[order_id]

def init_order_fraud(order_id, data):
    with grpc.insecure_channel(GRPC_SERVICES["fraud_detection"]) as ch:
        stub = fraud_detection_grpc.FraudDetectionStub(ch)
        stub.InitOrder(fraud_detection.OrderInitRequest(order_id=order_id, order_data=json.dumps(data)))

def init_order_transaction(order_id, data):
    with grpc.insecure_channel(GRPC_SERVICES["transaction_verification"]) as ch:
        stub = transaction_verification_grpc.TransactionVerificationStub(ch)
        stub.InitOrder(transaction_verification.OrderInitRequest(order_id=order_id, order_data=json.dumps(data)))

def init_order_suggestions(order_id, data):
    with grpc.insecure_channel(GRPC_SERVICES["suggestions"]) as ch:
        stub = suggestions_grpc.BookSuggestionsStub(ch)
        stub.InitOrder(suggestions.OrderInitRequest(order_id=order_id, order_data=json.dumps(data)))

def enqueue_order(order_id, order_data):
    with grpc.insecure_channel(GRPC_SERVICES['order_queue']) as ch:
        stub = order_queue_grpc.OrderQueueStub(ch)
        req = order_queue.Order(order_id=order_id, order_data=json.dumps(order_data))  # ✅ This matches your .proto
        return stub.Enqueue(req)

# --- Service logic ---
def check_fraud(data):
    with grpc.insecure_channel(GRPC_SERVICES["fraud_detection"]) as ch:
        stub = fraud_detection_grpc.FraudDetectionStub(ch)
        return stub.CheckFraud(fraud_detection.FraudCheckRequest(
            order_id=data.get("transactionId", "12345"),
            transaction_id=data.get("transactionId", "12345"),
            payment=fraud_detection.PaymentInfo(
                credit_card_number=data.get("creditCard", {}).get("number", ""),
                expiration_date=data.get("creditCard", {}).get("expirationDate", ""),
                cvv=data.get("creditCard", {}).get("cvv", "")
            ),
            amount=data.get("amount", 100)
        ))

def validate_transaction(data):
    if "order_id" not in data:
        data["order_id"] = data.get("transactionId", "12345")
    if isinstance(data.get("creditCard"), dict):
        data["payment"] = {
            "credit_card_number": data["creditCard"].get("number", ""),
            "expiration_date": data["creditCard"].get("expirationDate", ""),
            "cvv": data["creditCard"].get("cvv", "")
        }
        del data["creditCard"]
    request = ParseDict(data, transaction_verification.TransactionValidationRequest())
    with grpc.insecure_channel(GRPC_SERVICES["transaction_verification"]) as ch:
        stub = transaction_verification_grpc.TransactionVerificationStub(ch)
        return stub.ValidateTransaction(request)

def get_suggestions(num_books, order_id):
    with grpc.insecure_channel(GRPC_SERVICES["suggestions"]) as ch:
        stub = suggestions_grpc.BookSuggestionsStub(ch)
        req = suggestions.BookSuggestionsRequest(order_id=order_id, num_books=num_books)
        res = stub.GetSuggestions(req)
        return [{"title": b.title, "author": b.author} for b in res.books]

# --- API route ---
@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json(force=True)
    order_id = data.get("transactionId", str(uuid.uuid4()))
    num_books = data.get("numBooks", 3)
    data["order_id"] = order_id

    init_order(order_id, data)
    with ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(init_order_fraud, order_id, data),
            pool.submit(init_order_transaction, order_id, data),
            pool.submit(init_order_suggestions, order_id, data)
        ]
        for f in futures:
            f.result()

    with ThreadPoolExecutor() as pool:
        fraud_future = pool.submit(check_fraud, data)
        validation_future = pool.submit(validate_transaction, data)
        suggestions_future = pool.submit(get_suggestions, num_books, order_id)

        fraud_result = fraud_future.result()
        validation_result = validation_future.result()
        suggestions_result = suggestions_future.result()

    if fraud_result.is_fraudulent:
        status = "Order Rejected - Fraudulent Transaction"
        suggested_books = []
    elif not validation_result.valid:
        status = "Order Rejected - Invalid Transaction Data"
        suggested_books = []
    else:
        status = "Order Approved"
        suggested_books = suggestions_result
        enqueue_response = enqueue_order(order_id, data)
        print(f"[Enqueue] Order {order_id}: success={enqueue_response.success}, message={enqueue_response.message}")

    return jsonify({
        "orderId": order_id,
        "status": status,
        "suggestedBooks": suggested_books
    })

# --- Entry ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
