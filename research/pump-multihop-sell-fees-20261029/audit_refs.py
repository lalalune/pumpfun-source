#!/usr/bin/env python3
"""Portable multi-hop helper reference audit. Reads input ELFs; emits recomputed JSON only.
CALL identity uses complete official-narrow-normalized callee bodies.
Data checks are bounded objects/classes, not recursive transitive closure.
"""
if not __debug__:
    raise SystemExit("Run without -O")

from pathlib import Path
import argparse,collections,csv,difflib,gzip,hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
def sha(b): return hashlib.sha256(b).hexdigest()
def symbol_identity(n): return n  # Keep Rust hashes: distinct closures share a stem.

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
                self.symbols.append({'name':st(self.headers[h[6]],nm),'kind':info&15,'binding':info>>4,'visibility':other&3,'section':sec,'address':addr,'size':size})
        ti=self.sections['.text']['index']
        self.functions=[x for x in self.symbols if x['kind']==2 and x['section']==ti and x['size']]
    def section_bytes(self,name):
        s=self.sections[name]; return self.data[s['offset']:s['offset']+s['size']]
    def body(self,address,size):
        s=self.sections['.text']; assert s['addr']<=address<address+size<=s['addr']+s['size']
        p=s['offset']+address-s['addr']; return self.data[p:p+size]
ap=argparse.ArgumentParser(description="Bounded sell sub3 CALL/data audit; no compiler or runtime execution.")
ap.add_argument('--repo-root',type=Path,required=True)
ap.add_argument('--control',type=Path)
ap.add_argument('--candidate',type=Path)
ap.add_argument('--tools-dir',type=Path)
ap.add_argument('--output',type=Path)
ap.add_argument('--compare-retained',action='store_true')
a=ap.parse_args(); R=a.repo_root.resolve(); B=Path(__file__).resolve().parent
sys.path.insert(0,str(a.tools_dir or B/'tools')); from pump_compare_function_bytes import normalize
es={'original':Elf(R/'evidence/original/pump/deployed.so'),'control':Elf(a.control or B/'build/parent/symbols.so.gz'),'candidate':Elf(a.candidate or B/'build/candidate/symbols.so.gz')}
windows={}
with (R/'repro/reconstruction-status-2026-10-26/functions.tsv').open() as f:
 for row in csv.DictReader(f,delimiter='\t'):
  if row['program']=='pump' and row['variant']=='selected':
   lo,hi=int(row['original_start']),int(row['original_end']); windows[lo]=hi-lo

def describe(e,addr,size):
 raw=e.body(addr,size); norm,refs=normalize(raw,addr,e.sections)
 return {'address':addr,'bytes':size,'raw_sha256':sha(raw),'normalized_sha256':sha(norm),'refs':refs}
def fn(e,pattern):
 fs=[f for f in e.functions if pattern in f['name']]; assert len(fs)==1,(pattern,len(fs)); return fs[0]
def described_function(k,addr):
 e=es[k]
 if k=='original':return describe(e,addr,windows[addr])
 fs=[f for f in e.functions if f['address']==addr];assert fs
 d=describe(e,addr,fs[0]['size']);d['symbol']=fs[0]['name'];return d

targets={}; helpers={}
for k,e in es.items():
 if k=='original':ta,ts,ha,hs=0x5b3b0,18584,0x80488,576
 else:
  t=fn(e,'15multi_hop_curve8swap_hop17h');h=fn(e,'5trade4sub317h')
  ta,ts,ha,hs=t['address'],t['size'],h['address'],h['size']
 targets[k]=describe(e,ta,ts);helpers[k]=describe(e,ha,hs)
 helpers[k]['target_call_offsets']=[r['offset'] for r in targets[k]['refs'] if r['kind']=='direct-call' and r['target']==ha]
 helpers[k]['direct_callees']=[described_function(k,r['target'])|{'call_offset':r['offset']} for r in helpers[k]['refs'] if r['kind']=='direct-call']
