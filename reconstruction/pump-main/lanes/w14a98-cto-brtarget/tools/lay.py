import sys,os; T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import relayn, sc, eseq
for p in sys.argv[1:]:
    R=relayn.R; pre,bl,post=R.parse(p); inv={v:k for k,v in relayn.irmap(p).items()}
    print(p, ' '.join(map(str,eseq.seq(sc.fn(p))[:11])))
    print('  ',' '.join(inv.get(n,n) for n,b in bl[11:45]))
