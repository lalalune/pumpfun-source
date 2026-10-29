#!/usr/bin/env python3
"""Portable multi-hop helper reference audit. Reads input ELFs; emits recomputed JSON only.
CALL identity uses complete official-narrow-normalized callee bodies.
Data checks are bounded objects/classes, not recursive transitive closure.
"""
if not __debug__:
    raise SystemExit("Run without -O")

from pathlib import Path
import argparse,collections,csv,gzip,hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
def sha(b): return hashlib.sha256(b).hexdigest()
def stable_name(n): return re.sub(r'17h[0-9a-f]{16}E$', '17h<HASH>E', n)

class Elf:
    def __init__(self, path):
        self.path=Path(path); raw=self.path.read_bytes(); self.data=gzip.decompress(raw) if self.path.suffix=='.gz' else raw
        assert self.data[:6] == b'\x7fELF\x02\x01'
        shoff=struct.unpack_from('<Q',self.data,40)[0]
        ent,n,ni=struct.unpack_from('<HHH',self.data,58)
        self.headers=[struct.unpack_from('<IIQQQQIIQQ',self.data,shoff+i*ent) for i in range(n)]
        def st(h,x):
            p=h[4]+x; return self.data[p:self.data.index(b'\0',p)].decode('utf-8')
        names=self.headers[ni]
        self.sections={st(names,h[0]):{'type':h[1],'addr':h[3],'offset':h[4],'size':h[5],'index':i}
                       for i,h in enumerate(self.headers)}
        self.symbols=[]
        for h in self.headers:
            if h[1]!=2: continue
            for p in range(h[4],h[4]+h[5],24):
                nm,info,other,sec,addr,size=struct.unpack_from('<IBBHQQ',self.data,p)
                self.symbols.append({'name':st(self.headers[h[6]],nm),'kind':info&15,'section':sec,'address':addr,'size':size})
        ti=self.sections['.text']['index']
        self.functions=[x for x in self.symbols if x['kind']==2 and x['section']==ti and x['size']]
    def section_bytes(self,name):
        s=self.sections[name]; return self.data[s['offset']:s['offset']+s['size']]
    def body(self,address,size):
        s=self.sections['.text']; assert s['addr']<=address<address+size<=s['addr']+s['size']
        p=s['offset']+address-s['addr']; return self.data[p:p+size]
ap=argparse.ArgumentParser(description="Recompute the bounded multi-hop helper CALL and data relocation audit.")
ap.add_argument('--repo-root',type=Path,required=True)
ap.add_argument('--control',type=Path)
ap.add_argument('--candidate',type=Path)
ap.add_argument('--output',type=Path)
args=ap.parse_args();R=args.repo_root.resolve();B=Path(__file__).resolve().parent
es={'original':Elf(R/'evidence/original/pump/deployed.so'),'control':Elf(args.control or B/'build/parent/symbols.so.gz'),'candidate':Elf(args.candidate or B/'build/candidate/symbols.so.gz')}
sys.path.insert(0,str(B/'tools'));from pump_compare_function_bytes import normalize
out={'images':{k:sha(e.data) for k,e in es.items()},'helper':{},'sections':{},'limitations':['Narrow normalized bodies are not raw or recursive transitive identity.','Data reference spans are bounded diagnostics, not complete object identity.']}
for k,e in es.items():
 if k=='original': addr,size=0xa0838,192; target,tsize=0x5b3b0,18584
 else:
  f=next(f for f in e.functions if 'constant_product16tokens_for_quote' in f['name']);addr,size=f['address'],f['size']
  f=next(f for f in e.functions if f['name']=='_ZN14pump_recovered15multi_hop_curve8swap_hop17ha6abe54e52afef15E');target,tsize=f['address'],f['size']
 raw=e.body(addr,size);n,refs=normalize(raw,addr,e.sections);body=e.body(target,tsize);_,trefs=normalize(body,target,e.sections)
 row={'address':addr,'bytes':size,'normalized_sha256':sha(n),'target_call_offsets':[r['offset'] for r in trefs if r['kind']=='direct-call' and r['target']==addr],'refs':refs,'direct_callees':[]}
 for ref in refs:
  if ref['kind']!='direct-call':continue
  ca=ref['target']; cs=504 if k=='original' and ref['offset']==48 else 2136 if k=='original' else next(f['size'] for f in e.functions if f['address']==ca)
  cn,cr=normalize(e.body(ca,cs),ca,e.sections)
  row['direct_callees'].append({'offset':ref['offset'],'address':ca,'bytes':cs,'normalized_sha256':sha(cn),'refs':cr})
 out['helper'][k]=row
