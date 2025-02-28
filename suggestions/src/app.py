import sys
import os
import grpc
from concurrent import futures
import random

# Import gRPC stubs
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
suggestions_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/suggestions'))
sys.path.insert(0, suggestions_grpc_path)
import suggestions_pb2 as suggestions
import suggestions_pb2_grpc as suggestions_grpc

# Static list of books
BOOKS_LIST = [
    "The Great Gatsby", "1984", "To Kill a Mockingbird", "Moby Dick", "Pride and Prejudice",
    "War and Peace", "The Catcher in the Rye", "The Lord of the Rings", "Harry Potter Series",
    "Brave New World", "The Hobbit", "Fahrenheit 451", "Crime and Punishment", "The Odyssey"
]

class BookSuggestionsService(suggestions_grpc.BookSuggestionsServicer):
    def GetSuggestions(self, request, context):
        response = suggestions.BookSuggestionsResponse()
        num_suggestions = min(request.num_books, len(BOOKS_LIST))
        response.books.extend(random.sample(BOOKS_LIST, num_suggestions))
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    suggestions_grpc.add_BookSuggestionsServicer_to_server(BookSuggestionsService(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    print("Book Suggestions Server started. Listening on port 50053.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
