#!/usr/bin/env python3
"""Generate analyst disassembly, never a source rebuild or candidate executable."""
import argparse,hashlib,json,os,pathlib,secrets,shutil,subprocess,tempfile
from analyze import capture_directory, program_names
from deep_disassembly import rename_directory
def fresh_staging(parent, name):
    """Create a run-unique staging directory for one disassembly output.

    The staging name used to be only the output name and the process id,
    so a staging directory left behind by an interrupted run blocked any
    later run that reused the same pid: mkdir failed although the output
    itself was still fresh. Other staging paths in this tree already
    qualify the pid with a random token (probe_report.py, score.py); do
    the same here and retry on the rare collision instead of failing.
    """
    # Leave room for the pid and token under a near-limit output basename.
    prefix = name[:64]
    while len(os.fsencode(prefix)) > 64:
        prefix = prefix[:-1]
    for _ in range(100):
        staging = parent / f'.{prefix}.{os.getpid()}-{secrets.token_hex(8)}'
        try:
            staging.mkdir()
            return staging
        except FileExistsError:
            continue
    raise FileExistsError('could not create a unique disassembly staging directory')
ROOT=pathlib.Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--objdump',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);args=ap.parse_args()
if args.output.exists():ap.error('output already exists')
tool_source=args.objdump.resolve()
tool_bytes=tool_source.read_bytes()
tool_sha256=hashlib.sha256(tool_bytes).hexdigest()
manifest={'tool_sha256':tool_sha256,'outputs':{}}
args.output.parent.mkdir(parents=True,exist_ok=True)
# Plain mkdir preserves the process umask when this directory is published.
staging = fresh_staging(args.output.parent, args.output.name)
try:
    with tempfile.TemporaryDirectory(prefix='disassemble-inputs-') as temporary:
        private=pathlib.Path(temporary)
        inputs={}
        for name in program_names():
            data=(capture_directory(ROOT,name)/'deployed.so').read_bytes()
            directory=private/'inputs'/name;directory.mkdir(parents=True)
            snapshot=directory/'deployed.so';snapshot.write_bytes(data);snapshot.chmod(0o444)
            inputs[name]=(snapshot,hashlib.sha256(data).hexdigest())
        def check_snapshot(path,expected):
            if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise RuntimeError(f'{path.name} snapshot changed during the run')
        def check_inputs():
            for snapshot,digest in inputs.values():check_snapshot(snapshot,digest)
        serial=0
        def run_tool(arguments,**kwargs):
            global serial
            directory=private/f'tool-{serial}';serial+=1
            (directory/'bin').mkdir(parents=True)
            # Keep the common bin/../lib layout used by dynamically linked LLVM.
            # Library bytes are not part of tool_sha256, which names this executable.
            libraries=tool_source.parent.parent/'lib'
            if libraries.is_dir():(directory/'lib').symlink_to(libraries,target_is_directory=True)
            tool=directory/'bin'/args.objdump.name
            tool.write_bytes(tool_bytes);tool.chmod(0o555)
            check_snapshot(tool,tool_sha256);check_inputs()
            result=subprocess.run([str(tool),*arguments],check=True,**kwargs)
            check_snapshot(tool,tool_sha256);check_inputs()
            return result
        manifest['version']=run_tool(['--version'],stdout=subprocess.PIPE,text=True).stdout
        for name,(snapshot,input_sha256) in inputs.items():
            target=staging/f'{name}.asm'
            # A relative input name keeps objdump's file heading deterministic.
            with target.open('wb') as output:
                run_tool(['-d',snapshot.name],cwd=snapshot.parent,stdout=output)
            # Even an image with no code gets a file heading from objdump.
            if not target.stat().st_size:raise RuntimeError(f'{name}: objdump wrote no disassembly')
            manifest['outputs'][name]={'input_sha256':input_sha256,'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (staging/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    rename_directory(staging,args.output)
except BaseException:
    shutil.rmtree(staging,ignore_errors=True)
    raise
