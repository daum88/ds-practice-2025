import sys
import os
import time
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import grpc
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.protobuf.json_format import ParseDict

# OTEL imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient

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

# OpenTelemetry setup
resource = Resource.create({"service.name": "orchestrator"})

# Tracing
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="observability:4317", insecure=True)
    )
)

# Metrics
metric_exporter = OTLPMetricExporter(endpoint="observability:4317", insecure=True)
reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=1000)
metrics.set_meter_provider(MeterProvider(metric_readers=[reader], resource=resource))
meter = metrics.get_meter(__name__)

orders_counter = meter.create_counter(
    name="orchestrator_orders_total",
    description="Total number of checkout requests",
)
order_latency = meter.create_histogram(
    name="orchestrator_order_latency_seconds",
    description="End-to-end processing time per order",
)

# Create Flask app and enable CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

FlaskInstrumentor().instrument_app(app)
GrpcInstrumentorClient().instrument()

# Health endpoint
@app.get("/health")
def health():
    return "ok", 200

# gRPC service addresses
GRPC = {
    "fraud":      "fraud_detection:50051",
    "tx":         "transaction_verification:50052",
    "suggestions":"suggestions:50053",
    "queue":      "order_queue:50054",
}

# Helper to create stubs
def stub(svc_name):
    ch = grpc.insecure_channel(GRPC[svc_name])
    if svc_name == "fraud":
        return fraud_grpc.FraudDetectionStub(ch)
    if svc_name == "tx":
        return tx_grpc.TransactionVerificationStub(ch)
    if svc_name == "suggestions":
        return sugg_grpc.BookSuggestionsStub(ch)
    if svc_name == "queue":
        return queue_grpc.OrderQueueStub(ch)

# Enqueue helper
def enqueue_order(order_id, data, priority):
    stubq = stub("queue")
    req = queue_pb.OrderQueueRequest(
        order_id=order_id,
        priority=priority,
        order_data=json.dumps(data)
    )
    return stubq.Enqueue(req)

# Utility to extract vector clock from response, handling different field names

def extract_clock(resp, default_length):
    if hasattr(resp, 'vector_clock'):
        return list(resp.vector_clock)
    if hasattr(resp, 'vectorClock'):
        return list(resp.vectorClock)
    if hasattr(resp, 'vc'):
        return list(resp.vc)
    # fallback to zeros
    return [0] * default_length

# Orchestration endpoint
@app.route("/checkout", methods=["POST"])
def checkout():
    # metrics and tracing
    orders_counter.add(1)
    start = time.time()

    # generate order ID and payload
    order_id = str(uuid.uuid4())
    payload  = request.get_json(force=True)
    payload["order_id"] = order_id

    # ensure user.address
    billing = payload.get("billingAddress", {})
    user    = payload.setdefault("user", {})
    user.setdefault("address", billing.get("street", "Unknown"))

    # orchestration span
    with tracer.start_as_current_span("orchestrate_checkout") as span:
        span.set_attribute("order.id", order_id)

        # Init across services (no clock on init)
        services = ("tx", "fraud", "suggestions")
        for svc in services:
            try:
                init_req = {
                    "order_id": order_id,
                    "order_data": json.dumps(payload)
                }
                if svc == "tx":
                    stub("tx").InitOrder(tx_pb.OrderInitRequest(**init_req))
                elif svc == "fraud":
                    stub("fraud").InitOrder(fraud_pb.OrderInitRequest(**init_req))
                else:
                    stub("suggestions").InitOrder(sugg_pb.OrderInitRequest(**init_req))
            except Exception as e:
                span.record_exception(e)
                return jsonify({"error": f"init {svc} failed"}), 500

        # initial zero vector clock
        vc = [0] * len(services)

        # 1) VerifyItems & VerifyUserData in parallel
        pool = ThreadPoolExecutor(max_workers=2)
        fut_items = pool.submit(lambda: stub("tx").VerifyItems(
            tx_pb.OrderEventRequest(order_id=order_id, vector_clock=vc)
        ))
        fut_udata = pool.submit(lambda: stub("tx").VerifyUserData(
            tx_pb.OrderEventRequest(order_id=order_id, vector_clock=vc)
        ))

        res_items = fut_items.result()
        res_udata = fut_udata.result()
        a_ok, b_ok = res_items.success, res_udata.success
        ci = extract_clock(res_items, len(services))
        cu = extract_clock(res_udata, len(services))
        vc = [max(ci[i], cu[i]) for i in range(len(services))]

        if not (a_ok and b_ok):
            span.set_attribute("orchestrator.status", "early_abort")
            return jsonify({"orderId": order_id, "status": "Failed early"}), 400

        # 2) VerifyCreditCard
        res_credit = stub("tx").VerifyCreditCard(
            tx_pb.OrderEventRequest(order_id=order_id, vector_clock=vc)
        )
        cc = extract_clock(res_credit, len(services))
        vc = [max(vc[i], cc[i]) for i in range(len(services))]
        if not res_credit.success:
            span.set_attribute("orchestrator.status", "tx_fail")
            return jsonify({"orderId": order_id, "status": "Payment data invalid"}), 400

        # 3) CheckUserData (fraud)
        res_fraud_udata = stub("fraud").CheckUserData(
            fraud_pb.OrderEventRequest(order_id=order_id, vector_clock=vc)
        )
        cd = extract_clock(res_fraud_udata, len(services))
        vc = [max(vc[i], cd[i]) for i in range(len(services))]
        if not res_fraud_udata.success:
            span.set_attribute("orchestrator.status", "fraud_fail")
            return jsonify({"orderId": order_id, "status": "Fraud detected"}), 400

        # 4) CheckCreditCard (fraud)
        res_fraud_cc = stub("fraud").CheckCreditCard(
            fraud_pb.OrderEventRequest(order_id=order_id, vector_clock=vc)
        )
        ce = extract_clock(res_fraud_cc, len(services))
        vc = [max(vc[i], ce[i]) for i in range(len(services))]
        if not res_fraud_cc.success:
            span.set_attribute("orchestrator.status", "fraud_cc_fail")
            return jsonify({"orderId": order_id, "status": "Fraud CC fail"}), 400

        # 5) GenerateSuggestions
        try:
            sreq = sugg_pb.GenerateSuggestionsRequest(
                order_id=order_id,
                num_books=3,
                vector_clock=vc
            )
            sres = stub("suggestions").GenerateSuggestions(sreq)
            cb = extract_clock(sres, len(services))
            vc = [max(vc[i], cb[i]) for i in range(len(services))]
            books = [{"title": b.title, "author": b.author} for b in sres.books]
        except Exception:
            books = []

        # 6) Enqueue Order
        prio = 1 if len(payload.get("items", [])) > 2 else 5
        qres = enqueue_order(order_id, payload, prio)
        span.set_attribute("orchestrator.enqueue_success", qres.success)

        span.set_attribute("orchestrator.status", "approved")
        result = {"orderId": order_id, "status": "Order Approved", "suggestedBooks": books}

    # record latency
    order_latency.record(time.time() - start, {"status": result["status"]})
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
