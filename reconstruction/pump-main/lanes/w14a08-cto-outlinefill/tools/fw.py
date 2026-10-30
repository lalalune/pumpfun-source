#!/usr/bin/env python3
"""fw.py <name> <genes,comma> [work] [wts e.g. 1:2,none]: var from var/m3 + genes, raw-IR capture, then opt/llc oracle
unweighted and with Some:None weights on validate's 306 switch. Appends JSON to res.jsonl. Deletes var + raw IR."""
import sys,os,subprocess,json,re,shutil
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a08-cto-outlinefill'; T=O+'/tools'
sys.path.insert(0,T); import fg
name,genes=sys.argv[1],[g for g in sys.argv[2].split(',') if g]; work=sys.argv[3] if len(sys.argv)>3 else 'work0'
wts=(sys.argv[4] if len(sys.argv)>4 else 'none,1:2').split(',')
rec={'name':name,'genes':genes}
def out(r):
    open(O+'/res.jsonl','a').write(json.dumps(r)+'\n'); print(json.dumps(r),flush=True)
d=f'{O}/var/{name}'; shutil.rmtree(d,ignore_errors=True)
subprocess.run(['rsync','-a',O+'/var/m3/',d+'/'],check=True)
p=d+'/src/creator/admin_cto.rs'
try: s=fg.apply(open(p).read(),genes)
except Exception as e: rec['err']=str(e); out(rec); shutil.rmtree(d); sys.exit(0)
open(p,'w').write(s)
ir=f'{O}/ir/{name}'; shutil.rmtree(ir,ignore_errors=True)
r=subprocess.run(['python3',T+'/capraw.py',d,f'{O}/{work}',ir],capture_output=True,text=True)
raw=ir+'/pump_recovered.raw.ll'
if not os.path.exists(raw):
    rec['err']='compile'; out(rec); shutil.rmtree(d); shutil.rmtree(ir,ignore_errors=True); sys.exit(0)
L=open(raw).read().split('\n')
vs=next(i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto8validate' in l)
sw=None
for i in range(vs,len(L)):
    if L[i]=='}': break
    if 'lifetime.start.p0(i64 32, ptr %t)' in L[i]:
        for j in range(i,i+8):
            if L[j].lstrip().startswith('switch'): sw=j; break
        if sw: break
rec['sw']=sw
for w in wts:
    tag=f'{name}_{w.replace(":","")}'
    args=['python3',T+'/brw.py',raw,O+'/bw',tag]+([f'{sw}:{w}'] if w!='none' and sw else [])
    if w!='none' and not sw: rec[w]='no-switch'; continue
    o=subprocess.run(args,capture_output=True,text=True).stdout
    m=re.search(r'ratio (\S+) insns \S+ \S+ bytes (\d+) lddw (\d+) \| \[([^\]]*)\]',o)
    if m:
        mk=subprocess.run(['python3',T+'/mratio2.py',O+'/orig_fn.txt',f'{O}/bw/{tag}/fn.txt'],capture_output=True,text=True).stdout.split()[-1]
        rec[w]={'ratio':float(m.group(1)),'bytes':int(m.group(2)),'lddw':int(m.group(3)),'outl':m.group(4).replace(' ',''),'masked':float(mk)}
    else: rec[w]='fail:'+o[-200:]
    for f in ('ex.bc','ex.o','ex.ll','pei.mir'):
        q=f'{O}/bw/{tag}/{f}'
        if os.path.exists(q) and f!='ex.o' and not (os.environ.get('KEEP') and f=='ex.bc'): os.remove(q)
out(rec)
shutil.rmtree(d)
if not os.environ.get('KEEPIR'): shutil.rmtree(ir,ignore_errors=True)
