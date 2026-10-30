import sys,re
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import ctoracle as co
otok,w=co.orig_tokens(); ctok,n=co.so_tokens(sys.argv[1])
print('base',co.metrics(otok,ctok,n,27400))
# identify error sret sites: call followed by two ldxdw from r10 adjacent slots
def regs(t): return t[1]&15, t[1]>>4
def setdst(t,r): b=bytearray(t); b[1]=(b[1]&0xf0)|r; return bytes(b)
def setsrc(t,r): b=bytearray(t); b[1]=(b[1]&0x0f)|(r<<4); return bytes(b)
c=list(ctok); k=0
for i in range(len(c)-2):
    if c[i][0]==0x85 and c[i+1][0]==0x79 and c[i+2][0]==0x79 and (c[i+1][1]>>4)==10 and (c[i+2][1]>>4)==10:
        d1=c[i+1][1]&15; d2=c[i+2][1]&15
        if (d1,d2)==(8,6): c[i+1]=setdst(c[i+1],9); c[i+2]=setdst(c[i+2],7); k+=1
# exit block stores
for i in range(len(c)):
    if c[i][0]==0x7b and (c[i][1]&15)==4 and (c[i][1]>>4) in (8,6) and c[i+1:i+3] and c[min(i+2,len(c)-1)][0] in (0x7b,0x95):
        pass
print('sites',k,co.metrics(otok,c,n,27400))
