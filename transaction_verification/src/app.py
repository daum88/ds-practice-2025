import sys
import os
import json
import grpc
import logging
from concurrent import futures

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

base_pb = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../utils/pb"))
sys.path.append(base_pb)

import transaction_verification_pb2 as txn_pb
import transaction_verification_pb2_grpc as txn_grpc

class TransactionVerificationServicer(txn_grpc.TransactionVerificationServicer):
    def VerifyTransaction(self, request, context):
        """
        Validates the transaction based on the order data.
        Returns valid if there is at least one item.
        """
        order_data = json.loads(request.order_json)
        is_valid = bool(order_data.get("items"))
        logging.info(f"Transaction verification result: {is_valid}")
        return txn_pb.TransactionResponse(is_valid=is_valid)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    txn_grpc.add_TransactionVerificationServicer_to_server(TransactionVerificationServicer(), server)
    server.add_insecure_port("[::]:50052")
    server.start()
    logging.info("Transaction Verification Service running on port 50052")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
