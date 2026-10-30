"""Publish validator reports without replacing any of their input files."""
import gzip
import json
import os
from pathlib import Path
import tempfile
from probe_report import write_json_report


def protected_inputs(root, script, candidate, source):
    root, source = Path(root), Path(source)
    paths = [Path(candidate), Path(script), Path(__file__), Path(__file__).with_name('probe_report.py'),
             Path(__file__).with_name('pump_trade_fixture.py'),
             root / 'repro/pump/constant-product-differential.json',
             root / 'research/imported-lab/analysis/pump_fun/config-snapshot.json',
             root / 'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json']
    paths.extend(path for path in (root / 'evidence').rglob('*') if path.is_file())
    paths.extend(path for path in source.rglob('*') if path.is_file() and 'target' not in path.parts
                 and (path.suffix == '.rs' or path.name in ('Cargo.toml', 'Cargo.lock')))
    return paths


def validate_destination(output, inputs):
    output = Path(output)
    for path in inputs:
        path = Path(path)
        if (output.resolve() == path.resolve()
                or (output.exists() and path.exists() and output.samefile(path))):
            raise ValueError('validation output aliases an input: ' + str(output))


def write_report(output, report, inputs, *, gzip_enabled=True):
    output = Path(output)
    validate_destination(output, inputs)
    if not gzip_enabled or output.suffix != '.gz':
        write_json_report(output, report)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, staged = tempfile.mkstemp(prefix='.' + output.name + '.', dir=output.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(gzip.compress((json.dumps(report, indent=2) + '\n').encode('utf-8'), mtime=0))
            stream.flush()
            os.fsync(stream.fileno())
        validate_destination(output, inputs)
        os.replace(staged, output)
    finally:
        if os.path.exists(staged):
            os.unlink(staged)
