"""Verify the current-main replay packet without executing the programs."""
import gzip
import hashlib
import json
from pathlib import Path
from verify_runtime import verify_rows
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
def main():
    manifest = json.loads((HERE / 'current-main-manifest.json').read_text())
    for section, root in [('packet', HERE), ('external', ROOT)]:
        for name, expected in manifest[section].items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f'Hash mismatch: {name}')
    report = json.loads(gzip.decompress((HERE / 'current-main-runtime.json.gz').read_bytes()))
    for image, build in [('control', 'control'), ('candidate', 'v3')]:
        if report['images'][image] != manifest['builds'][build]['candidate_sha256']:
            raise ValueError(f'Binary mismatch: {image}')
    print(json.dumps(verify_rows(report), sort_keys=True))
if __name__ == '__main__':
    main()
