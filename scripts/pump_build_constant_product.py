#!/usr/bin/env python3
"""Compile the arithmetic fragment unchanged and retain its measured byte mismatch."""
import argparse, hashlib, json, pathlib, subprocess
from elftools.elf.elffile import ELFFile
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--toolchain',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
rustc=a.toolchain.resolve()/'rust/bin/rustc';src=ROOT/'programs/pump/recovered/constant_product.rs';obj=a.output.resolve()/'constant_product.o'
cmd=[str(rustc),'--edition=2021','--target','sbf-solana-solana','--crate-type','lib','--emit=obj','-C','opt-level=3','-C','panic=abort','-C','overflow-checks=yes',str(src),'-o',str(obj)]
r=subprocess.run(cmd,text=True,capture_output=True);(a.output/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
with obj.open('rb') as f:compiled=ELFFile(f).get_section_by_name('.text.constant_product_output').data()
original=(ROOT/'evidence/original/pump/deployed.so').read_bytes()[0x880b0:0x88908]
sha=lambda b:hashlib.sha256(b).hexdigest()
locations={str(rustc):'<toolchain>/rust/bin/rustc',str(src):'<repo>/'+src.relative_to(ROOT).as_posix(),str(obj):'<output>/'+obj.name}
report={'scope':'Arithmetic semantics only. Error representation is a compact enum, not original Anchor allocation/metadata, so this fragment does not claim the historical ABI or complete function reconstruction. No original code enters compilation.','source_sha256':sha(src.read_bytes()),'rustc_sha256':sha(rustc.read_bytes()),'rustc_version':subprocess.check_output([str(rustc),'--version','--verbose'],text=True),'command':[locations.get(s,s) for s in cmd],'object_sha256':sha(obj.read_bytes()),'original_function_start':0x880b0,'original_function_end':0x88908,'original_function_bytes':len(original),'compiled_function_bytes':len(compiled),'original_function_sha256':sha(original),'compiled_function_sha256':sha(compiled),'full_function_byte_equality':original==compiled,'whole_program_byte_equality':None}
(a.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
