import sys
import os
import json
import grpc
import logging
from concurrent import futures

# Import the OpenAI client library
import openai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Ensure the shared pb directory is on the sys.path
base_pb = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../utils/pb"))
sys.path.append(base_pb)

import suggestions_pb2 as suggest_pb
import suggestions_pb2_grpc as suggest_grpc

# Retrieve OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY", "")

def extract_clean_json_array(text):
    """
    Removes any triple backticks from the text and extracts the JSON array by finding
    the first '[' and the last ']'.
    """
    # Remove all occurrences of triple backticks
    text_no_ticks = text.replace("```", "")
    # Find the first occurrence of '[' and the last occurrence of ']'
    start = text_no_ticks.find('[')
    end = text_no_ticks.rfind(']')
    if start != -1 and end != -1 and end > start:
        return text_no_ticks[start:end+1].strip()
    return text_no_ticks.strip()

def call_openai_for_suggestions(order_data):
    """
    Calls the OpenAI ChatCompletion API to generate personalized book suggestions
    based on the user's order data. It extracts a JSON array from the response and
    returns it as a list of suggestion objects.
    """
    user = order_data.get("user", {})
    user_name = user.get("name", "User")
    items = order_data.get("items", [])

    # Create a string describing the items
    item_descriptions = ", ".join(
        f"{item.get('quantity', 1)}x {item.get('name', 'Unknown')}" for item in items
    )

    prompt = (
        f"The user named {user_name} has these items in their cart: {item_descriptions}. "
        "Based on these items, suggest 2 to 3 books that might complement the user's interests. "
        "Return ONLY a JSON array of objects, where each object has 'bookId', 'title', and 'author'."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI that recommends books."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200,
        )
        assistant_reply = response.choices[0].message["content"].strip()
        logging.info("Raw AI reply: %s", assistant_reply)

        # Use our new extraction function to get a clean JSON array string
        json_array_text = extract_clean_json_array(assistant_reply)
        logging.info("Extracted JSON text: %s", json_array_text)

        try:
            suggestions = json.loads(json_array_text)
            # Ensure suggestions is a list
            if not isinstance(suggestions, list):
                suggestions = [suggestions]
        except json.JSONDecodeError:
            logging.warning("Extracted text is not valid JSON. Using fallback.")
            suggestions = [{
                "bookId": "UNKNOWN",
                "title": assistant_reply,
                "author": "AI Generated"
            }]
        return suggestions
    except Exception as e:
        logging.error(f"OpenAI API call failed: {e}")
        # Fallback to a static suggestion if the API call fails
        return [{"bookId": "001", "title": "Static Fallback Book", "author": "System"}]

class SuggestionsServicer(suggest_grpc.SuggestionsServicer):
    def GetSuggestions(self, request, context):
        """
        AI-based suggestions service endpoint.
        Receives order data, calls the AI API for personalized suggestions,
        cleans the response, and returns the results as a JSON string.
        """
        order_data = json.loads(request.order_json)
        logging.info("Received order data for suggestions: %s", order_data)
        suggestions = call_openai_for_suggestions(order_data)
        logging.info("Final suggestions: %s", suggestions)
        return suggest_pb.SuggestionsResponse(suggestions_json=json.dumps(suggestions))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    suggest_grpc.add_SuggestionsServicer_to_server(SuggestionsServicer(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    logging.info("Suggestions Service running on port 50053 (AI-based)")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
