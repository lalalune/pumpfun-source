#!/usr/bin/env python3
"""rec.py <name> <genes> <status> <hypothesis> [note]: ledger row for oracle trial x/<name> (mm + fdelta)"""
import sys,subprocess,json,re,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a19-cto-framebasis'); T=O+'/tools'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a19-cto-framebasis/reconstruction/pump-main/log_attempt.py'
n,g,st,hyp=sys.argv[1:5]; note=sys.argv[5] if len(sys.argv)>5 else ''
mm=subprocess.run(['python3',T+'/mm.py',f'{O}/x/{n}'],capture_output=True,text=True).stdout.strip()
fd=subprocess.run(['python3',T+'/fdelta.py',f'{O}/x/m3',f'{O}/x/{n}'],capture_output=True,text=True).stdout.strip().replace('\n',' ; ')
d=dict(re.findall(r'(\w+)=(\S+)',mm)); nn=int(d['n']); b=sum(16 if 'lddw' in l else 8 for l in open(f'{O}/x/{n}/fn.txt'))
data={'output':f'{O}/x/{n}','normalized':None,'raw':None,'losses':None,'target':{'ratio':float(d['ratio']),'cand_bytes':b},
      'oracle':'raw-IR capture + opt -O3 + llc (eq_main on f8dc901: 0.63481 at 27400 B)','M':int(d['M']),'M_jumpmasked':int(d['J']),'M_framemasked':int(d['F']),
      'frame_delta_vs_main':fd[:900],'genes':g,'notes':note}
key=f'0x22a10-w14-f8dc901-framebasis-{n}-v1'
r=subprocess.run(['python3',L,'record','--lane','w14a19-cto-framebasis','--approach','framebasis','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
print(key,r.returncode,r.stdout.strip()[-120:],r.stderr.strip()[-200:])
