#!/usr/bin/env python3
"""Build native recovered fee routing for original-versus-recovered tests."""
import argparse
import pathlib
import subprocess
import tempfile

from deep_disassembly import rename_directory

ROOT = pathlib.Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--output', type=pathlib.Path, required=True)
a = p.parse_args()
out = a.output.resolve()
if out.exists():
    raise FileExistsError(out)
out.parent.mkdir(parents=True, exist_ok=True)
src = ROOT / 'programs/pump-fees/recovered'
with tempfile.TemporaryDirectory(prefix='.quote-host-', dir=out.parent) as temporary:
    # A failed compile must not leave a partial output that blocks the rerun.
    staging = pathlib.Path(temporary) / 'result'
    staging.mkdir()  # Retain ordinary umask permissions after publication.
    math = staging / 'libpump_fees_math.rlib'
    quote = staging / 'libpump_quote_fees.rlib'
    commands = [
        ['--crate-name', 'pump_fees_math', '--crate-type', 'rlib', str(src / 'fee_selection.rs'), '-o', str(math)],
        ['--crate-name', 'pump_quote_fees', '--crate-type', 'rlib', '--extern', f'pump_fees_math={math}', str(src / 'quote_fees.rs'), '-o', str(quote)],
        ['--extern', f'pump_fees_math={math}', '--extern', f'pump_quote_fees={quote}', '-L', f'dependency={staging}', str(src / 'quote_fees_host.rs'), '-o', str(staging / 'quote-fees-host')],
    ]
    for cmd in commands:
        subprocess.run(['rustc', '--edition=2021', '-O', *cmd], check=True)
    rename_directory(staging, out)
print(out / 'quote-fees-host')
