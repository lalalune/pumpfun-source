import sys,re
# rcorder.py [fn.bin]: Rc-clone order map of admin_cto::execute (orig vs candidate). Each AccountInfo clone is an
# Rc strong-count increment (ldxdw rP,[rA+0x8|0x10]; ldxdw rX,[rP]; add64 rX,1; jeq rX,0). Prints (accounts offset,
# lam|dat) per clone, side by side, and marks the rows that differ. Experiment only (w15a30-cto-litfamily).
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a109-cto-stitch13/tools')
fn=sys.argv[1] if len(sys.argv)>1 else None
sys.argv=['x']
import dis as D
def defs(L,k,r):
    # most recent instruction before k writing register r (straight-line, ignores branches)
    for j in range(k-1,max(-1,k-60),-1):
        s=L[j][1]
        m=re.match(r'(\w+) r(\d+),',s)
        if m and m.group(2)==r and not s.startswith(('stx','st','j','call')): return j
    return None
def seq(L):
    out=[]
    for k in range(len(L)-3):
        a,s=L[k]
        mm=re.match(r'add64 r(\d+), 1$',s)
        if not mm: continue
        x=mm.group(1)
        if not any(re.match(rf'jeq r{x}, 0',L[k+j][1]) for j in (1,2,3)): continue
        j=defs(L,k,x); 
        m2=re.match(rf'ldxdw r{x}, \[r(\d+)\+0x0\]',L[j][1]) if j is not None else None
        if not m2: out.append((a,'?',L[j][1] if j else None)); continue
        p=m2.group(1); j2=defs(L,j,p)
        m3=re.match(rf'ldxdw r{p}, \[r(\d+)\+(0x[0-9a-f]+)\]',L[j2][1]) if j2 is not None else None
        if not m3: out.append((a,'??',L[j2][1] if j2 else None)); continue
        fo={'0x8':'lam','0x10':'dat'}.get(m3.group(2),m3.group(2)); b=m3.group(1); j3=defs(L,j2,b)
        src=L[j3][1] if j3 is not None else None
        mm4=re.match(rf'ldxdw r{b}, \[r(\d+)([+-]0x[0-9a-f]+)\]',src or '')
        out.append((a,fo,(mm4.group(2) if mm4 else src)))
    return out
o=seq(D.d(D.orig())); m=seq(D.d(open(fn or '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a30-cto-litfamily/rx/M_main/fn.bin','rb').read()))
print(len(o),len(m))
for i in range(max(len(o),len(m))):
    x=o[i] if i<len(o) else None; y=m[i] if i<len(m) else None
    fx=f"{x[0]:6x} {x[1]!s:4s} {str(x[2])[:24]:24s}" if x else ' '*36
    fy=f"{y[0]:6x} {y[1]!s:4s} {str(y[2])[:24]:24s}" if y else ''
    print(fx,'|',fy, '' if (x and y and x[1:]==y[1:]) else '  <<')
