#!/usr/bin/env python3
"""Locate Anchor discriminator comparisons and wrapper calls in original SBF.
This produces addresses for manual recovery, never compiler inputs or rebuilt code.
"""
import hashlib,json,pathlib,re,struct
from analyze import capture_directory, elf_layout, instruction_log_names, program_names
ROOT=pathlib.Path(__file__).resolve().parents[1]
def recover(name, root=ROOT):
 b=(capture_directory(root,name)/'deployed.so').read_bytes(); layout=elf_layout(b)
 text=next(s for s in layout['sections'] if s['name']=='.text')
 if text['type']==8 or text['size']%8: raise ValueError('invalid text extent')
 start=text['offset']; end=start+text['size']; delta=text['address']-start
 instructions=[]; at=start
 while at<end:
  instructions.append(at)
  width=16 if b[at]==0x18 else 8
  if at+width>end: raise ValueError('truncated SBF instruction in text')
  at+=width
 instruction_set=set(instructions)
 relocations=set()
 for s in layout['sections']:
  if s['type'] in (4,9):
   stride=24 if s['type']==4 else 16
   if s['size']%stride: raise ValueError('invalid relocation table')
   for pos in range(s['offset'],s['offset']+s['size'],stride):
    addr,info=struct.unpack_from('<QQ',b,pos)
    if info&0xffffffff and addr<text['address']+text['size'] and addr+8>text['address']:
     rel_off=addr-delta
     if rel_off not in instruction_set: raise ValueError('text relocation does not target a logical instruction')
     relocations.add(rel_off)
 lddw_sites=[pc for pc in instructions if b[pc]==0x18 and pc not in relocations]
 idl=root/f'evidence/upstream/{name}.json'
 if idl.exists(): candidates={i['name']:bytes(i['discriminator']) for i in json.loads(idl.read_text(encoding="utf-8"))['instructions']}
 else:
  names=instruction_log_names(b)
  names=[re.sub(r'(?<!^)(?=[A-Z])','_',n).lower() for n in names]
  candidates={n:hashlib.sha256(('global:'+n).encode()).digest()[:8] for n in names}
 result={}
 for n,d in candidates.items():
  hits=[]
  for pc in lddw_sites:
   if b[pc+4:pc+8]+b[pc+12:pc+16]==d:
    regs=b[pc+1]; j=pc+16
    while j in instruction_set and j<pc+48 and b[j] in (0xbf,0x79) and (b[j+1]&15)!=(regs&15): j+=8
    if j in instruction_set:
     jop,jregs,joff,_=struct.unpack_from('<BBhi',b,j)
     if jop in (0x1d,0x5d) and ((jregs>>4)==(regs&15) or (jregs&15)==(regs&15)):
      target=j+8+joff*8 if jop==0x1d else j+8
      if target in instruction_set:
       calls=[]; cursor=target
       while cursor in instruction_set and cursor<target+256:
        cop,cregs,coff,cimm=struct.unpack_from('<BBhi',b,cursor)
        if cop==0x85 and cregs>>4==1 and cursor not in relocations and cimm!=-1:
         call_target=cursor+8+cimm*8
         if call_target in instruction_set:
          calls.append({'call_address':cursor+delta,'target':call_target+delta}); break
        if cop in (0x05,0x95): break
        cursor+=16 if cop==0x18 else 8
       hits.append({'constant_address':pc+delta,'comparison_address':j+delta,'matched_branch_address':target+delta,'first_direct_calls':calls})
  result[n]={'discriminator':d.hex(),'matches':hits}
 return {'binary_sha256':hashlib.sha256(b).hexdigest(),'basis':'official IDL' if idl.exists() else 'SHA256(global:snake_case(instruction log name)) hypothesis','instructions':result}
def dispatch(root=ROOT):
 """Dispatch report for every selected program, in selector order."""
 return {n:recover(n, root) for n in program_names(root)}
if __name__=='__main__':
 out=dispatch(ROOT)
 (ROOT/'evidence/dispatch-map.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n')
 for name,r in out.items(): print(name,sum(bool(i['matches']) for i in r['instructions'].values()),'/',len(r['instructions']))
