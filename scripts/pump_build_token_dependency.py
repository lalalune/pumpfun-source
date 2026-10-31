#!/usr/bin/env python3
"""Reproduce the pinned SPL Token verified-build recipe in its official Linux image."""
if not __debug__:
 raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse, hashlib, json, pathlib, shutil, subprocess, uuid

ROOT=pathlib.Path(__file__).resolve().parents[1]
TOKEN_COMMIT='a94dd19750dc3b2409f73e15bb74754935b2a489'
TOKEN_IMAGE='solanafoundation/solana-verifiable-build@sha256:d7079331a2696eca570fbeeb5caa556cb09084f89ca96f0a0edb86e1cf83e165'
p=argparse.ArgumentParser();p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--dependency',choices=['spl_token','spl_token_2022','associated_token','token_metadata'],default='spl_token');recovery_group=p.add_mutually_exclusive_group();recovery_group.add_argument('--metaplex-recovery',action='store_true',help='Apply the recorded, behaviorally recovered Metaplex Rust patch before compilation');recovery_group.add_argument('--metaplex-audit-recovery',action='store_true',help='Apply the five-file edition/burn/metadata source recovery trial');recovery_group.add_argument('--metaplex-uses-recovery',action='store_true',help='Apply the ten-file Uses/token-standard source trial');recovery_group.add_argument('--metaplex-context-recovery',action='store_true',help='Apply source recovery for Uses, system-program context and burn seed ownership');recovery_group.add_argument('--metaplex-validation-recovery',action='store_true',help='Apply twelve-file collection/mint validation source trial');recovery_group.add_argument('--metaplex-dispatch-recovery',action='store_true',help='Apply the observed remaining handler and dispatch source trial');recovery_group.add_argument('--metaplex-zero-use-recovery',action='store_true',help='Correct observed zero-use rejection and edition conversion evaluation order');recovery_group.add_argument('--metaplex-utilize-guard-recovery',action='store_true',help='Test target-derived Utilize guard layout over candidate11');recovery_group.add_argument('--metaplex-utilize-positive-guard-recovery',action='store_true',help='Test the reviewed positive remaining-use guard over candidate12');recovery_group.add_argument('--metaplex-utilize-unified-guard-recovery',action='store_true',help='Test accepted11 unified guard with dominated infallible subtraction');a=p.parse_args()
if (a.metaplex_recovery or a.metaplex_audit_recovery or a.metaplex_uses_recovery or a.metaplex_context_recovery or a.metaplex_validation_recovery or a.metaplex_dispatch_recovery or a.metaplex_zero_use_recovery or a.metaplex_utilize_guard_recovery or a.metaplex_utilize_positive_guard_recovery or a.metaplex_utilize_unified_guard_recovery) and a.dependency!='token_metadata':p.error('Metaplex recovery flags require --dependency token_metadata')
if a.dependency=='spl_token':
    COMMIT=TOKEN_COMMIT;IMAGE=TOKEN_IMAGE;REPOSITORY='https://github.com/solana-program/token';MANIFEST='pinocchio/program/Cargo.toml';LIBRARY='pinocchio_token_program';TOOLS=['--tools-version','v1.54']
elif a.dependency=='spl_token_2022':
    COMMIT='8867f751c0f69367ba03af4f85510b5611989491';IMAGE='solanafoundation/solana-verifiable-build@sha256:6c73adc767ee7ff212f2532d4695472b12f3d4ac20aea3db22b89d8c614dac50';REPOSITORY='https://github.com/solana-program/token-2022';MANIFEST='program/Cargo.toml';LIBRARY='spl_token_2022';TOOLS=[]
elif a.dependency=='associated_token':
    COMMIT='f5ce86d43dd31ddefb96d4e8cdd67dd073dc5dca';IMAGE='solanafoundation/solana-verifiable-build@sha256:ee9ad7809009a99a70f659f7cba959e0c3c124e10f771b524914fd42f2b605a8';REPOSITORY='https://github.com/solana-labs/solana-program-library';MANIFEST='associated-token-account/program/Cargo.toml';LIBRARY='spl_associated_token_account';TOOLS=[]
else:
    COMMIT='17e99434af5ead3e989c08f32af33609821d0bc0';IMAGE='solanafoundation/solana-verifiable-build@sha256:43206149a565ec35da95b1a909f4714f5d5f0d8241c31df24189e517acd18467';REPOSITORY='https://github.com/metaplex-foundation/mpl-token-metadata';MANIFEST='programs/token-metadata/Cargo.toml';LIBRARY='token_metadata';TOOLS=[]
