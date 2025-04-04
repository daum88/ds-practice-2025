import json
import grpc
import sys
import os
import re
import grpc
from concurrent import futures
# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
transaction_verification_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/transaction_verification'))
sys.path.insert(0, transaction_verification_grpc_path)
import transaction_verification_pb2 as transaction_verification
import transaction_verification_pb2_grpc as transaction_verification_grpc

# In-memory store for orders
orders = {}

class TransactionVerificationService(transaction_verification_grpc.TransactionVerificationServicer):
    def InitOrder(self, request, context):
        orders[request.order_id] = {
            'data': json.loads(request.order_data),
            'vector_clock': {'transaction_verification': 1}
        }
        print(f"Initialized order {request.order_id} with vector clock {orders[request.order_id]['vector_clock']}")
        return transaction_verification.OrderInitResponse(success=True, message='Order initialized')

    def ValidateTransaction(self, request, context):
        response = transaction_verification.TransactionValidationResponse()
        errors = []

        if not request.items:
            errors.append('❌ Transaction must contain at least one item.')
        if not request.user.name:
            errors.append('❌ User name is required.')
        if not request.user.contact:
            errors.append('❌ User contact is required.')
        if len(request.payment.credit_card_number) != 16:
            errors.append('❌ Invalid credit card number. Must be exactly 16 digits.')

        # Update vector clock
        if request.order_id in orders:
            orders[request.order_id]['vector_clock']['transaction_verification'] += 1
            print(f"Vector clock updated for {request.order_id}: {orders[request.order_id]['vector_clock']}")

        if errors:
            response.valid = False
            response.message = ' | '.join(errors)
            print('🔥 Validation Failed:', response.message)
        else:
            response.valid = True
            response.message = '✅ Transaction is valid.'
            print('Validation Passed:', response.message)
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    transaction_verification_grpc.add_TransactionVerificationServicer_to_server(TransactionVerificationService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print('Transaction Verification Server started on port 50052.')
    server.wait_for_termination()

if __name__ == '__main__':
    serve()