#!/usr/bin/env python3
# jmis.py <xdir> : jumps aligned (jump-masked alignment) but with a different offset: orig addr, orig off, cand off (insns)
import sys,re,difflib,collections,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a19-cto-framebasis')
def rd(f):
    A=[];T=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); a=int(p[0],16); A.append((a,s)); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        s=re.sub(r'^(j\w+ .*?)([+-]0x[0-9a-f]+|[+-]\d+)$',r'\1J',s); T.append(s)
    return A,T
oa,ot=rd(O+'/orig_fn.txt'); ca,ct=rd(sys.argv[1]+'/fn.txt')
def joff(s):
    m=re.search(r'([+-])0x([0-9a-f]+)$',s) or re.search(r'([+-])(\d+)$',s)
    if not m: return None
    v=int(m.group(2),16) if '0x' in s.split()[-1] else int(m.group(2)); return v if m.group(1)=='+' else -v
H=collections.Counter(); rows=[]
for b in difflib.SequenceMatcher(None,ot,ct,autojunk=False).get_matching_blocks():
    for k in range(b.size):
        a,s=oa[b.a+k]; c,t=ca[b.b+k]
        if s.startswith('j') and s!=t:
            jo,jc=joff(s),joff(t)
            if jo is None or jc is None: continue
            rows.append((a,jo,jc)); H[(a//0x800*0x800)]+=1
print('mismatched jumps',len(rows)); print('per 0x800:',sorted(H.items()))
D=collections.Counter((jc-jo) for a,jo,jc in rows); print('delta (cand-orig insns):',D.most_common(12))
if '-v' in sys.argv:
    for a,jo,jc in rows: print(f'{a:#06x} tgt {a+8+jo*8:#06x} orig {jo:+d} cand {jc:+d} d {jc-jo:+d}')
