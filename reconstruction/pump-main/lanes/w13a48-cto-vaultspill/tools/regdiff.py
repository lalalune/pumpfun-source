#!/usr/bin/env python3
"""regdiff.py <fn.bin> [step]: per orig region (step bytes), unmatched orig insns under 3 maskings: frame (abs), frame+reg."""
import sys, difflib, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctoracle
def toks(raw):
    t=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; t.append(raw[i:i+n]); i+=n
    return t
def regmask(tok):
    b=bytearray(ctoracle.abstract(tok)); b[1]=0; return bytes(b)
def main():
  otok,w=ctoracle.orig_tokens(); offs=[];o=0
  for t in otok: offs.append(o); o+=len(t)
  step=int(sys.argv[2],0) if len(sys.argv)>2 else 0x800
  res={}
  for p in sys.argv[1].split(','):
      ct=toks(Path(p).read_bytes()); row=[]
      for f in (ctoracle.abstract, regmask):
          sm=difflib.SequenceMatcher(None,[f(t) for t in otok],[f(t) for t in ct],autojunk=False)
          m=[0]*len(otok)
          for a,b,s in sm.get_matching_blocks():
              for k in range(s): m[a+k]=1
          reg={}
          for i,x in enumerate(m):
              r=offs[i]//step; reg[r]=reg.get(r,0)+(1-x)
          row.append((round(sm.ratio(),5),reg))
      res[p]=row
  regs=sorted(res[list(res)[0]][0][1])
  for k,(name,fn) in enumerate((('abs',0),('abs+reg',1))):
      print(name)
      print('region  '+' '.join(f'{Path(p).parent.name[:10]:>10}' for p in res))
      print('ratio   '+' '.join(f'{res[p][k][0]:>10}' for p in res))
      for r in regs: print(f'{r*step:#7x} '+' '.join(f'{res[p][k][1].get(r,0):>10}' for p in res))

if __name__=='__main__': main()