source=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(cmd):return subprocess.check_output(cmd,text=True).strip()
assert read(['git','-C',str(source),'rev-parse','HEAD'])==COMMIT
assert not read(['git','-C',str(source),'status','--porcelain']), 'source checkout must be fresh and clean'
# token-metadata is its own Cargo workspace, so its build target is not the root one.
build_root=source/'programs/token-metadata' if a.dependency=='token_metadata' else source
assert not (source/'target').exists() and not (build_root/'target').exists(), 'require a clean build target'
tracked=read(['git','-C',str(source),'ls-files']).splitlines()
source_hashes={name:sha((source/name).read_bytes()) for name in tracked if (source/name).is_file()}
source_patch=None
if a.metaplex_recovery or a.metaplex_audit_recovery or a.metaplex_uses_recovery or a.metaplex_context_recovery or a.metaplex_validation_recovery or a.metaplex_dispatch_recovery or a.metaplex_zero_use_recovery or a.metaplex_utilize_guard_recovery or a.metaplex_utilize_positive_guard_recovery or a.metaplex_utilize_unified_guard_recovery:
    recovery=ROOT/'repro/pump'/('metaplex-utilize-unified-guard-source-recovery' if a.metaplex_utilize_unified_guard_recovery else 'metaplex-utilize-positive-guard-source-recovery' if a.metaplex_utilize_positive_guard_recovery else 'metaplex-utilize-guard-source-recovery' if a.metaplex_utilize_guard_recovery else 'metaplex-zero-use-source-recovery' if a.metaplex_zero_use_recovery else 'metaplex-dispatch-source-recovery' if a.metaplex_dispatch_recovery else 'metaplex-validation-source-recovery' if a.metaplex_validation_recovery else 'metaplex-context-source-recovery' if a.metaplex_context_recovery else 'metaplex-uses-source-recovery' if a.metaplex_uses_recovery else 'metaplex-audit-source-recovery' if a.metaplex_audit_recovery else 'metaplex-source-recovery')
    patch=recovery/'source.patch';inputs=json.loads((recovery/'source-inputs.json').read_text())
    assert inputs['upstream_commit']==COMMIT
    assert all(source_hashes[name]==digest for name,digest in inputs['baseline'].items())
    (out/'upstream-source-manifest.json').write_text(json.dumps(source_hashes,indent=2)+'\n',encoding='utf-8',newline='\n')
    subprocess.run(['git','-C',str(source),'apply','--check',str(patch)],check=True)
    subprocess.run(['git','-C',str(source),'apply',str(patch)],check=True)
    assert set(read(['git','-C',str(source),'diff','--name-only']).splitlines())==set(inputs['patched'])
    source_hashes={name:sha((source/name).read_bytes()) for name in tracked if (source/name).is_file()}
    assert all(source_hashes[name]==digest for name,digest in inputs['patched'].items())
    shutil.copyfile(patch,out/'source.patch');shutil.copyfile(recovery/'source-inputs.json',out/'patch-source-inputs.json')
    source_patch={'path':'source.patch','sha256':sha(patch.read_bytes()),'scope':('Reviewed unified-guard dominated-subtraction source hypothesis; unaccepted and not historically attributed.' if a.metaplex_utilize_unified_guard_recovery else 'Reviewed positive-guard source hypothesis; unaccepted and not historically attributed.' if a.metaplex_utilize_positive_guard_recovery else 'Behaviorally recovered Rust changes applied to public baseline; not attributed historical source.')}
