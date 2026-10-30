import sys,re
# errw.py <raw.ll> <out.ll> <w_err> <w_ok> [maxline]: add branch_weights making branches into error!-construction blocks unlikely (execute only)
src,dst,we,wo=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]); maxline=int(sys.argv[5]) if len(sys.argv)>5 else 345
t=open(src).read()
F='_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E'
s=t.index('@'+F+'('); s=t.rfind('\ndefine',0,s); e=t.index('\n}\n',s)
body=t[s:e]
# block name -> text
parts=re.split(r'\n(?=[\w.\-$"]+:)',body)
blk={}
for p in parts[1:]:
    name=p.split(':',1)[0].strip('"'); blk[name]=p
def is_err(b,depth=0):
    p=blk.get(b,'')
    if 'PumpError4name' in p or 'ErrorCode$GT$4name' in p:
        m=re.search(r'store i32 (\d+), ptr',p)
        return True
    if depth<2:
        m=re.search(r'\n\s*br label %"?([\w.\-$]+)"?\s*$',p.rstrip())
        if m and len(p.split('\n'))<4: return is_err(m.group(1),depth+1)
    return False
n=0
def fix(m):
    global n
    c,a,b=m.group(1),m.group(2),m.group(3)
    ea,eb=is_err(a),is_err(b)
    if ea==eb: return m.group(0)
    n+=1
    w=(we,wo) if ea else (wo,we)
    return f'br i1 {c}, label %{a}, label %{b}, !prof !{{!"branch_weights", i32 {w[0]}, i32 {w[1]}}}'
nb=re.sub(r'br i1 (%[\w.\-]+), label %"?([\w.\-$]+)"?, label %"?([\w.\-$]+)"?(?=\n)',fix,body)
t=t[:s]+nb+t[e:]
open(dst,'w').write(t); print('weighted',n,file=sys.stderr)
