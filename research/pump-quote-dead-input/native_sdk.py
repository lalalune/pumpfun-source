"""Authenticate the official native Linux v1.44 SDK for isolated replay proofs."""
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

URL = 'https://github.com/anza-xyz/platform-tools/releases/download/v1.44/platform-tools-linux-x86_64.tar.bz2'
SHA256 = '6719b889d60677a8a2fcf4c82f68441a1afe0ab093edd2efe9f84a67a808b3e9'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            value.update(block)
    return value.hexdigest()


def prepare(root, sdk, proof):
    archive = root / 'work/platform-tools-linux-v144.tar.bz2'
    urllib.request.urlretrieve(URL, archive)
    if digest(archive) != SHA256:
        raise ValueError('official Linux SDK archive differs')
    sdk.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'r:bz2') as source:
        source.extractall(sdk, filter='data')
    libraries = sdk / 'rust/lib/rustlib/sbpf-solana-solana/lib'
    expected = json.loads((root / 'scripts/pump_linux_v144_sbpf_libraries.json').read_text())['target_libraries']
    actual = {path.name: digest(path) for path in libraries.iterdir() if path.is_file()}
    if actual != expected:
        raise ValueError('native target libraries differ from pinned official Linux SBPF set')
    record = {'url': URL, 'archive_sha256': SHA256, 'native_host': 'Linux x86_64',
              'target': 'sbpf-solana-solana', 'target_libraries': actual,
              'tools': {name: digest(sdk / name) for name in ('rust/bin/rustc', 'rust/bin/cargo', 'llvm/bin/llvm-objcopy')},
              'scope': 'Unmodified official native Linux SDK; no macOS profile or tool-byte substitution.'}
    (proof / 'native-sdk.json').write_text(json.dumps(record, indent=2) + '\n')
    return ['--target', 'sbpf-solana-solana']
