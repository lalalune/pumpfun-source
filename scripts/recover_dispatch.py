#!/usr/bin/env python3
"""Locate Anchor discriminator comparisons and wrapper calls in original SBF.
This produces addresses for manual recovery, never compiler inputs or rebuilt code.
"""
import hashlib,json,pathlib,re,struct
from analyze import elf_layout, program_names
ROOT=pathlib.Path(__file__).resolve().parents[1]
def recover(name, root=ROOT):
 b=(root/f'evidence/original/{name}/deployed.so').read_bytes(); layout=elf_layout(b)
 text=next(s for s in layout['sections'] if s['name']=='.text'); start=text['offset']; end=start+text['size']; delta=text['address']-start
 idl=root/f'evidence/upstream/{name}.json'
 if idl.exists(): candidates={i['name']:bytes(i['discriminator']) for i in json.loads(idl.read_text())['instructions']}
 else:
  names=json.loads((root/'evidence/binary-analysis.json').read_text())[name]['instruction_log_names']
  names=[re.sub(r'(?<!^)(?=[A-Z])','_',n).lower() for n in names]
  candidates={n:hashlib.sha256(('global:'+n).encode()).digest()[:8] for n in names}
 result={}
 for n,d in candidates.items():
  hits=[]; pc=start
  while pc<end:
   op,regs,off,imm=struct.unpack_from('<BBhi',b,pc)
   if op==0x18:
    if b[pc+4:pc+8]+b[pc+12:pc+16]==d:
     j=pc+16
     while j<pc+48 and b[j] in (0xbf,0x79) and (b[j+1]&15)!=(regs&15): j+=8
     jop,jregs,joff,_=struct.unpack_from('<BBhi',b,j)
     if jop in (0x1d,0x5d) and ((jregs>>4)==(regs&15) or (jregs&15)==(regs&15)):
      target=j+8+joff*8 if jop==0x1d else j+8; calls=[]; cursor=target
      while start<=cursor<end and cursor<target+256:
       cop,cregs,coff,cimm=struct.unpack_from('<BBhi',b,cursor)
       if cop==0x85 and cregs>>4==1: calls.append({'call_address':cursor+delta,'target':cursor+8+cimm*8+delta}); break
       if cop in (0x05,0x95): break
       cursor+=16 if cop==0x18 else 8
      hits.append({'constant_address':pc+delta,'comparison_address':j+delta,'matched_branch_address':target+delta,'first_direct_calls':calls})
    pc+=16
   else: pc+=8
  result[n]={'discriminator':d.hex(),'matches':hits}
 return {'binary_sha256':hashlib.sha256(b).hexdigest(),'basis':'official IDL' if idl.exists() else 'SHA256(global:snake_case(instruction log name)) hypothesis','instructions':result}
def dispatch(root=ROOT):
 """Dispatch report for every selected program, in selector order."""
 return {n:recover(n, root) for n in program_names()}
if __name__=='__main__':
 out=dispatch(ROOT)
 (ROOT/'evidence/dispatch-map.json').write_text(json.dumps(out,indent=2)+'\n')
 for name,r in out.items(): print(name,sum(bool(i['matches']) for i in r['instructions'].values()),'/',len(r['instructions']))
