import argparse,json
from do53 import resolve_do53
from dot import resolve_dot
from doh import resolve_doh

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('domain',nargs='?',default='example.lab'); args=p.parse_args()
    for fn in (resolve_do53,resolve_dot,resolve_doh):
        try: print(json.dumps(fn(args.domain),indent=2))
        except Exception as e: print(f'{fn.__name__}: {e}')
