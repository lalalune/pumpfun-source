"""Real offline Cargo freshness after the production AMM local-source invalidation."""
import ast, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path
repo=Path(sys.argv[1]).resolve();sdk=Path(sys.argv[2]).resolve()
source=(repo/'scripts/amm_sell/native_build.py').read_text();module=ast.parse(source)
with tempfile.TemporaryDirectory(prefix='amm-native-fingerprint-') as directory:
 root=Path(directory).resolve();ws=root/'ws';target=root/'target';crate=ws/'programs/pump-amm';local=ws/'crates/native-transfer-fee'
 for path in [crate/'src',local/'src']:path.mkdir(parents=True)
 (ws/'Cargo.toml').write_text('[workspace]\nmembers=["programs/pump-amm","crates/native-transfer-fee"]\nresolver="2"\n')
 (crate/'Cargo.toml').write_text('[package]\nname="pump-amm-recovered"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nnative-transfer-fee={path="../../crates/native-transfer-fee"}\n')
 (crate/'src/main.rs').write_text('fn main(){println!("{}",native_transfer_fee::value());}\n')
 (local/'Cargo.toml').write_text('[package]\nname="native-transfer-fee"\nversion="0.1.0"\nedition="2021"\n')
 leaf=local/'src/lib.rs';leaf.write_text('pub fn value()->u64{1}\n')
 env=dict(os.environ,CARGO_HOME=str(root/'cargo-home'),CARGO_TARGET_DIR=str(target),RUSTC=str(sdk/'rust/bin/rustc'))
 env.pop('RUSTC_WRAPPER',None);env.pop('RUSTC_WORKSPACE_WRAPPER',None)
 cargo=sdk/'rust/bin/cargo';cmd=[str(cargo),'build','--release','--offline','--verbose']
 first=subprocess.run(cmd,cwd=ws,env=env,capture_output=True,text=True,check=True)
 binary=target/'release/pump-amm-recovered'
 before=subprocess.check_output([str(binary)],text=True).strip()
 future=time.time()+3600
 for p in (target/'release/.fingerprint').rglob('*'):
  if p.is_file():os.utime(p,(future,future))
 leaf.write_text('pub fn value()->u64{2}\n')
 # Execute the actual unchanged touch loop from native_build.build.
 invalidator=next((n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='invalidate_local_crates'),None)
 if invalidator:
  scope={'shutil':shutil};exec(compile(ast.Module(body=[invalidator],type_ignores=[]),'production-local-invalidation','exec'),scope);scope['invalidate_local_crates'](target)
 else:
  function=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='build')
  body=next(n for n in ast.walk(function) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='crate')
  exec(compile(ast.Module(body=[body],type_ignores=[]),'production-local-invalidation','exec'),{'ws':ws,'now':time.time(),'os':os})
 second=subprocess.run(cmd+['--locked'],cwd=ws,env=env,capture_output=True,text=True,check=True)
 after=subprocess.check_output([str(binary)],text=True).strip()
 print(json.dumps({'rustc':subprocess.check_output([str(sdk/'rust/bin/rustc'),'--version'],text=True).strip(),'cargo':subprocess.check_output([str(cargo),'--version'],text=True).strip(),'before_output':before,'changed_source':leaf.read_text().strip(),'after_output':after,'second_build_log':second.stderr},indent=2))
