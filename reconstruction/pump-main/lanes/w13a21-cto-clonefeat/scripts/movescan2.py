#!/usr/bin/env python3
"""movescan2.py (w13a21: movescan.py + clonefeat spill/reg per edit)
movescan.py <module.ll> <outdir> [--par N]
llc oracle scan of cross-block 'where is the value computed' edits in admin_cto::execute:
 sink:  a pure instruction (load/gep/icmp/cast/binop/select/extractvalue) whose non-phi uses all sit in ONE other block U
        is moved to the top of U (after phis/landing);
 hoist: a pure instruction in block U whose operands are not defined in U, where U has exactly one predecessor P,
        is moved to the end of P (before the terminator).
Numbered values are renamed to keep numbering valid. Experiment-only."""
import sys,re,json,os,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co
import clonefeat as cf
a=sys.argv; mod=Path(a[1]).read_text(); out=Path(a[2]); out.mkdir(parents=True,exist_ok=True)
par=int(a[a.index('--par')+1]) if '--par' in a else 3
sym=co.SYMRE.search(mod).group(0); i,j=co.fn_bounds(mod,sym); fn=mod[i:j]; L=fn.split('\n')
PURE=re.compile(r'^  %([\w.$"-]+) = (load|getelementptr|icmp|select|zext|sext|trunc|and|or|xor|add|sub|shl|lshr|ashr|mul|extractvalue|insertvalue|ptrtoint|inttoptr) ')
# blocks
blocks=[]; cur=None
for k,l in enumerate(L):
    m=re.match(r'^([\w.$"-]+):',l)
    if m: cur={'name':m.group(1),'start':k,'lines':[],'preds':[]}; blocks.append(cur)
    elif cur is not None and l.startswith('  '): cur['lines'].append(k)
    if m and 'preds = ' in l: cur['preds']=[p.strip().lstrip('%') for p in l.split('preds = ')[1].split(', ')]
# first block 'start' has no label line in the text: handle by mapping lines before the first label
first_label=blocks[0]['start'] if blocks else 0
entry={'name':'start','start':-1,'lines':[k for k in range(len(L)) if k<first_label and L[k].startswith('  ')],'preds':[]}
if entry['lines']: blocks.insert(0,entry)
blk_of={}
for b in blocks:
    for k in b['lines']: blk_of[k]=b
bname={b['name']:b for b in blocks}
defs={}
for k,l in enumerate(L):
    m=re.match(r'^  %([\w.$"-]+) = ',l)
    if m: defs[m.group(1)]=k
def uses(v):
    pat=re.compile(r'%'+re.escape(v)+r'(?![\w.$-])')
    return [k for k,l in enumerate(L) if k!=defs[v] and pat.search(l)]
def is_phi(k): return re.match(r'^  %\S+ = phi ',L[k]) is not None
def first_nonphi(b):
    for k in b['lines']:
        if not is_phi(k) and 'landingpad' not in L[k]: return k
def term(b): return b['lines'][-1]
cands=[]
for v,k in defs.items():
    m=PURE.match(L[k])
    if not m or k not in blk_of: continue
    b=blk_of[k]; us=uses(v)
    if not us or any(is_phi(u) for u in us): pass
    else:
        ub={blk_of[u]['name'] for u in us if u in blk_of}
        if len(ub)==1 and b['name'] not in ub:
            U=bname[next(iter(ub))]; cands.append(('sink',v,k,first_nonphi(U),U['name']))
    # hoist
    if len(b['preds'])==1 and b['preds'][0] in bname:
        ops=re.findall(r'%([\w.$"-]+)',L[k].split(' = ',1)[1])
        if all(defs.get(o) is None or blk_of.get(defs[o]) is not b for o in ops):
            P=bname[b['preds'][0]]
            if P['lines']: cands.append(('hoist',v,k,term(P),P['name']))
def renum(lines):
    # renumber numeric values in order of definition to keep LLVM happy
    s='\n'.join(lines); order=[]
    for l in lines:
        m=re.match(r'^  %(\d+) = ',l)
        if m: order.append(m.group(1))
    if order==sorted(order,key=int) and order==[str(x) for x in range(int(order[0]),int(order[0])+len(order))] if order else True: return s
    nums=sorted(order,key=int); mp={o:n for o,n in zip(order,nums)}
    s=re.sub(r'%(\d+)(?![\w.$-])',lambda m:'%__'+mp[m.group(1)] if m.group(1) in mp else m.group(0),s)
    return s.replace('%__','%')
otok,w=co.orig_tokens()
def one(c):
    kind,v,k,dest,bn=c
    L2=list(L); line=L2[k]
    if kind=='sink': L2.insert(dest,line); del L2[k if k<dest else k+1]
    else: L2.insert(dest,line); del L2[k+1 if dest<=k else k]
    s=renum(L2)
    d=out/f'{kind}{k}'; d.mkdir(exist_ok=True)
    (d/'m.ll').write_text(mod[:i]+s+mod[j:])
    r=subprocess.run(co.LLC+[str(d/'m.ll'),'-filetype=obj','-o',str(d/'m.o')],capture_output=True,text=True)
    row={'kind':kind,'v':v,'line':k,'to':bn,'from':blk_of[k]['name']}
    if r.returncode: row['err']=r.stderr[-200:]
    else:
        ctok,raw,_=co.obj_tokens(d/'m.o',sym); row.update(co.metrics(otok,ctok,len(raw),w['bytes'])); row['cf']=list(cf.feats(ctok))
    for f in ('m.ll','m.o'): (d/f).unlink(missing_ok=True)
    d.rmdir(); return row
print('candidates',len(cands),sum(c[0]=='sink' for c in cands),'sink',flush=True)
with ThreadPoolExecutor(par) as ex, open(out/'scan.jsonl','a') as f:
    for row in ex.map(one,cands):
        f.write(json.dumps(row)+'\n'); f.flush()
