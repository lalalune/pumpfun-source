"""Reuse compiled local SBF programs while restoring every case's account inputs.

The fresh Harness remains available through PUMP_AMM_FRESH_VM=1. This wrapper
records accounts changed by setup and all writable transaction accounts before
execution, then restores them before the next case. Program loading is cached;
transaction history is disabled by the underlying Harness.
"""
import atexit
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
from solders.account import Account
from solders.pubkey import Pubkey

# Captured fixtures and the AMM source tree the AMM runners read on top of the
# publisher's own defaults; a receipt must never replace them either.
AMM_ROOT = Path(__file__).resolve().parents[1]
AMM_REPORT_INPUTS = (
    AMM_ROOT / 'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',
    AMM_ROOT / 'research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json',
    AMM_ROOT / 'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',
    AMM_ROOT / 'programs/pump-amm',
)

class _ResettableVM:
    def __init__(self, vm):
        self._vm = vm
        self._before = {}
        self._programs = {}

    def __getattr__(self, name):
        return getattr(self._vm, name)

    def _remember(self, key):
        if key not in self._before:
            self._before[key] = self._vm.get_account(key)

    def set_account(self, key, account):
        self._remember(key)
        return self._vm.set_account(key, account)

    def add_program_from_file(self, key, path):
        data = Path(path).read_bytes()
        digest = hashlib.sha256(data).digest()
        if self._programs.get(key) != digest:
            self._vm.add_program(key, data)
            self._programs[key] = digest

    def send_transaction(self, tx):
        message = tx.message
        header = message.header
        signed = header.num_required_signatures
        unsigned_end = len(message.account_keys) - header.num_readonly_unsigned_accounts
        signed_end = signed - header.num_readonly_signed_accounts
        for index, key in enumerate(message.account_keys):
            if index < signed_end or signed <= index < unsigned_end:
                self._remember(key)
        return self._vm.send_transaction(tx)

    def reset(self):
        for key, account in self._before.items():
            self._vm.set_account(key, account if account is not None else Account(0, b'', Pubkey.default()))
        self._before.clear()

_pinned = {}
def pin_program(path):
    """Return a private copy of one byte snapshot of path, the same for the whole run.

    acquire_harness reloads whenever a path's bytes change, so a suite that passes
    its input path to every case could run two images under one receipt.
    """
    # Key the path as given: resolving symlinks would re-pin a retargeted link.
    key = os.path.abspath(path)
    if key not in _pinned:
        directory = tempfile.mkdtemp(prefix='pump-amm-pinned-')
        atexit.register(shutil.rmtree, directory, True)
        snapshot = Path(directory) / 'program.so'
        snapshot.write_bytes(Path(key).read_bytes())
        _pinned[key] = snapshot
    return _pinned[key]

_cached = {}
def acquire_harness(program):
    # Import the LiteSVM harness only when a VM is needed: pin_program is also
    # imported by metadata-only consumers (test_tooling.py on solders wheels
    # without LiteSVM, such as Windows).
    from pump_amm_admin_differential import Harness
    if os.environ.get('PUMP_AMM_FRESH_VM') == '1':
        return Harness(program)
    key = str(Path(program).resolve())
    data = Path(key).read_bytes()
    digest = hashlib.sha256(data).digest()
    if key not in _cached or _cached[key][0] != digest:
        # Harness loads from a path. Give it the same snapshot that was hashed,
        # even if a concurrent build replaces the original path during loading.
        with tempfile.NamedTemporaryFile(prefix='pump-amm-program-', suffix='.so') as snapshot:
            snapshot.write(data)
            snapshot.flush()
            harness = Harness(snapshot.name)
        harness.vm = _ResettableVM(harness.vm)
        _cached[key] = (digest, harness)
    harness = _cached[key][1]
    harness.vm.reset()
    return harness
