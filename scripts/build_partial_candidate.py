#!/usr/bin/env python3
"""Build an incomplete program from source and retain an honest whole-file comparison."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,hashlib,json,os,pathlib,subprocess,shutil
from compare import compare
from build_source_manifest import source_manifest
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--manifest',type=pathlib.Path,required=True);p.add_argument('--program',required=True,choices=['pump','pump_amm','pump_fees','mayhem']);p.add_argument('--artifact-name',required=True);p.add_argument('--tools-version',default='v1.52');p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--extra-input',type=pathlib.Path,action='append',default=[],help='Additional repository-local path dependency or build asset to hash (repeatable)');a=p.parse_args()
a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False);manifest=a.manifest.resolve();crate=manifest.parent
workspace=pathlib.Path(subprocess.check_output(['cargo','locate-project','--workspace','--manifest-path',str(manifest),'--message-format','plain'],text=True,cwd=ROOT).strip()).parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def sources():
 return source_manifest(crate,workspace,ROOT,a.extra_input,cwd=ROOT)
# Isolate both mutable build-sbf SDK links and rustup's `solana` alias.
sdk_source=pathlib.Path(shutil.which('cargo-build-sbf')).resolve().parent/'sdk/sbf'
sdk=a.output/'sdk';shutil.copytree(sdk_source,sdk,ignore=shutil.ignore_patterns('dependencies'))
rustup_source=pathlib.Path(os.environ.get('RUSTUP_HOME',str(pathlib.Path.home()/'.rustup')))
rustup=a.output/'rustup';(rustup/'toolchains').mkdir(parents=True)
active=subprocess.check_output(['rustup','show','active-toolchain'],text=True).split()[0]
for entry in (rustup_source/'toolchains').iterdir():
 if entry.name!='solana':(rustup/'toolchains'/entry.name).symlink_to(entry.resolve(),target_is_directory=True)
(rustup/'settings.toml').write_text('version = "12"\ndefault_toolchain = '+json.dumps(active)+'\nprofile = "minimal"\n')
before=sources();cmd=['cargo','build-sbf','--manifest-path',str(manifest),'--tools-version',a.tools_version,'--offline','--sbf-sdk',str(sdk),'--sbf-out-dir',str(a.output/'artifacts'),'--','--locked','--offline']
env=os.environ.copy();env['CARGO_TARGET_DIR']=str(a.output/'target');env['RUSTUP_HOME']=str(rustup)
recorded_env={'CARGO_TARGET_DIR':'<output>/target','RUSTUP_HOME':'<output>/rustup'}
if 'CARGO_HOME' in env:recorded_env['CARGO_HOME']=str(pathlib.Path(env['CARGO_HOME']).resolve()).replace(str(ROOT),'<repo>')
attempt={'scope':'Independent source build attempt; captured binaries are not compiler inputs. Failed attempts establish no binary identity.','program':a.program,'source_sha256':before,'selected_toolchain':a.tools_version,'command':[s.replace(str(a.output),'<output>').replace(str(ROOT),'<repo>') for s in cmd],'environment':recorded_env}
(a.output/'build-attempt.json').write_text(json.dumps(attempt,indent=2)+'\n')
r=subprocess.run(cmd,env=env,text=True,capture_output=True,cwd=ROOT);(a.output/'build.log').write_text(r.stdout+r.stderr)
after=sources();attempt.update(returncode=r.returncode,source_after_sha256=after,source_unchanged=before==after,build_log_sha256=sha((a.output/'build.log').read_bytes()))
(a.output/'build-attempt.json').write_text(json.dumps(attempt,indent=2)+'\n')
r.check_returncode();assert before==after,'source or lockfile changed during build'
binary=a.output/'artifacts'/a.artifact_name
original=ROOT/'evidence/original'/a.program/'deployed.so'
# The reference is read only after compilation has finished.
comparison=compare(original.read_bytes(),binary.read_bytes())
rustc=pathlib.Path.home()/'.cache/solana'/a.tools_version/'platform-tools/rust/bin/rustc'
report={'scope':'Independent clean-target source build. Bounded recovered behavior does not establish complete historical source or a deployable substitute.','program':a.program,'source_sha256':before,'cargo_build_sbf_version':subprocess.check_output(['cargo','build-sbf','--version'],text=True).strip(),'selected_toolchain':a.tools_version,'rustc_version':subprocess.check_output([str(rustc),'--version','--verbose'],text=True).strip(),'rustc_sha256':sha(rustc.read_bytes()),'command':[s.replace(str(a.output),'<output>').replace(str(ROOT),'<repo>') for s in cmd],'environment':recorded_env,'sdk_source_sha256':{str(f.relative_to(sdk_source)):sha(f.read_bytes()) for f in sorted(sdk_source.rglob('*')) if f.is_file() and 'dependencies' not in f.relative_to(sdk_source).parts},'build_log_sha256':sha((a.output/'build.log').read_bytes()),'comparison':comparison}
(a.output/'build-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(comparison,indent=2))
