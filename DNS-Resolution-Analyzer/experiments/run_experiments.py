"""Run from Ubuntu host as root; measurements execute inside client namespace."""
import argparse,csv,json,subprocess,sys,time,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'comparison'))
from do53 import resolve_do53
from dot import DoTConnection
from doh import DoHConnection

def command(*args): return subprocess.run(args,check=True,text=True,capture_output=True).stdout

def worker(a):
    names=(ROOT/'experiments/domains.txt').read_text().splitlines()[:a.limit]
    random.Random(a.run).shuffle(names)
    conn=None
    def create(): return DoTConnection() if a.protocol=='DoT' else DoHConnection()
    fields=['run','rtt_ms','loss_pct','cache','mode','domain','protocol','status','time_ms','setup_ms','query_ms','bytes','wire_bytes','fallback','rcode','response','error']
    with open(a.output,'a',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields)
        if f.tell()==0: w.writeheader()
        try:
            if a.mode=='persistent': conn=create(); conn.resolve('example.lab')
            for name in names:
                row=dict(run=a.run,rtt_ms=a.rtt,loss_pct=a.loss,cache=a.cache,mode=a.mode,domain=name,protocol=a.protocol,status='ok')
                temporary=None; cap=None; capture_path=None
                try:
                    # Clear message, RRset and delegation cache before each measured lookup.
                    command('ip','netns','exec','unbound','unbound-control','-c',str(ROOT/'runtime/unbound.conf'),'flush_zone','.')
                    # Flush_zone can leave infrastructure cache; explicitly clear it too.
                    command('ip','netns','exec','unbound','unbound-control','-c',str(ROOT/'runtime/unbound.conf'),'flush_infra','all')
                    if a.cache=='warm': resolve_do53(name)
                    if a.protocol=='Do53': fn=resolve_do53
                    else:
                        if conn is None: temporary=create()
                        fn=(conn or temporary).resolve
                    if a.capture:
                        capture_path=ROOT/'captures/comparison'/f'{a.rtt}_{a.loss}_{a.run}_{a.cache}_{a.protocol}_{a.mode}_{name}.pcap'
                        cap=subprocess.Popen(['tcpdump','-U','-i','eth0','-w',str(capture_path),'host','10.10.2.53','and','(port 53 or port 853 or port 443)'],stderr=subprocess.PIPE,text=True)
                        while True:
                            line=cap.stderr.readline()
                            if 'listening on' in line: break
                            if not line: raise RuntimeError('tcpdump failed')
                    row.update(fn(name))
                    if row['rcode'] not in (0,3): row['status']='dns_error'
                except Exception as e:
                    row.update(status='error',error=str(e))
                    if conn is not None:
                        conn.close(); conn=None
                finally:
                    if temporary: temporary.close()
                    if cap:
                        cap.terminate(); cap.wait(timeout=5); cap.stderr.close()
                        try:
                            sizes=command('tshark','-r',str(capture_path),'-T','fields','-e','frame.len')
                            row['wire_bytes']=sum(int(v) for v in sizes.splitlines() if v)
                            command('editcap','-F','pcapng',str(capture_path),str(capture_path.with_suffix('.pcapng')))
                            capture_path.unlink()
                        except Exception as e: row['error']=str(row.get('error',''))+' capture: '+str(e)
                    w.writerow(row); f.flush()
                    if a.mode=='persistent' and conn is None:
                        try: conn=create(); conn.resolve('example.lab')
                        except Exception:
                            if conn: conn.close()
                            conn=None
        finally:
            if conn: conn.close()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--worker',action='store_true'); p.add_argument('--runs',type=int,default=5); p.add_argument('--limit',type=int,default=200); p.add_argument('--capture',action='store_true'); p.add_argument('--output',default=str(ROOT/'experiments/results.csv')); p.add_argument('--rtt',type=int,default=20); p.add_argument('--loss',type=float,default=0); p.add_argument('--run',type=int,default=1); p.add_argument('--cache',default='cold'); p.add_argument('--protocol',default='Do53'); p.add_argument('--mode',default='new'); p.add_argument('--smoke',action='store_true'); a=p.parse_args()
    if a.worker: return worker(a)
    a.output=str(Path(a.output).resolve())
    if Path(a.output).exists(): p.error('Output exists; choose another --output to avoid duplicate data')
    try:
        for rtt in ([0] if a.smoke else [20,100,200]):
            for loss in ([0] if a.smoke else [0,2,5]):
                command('bash',str(ROOT/'network/apply_impairments.sh'),str(rtt),str(loss))
                for run in range(1,(1 if a.smoke else a.runs)+1):
                    for cache in ['cold','warm']:
                        for protocol,mode in [('Do53','new'),('DoT','new'),('DoT','persistent'),('DoH','new'),('DoH','persistent')]:
                            print(rtt,loss,run,cache,protocol,mode,flush=True)
                            subprocess.run(['ip','netns','exec','client',sys.executable,__file__,'--worker','--rtt',str(rtt),'--loss',str(loss),'--run',str(run),'--cache',cache,'--protocol',protocol,'--mode',mode,'--limit',str(min(a.limit,2) if a.smoke else a.limit),'--output',a.output]+(['--capture'] if a.capture else []),check=True)
    finally: command('bash',str(ROOT/'network/apply_impairments.sh'),'0','0')
if __name__=='__main__': main()
