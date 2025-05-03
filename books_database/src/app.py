import grpc
import os
import sys
import time
import threading
import logging
from concurrent import futures
from google.protobuf.empty_pb2 import Empty

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
books_db_grpc_path = os.path.abspath(os.path.join(FILE, "../../../utils/pb/books_database"))
sys.path.insert(0, books_db_grpc_path)

import books_database_pb2 as pb
import books_database_pb2_grpc as grpc_pb

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

PRELOAD = {
    "Pride and Prejudice":    10,
    "The Great Gatsby":        5,
    "Moby-Dick":               3,
    "To Kill a Mockingbird":   8,
    "1984":                    7
}

class BaseStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.kv   = {}   # title -> stock
        self.ver  = {}   # title -> version

    def _init_if_missing(self, title):
        if title not in self.kv:
            self.kv[title] = 0
            self.ver[title] = 0

    def read(self, title):
        with self.lock:
            self._init_if_missing(title)
            return self.kv[title], self.ver[title]

    def write(self, title, value):
        with self.lock:
            self._init_if_missing(title)
            self.kv[title] = value
            self.ver[title] += 1
            return self.ver[title]

    def decrement(self, title, amount):
        with self.lock:
            self._init_if_missing(title)
            cur = self.kv[title]
            if cur >= amount:
                new = cur - amount
                self.kv[title] = new
                self.ver[title] += 1
                return True, new, self.ver[title]
            else:
                return False, cur, self.ver[title]

    def cas_decrement(self, title, amount, expect_version):
        with self.lock:
            self._init_if_missing(title)
            if self.ver[title] != expect_version:
                return False, self.kv[title], self.ver[title]
            cur = self.kv[title]
            if cur >= amount:
                new = cur - amount
                self.kv[title] = new
                self.ver[title] += 1
                return True, new, self.ver[title]
            else:
                return False, cur, self.ver[title]

    def increment(self, title, amount):
        with self.lock:
            self._init_if_missing(title)
            cur = self.kv[title]
            new = cur + amount
            self.kv[title] = new
            self.ver[title] += 1
            return new, self.ver[title]


