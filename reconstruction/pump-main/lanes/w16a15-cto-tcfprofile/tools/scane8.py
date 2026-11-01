import sys,os,glob,json,struct
from collections import Counter
def ins(raw):
    i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; yield i,raw[i:i+n]; i+=n
res=Counter(); ex={}
for fb in glob.glob(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/*/rx/*/fn.bin')):
    raw=open(fb,'rb').read(); regs=[]
    for o,b in ins(raw):
        if b[0]==0x79 and struct.unpack('<h',b[2:4])[0]==0xe8 and 0x2400<=o<0x3e00 and (b[1]>>4)!=10: regs.append(b[1]&15)
    k=tuple(regs); res[k]+=1; ex.setdefault(k,[]).append(fb.split('lanes/')[1])
for k,v in res.most_common(): print(k,v,ex[k][:4])
