# nmove.py: edit module for oracle: MOVES env "X>Y;..." moves named IR block X right after Y (swap_hop only)
import os,re
def split(t):
    L=t.split('\n')
    s=next(i for i,l in enumerate(L) if l.startswith('define') and '8swap_hop17h' in l)
    h=s
    while not L[h].rstrip().endswith('{'): h+=1
    e=next(i for i in range(h,len(L)) if L[i]=='}')
    blocks=[];cur=['entry',[]]
    for l in L[h+1:e]:
        m=re.match(r'^("[^"]+"|[\w.$-]+):',l)
        if m: blocks.append(cur); cur=[m.group(1),[]]
        cur[1].append(l)
    blocks.append(cur)
    return L[:h+1],blocks,L[e:]
def edit(t):
    pre,blocks,post=split(t)
    for op in os.environ['MOVES'].split(';'):
        x,y=op.split('>')
        bx=next(b for b in blocks if b[0]==x); blocks.remove(bx)
        k=next(i for i,b in enumerate(blocks) if b[0]==y); blocks.insert(k+1,bx)
    body=[l for b in blocks for l in b[1]]
    s0=next(i for i,l in enumerate(pre) if l.startswith('define') and '8swap_hop17h' in l)
    fn='\n'.join(pre[s0:]+body)
    fn=re.sub(r'%(\d+)\b',r'%v\1',fn); fn=re.sub(r'^(\d+):',r'v\1:',fn,flags=re.M)
    return '\n'.join(pre[:s0]+[fn]+post)
