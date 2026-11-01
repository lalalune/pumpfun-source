#!/usr/bin/env python3
"""runq.py APPROACH QUEUEFILE : lines 'file<TAB>hypothesis'; runs 2 parallel builds (slots 0/1); appends summary to gen/results.log"""
import json,subprocess,sys,threading,queue
SW='$HOME/Documents/Codex/2026-10-24/amm-sell-swarm'
appr,qf=sys.argv[1:3]
items=[l.rstrip('\n').split('\t',1) for l in open(qf) if l.strip()]
q=queue.Queue(); [q.put(i) for i in items]
lock=threading.Lock()
recs=[json.loads(l) for l in open(SW+'/ATTEMPTS.jsonl')]
shas={}
for r in recs:
    if r.get('candidate_sha256'): shas.setdefault(r['candidate_sha256'],[]).append(f"{r['lane']}/{r['key'][:8]}")
def work(slot):
    while True:
        try: f,h=q.get_nowait()
        except queue.Empty: return
        p=subprocess.run(['python3','-B','harness/try_sell.py','--lane','macro-idioms','--approach',appr,'--hypothesis',h,'--sell',f,'--slot',str(slot),'--disasm'],cwd=SW,capture_output=True,text=True)
        try:
            d=json.loads(p.stdout); m=d.get('metrics') or {}
            same=[x for x in shas.get(d.get('candidate_sha256'),[]) if not x.endswith(d.get('key','')[:8])]
            line=f"{f.split('/')[-1]:28s} rc={p.returncode} {d.get('status')} dup={d.get('duplicate')} key={d.get('key','')[:16]} dist={m.get('align_distance')} slots={m.get('slot_diffs')} size={m.get('sell_size')} lost={m.get('lost_windows_normalized_count')} same={same[:2]}"
        except Exception as e:
            line=f"{f.split('/')[-1]:28s} rc={p.returncode} PARSEFAIL {p.stderr[-300:]!r}"
        with lock:
            print(line, flush=True); open(SW+'/lanes/macro-idioms/gen/results.log','a').write(line+'\n')
ts=[threading.Thread(target=work,args=(s,)) for s in (0,1)]
[t.start() for t in ts]; [t.join() for t in ts]
