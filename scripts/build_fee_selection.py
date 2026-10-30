#!/usr/bin/env python3
"""Compile recovered Rust independently, then compare one original function.
No original bytes enter compilation; object remains unmodified, including relocations.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,hashlib,json,pathlib,subprocess
from elftools.elf.elffile import ELFFile
ROOT=pathlib.Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--toolchain',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);args=ap.parse_args()
args.toolchain=args.toolchain.resolve();args.output=args.output.resolve()
args.output.mkdir(parents=True,exist_ok=False)
source=ROOT/'programs/pump-fees/recovered/fee_selection.rs';rustc=args.toolchain/'rust/bin/rustc';obj=args.output/'fee_selection.o'
command=[str(rustc),'--edition=2021','--crate-type','lib','--emit=obj','--target','sbf-solana-solana','-C','opt-level=3','-C','overflow-checks=yes','-C','panic=abort',str(source),'-o',str(obj)]
sha=lambda b:hashlib.sha256(b).hexdigest()
# Hash the inputs before the build: the report binds these hashes, so a later
# change must fail the run instead of certifying bytes that were never compiled.
source_before=sha(source.read_bytes());rustc_before=sha(rustc.read_bytes())
r=subprocess.run(command,capture_output=True,text=True);(args.output/'build.log').write_text(r.stdout+r.stderr,encoding='utf-8',newline='\n');r.check_returncode()
assert sha(source.read_bytes())==source_before,'source changed during build'
assert sha(rustc.read_bytes())==rustc_before,'rustc changed during build'
with obj.open('rb') as f:
 e=ELFFile(f);section=e.get_section_by_name('.text.select_fee_tier');compiled=section.data();relocs=[]
 for s in e.iter_sections():
  if s.name not in ('.rel.text.select_fee_tier','.rela.text.select_fee_tier'):continue
  symbols=e.get_section(s['sh_link'])
  for x in s.iter_relocations(): relocs.append({'offset':x['r_offset'],'type':x['r_info_type'],'symbol':symbols.get_symbol(x['r_info_sym']).name})
original=(ROOT/'evidence/original/pump_fees/deployed.so').read_bytes();start=0xab158;end=0xab2d0;reference=original[start:end]
diffs=[i for i,(x,y) in enumerate(zip(reference,compiled)) if x!=y]
relocation_fields=set()
for r in relocs:
 offset=r['offset']
 if r['type']==1: relocation_fields.update(range(offset+4,offset+8));relocation_fields.update(range(offset+12,offset+16))
 elif r['type']==10: relocation_fields.update(range(offset+4,offset+8))
report={'source_sha256':source_before,'rustc_sha256':rustc_before,'rustc_version':subprocess.check_output([str(rustc),'--version','--verbose'],text=True),'command':command,'object_sha256':sha(obj.read_bytes()),'original_binary_sha256':sha(original),'original_function_start':start,'original_function_end':end,'original_function_bytes':len(reference),'compiled_function_bytes':len(compiled),'compiled_function_sha256':sha(compiled),'original_function_sha256':sha(reference),'first_difference':diffs[0] if diffs else None,'different_byte_offsets':diffs,'relocations':relocs,'instruction_match_except_unresolved_relocations':len(reference)==len(compiled) and not(set(diffs)-relocation_fields),'whole_program_byte_equality':False,'scope':'One unlinked function only. Relocations remain unresolved and object bytes are never patched.'}
# Replace local absolute locations in portable evidence; build command remains reproducible via arguments.
locations={str(rustc):'<toolchain>/rust/bin/rustc',str(source):'<repo>/'+source.relative_to(ROOT).as_posix(),str(obj):'<output>/'+obj.name}
report['command']=[locations.get(x,x) for x in command]
(args.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(report,indent=2))
