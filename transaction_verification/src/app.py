import sys
import os
import re

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
transaction_verification_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/transaction_verification'))
sys.path.insert(0, transaction_verification_grpc_path)
import transaction_verification_pb2 as transaction_verification
import transaction_verification_pb2_grpc as transaction_verification_grpc


import grpc
from concurrent import futures

class TransactionVerificationService(transaction_verification_grpc.TransactionVerificationServicer):
    def ValidateTransaction(self, request, context):
        response = transaction_verification.TransactionValidationResponse()

        # Print received transaction data for debugging
        print("🚀 Received Transaction Data:")
        print(request)

        errors = []

        # Check if transaction has items
        if not request.items:
            errors.append("❌ Transaction must contain at least one item.")

        # Check if user data is provided
        if not request.user.name:
            errors.append("❌ User name is required.")
        if not request.user.contact:
            errors.append("❌ User contact is required.")

        # Check if credit card number is exactly 16 digits
        if len(request.payment.credit_card_number) != 16:
            errors.append("❌ Invalid credit card number. Must be exactly 16 digits.")

        if errors:
            response.valid = False
            response.message = " | ".join(errors)  # Combine errors
            print("🔥 Validation Failed:", response.message)
            return response

        response.valid = True
        response.message = "✅ Transaction is valid."
        print("✅ Validation Passed:", response.message)
        return response


    '''def is_valid_credit_card(self, credit_card_number):
        credit_card_number = re.sub(r'\D', '', credit_card_number)  # Remove non-digit characters
        if not credit_card_number:
            return False
        
        total = 0
        num_digits = len(credit_card_number)
        odd_even = num_digits & 1
        
        for i in range(num_digits):
            digit = int(credit_card_number[i])
            if (i & 1) ^ odd_even:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        
        return (total % 10) == 0 '''

def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    transaction_verification_grpc.add_TransactionVerificationServicer_to_server(TransactionVerificationService(), server)
    # Listen on port 50052
    port = "50052"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Transaction Verification Server started. Listening on port 50052.")
    # Keep thread alive
    server.wait_for_termination()

if __name__ == '__main__':
    serve()