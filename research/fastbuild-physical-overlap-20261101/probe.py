"""Real fastbuild with a tiny SBF crate on a case-insensitive filesystem."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

repo, sdk = map(lambda p: Path(p).resolve(), sys.argv[1:])
sys.path.insert(0, str(repo / 'reconstruction/harness'))
import fastbuild
from source_inputs import snapshot

records = []
with tempfile.TemporaryDirectory(prefix='build-case-overlap-') as temporary:
    root = Path(temporary).resolve()
    fastbuild.SDK = sdk
    fastbuild.LOCKDIR = root / 'locks'
    fastbuild.RECIPES['mac'] = {'triple': 'sbf-solana-solana',
        'rustc': sdk / 'rust/bin/rustc', 'template': root / 'no-template'}
    for kind in ('separate', 'canonical-overlap', 'case-overlap'):
        case = root / kind
        source = case / 'source'
        (source / 'src').mkdir(parents=True)
        alias = case / 'SOURCE'
        if not alias.exists() or not alias.samefile(source):
            raise RuntimeError('requires a case-insensitive filesystem')
        (source / 'Cargo.toml').write_text('[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n[lib]\ncrate-type=["cdylib","lib"]\n[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n[workspace]\n')
        (source / 'src/lib.rs').write_text('#![no_std]\n#[no_mangle]pub extern "C" fn entrypoint(_: *const u8)->u64{37}\n#[panic_handler]fn panic(_: &core::panic::PanicInfo)->!{loop{}}\n')
        subprocess.run([str(sdk / 'rust/bin/cargo'), 'generate-lockfile', '--offline'],
                       cwd=source, check=True, capture_output=True)
        before = snapshot(source)
        out = (case / 'out' if kind == 'separate' else
               source / 'out' if kind == 'canonical-overlap' else alias / 'out')
        row = {'mode': kind}
        try:
            built = fastbuild.build(source, case / 'work', out, quiet=True, recipe='mac', timeout=30)
            row.update(ok=built['ok'], candidate_sha256=built.get('candidate_sha256'))
            if not built['ok']:
                row['log_tail'] = Path(built['log']).read_text()[-2000:]
        except Exception as error:
            row.update(error=str(error), error_type=type(error).__name__)
        after = snapshot(source)
        row['source_unchanged'] = before == after
        row['created_source_files'] = sorted({r['path'] for r in after['files']} -
                                            {r['path'] for r in before['files']})
        row['output_exists'] = out.exists()
        records.append(row)
print(json.dumps(records, indent=2))
