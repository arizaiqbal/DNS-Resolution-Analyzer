import httpx, ssl
from common import *

class DoHConnection:
    def __init__(self,url=URL):
        self.url=url
        self.client=httpx.Client(verify=ssl.create_default_context(cafile=str(CA)),timeout=10,trust_env=False)
    def close(self): self.client.close()
    def resolve(self,domain):
        query,tid=make_query(domain)
        start=now(); setup=0; starts={}
        def trace(event,info):
            nonlocal setup
            name,_,phase=event.rpartition('.')
            if name.endswith(('connect_tcp','start_tls')):
                if phase=='started': starts[name]=now()
                elif phase=='complete' and name in starts: setup+=ms(starts.pop(name))
        r=self.client.post(self.url,content=query,headers={'Content-Type':'application/dns-message','Accept':'application/dns-message'},extensions={'trace':trace})
        r.raise_for_status()
        if r.headers.get('content-type','').split(';')[0]!='application/dns-message': raise ValueError('Invalid DoH content type')
        return result(domain,'DoH',query,r.content,tid,start,setup)

def resolve_doh(domain,url=URL):
    conn=DoHConnection(url)
    try: return conn.resolve(domain)
    finally: conn.close()
