from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
W=Path(__file__).resolve().parent;P=W/'mayhem-trade-arithmetic-lowering';label=sys.argv[1];assert label in ('overflow-early','overflow-late','overflow-early-repeat','overflow-late-repeat');B=W/'mayhem-trade-signer-composition'/('late-inline' if 'late' in label else 'baseline');out=P/label;out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):return dict(bytes=p.stat().st_size,sha256=sha(p))
def snap(p):return {x.relative_to(p).as_posix():sha(x) for x in sorted(p.rglob('*')) if x.is_file()}
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
source=out/'source/programs/mayhem';shutil.copytree(B/'source/programs/mayhem',source);old=json.loads((B/'launch.json').read_bytes());before=snap(source);assert before==old['source_inputs']
p=source/'src/instructions/pump_interface.rs';b=p.read_bytes();original=b
for old_text,new_text in [(b'  let scaled=reference.checked_mul(tolerance_bps as u128);',b'  let (scaled,overflow)=reference.overflowing_mul(tolerance_bps as u128);'),(b'  let delta=scaled.ok_or(MayhemError::MathOverflow)?/10_000;',b'  let delta=if overflow{return Err(MayhemError::MathOverflow);}else{scaled}/10_000;')]:assert b.count(old_text)==1;b=b.replace(old_text,new_text)
assert b.count(b'\n')==original.count(b'\n');p.write_bytes(b);inputs=snap(source);assert [n for n in inputs if inputs[n]!=before[n]]==['src/instructions/pump_interface.rs']
command=old['command'][:];command[command.index('--out-dir')+1]=str(out/'target');(out/'target').mkdir();name='_ZN16mayhem_recovered12instructions14pump_interface19legacy_sell_handler17hf2e4c78980301589E'
if not label.endswith('repeat'):command += ['-C','llvm-args=-print-after=codegenprepare,finalize-isel','-C','llvm-args=-filter-print-funcs='+name]
env=dict(old['environment']);env.update(MAYHEM_LINKER_OUTPUT=str(out/'link'),TEMP=str(out/'temp'),TMP=str(out/'temp'),CARGO_MANIFEST_DIR=str(source),CARGO_MANIFEST_PATH=str(source/'Cargo.toml'));(out/'temp').mkdir()
for collection in ('checked_executables','reused_dependencies'):assert all(sha(Path(n))==h for n,h in old[collection].items())
save(out/'launch.json',dict(command=command,cwd=str(source),environment=env,source_inputs=inputs,parent_source_inputs=before,changed_source_files=['src/instructions/pump_interface.rs'],checked_executables=old['checked_executables'],reused_dependencies=old['reused_dependencies'],parent_launch_sha256=sha(B/'launch.json'),function_filter=name if not label.endswith('repeat') else None,scope='Compose retained PR327 overflowing-product price form with exact PR330 source, optionally with late signer seeds. No original compiler input or target execution.',target_executions=0))
start=time.monotonic();result=dict(status='STARTED',target_executions=0)
try:
    with (out/'stdout.log').open('wb') as so,(out/'stderr.log').open('wb') as se:
        proc=subprocess.Popen(command,cwd=source,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW);save(out/'process.json',dict(pid=proc.pid));code=proc.wait()
    result['returncode']=code;assert code==0,'overflow composition compilation failed'
    shutil.copyfile(out/'target/mayhem_recovered.so',out/'symbols.so');strip=[str(W/'mayhem-native-build/sdk/llvm/bin/llvm-objcopy.exe'),'--strip-all',str(out/'symbols.so'),str(out/'candidate-v154-strip.so')]
    proc=subprocess.run(strip,env=env,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);(out/'strip.stdout.log').write_bytes(proc.stdout);(out/'strip.stderr.log').write_bytes(proc.stderr);result['strip']=dict(command=strip,returncode=proc.returncode);assert proc.returncode==0
    result['outputs']={p.name:identity(p) for p in out.glob('*.so')}
    assert snap(source)==inputs and all(sha(Path(n))==h for key in ('checked_executables','reused_dependencies') for n,h in old[key].items())
    result.update(status='SUCCEEDED',source_unchanged=True,dependencies_unchanged=True)
except Exception as exc:result.update(status='FAILED',error=str(exc));raise
finally:result['elapsed_seconds']=time.monotonic()-start;save(out/'result.json',result)
print(label,result['status'],result.get('outputs'))
