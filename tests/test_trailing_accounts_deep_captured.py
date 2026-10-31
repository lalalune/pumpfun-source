"""Captured-program checks for accounts past the declared list, wider harvest.

The deep companion of `tests/test_trailing_accounts_captured.py`: the same
wrapper around LiteSVM, collecting prefixes of 26 base modules with up to 300 sends each and
eight rows kept per class, for a wider recorded harvest. Open rows are observations excluded from native prediction counts. Each row goes to
`programs/pump/recovered/trailing_accounts_deep_host.rs`, whose model
confirms the arms the first test leaves unconfirmed and carries the
corrections the wider harvest forces. An answer of `same` must match the
plain run in error, logs and account state. This shows matching behavior on
these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import collections
import concurrent.futures
import hashlib
import importlib
import io
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tests'))

from solders.instruction import AccountMeta, Instruction
import solders.litesvm as litesvm
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/trailing_accounts_deep_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
IX = {bytes(i['discriminator']): i for i in IDL['instructions']}
RealVm = litesvm.LiteSVM

# Unknown keys: absent from every fixture, even slots writable.
EXTRAS = [AccountMeta(Pubkey.from_bytes(bytes([230 + i]) * 32), False, i % 2 == 0) for i in range(9)]
COUNTS = (1, 2, 3, 5, 8, 9)
SENDS = 300
PER_CLASS = 8
MODULES = (
    'test_global_admin_captured',
    'test_global_lifecycle_captured',
    'test_fee_params_captured',
    'test_creator_fee_distribution_captured',
    'test_creator_fee_distribution_quote_captured',
    'test_holder_distribution_captured',
    'test_legacy_buy_captured',
    'test_legacy_sell_captured',
    'test_legacy_cashback_captured',
    'test_migrate_captured',
    'test_migrate_v2_captured',
    'test_multi_hop_hop_captured',
    'test_sell_v2_captured',
    'test_v3_trade_accounting_captured',
    'test_claim_cashback_captured',
    'test_create_v2_captured',
    'test_creator_fee_distribution_token2022_captured',
    'test_quote_control_captured',
    'test_quote_control_init_captured',
    'test_v2_token_quote_captured',
    'test_distribution_alias_captured',
    'test_sweep_alias_captured',
    'test_v3_alias_captured',
    'test_trade_recipients_captured',
    'test_claim_cashback_v2_token2022_captured',
    'test_creator_fee_collect_token2022_captured',
)


def label(result):
    """Outcome of a run: `ok`, a custom code, or the runtime error name."""
    if not isinstance(result, FailedTransactionMetadata):
        return 'ok'
    text = str(result.err())
    code = re.search(r'InstructionErrorCustom\((\d+)\)', text)
    if code:
        return code.group(1)
    if any('panicked' in line for line in result.meta().logs()):
        return 'panic'
    name = re.search(r'(?:Fieldless|Tagged)\((?:InstructionErrorFieldless\.)?(\w+)', text)
    return name.group(1) if name else text[:40]


def trace(result):
    meta = result.meta() if hasattr(result, 'meta') else result
    return [line for line in meta.logs() if ' consumed ' not in line]


def state(result, extras):
    """Post-run accounts of a successful simulation, without the extra keys."""
    if isinstance(result, FailedTransactionMetadata):
        return None
    skip = {str(meta.pubkey) for meta in extras}
    return sorted((str(key), str(account)) for key, account in result.post_accounts() if str(key) not in skip)


def rebuild(tx, keep, extras):
    """The transaction again with Pump's remaining accounts cut to `keep`, plus extras."""
    msg = tx.message
    keys = msg.account_keys
    head = msg.header
    signers = head.num_required_signatures
    writable_signers = signers - head.num_readonly_signed_accounts
    writable_end = len(keys) - head.num_readonly_unsigned_accounts
    writable = lambda i: i < writable_signers or signers <= i < writable_end
    out = []
    for compiled in msg.instructions:
        program = keys[compiled.program_id_index]
        metas = [AccountMeta(keys[i], i < signers, writable(i)) for i in bytes(compiled.accounts)]
        if program == PUMP and keep is not None:
            metas = metas[:keep] + extras
        out.append(Instruction(program, bytes(compiled.data), metas))
    return Transaction.new_unsigned(Message.new_with_blockhash(out, keys[0], msg.recent_blockhash))


def pump_call(tx):
    """(instruction, metas) of the only Pump instruction in `tx`, else None."""
    msg = tx.message
    calls = [c for c in msg.instructions if msg.account_keys[c.program_id_index] == PUMP]
    if len(calls) != 1:
        return None
    entry = IX.get(bytes(calls[0].data)[:8])
    if entry is None:
        return None
    return entry, [msg.account_keys[i] for i in bytes(calls[0].accounts)]


def shareholders(vm, entry, keys):
    """Stored row count of the `sharing_config` slot, 0 where the command has none."""
    names = [a['name'] for a in entry['accounts']]
    if 'sharing_config' not in names:
        return 0
    account = vm.get_account(keys[names.index('sharing_config')])
    if account is None or len(account.data) < 80:
        return 0
    return struct.unpack_from('<I', bytes(account.data), 76)[0]


