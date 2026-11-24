"""Minimal HTTP/1.1 DoH lab frontend forwarding to the same Unbound cache."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import ssl, socket, struct

CERTS = Path(__file__).resolve().parent / 'certs'

def exact(sock, n):
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(n-len(data))
        if not chunk: raise ConnectionError('Incomplete DNS response')
        data.extend(chunk)
    return bytes(data)

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def do_POST(self):
        if self.path != '/dns-query': return self.send_error(404)
        if self.headers.get_content_type() != 'application/dns-message': return self.send_error(415)
        try:
            n = int(self.headers.get('Content-Length', '0'))
            if not 12 <= n <= 65535: return self.send_error(400)
            query = self.rfile.read(n)
            with socket.create_connection(('127.0.0.1', 53), timeout=5) as sock:
                sock.sendall(struct.pack('!H', n) + query)
                reply = exact(sock, struct.unpack('!H', exact(sock, 2))[0])
        except (OSError, ValueError): return self.send_error(502)
        self.send_response(200)
        self.send_header('Content-Type', 'application/dns-message')
        self.send_header('Content-Length', str(len(reply)))
        self.end_headers()
        self.wfile.write(reply)

if __name__ == '__main__':
    server = ThreadingHTTPServer(('10.10.2.53', 443), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERTS/'server.crt', CERTS/'server.key')
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    server.serve_forever()
