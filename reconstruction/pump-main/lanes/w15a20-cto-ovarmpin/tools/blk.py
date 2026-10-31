import sys,re
def blocks(p):
    t=open(p).read(); s=t.index('define'); 
    m=re.search(r'\ndefine [^\n]*admin_cto7execute[^\n]*\{\n',t); body=t[m.end():t.index('\n}\n',m.end())]
    bl=[];cur=None
    for l in body.split('\n'):
        mm=re.match(r'^([\w.$"-]+):',l)
        if mm: cur=[mm.group(1),[]]; bl.append(cur); continue
        if cur is None: cur=['entry',[]]; bl.append(cur)
        cur[1].append(l)
    return bl
def sig(b):
    calls=[re.search(r'@([\w$."]+)\(',l) for l in b[1] if ' call ' in l or 'invoke ' in l]
    calls=[c.group(1)[-60:] for c in calls if c and 'llvm.' not in c.group(1)]
    return calls
if __name__=='__main__':
    for i,b in enumerate(blocks(sys.argv[1])):
        c=sig(b); print(i,b[0],len(b[1]),' '.join(c)[:200])
