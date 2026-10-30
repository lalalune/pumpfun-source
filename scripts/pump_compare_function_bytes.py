#!/usr/bin/env python3
"""Compare complete main-Pump function windows with narrowly masked relocation operands.

Masks internal direct-call immediates and lddw values that point into an ELF
section. Other constants, registers, branch offsets and instruction bytes must
match. Raw equality and the masked operands are reported separately.
"""
import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path

from pump_exact_body_inventory import window_inventory
from pump_quote_control_function_match import sections, candidate_functions

ROOT = Path(__file__).resolve().parents[1]


def normalize(raw, address, image_sections):
    assert len(raw) % 8 == 0, "SBF body must contain complete instruction slots"
    masked = bytearray(raw)
    operands = []
    i = 0
    while i < len(raw):
        op, regs, offset, immediate = struct.unpack_from('<BBhi', raw, i)
        if op == 0x18:
            assert i + 16 <= len(raw)
            value = struct.unpack_from('<I', raw, i+4)[0] | struct.unpack_from('<I', raw, i+12)[0] << 32
            targets = [name for name, sec in image_sections.items()
                       if sec['addr'] > 0 and sec['addr'] <= value < sec['addr'] + sec['size']]
            if targets:
                masked[i+4:i+8] = bytes(4); masked[i+12:i+16] = bytes(4)
                operands.append({'offset':i,'kind':'elf-pointer','value':value,'sections':targets})
            i += 16
        else:
            if op == 0x85 and regs >> 4 == 1 and immediate != -1:
                masked[i+4:i+8] = bytes(4)
                operands.append({'offset':i,'kind':'direct-call','target':address+i+8+immediate*8})
            i += 8
    return bytes(masked), operands


def body(image, sections_, address, size):
    text = sections_['.text']; offset = address-text['addr']+text['offset']
    assert text['addr'] <= address < address+size <= text['addr']+text['size']
    return image[offset:offset+size]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-start',type=lambda s:int(s,0),required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--symbol',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--objdump',default=str(Path.home()/'.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objdump'))
    args=p.parse_args()
    original=(ROOT/'evidence/original/pump/deployed.so').read_bytes();candidate=args.candidate.read_bytes()
    with window_inventory().open() as stream:
        row=next(r for r in csv.DictReader(stream,delimiter='\t') if r['program']=='pump' and r['variant']=='selected' and int(r['original_start'])==args.original_start)
    size=int(row['original_end'])-args.original_start
    original_sections=sections(original);candidate_sections=sections(candidate)
    ob=body(original,original_sections,args.original_start,size)
    on,oo=normalize(ob,args.original_start,original_sections)
    candidates=[]
    for start,length,name in candidate_functions(args.candidate,args.objdump,args.symbol):
        cb=body(candidate,candidate_sections,start,length);cn,co=normalize(cb,start,candidate_sections)
        diffs=[{'offset':i,'original':on[i:i+8].hex(),'candidate':cn[i:i+8].hex()} for i in range(0,max(len(on),len(cn)),8) if on[i:i+8]!=cn[i:i+8]]
        candidates.append({'symbol':name,'start':start,'bytes':length,'raw_equal':ob==cb,'normalized_equal':on==cn,'different_slots':diffs,'operands':co})
    if not candidates:
        p.error('no candidate function symbols matched the requested pattern')
    result={'scope':__doc__,'original_sha256':hashlib.sha256(original).hexdigest(),'candidate_sha256':hashlib.sha256(candidate).hexdigest(),'original_start':args.original_start,'original_bytes':size,'original_operands':oo,'candidates':candidates}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'original_bytes':size,'candidates':[{k:r[k] for k in ['start','bytes','raw_equal','normalized_equal']}|{'different_slots':len(r['different_slots'])} for r in candidates]},indent=2))


if __name__=='__main__':main()
