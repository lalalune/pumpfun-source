"""Actual SBF builds distinguish POSIX execute permissions with identical bytes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo, sdk = (Path(value).resolve() for value in sys.argv[1:])
sys.path.insert(0, str(repo / 'reconstruction/harness'))
import fastbuild
from source_inputs import snapshot, assert_unchanged

with tempfile.TemporaryDirectory(prefix='source-execute-bits-') as temporary:
    root = Path(temporary).resolve()
    source = root / 'source'
    (source / 'src').mkdir(parents=True)
    (source / 'Cargo.toml').write_text('[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n[lib]\ncrate-type=["cdylib"]\n[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n[workspace]\n')
    (source / 'src/lib.rs').write_text('#![no_std]\n#[no_mangle]pub extern "C" fn entrypoint(_: *const u8)->u64{37}\n#[panic_handler]fn panic(_: &core::panic::PanicInfo)->!{loop{}}\n')
    (source / 'build.rs').write_text('fn main(){let output=std::process::Command::new("./helper.sh").output().expect("execute source helper");assert!(output.status.success());println!("cargo:rerun-if-changed=helper.sh");}\n')
    helper = source / 'helper.sh'
    helper.write_text('#!/bin/sh\nexit 0\n')
    subprocess.run([str(sdk / 'rust/bin/cargo'), 'generate-lockfile', '--offline'], cwd=source, capture_output=True, check=True)
    fastbuild.SDK = sdk
    fastbuild.LOCKDIR = root / 'locks'
    fastbuild.RECIPES['mac'] = dict(triple='sbf-solana-solana', rustc=sdk / 'rust/bin/rustc', template=root/'no-template')
    rows=[]
    previous=None
    for mode in (0o755, 0o645, 0o644):
        helper.chmod(mode)
        current=snapshot(source)
        row=dict(mode=oct(mode),source_sha256=current['sha256'],helper=next(x for x in current['files'] if x['path']=='helper.sh'))
        if previous is not None:
            try:
                assert_unchanged(source,previous)
                row['change_detected']=False
            except ValueError:
                row['change_detected']=True
        result=fastbuild.build(source,root/f'work-{mode}',root/f'out-{mode}',quiet=True,recipe='mac',timeout=30)
        row.update(ok=result['ok'], candidate_sha256=result.get('candidate_sha256'), source_unchanged=current==snapshot(source))
        log=(root/f'out-{mode}'/'build.log').read_text()
        row['permission_denied']='Permission denied' in log or 'PermissionDenied' in log
        if not result['ok']: row['log_tail']=log.replace(str(root),'<probe-root>')[-1600:]
        rows.append(row)
        previous=current
    print(json.dumps(rows,indent=2))
