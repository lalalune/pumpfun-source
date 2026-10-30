from pathlib import Path
import json,hashlib,subprocess,sys,shutil,datetime,os
B=Path('/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-contribution-review/pump-legacy-exact-sol-20261029');L=Path('/home/ahi200/pumpfun-work/20261029-pump-legacy-exact-sol');S=Path('/home/ahi200/pumpfun-work/20261027-crank/sdk')
label=sys.argv[1];src=L/('source-'+label);out=L/label;out.mkdir();target=L/'target';target.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inventory=lambda p:{q.relative_to(p).as_posix():sha(q) for q in sorted(p.rglob('*')) if q.is_file()}
inputs=inventory(src);receipt=json.loads((B/'build-comparison.json').read_text(encoding='utf-8-sig'));manifest=receipt['command'][receipt['command'].index('--manifest-path')+1];inside=manifest.removesuffix('/programs/pump/Cargo.toml');sdk='/Users/shawwalters/.cache/solana/v1.44/platform-tools';hybrid='/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work/toolchains/hybrid144';ch='/Users/shawwalters/.cargo';ct=receipt['environment']['CARGO_TARGET_DIR']
if label=='parent':
    expected=receipt['source_sha256'];assert len(inputs)==len(expected),(len(inputs),len(expected))
    for n,h in inputs.items():assert any(k.endswith('/'+n) and v==h for k,v in expected.items()),n
assert sha(B/'pump_physical_source_wrapper.py')=='d959fe0074fafe7f310a8f40051ce87f795b1e81b104a38dfe57086efa6bae1b'
cmd=['docker','run','--rm','--platform','linux/amd64','--network','none','--entrypoint=/usr/bin/env']
for host,dest,mode in [(src,inside,'ro'),(S,sdk,'ro'),(S,hybrid,'ro'),(L/'cargo-home',ch,'rw'),(target,ct,'rw'),(B,'/controllers','ro'),(out,'/analysis','rw')]:cmd+=['-v',str(host)+':'+dest+':'+mode]
cmd+=['-w',inside]
env={'CARGO_HOME':ch,'CARGO_TARGET_DIR':ct,'CARGO_BUILD_JOBS':'2','RUSTC':hybrid+'/rust/bin/rustc','RUSTDOC':hybrid+'/rust/bin/rustdoc','CC':sdk+'/llvm/bin/clang','AR':sdk+'/llvm/bin/llvm-ar','OBJDUMP':sdk+'/llvm/bin/llvm-objdump','OBJCOPY':sdk+'/llvm/bin/llvm-objcopy','LD_LIBRARY_PATH':sdk+'/rust/lib:'+sdk+'/llvm/lib','CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS':'-Zremap-cwd-prefix=','RUSTC_WRAPPER':'/controllers/pump_physical_source_wrapper.py','PUMP_LOGICAL_REGISTRY_SRC':ch+'/registry/src','PUMP_SOURCE_WRAPPER_LOG':'/analysis/physical-source-calls.jsonl'}
for k,v in env.items():cmd+=['-e',k+'='+v]
cmd+=['solanafoundation/solana-verifiable-build@sha256:6c73adc767ee7ff212f2532d4695472b12f3d4ac20aea3db22b89d8c614dac50','-u','RUSTFLAGS','-u','CARGO_ENCODED_RUSTFLAGS',sdk+'/rust/bin/cargo','build','--manifest-path',manifest,'--release','--target','sbpf-solana-solana','--offline','--locked','-vv']
launch={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Linux transport control for exact Pump673 source; native macOS image reproduction not assumed','command':cmd,'inputs':inputs,'tools':{n:sha(S/p) for n,p in {'rustc':'rust/bin/rustc','cargo':'rust/bin/cargo','objcopy':'llvm/bin/llvm-objcopy'}.items()},'controller_sha256':sha(Path(__file__))}
(out/'launch.json').write_text(json.dumps(launch,indent=2)+'\n')
for q in src.rglob('*.rs'):os.utime(q,None)
with(out/'build.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
lines=(out/'build.log').read_text().splitlines();actual_root=sum(line.strip().startswith('Running ') and '--crate-name pump_recovered ' in line for line in lines)
result={'returncode':r.returncode,'inputs_unchanged':inputs==inventory(src),'actual_root_compilations':actual_root};(out/'result.json').write_text(json.dumps(result,indent=2));r.check_returncode();assert result['inputs_unchanged'] and actual_root==1, result
shutil.copy2(target/'sbpf-solana-solana/release/pump_recovered.so',out/'symbols.so');subprocess.run([str(S/'llvm/bin/llvm-objcopy'),'--strip-all',str(out/'symbols.so'),str(out/'candidate.so')],check=True)
result.update(symbols_sha256=sha(out/'symbols.so'),candidate_sha256=sha(out/'candidate.so'));(out/'result.json').write_text(json.dumps(result,indent=2));print(label,result,flush=True)
