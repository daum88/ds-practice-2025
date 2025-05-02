
import grpc
import os
import sys
from concurrent import futures
import threading
import json
from google.protobuf.empty_pb2 import Empty

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
books_db_grpc_path     = os.path.abspath(os.path.join(FILE, "../../../utils/pb/books_database"))

sys.path.insert(0, books_db_grpc_path)

import books_database_pb2 as pb
import books_database_pb2_grpc as grpc_pb

# In-memory store + vector clock just for demo
class BaseStore:
    def __init__(self):
        self.store = {}
        self.lock  = threading.Lock()

    def read(self, title):
        with self.lock:
            return self.store.get(title, 0)

    def write(self, title, value):
        with self.lock:
            self.store[title] = value

# Primary replica: accepts client writes, synchronously
# pushes them to backups before replying.
class PrimaryServicer(grpc_pb.BooksDatabaseServicer):
    def __init__(self, backup_addrs):
        self.base     = BaseStore()
        self.backups  = [grpc.insecure_channel(a) for a in backup_addrs]
        self.stubs    = [grpc_pb.BooksDatabaseStub(ch) for ch in self.backups]

    def Read(self, req, ctx):
        stock = self.base.read(req.title)
        return pb.ReadResponse(stock=stock)

    def Write(self, req, ctx):
        # local write
        self.base.write(req.title, req.new_stock)

        # propagate to backups
        ok = True
        for stub in self.stubs:
            try:
                resp = stub.Write(req, timeout=1.0)
                if not resp.success:
                    ok = False
            except:
                ok = False

        return pb.WriteResponse(success=ok)

# Backup replica: just applies writes
class BackupServicer(grpc_pb.BooksDatabaseServicer):
    def __init__(self):
        self.base = BaseStore()

    def Read(self, req, ctx):
        return pb.ReadResponse(stock=self.base.read(req.title))

    def Write(self, req, ctx):
        self.base.write(req.title, req.new_stock)
        return pb.WriteResponse(success=True)


def serve_primary(backups):
    server = grpc.server(futures.ThreadPoolExecutor())
    grpc_pb.add_BooksDatabaseServicer_to_server(PrimaryServicer(backups), server)
    server.add_insecure_port("[::]:50055")
    server.start()
    server.wait_for_termination()

def serve_backup(port):
    server = grpc.server(futures.ThreadPoolExecutor())
    grpc_pb.add_BooksDatabaseServicer_to_server(BackupServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    import sys
    role = sys.argv[1]  # "primary" or "backup"
    if role == "primary":
        # pass backup addresses on cmd-line
        backups = sys.argv[2:]
        serve_primary(backups)
    else:
        port = int(sys.argv[2])
        serve_backup(port)
