"""Run real fastbuild builds where build.rs generates tracked or OUT_DIR Rust."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo, sdk = map(lambda value: Path(value).resolve(), sys.argv[1:])
sys.path.insert(0, str(repo / 'reconstruction/harness'))
import fastbuild
from source_inputs import snapshot

sha = lambda data: hashlib.sha256(data).hexdigest()
with tempfile.TemporaryDirectory(prefix='fastbuild-source-generator-') as temporary:
    root = Path(temporary).resolve()
    fastbuild.SDK = sdk
    fastbuild.LOCKDIR = root / 'locks'
    fastbuild.RECIPES['mac'] = dict(triple='sbf-solana-solana', rustc=sdk/'rust/bin/rustc', template=root/'absent')
    rows = []
    for case in ('unchanged', 'rewrite_source', 'add_source', 'out_dir', 'pre_generated'):
        source = root / case / 'source'
        (source / 'src').mkdir(parents=True)
        (source / 'Cargo.toml').write_text('[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n[lib]\ncrate-type=["cdylib"]\n[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n[workspace]\n')
        include = 'include!(concat!(env!("OUT_DIR"), "/generated.rs"));' if case == 'out_dir' else 'include!("generated.rs");'
        (source / 'src/lib.rs').write_text('#![no_std]\n'+include+'\n#[no_mangle]pub extern "C" fn entrypoint(_: *const u8)->u64{VALUE}\n#[panic_handler]fn panic(_: &core::panic::PanicInfo)->!{loop{}}\n')
        if case not in ('add_source', 'out_dir'):
            (source / 'src/generated.rs').write_text('const VALUE: u64 = '+('2' if case == 'pre_generated' else '1')+';\n')
        if case in ('rewrite_source', 'add_source'):
            build = 'fn main(){std::fs::write("src/generated.rs", "const VALUE: u64 = 2;\\n").unwrap();}\n'
        elif case == 'out_dir':
            build = 'fn main(){let out=std::path::PathBuf::from(std::env::var_os("OUT_DIR").unwrap());std::fs::write(out.join("generated.rs"), "const VALUE: u64 = 2;\\n").unwrap();std::fs::create_dir_all("target").unwrap();std::fs::write("target/ordinary-build-output", b"ignored").unwrap();}\n'
        else:
            build = 'fn main(){}\n'
        (source/'build.rs').write_text(build)
        subprocess.run([str(sdk/'rust/bin/cargo'), 'generate-lockfile', '--offline'], cwd=source, capture_output=True, check=True)
        admitted = snapshot(source)
        work, out = root/case/'work', root/case/'out'
        try:
            result = fastbuild.build(source, work, out, quiet=True, recipe='mac', timeout=30)
            error = None
        except ValueError as caught:
            result = None
            error = str(caught)
        staged = work/'ws/programs/pump'
        rows.append({'case':case,'result':result,'error':error,
                     'caller_source_unchanged':snapshot(source)==admitted,
                     'receipt_source_sha256':json.loads((out/'source-inputs.json').read_text())['sha256'],
                     'candidate_exists':(out/'candidate.so').exists(),
                     'caller_generated_sha256':sha((source/'src/generated.rs').read_bytes()) if (source/'src/generated.rs').exists() else None,
                     'staged_generated_sha256':sha((staged/'src/generated.rs').read_bytes()) if (staged/'src/generated.rs').exists() else None,
                     'build_log':(out/'build.log').read_text().replace(str(root),'<probe-root>')})
    print(json.dumps(rows,indent=2).replace(str(root),'<probe-root>'))
