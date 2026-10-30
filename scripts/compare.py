#!/usr/bin/env python3
"""Compare a separately built artifact, including allocation padding; never copies code."""
import argparse,hashlib,json,pathlib,sys,tempfile
from analyze import elf_layout

def digest(b): return hashlib.sha256(b).hexdigest()
def program_names(root):
    path = root / 'repro/programs.json'
    if path.is_file():
        return json.loads(path.read_text())
    names = {
        item.name for item in (root / 'evidence/original').iterdir()
        if (item / 'deployed.so').is_file()
    }
    if (root / 'evidence/dependencies/donation_relay/deployed.so').is_file():
        names.add('donation_relay')
    return sorted(names)


def compare(original,candidate):
    equal = original == candidate
    if equal:
        first = None
        different = 0
    else:
        first = next((i for i,(a,b) in enumerate(zip(original,candidate)) if a!=b),None)
        if first is None:
            first = min(len(original),len(candidate))
        different = sum(a!=b for a,b in zip(original,candidate))
    return {'original_bytes':len(original),'candidate_bytes':len(candidate),'original_sha256':digest(original),'candidate_sha256':digest(candidate),'full_byte_equality':equal,'first_difference':first,'different_positions_in_shared_length':different,'length_difference':len(candidate)-len(original)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('program'); ap.add_argument('candidate',type=pathlib.Path); ap.add_argument('--pad-zero-to-allocation',action='store_true'); ap.add_argument('--output',type=pathlib.Path,required=True); args=ap.parse_args()
    root=pathlib.Path(__file__).resolve().parents[1]
    if args.program not in program_names(root): ap.error('unknown program')
    capture_group = 'dependencies' if args.program == 'donation_relay' else 'original'
    original=(root/f'evidence/{capture_group}/{args.program}/deployed.so').read_bytes(); candidate=args.candidate.read_bytes()
    if args.output.exists() or args.output.is_symlink(): ap.error('output already exists')
    before=digest(candidate)
    if args.pad_zero_to_allocation:
        layout=elf_layout(original)
        if not layout['trailing_all_zero']: ap.error('captured allocation suffix is nonzero')
        if len(candidate)>len(original): ap.error('candidate exceeds allocation')
        elf_layout(candidate)
        candidate+=bytes(len(original)-len(candidate))
    result=compare(original,candidate); result.update({'candidate_input_sha256':before,'zero_padding_requested':args.pad_zero_to_allocation,'source_provenance_verified':False,'note':'Byte equality alone does not prove compilation from source. Original bytes must never be inputs to compilation/linking.'})
    from deep_disassembly import rename_directory
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.compare-',dir=args.output.parent) as temporary:
        staging=pathlib.Path(temporary)/'result'
        staging.mkdir()  # Retain ordinary umask permissions after publication.
        (staging/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
        if args.pad_zero_to_allocation: (staging/'candidate.deployed.so').write_bytes(candidate)
        # Publish the complete packet without replacing a concurrent output.
        rename_directory(staging,args.output)
    print(json.dumps(result,indent=2)); return 0 if result['full_byte_equality'] else 1
if __name__=='__main__': sys.exit(main())
