import sys,subprocess
A=sys.argv[1:]; base=A[0]
D={'B12':'label %bb21.i, label %bb13.i','B21':'label %bb25.i, label %bb26.i','B13':'label %bb15.i, label %bb20.i','B7':'label %bb8.i, label %bb20.i','B20':'label %bb42.i, label %bb77.i'}
for v in open(A[1]).read().split('\n'):
    if not v.strip(): continue
    n,*ws=v.split()
    args=[D[w.split('=')[0]]+'='+w.split('=')[1] for w in ws]
    r=subprocess.run(['python3','tools/prof.py',base,n,*args],capture_output=True,text=True); print(r.stdout.strip() or r.stderr[-300:])
    q=subprocess.run(['python3','tools/seq.py',f'tmp/p/{n}.s','bb6.i','24'],capture_output=True,text=True).stdout
    print('   ',' '.join(l.split()[0] for l in q.split('\n') if l.strip()))
