#!/usr/bin/env python3
"""Run an unchanged fixture with explicit captured main-program loader accounts."""
import argparse,sys,hashlib,os,types,importlib.util,io,pkgutil
from pathlib import Path
WRAPPER_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
loader_path=Path(__file__).resolve().with_name('pump_captured_loader.py')
loader_bytes=loader_path.read_bytes()
loader_spec=importlib.util.spec_from_file_location('pump_captured_loader',loader_path)
loader=importlib.util.module_from_spec(loader_spec)
sys.modules[loader_spec.name]=loader
exec(compile(loader_bytes,str(loader_path),'exec'),loader.__dict__)
from probe_report import write_json_report
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path,required=True);p.add_argument('script',type=Path);p.add_argument('arguments',nargs=argparse.REMAINDER);args=p.parse_args()
def same_file(left,right):
    left,right=left.expanduser().resolve(),right.expanduser().resolve()
    if left==right:return True
    try:return left.exists()and right.exists()and os.path.samefile(left,right)
    except OSError:return False
def protected_inputs(script):
    return [Path(__file__).resolve(),loader_path,Path(write_json_report.__code__.co_filename).resolve(),script,loader.ROOT/'evidence/original/pump/capture.json',loader.ROOT/'evidence/original/pump/program-account.bin',loader.ROOT/'evidence/original/pump/programdata-account.bin',loader.ROOT/'evidence/original/pump/deployed.so']
def wrapped_artifact_paths(arguments):
    """Bind the documented fixture candidate/output options before it runs.

    Keep the last occurrence, as argparse does. Other fixture arguments pass
    through unchanged; these are path boundaries, not loader hash inputs.
    """
    values={}
    index=0
    while index<len(arguments):
        option=arguments[index]
        if option=='--':break
        name,separator,value=option.partition('=')
        if name in ('--candidate','--output'):
            if separator:values[name]=value
            elif index+1<len(arguments) and not arguments[index+1].startswith('--'):
                index+=1;values[name]=arguments[index]
        index+=1
    return [Path(value).absolute() for value in values.values()]
script=args.script.expanduser().resolve();paths=protected_inputs(script)
receipt_inputs=[*paths,*wrapped_artifact_paths(args.arguments)]
for path in receipt_inputs:
    if same_file(args.receipt,path):p.error('receipt path aliases protected input: '+str(path))
# Execute the same harness bytes whose digest is recorded. The loader supplies
# digests of the captured account bytes it actually read during import.
harness_bytes=script.read_bytes()
input_sha256=dict(loader.INPUT_SHA256)
input_sha256[str(script)]=hashlib.sha256(harness_bytes).hexdigest()
input_sha256[str(Path(__file__).resolve())]=WRAPPER_SHA256
input_sha256[str(loader_path)]=hashlib.sha256(loader_bytes).hexdigest()
for path in paths:
    if str(path) not in input_sha256:
        input_sha256[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
args.receipt=args.receipt.expanduser().resolve();sys.path.insert(0,str(script.parent));sys.argv=[str(script),*args.arguments]
# The receipt is also written after a failed harness run, so it must say so:
# without an explicit marker a crashed run is indistinguishable from a
# successful reproduction at receipt level.
completed=False;failure=None
try:
    loader.install()
    main=types.ModuleType('__main__');main.__file__=str(script);main.__package__='';main.__cached__=None
    previous_main=sys.modules.get('__main__');sys.modules['__main__']=main
    try:
        code=pkgutil.read_code(io.BytesIO(harness_bytes))
        if code is None:code=compile(harness_bytes,str(script),'exec')
        exec(code,main.__dict__)
    finally:
        if previous_main is None:sys.modules.pop('__main__',None)
        else:sys.modules['__main__']=previous_main
except SystemExit as error:
    completed = error.code is None or (isinstance(error.code, int) and error.code == 0)
    if not completed:failure=f'{type(error).__name__}: {error}'
    raise
except BaseException as error:
    failure=f'{type(error).__name__}: {error}'
    raise
else:
    completed=True
finally:
    try:
        record={'scope':loader.__doc__,'harness':str(script),'input_sha256':input_sha256,'loads':loader.LOADS,'ok':completed}
        if failure is not None:record['error']=failure
        write_json_report(args.receipt,record)
    except Exception:
        if completed:raise  # never mask the harness failure with receipt trouble
