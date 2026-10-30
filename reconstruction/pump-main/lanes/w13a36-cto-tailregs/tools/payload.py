import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../w12a02-cto-iroracle/scripts"))
import tail, ctoracle as co
ct=list(tail.toks(sys.argv[1])); n=0
for i in range(len(ct)-1):
    a,b=ct[i],ct[i+1]
    # ldxdw rX,[r10+off] ; ldxdw r7,[r10+off]
    if a[0]==0x79 and (a[1]>>4)==10 and (a[1]&15)==8 and b[0]==0x79 and (b[1]&15)==7 and (b[1]>>4)==10:
        x=bytearray(a); x[1]=(10<<4)|9; ct[i]=bytes(x); n+=1
    # exit block: stxdw [rS+8], r8
    if a[0]==0x7b and (a[1]>>4)==8 and b[0]==0x7b and (b[1]>>4)==7 and ct[i+2][0]==0x95:
        x=bytearray(a); x[1]=(9<<4)|(a[1]&15); ct[i]=bytes(x); n+=1
print('rewrote',n,'ratio',co.metrics(tail.OT,ct,sum(len(t) for t in ct),27400)['ratio'])
