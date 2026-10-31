#!/usr/bin/env python3
"""rec.py name hypothesis : record a raw-IR screen row for rx/<name>"""
import sys,os,json,subprocess,difflib
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a121-cto-delwin')
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a121-cto-delwin/reconstruction/pump-main/log_attempt.py'
name,hyp=sys.argv[1],sys.argv[2]; base=sys.argv[3] if len(sys.argv)>3 else 'ebe5387'
p=OUT+'/rx/'+name+'/res.json'
if not os.path.exists(p): p=OUT+'/px/'+name+'/res.json'
r=json.load(open(p)) if os.path.exists(p) else {'error':'compile'}
mc=subprocess.run(['python3',OUT+'/tools/mc.py',name],capture_output=True,text=True).stdout.split()
M=int(mc[2]) if len(mc)>2 and mc[1]=='M' else None
ed=open(OUT+'/ev/'+name+'.py').read() if os.path.exists(OUT+'/ev/'+name+'.py') else ''
st='rejected' if not r.get('eq_main') else 'analyzed'
data={'output':OUT+'/rx/'+name,'normalized':None,'raw':None,'losses':[],'raw_losses':[],
 'target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes'),'M':M},
 'notes':'delwin raw-IR capture+rx opt/llc oracle on main %s (M 2247, 3123 slots); eq_main %s; edits: %s'%(base,r.get('eq_main'),ed[:600])}
k='0x22a10-w14-%s-delwin-%s-v1'%(base,name)
print(subprocess.run(['python3',L,'record','--lane','w14a121-cto-delwin','--approach','delwin','--target','0x22a10','--dedupe-key',k,'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True).stdout.strip()[:200], k, M, r.get('bytes'))
