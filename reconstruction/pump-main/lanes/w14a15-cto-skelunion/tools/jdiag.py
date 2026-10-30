#!/usr/bin/env python3
"""jdiag.py name: for jm-aligned jumps that mismatch, histogram of (orig src region -> orig dst region, delta) where
delta = cand_off - orig_off (insns). Shows which spans need bytes."""
import sys,os,difflib,collections,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a15-cto-skelunion')
def toks(raw):
    out=[];i=0
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8; out.append((i,raw[i:i+n])); i+=n
    return out
def jm(x):
    b=bytearray(oracle.mask([x])[0]) if False else bytearray(x)
    op=b[0]
    if op==0x85: b[1]&=0x0f; b[4:8]=b'\0'*4
    if op==0x18: b[4:8]=b'\0'*4; b[12:16]=b'\0'*4
    isj=(op&7) in (5,6) and op not in (0x85,0x95)
    if isj: b[2:4]=b'\0\0'
    return bytes(b),isj
ot=toks(oracle.orig_window())
def main():
  for n in sys.argv[1:]:
      ct=toks(open(f'{O}/rx/{n}/fn.bin','rb').read())
      A=[jm(x)[0] for _,x in ot]; B=[jm(x)[0] for _,x in ct]
      sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
      H=collections.Counter(); bad=0; good=0
      for a,b,s in sm.get_matching_blocks():
          for k in range(s):
              (oa,ox),(ca,cx)=ot[a+k],ct[b+k]
              if not jm(ox)[1]: continue
              oo=struct.unpack_from('<h',ox,2)[0]; co=struct.unpack_from('<h',cx,2)[0]
              if oo==co: good+=1; continue
              bad+=1; H[(oa//0x800*0x800, (oa+8+oo*8)//0x800*0x800, co-oo)]+=1
      print(n,'jumps ok',good,'bad',bad)
      for (s,d,dl),c in sorted(H.items(),key=lambda x:-x[1])[:25]: print(f'  {s:#06x}->{d:#06x} delta {dl:+d} x{c}')
  
if __name__=='__main__': main()
