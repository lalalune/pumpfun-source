#!/usr/bin/env python3
"""Run current source-bound adapters with genuine captures and private drift controls."""
import argparse, hashlib, json, os, re, subprocess, sys, tempfile
from pathlib import Path

BASE='a073c5c8e561dfe0f8a842d27aa1b446de140333'
ARCHIVE='research/tooling-roadmap-call-classification-20261029/'
ADAPTERS={
 'reviewed':('reconstruction/diagnostics/roadmap-reviewed-regeneration/generate.py','scripts/reconstruction_roadmap.py'),
 'stable':('reconstruction/diagnostics/roadmap-stable-attribution/generate.py','scripts/reconstruction_roadmap.py'),
 'defined':('reconstruction/diagnostics/defined-dynamic-calls/generate.py','scripts/reconstruction_roadmap.py'),
 'manifest':('reconstruction/diagnostics/manifest-admission/run.py','scripts/revalidate_all.py'),
 'qualified':('reconstruction/tooling/revalidation-qualification/audit.py','scripts/revalidate_all.py'),
}
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def semantic_payloads(output,cohort):
    def stable(value):
        if isinstance(value,dict):return {k:stable(v) for k,v in value.items() if k!='elapsed_seconds'}
        if isinstance(value,list):return [stable(v) for v in value]
        if isinstance(value,str):return value.replace(str(cohort),'${REPO}')
        return value
    result={}
    for path in sorted(output.iterdir()):
        if path.name in ('manifest.json','verify.py','provenance.json','inputs.json','attribution-inputs.json','dynamic-call-inputs.json'):continue
        if path.suffix=='.json':data=json.dumps(stable(json.loads(path.read_text())),sort_keys=True).encode()
        else:data=re.sub(r'\| Elapsed \| [^|]*\|','| Elapsed | <duration> |',path.read_text()).encode()
        result[path.name]=sha(data)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository',type=Path);parser.add_argument('--revision')
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--compare',type=Path)
    args=parser.parse_args();root=args.repository.resolve()
    def git(name,revision):return subprocess.check_output(['git','-C',str(root),'show',revision+':'+name])
    def read(name):return git(name,args.revision) if args.revision else (root/name).read_bytes()
    evidence={p.relative_to(root).as_posix():p.read_bytes() for p in (root/'evidence').rglob('*') if p.is_file()}
    env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME','PYTHONOPTIMIZE')};env['PYTHONHASHSEED']='0'
    rows=[];calls=0
    with tempfile.TemporaryDirectory(prefix='manifest-adapter-controls-') as temporary:
        workspace=Path(temporary).resolve()
        for label,(adapter,changed) in ADAPTERS.items():
            cohort=workspace/label
            names=['scripts/'+name+'.py' for name in ('analyze_program','deep_disassembly','analyze','window_elf_reader','reconstruction_roadmap','revalidate_all')]+[adapter]
            if label in ('reviewed','stable','defined'):
                names += [ARCHIVE+'proof.py',ARCHIVE+'archived/reconstruction_roadmap.py']
            if label=='manifest':names += ['reconstruction/diagnostics/manifest-admission/check.py']
            sources={name:read(name) for name in names}
            for name,raw in {**sources,**evidence}.items():
                path=cohort/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            if label in ('manifest','qualified'):
                seeded=subprocess.run([sys.executable,'-B',str(cohort/'scripts/analyze_program.py'),'--program','mayhem','--output',str(cohort/'research/static-mayhem')],cwd=cohort,env=env,capture_output=True,text=True)
                assert seeded.returncode==0,seeded.stderr
                assert sorted(p.name for p in (cohort/'research').iterdir())==['static-mayhem']
            def run(output):
                nonlocal calls
                calls+=1
                return subprocess.run([sys.executable,'-B',str(cohort/adapter),'--repo',str(cohort),'--output',str(output)],cwd=cohort,env=env,capture_output=True,text=True,timeout=60)
            output=workspace/(label+'-normal');normal=run(output)
            assert normal.returncode==0,(label,normal.stderr)
            if (output/'verify.py').exists():
                checked=subprocess.run([sys.executable,'-B',str(output/'verify.py')],env=env,capture_output=True,text=True)
                assert checked.returncode==0,(label,checked.stdout,checked.stderr)
            payloads=semantic_payloads(output,cohort)
            binding_file={'reviewed':'inputs.json','stable':'attribution-inputs.json','defined':'dynamic-call-inputs.json'}.get(label)
            if binding_file:
                binding=json.loads((output/binding_file).read_text());assert binding[changed]==sha(sources[changed])
            if label=='qualified':
                provenance=json.loads((output/'provenance.json').read_text());assert provenance['reviewed_source']['sha256']==sha(sources[changed])
            mutation=cohort/changed;mutation.write_bytes(sources[changed]+b'\n# unreviewed drift\n')
            bad=workspace/(label+'-drift');rejected=run(bad)
            assert rejected.returncode!=0 and not bad.exists(),(label,rejected.stderr)
            mutation.write_bytes(sources[changed])
            old_admitted=True
            if args.revision is None:
                mutation.write_bytes(git(changed,BASE));old=workspace/(label+'-old');checked=run(old)
                assert checked.returncode!=0 and not old.exists(),(label,checked.stderr)
                old_admitted=False;mutation.write_bytes(sources[changed])
            occupied=workspace/(label+'-occupied');occupied.write_bytes(b'prior report')
            refused=run(occupied);assert refused.returncode!=0 and occupied.read_bytes()==b'prior report'
            assert all((cohort/name).read_bytes()==raw for name,raw in {**sources,**evidence}.items())
            rows.append({'adapter':label,'normal_exit':normal.returncode,'source_sha256':{name:sha(raw) for name,raw in sources.items()},'semantic_payload_sha256':payloads,'drift_rejected':True,'previous_identity_admitted':old_admitted,'occupied_output_preserved':True})
    assert all((root/name).read_bytes()==raw for name,raw in evidence.items())
    result={'source_revision':args.revision or subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),'actual_adapter_cli_calls':calls,'results':rows,'input_evidence_unchanged':True,'limits':'Audit roots contain only one newly generated static packet. Comparison excludes verifier/manifest, source provenance/input bindings, elapsed fields and owned path spelling; source bindings are checked explicitly.'}
    if args.compare:
        prior=json.loads(args.compare.read_text())
        for old,new in zip(prior['results'],rows):
            assert old['adapter']==new['adapter']
            assert old['semantic_payload_sha256']==new['semantic_payload_sha256'],new['adapter']
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'actual_adapter_cli_calls':calls,'adapters':len(rows)}))


if __name__=='__main__':main()
