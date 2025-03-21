import sys
import os
import grpc
import json
import logging
import openai
from concurrent import futures

# Import gRPC stubs
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
suggestions_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/suggestions'))
sys.path.insert(0, suggestions_grpc_path)
import suggestions_pb2 as suggestions
import suggestions_pb2_grpc as suggestions_grpc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Load OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY", "")

def extract_clean_json_array(text: str) -> str:
    text = text.replace("```", "")
    start = text.find('[')
    end = text.rfind(']')
    return text[start:end+1].strip() if start != -1 and end > start else text.strip()

def call_openai_for_book_suggestions(num_books: int) -> list[dict]:
    prompt = (
        f"Please suggest {num_books} book{'s' if num_books != 1 else ''}. "
        "Return **only** a JSON array of objects, each with “title” and “author”."
    )
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful book recommendation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200,
        )
        raw = resp.choices[0].message["content"]
        logging.info("Raw AI reply: %s", raw)
        arr = extract_clean_json_array(raw)
        books = json.loads(arr)
        return books if isinstance(books, list) else [books]
    except Exception as e:
        logging.error("OpenAI call failed (%s); falling back to static list", e)
        # Fallback: static sample
        from random import sample
        from __main__ import BOOKS_LIST
        k = min(num_books, len(BOOKS_LIST))
        return [{"title": b["title"], "author": b["author"]} for b in sample(BOOKS_LIST, k)]

class BookSuggestionsService(suggestions_grpc.BookSuggestionsServicer):
    def GetSuggestions(self, request, context):
        logging.info("Request for %d book suggestions", request.num_books)
        ai_suggestions = call_openai_for_book_suggestions(request.num_books)
        response = suggestions.BookSuggestionsResponse()
        response.books.extend([
            suggestions.Book(title=b.get("title","Unknown"), author=b.get("author","Unknown"))
            for b in ai_suggestions
        ])
        logging.info("Returning suggestions: %s", ai_suggestions)
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    suggestions_grpc.add_BookSuggestionsServicer_to_server(BookSuggestionsService(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    logging.info("Book Suggestions Server started. Listening on port 50053.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
