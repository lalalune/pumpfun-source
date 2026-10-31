#!/usr/bin/env python3
"""pairgain.py fn.bin del_off[,del_off..] ins_off : exact slot effect of deleting the given ours instructions
and inserting the same number of junk 8-byte slots at ins_off (ours offset, before deletion). M unchanged if the
deleted tokens are unmatched; prints slots and SequenceMatcher M."""
import sys,os,difflib
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
exec(open(D+'/rx.py').read().split('OUT=os.environ')[0].replace("sys.argv[1:]","[]"))
f=sys.argv[1]; dels=[int(x,0) for x in sys.argv[2].split(',')]; ins=int(sys.argv[3],0)
raw=open(f,'rb').read()
toks=[];i=0
while i<len(raw):
    n=16 if raw[i]==0x18 else 8; toks.append((i,raw[i:i+n])); i+=n
out=[]
J=b'\xff'*8
for off,t in toks:
    if off==ins: out+= [J]*len(dels)
    if off in dels: continue
    out.append(t)
nb=b''.join(out); assert len(nb)==len(raw)
o=mask(orig_window())
for name,b in (('base',raw),('pair',nb)):
    c=mask(b); M=sum(x.size for x in difflib.SequenceMatcher(None,o,c,autojunk=False).get_matching_blocks())
    ob=b''.join(o); cb=b''.join(c)
    print(name,'M',M,'slots',sum(1 for i in range(0,len(ob),8) if ob[i:i+8]!=cb[i:i+8]))
