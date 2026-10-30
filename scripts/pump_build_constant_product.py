#!/usr/bin/env python3
"""Compile the arithmetic fragment unchanged and retain its measured byte mismatch."""
import argparse, hashlib, json, pathlib, subprocess
from elftools.elf.elffile import ELFFile
ROOT=pathlib.Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
RANGE_START=0x880b0
RANGE_END=0x88908

def pinned_original(root):
    """Slice the retained original function only from the pinned capture.

    Python slicing never raises on a short or shifted image, so the whole-file
    SHA-256 is bound to the capture manifest first and the exact slice length
    is checked second; a report must never measure the wrong byte range.
    """
    raw=(root/'evidence/original/pump/deployed.so').read_bytes()
    manifest=json.loads((root/'evidence/original/pump/capture.json').read_text())
    expected=manifest.get('payload_sha256')
    if not expected or sha(raw)!=expected:
        raise SystemExit('captured pump deployed.so does not match its retained capture manifest')
    original=raw[RANGE_START:RANGE_END]
    if len(original)!=RANGE_END-RANGE_START:
        raise SystemExit('captured pump deployed.so is shorter than the pinned original function range')
    return original

p=argparse.ArgumentParser();p.add_argument('--toolchain',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
original=pinned_original(ROOT)
rustc=a.toolchain.resolve()/'rust/bin/rustc';src=ROOT/'programs/pump/recovered/constant_product.rs';obj=a.output.resolve()/'constant_product.o'
cmd=[str(rustc),'--edition=2021','--target','sbf-solana-solana','--crate-type','lib','--emit=obj','-C','opt-level=3','-C','panic=abort','-C','overflow-checks=yes',str(src),'-o',str(obj)]
r=subprocess.run(cmd,text=True,capture_output=True);(a.output/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
with obj.open('rb') as f:compiled=ELFFile(f).get_section_by_name('.text.constant_product_output').data()
locations={str(rustc):'<toolchain>/rust/bin/rustc',str(src):'<repo>/'+src.relative_to(ROOT).as_posix(),str(obj):'<output>/'+obj.name}
report={'scope':'Arithmetic semantics only. Error representation is a compact enum, not original Anchor allocation/metadata, so this fragment does not claim the historical ABI or complete function reconstruction. No original code enters compilation.','source_sha256':sha(src.read_bytes()),'rustc_sha256':sha(rustc.read_bytes()),'rustc_version':subprocess.check_output([str(rustc),'--version','--verbose'],text=True),'command':[locations.get(s,s) for s in cmd],'object_sha256':sha(obj.read_bytes()),'original_function_start':RANGE_START,'original_function_end':RANGE_END,'original_function_bytes':len(original),'compiled_function_bytes':len(compiled),'original_function_sha256':sha(original),'compiled_function_sha256':sha(compiled),'full_function_byte_equality':original==compiled,'whole_program_byte_equality':None}
(a.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
