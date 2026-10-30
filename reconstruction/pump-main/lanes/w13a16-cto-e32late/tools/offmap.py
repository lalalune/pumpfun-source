#!/usr/bin/env python3
"""offmap.py <m.o> [--top N]: align original vs candidate execute on abstracted tokens (r10 offsets,
jump offsets masked); for aligned r10 accesses, print counts of orig_off->cand_off pairs (frame map vote)."""
import sys,re,difflib,collections,subprocess
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a16-cto-e32late'
def load(lines):
    res=[]
    for l in lines:
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip()
        s=re.sub(r'<[^>]*>','',s).strip()
        off=None
        m=re.search(r'\[r10 - (0x[0-9a-f]+)\]',s)
        if m: off=int(m.group(1),16)
        a=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s)
        a=re.sub(r'(goto|j\w+ .*?,) ?[+-]?0x[0-9a-f]+$|goto [+-]?\d+',r'\1J',a)
        a=re.sub(r'(r\d+ = |add64 r\d+, )-0x[0-9a-f]+','\\1-F',a)
        a=re.sub(r'call .*','call',a)
        if a.startswith('mov64') and 'r10' in a: pass
        res.append((a,off,s))
    return res
o=load(open(OUT+'/orig.dis').read().splitlines())
c=load(subprocess.run(['bash',OUT+'/tools/dis.sh',sys.argv[1]],capture_output=True,text=True).stdout.splitlines())
sm=difflib.SequenceMatcher(None,[x[0] for x in o],[x[0] for x in c],autojunk=False)
pairs=collections.Counter(); eq=0; tot=0
for a,b,n in sm.get_matching_blocks():
    for k in range(n):
        x=o[a+k]; y=c[b+k]
        if x[1] is not None and y[1] is not None:
            tot+=1; pairs[(x[1],y[1])]+=1; eq+= x[1]==y[1]
print(f'abs_match_ratio {sm.ratio():.5f} r10_aligned {tot} r10_equal {eq}')
top=int(sys.argv[3]) if len(sys.argv)>3 else 0
if top:
    byo=collections.defaultdict(collections.Counter)
    for (x,y),n in pairs.items(): byo[x][y]+=n
    for x in sorted(byo):
        tot_x=sum(byo[x].values()); y,n=byo[x].most_common(1)[0]
        print(f'{x:#06x} -> {y:#06x} ({n}/{tot_x}) d={y-x:+d}')
