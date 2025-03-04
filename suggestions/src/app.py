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


# Static list of books with authors
BOOKS_LIST = [
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"title": "1984", "author": "George Orwell"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"title": "Moby Dick", "author": "Herman Melville"},
    {"title": "Pride and Prejudice", "author": "Jane Austen"},
    {"title": "War and Peace", "author": "Leo Tolstoy"},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger"},
    {"title": "The Lord of the Rings", "author": "J.R.R. Tolkien"},
    {"title": "Harry Potter Series", "author": "J.K. Rowling"},
    {"title": "Brave New World", "author": "Aldous Huxley"},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien"},
    {"title": "Fahrenheit 451", "author": "Ray Bradbury"},
    {"title": "Crime and Punishment", "author": "Fyodor Dostoevsky"},
    {"title": "The Odyssey", "author": "Homer"}
]

class BookSuggestionsService(suggestions_grpc.BookSuggestionsServicer):
    def GetSuggestions(self, request, context):
        response = suggestions.BookSuggestionsResponse()
        print("Getting Book suggestions...")
        num_suggestions = min(request.num_books, len(BOOKS_LIST))
        selected_books = random.sample(BOOKS_LIST, k=num_suggestions)
        print(f"Books suggestions: {selected_books}")
        response.books.extend([
            suggestions.Book(title=book["title"], author=book["author"]) for book in selected_books
        ])
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
