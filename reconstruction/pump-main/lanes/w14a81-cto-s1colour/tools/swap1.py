# swap1.py fn.bin out.jsonl : every pairwise swap of 8-byte spill colours, plain ratio delta (experiment only)
import sys,os,json
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import chill,slots
c=open(sys.argv[1],'rb').read(); S=[s for s in slots.spill_slots(c) if s<0xff0]; r0=chill.score(c)
def job(p):
    a,b=p; return a,b,chill.score(chill.apply(c,{a:b,b:a}))
if __name__=='__main__':
    P=[(S[i],S[j]) for i in range(len(S)) for j in range(i+1,len(S))]
    with Pool(4) as pool, open(sys.argv[2],'w') as f:
        for a,b,r in pool.imap_unordered(job,P,chunksize=50):
            if r>r0: f.write(json.dumps({'a':hex(a),'b':hex(b),'r':round(r,5),'d':round(r-r0,5)})+'\n')
