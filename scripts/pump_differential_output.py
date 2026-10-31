"""Prepare and atomically publish Pump differential reports without input loss."""
import errno
import os
from pathlib import Path
import sys
import secrets


def aliases(destination, source):
    """True when destination is source or lies inside it, compared by inode.

    samefile() compares the filesystem entries themselves, so a differently
    spelled path for the same file is caught on a case-insensitive volume, and
    the comparison applies to directory inputs as well as regular files.
    """
    probe = destination
    while True:
        if probe.exists() and probe.samefile(source):
            return True
        if probe.parent == probe:
            return False
        probe = probe.parent


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
            if (destination == source or destination.is_relative_to(source)
                    or (source.exists() and aliases(destination, source))):
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
        staged_identity = None
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
                metadata = os.fstat(stream.fileno())
                staged_identity = (metadata.st_dev, metadata.st_ino)
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
            self._sync_directory(self.output.parent)
        finally:
            if staged is not None:
                try:
                    metadata = staged.lstat()
                except FileNotFoundError:
                    pass
                else:
                    if staged_identity == (metadata.st_dev, metadata.st_ino):
                        staged.unlink(missing_ok=True)

    @staticmethod
    def _sync_directory(directory):
        """Order the published directory entry behind the staged bytes.

        fsync on the staging file flushes its bytes but not the rename or
        hard link that names the report, so a crash after write() returned
        could leave the previous report in place. Flushing the directory once
        per publication requests persistence of the published name. Directory
        fsync is unsupported on Windows and on some filesystems; those retain
        the previous publication behavior. Other I/O errors remain visible.
        """
        try:
            descriptor = os.open(directory, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        except OSError as error:
            if os.name == 'nt' or error.errno in (errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP):
                return
            raise
        try:
            os.fsync(descriptor)
        except OSError as error:
            if error.errno in (errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP):
                return
            raise
        finally:
            os.close(descriptor)
