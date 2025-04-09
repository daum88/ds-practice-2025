import sys
import os
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import grpc
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.protobuf.json_format import ParseDict

# Import gRPC stubs paths
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
transaction_verification_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/transaction_verification'))
suggestions_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/suggestions'))
order_queue_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/order_queue'))
sys.path.insert(0, fraud_detection_grpc_path)
sys.path.insert(0, transaction_verification_grpc_path)
sys.path.insert(0, suggestions_grpc_path)
sys.path.insert(0, order_queue_grpc_path)

import fraud_detection_pb2 as fraud_pb
import fraud_detection_pb2_grpc as fraud_grpc
import transaction_verification_pb2 as tx_pb
import transaction_verification_pb2_grpc as tx_grpc
import suggestions_pb2 as sugg_pb
import suggestions_pb2_grpc as sugg_grpc
import order_queue_pb2 as queue_pb
import order_queue_pb2_grpc as queue_grpc

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

# For convenience, define indexes for each service in our local vector clock:
IDX_TRANSACTION = 0
IDX_FRAUD       = 1
IDX_SUGGESTIONS = 2

# Local store for orders
orders = {}
# orders[order_id] = {
#   "data": {...},
#   "vc": [0,0,0]   # orchestrator's local vector clock
# }

def merge_vc(local_vc, incoming_vc):
    for i in range(len(local_vc)):
        local_vc[i] = max(local_vc[i], incoming_vc[i])

# --------------- gRPC stub helper functions ---------------
def get_transaction_stub():
    channel = grpc.insecure_channel(GRPC_SERVICES["transaction_verification"])
    return tx_grpc.TransactionVerificationStub(channel)

def get_fraud_stub():
    channel = grpc.insecure_channel(GRPC_SERVICES["fraud_detection"])
    return fraud_grpc.FraudDetectionStub(channel)

def get_suggestions_stub():
    channel = grpc.insecure_channel(GRPC_SERVICES["suggestions"])
    return sugg_grpc.BookSuggestionsStub(channel)

def get_order_queue_stub():
    channel = grpc.insecure_channel(GRPC_SERVICES["order_queue"])
    return queue_grpc.OrderQueueStub(channel)

# Function to call OrderQueue to enqueue a valid order.
def enqueue_order(order_id, data, priority=5):
    with grpc.insecure_channel(GRPC_SERVICES["order_queue"]) as channel:
        stub = queue_grpc.OrderQueueStub(channel)
        req = queue_pb.OrderQueueRequest(
            order_id=order_id,
            priority=priority,
            order_data=json.dumps(data)
        )
        return stub.Enqueue(req)

# --------------- End of gRPC helpers ---------------

