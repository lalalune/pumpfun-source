# junkmap.py fn.bin out.json : M for a single +8 junk insertion at every instruction boundary
import sys,os,json,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); A=sys.argv[:]
sys.argv=['junkgreedy.py',A[1],'0']
src=open(T+'/junkgreedy.py').read().split("if __name__=='__main__':")[0]
exec(src)
if __name__=='__main__':
    n=len(parse(raw)); offs=[0]
    for b in parse(raw): offs.append(offs[-1]+len(b))
    with mp.get_context('fork').Pool(int(os.environ.get('NP','6'))) as P: res=P.map(ev,[(raw,k) for k in range(1,n)])
    json.dump({'base':M(raw),'res':[(offs[k],m) for k,m in res]},open(A[2],'w'))