assert helpers['original']['target_call_offsets']==[0x1c08,0x1d68]
assert helpers['control']['target_call_offsets']==[]
assert len(helpers['candidate']['target_call_offsets'])==1
assert len({(h['bytes'],h['normalized_sha256']) for h in helpers.values()})==1
callee_counts={len(h['direct_callees']) for h in helpers.values()};assert len(callee_counts)==1
for i in range(next(iter(callee_counts))):
 assert len({(h['direct_callees'][i]['call_offset'],h['direct_callees'][i]['bytes'],h['direct_callees'][i]['normalized_sha256']) for h in helpers.values()})==1

# Compare all direct target calls by stable symbols, keeping each occurrence and its offset.
call_lists={}
for k in ['control','candidate']:
 call_lists[k]=[]
 for r in targets[k]['refs']:
  if r['kind']=='direct-call':
   d=described_function(k,r['target']); call_lists[k].append({'offset':r['offset'],'target':r['target'],'symbol':d['symbol'],'symbol_identity':symbol_identity(d['symbol'])})
by_symbol={}
for k,rows in call_lists.items():
 for r in rows:by_symbol.setdefault(r['symbol_identity'],{}).setdefault(k,r['target'])
callees=[]
for name,addresses in sorted(by_symbol.items()):
 d={'symbol_identity':name,'occurrences':{k:sum(r['symbol_identity']==name for r in call_lists[k]) for k in call_lists}}
 for k,addr in addresses.items():d[k]=described_function(k,addr)
 if len(addresses)==2:
  p,c=d['control'],d['candidate'];d['raw_equal']=p['raw_sha256']==c['raw_sha256'];d['narrow_normalized_equal']=(p['bytes'],p['normalized_sha256'])==(c['bytes'],c['normalized_sha256'])
 callees.append(d)

p,c=es['control'],es['candidate'];sn='.data.rel.ro';pb,cb=p.section_bytes(sn),c.section_bytes(sn);assert len(pb)==len(cb)
rels=[]
for e in [p,c]:
 s=e.sections[sn];rels.append({addr-s['addr']:info for addr,info in struct.iter_unpack('<QQ',e.section_bytes('.rel.dyn')) if s['addr']<=addr<s['addr']+s['size']})
assert rels[0]==rels[1]
def deref(e,word):
 for encoding,addr in [('direct',word),('high32',word>>32 if word&0xffffffff==0 else -1)]:
  for name,s in e.sections.items():
   if s['addr']>0 and s['addr']<=addr<s['addr']+s['size']:return name,addr,encoding
 raise ValueError(hex(word))
checked=[];unresolved=[]
for i in range(0,len(pb),8):
 if i not in rels[0]:assert pb[i:i+8]==cb[i:i+8];continue
 assert rels[0][i]==8
 pn,pa,pe=deref(p,struct.unpack_from('<Q',pb,i)[0]);cn,ca,ce=deref(c,struct.unpack_from('<Q',cb,i)[0]);assert pn==cn and pe==ce
 d={'offset':i,'section':pn,'control':pa,'candidate':ca,'encoding':pe,'changed':pb[i:i+8]!=cb[i:i+8]}
 if pn=='.text':
  pf=described_function('control',pa);cf=described_function('candidate',ca)
  d.update(same_symbol=symbol_identity(pf['symbol'])==symbol_identity(cf['symbol']),same_normalized_body=(pf['bytes'],pf['normalized_sha256'])==(cf['bytes'],cf['normalized_sha256']))
  if not d['same_symbol'] or not d['same_normalized_body']:unresolved.append(d)
 else:
  d['same_section_offset']=pa-p.sections[pn]['addr']==ca-c.sections[cn]['addr']
  if not d['same_section_offset']:unresolved.append(d)
 checked.append(d)
