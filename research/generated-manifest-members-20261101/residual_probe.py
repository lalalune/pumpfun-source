#!/usr/bin/env python3
"""Only an owned generated static hash-verifier packet is audited; never the real research tree."""
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
parser=argparse.ArgumentParser(description="Actual static roadmap/audit manifest admission proof.")
parser.add_argument('repository',type=Path)
parser.add_argument('--revision')
parser.add_argument('--expect',choices=('before','fixed'),required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--compare',type=Path)
args=parser.parse_args();ROOT=args.repository.resolve()
BASE=args.revision or subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
NAMES=['scripts/'+n+'.py' for n in ('analyze_program','deep_disassembly','analyze','window_elf_reader','reconstruction_roadmap','revalidate_all')]+['reconstruction/tooling/revalidation-qualification/audit.py']
sha=lambda b:hashlib.sha256(b).hexdigest()
sources={n:subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':'+n]) if args.revision else (ROOT/n).read_bytes() for n in NAMES}
def semantic_payloads(output,cohort):
    def stable(value):
        if isinstance(value,dict):return {k:stable(v) for k,v in value.items() if k!='elapsed_seconds'}
        if isinstance(value,list):return [stable(v) for v in value]
        if isinstance(value,str):return value.replace(str(cohort),'${REPO}')
        return value
    result={}
    for path in sorted(output.iterdir()):
        if path.name in ('manifest.json','verify.py','provenance.json'):continue
        if path.suffix=='.json':data=json.dumps(stable(json.loads(path.read_text())),sort_keys=True).encode()
        else:data=re.sub(r'\| Elapsed \| [^|]*\|','| Elapsed | <duration> |',path.read_text()).encode()
        result[path.name]=sha(data)
    return result
ENV={k:v for k,v in os.environ.items() if k not in ('PYTHONHOME','PYTHONPATH','PYTHONOPTIMIZE')}
ENV['PYTHONHASHSEED']='0'
original_evidence={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in (ROOT/'evidence').rglob('*') if p.is_file()}
rows=[]
with tempfile.TemporaryDirectory(prefix='manifest-residual-static-') as t:
    temp=Path(t).resolve();src=temp/'source'
    for n,b in sources.items():
        p=src/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    shutil.copytree(ROOT/'evidence',src/'evidence')
    input_packet=src/'research/static-mayhem'
    init=subprocess.run([sys.executable,'-B',str(src/'scripts/analyze_program.py'),'--program','mayhem','--output',str(input_packet)],capture_output=True,text=True,env=ENV)
    assert init.returncode==0,init.stderr
    assert sorted(p.name for p in (src/'research').iterdir())==['static-mayhem']
    inputs={p.name:sha(p.read_bytes()) for p in input_packet.iterdir()}
    spec=importlib.util.spec_from_file_location('canonical_static_only',src/'scripts/revalidate_all.py');canonical=importlib.util.module_from_spec(spec);spec.loader.exec_module(canonical)
    commands=[('roadmap','scripts/reconstruction_roadmap.py',[]),('root_revalidation','scripts/revalidate_all.py',[]),('qualified_revalidation','reconstruction/tooling/revalidation-qualification/audit.py',['--repo',str(src)])]
    for label,script,extra in commands:
        output=temp/label
        call=subprocess.run([sys.executable,'-B',str(src/script),*extra,'--output',str(output)],cwd=src,capture_output=True,text=True,env=ENV,timeout=60)
        assert call.returncode==0,(label,call.stderr)
        original=(output/'manifest.json').read_bytes();manifest=json.loads(original);value=manifest['summary.json']
        def dup(key,val):return ('{'+key+':'+json.dumps(val)+','+original.decode().lstrip()[1:]).encode()
        variants={'clean':original,'contradictory_duplicate':dup('"summary.json"','0'*64),'identical_duplicate':dup('"summary.json"',value),'escaped_duplicate':dup('"\\u0073ummary.json"','0'*64),'escaped_unique':original.replace(b'"summary.json"',b'"\\u0073ummary.json"',1),'bad_digest':json.dumps({**manifest,'summary.json':'0'*64}).encode(),'malformed':b'{'}
        cases=[]
        for kind,data in variants.items():
            (output/'manifest.json').write_bytes(data)
            checks=[]
            for flags in ([],['-O'],['-OO']):
                check=subprocess.run([sys.executable,'-B',*flags,str(output/'verify.py')],cwd=output,capture_output=True,text=True,env=ENV)
                success=kind in ('clean','escaped_unique') or (kind.endswith('duplicate') and args.expect=='before')
                assert (check.returncode==0)==success,(label,kind,check.stdout,check.stderr)
                checks.append(check.returncode)
            canon=canonical.check_manifest(output)
            expected='manifest_parse_error' if kind.endswith('duplicate') or kind=='malformed' else 'fail' if kind=='bad_digest' else 'pass'
            assert canon['status']==expected,(label,kind,canon)
            cases.append({'case':kind,'normal_O_OO_exit':checks,'canonical_status':canon['status']})
        (output/'manifest.json').write_bytes(original)
        rows.append({'generator':label,'source':script,'source_sha256':sha(sources[script]),'semantic_payload_sha256':semantic_payloads(output,src),'cases':cases})
        assert inputs=={p.name:sha(p.read_bytes()) for p in input_packet.iterdir()}
    assert all((src/n).read_bytes()==b for n,b in sources.items())
    assert all(sha((src/n).read_bytes())==digest for n,digest in original_evidence.items())
assert all(sha((ROOT/n).read_bytes())==digest for n,digest in original_evidence.items())
result={'base':BASE,'capture_sha256':{n:h for n,h in original_evidence.items() if n.endswith('/deployed.so')},'python_hash_seed':'0','input':'One genuine Mayhem packet generated by unchanged production CLI in a private repo, with no other research directories or executable verifiers. Roadmap reads real retained Pump/AMM/Mayhem captures.','source_sha256':{n:sha(b) for n,b in sources.items()},'actual_generation_calls':4,'actual_emitted_verifier_calls':63,'additional_duplicate_false_passes':27 if args.expect=='before' else 0,'semantic_exclusions':['manifest.json','verify.py','provenance.json','JSON elapsed_seconds fields','owned repo path spelling','README elapsed row'],'input_packet_unchanged':True,'results':rows}
if not args.revision:assert all((ROOT/n).read_bytes()==b for n,b in sources.items())
if args.compare:
    previous=json.loads(args.compare.read_text())
    for old,new in zip(previous['results'],rows):
        assert old['generator']==new['generator']
        assert old['semantic_payload_sha256']==new['semantic_payload_sha256'],new['generator']
path=args.output;path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'generation_calls':4,'verifier_calls':63,'additional_false_passes':result['additional_duplicate_false_passes'],'proof':str(path)}))
