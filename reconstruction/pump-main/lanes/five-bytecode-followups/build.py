#!/usr/bin/env python3
"""Run the existing identity recipe with explicit local SDK and registry locations."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('cache', 'sdk', 'registry', 'work', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    os.environ['PUMP_RECON_HOME'] = str(args.cache.resolve())
    sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
    import fastbuild
    fastbuild.SDK = args.sdk.resolve()
    original_run = fastbuild.run_compiler

    def run(cmd, **kwargs):
        env = kwargs['env'].copy()
        env['CARGO_HOME'] = str(args.registry.resolve())
        env['PUMP_LOGICAL_REGISTRY_SRC'] = str((args.registry / 'registry/src').resolve())
        kwargs['env'] = env
        return original_run(cmd, **kwargs)

    fastbuild.run_compiler = run
    result = fastbuild.build(ROOT / 'programs/pump', args.work, args.out,
                             recipe='identity', timeout=600)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'build-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return not result['ok']


if __name__ == '__main__':
    raise SystemExit(main())
