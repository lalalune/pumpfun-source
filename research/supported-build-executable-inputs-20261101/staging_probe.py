"""Actual adapter staging loop followed by an offline host Cargo build."""
import ast,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
repo=Path(sys.argv[1]).resolve();rust=Path(sys.argv[2]).resolve()
module=ast.parse((repo/'scripts/build_supported_sbpf_candidate.py').read_text())
execute=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
stage=next(n for n in ast.walk(execute) if isinstance(n,ast.For) and ast.unparse(n.target)=='(name, digest)' and "source_sha256" in ast.unparse(n.iter))
compiled=compile(ast.fix_missing_locations(ast.Module(body=[stage],type_ignores=[])),str(repo/'scripts/build_supported_sbpf_candidate.py'),'exec')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='supported-executable-') as temporary:
 root=Path(temporary);source=root/'repo/program';(source/'src').mkdir(parents=True);(source/'tools').mkdir()
 (source/'Cargo.toml').write_text('[package]\nname="input-mode-probe"\nversion="0.1.0"\nedition="2021"\n[workspace]\n')
 (source/'src/main.rs').write_text('include!(concat!(env!("OUT_DIR"),"/generated.rs"));fn main(){println!("{}",VALUE);}\n')
 (source/'build.rs').write_text('fn main(){let result=std::process::Command::new("./tools/generate.sh").output().expect("run executable input");assert!(result.status.success());std::fs::write(std::path::Path::new(&std::env::var("OUT_DIR").unwrap()).join("generated.rs"),result.stdout).unwrap();}\n')
 helper=source/'tools/generate.sh';helper.write_text('#!/bin/sh\nprintf "pub const VALUE: u64=37;\\n"\n');helper.chmod(0o755)
 env=dict(os.environ,CARGO_HOME=str(root/'cargo-home'),RUSTC=str(rust/'rustc'),PATH=str(rust)+os.pathsep+os.environ['PATH'])
 subprocess.run([str(rust/'cargo'),'generate-lockfile','--offline'],cwd=source,env=env,check=True,capture_output=True)
 def build(path,target):
  result=subprocess.run([str(rust/'cargo'),'build','--locked','--offline'],cwd=path,env=dict(env,CARGO_TARGET_DIR=str(target)),capture_output=True,text=True,timeout=60)
  return {'returncode':result.returncode,'stderr':result.stderr,'output':subprocess.check_output([str(target/'debug/input-mode-probe')],text=True).strip() if result.returncode==0 else None}
 original=build(source,root/'original-target')
 output=root/'out';planned={'source_sha256':{p.relative_to(root/'repo').as_posix():sha(p) for p in source.rglob('*') if p.is_file()}}
 exec(compiled,{'planned':planned,'repo':root/'repo','output':output,'sha':sha,'shutil':shutil})
 staged=output/'source/program';result=build(staged,root/'staged-target')
 print(json.dumps({'original':original,'staged':result,'original_helper_mode':oct(helper.stat().st_mode&0o777),'staged_helper_mode':oct((staged/'tools/generate.sh').stat().st_mode&0o777)},indent=2))
