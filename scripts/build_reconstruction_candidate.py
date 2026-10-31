#!/usr/bin/env python3
"""Proposed routing: defaults/old overrides retain the frozen historical helper.
Only explicit v1.53/v1.54 select the measured supported-target adapter.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

DEFAULTS = {'pump': 'v1.44', 'pump_amm': 'v1.44', 'pump_fees': 'v1.44', 'mayhem': 'v1.52'}
ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/build_partial_candidate.py').is_file())
ADAPTER = Path(__file__).with_name('build_supported_sbpf_candidate.py')


def command(arguments):
    parser = argparse.ArgumentParser(description=__doc__, add_help=False, allow_abbrev=False)
    parser.add_argument('--program', choices=DEFAULTS, required=True)
    parser.add_argument('--tools-version')
    selected, unknown = parser.parse_known_args(arguments)
    # The historical helper expands abbreviations this router cannot route on,
    # and its last flag wins, so `--tools v1.53` would lose to the default.
    for argument in unknown:
        flag = argument.split('=', 1)[0]
        if len(flag) > 2 and any(name.startswith(flag) for name in ('--program', '--tools-version')):
            parser.error(f'abbreviated routing flag {flag}: spell it out')
    forwarded = list(arguments)
    helper = ADAPTER if selected.tools_version in ('v1.53', 'v1.54') else ROOT/'scripts/build_partial_candidate.py'
    if selected.tools_version is None:
        forwarded += ['--tools-version', DEFAULTS[selected.program]]
    return [sys.executable, str(helper), *forwarded]


def main(arguments=None):
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    if '--help' in arguments or '-h' in arguments:
        print(__doc__)
        print('Unchanged defaults: Pump/AMM/Fees=v1.44; Mayhem=v1.52.')
        print('Arguments: --manifest PATH --program NAME --artifact-name NAME.so --output PATH')
        print('Optional: --tools-version VERSION --extra-input PATH (repeatable) --dry-run')
        print('Dry-run never invokes Cargo/rustc; explicit v1.53/v1.54 validate pinned tools and source recipe.')
        return 0
    selected = command(arguments)
    if '--dry-run' in arguments and Path(selected[1]).name == 'build_partial_candidate.py':
        print(json.dumps({'route': 'historical helper; no build invoked',
                          'command': [x for x in selected if x != '--dry-run'],
                          'default_map': DEFAULTS, 'historical_helper_unchanged': True}, indent=2))
        return 0
    return subprocess.call(selected)


if __name__ == '__main__':
    raise SystemExit(main())
