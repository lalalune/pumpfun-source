#!/usr/bin/env python3
"""ire.py <base m.ll> <name> <edits.py> [FORCE]: post-opt IR edit + RAPRIO llc (sticky, optional forces) with SSC debug.
Prints M, ratio, slots, bytes, window rotation, holder-arg spill weight (SS interval starting at 48r) and the top colour
order. edits.py defines EDITS = list of (old,new) exact single-occurrence replacements or callables t->t. Experiment only."""
import sys,os,json,runpy,subprocess,tempfile,difflib,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); sys.path.insert(0,os.path.dirname(T)+'/t2')
import oracle, winrot
OUT=os.path.dirname(T); LLC=OUT+'/llvmb/bin/llc'
O=oracle.orig_window(); OM=oracle.mask(O)
def edit(t,ed):
    for e in runpy.run_path(ed)['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:160]); t=t.replace(x,y)
    return t
def run(ll,force='',keep=None):
    env=dict(os.environ,RAPRIO_STICKY='1')
    if force: env['RAPRIO_FORCE']=force
    fd,obj=tempfile.mkstemp(suffix='.o',dir=OUT+'/an'); os.close(fd)
    p=subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',ll,'-filetype=obj','-o',obj,'-debug-only=stack-slot-coloring'],env=env,capture_output=True,text=True)
    if p.returncode: os.remove(obj); return {'err':p.stderr[-600:]}
    b=oracle.elf_fn(obj,oracle.KEEP); os.remove(obj)
    if keep: open(keep,'wb').write(b)
    c=oracle.mask(b); M=sum(x.size for x in difflib.SequenceMatcher(None,OM,c,autojunk=False).get_matching_blocks())
    r,sd=oracle.metric(b,O); n,diff,cm=winrot.rot(b)
    # SSC intervals of execute only (the last function block in the log that has SS#)
    t=p.stderr; parts=t.split('********** Stack Slot Coloring **********')
    blk=[x for x in parts if 'SS#' in x]; blk=blk[-1] if blk else t
    pre=blk.split('Color spill slot')[0]
    iv=[(int(a),bb,float(w)) for a,bb,w in re.findall(r'SS#(\d+) \[(\d+[rBeD]?),.*?weight:(\S+)',pre)]
    hold=[(a,w) for a,bb,w in iv if bb=='48r']
    top=sorted(iv,key=lambda x:-x[2])[:8]
    return {'M':M,'ratio':round(r,5),'slots':sd,'bytes':len(b),'rot':n,'hold':(hold[0][0],round(hold[0][1],4)) if hold else None,
            'hold_rank':[a for a,bb,w in sorted(iv,key=lambda x:-x[2])].index(hold[0][0]) if hold else None,
            'top':[f'{a}@{bb}:{w:.3f}' for a,bb,w in top]}
if __name__=='__main__':
    base,name,ed=sys.argv[1:4]; force=sys.argv[4] if len(sys.argv)>4 else ''
    d=os.path.join(OUT,'irx',name); os.makedirs(d,exist_ok=True)
    t=open(base).read()
    if ed!='-': t=edit(t,ed)
    open(d+'/m.ll','w').write(t)
    r=run(d+'/m.ll',force,keep=d+'/fn.bin'); r['name']=name
    if force: r['force']=force
    print(json.dumps(r),flush=True)
