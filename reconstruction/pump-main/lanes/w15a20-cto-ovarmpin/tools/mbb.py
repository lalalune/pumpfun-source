import sys,re
# returns list of (phase, [(bbnum, irname, ninstr, calls)])
def parse(p):
    t=open(p).read(); parts=re.split(r'^# \*\*\* IR Dump (Before|After) .*$',t,flags=re.M)
    res={}
    for k in range(1,len(parts),2):
        ph=parts[k]; body=parts[k+1]; bl=[]; cur=None
        for l in body.split('\n'):
            m=re.match(r'^bb\.(\d+)(?:\.([^\s:(]+))?',l)
            if m: cur=[int(m.group(1)),m.group(2) or '',0,[]]; bl.append(cur); continue
            if cur and l.startswith('  ') and l.strip() and not l.strip().startswith(('successors','liveins','predecessors',';')):
                cur[2]+=1
                c=re.search(r'JAL @?"?([\w$.]+)',l) or re.search(r'CALL\w* @"?([\w$.]+)',l)
                if c: cur[3].append(c.group(1)[-45:])
        res[ph]=bl
    return res
if __name__=='__main__':
    r=parse(sys.argv[1]); ph=sys.argv[2] if len(sys.argv)>2 else 'After'
    off=0
    for b in r[ph]:
        print(f'{off:5d} bb.{b[0]} {b[1][:70]} n={b[2]} {" ".join(b[3])[:150]}'); off+=b[2]
