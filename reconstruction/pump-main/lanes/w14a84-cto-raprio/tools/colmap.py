#!/usr/bin/env python3
"""colmap.py <m.ll> <out-prefix> [lo hi] [--prio P] [--force F]: per-vreg colour map against the original.
Runs the private llc with RAPRIO_TAG=1 (asm: every final instruction that survives from greedy carries its vreg operands and
their registers) and RAPRIO_LOG, aligns our window with the original at L2 (frame+registers masked), and for every aligned pair
votes, per vreg whose register appears in a dst/src field, for the original's register in that field. Output (<prefix>.json and
stdout): vreg, our register, votes per original register, disagreement count, split ancestry root. Experiment only."""
import sys,os,re,json,subprocess,difflib,collections,types
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from bdis import decode
C=types.ModuleType('C'); C.__dict__['__file__']=T+'/cls.py'; _s=open(T+'/cls.py').read(); exec(_s[:_s.index('def main')],C.__dict__)
src=open(T+'/rx.py').read(); g={'__name__':'x'}; exec(src.split("OUT=os.environ")[0],g)
LLC=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a84-cto-raprio/llvmb/bin/llc')
A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
a=sys.argv[1:]; m,pre=a[0],a[1]; lo,hi=0,1<<30
if len(a)>3 and not a[2].startswith('--'): lo,hi=int(a[2],0),int(a[3],0)
env=dict(os.environ,RAPRIO_TAG='1',RAPRIO_LOG=pre+'.ra.log')
for k,e in (('--prio','RAPRIO_PRIO'),('--force','RAPRIO_FORCE')):
    if k in a: env[e]=a[a.index(k)+1]
if os.path.exists(pre+'.ra.log'): os.remove(pre+'.ra.log')
subprocess.run([LLC,*A,m,'-filetype=asm','-o',pre+'.s'],env=env,check=True)
env.pop('RAPRIO_LOG'); subprocess.run([LLC,*A,m,'-filetype=obj','-o',pre+'.o'],env=env,check=True)
c=g['elf_fn'](pre+'.o',g['KEEP']); open(pre+'.bin','wb').write(c)
# asm instruction lines of execute
lines=[]; f=False
for l in open(pre+'.s'):
    if re.match(r'^_ZN14pump_recovered9admin_cto7execute\w*:',l): f=True; continue
    if f and l.startswith('.Lfunc_end'): break
    if f and l.startswith('\t') and not l.startswith('\t.'):
        txt=l.strip(); tag=None
        if '# rp ' in txt: txt,tag=txt.split('# rp ',1)
        lines.append((txt.strip(),tag))
ci=decode(c)
assert len(ci)==len(lines),(len(ci),len(lines))
O=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a84-cto-raprio/orig.bin'),'rb').read(); oi=decode(O)
def tk(raw,ins,lv): return [C.mask(raw[d['off']:d['off']+d['n']],lv) for d in ins]
sm=difflib.SequenceMatcher(None,tk(O,oi,2),tk(c,ci,2),autojunk=False)
votes=collections.defaultdict(collections.Counter); ours={}; sites=collections.defaultdict(list)
untag=0; pairs=0
for x,y,n in sm.get_matching_blocks():
    for k in range(n):
        od,cd=oi[x+k],ci[y+k]
        if not (lo<=od['off']<hi): continue
        pairs+=1; tag=lines[y+k][1]
        if not tag: untag+=1; continue
        ops=[(t[0],int(t[1:].split('=')[0]),t.split('=')[1]) for t in tag.split()[1:]]
        for fld in ('dst','src'):
            R='R%d'%cd[fld]
            for kind,v,ph in ops:
                if ph==R:
                    votes[v]['r%d'%od[fld]]+=1; ours[v]=ph.lower()
                    if od[fld]!=cd[fld]: sites[v].append('%04x'%od['off'])
par={}; seen=set()
for l in open(pre+'.ra.log'):
    p=l.split()
    if p[0]=='Q': seen.add(int(p[1]))
    elif p[0]=='R' and 'new:' in p:
        q=int(p[1])
        for z in p[p.index('new:')+1:]:
            z=int(z)
            if z!=q and z not in seen and z not in par: par[z]=q
def root(v):
    ch=[v]
    while ch[-1] in par: ch.append(par[ch[-1]])
    return ch
rows=[]
for v,cnt in votes.items():
    tot=sum(cnt.values()); agree=cnt[ours[v]]; best,bn=cnt.most_common(1)[0]
    rows.append({'vreg':v,'ours':ours[v],'votes':dict(cnt.most_common()),'n':tot,'miss':tot-agree,'orig_major':best,'root':root(v)[-1],'chain':root(v),'sites':sites[v][:6]})
rows.sort(key=lambda r:-r['miss'])
json.dump({'pairs':pairs,'untagged':untag,'rows':rows},open(pre+'.json','w'),indent=0)
print(f'aligned L2 pairs {pairs} in [{lo:#x},{hi:#x}), untagged {untag}; vregs with register votes {len(rows)}, with misses {sum(1 for r in rows if r["miss"])}, total misses {sum(r["miss"] for r in rows)}')
for r in rows[:40]:
    if not r['miss']: break
    print(f"%{r['vreg']:<5} ours {r['ours']:<3} orig {r['orig_major']:<3} miss {r['miss']:>3}/{r['n']:<3} root %{r['root']:<5} votes {r['votes']} at {' '.join(r['sites'])}")
