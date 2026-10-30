#!/usr/bin/env python3
"""recx.py <variant> <mech-key> <status> <hypothesis> [note] : record an IR-oracle (src.sh) result"""
import sys,json,subprocess,re
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a17-cto-outlineport'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a17-cto-outlineport/reconstruction/pump-main/log_attempt.py'
v,key,st,hyp=sys.argv[1:5]; note=sys.argv[5] if len(sys.argv)>5 else ''
r=subprocess.run(['python3',O+'/tools/oratio.py',O+'/orig_fn.txt',f'{O}/x/{v}/fn.txt'],capture_output=True,text=True).stdout
m=re.search(r'ratio ([\d.]+).*bytes (\d+).*lddw (\d+)',r)
data={'output':f'{O}/x/{v}','target':{'ratio':float(m.group(1)),'cand_bytes':int(m.group(2)),'lddw':int(m.group(3))},'notes':'raw-IR capture + opt -O3 + llc oracle (= measure.sh ratio); '+note}
k=f'0x22a10-w13-74b3171-outlineport-{key}-v1'
subprocess.run(['python3',L,'record','--lane','w13a17-cto-outlineport','--approach','outlineport','--target','0x22a10','--dedupe-key',k,'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],check=True,capture_output=True)
print('recorded',k,m.group(0))
