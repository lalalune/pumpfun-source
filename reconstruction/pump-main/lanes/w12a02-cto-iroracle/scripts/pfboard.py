#!/usr/bin/env python3
"""pfboard.py <unstripped.so>...: rank admin_cto candidates by a heuristic frame-remap score
(not emitted code or a proof that frame differences are eliminated) next to the plain ratio and size. JSON lines on stdout."""
import argparse, json, sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, str(Path(__file__).resolve().parent))

def one(p):
    import ctoracle, framebound
    try:
        ctok, n = ctoracle.so_tokens(p)
        r0, r1, _ = framebound.bound(ctok)
        return {'so': p, 'bytes': n, 'ratio': r0, 'pf': r1}
    except Exception as e:  # noqa
        return {'so': p, 'error': repr(e)[:120]}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidates', nargs='+')
    args = parser.parse_args()
    failed = False
    with ProcessPoolExecutor(4) as ex:
        for r in ex.map(one, args.candidates):
            failed |= 'error' in r
            print(json.dumps(r), flush=True)
    raise SystemExit(1 if failed else 0)
