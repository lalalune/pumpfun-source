#!/usr/bin/env python3
"""Run an unchanged fixture with explicit captured main-program loader accounts."""
import argparse,sys,json,runpy,hashlib,os
from pathlib import Path
import pump_captured_loader as loader
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path,required=True);p.add_argument('script',type=Path);p.add_argument('arguments',nargs=argparse.REMAINDER);args=p.parse_args()
def same_file(left,right):
    left,right=left.expanduser().resolve(),right.expanduser().resolve()
    if left==right:return True
    try:return left.exists()and right.exists()and os.path.samefile(left,right)
    except OSError:return False
def protected_inputs(script):
    return [Path(__file__),Path(loader.__file__),script,loader.ROOT/'evidence/original/pump/capture.json',loader.ROOT/'evidence/original/pump/program-account.bin',loader.ROOT/'evidence/original/pump/programdata-account.bin']
script=args.script.expanduser().resolve();paths=protected_inputs(script)
for path in paths:
    if same_file(args.receipt,path):p.error('receipt path aliases protected input: '+str(path))
args.receipt=args.receipt.expanduser().resolve();loader.install();sys.path.insert(0,str(script.parent));sys.argv=[str(script),*args.arguments]
try:runpy.run_path(str(script),run_name='__main__')
finally:
    args.receipt.parent.mkdir(parents=True,exist_ok=True);args.receipt.write_text(json.dumps({'scope':loader.__doc__,'harness':str(script),'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths},'loads':loader.LOADS},indent=2)+'\n')
