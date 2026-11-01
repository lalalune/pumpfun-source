import sys,os,subprocess
sys.path.insert(0,os.path.dirname(__file__)); import g
base,dest,genes=sys.argv[1],sys.argv[2],sys.argv[3]
subprocess.run(['rm','-rf',dest]); subprocess.run(['rsync','-a','--exclude','target',base+'/',dest+'/'],check=True)
P={'cto':dest+'/src/creator/admin_cto.rs','lib':dest+'/src/lib.rs'}
S={k:open(v).read() for k,v in P.items()}; N={k:v.count('\n') for k,v in S.items()}
done=set()
for name in [x for x in genes.split('+') if x]:
    for f,a,b in g.G[name]:
        if (f,a,b) in done: continue
        c=S[f].count(a); assert c==1,(name,f,c,a[:100]); S[f]=S[f].replace(a,b); done.add((f,a,b))
for k in S:
    assert S[k].count('\n')==N[k],('line count',k); open(P[k],'w').write(S[k])
print('ok',dest)