# Every target LDDW is retained. Equal section offsets into byte-identical rodata prove the entire section referent;
# data.rel.ro words are covered above. No semantic size is guessed for strings or compound objects.
pointers={}
for k in ['control','candidate']:
 e=es[k];pointers[k]=[]
 for ref in targets[k]['refs']:
  if ref['kind']=='elf-pointer':
   assert len(ref['sections'])==1
   sn=ref['sections'][0];off=ref['value']-e.sections[sn]['addr']
   pointers[k].append({'instruction_offset':ref['offset'],'address':ref['value'],'section':sn,'section_offset':off})
counts=lambda k:collections.Counter((r['section'],r['section_offset']) for r in pointers[k])
pointer_changes=[{'section':sn,'section_offset':off,'control':counts('control')[(sn,off)],'candidate':counts('candidate')[(sn,off)]} for sn,off in sorted(set(counts('control'))|set(counts('candidate'))) if counts('control')[(sn,off)]!=counts('candidate')[(sn,off)]]
# A bounded second edge: references inside each common direct callee. No recursive closure is claimed.
edge_checks=[]
for d in callees:
 if 'control' not in d or 'candidate' not in d:continue
 pr,cr=d['control']['refs'],d['candidate']['refs']; differences=[]
 if len(pr)!=len(cr):differences.append({'reason':'reference count changed'})
 for left,right in zip(pr,cr):
  if (left['offset'],left['kind'])!=(right['offset'],right['kind']):differences.append({'offset':left['offset'],'reason':'reference shape changed'});continue
  if left['kind']=='direct-call':
   lf=described_function('control',left['target']);rf=described_function('candidate',right['target'])
   if (symbol_identity(lf['symbol']),lf['bytes'],lf['normalized_sha256'])!=(symbol_identity(rf['symbol']),rf['bytes'],rf['normalized_sha256']):differences.append({'offset':left['offset'],'reason':'callee identity or narrow body differs','control':lf['symbol'],'candidate':rf['symbol']})
  else:
   ls=left['sections'];rs=right['sections']
   if ls!=rs or len(ls)!=1:differences.append({'offset':left['offset'],'reason':'pointer section differs'})
   elif ls==['.text']:
    lf=described_function('control',left['value']);rf=described_function('candidate',right['value'])
    if (symbol_identity(lf['symbol']),lf['bytes'],lf['normalized_sha256'])!=(symbol_identity(rf['symbol']),rf['bytes'],rf['normalized_sha256']):differences.append({'offset':left['offset'],'reason':'function pointer identity or narrow body differs'})
   elif left['value']-p.sections[ls[0]]['addr']!=right['value']-c.sections[rs[0]]['addr']:differences.append({'offset':left['offset'],'reason':'pointer section offset differs'})
 edge_checks.append({'symbol':d['symbol_identity'],'references':len(pr),'differences':differences})
# pub(crate) changed Rust visibility only: inventory all physical named bodies to expose collateral codegen changes.
fp={f['name']:f for f in p.functions};fc={f['name']:f for f in c.functions};changed=[]
for name in sorted(fp.keys()&fc.keys()):
 pf,cf=fp[name],fc[name];pd=describe(p,pf['address'],pf['size']);cd=describe(c,cf['address'],cf['size'])
 if (pd['bytes'],pd['normalized_sha256'])!=(cd['bytes'],cd['normalized_sha256']):changed.append({'symbol':name,'control':{k:pd[k] for k in ['address','bytes','normalized_sha256']},'candidate':{k:cd[k] for k in ['address','bytes','normalized_sha256']}})
helper_source={}
for k,e in es.items():
 h=helpers[k];raw=e.body(h['address'],h['bytes']);ref=next(r for r in h['refs'] if r['offset']==0x190)
 sec=e.sections['.rodata'];off=ref['value']-sec['addr'];path=e.section_bytes('.rodata')[off:off+29]
 code=struct.unpack_from('<i',raw,0x1a8+4)[0];line=struct.unpack_from('<i',raw,0x1b8+4)[0];length=struct.unpack_from('<i',raw,0x1c0+4)[0]
 assert path==b'programs/pump/src/trade_v3.rs' and code==6024 and line==294 and length==29
 helper_source[k]={'error_code':code,'source_line':line,'source_file':path.decode(),'source_file_length':length,'source_path_bytes_equal':True}
 if k!='original':
  f=fn(e,'5trade4sub317h');helper_source[k]['elf_binding']=f['binding'];helper_source[k]['elf_visibility']=f['visibility']
