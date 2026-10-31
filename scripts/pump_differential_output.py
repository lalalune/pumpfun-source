"""Prepare and atomically publish Pump differential reports without input loss."""
import os
from pathlib import Path
import sys
import secrets


class PumpReport:
    """Keep existing report replacement semantics, while protecting inputs."""

    def __init__(self, output, root, candidate, script, *, extra_inputs=(), overwrite=True):
        self.output = Path(output)
        self.root = Path(root).resolve()
        self.overwrite = overwrite
        self.inputs = [Path(script), Path(__file__), *map(Path, extra_inputs)]
        if candidate is not None:
            self.inputs.append(Path(candidate))
        # These shared images/metadata are used by the admitted Pump runners.
        self.inputs.extend(self.root / path for path in (
            'evidence/original/pump/deployed.so',
            'evidence/original/pump_fees/deployed.so',
            'evidence/original/pump_amm/deployed.so',
            'evidence/upstream/pump.json',
            'evidence/upstream/pump_fees.json',
            'evidence/upstream/pump_amm.json',
            'research/imported-lab/analysis/pump_fun/config-snapshot.json',
            'research/pump-two-curve-inputs/fixture/base-fixture.json',
            'scripts/pump_create_nested_fixture.py',
        ))
        self.inputs.extend(self.root / f'evidence/dependencies/{name}/deployed.so'
                           for name in ('spl_token', 'spl_token_2022', 'associated_token'))
        # A loaded shared fixture declares the data files it read at import.
        self.inputs.extend(Path(path) for module in tuple(sys.modules.values())
                           for path in getattr(module, 'REPORT_INPUTS', ()))
        self.check()
        self.output.parent.mkdir(parents=True, exist_ok=True)

    def check(self):
        # Include modules imported after initial admission, such as the nested
        # fixture. Do not permit a receipt to replace its executing code.
        inputs = self.inputs + [Path(module.__file__) for module in tuple(sys.modules.values())
                                if getattr(module, '__file__', None)]
        destination = self.output.resolve()
        for source in inputs:
            source = source.resolve()
            if (destination == source or (source.is_dir() and destination.is_relative_to(source))
                    or (destination.exists() and source.is_file() and destination.samefile(source))):
                raise ValueError('report output aliases an input: ' + str(self.output))
        if not self.overwrite and self.output.exists():
            raise FileExistsError('Retain prior attempts; output must be fresh: ' + str(self.output))
        # os.replace cannot publish over a directory; refuse it before the run.
        if self.output.is_dir() and not self.output.is_symlink():
            raise IsADirectoryError('report output is a directory: ' + str(self.output))

    def write(self, payload):
        """Publish complete bytes; failed staging never truncates a prior report."""
        self.check()
        staged = None
        try:
            for _ in range(100):
                path = self.output.with_name('.' + self.output.name[:32] + '.' + secrets.token_hex(8))
                try:
                    stream = path.open('xb')
                except FileExistsError:
                    continue
                staged = path
                break
            else:
                raise FileExistsError('could not create a unique report staging file')
            with stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            self.check()
            if self.overwrite:
                os.replace(staged, self.output)
                staged = None
            elif os.name == 'nt':
                os.rename(staged, self.output)
                staged = None
            else:
                os.link(staged, self.output)
        finally:
            if staged is not None:
                staged.unlink(missing_ok=True)
