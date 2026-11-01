#!/usr/bin/env python3
"""Verify that a completion checkpoint binds its reused runtime receipt to its own build.

``runtime-reuse.json`` lets a checkpoint carry the historical runtime cases forward
while running no VM, on one written condition: the fresh stripped Pump image must
equal ``candidate_sha256_required_for_reuse``. The file records
``"fresh_candidate_identity_checked_here": false`` and leaves that comparison to
"the parent", and nothing in the repository performed it, so a later checkpoint
could publish a different image and still cite the old cases.

The checks below read the checkpoint's own receipts: the build that produced the
image, the summary that publishes it, the historical receipt's bytes and the
historical checkpoint's own image hash. Each must name the same stripped image.
"""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
CHECKPOINTS=ROOT/'reconstruction/pump-main/checkpoints'


class ReuseError(Exception): pass


def check(ok,msg):
    # Explicit check instead of `assert`, which `python -O` strips.
    if not ok: raise ReuseError(msg)


def sha(data): return hashlib.sha256(data).hexdigest()


def load(path):
    check(path.is_file(),f'{path}: missing')
    return json.loads(path.read_text())


def verify(packet, root=ROOT):
    """Return the receipt digest a checkpoint reuses, or None when it reuses none."""
    packet=Path(packet)
    if not (packet/'runtime-reuse.json').exists(): return None
    reuse=load(packet/'runtime-reuse.json'); summary=load(packet/'summary.json')
    build=load(packet/'build.json')
    required=reuse['candidate_sha256_required_for_reuse']
    # The reuse condition names the image the historical cases were captured
    # against. A build that emits another image, or a summary that publishes one
    # while the build record still says the old hash, breaks that condition.
    check(build['candidate_sha256']==required,
          f'{packet.name}: build candidate {build["candidate_sha256"]} != reuse {required}')
    check(summary['stripped_sha256']==required,
          f'{packet.name}: summary stripped {summary["stripped_sha256"]} != reuse {required}')
    # Paths in the receipt are repository-relative; refuse one that leaves the
    # checkpoint tree before reading it.
    checkpoints=(Path(root)/'reconstruction/pump-main/checkpoints').resolve()
    historical_name=reuse['historical_checkpoint']
    check(isinstance(historical_name,str) and historical_name not in ('','.','..')
          and Path(historical_name).name==historical_name,
          f'{packet.name}: historical checkpoint must be a sibling name')
    historical_directory=(checkpoints/historical_name).resolve()
    check(historical_directory.parent==checkpoints,
          f'{packet.name}: historical checkpoint is outside the checkpoints')
    receipt_name=Path(reuse['historical_receipt'])
    check(not receipt_name.is_absolute(),
          f'{packet.name}: historical receipt must be repository-relative')
    receipt=(Path(root)/receipt_name).resolve()
    check(checkpoints in receipt.parents,
          f'{packet.name}: historical receipt {reuse["historical_receipt"]} is outside the checkpoints')
    check(historical_directory in receipt.parents,
          f'{packet.name}: historical receipt is not in its named historical checkpoint')
    raw=receipt.read_bytes()
    check(sha(raw)==reuse['historical_compressed_sha256'],
          f'{packet.name}: historical receipt {sha(raw)} != {reuse["historical_compressed_sha256"]}')
    uncompressed=gzip.decompress(raw)
    check(sha(uncompressed)==reuse['historical_uncompressed_sha256'],
          f'{packet.name}: historical receipt content differs from its recorded digest')
    # The historical checkpoint must itself claim the image the reuse names;
    # otherwise the cases came from bytes neither checkpoint publishes.
    # `historical_checkpoint` is a sibling name, `historical_receipt` is repository-relative.
    transcript=json.loads(uncompressed)
    check(transcript['candidate_sha256']==required,
          f'{packet.name}: historical receipt candidate differs from its required image')
    historical=load(historical_directory/'summary.json')
    check(historical['stripped_sha256']==required,
          f'{packet.name}: historical {reuse["historical_checkpoint"]} stripped '
          f'{historical["stripped_sha256"]} != reuse {required}')
    return reuse['historical_compressed_sha256']


def main():
    parser=argparse.ArgumentParser(description='Bind each reused runtime receipt to its checkpoint image')
    parser.add_argument('--repo-root',type=Path,default=ROOT)
    parser.add_argument('packets',nargs='*',type=Path)
    args=parser.parse_args()
    packets=args.packets or sorted(p for p in Path(args.repo_root).glob(
        'reconstruction/pump-main/checkpoints/*') if p.is_dir())
    # A wrong --repo-root, or a checkpoints folder that went missing, used to
    # leave this empty and still print PASS: a scan of nothing proves nothing.
    check(packets,f'no checkpoint packets found under {args.repo_root}')
    reusing=[(p,verify(p,args.repo_root)) for p in packets]
    bound=[(p,h) for p,h in reusing if h is not None]
    for packet,receipt in bound:
        print(f'{packet.name}: reuses {receipt[:16]} for its own stripped image')
    print(f'PASS: {len(bound)} of {len(reusing)} checkpoints reuse a runtime receipt, '
          f'each bound to the image it publishes')


if __name__=='__main__':
    try: main()
    except ReuseError as error: sys.exit(f'FAIL: {error}')