preserved_quote_helper={}
for k,e in es.items():
 if k=='original':addr,size=0xa0838,192
 else:
  f=fn(e,'constant_product16tokens_for_quote17h');addr,size=f['address'],f['size']
 d=describe(e,addr,size);d['target_call_offsets']=[r['offset'] for r in targets[k]['refs'] if r['kind']=='direct-call' and r['target']==addr]
 assert len(d['target_call_offsets'])==1
 preserved_quote_helper[k]=d
assert len({(d['bytes'],d['normalized_sha256']) for d in preserved_quote_helper.values()})==1
assert not unresolved and p.section_bytes('.rodata')==c.section_bytes('.rodata')
assert not pointer_changes and all(not d['differences'] for d in edge_checks)
assert all(d['narrow_normalized_equal'] for d in callees if 'control' in d and 'candidate' in d)
assert not (fp.keys()^fc.keys()) and [d['symbol'] for d in changed]==['_ZN14pump_recovered15multi_hop_curve8swap_hop17ha6abe54e52afef15E']
sequences={k:[r['symbol_identity'] for r in rows] for k,rows in call_lists.items()}
call_sequence_changes=[{'kind':tag,'control_range':[a0,a1],'candidate_range':[b0,b1],'control':sequences['control'][a0:a1],'candidate':sequences['candidate'][b0:b1]} for tag,a0,a1,b0,b1 in difflib.SequenceMatcher(a=sequences['control'],b=sequences['candidate'],autojunk=False).get_opcodes() if tag!='equal']
call_counts={k:{'raw_CALL_opcode_slots':sum(e.body(targets[k]['address'],targets[k]['bytes'])[i]==0x85 for i in range(0,targets[k]['bytes'],8)),'direct_internal_calls':sum(r['kind']=='direct-call' for r in targets[k]['refs'])} for k,e in es.items()}
out={'preserved_tokens_for_quote':preserved_quote_helper,'call_counts':call_counts,'call_sequence_changes':call_sequence_changes,'helper_error_boundary':helper_source,'callee_reference_checks':edge_checks,'physical_named_function_comparison':{'control_count':len(fp),'candidate_count':len(fc),'removed':sorted(fp.keys()-fc.keys()),'added':sorted(fc.keys()-fp.keys()),'narrow_changed':changed},'images':{k:sha(e.data) for k,e in es.items()},'target':targets,'helper':helpers,'target_direct_calls':call_lists,'target_callees':callees,'target_lddw':pointers,'target_lddw_multiset_changes':pointer_changes,'sections':{sn:{k:{'bytes':len(e.section_bytes(sn)),'sha256':sha(e.section_bytes(sn))} for k,e in es.items()} for sn in ['.rodata','.data.rel.ro']},'control_candidate_data':{'rodata_byte_equal':p.section_bytes('.rodata')==c.section_bytes('.rodata'),'relocation_maps_equal':True,'changed_words_all_relocations':True,'relocated_words_checked':checked,'changed_word_count':sum(x['changed'] for x in checked),'unresolved':unresolved},'limitations':['Complete helper and direct-callee narrow-normalized equality does not establish raw or recursive transitive equality.','Target CALL counts and LDDW section offsets are static linear references, not execution-path equivalence.','Original target still has separate buy-side sub3; candidate restores only the sell-side call.','No compiler, VM, signature verification, whole-window gain census, or production behavior is rerun by this audit.']}
result=json.dumps(out,indent=2)+'\n'
if a.compare_retained:assert out==json.loads((B/'audit/reference-audit.json').read_text(encoding='utf8'))
if a.output:a.output.write_bytes(result.encode())
elif a.compare_retained:print(json.dumps({'retained_equal':True,'images':out['images'],'call_counts':call_counts}))
else:print(result,end='')
