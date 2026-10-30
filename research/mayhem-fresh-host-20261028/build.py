"""Build the host macro, then Mayhem, entirely offline from retained source."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
def run(args):
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
 common=[]
 for n in ['sdk','vendor','msvc','windows_sdk']:common+=['--'+n.replace('_','-'),str(getattr(args,n).resolve())]
 common+=['--kit-version',args.kit_version]
 host=[sys.executable,'-I','-B',str(HERE/'host_build.py'),*common,'--output',str(out/'host')]
 with (out/'host-driver.log').open('wb') as f:result=subprocess.run(host,stdout=f,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError('Host build failed; see retained host-driver.log')
 controller=out/'controller';shutil.copytree(HERE/'controller',controller);(controller/'historical-macro.json').write_bytes((out/'host/macro-binding.json').read_bytes())
 target=[sys.executable,'-I','-B',str(controller/'build.py'),*common,'--target-sysroot',str(args.target_sysroot.resolve()),'--historical-macro-directory',str(out/'host/target/release'),'--output',str(out/'target')]
 with (out/'target-driver.log').open('wb') as f:result=subprocess.run(target,stdout=f,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError('Target build failed; see retained target-driver.log')
 r=json.loads((out/'target/result.json').read_text());expected={'symbols.so':'7b15bb1e5c7c9c53041322fa64d4a420906fffd96ff97a55d70d627bcb854960','candidate-v154-strip.so':'9af9e3b1cbc9d89340af4d9d46e4c88d3dc2fc67e0090f9370047d97532ff09d'}
 for name,digest in expected.items():
  if hashlib.sha256((out/'target'/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Output differs: '+name)
 report=dict(host_command=host,target_command=target,host=json.loads((out/'host/result.json').read_text()),target_outputs=r['outputs'],ordinary_stripped_meaningful_elf_bytes=775416,allocation_tail_emitted=False,target_executions=0)
 (out/'result.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(dict(status='SUCCEEDED',outputs=r['outputs'])),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__)
 for n in ['sdk','target-sysroot','vendor','msvc','windows-sdk','output']:a.add_argument('--'+n,type=Path,required=True)
 a.add_argument('--kit-version',default='10.0.26100.0');run(a.parse_args())
