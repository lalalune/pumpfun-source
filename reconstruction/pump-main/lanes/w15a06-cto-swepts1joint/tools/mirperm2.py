#!/usr/bin/env python3
"""mirperm.py <dbgdir> [subset] : per-interval spill-colour bound for the sharing-CPI tail (experiment only).
Inputs in dbgdir: pre.mir (-stop-before=stack-slot-coloring), ssc.mir (-stop-after=stack-slot-coloring), ssc.log
(-debug-only=stack-slot-coloring). Gives each sharing-tail spill interval (pre-colour FI) the colour of the original's
slot (colour c <-> offset 0x8e0+8*(c-179)), re-homes any other interval that now overlaps onto the first legal colour,
rewrites ssc.mir and runs llc -start-after=stack-slot-coloring. subset: 'all' or comma list of array offsets."""
import sys,re,os,subprocess,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+'/../t139')
import px2
D=sys.argv[1]; SUB=sys.argv[2] if len(sys.argv)>2 else 'all'
log=open(D+'/ssc.log').read()
SUBK={'B':0,'e':1,'r':2,'d':3}
def iv(s): return [(int(a)*4+SUBK[b],int(c)*4+SUBK[d]) for a,b,c,d in re.findall(r'\[(\d+)([Berd]),(\d+)([Berd]):\d+\)',s)]
IV={int(m.group(1)):iv(m.group(2)) for m in re.finditer(r'^SS#(\d+) (.*)$',log,re.M)}
COL={int(a):int(b) for a,b in re.findall(r'Assigning fi#(\d+) to fi#(\d+)',log)}
for f in IV: COL.setdefault(f,f)
pre=open(D+'/pre.mir').read().split('\n'); ssc=open(D+'/ssc.mir').read().split('\n')
bp=pre.index('body:             |'); bs=ssc.index('body:             |'); assert len(pre)-bp==len(ssc)-bs
# sharing tail: second LDD->ST into _55.i98 run (lines after the first big run)
rows=[]
for i in range(bp,len(pre)-1):
    m=re.match(r'\s+\$(r\d+) = LDD_V1 %stack\.(\d+), 0\s*$',pre[i])
    if not m: continue
    m2=re.match(r'\s+(ST\w+) killed \$'+m.group(1)+r', %stack\.\d+\._55\.i9\d, (\d+)',pre[i+1])
    if m2: rows.append((i,int(m.group(2)),int(m2.group(2))))
# split runs by gaps
runs=[[rows[0]]]
for r in rows[1:]:
    (runs[-1].append(r) if r[0]-runs[-1][-1][0]<40 else runs.append([r]))
tail=max(runs,key=lambda r:r[0][0]) if len(runs)>1 else runs[0]
tail=[r for r in runs if len(r)>=40][-1]
ORIG={24:0x910,32:0xac8,40:0xa88,48:0xa48,56:0x948,64:0x960,65:0x968,66:0x970,72:0x978,80:0x940,88:0x980,96:0x988,104:0x990,112:0x998,113:0x9a0,114:0x9a8,120:0x918,128:0x8e0,136:0x9b0,144:0x9b8,152:0x9c0,160:0x9c8,161:0x9d0,162:0x9d8,168:0x920,176:0x900,184:0x9e0,192:0x9e8,200:0x9f0,208:0x9f8,209:0xa00,210:0xa08,216:0xa50,224:0x908,232:0xa10,240:0xa18,248:0xa20,256:0xa28,257:0xa30,258:0xa38,264:0xa40,272:0x928,280:0xa58,288:0xa90,296:0xa60,304:0xa68,305:0xa70,306:0xa78,312:0xa80,320:0xa98,328:0xac0}
want={}
for i,f,a in tail:
    if a in ORIG and (SUB in('all','valid') or str(a) in SUB.split(',')): want[f]=179+(ORIG[a]-0x8e0)//8
if SUB=='valid' or os.environ.get('EXCL'):
    ex=set(int(x) for x in os.environ.get('EXCL','179,184,185').split(','))
    want={f:c for f,c in want.items() if c not in ex}
def ov(a,b):
    i=j=0
    while i<len(a) and j<len(b):
        if a[i][0]<b[j][1] and b[j][0]<a[i][1]: return True
        if a[i][1]<=b[j][1]: i+=1
        else: j+=1
    return False
new={f:want.get(f,COL[f]) for f in COL}
EV=[int(x) for x in os.environ.get('EVICT','').split(',') if x]
mx=max(COL.values()); EVC={}
for k,f in enumerate(EV): new[f]=mx+1+k; EVC[f]=mx+1+k; IV.setdefault(mx+1+k,[])
# validate wanted set pairwise
W=list(want)
for x in range(len(W)):
    for y in range(x+1,len(W)):
        if want[W[x]]==want[W[y]] and ov(IV[W[x]],IV[W[y]]): print('WANT CONFLICT',W[x],W[y],file=sys.stderr)
colours=sorted(set(COL.values()))
moved=[]
for g in sorted(COL):
    if g in want: continue
    c=new[g]
    if any(new[h]==c and h!=g and ov(IV[g],IV[h]) for h in want):
        for c2 in colours:
            if not any(new[h]==c2 and h!=g and ov(IV[g],IV[h]) for h in COL if h!=g and (h in want or h<g or new[h]!=COL[h] or True)):
                new[g]=c2; moved.append((g,c,c2)); break
        else: print('NO COLOUR for',g,c,file=sys.stderr)
# rewrite
out=list(ssc); nrw=0
for k in range(bp,len(pre)):
    l=pre[k]; fs=re.findall(r'%stack\.(\d+)\b',l)
    s=ssc[bs+(k-bp)]
    for f in set(int(x) for x in fs):
        if f in COL and new[f]!=COL[f]:
            assert f'%stack.{COL[f]}' in s,(l,s)
            s=re.sub(r'%%stack\.%d\b'%COL[f],'%%stack.%d'%new[f],s); nrw+=1
    out[bs+(k-bp)]=s
if EVC:
    ix=next(i for i,l in enumerate(out) if l.startswith('  - { id: %d,'%mx))
    blk=out[ix:ix+3]; add=[]
    for c in sorted(EVC.values()): add+=[blk[0].replace('id: %d,'%mx,'id: %d,'%c)]+blk[1:]
    out=out[:ix+3]+add+out[ix+3:]
nm=D+'/perm_'+SUB.replace(',','_')[:40]+('_ev' if EVC else '')
open(nm+'.mir','w').write('\n'.join(out))
r=subprocess.run([D+'/llc.sh',nm+'.mir','-start-after=stack-slot-coloring','-filetype=obj','-o',nm+'.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
import importlib.util as _iu; _sp=_iu.spec_from_file_location('objsc_fix',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a06-cto-swepts1joint/tools/fixfs.py')); _m=_iu.module_from_spec(_sp); _sp.loader.exec_module(_m); c=_m.fixfs(px2.G['elf_fn'](nm+'.o',px2.G['KEEP'])); open(nm+'.bin','wb').write(c); os.remove(nm+'.o'); os.remove(nm+'.mir')
s=px2.score_bin(c)
print(json.dumps({'sub':SUB,'ch':{hex(k*0x400):v for k,v in sorted(s['ch'].items())} if os.environ.get('CH') else 0,'n_want':len(want),'changed':sum(1 for f in want if want[f]!=COL[f]),'moved':len(moved),'nmax':max(new.values()),'rewr':nrw,**{k:s[k] for k in('ratio','M','slots','bytes')}}))
