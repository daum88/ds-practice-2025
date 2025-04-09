import sys
import os
import json
import grpc
import logging
import openai
from concurrent import futures

# Import gRPC stubs
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
suggestions_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/suggestions'))
sys.path.insert(0, suggestions_grpc_path)

import suggestions_pb2 as suggestions_pb
import suggestions_pb2_grpc as suggestions_grpc

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# We'll assume Suggestions service is index 2 in the VC.
SVC_IDX = 2
def merge_and_increment(local_vc, incoming_vc):
    for i in range(len(local_vc)):
        local_vc[i] = max(local_vc[i], incoming_vc[i])
    local_vc[SVC_IDX] += 1
    return local_vc

orders = {}

<<<<<<< Updated upstream
class BookSuggestionsService(suggestions_grpc.BookSuggestionsServicer):
    def InitOrder(self, request, context):
        orders[request.order_id] = {
            'data': json.loads(request.order_data),
            'vector_clock': {'suggestions': 1}
        }
        logging.info(f"Initialized order {request.order_id} with vector clock {orders[request.order_id]['vector_clock']}")
        return suggestions.OrderInitResponse(success=True, message='Order initialized')

    def GetSuggestions(self, request, context):
=======
# Fallback static list
BOOKS_LIST = [
    {"title": "1984", "author": "George Orwell"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"title": "Pride and Prejudice", "author": "Jane Austen"},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger"}
]

class BookSuggestionsService(suggestions_grpc.BookSuggestionsServicer):
    def InitOrder(self, request, context):
>>>>>>> Stashed changes
        order_id = request.order_id
        orders[order_id] = {
            'data': json.loads(request.order_data),
            'vc': [0, 0, 0]
        }
        logging.info(f"[SuggestionsSvc] InitOrder {order_id} => VC={orders[order_id]['vc']}")
        return suggestions_pb.OrderInitResponse(success=True, message='Order initialized')

    def GenerateSuggestions(self, request, context):
        """
        Event (f): produce suggestions for the user’s items or topic.
        """
        order_id = request.order_id
        incoming_vc = list(request.vector_clock)
        if order_id not in orders:
            return suggestions_pb.GenerateSuggestionsResponse(
                success=False,
                message="Order not found in suggestions service",
                updated_vc=incoming_vc,
                books=[]
            )

        local_vc = orders[order_id]['vc']
        updated_vc = merge_and_increment(local_vc, incoming_vc)
        logging.info(f"[SuggestionsSvc] GenerateSuggestions => merged VC={updated_vc}")

        num_books = request.num_books
        try:
            prompt = f"Please suggest {num_books} book(s). Return only a JSON array of objects with title and author."
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful book recommendation assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            raw = resp.choices[0].message["content"].replace('```', '').strip()
            # Parse JSON from the raw string.
            books = json.loads(raw[raw.find('['): raw.rfind(']')+1])
        except Exception as e:
            logging.error(f"AI suggestions failed ({e}); using fallback list.")
            from random import sample
            books = sample(BOOKS_LIST, min(num_books, len(BOOKS_LIST)))

        # Build response using GenerateSuggestionsResponse.
        response = suggestions_pb.GenerateSuggestionsResponse(
            success=True,
            message="Suggestions generated",
            updated_vc=updated_vc
        )
        for b in books:
            bk = suggestions_pb.Book(title=b.get('title', 'Untitled'), author=b.get('author', 'Unknown'))
            response.books.append(bk)
        return response

    def ClearOrder(self, request, context):
        """
        Final broadcast from orchestrator to clear local data if local VC <= final VC.
        """
        order_id = request.order_id
        final_vc = list(request.final_vc)
        if order_id not in orders:
            return suggestions_pb.ClearOrderResponse(
                success=False,
                message="Order not found in suggestions."
            )

        local_vc = orders[order_id]['vc']
        can_clear = all(local_vc[i] <= final_vc[i] for i in range(len(local_vc)))
        if can_clear:
            del orders[order_id]
            logging.info(f"[SuggestionsSvc] ClearOrder => {order_id} removed successfully.")
            return suggestions_pb.ClearOrderResponse(success=True, message="Order cleared.")
        else:
            logging.info(f"[SuggestionsSvc] ClearOrder => local VC {local_vc} > final VC {final_vc}, cannot clear.")
            return suggestions_pb.ClearOrderResponse(
                success=False,
                message="Local VC is ahead of final VC => cannot clear order yet."
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    suggestions_grpc.add_BookSuggestionsServicer_to_server(
        BookSuggestionsService(), server
    )
    server.add_insecure_port('[::]:50053')
    server.start()
    logging.info("Book Suggestions Server started on port 50053.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