(out/'source-manifest.json').write_text(json.dumps(source_hashes,indent=2)+'\n',encoding='utf-8',newline='\n')
subprocess.run(['docker','pull','--platform','linux/amd64',IMAGE],check=True)
image_info=json.loads(read(['docker','image','inspect',IMAGE]))
(out/'image-inspect.json').write_text(json.dumps(image_info,indent=2)+'\n',encoding='utf-8',newline='\n')
workdir=read(['docker','run','--rm','--platform','linux/amd64',IMAGE,'pwd'])
assert workdir.startswith('/') and workdir != '/' and '\n' not in workdir
name='pump-token-rebuild-'+uuid.uuid4().hex[:12]
container=read(['docker','run','--rm','--platform','linux/amd64','--name',name,'--mount',f'type=bind,source={source},target={workdir}','-d',IMAGE,'sleep','infinity'])
commands=[]
try:
    active=read(['docker','exec','-w','/',container,'rustup','show','active-toolchain']).split()[0]
    cmd=['docker','exec','-e','RUSTUP_TOOLCHAIN='+active,'-w',workdir.rstrip('/')+'/'+str(pathlib.PurePosixPath(MANIFEST).parent),container,'cargo','build-sbf',*TOOLS,'--','--config','registries.crates-io.protocol="sparse"','--locked','--manifest-path',workdir.rstrip('/')+'/'+MANIFEST]
    if a.dependency=='associated_token':
        cmd=['docker','exec','-e','RUSTUP_TOOLCHAIN='+active,'-e','RUSTFLAGS=-D warnings','-w',workdir,container,'cargo','build-bpf','--manifest-path',workdir.rstrip('/')+'/'+MANIFEST,'--','--locked']
    commands.append(cmd)
    print('Building pinned '+a.dependency+' source with its official image recipe',flush=True)
    with (out/'build.log').open('w') as log:
        result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        print((out/'build.log').read_text()[-12000:]);result.check_returncode()
    installed=read(['docker','exec',container,'rustup','toolchain','list'])
    selected_names=[line.split()[0] for line in installed.splitlines() if 'solana' in line.split()[0] or line.split()[0]=='bpf']
    assert len(selected_names)==1, installed
    selected_name=selected_names[0]
    selected_rustc=read(['docker','exec',container,'rustup','which','--toolchain',selected_name,'rustc'])
    selected_resolved=read(['docker','exec',container,'readlink','-f',selected_rustc])
    tool_info=read(['docker','exec',container,selected_rustc,'--version','--verbose'])
    selected_hash=read(['docker','exec',container,'sha256sum',selected_rustc]).split()[0]
    (out/'tool-versions.json').write_text(json.dumps({'selected_toolchain':selected_name,'installed_toolchains':installed,'selected_rustc_path':selected_rustc,'selected_rustc_resolved':selected_resolved,'selected_rustc_sha256':selected_hash,'selected_rustc_version':tool_info},indent=2)+'\n',encoding='utf-8',newline='\n')
finally:
    subprocess.run(['docker','stop',container],check=False,stdout=subprocess.DEVNULL)
assert all(sha((source/name).read_bytes())==digest for name,digest in source_hashes.items()), 'build modified source or lockfile'
candidate=build_root/'target/deploy'/(LIBRARY+'.so')
assert candidate.is_file()
shutil.copyfile(candidate,out/(LIBRARY+'.so'))
# Reference bytes are read only after the source-only build has finished.
b=candidate.read_bytes();original=(ROOT/'evidence/dependencies'/a.dependency/'deployed.so').read_bytes()
raw=b
from analyze import elf_layout
original_layout=elf_layout(original);elf_layout(raw)
if len(raw)<=len(original):
    assert original_layout['trailing_all_zero'], 'captured non-ELF allocation suffix must be verified zero before padding'
    b=raw+bytes(len(original)-len(raw))
(out/'rebuilt.deployed.so').write_bytes(b)
normalized=b.rstrip(b'\0');original_normalized=original.rstrip(b'\0')
first=next((i for i,(x,y) in enumerate(zip(b,original)) if x!=y),None)
if first is None and len(b)!=len(original):first=min(len(b),len(original))
report={'scope':'Fresh Linux container source build; no captured binary mounted into build container. Original padding is compared explicitly.','source_repository':REPOSITORY,'dependency':a.dependency,'source_commit':COMMIT,'image':IMAGE,'platform':'linux/amd64','onchain_recipe':None if a.dependency in ('associated_token','token_metadata') else 'repro/pump/'+a.dependency+'-onchain-build-params.json','active_host_toolchain':active,'commands':[[x.replace(container,'<container>').replace(str(source),'<source>') for x in cmd] for cmd in commands],'source_manifest_sha256':sha((out/'source-manifest.json').read_bytes()),'build_log_sha256':sha((out/'build.log').read_bytes()),'original_bytes':len(original),'candidate_input_bytes':len(raw),'candidate_input_sha256':sha(raw),'zero_padding_bytes':len(b)-len(raw),'candidate_bytes':len(b),'original_sha256':sha(original),'candidate_sha256':sha(b),'original_normalized_sha256':sha(original_normalized),'candidate_normalized_sha256':sha(normalized),'normalized_byte_equality':normalized==original_normalized,'full_byte_equality':b==original,'first_difference':first}
if source_patch is not None:report['source_patch']=source_patch
(out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(report,indent=2))
if b!=original:raise SystemExit(1)
