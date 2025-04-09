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
import transaction_verification_pb2 as transaction_pb
import transaction_verification_pb2_grpc as transaction_grpc


# --------------------------------------------------------------------
# A helper to merge and increment vector clocks.
# We'll assume transaction-verification service has index 0 in the VC.
# --------------------------------------------------------------------
SVC_IDX = 0  # transaction-verification is index 0
def merge_and_increment(local_vc, incoming_vc):
    for i in range(len(local_vc)):
        local_vc[i] = max(local_vc[i], incoming_vc[i])
    local_vc[SVC_IDX] += 1
    return local_vc


# --------------------------------------------------------------------
# In-memory store: orders[order_id] = {
#    'data': {...},          # the JSON order data
#    'vc': [0,0,0]           # the local vector clock for this order
# }
# --------------------------------------------------------------------
orders = {}

class TransactionVerificationService(transaction_grpc.TransactionVerificationServicer):
    def InitOrder(self, request, context):
        """
        Caches the order data and initializes the vector clock to [0,0,0].
        """
        order_id = request.order_id
        orders[order_id] = {
            'data': json.loads(request.order_data),
            'vc': [0,0,0]
        }
        print(f"[TransactionSvc] InitOrder {order_id} => VC={orders[order_id]['vc']}")
        return transaction_pb.OrderInitResponse(success=True, message='Order initialized')

    def VerifyItems(self, request, context):
        """
        Event (a): Checks if the items list is not empty.
        Merges incoming VC -> increments -> returns updated VC.
        """
        order_id = request.order_id
        incoming_vc = list(request.vector_clock)  # repeated int in proto => list in Python
        if order_id not in orders:
            return transaction_pb.OrderEventResponse(
                success=False,
                message="Order not found in transaction-verification",
                updated_vc=incoming_vc
            )

        local_vc = orders[order_id]['vc']
        # merge and increment
        updated_vc = merge_and_increment(local_vc, incoming_vc)

        # Dummy check
        data = orders[order_id]['data']
        items = data.get("items", [])
        if not items:
            print(f"[TransactionSvc] VerifyItems FAIL => no items, VC={updated_vc}")
            return transaction_pb.OrderEventResponse(
                success=False,
                message="Items list is empty!",
                updated_vc=updated_vc
            )
        else:
            print(f"[TransactionSvc] VerifyItems OK => VC={updated_vc}")
            return transaction_pb.OrderEventResponse(
                success=True,
                message="Items verified.",
                updated_vc=updated_vc
            )

    def VerifyUserData(self, request, context):
        """
        Event (b): Checks if user data is filled in.
        """
        order_id = request.order_id
        incoming_vc = list(request.vector_clock)
        if order_id not in orders:
            return transaction_pb.OrderEventResponse(
                success=False,
                message="Order not found",
                updated_vc=incoming_vc
            )

        local_vc = orders[order_id]['vc']
        updated_vc = merge_and_increment(local_vc, incoming_vc)

        data = orders[order_id]['data']
        user = data.get("user", {})
        if not user.get("name") or not user.get("contact") or not user.get("address"):
            print(f"[TransactionSvc] VerifyUserData FAIL => incomplete user data, VC={updated_vc}")
            return transaction_pb.OrderEventResponse(
                success=False,
                message="User data is incomplete!",
                updated_vc=updated_vc
            )
        print(f"[TransactionSvc] VerifyUserData OK => VC={updated_vc}")
        return transaction_pb.OrderEventResponse(
            success=True,
            message="User data verified.",
            updated_vc=updated_vc
        )

    def VerifyCreditCard(self, request, context):
        """
        Event (c): Checks if CC number is the correct format (e.g., 16 digits).
        """
        order_id = request.order_id
        incoming_vc = list(request.vector_clock)
        if order_id not in orders:
            return transaction_pb.OrderEventResponse(
                success=False,
                message="Order not found",
                updated_vc=incoming_vc
            )

        local_vc = orders[order_id]['vc']
        updated_vc = merge_and_increment(local_vc, incoming_vc)

        data = orders[order_id]['data']
        cc_number = data.get("creditCard", {}).get("number", "")
        if len(cc_number) != 16:
            print(f"[TransactionSvc] VerifyCreditCard FAIL => invalid CC, VC={updated_vc}")
            return transaction_pb.OrderEventResponse(
                success=False,
                message="Invalid credit card number. Must be 16 digits.",
                updated_vc=updated_vc
            )
        print(f"[TransactionSvc] VerifyCreditCard OK => VC={updated_vc}")
        return transaction_pb.OrderEventResponse(
            success=True,
            message="Credit Card format OK.",
            updated_vc=updated_vc
        )

    def ClearOrder(self, request, context):
        """
        The orchestrator broadcasts a final VC for the order.
        If local VC <= final VC, we can safely clear the data.
        """
        order_id = request.order_id
        final_vc = list(request.final_vc)
        if order_id not in orders:
            return transaction_pb.ClearOrderResponse(
                success=False,
                message="Order not found in transaction-verification."
            )

        local_vc = orders[order_id]['vc']
        # check if local_vc <= final_vc in every component
        can_clear = all(local_vc[i] <= final_vc[i] for i in range(len(local_vc)))
        if can_clear:
            del orders[order_id]
            print(f"[TransactionSvc] ClearOrder => {order_id} removed successfully.")
            return transaction_pb.ClearOrderResponse(success=True, message="Order cleared.")
        else:
            print(f"[TransactionSvc] ClearOrder => local VC {local_vc} > final VC {final_vc}, ERROR.")
            return transaction_pb.ClearOrderResponse(
                success=False,
                message="Local VC is ahead of final VC => cannot clear order yet."
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    transaction_grpc.add_TransactionVerificationServicer_to_server(
        TransactionVerificationService(), server
    )
    server.add_insecure_port('[::]:50052')
    server.start()
    print('Transaction Verification Server started on port 50052.')
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
