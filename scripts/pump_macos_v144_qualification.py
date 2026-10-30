#!/usr/bin/env python3
"""Build frozen Pump inputs using the pinned macOS compiler/Linux SBF profile."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
from pathlib import Path
from collections import Counter
from functools import lru_cache
import gzip,hashlib,importlib.util,json,os,platform,shutil,subprocess,sys,tarfile,urllib.request
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/pump-macos-qualification'
EVIDENCE=OUT/'evidence'
SPEC=ROOT/'research/pump-macos-v144-qualification-20261027/inputs.json'
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def run(name,args,env=None):
    with (EVIDENCE/(name+'.log')).open('w')as log:
        p=subprocess.run([str(x)for x in args],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    row={'name':name,'command':[str(x)for x in args],'returncode':p.returncode}
    with (EVIDENCE/'commands.jsonl').open('a')as f:f.write(json.dumps(row)+'\n')
    p.check_returncode()
def archive(destination,source):
    # Pin the gzip header mtime: the archives are hashed into MANIFEST.json,
    # and a wall-clock header made identical inputs hash differently per run.
    with open(destination,'wb')as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0)as compressed,tarfile.open(fileobj=compressed,mode='w')as t:
        for p in sorted(source.rglob('*')):
            if p.is_file():t.add(p,arcname=p.relative_to(source))
def retain(build,label):
    if not build.exists():return
    d=EVIDENCE/label;d.mkdir(exist_ok=True)
    for name in ['candidate.so','unstripped.so','build.log','build-comparison.json','build-attempt.json','build-plan.json','target-library-profile-files.json','archive-reproduction.json']:
        p=build/name
        if p.is_file():(d/(name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
    if(build/'link').is_dir():archive(d/'link-inputs.tar.gz',build/'link')
    for name in ['ordered.ld','data-order-certificate.json']:
        if(build/name).is_file():shutil.copyfile(build/name,d/name)
def main():
    EVIDENCE.mkdir(parents=True,exist_ok=False)
    spec=json.loads(SPEC.read_text());shutil.copyfile(SPEC,EVIDENCE/'inputs.json')
    (EVIDENCE/'revision.txt').write_text(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True),encoding='utf-8',newline='\n')
    shutil.copyfile(Path(__file__),EVIDENCE/'qualification.py')
    shutil.copyfile(ROOT/'.github/workflows/qualify-pump-macos-v144.yml',EVIDENCE/'workflow.yml')
    (EVIDENCE/'host.json').write_text(json.dumps({'system':platform.system(),'machine':platform.machine(),'python':sys.version},indent=2)+'\n',encoding='utf-8',newline='\n')
    assert platform.system()=='Darwin'and platform.machine()=='arm64','Requires the standard Apple Silicon macOS runner'
    for label,definition in spec['archives'].items():
        path=OUT/(label+'.tar.bz2')
        with urllib.request.urlopen(definition['url'])as response,path.open('wb')as f:shutil.copyfileobj(response,f)
        assert sha(path)==definition['sha256'],label
        destination=OUT/label;destination.mkdir()
        with tarfile.open(path)as t:t.extractall(destination,filter='data')
    sdk=OUT/'macos';libraries=OUT/'linux/rust/lib/rustlib/sbf-solana-solana/lib'
    profile=json.loads((ROOT/'scripts/pump_linux_v144_sbf_libraries.json').read_text())
    assert all(sha(sdk/name)==digest for name,digest in profile['native_tools'].items())
    assert {p.name:sha(p)for p in libraries.iterdir()if p.is_file()}==profile['target_libraries']
    primary=OUT/'primary';primary.mkdir();source=ROOT/spec['primary_archive']
    assert sha(source)==spec['primary_archive_sha256']
    with tarfile.open(source)as t:t.extractall(primary,filter='data')
    registry=OUT/'registry';env=dict(os.environ,CARGO_HOME=str(registry),RUSTC=str(sdk/'rust/bin/rustc'),PATH=str(sdk/'rust/bin')+os.pathsep+os.environ['PATH'])
    run('fetch',[sdk/'rust/bin/cargo','fetch','--locked','--manifest-path',primary/'Cargo.toml'],env)
    common=[sys.executable,'-B',ROOT/'scripts/pump_build_verified.py','--sdk',sdk,'--workspace-layout','--target-library-profile','linux-v1.44-sbf','--target-library-directory',libraries]
    baseline=OUT/'baseline';candidate=OUT/'candidate';repeat=OUT/'repeat';canonical=OUT/'round37-canonical'
    builds=[(baseline,'baseline'),(candidate,'candidate'),(repeat,'repeat'),(canonical.with_name(canonical.name+'-identity'),'round37-identity'),(canonical,'round37-canonical')]
    try:
        run('baseline',common+['--source-directory','programs/pump','--registry-home',registry,'--output',baseline])
        cached=['--registry-home',baseline/'cargo-home','--dependency-cache',OUT/'external-cache']
        run('candidate',common+['--source-directory',primary,*cached,'--dependency-cache-seed',baseline,'--output',candidate])
        run('repeat',common+['--source-directory',primary,*cached,'--output',repeat])
        run('round37-canonical',[sys.executable,'-B',ROOT/'repro/pump/main-contract-round37-20261027/reproduce.py','--sdk',sdk,'--registry-home',baseline/'cargo-home','--dependency-cache',OUT/'external-cache','--target-library-directory',libraries,'--output',canonical])
        assert all((candidate/n).read_bytes()==(repeat/n).read_bytes()for n in ['candidate.so','unstripped.so'])
        helper=ROOT/spec['window_reader'];module=importlib.util.spec_from_file_location('qualification_windows',helper);w=importlib.util.module_from_spec(module);module.loader.exec_module(w)
        w.m.elf_layout=lru_cache(maxsize=8)(w.m.elf_layout);w.m.relocations=lru_cache(maxsize=8)(w.m.relocations)
        original=(ROOT/'evidence/original/pump/deployed.so').read_bytes();ow=w.windows(original);oc=Counter(x['signature']for x in ow);assert len(ow)==1035
        counters={};measurement={'original_sha256':hashlib.sha256(original).hexdigest(),'whole_elf_equal':False,'builds':{}}
        for path,label in builds:
            rows=w.windows((path/'unstripped.so').read_bytes());cc=Counter(x['signature']for x in rows);counters[label]=cc
            measurement['builds'][label]={'normalized_matches':sum((oc&cc).values()),'candidate_sha256':sha(path/'candidate.so'),'unstripped_sha256':sha(path/'unstripped.so')}
        assert measurement['builds']['baseline']['normalized_matches']==744
        assert measurement['builds']['candidate']['normalized_matches']>=778
        assert sum(((oc&counters['baseline'])&counters['candidate']).values())==744
        assert measurement['builds']['round37-canonical']['candidate_sha256']==spec['round37_candidate_sha256']
        assert measurement['builds']['round37-canonical']['unstripped_sha256']==spec['round37_unstripped_sha256']
        (EVIDENCE/'measurement.json').write_text(json.dumps(measurement,indent=2)+'\n',encoding='utf-8',newline='\n')
    finally:
        for path,label in builds:retain(path,label)
        (EVIDENCE/'MANIFEST.json').write_text(json.dumps({p.relative_to(EVIDENCE).as_posix():sha(p)for p in sorted(EVIDENCE.rglob('*'))if p.is_file()and p.name!='MANIFEST.json'},indent=2)+'\n',encoding='utf-8',newline='\n')
if __name__=='__main__':main()