class Twin:
    """LiteSVM with a simulated twin of each Pump transaction."""
    rows = []
    sends = 0
    seen = collections.Counter()
    result = None

    def __init__(self, *args):
        self.__dict__['vm'] = RealVm(*args).with_sigverify(False)

    def __getattr__(self, name):
        value = getattr(self.vm, name)
        if name.startswith('with_'):
            def chain(*args):
                self.__dict__['vm'] = value(False) if name == 'with_sigverify' else value(*args)
                return self
            return chain
        return value

    def __setattr__(self, name, value):
        setattr(self.vm, name, value)

    def send_transaction(self, tx):
        if Twin.sends >= SENDS:
            finish(stopped_at_send_limit=True)
        Twin.sends += 1
        call = pump_call(tx)
        if call is not None:
            self.twin(tx, *call)
        return self.vm.send_transaction(tx)

    def twin(self, tx, entry, keys):
        vm = self.vm
        declared = len(entry['accounts'])
        remaining = len(keys) - declared
        plain = vm.simulate_transaction(rebuild(tx, None, []))
        base = label(plain)
        key = (entry['name'], remaining, base)
        Twin.seen[key] += 1
        if remaining < 0 or Twin.seen[key] > PER_CLASS:
            return
        bare = label(vm.simulate_transaction(rebuild(tx, declared, []))) if remaining else base
        for count in COUNTS:
            extras = EXTRAS[:count]
            run = vm.simulate_transaction(rebuild(tx, len(keys), extras))
            Twin.rows.append({
                'name': entry['name'], 'remaining': remaining, 'extra': count, 'base': base, 'bare': bare,
                'rows': shareholders(vm, entry, keys), 'got': label(run),
                'same': trace(run) == trace(plain) and state(run, extras) == state(plain, extras),
            })


def finish(stopped_at_send_limit=False):
    """Report and leave: subtests would otherwise walk every remaining base case."""
    result = Twin.result
    print(json.dumps({'rows': Twin.rows, 'failures': len(result.failures), 'errors': len(result.errors), 'sends': Twin.sends, 'stopped_at_send_limit': stopped_at_send_limit, 'base_suite_completed': not stopped_at_send_limit}), flush=True)
    os._exit(0)


def collect(name):
    litesvm.LiteSVM = Twin
    module = importlib.import_module(name)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    Twin.result = unittest.TextTestResult(io.StringIO(), False, 0)
    suite.run(Twin.result)
    finish()


def harvest(name):
    run = subprocess.run([sys.executable, '-I', '-B', __file__, name], capture_output=True, text=True, timeout=540)
    if run.returncode:
        raise AssertionError(f'{name}: {run.stderr[-400:]}')
    return name, json.loads(run.stdout.splitlines()[-1])


def build_host(directory):
    binary = Path(directory) / 'trailing_accounts_deep_host'
    subprocess.run(
        ['rustc', '--edition=2021', '-D', 'warnings', '-o', str(binary), str(HOST_SOURCE)],
        check=True, capture_output=True, text=True,
    )
    return binary


def host_line(row):
    return ','.join(str(row[k]) for k in ('name', 'remaining', 'extra', 'base', 'rows'))


def ask_host(binary, rows):
    run = subprocess.run([str(binary)], input=''.join(host_line(r) + '\n' for r in rows),
                         capture_output=True, text=True, check=True)
    return run.stdout.split()


def mismatches(rows, answers):
    if len(rows) != len(answers):
        raise ValueError('one native answer is required per captured case')
    wrong = []
    for row, answer in zip(rows, answers):
        if answer == 'open':
            good = True
        elif answer == 'same':
            good = row['got'] == row['base'] and row['same']
        elif answer == 'bare':
            good = row['got'] == row['bare']
        else:
            good = row['got'] == answer
        if not good:
            wrong.append((row, answer))
    return wrong


# Open rows are harvested observations, not matched native predictions.
# A stopped prefix is not completion of the underlying base suite.
class TrailingAccountsDeepCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.host = build_host(cls.tmp.name)
        with concurrent.futures.ThreadPoolExecutor(6) as pool:
            cls.runs = dict(pool.map(harvest, MODULES))
        cls.rows = [row for run in cls.runs.values() for row in run['rows']]
        cls.answers = ask_host(cls.host, cls.rows)

    def test_collected_prefix_has_no_reported_failures(self):
        self.assertEqual({k: (v['failures'], v['errors']) for k, v in self.runs.items() if v['failures'] or v['errors']}, {})

    def test_every_answered_case_matches_captured_program(self):
        self.assertGreater(len(self.rows), 1000)
        self.assertGreater(sum(a != 'open' for a in self.answers), 0)
        wrong = mismatches(self.rows, self.answers)
        self.assertEqual(wrong[:5], [], f'{len(wrong)} mismatches')

    def test_checker_rejects_a_changed_answer(self):
        row = next(r for r, a in zip(self.rows, self.answers) if a == 'same' and r['base'] == 'ok')
        self.assertEqual(len(mismatches([row], ['6027'])), 1)
        self.assertEqual(len(mismatches([{**row, 'same': False}], ['same'])), 1)
        for answers in ([], ['same', 'same']):
            with self.assertRaisesRegex(ValueError, 'one native answer'):
                mismatches([row], answers)


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1].startswith('test_'):
        collect(sys.argv[1])
    else:
        unittest.main(verbosity=2)
