import sys
import os
import json
import grpc
import logging
from concurrent import futures

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Append the shared pb directory and the fraud_detection subdirectory.
base_pb = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../utils/pb"))
sys.path.append(base_pb)
sys.path.append(os.path.join(base_pb, "fraud_detection"))

from fraud_detection import fraud_detection_pb2 as fraud_pb
from fraud_detection import fraud_detection_pb2_grpc as fraud_grpc

def luhn_check(card_number):
    """
    Perform a Luhn algorithm check to validate the credit card number.
    Returns True if the card number is valid, False otherwise.
    """
    total = 0
    reverse_digits = card_number[::-1]
    for i, d in enumerate(reverse_digits):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

class FraudDetectionServicer(fraud_grpc.FraudDetectionServicer):
    def CheckFraud(self, request, context):
        """
        Implements the CheckFraud gRPC method.
        The order is flagged as fraudulent if any of the following conditions are met:
          1. The user's name contains "risky".
          2. The credit card number is not exactly 16 digits or is non-numeric.
          3. The credit card number fails the Luhn algorithm check.
          4. The total quantity of items in the order exceeds 10.
        """
        order_data = json.loads(request.order_json)

        # Extract user data
        user = order_data.get("user", {})
        name = user.get("name", "")

        # Check if user's name contains "risky"
        if "risky" in name.lower():
            logging.info(f"Fraud detected: User name '{name}' contains 'risky'.")
            return fraud_pb.FraudResponse(is_fraudulent=True)

        # Extract credit card details
        credit_card = order_data.get("creditCard", {})
        card_number = credit_card.get("number", "")

        # Check if credit card number is exactly 16 digits and numeric
        if len(card_number) != 16 or not card_number.isdigit():
            logging.info(f"Fraud detected: Credit card number '{card_number}' is invalid.")
            return fraud_pb.FraudResponse(is_fraudulent=True)

        # Validate credit card number using the Luhn algorithm
        if not luhn_check(card_number):
            logging.info(f"Fraud detected: Credit card number '{card_number}' failed Luhn check.")
            return fraud_pb.FraudResponse(is_fraudulent=True)

        # Check total quantity of items; if over 10, flag as suspicious
        items = order_data.get("items", [])
        total_quantity = sum(item.get("quantity", 0) for item in items)
        if total_quantity > 10:
            logging.info(f"Fraud detected: Total item quantity {total_quantity} exceeds limit.")
            return fraud_pb.FraudResponse(is_fraudulent=True)

        logging.info(f"No fraud detected for user '{name}'.")
        return fraud_pb.FraudResponse(is_fraudulent=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    fraud_grpc.add_FraudDetectionServicer_to_server(FraudDetectionServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    logging.info("Fraud Detection Service running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
