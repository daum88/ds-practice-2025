from concurrent import futures
import random
import threading
import grpc
import os
import sys

from google.protobuf.empty_pb2 import Empty

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
payment_grpc_path = os.path.abspath(os.path.join(FILE, "../../../utils/pb/payment"))
sys.path.insert(0, payment_grpc_path)

import payment_pb2 as payment
import payment_pb2_grpc as payment_grpc

class PaymentService(payment_grpc.PaymentServiceServicer):
    """
    A dummy payment service that supports 2PC:
      - PreparePayment: check & reserve funds
      - FinalizePayment: either commit (abort=False) or abort (abort=True)
    """
    def __init__(self):
        # Keep track of prepared payments: id -> PreparePaymentRequest
        self._lock = threading.Lock()
        self._prepared = {}

    def PreparePayment(self, request: payment.PreparePaymentRequest, context):
        """Phase 1: decide whether we can do the payment."""
        # simulate a 10% random failure
        ok = random.random() > 0.1
        with self._lock:
            if ok:
                self._prepared[request.id] = request
        print(f"[Payment] Prepare {request.id}: {'OK' if ok else 'REJECT'} "
              f"for user {request.user_name} ({request.user_contact}) "
              f"amount={request.amount}")
        return payment.PreparePaymentResponse(ready=ok)

    def FinalizePayment(self, request: payment.FinalizePaymentRequest, context):
        """Phase 2: commit or abort the payment."""
        with self._lock:
            prep = self._prepared.pop(request.id, None)

        if prep is None:
            # never prepared (or already finalized)
            print(f"[Payment] Finalize {request.id}: no prior prepare, treating as abort")
        elif request.abort:
            print(f"[Payment] Abort   {request.id}: rolling back for user {prep.user_name}")
        else:
            # here you would charge the card, send receipt, etc.
            print(f"[Payment] Commit  {request.id}: charging user {prep.user_name}")

        return Empty()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    payment_grpc.add_PaymentServiceServicer_to_server(PaymentService(), server)
    port = 50055
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"[Payment] gRPC server listening on {port}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
