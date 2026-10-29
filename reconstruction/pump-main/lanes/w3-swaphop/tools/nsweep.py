# nsweep.py BASE.ll lo hi : single block moves among blocks [lo,hi) in parallel; prints best by opregs
import sys,os,subprocess,itertools,json
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import nmove
base=sys.argv[1]
def run(op):
    i=os.getpid(); x,y=op
    env=dict(os.environ,MOVES=f'{x}>{y}')
    r=subprocess.run(['python3',os.path.dirname(os.path.abspath(__file__))+'/oracle.py',base,f'sw{i}',os.path.dirname(os.path.abspath(__file__))+'/nmove.py'],capture_output=True,text=True,env=env).stdout
    try:
        f=r.split(); ex=float(f[f.index('exactish')+1]); orr=float(f[f.index('opregs')+1])
    except Exception: return (op,0,0)
    return (op,ex,orr)
if __name__=='__main__':
  lo,hi=int(sys.argv[2]),int(sys.argv[3]); ylo=int(sys.argv[4]) if len(sys.argv)>4 else lo-1
  t=open(base).read(); pre,b,post=nmove.split(t); names=[x[0] for x in b]
  ops=[(names[x],names[y]) for x in range(lo,hi) for y in range(ylo,len(names)) if y!=x and y!=x-1 and x>0]
  print(len(ops),flush=True)
  with Pool(8) as p:res=p.map(run,ops,chunksize=4)
  res.sort(key=lambda r:-r[2])
  json.dump(res,open(base+f'.sweep{lo}-{hi}.json','w'))
  for r in res[:15]: print(r)
