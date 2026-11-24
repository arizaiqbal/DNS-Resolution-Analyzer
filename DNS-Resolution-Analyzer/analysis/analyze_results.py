import argparse
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('csv',nargs='?',default=ROOT/'experiments/results.csv'); a=p.parse_args()
d=pd.read_csv(a.csv); out=ROOT/'graphs'; out.mkdir(exist_ok=True)
keys=['rtt_ms','loss_pct','cache','protocol','mode']
counts=d.groupby(keys).status.agg(attempts='size',successes=lambda x:(x=='ok').sum()); counts['success_pct']=100*counts.successes/counts.attempts
ok=d[d.status=='ok'].copy()
for col in ['time_ms','setup_ms','query_ms','bytes','wire_bytes']: ok[col]=pd.to_numeric(ok[col],errors='coerce')
summary=ok.groupby(keys)[['time_ms','setup_ms','query_ms','bytes','wire_bytes']].agg(['mean','std','min','max','count']); summary.columns=['_'.join(c) for c in summary.columns]; counts.join(summary).to_csv(out/'summary.csv')
if ok.empty: raise SystemExit('No successful lookups; see summary.csv')
for metric,label in [('time_ms','Latency (ms)'),('setup_ms','Connection setup (ms)'),('query_ms','Query time (ms)'),('bytes','DNS payload bytes'),('wire_bytes','Captured frame bytes')]:
    if not ok[metric].notna().any(): continue
    for (cache,loss), group in ok.groupby(['cache','loss_pct']):
        means=group.groupby(['rtt_ms','protocol','mode'])[metric].mean().unstack(['protocol','mode'])
        ax=means.plot(marker='o',figsize=(9,5)); ax.set(xlabel='Added RTT (ms)',ylabel=label,title=f'{cache} cache, {loss:g}% loss per direction'); plt.tight_layout(); plt.savefig(out/f'{metric}_{cache}_{loss:g}.png'); plt.close()
print(counts.join(summary).to_string())
