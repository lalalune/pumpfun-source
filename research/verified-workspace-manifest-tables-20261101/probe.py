"""Exercise verified workspace builds with real SBF Cargo and legal TOML variants."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo, sdk = map(lambda value: Path(value).resolve(), sys.argv[1:])
manifest = '''[package]
name="pump-recovered"
version="0.1.0"
edition="2021"
[lib]
crate-type=["cdylib","lib"]
[profile.release]
panic="abort"
lto=false
codegen-units=1
[workspace]
'''
variants = {
    'plain': manifest,
    'header_comment': '# The [profile.release] settings are preserved below.\n' + manifest,
    'multiline_metadata': manifest.replace('[lib]', 'description="""\n[profile.release]\nThis is package metadata.\n[workspace]\n"""\n[lib]'),
    'trailing_comment': manifest + '# Empty workspace remains intentional.\n',
}
results = {}
with tempfile.TemporaryDirectory(prefix='.verified-manifest-', dir=repo) as temporary:
    root = Path(temporary)
    registry = root/'registry'
    registry.mkdir()
    for name, text in variants.items():
        source = root/name
        (source/'src').mkdir(parents=True)
        (source/'Cargo.toml').write_text(text)
        (source/'Cargo.lock').write_text('version = 3\n\n[[package]]\nname = "pump-recovered"\nversion = "0.1.0"\n')
        (source/'src/lib.rs').write_text('#![no_std]\n#[no_mangle]pub extern "C" fn entrypoint(_: *const u8)->u64{27}\n#[panic_handler]fn panic(_: &core::panic::PanicInfo)->!{loop{}}\n')
        output=root/(name+'-out')
        command=[sys.executable,'-B',str(repo/'scripts/pump_build_verified.py'),'--source-directory',str(source),'--sdk',str(sdk),'--registry-home',str(registry),'--output',str(output),'--workspace-layout','--target','sbpf-solana-solana']
        child=subprocess.run(command,capture_output=True,text=True,timeout=90)
        record={'returncode':child.returncode,'stderr':child.stderr.replace(str(root),'<fixture>').replace(str(repo),'<repo>'),'log':(output/'build.log').read_text() if (output/'build.log').is_file() else None}
        receipt=output/'build-comparison.json'
        if receipt.is_file():
            report=json.loads(receipt.read_text())
            record.update(source_unchanged=report['source_unchanged'],candidate_sha256=hashlib.sha256((output/'candidate.so').read_bytes()).hexdigest(),workspace_manifest=(output/'source/Cargo.toml').read_text(),package_manifest=(output/'source/programs/pump/Cargo.toml').read_text())
        results[name]=record
print(json.dumps(results,indent=2))
