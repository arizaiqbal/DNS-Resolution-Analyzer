from pathlib import Path
import sys, time, struct
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'resolver'))
from dns_packet import build_dns_query
from dns_decoder import decode_dns_response
from dns_client import receive_exact
SERVER = '10.10.2.53'
CA = ROOT/'unbound/certs/ca.crt'
URL = f'https://{SERVER}/dns-query'

def now(): return time.perf_counter()
def ms(start): return (now()-start)*1000

def make_query(domain): return build_dns_query(domain, recursion_desired=True)

def result(domain, protocol, query, reply, tid, start, setup=0, fallback=False, extra_bytes=0):
    elapsed = ms(start)
    decoded = decode_dns_response(reply)
    if decoded['transaction_id'] != tid or not decoded['is_response']:
        raise ValueError('Invalid DNS response')
    return dict(domain=domain, protocol=protocol, time_ms=elapsed,
                setup_ms=setup, query_ms=max(0, elapsed-setup),
                bytes=len(query)+len(reply)+extra_bytes, fallback=fallback,
                rcode=decoded['rcode'], response=str(decoded['answers']))

def exchange(sock, query):
    sock.sendall(struct.pack('!H',len(query))+query)
    return receive_exact(sock, struct.unpack('!H',receive_exact(sock,2))[0])
