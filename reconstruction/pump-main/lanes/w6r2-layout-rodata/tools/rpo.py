# rpo.py file.mir [pattern...] : rustc reverse postorder (successors visited next_back) and positions of blocks containing patterns
import sys,re
txt=open(sys.argv[1]).read()
blocks={}; order=[]
for m in re.finditer(r'\n    (bb\d+)(?: \(cleanup\))?: \{\n(.*?)\n    \}',txt,re.S):
    b=m.group(1); body=m.group(2); blocks[b]=body; order.append(b)
def succ(b):
    lines=[l for l in blocks[b].split('\n') if l.strip()]
    t=lines[-1]
    if '->' not in t: return []
    tgt=t.split('->',1)[1]
    return re.findall(r'(bb\d+)',tgt)
visited=set(['bb0']); post=[]; stack=[('bb0',list(succ('bb0')))]
while stack:
    b,it=stack[-1]
    pushed=False
    while it:
        s=it.pop()  # next_back
        if s not in visited:
            visited.add(s); stack.append((s,list(succ(s)))); pushed=True; break
    if not pushed:
        post.append(b); stack.pop()
rpo=post[::-1]
pos={b:i for i,b in enumerate(rpo)}
for p in sys.argv[2:]:
    hits=[(pos.get(b),b) for b in blocks if p in blocks[b]]
    print(p, sorted(hits)[:8])
print('blocks',len(blocks),'rpo',len(rpo))
