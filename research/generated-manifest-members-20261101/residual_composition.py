#!/usr/bin/env python3
"""Compose the reviewed pin transition and #3925 writer in either order."""
import argparse,hashlib,json,os,resource,signal,subprocess,sys,tempfile
from pathlib import Path

BASE='a073c5c8e561dfe0f8a842d27aa1b446de140333'
WRITER='1b0be728950b66a26b86e92069cd69c6e85ce5bd'
NAME='reconstruction/diagnostics/defined-dynamic-calls/generate.py'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=args.repository.resolve()
    def git(*arguments):return subprocess.check_output(['git','-C',str(root),*arguments])
    original=git('show',BASE+':'+NAME)
    pin=git('diff',BASE,'--',NAME)
    writer=git('diff',BASE,WRITER,'--',NAME)
    assert b'529e187a98c05fc83cb17b80972594897d23a9eef75e30cb55b76341b05bc88a' in pin
    names=['scripts/'+name+'.py' for name in ('reconstruction_roadmap','window_elf_reader','deep_disassembly','analyze')]
    names += ['research/tooling-roadmap-call-classification-20261029/proof.py',
              'research/tooling-roadmap-call-classification-20261029/archived/reconstruction_roadmap.py']
    sources={name:(root/name).read_bytes() for name in names}
    evidence={p.relative_to(root).as_posix():p.read_bytes() for p in (root/'evidence').rglob('*') if p.is_file()}
    env={k:v for k,v in os.environ.items() if k not in ('PYTHONHOME','PYTHONPATH','PYTHONOPTIMIZE')};env['PYTHONHASHSEED']='0'
    def limit():
        resource.setrlimit(resource.RLIMIT_FSIZE,(64,64));signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
    rows=[]
    with tempfile.TemporaryDirectory(prefix='manifest-writer-composition-') as temporary:
        workspace=Path(temporary).resolve()
        for order,patches in (('pin_then_writer',(pin,writer)),('writer_then_pin',(writer,pin))):
            cohort=workspace/order
            for name,raw in {**sources,**evidence,NAME:original}.items():
                path=cohort/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            for patch in patches:
                subprocess.run(['git','apply','--check','-'],cwd=cohort,input=patch,check=True)
                subprocess.run(['git','apply','-'],cwd=cohort,input=patch,check=True)
            combined=(cohort/NAME).read_bytes()
            def run(output,limited=False):
                return subprocess.run([sys.executable,'-B',str(cohort/NAME),'--repo',str(cohort),'--output',str(output)],cwd=cohort,env=env,capture_output=True,text=True,timeout=60,preexec_fn=limit if limited else None)
            output=workspace/(order+'-normal');normal=run(output)
            assert normal.returncode==0,normal.stderr
            packet={p.name:sha(p.read_bytes()) for p in output.iterdir()}
            checked=subprocess.run([sys.executable,'-B',str(output/'verify.py')],capture_output=True,text=True,env=env)
            assert checked.returncode==0,checked.stderr
            retry=workspace/(order+'-retry');failed=run(retry,True)
            assert failed.returncode!=0 and 'File too large' in failed.stderr,failed.stderr
            assert not retry.exists()
            assert not list(workspace.glob('.'+retry.name+'.staging-*'))
            retried=run(retry);assert retried.returncode==0,retried.stderr
            assert packet=={p.name:sha(p.read_bytes()) for p in retry.iterdir()}
            checked=subprocess.run([sys.executable,'-B',str(retry/'verify.py')],capture_output=True,text=True,env=env)
            assert checked.returncode==0,checked.stderr
            assert all((cohort/name).read_bytes()==raw for name,raw in {**sources,**evidence}.items())
            assert (cohort/NAME).read_bytes()==combined
            rows.append({'order':order,'combined_source_sha256':sha(combined),'packet_sha256':packet,'normal_exit':normal.returncode,'write_limit_rejected':True,'no_partial_output':True,'retry_exit':retried.returncode})
    assert rows[0]['combined_source_sha256']==rows[1]['combined_source_sha256']
    assert rows[0]['packet_sha256']==rows[1]['packet_sha256']
    assert all((root/name).read_bytes()==raw for name,raw in {**sources,**evidence}.items())
    result={'base':BASE,'writer_pr':'https://github.com/lalalune/pumpfun-source/pull/3925','writer_head':WRITER,'pin_patch_sha256':sha(pin),'writer_patch_sha256':sha(writer),'generator_cli_calls':6,'emitted_verifier_calls':4,'both_orders_identical':True,'original_inputs_unchanged':True,'results':rows}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'generator_cli_calls':6,'both_orders_identical':True}))


if __name__=='__main__':main()