class PrimaryServicer(grpc_pb.BooksDatabaseServicer):
    def __init__(self, backup_addrs):
        self.store = BaseStore()

        # LOCAL preload
        for title, stock in PRELOAD.items():
            ver = self.store.write(title, stock)
        logging.info("Primary preloaded: %s", PRELOAD)

        # WAIT for each backup to bind its port, then build stubs
        self.stubs = []
        for addr in backup_addrs:
            channel = grpc.insecure_channel(addr)
            try:
                grpc.channel_ready_future(channel).result(timeout=5.0)
                logging.info("Primary: backup %s is ready", addr)
            except grpc.FutureTimeoutError:
                logging.warning("Primary: backup %s not ready after 5s", addr)
            self.stubs.append(grpc_pb.BooksDatabaseStub(channel))

        # REPLICATE preload to backups
        for title, stock in PRELOAD.items():
            req = pb.WriteRequest(title=title, new_stock=stock)
            for stub in self.stubs:
                try:
                    resp = stub.Write(req, timeout=2.0)
                    if not resp.success:
                        logging.warning("Backup rejected Write(%s)", title)
                except Exception as e:
                    logging.error("Replicate preload to %s failed: %s", stub, e)

    def Read(self, req, ctx):
        stock, ver = self.store.read(req.title)
        logging.debug("Read(%s) → stock=%d, ver=%d", req.title, stock, ver)
        return pb.ReadResponse(stock=stock, version=ver)

    def Write(self, req, ctx):
        new_ver = self.store.write(req.title, req.new_stock)
        logging.info("Write(%s=%d) → ver=%d", req.title, req.new_stock, new_ver)
        ok = True
        for stub in self.stubs:
            try:
                r = stub.Write(req, timeout=2.0)
                if not r.success:
                    ok = False
            except Exception as e:
                ok = False
                logging.error("Replicate Write to backup failed: %s", e)
        return pb.WriteResponse(success=ok, version=new_ver)

    def DecrementStock(self, req, ctx):
        ok, new_stock, new_ver = self.store.decrement(req.title, req.amount)
        if ok:
            logging.info("DecrementStock(%s by %d) → %d@ver%d", req.title, req.amount, new_stock, new_ver)
            wr = pb.WriteRequest(title=req.title, new_stock=new_stock)
            for stub in self.stubs:
                try:
                    stub.Write(wr, timeout=2.0)
                except Exception as e:
                    logging.error("Replicate Decrement failed: %s", e)
        else:
            logging.warning("DecrementStock failed %s: have=%d need=%d", req.title, new_stock, req.amount)
        return pb.DecrementResponse(success=ok, stock=new_stock, version=new_ver)

    def CASDecrement(self, req, ctx):
        ok, new_stock, new_ver = self.store.cas_decrement(
            req.title, req.amount, req.expect_version
        )
        if ok:
            logging.info("CASDecrement(%s amt=%d ver→%d) OK", req.title, req.amount, new_ver)
            wr = pb.WriteRequest(title=req.title, new_stock=new_stock)
            for stub in self.stubs:
                try:
                    stub.Write(wr, timeout=2.0)
                except Exception as e:
                    logging.error("Replicate CASDecrement failed: %s", e)
        else:
            logging.warning("CASDecrement(%s) FAILED: cur_ver=%d", req.title, new_ver)
        return pb.DecrementResponse(success=ok, stock=new_stock, version=new_ver)

    def IncrementStock(self, req, ctx):
        new_stock, new_ver = self.store.increment(req.title, req.amount)
        logging.info("IncrementStock(%s by %d) → %d@ver%d", req.title, req.amount, new_stock, new_ver)
        wr = pb.WriteRequest(title=req.title, new_stock=new_stock)
        for stub in self.stubs:
            try:
                stub.Write(wr, timeout=2.0)
            except Exception as e:
                logging.error("Replicate Increment failed: %s", e)
        return pb.IncrementResponse(success=True, stock=new_stock, version=new_ver)

    def CompareStock(self, req, ctx):
        cur, _ = self.store.read(req.title)
        enough = (cur >= req.threshold)
        return pb.CompareResponse(enough=enough, stock=cur)


class BackupServicer(grpc_pb.BooksDatabaseServicer):
    def __init__(self):
        self.store = BaseStore()
        logging.info("Backup initialized")

    def Read(self, req, ctx):
        stock, ver = self.store.read(req.title)
        return pb.ReadResponse(stock=stock, version=ver)

    def Write(self, req, ctx):
        ver = self.store.write(req.title, req.new_stock)
        return pb.WriteResponse(success=True, version=ver)

    def DecrementStock(self, req, ctx):
        ok, new_stock, ver = self.store.decrement(req.title, req.amount)
        return pb.DecrementResponse(success=ok, stock=new_stock, version=ver)

    def CASDecrement(self, req, ctx):
        ok, new_stock, ver = self.store.cas_decrement(
            req.title, req.amount, req.expect_version
        )
        return pb.DecrementResponse(success=ok, stock=new_stock, version=ver)

    def IncrementStock(self, req, ctx):
        new_stock, ver = self.store.increment(req.title, req.amount)
        return pb.IncrementResponse(success=True, stock=new_stock, version=ver)

    def CompareStock(self, req, ctx):
        cur, _ = self.store.read(req.title)
        return pb.CompareResponse(enough=(cur >= req.threshold), stock=cur)


def serve_primary(backups):
    server = grpc.server(futures.ThreadPoolExecutor())
    grpc_pb.add_BooksDatabaseServicer_to_server(PrimaryServicer(backups), server)
    server.add_insecure_port("[::]:50055")
    logging.info("Books Primary listening on 50055; backups=%s", backups)
    server.start()
    server.wait_for_termination()

def serve_backup(port):
    server = grpc.server(futures.ThreadPoolExecutor())
    grpc_pb.add_BooksDatabaseServicer_to_server(BackupServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    logging.info("Books Backup listening on %d", port)
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    role = sys.argv[1]    # "primary" or "backup"
    if role == "primary":
        serve_primary(sys.argv[2:])
    else:
        serve_backup(int(sys.argv[2]))