@app.route('/checkout', methods=['POST'])
def checkout():
    """
    Orchestrates the new flow of events (a–f) with partial concurrency.
    If any event fails, we broadcast ClearOrder to all services with the final VC and stop.
    If all succeed, we enqueue the order in the Order Queue and then return the suggestions to the user.
    """
    # Force JSON parsing (in case Content-Type header is missing)
    req_data = request.get_json(force=True)
    if not req_data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # Augment request data if necessary (e.g. ensuring user address exists)
    if "user" in req_data:
        if "address" not in req_data["user"] or not req_data["user"]["address"]:
            billing = req_data.get("billingAddress", {})
            req_data["user"]["address"] = billing.get("street", "Unknown Address")
    else:
        req_data["user"] = {"address": req_data.get("billingAddress", {}).get("street", "Unknown Address")}

    order_id = str(uuid.uuid4())
    req_data["order_id"] = order_id

    # Initialize orchestrator local record for the order.
    orders[order_id] = {
        "data": req_data,
        "vc": [0, 0, 0]
    }
    local_vc = orders[order_id]["vc"]

    # 1) Initialize order in all services.
    init_in_all_services(order_id, req_data)

    # 2) Run events (a) and (b) concurrently.
    executor = ThreadPoolExecutor(max_workers=6)
    futures = {}

    # (a) Transaction: VerifyItems.
    def event_a():
        stub = get_transaction_stub()
        req = tx_pb.OrderEventRequest(order_id=order_id, vector_clock=local_vc)
        return stub.VerifyItems(req)

    # (b) Transaction: VerifyUserData.
    def event_b():
        stub = get_transaction_stub()
        req = tx_pb.OrderEventRequest(order_id=order_id, vector_clock=local_vc)
        return stub.VerifyUserData(req)

    futures['a'] = executor.submit(event_a)
    futures['b'] = executor.submit(event_b)

    final_status = {"ok": True, "message": "", "suggestions": []}

    # Once (a) completes, if successful, do (c): VerifyCreditCard.
    def handle_a_result():
        a_resp = futures['a'].result()
        merge_vc(local_vc, a_resp.updated_vc)
        if not a_resp.success:
            final_status["ok"] = False
            final_status["message"] = f"(a) failed: {a_resp.message}"
            return
        stub = get_transaction_stub()
        c_req = tx_pb.OrderEventRequest(order_id=order_id, vector_clock=local_vc)
        c_resp = stub.VerifyCreditCard(c_req)
        merge_vc(local_vc, c_resp.updated_vc)
        if not c_resp.success:
            final_status["ok"] = False
            final_status["message"] = f"(c) failed: {c_resp.message}"

    # Once (b) completes, if successful, do (d): Fraud CheckUserData.
    def handle_b_result():
        b_resp = futures['b'].result()
        merge_vc(local_vc, b_resp.updated_vc)
        if not b_resp.success:
            final_status["ok"] = False
            final_status["message"] = f"(b) failed: {b_resp.message}"
            return
        stub = get_fraud_stub()
        d_req = fraud_pb.OrderEventRequest(order_id=order_id, vector_clock=local_vc)
        d_resp = stub.CheckUserData(d_req)
        merge_vc(local_vc, d_resp.updated_vc)
        if not d_resp.success:
            final_status["ok"] = False
            final_status["message"] = f"(d) failed: {d_resp.message}"

    futures['handle_a'] = executor.submit(handle_a_result)
    futures['handle_b'] = executor.submit(handle_b_result)
    futures['handle_a'].result()
    futures['handle_b'].result()

    if not final_status["ok"]:
        broadcast_clear(order_id, local_vc)
        return jsonify({
            "orderId": order_id,
            "status": f"Failed early: {final_status['message']}",
            "suggestedBooks": []
        })

    # (e) Fraud: CheckCreditCard in fraud service.
    def event_e():
        stub = get_fraud_stub()
        req = fraud_pb.OrderEventRequest(order_id=order_id, vector_clock=local_vc)
        return stub.CheckCreditCard(req)

    e_resp = event_e()
    merge_vc(local_vc, e_resp.updated_vc)
    if not e_resp.success:
        final_status["ok"] = False
        final_status["message"] = f"(e) failed: {e_resp.message}"
        broadcast_clear(order_id, local_vc)
        return jsonify({
            "orderId": order_id,
            "status": final_status["message"],
            "suggestedBooks": []
        })

    # (f) Suggestions: Get AI suggestions
    def event_f():
        stub = get_suggestions_stub()
        req = sugg_pb.GenerateSuggestionsRequest(
            order_id=order_id,
            num_books=3,
            vector_clock=local_vc
        )
        return stub.GenerateSuggestions(req)

    try:
        f_resp = event_f()
    except Exception as ex:
        print(f"[Orchestrator] AI suggestions failed: {str(ex)}; using fallback list.")
        from random import sample
        BOOKS_LIST = [
            {"title": "1984", "author": "George Orwell"},
            {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
            {"title": "Pride and Prejudice", "author": "Jane Austen"},
            {"title": "The Catcher in the Rye", "author": "J.D. Salinger"}
        ]
        suggested_books = sample(BOOKS_LIST, 3)
    else:
        if not hasattr(f_resp, "books") or not f_resp.books:
            from random import sample
            BOOKS_LIST = [
                {"title": "1984", "author": "George Orwell"},
                {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
                {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
                {"title": "Pride and Prejudice", "author": "Jane Austen"},
                {"title": "The Catcher in the Rye", "author": "J.D. Salinger"}
            ]
            suggested_books = sample(BOOKS_LIST, 3)
        else:
            suggested_books = [{"title": b.title, "author": b.author} for b in f_resp.books]

    # Enqueue the order in the OrderQueue.
    item_count = len(req_data.get("items", []))
    priority = 1 if item_count > 2 else 5
    queue_response = enqueue_order(order_id, req_data, priority)
    if queue_response.success:
        print(f"[Orchestrator] Order {order_id} enqueued successfully (priority={priority}).")
    else:
        print(f"[Orchestrator] Failed to enqueue order {order_id}: {queue_response.message}")

    broadcast_clear(order_id, local_vc)

    # IMPORTANT: Return status exactly "Order Approved" so that frontend shows green.
    return jsonify({
        "orderId": order_id,
        "status": "Order Approved",
        "suggestedBooks": suggested_books
    })

def init_in_all_services(order_id, data):
    """
    Calls InitOrder in each microservice to cache data & initialize vector clocks.
    """
    with grpc.insecure_channel(GRPC_SERVICES["transaction_verification"]) as ch:
        stub = tx_grpc.TransactionVerificationStub(ch)
        stub.InitOrder(tx_pb.OrderInitRequest(order_id=order_id, order_data=json.dumps(data)))
    with grpc.insecure_channel(GRPC_SERVICES["fraud_detection"]) as ch:
        stub = fraud_grpc.FraudDetectionStub(ch)
        stub.InitOrder(fraud_pb.OrderInitRequest(order_id=order_id, order_data=json.dumps(data)))
    with grpc.insecure_channel(GRPC_SERVICES["suggestions"]) as ch:
        stub = sugg_grpc.BookSuggestionsStub(ch)
        stub.InitOrder(sugg_pb.OrderInitRequest(order_id=order_id, order_data=json.dumps(data)))

def broadcast_clear(order_id, final_vc):
    """
    Broadcasts a ClearOrder message to all services with the final vector clock.
    """
    print(f"[Orchestrator] Broadcasting ClearOrder({order_id}) with final VC={final_vc}")
    try:
        stub = get_transaction_stub()
        req = tx_pb.ClearOrderRequest(order_id=order_id, final_vc=final_vc)
        resp = stub.ClearOrder(req)
        print(f"  [Transaction] Clear => success={resp.success}, msg={resp.message}")
    except Exception as e:
        print(f"  [Transaction] Error in ClearOrder: {e}")
    try:
        stub = get_fraud_stub()
        req = fraud_pb.ClearOrderRequest(order_id=order_id, final_vc=final_vc)
        resp = stub.ClearOrder(req)
        print(f"  [Fraud] Clear => success={resp.success}, msg={resp.message}")
    except Exception as e:
        print(f"  [Fraud] Error in ClearOrder: {e}")
    try:
        stub = get_suggestions_stub()
        req = sugg_pb.ClearOrderRequest(order_id=order_id, final_vc=final_vc)
        resp = stub.ClearOrder(req)
        print(f"  [Suggestions] Clear => success={resp.success}, msg={resp.message}")
    except Exception as e:
        print(f"  [Suggestions] Error in ClearOrder: {e}")

    if order_id in orders:
        del orders[order_id]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