for sn in ['.rodata','.data.rel.ro']:
 out['sections'][sn]={k:{'bytes':len(e.section_bytes(sn)),'sha256':sha(e.section_bytes(sn))} for k,e in es.items()}
assert out['helper']['original']['target_call_offsets']==[0x1db0]
assert out['helper']['control']['target_call_offsets']==[]
assert len(out['helper']['candidate']['target_call_offsets'])==1
assert len({(x['bytes'],x['normalized_sha256']) for x in out['helper'].values()})==1
for i in range(2):assert len({(x['direct_callees'][i]['bytes'],x['direct_callees'][i]['normalized_sha256']) for x in out['helper'].values()})==1
out['conclusion']='Candidate restores exactly one original tokens_for_quote call; helper and two direct callee complete narrow-normalized bodies equal across all three images. Control has zero such calls.'
import struct
p,c=es['control'],es['candidate']; sn='.data.rel.ro';pb,cb=p.section_bytes(sn),c.section_bytes(sn); assert len(pb)==len(cb)
rels=[]
for e in [p,c]:
 s=e.sections[sn];rels.append({a-s['addr']:info for a,info in struct.iter_unpack('<QQ',e.section_bytes('.rel.dyn')) if s['addr']<=a<s['addr']+s['size']})
assert rels[0]==rels[1];checked=[];unresolved=[]
def deref(e,word):
 for enc,a in [('direct',word),('high32',word>>32 if word&0xffffffff==0 else -1)]:
  for name,s in e.sections.items():
   if s['addr']>0 and s['addr']<=a<s['addr']+s['size']:return name,a,enc
 raise ValueError(hex(word))
for i in range(0,len(pb),8):
 if i not in rels[0]:
  assert pb[i:i+8]==cb[i:i+8]
  continue
 assert i in rels[0] and rels[0][i]==8
 pn,pa,pe=deref(p,struct.unpack_from('<Q',pb,i)[0]);cn,ca,ce=deref(c,struct.unpack_from('<Q',cb,i)[0]); assert pn==cn and pe==ce
 row={'offset':i,'section':pn,'control':pa,'candidate':ca,'encoding':pe,'changed':pb[i:i+8]!=cb[i:i+8]}
 if pn=='.text':
  pf=next(f for f in p.functions if f['address']==pa);cf=next(f for f in c.functions if f['address']==ca)
  row.update(same_symbol=pf['name']==cf['name'],same_normalized_body=pf['size']==cf['size'] and normalize(p.body(pa,pf['size']),pa,p.sections)[0]==normalize(c.body(ca,cf['size']),ca,c.sections)[0])
  if not row['same_symbol'] or not row['same_normalized_body']:unresolved.append(row)
 else:
  row['same_section_offset']=pa-p.sections[pn]['addr']==ca-c.sections[cn]['addr']
  if not row['same_section_offset']:unresolved.append(row)
 checked.append(row)
out['control_candidate_data']={'rodata_byte_equal':p.section_bytes('.rodata')==c.section_bytes('.rodata'),'relocation_maps_equal':True,'changed_words_all_relocations':True,'relocated_words_checked':checked,'changed_word_count':sum(x['changed'] for x in checked),'unresolved':unresolved}
result=json.dumps(out,indent=2)+'\n'
if args.output:args.output.write_text(result,encoding='utf-8')
else:print(result,end='')





