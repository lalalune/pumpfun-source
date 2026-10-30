#!/usr/bin/env python3
"""Build recovered two-crate quote-selection code; compare unmodified object bytes."""
import argparse,hashlib,json,pathlib,subprocess
from elftools.elf.elffile import ELFFile
ROOT=pathlib.Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--toolchain',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);ap.add_argument('--opt-level',choices=['0','1','2','3','s','z'],default='3');args=ap.parse_args()
args.output.mkdir(parents=True,exist_ok=False);rustc=args.toolchain.resolve()/'rust/bin/rustc';source=ROOT/'programs/pump-fees/recovered';lib=args.output.resolve()/'libpump_fees_math.rlib';obj=args.output.resolve()/'quote_fees.o';commands=[];logs=[]
def build(extra):
 cmd=[str(rustc),'--edition=2021','--target','sbf-solana-solana','-C','opt-level='+args.opt_level,'-C','overflow-checks=yes','-C','panic=abort']+extra
 r=subprocess.run(cmd,text=True,capture_output=True);commands.append(cmd);logs.append(r.stdout+r.stderr)
 # Retain diagnostics before raising so a failed step still leaves its compiler output.
 (args.output/'build.log').write_text('\n'.join(logs));r.check_returncode()
build(['--crate-name','pump_fees_math','--crate-type','rlib',str(source/'fee_selection.rs'),'-o',str(lib)])
build(['--crate-name','pump_quote_fees','--crate-type','lib','--emit=obj','--extern','pump_fees_math='+str(lib),str(source/'quote_fees.rs'),'-o',str(obj)])
build(['--crate-name','recovered_memory','--crate-type','lib','--emit=obj',str(source/'memory_compare.rs'),'-o',str(args.output.resolve()/'memory_compare.o')])
sha=lambda b:hashlib.sha256(b).hexdigest()
with obj.open('rb') as f:
 e=ELFFile(f);data=e.get_section_by_name('.text.get_fees_with_quote').data();relocs=[]
 for sec in e.iter_sections():
  if sec.name not in ['.rel.text.get_fees_with_quote','.rela.text.get_fees_with_quote']:continue
  syms=e.get_section(sec['sh_link'])
  for r in sec.iter_relocations():relocs.append({'offset':r['r_offset'],'type':r['r_info_type'],'symbol':syms.get_symbol(r['r_info_sym']).name})
original=(ROOT/'evidence/original/pump_fees/deployed.so').read_bytes();ref=original[0x3f748:0x3f9d8];diff=[i for i,(x,y) in enumerate(zip(data,ref)) if x!=y];fields=set()
for r in relocs:
 o=r['offset']
 if r['type']==1:fields.update(range(o+4,o+8));fields.update(range(o+12,o+16))
 elif r['type']==10:fields.update(range(o+4,o+8))
def portable(s):return s.replace(str(rustc.parent.parent.parent),'<toolchain>').replace(str(args.output.resolve()),'<output>').replace(str(ROOT),'<repo>')
report={'scope':'Unlinked quote-selector function only. Original bytes never enter compilation and object remains unmodified.','source_sha256':{p:sha((source/p).read_bytes()) for p in ['fee_selection.rs','quote_fees.rs','memory_compare.rs']},'rustc_version':subprocess.check_output([str(rustc),'--version','--verbose'],text=True),'rustc_sha256':sha(rustc.read_bytes()),'commands':[[portable(x) for x in cmd] for cmd in commands],'object_sha256':sha(obj.read_bytes()),'math_rlib_sha256':sha(lib.read_bytes()),'memory_object_sha256':sha((args.output/'memory_compare.o').read_bytes()),'original_program_sha256':sha(original),'original_function_start':0x3f748,'original_function_end':0x3f9d8,'original_function_bytes':len(ref),'compiled_function_bytes':len(data),'original_function_sha256':sha(ref),'compiled_function_sha256':sha(data),'relocations':relocs,'different_byte_offsets':diff,'instruction_match_except_unresolved_relocations':len(ref)==len(data) and not(set(diff)-fields),'whole_program_byte_equality':None}
(args.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['original_function_bytes','compiled_function_bytes','instruction_match_except_unresolved_relocations']}))
