"""Real offline verified SBF builds with a compiler-declared env-dependent registry fixture."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo, sdk = map(lambda value: Path(value).resolve(), sys.argv[1:])
with tempfile.TemporaryDirectory(prefix='.dependency-env-', dir=repo) as temporary:
    root = Path(temporary)
    source, vendor, cargo = root/'source', root/'vendor', root/'cargo-home'
    dep = vendor/'repro-dependency-0.1.0'
    for directory in [source/'src', dep/'src', cargo]: directory.mkdir(parents=True)
    (dep/'Cargo.toml').write_text('[package]\nname="repro-dependency"\nversion="0.1.0"\nedition="2021"\n')
    (dep/'src/lib.rs').write_text('#![no_std]\npub fn value()->u64{env!("PROBE_DEPENDENCY_VALUE").as_bytes()[0] as u64 + env!("PROBE_DEPENDENCY_VALUE").len() as u64 + env!("CARGO_PKG_VERSION").len() as u64 + option_env!("PROBE_OPTION").map(|s|s.len()+1).unwrap_or(0) as u64}\n')
    checksums={p.relative_to(dep).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dep.rglob('*') if p.is_file()}
    (dep/'.cargo-checksum.json').write_text(json.dumps({'files':checksums,'package':None}))
    (cargo/'config.toml').write_text('[source.crates-io]\nreplace-with="fixture"\n[source.fixture]\ndirectory='+json.dumps(str(vendor))+'\n')
    (source/'Cargo.toml').write_text('[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n[lib]\ncrate-type=["cdylib","lib"]\n[dependencies]\nrepro-dependency="=0.1.0"\n[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n[workspace]\n')
    (source/'src/lib.rs').write_text('#![no_std]\n#[no_mangle]pub extern "C" fn entrypoint(_: *const u8)->u64{repro_dependency::value()}\n#[panic_handler]fn panic(_: &core::panic::PanicInfo)->!{loop{}}\n')
    env=dict(os.environ,CARGO_HOME=str(cargo),RUSTC=str(sdk/'rust/bin/rustc'))
    lock=subprocess.run([str(sdk/'rust/bin/cargo'),'generate-lockfile','--offline'],cwd=source,env=env,capture_output=True,text=True,timeout=20)
    if lock.returncode:raise RuntimeError(lock.stderr)
    results={}
    cases = [('initial','A',None,'cache'), ('same','A',None,'cache'), ('unrelated','A',None,'cache'),
             ('changed','B',None,'cache'), ('fresh_b','B',None,'cache-b'),
             ('optional','A','','cache'), ('fresh_optional','A','','cache-optional'),
             ('escaped','A\n\\\rß\x85',None,'cache'), ('fresh_escaped','A\n\\\rß\x85',None,'cache-escaped'),
             ('escaped_repeat','A\n\\\rß\x85',None,'cache-escaped'), ('missing',None,None,'cache')]
    for name,value,optional,cache_name in cases:
        cache=root/cache_name
        output=root/name
        command=[sys.executable,'-B',str(repo/'scripts/pump_build_verified.py'),'--source-directory',str(source),'--sdk',str(sdk),'--registry-home',str(cargo),'--output',str(output),'--dependency-cache',str(cache)]
        child_env=dict(env,PROBE_UNRELATED='harmless-change' if name=='unrelated' else 'same')
        for variable, selected in [('PROBE_DEPENDENCY_VALUE',value),('PROBE_OPTION',optional)]:
            if selected is None: child_env.pop(variable,None)
            else: child_env[variable]=selected
        process=subprocess.run(command,env=child_env,capture_output=True,text=True,timeout=120)
        record={'returncode':process.returncode,'stderr':process.stderr,'log':(output/'build.log').read_text() if (output/'build.log').is_file() else None}
        if (output/'build-comparison.json').is_file():
            report=json.loads((output/'build-comparison.json').read_text())
            record.update(candidate_sha256=hashlib.sha256((output/'candidate.so').read_bytes()).hexdigest(),cache_key=report['dependency_cache']['key'],cache_status=report['dependency_cache']['status'],source_unchanged=report['source_unchanged'],changed_environment_dependencies=report['dependency_cache'].get('changed_environment_dependencies',[]))
        if (output/'build-plan.json').is_file():
            plan=json.loads((output/'build-plan.json').read_text())
            record['dependency_plan']=[inv for inv in plan['invocations'] if inv['package_name']=='repro-dependency']
        record['depinfo']={p.relative_to(output).as_posix():p.read_text() for p in (output/'target').rglob('repro_dependency-*.d')}
        results[name]=record
    print(json.dumps(results,indent=2))
