#!/usr/bin/env python3
"""Compare a separately built artifact, including allocation padding; never copies code."""
import argparse,hashlib,json,pathlib,sys
from analyze import elf_layout

def digest(b): return hashlib.sha256(b).hexdigest()
def program_names(root):
    path = root / 'repro/programs.json'
    if path.is_file():
        return json.loads(path.read_text())
    return sorted(
        item.name for item in (root / 'evidence/original').iterdir()
        if (item / 'deployed.so').is_file()
    )


def compare(original,candidate):
    first=next((i for i,(a,b) in enumerate(zip(original,candidate)) if a!=b),None)
    if first is None and len(original)!=len(candidate): first=min(len(original),len(candidate))
    return {'original_bytes':len(original),'candidate_bytes':len(candidate),'original_sha256':digest(original),'candidate_sha256':digest(candidate),'full_byte_equality':original==candidate,'first_difference':first,'different_positions_in_shared_length':sum(a!=b for a,b in zip(original,candidate)),'length_difference':len(candidate)-len(original)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('program'); ap.add_argument('candidate',type=pathlib.Path); ap.add_argument('--pad-zero-to-allocation',action='store_true'); ap.add_argument('--output',type=pathlib.Path,required=True); args=ap.parse_args()
    root=pathlib.Path(__file__).resolve().parents[1]
    if args.program not in program_names(root): ap.error('unknown program')
    original=(root/f'evidence/original/{args.program}/deployed.so').read_bytes(); candidate=args.candidate.read_bytes()
    if args.output.exists(): ap.error('output already exists')
    before=digest(candidate)
    if args.pad_zero_to_allocation:
        layout=elf_layout(original)
        if not layout['trailing_all_zero']: ap.error('captured allocation suffix is nonzero')
        if len(candidate)>len(original): ap.error('candidate exceeds allocation')
        elf_layout(candidate)
        candidate+=bytes(len(original)-len(candidate))
    result=compare(original,candidate); result.update({'candidate_input_sha256':before,'zero_padding_requested':args.pad_zero_to_allocation,'source_provenance_verified':False,'note':'Byte equality alone does not prove compilation from source. Original bytes must never be inputs to compilation/linking.'})
    args.output.mkdir(parents=True)
    (args.output/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    if args.pad_zero_to_allocation: (args.output/'candidate.deployed.so').write_bytes(candidate)
    print(json.dumps(result,indent=2)); return 0 if result['full_byte_equality'] else 1
if __name__=='__main__': sys.exit(main())
