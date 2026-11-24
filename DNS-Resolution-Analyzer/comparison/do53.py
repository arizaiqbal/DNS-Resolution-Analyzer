import socket, struct
from common import *

def resolve_do53(domain, server=SERVER):
    query, tid = make_query(domain)
    start = now()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(5)
        sock.connect((server,53))
        sock.send(query)
        reply = sock.recv(65535)
    if len(reply)<12 or struct.unpack('!H',reply[:2])[0]!=tid:
        raise ValueError('Invalid UDP reply')
    fallback = bool(struct.unpack('!H',reply[2:4])[0]&0x0200)
    extra = 0
    setup = 0
    if fallback:
        extra = len(query)+len(reply)
        t = now()
        with socket.create_connection((server,53),timeout=5) as sock:
            setup = ms(t)
            reply = exchange(sock,query)
    return result(domain,'Do53',query,reply,tid,start,setup,fallback,extra)
