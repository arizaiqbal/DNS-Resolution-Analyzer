import socket, ssl
from common import *

class DoTConnection:
    def __init__(self, server=SERVER, port=853):
        self.server, self.port, self.sock = server, port, None
    def connect(self):
        ctx = ssl.create_default_context(cafile=str(CA))
        raw = socket.create_connection((self.server,self.port),timeout=5)
        try: self.sock = ctx.wrap_socket(raw,server_hostname=self.server)
        except Exception:
            raw.close(); raise
    def close(self):
        if self.sock: self.sock.close(); self.sock=None
    def resolve(self,domain):
        query,tid=make_query(domain)
        start=now(); setup=0
        if self.sock is None:
            self.connect(); setup=ms(start)
        try:
            reply=exchange(self.sock,query)
            return result(domain,'DoT',query,reply,tid,start,setup)
        except Exception:
            self.close(); raise

def resolve_dot(domain,server=SERVER,port=853):
    conn=DoTConnection(server,port)
    try: return conn.resolve(domain)
    finally: conn.close()
