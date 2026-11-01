#!/usr/bin/env python3
"""Reproduce the admin-packet manifest admission gap.

Copies the two packets out of a checkout and runs each verifier with
nonexistent images under five modes: pristine, changed member, extra
unlisted file, symlinked member, duplicated manifest path. Admission is
correct only when every tamper mode is refused before the image stage
(the verifier output never references the nonexistent image paths).

Usage:
  python3 reproduce.py --checkout <repo> --revision <sha> \
      --expect base|fixed --output results.json
Exit 0 when the observations match the expectation, 1 otherwise.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PACKETS = ('pump-fees-admin-cto-sharing-direct-20261030',
           'pump-global-admin-sequences-20261030')
IMAGES = json.dumps({'original': '/nonexistent/original.so',
                     'candidate': '/nonexistent/candidate.so'})
MODES = ('pristine', 'changed', 'extra', 'symlink', 'duplicate')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify(packet):
    result = subprocess.run([sys.executable, '-B', str(packet / 'verify.py'),
                             '--images', IMAGES],
                            cwd=packet, capture_output=True, text=True)
    text = result.stdout + result.stderr
    if '/nonexistent/' in text:
        return 'reached-image-stage'
    if result.returncode != 0:
        return 'refused'
    return 'accepted'


def run_mode(source, mode, root):
    packet = root / 'packet'
    shutil.copytree(source, packet)
    if mode == 'changed':
        (packet / 'README.md').write_bytes(b'tampered member bytes\n')
    elif mode == 'extra':
        (packet / 'runtime/unlisted.bin').write_bytes(b'\x00')
    elif mode == 'symlink':
        member = packet / 'README.md'
        member.replace(root / 'README.md')
        member.symlink_to(root / 'README.md')
    elif mode == 'duplicate':
        path = packet / 'MANIFEST.json'
        manifest = json.loads(path.read_text())
        manifest['files'].append(dict(manifest['files'][0]))
        path.write_text(json.dumps(manifest))
    return classify(packet)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkout', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--expect', choices=('base', 'fixed'), required=True)
    parser.add_argument('--output')
    args = parser.parse_args()

    research = Path(args.checkout) / 'research'
    record = {'revision': args.revision, 'expect': args.expect, 'packets': {}}
    ok = True
    for name in PACKETS:
        source = research / name
        entry = {'verify.py_sha256': sha256(source / 'verify.py'),
                 'MANIFEST.json_sha256': sha256(source / 'MANIFEST.json'),
                 'modes': {}}
        for mode in MODES:
            with tempfile.TemporaryDirectory() as tmp:
                outcome = run_mode(source, mode, Path(tmp))
            entry['modes'][mode] = outcome
            if mode == 'pristine':
                want = 'reached-image-stage'
            elif args.expect == 'fixed':
                want = 'refused'
            elif mode in ('duplicate', 'symlink'):
                want = 'reached-image-stage'  # the defect, on base
            else:
                want = 'refused'
            if outcome != want:
                ok = False
                print(f'MISMATCH {name} {mode}: got {outcome}, want {want}')
        record['packets'][name] = entry
        print(f"{name}: " + ' '.join(f"{m}={entry['modes'][m]}" for m in MODES))
    if args.output:
        Path(args.output).write_text(json.dumps(record, indent=2) + '\n')
    print('MATCH' if ok else 'NO MATCH', f'(expect {args.expect})')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
