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
import suggestions_pb2 as suggestions
import suggestions_pb2_grpc as suggestions_grpc

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# In-memory store for caching orders and tracking vector clocks
orders = {}

class BookSuggestionsService(suggestions_grpc.BookSuggestionsServicer):
    def InitOrder(self, request, context):
        orders[request.order_id] = {
            'data': json.loads(request.order_data),
            'vector_clock': {'suggestions': 1}
        }
        logging.info(f"Initialized order {request.order_id} with vector clock {orders[request.order_id]['vector_clock']}")
        return suggestions.OrderInitResponse(success=True, message='Order initialized')

    def GetSuggestions(self, request, context):
        order_id = request.order_id
        if order_id in orders:
            orders[order_id]['vector_clock']['suggestions'] += 1
            logging.info(f"Vector clock for {order_id}: {orders[order_id]['vector_clock']}")
        else:
            logging.warning(f"GetSuggestions called for uninitialized order {order_id}")

        # Existing suggestion logic
        try:
            prompt = f"Please suggest {request.num_books} book{'s' if request.num_books != 1 else ''}. Return only a JSON array of objects with title and author."
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful book recommendation assistant."}, {"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            raw = resp.choices[0].message["content"].replace('```', '').strip()
            books = json.loads(raw[raw.find('['):raw.rfind(']')+1])
        except Exception as e:
            logging.error(f"AI suggestions failed ({e}); falling back to static list")
            from random import sample
            from __main__ import BOOKS_LIST
            books = [ {"title": b['title'], "author": b['author']} for b in sample(BOOKS_LIST, min(request.num_books, len(BOOKS_LIST))) ]

        response = suggestions.BookSuggestionsResponse()
        response.books.extend([suggestions.Book(title=b['title'], author=b['author']) for b in books])
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    suggestions_grpc.add_BookSuggestionsServicer_to_server(BookSuggestionsService(), server)
    server.add_insecure_port('[::]:50053')
    server.start()
    logging.info("Book Suggestions Server started on port 50053.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

