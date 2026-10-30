#!/usr/bin/env python3
"""Generate analyst disassembly, never a source rebuild or candidate executable."""
import argparse,hashlib,json,pathlib,shutil,subprocess,tempfile
from analyze import program_names
ROOT=pathlib.Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(); ap.add_argument('--objdump',type=pathlib.Path,required=True); ap.add_argument('--output',type=pathlib.Path,required=True); args=ap.parse_args()
if args.output.exists(): ap.error('output already exists')
manifest={'tool_sha256':hashlib.sha256(args.objdump.read_bytes()).hexdigest(),'version':subprocess.check_output([str(args.objdump),'--version'],text=True),'outputs':{}}
# Disassemble into a sibling staging directory so a failed run leaves no partial output behind.
args.output.parent.mkdir(parents=True,exist_ok=True)
staging=pathlib.Path(tempfile.mkdtemp(prefix=f'.{args.output.name}.',dir=args.output.parent))
try:
    for name in program_names():
        binary=ROOT/f'evidence/original/{name}/deployed.so'; target=staging/f'{name}.asm'
        with target.open('wb') as out: subprocess.run([str(args.objdump),'-d',str(binary)],stdout=out,check=True)
        manifest['outputs'][name]={'input_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (staging/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    staging.rename(args.output)
except BaseException:
    shutil.rmtree(staging,ignore_errors=True); raise
