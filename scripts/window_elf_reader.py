#!/usr/bin/env python3
"""Read-only instruction-window matching; no executable or normalized bytes are written."""
from pathlib import Path
import hashlib,json,re,struct
REPO=next((p for p in Path(__file__).resolve().parents if (p/'evidence/original/pump_fees/deployed.so').is_file()), Path.cwd())
class Elf:
 def __init__(self,path):
  self.path=path;self.b=path.read_bytes();b=self.b;off=struct.unpack_from('<Q',b,40)[0];size,count,ni=struct.unpack_from('<HHH',b,58);self.raw=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*size) for i in range(count)];ns=self.raw[ni];names=b[ns[4]:ns[4]+ns[5]];self.secs={names[s[0]:].split(b'\0',1)[0].decode():s for s in self.raw};self.text=self.secs['.text'];self.lo=self.text[4];self.hi=self.lo+self.text[5];self.symbols={};self.funcs=[]
  for kind in ['.dynsym','.symtab']:
   if kind not in self.secs:continue
   s=self.secs[kind];st=self.raw[s[6]];strings=b[st[4]:st[4]+st[5]]
   for i,p in enumerate(range(s[4],s[4]+s[5],24)):
    n,info,_,idx,value,length=struct.unpack_from('<IBBHQQ',b,p);name=strings[n:].split(b'\0',1)[0].decode()
    if kind=='.dynsym':self.symbols[i]=name
    if info&15==2 and length and self.lo<=value<self.hi:self.funcs.append({'name':name,'start':value,'size':length})
  self.relocations={};self.entries={f['start'] for f in self.funcs};entry=struct.unpack_from('<Q',b,24)[0]
  if self.lo<=entry<self.hi:self.entries.add(entry)
  if '.rel.dyn' in self.secs:
   s=self.secs['.rel.dyn']
   for i in range(s[4],s[4]+s[5],16):
    at,info=struct.unpack_from('<QQ',b,i);typ=info&0xffffffff;symbol=self.symbols.get(info>>32,'');self.relocations[at]={'type':typ,'symbol':symbol}
    if typ==8:
     ptr=(struct.unpack_from('<I',b,at+4)[0] | (struct.unpack_from('<I',b,at+12)[0]<<32)) if self.lo<=at<self.hi and b[at]==0x18 else struct.unpack_from('<Q',b,at)[0]>>32
     if self.lo<=ptr<self.hi and ptr%8==0:self.entries.add(ptr)
  self.calls={};norm=bytearray(b)
  for at in range(self.lo,self.hi,8):
   # Relocated external calls also use src=1 with imm=-1; they are not
   # self-calls or independent function-entry evidence.
   if b[at]==0x85 and b[at+1]==0x10 and self.relocations.get(at,{}).get('type')!=10:
    imm=struct.unpack_from('<i',b,at+4)[0];target=at+8+imm*8;self.calls[at]=target;norm[at+4:at+8]=bytes(4)
    if self.lo<=target<self.hi and target%8==0:self.entries.add(target)
   if at in self.relocations:
    typ=self.relocations[at]['type']
    if typ==8 and b[at]==0x18:norm[at+4:at+8]=bytes(4);norm[at+12:at+16]=bytes(4)
    elif typ==10 and b[at]==0x85:norm[at+4:at+8]=bytes(4)
  self.normalized=bytes(norm);self.entries=sorted(self.entries)
 def pattern(self,start,size):
  return [{'offset':at-start,**r} for at,r in sorted(self.relocations.items()) if start<=at<start+size]
 def callsites(self,start,size):return [{'offset':at-start,'target':target} for at,target in self.calls.items() if start<=at<start+size]
 def identity(self):return {'path':self.path.relative_to(REPO).as_posix(),'sha256':hashlib.sha256(self.b).hexdigest(),'text_sha256':hashlib.sha256(self.b[self.lo:self.hi]).hexdigest()}
