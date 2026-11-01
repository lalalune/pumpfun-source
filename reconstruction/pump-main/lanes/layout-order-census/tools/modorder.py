import sys,re
sys.argv=['x','../../../baseline-main-d2cb88d/unstripped.so','base-refined.json']
src=open('predict.py').read()
exec(src.split('# L at def granularity')[0].replace("run('S","(lambda *a,**k:0)('S"))
sys.path.insert(0,'./worktrees/restore/reconstruction/harness')
from win import demangle
def module(a):
    n=demangle(names[a])
    m=re.search(r'pump_recovered::([a-z_0-9]+)::',n)
    if n.startswith('pump_recovered::') or n.startswith('_<pump_recovered::'):
        if m: return m.group(1)
        return '<root>'
    m=re.search(r'pump_recovered::([a-z_0-9]+)::',n)
    return m.group(1) if m else '<root>'
L=[a for a in noext if region(a)=='L']
oL=sorted(L,key=okey)
runs=[]
for a in oL:
    m=module(a)
    if runs and runs[-1][0]==m: runs[-1][1]+=1
    else: runs.append([m,1,hex(inv[a])])
print('original module runs',len(runs))
for r in runs: print('  O',r)
cr=[]
for a in L:
    m=module(a)
    if cr and cr[-1][0]==m: cr[-1][1]+=1
    else: cr.append([m,1,hex(a)])
print('our module runs',len(cr))
for r in cr: print('  C',r)
