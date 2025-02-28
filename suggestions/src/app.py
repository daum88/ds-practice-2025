import sys
import os
import json
import grpc
import logging
from concurrent import futures

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

base_pb = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../utils/pb"))
sys.path.append(base_pb)

import suggestions_pb2 as suggest_pb
import suggestions_pb2_grpc as suggest_grpc

class SuggestionsServicer(suggest_grpc.SuggestionsServicer):
    def GetSuggestions(self, request, context):
        """
        Returns a list of book suggestions.
        This is dummy logic; in a real system, an AI or heuristic would generate suggestions.
        """
        suggestions = [{"bookId": "001", "title": "New Book", "author": "AI Author"}]
        logging.info(f"Suggestions generated: {suggestions}")
        return suggest_pb.SuggestionsResponse(suggestions_json=json.dumps(suggestions))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    suggest_grpc.add_SuggestionsServicer_to_server(SuggestionsServicer(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    logging.info("Suggestions Service running on port 50053")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
