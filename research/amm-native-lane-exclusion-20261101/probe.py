"""Two real native_build invocations with a paused genuine Cargo build script.

The isolated metadata map is recorded from this tiny crate's real compiler calls;
Linux/mac metadata are equal only in this fixture. No compiler output is mocked.
"""
import hashlib, importlib.util, json, os, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path
repo=Path(sys.argv[1]).resolve();sdk=Path(sys.argv[2]).resolve()
spec=importlib.util.spec_from_file_location('native_probe',repo/'scripts/amm_sell/native_build.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
CHILD=r'''
import importlib.util,json,sys
from pathlib import Path
repo,sdk,root,build_id,sell,lane_name=sys.argv[1:]
spec=importlib.util.spec_from_file_location('native_child',Path(repo)/'scripts/amm_sell/native_build.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=Path(root);m.SDK=Path(sdk);m.CARGO_HOME=r/'cargo-home';m.HERE=r/'recipe';m.PRISTINE=r/'pristine';m.SEED_TARGET=r/'no-seed'
result=m.build(r/lane_name,build_id,sell=sell,jobs=1)
if result['returncode']:
 result['log_tail']=(Path(result['output_dir'])/'build.log').read_text()[-6000:]
print(json.dumps(result))
'''
with tempfile.TemporaryDirectory(prefix='native-lane-exclusion-') as directory:
 root=Path(directory).resolve();pristine=root/'pristine';crate=pristine/'programs/pump-amm';local=pristine/'crates/native-transfer-fee'
 for p in [crate/'src/instructions/swap',local/'src',root/'recipe']:p.mkdir(parents=True)
 (pristine/'Cargo.toml').write_text('[workspace]\nmembers=["programs/pump-amm","crates/native-transfer-fee"]\nresolver="2"\n[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n')
 (crate/'Cargo.toml').write_text('[package]\nname="pump-amm-recovered"\nversion="0.1.0"\nedition="2021"\n[lib]\nname="pump_amm_recovered"\ncrate-type=["cdylib","lib"]\n[dependencies]\nnative-transfer-fee={path="../../crates/native-transfer-fee"}\n')
 (local/'Cargo.toml').write_text('[package]\nname="native-transfer-fee"\nversion="0.1.0"\nedition="2021"\n')
 (local/'src/lib.rs').write_text('#![no_std]\npub fn value()->u64{0}\n')
 (crate/'src/lib.rs').write_text('#![no_std]\nmod instructions {pub mod swap {pub mod sell;}}\n#[no_mangle]pub extern "C" fn entrypoint(_: *const u8)->u64{instructions::swap::sell::value()+native_transfer_fee::value()}\n#[panic_handler]fn panic(_: &core::panic::PanicInfo)->!{loop{}}\n')
 (crate/'src/instructions/swap/sell.rs').write_text('pub fn value()->u64{1}\n')
 (crate/'build.rs').write_text('fn main(){println!("cargo:rerun-if-env-changed=PROBE_GATE");if let Ok(p)=std::env::var("PROBE_GATE"){let p=std::path::Path::new(&p);std::fs::write(p.join("ready"),b"ready").unwrap();while !p.join("release").exists(){std::thread::sleep(std::time::Duration::from_millis(5));}}}\n')
 (root/'recipe/metadata-map.json').write_text('[]')
 shutil.copy2(repo/'scripts/amm_sell/ordered.ld',root/'recipe/ordered.ld')
 native.SDK=sdk;native.CARGO_HOME=root/'cargo-home';native.HERE=root/'recipe';native.PRISTINE=pristine;native.SEED_TARGET=root/'no-seed'
 ws,harness,target=native.ensure_lane(root/'lane',None)
 capture=root/'capture.py';capture.write_text('#!'+sys.executable+'\nimport os,sys,json\nfrom pathlib import Path\nc,*a=sys.argv[1:]\nif "--target" in a and "--crate-name" in a and any(x.startswith("metadata=") for x in a):\n n=a[a.index("--crate-name")+1];s=next(x for x in a if x.endswith(".rs"));m=next(x[9:] for x in a if x.startswith("metadata="));r={"crate":n,"package":s,"types":[a[i+1] for i,x in enumerate(a) if x=="--crate-type"],"features":sorted(a[i+1] for i,x in enumerate(a) if x=="--cfg" and a[i+1].startswith("feature=")),"linux_metadata":m,"mac_metadata":m,"linux_extra":"","mac_extra":""}\n with open(os.environ["PROBE_MAP"],"a") as f:f.write(json.dumps(r)+"\\n")\nos.execv(c,[c,*a])\n');capture.chmod(0o755)
 env=native.build_environment(harness,target,root,'',1,None);env.update(RUSTC_WRAPPER=str(capture),PROBE_MAP=str(root/'map.jsonl'))
 seed=subprocess.run([str(sdk/'rust/bin/cargo'),'build','--release','--offline','--target','sbpf-solana-solana'],cwd=ws,env=env,capture_output=True,text=True,timeout=60)
 if seed.returncode:raise RuntimeError(seed.stderr)
 rows=[json.loads(line) for line in (root/'map.jsonl').read_text().splitlines()];(root/'recipe/metadata-map.json').write_text(json.dumps(rows))
 shutil.copy2(ws/'Cargo.lock',root/'lane/baseline-ws/Cargo.lock');shutil.copy2(ws/'Cargo.lock',pristine/'Cargo.lock')
 a,b=root/'a.rs',root/'b.rs';a.write_text('pub fn value()->u64{11}\n');b.write_text('pub fn value()->u64{22}\n')
 def command(build_id,sell,lane_name='lane'):return [sys.executable,'-B','-c',CHILD,str(repo),str(sdk),str(root),build_id,str(sell),lane_name]
 def completed(build_id,sell,lane_name='lane'):
  p=subprocess.run(command(build_id,sell,lane_name),capture_output=True,text=True,timeout=60)
  if p.returncode:raise RuntimeError(p.stdout+p.stderr)
  r=json.loads(p.stdout)
  if r['returncode']:raise RuntimeError(json.dumps(r))
  return r
 control_a=completed('control-a',a)
 gate=root/'gate';gate.mkdir();first=second=None
 try:
  first=subprocess.Popen(command('concurrent-a',a),env=dict(os.environ,PROBE_GATE=str(gate)),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  deadline=time.monotonic()+30
  while not (gate/'ready').exists() and first.poll() is None and time.monotonic()<deadline:time.sleep(.01)
  if not (gate/'ready').exists():raise RuntimeError('first build did not reach actual build-script gate: '+repr(first.communicate(timeout=5)))
  second=subprocess.Popen(command('concurrent-b',b),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  deadline=time.monotonic()+15
  while (ws/native.SELL_REL).read_bytes()!=b.read_bytes() and second.poll() is None and time.monotonic()<deadline:time.sleep(.01)
  overwritten=(ws/native.SELL_REL).read_bytes()==b.read_bytes()
  separate=completed('other-b',b,'independent-lane')
  (gate/'release').touch()
  ao,ae=first.communicate(timeout=60);bo,be=second.communicate(timeout=60)
  ar=json.loads(ao) if ao.strip() else {};br=json.loads(bo) if bo.strip() else {}
  control_b=completed('control-b',b)
  print(json.dumps({'compiler':subprocess.check_output([str(sdk/'rust/bin/rustc'),'--version'],text=True).strip(),'seed_metadata_rows':len(rows),'workspace_overwritten_during_first_compile':overwritten,'first_returncode':first.returncode,'second_returncode':second.returncode,'independent_lane_returncode':separate['returncode'],'independent_lane_candidate_sha256':separate.get('candidate_sha256'),'first_record_returncode':ar.get('returncode'),'second_record_returncode':br.get('returncode'),'first_declared_source_sha256':ar.get('sell_sha256'),'source_a_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'first_binary_sha256':ar.get('candidate_sha256'),'control_a_binary_sha256':control_a['candidate_sha256'],'control_b_binary_sha256':control_b['candidate_sha256'],'first_matches_a':ar.get('candidate_sha256')==control_a['candidate_sha256'],'first_matches_b':ar.get('candidate_sha256')==control_b['candidate_sha256'],'first_stderr':ae,'second_stderr':be},indent=2))
 finally:
  (gate/'release').touch()
  for process in (first,second):
   if process is not None and process.poll() is None:os.killpg(process.pid,signal.SIGKILL);process.communicate(timeout=5)
