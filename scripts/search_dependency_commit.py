#!/usr/bin/env python3
"""Search upstream commits for the exact byte-identical build of a captured dependency.

The pinned Metaplex/ATA source commits are size-exact but not byte-exact (relocation drift
from a near-miss on the exact deployed commit). This builds each candidate upstream commit in
the dependency's official solana-verifiable-build image and compares the padded output against
the captured mainnet binary, reporting full_byte_equality per commit. One long-lived container
per dependency keeps the cargo cache warm across candidates.
"""
import argparse, hashlib, json, subprocess, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sha = lambda b: hashlib.sha256(b).hexdigest()
def read(c): return subprocess.check_output(c, text=True).strip()

CFG = {
    'associated_token': dict(
        repo='https://github.com/solana-labs/solana-program-library',
        manifest='associated-token-account/program/Cargo.toml',
        library='spl_associated_token_account', deploy='target/deploy', build='build-bpf',
        image='solanafoundation/solana-verifiable-build@sha256:ee9ad7809009a99a70f659f7cba959e0c3c124e10f771b524914fd42f2b605a8'),
    'token_metadata': dict(
        repo='https://github.com/metaplex-foundation/mpl-token-metadata',
        manifest='programs/token-metadata/Cargo.toml',
        library='token_metadata', deploy='programs/token-metadata/target/deploy', build='build-sbf',
        image='solanafoundation/solana-verifiable-build@sha256:43206149a565ec35da95b1a909f4714f5d5f0d8241c31df24189e517acd18467'),
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dependency', choices=list(CFG), required=True)
    p.add_argument('--commits', nargs='+', required=True)
    p.add_argument('--features', default='', help='comma-separated cargo features to enable')
    p.add_argument('--output', type=pathlib.Path, required=True)
    a = p.parse_args()
    cfg = CFG[a.dependency]
    original = (ROOT / 'evidence/dependencies' / a.dependency / 'deployed.so').read_bytes()
    out = a.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    src = out / 'src'
    if not src.exists():
        subprocess.run(['git', 'clone', '--no-single-branch', cfg['repo'], str(src)], check=True)
    subprocess.run(['git', '-C', str(src), 'fetch', '--all', '--tags', '--force', '--quiet'], check=False)
    subprocess.run(['docker', 'pull', '--platform', 'linux/amd64', cfg['image']], check=True)
    workdir = read(['docker', 'run', '--rm', '--platform', 'linux/amd64', cfg['image'], 'pwd'])
    name = f'search-{a.dependency}'
    container = read(['docker', 'run', '--rm', '--platform', 'linux/amd64', '--name', name,
                      '--mount', f'type=bind,source={src},target={workdir}', '-d', cfg['image'], 'sleep', 'infinity'])
    results = []
    try:
        active = read(['docker', 'exec', '-w', '/', container, 'rustup', 'show', 'active-toolchain']).split()[0]
        mpath = workdir.rstrip('/') + '/' + cfg['manifest']
        mdir = workdir.rstrip('/') + '/' + str(pathlib.PurePosixPath(cfg['manifest']).parent)
        for commit in a.commits:
            subprocess.run(['git', '-C', str(src), 'reset', '--hard', '--quiet'], check=False)
            clean = subprocess.run(['git', '-C', str(src), 'clean', '-fdxq'],
                                   capture_output=True, text=True)
            if clean.returncode:
                clean = subprocess.run(['docker', 'exec', '--user', '0:0', '-w', workdir, container,
                                        'git', '-c', f'safe.directory={workdir}', 'clean', '-fdxq'],
                                       capture_output=True, text=True)
                if clean.returncode:
                    raise RuntimeError('container cleanup failed: ' + clean.stderr[-500:])
            co = subprocess.run(['git', '-C', str(src), 'checkout', '--force', '--quiet', commit + '^{commit}'],
                                capture_output=True, text=True)
            if co.returncode:
                co = subprocess.run(['git', '-C', str(src), 'checkout', '--force', '--quiet', commit],
                                    capture_output=True, text=True)
            if co.returncode:
                results.append(dict(commit=commit, checked_out=False, error=co.stderr[-500:])); continue
            head = read(['git', '-C', str(src), 'rev-parse', 'HEAD'])
            so = src / cfg['deploy'] / (cfg['library'] + '.so')
            if so.exists():
                raise RuntimeError(f'dependency artifact survived cleanup: {so}')
            feat = ['--features', a.features] if a.features else []
            if cfg['build'] == 'build-sbf':
                cmd = ['docker', 'exec', '-e', 'RUSTUP_TOOLCHAIN=' + active, '-w', mdir, container,
                       'cargo', 'build-sbf', '--', '--config', 'registries.crates-io.protocol="sparse"', *feat, '--locked', '--manifest-path', mpath]
            else:
                cmd = ['docker', 'exec', '-e', 'RUSTUP_TOOLCHAIN=' + active, '-e', 'RUSTFLAGS=-D warnings', '-w', workdir, container,
                       'cargo', 'build-bpf', '--manifest-path', mpath, '--', *feat, '--locked']
            b = subprocess.run(cmd, capture_output=True, text=True)
            built = b.returncode == 0 and so.is_file()
            row = dict(commit=commit, head=head, built=built)
            if built:
                raw = so.read_bytes()
                padded = raw + bytes(len(original) - len(raw)) if len(raw) < len(original) else raw
                first = next((i for i, (x, y) in enumerate(zip(padded, original)) if x != y), None)
                if first is None and len(padded) != len(original):
                    first = min(len(padded), len(original))
                row.update(candidate_bytes=len(raw), original_bytes=len(original),
                           full_byte_equality=padded == original, first_difference=first,
                           candidate_sha256=sha(raw))
                if padded == original:
                    (out / f'MATCH-{head[:12]}.so').write_bytes(raw)
            elif b.returncode == 0:
                row.update(artifact_missing=True,
                           error_tail=f'build succeeded without producing {so}')
            else:
                row['error_tail'] = b.stderr[-1500:]
            results.append(row)
            print(json.dumps({k: row[k] for k in row if k != 'error_tail'}), flush=True)
    finally:
        subprocess.run(['docker', 'stop', container], check=False, stdout=subprocess.DEVNULL)
    report = dict(dependency=a.dependency, features=a.features, image=cfg['image'], repo=cfg['repo'],
                  original_sha256=sha(original), original_bytes=len(original),
                  matches=[r['head'] for r in results if r.get('full_byte_equality')], results=results)
    (out / 'search-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('\n=== SUMMARY ===')
    for r in results:
        print(r.get('head', r['commit'])[:12], 'built' if r.get('built') else 'BUILD-FAIL',
              'BYTE-EQUAL' if r.get('full_byte_equality') else f"diff@{r.get('first_difference')}")
    print('MATCHES:', report['matches'])


if __name__ == '__main__':
    main()
