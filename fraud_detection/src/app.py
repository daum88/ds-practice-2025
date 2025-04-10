import sys
import os
import json
import random
import grpc
from concurrent import futures

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)

import fraud_detection_pb2 as fraud_pb
import fraud_detection_pb2_grpc as fraud_grpc

# --------------------------------------------------------------------
# Helper for vector clock merging.
# We'll assume Fraud-Detection service is index 1 in the VC.
# --------------------------------------------------------------------
SVC_IDX = 1
def merge_and_increment(local_vc, incoming_vc):
    for i in range(len(local_vc)):
        local_vc[i] = max(local_vc[i], incoming_vc[i])
    local_vc[SVC_IDX] += 1
    return local_vc


# --------------------------------------------------------------------
# In-memory store of orders:
# orders[order_id] = {
#    'data': {...},
#    'vc': [0,0,0]
# }
# --------------------------------------------------------------------
orders = {}

class FraudDetectionService(fraud_grpc.FraudDetectionServicer):
    def InitOrder(self, request, context):
        order_id = request.order_id
        orders[order_id] = {
            'data': json.loads(request.order_data),
            'vc': [0,0,0]
        }
        print(f"[FraudSvc] InitOrder {order_id} => VC={orders[order_id]['vc']}")
        return fraud_pb.OrderInitResponse(success=True, message='Order initialized')

    def CheckUserData(self, request, context):
        """
        Event (d): Fraud check on user data.
        We'll do some silly check like if username is "fraud" => fail.
        """
        order_id = request.order_id
        incoming_vc = list(request.vector_clock)
        if order_id not in orders:
            return fraud_pb.OrderEventResponse(
                success=False,
                message="Order not found in fraud-detection",
                updated_vc=incoming_vc
            )

        local_vc = orders[order_id]['vc']
        updated_vc = merge_and_increment(local_vc, incoming_vc)

        data = orders[order_id]['data']
        user = data.get("user", {})
        if user.get("name", "").lower() == "fraud":
            print(f"[FraudSvc] CheckUserData FAIL => user name suspicious, VC={updated_vc}")
            return fraud_pb.OrderEventResponse(
                success=False,
                message="User data flagged as fraudulent (name=fraud).",
                updated_vc=updated_vc
            )
        print(f"[FraudSvc] CheckUserData OK => VC={updated_vc}")
        return fraud_pb.OrderEventResponse(
            success=True,
            message="User data is not fraudulent.",
            updated_vc=updated_vc
        )

    def CheckCreditCard(self, request, context):
        """
        Event (e): Fraud check on credit card. 
        We'll do silly checks (random or amount-based).
        """
        order_id = request.order_id
        incoming_vc = list(request.vector_clock)
        if order_id not in orders:
            return fraud_pb.OrderEventResponse(
                success=False,
                message="Order not found",
                updated_vc=incoming_vc
            )

        local_vc = orders[order_id]['vc']
        updated_vc = merge_and_increment(local_vc, incoming_vc)

        data = orders[order_id]['data']
        amount = data.get("amount", 0)
        # random "fraud" or large amounts
        if amount > 1000 or random.random() < 0.1:
            print(f"[FraudSvc] CheckCreditCard FAIL => flagged as fraudulent, VC={updated_vc}")
            return fraud_pb.OrderEventResponse(
                success=False,
                message="Credit card data flagged as fraudulent (random).",
                updated_vc=updated_vc
            )
        print(f"[FraudSvc] CheckCreditCard OK => VC={updated_vc}")
        return fraud_pb.OrderEventResponse(
            success=True,
            message="Credit card is not fraudulent.",
            updated_vc=updated_vc
        )

    def ClearOrder(self, request, context):
        """
        Final broadcast from orchestrator to clear local data if local VC <= final VC.
        """
        order_id = request.order_id
        final_vc = list(request.final_vc)
        if order_id not in orders:
            return fraud_pb.ClearOrderResponse(
                success=False,
                message="Order not found in fraud-detection."
            )
        local_vc = orders[order_id]['vc']
        can_clear = all(local_vc[i] <= final_vc[i] for i in range(len(local_vc)))
        if can_clear:
            del orders[order_id]
            print(f"[FraudSvc] ClearOrder => {order_id} removed successfully.")
            return fraud_pb.ClearOrderResponse(success=True, message="Order cleared.")
        else:
            print(f"[FraudSvc] ClearOrder => local VC {local_vc} > final VC {final_vc}, ERROR.")
            return fraud_pb.ClearOrderResponse(
                success=False,
                message="Local VC is ahead of final VC => cannot clear order yet."
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    fraud_grpc.add_FraudDetectionServicer_to_server(FraudDetectionService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Fraud Detection Server started on port 50051.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()