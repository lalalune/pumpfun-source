"""Captured-program checks for the `msg!` lines of the Pump handlers.

The existing captured tests of these instructions compare state, events and
error codes. Here the same cases run from the captured
`evidence/original/pump/deployed.so` on LiteSVM, and every handler log line of
a case that gets that far must equal the answer of
`programs/pump/recovered/handler_logs_host.rs`, byte for byte: the no-op
messages and the GlobalVolumeAccumulator dump of
`admin_update_token_incentives`. The fixtures come from those tests. This
shows matching behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_account_lifecycle_captured as lifecycle  # noqa: E402
import test_claim_cashback_captured as cashback  # noqa: E402
import test_claim_cashback_v2_captured as cashback_v2  # noqa: E402
import test_creator_assignment_captured as assignment  # noqa: E402
import test_creator_fee_collect_captured as collect  # noqa: E402
import test_creator_fee_distribution_captured as distribution  # noqa: E402
import test_migrate_captured as migrate  # noqa: E402
import test_migrate_v2_captured as migrate_v2  # noqa: E402
import test_sweep_fees_captured as sweep  # noqa: E402
import test_token_incentives_captured as incentives  # noqa: E402
import test_token_schedule_captured as schedule  # noqa: E402

PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/handler_logs_host.rs'
MODULES = (lifecycle, cashback, cashback_v2, assignment, collect, distribution, sweep, incentives, schedule)
EXECUTABLE_RECIPIENT = 6052
MESSAGES = ('Nothing to sweep for fee bucket ', 'Bonding curve has creator already set', 'Missing metaplex creators',
            'No tokens to claim', 'No cashback to claim', 'No changes in accumulator for user=',
            'Account already has the correct size', 'Account already has more than ', 'Unable to distribute to ',
            'Insufficient fees for distribution.', 'No creator fee to collect', 'Bonding curve already migrated',
            'Creator account does not have enough rent-exemption lamports',
            'Creator account is executable, so it cannot receive lamports', 'GlobalVolumeAccumulator=')


class SharedVm:
    """One VM for every case: programs load once, each case clears the last one's accounts."""
    inner = None
    logs = ()
    touched = []

    def __init__(self):
        cls = SharedVm
        if cls.inner is None:
            cls.inner = LiteSVM().with_sigverify(True).with_transaction_history(0)
            cls.loaded = set()
        for key in dict.fromkeys(cls.touched):
            cls.inner.set_account(key, Account(0, b'', Pubkey.default()))
        cls.touched = []

    def with_sigverify(self, _):
        return self

    def with_transaction_history(self, _):
        return self

    def add_program_from_file(self, key, path):
        if key not in SharedVm.loaded:
            SharedVm.loaded.add(key)
            SharedVm.inner.add_program_from_file(key, path)

    def set_account(self, key, account):
        SharedVm.touched.append(key)
        SharedVm.inner.set_account(key, account)

    def send_transaction(self, tx):
        # Accounts a case creates must go too; programs and sysvars stay.
        accounts = [(k, SharedVm.inner.get_account(k)) for k in tx.message.account_keys]
        SharedVm.touched += [k for k, a in accounts if not (a and a.executable) and k != Pubkey.default()
                             and not str(k).startswith('Sysvar')]
        result = SharedVm.inner.send_transaction(tx)
        SharedVm.logs = tuple((result.meta() if hasattr(result, 'meta') else result).logs())
        return result

    def __getattr__(self, name):
        return getattr(SharedVm.inner, name)


class RecordingVm:
    """The migrate tests install Pump through the upgradeable loader, so they keep their own VM per case."""

    def __init__(self):
        self.inner = LiteSVM()

    def with_transaction_history(self, count):
        self.inner = self.inner.with_transaction_history(count)
        return self

    def send_transaction(self, tx):
        result = self.inner.send_transaction(tx)
        SharedVm.logs = tuple((result.meta() if hasattr(result, 'meta') else result).logs())
        return result

    def __getattr__(self, name):
        return getattr(self.inner, name)


def handler_lines():
    lines = [line[13:] for line in SharedVm.logs if line.startswith('Program log: ')]
    return '|'.join(line for line in lines if line.startswith(MESSAGES)) or '-'


def sweep_line(c):
    return f"sweep,{int(c['bucket'] == 'creator')},{c['creator_fee'] if c['bucket'] == 'creator' else c['protocol_fees']}"


def tokens_line(c):
    days = ';'.join(f'{d}:{s}:{v}' for d, s, v in c['days'])
    return (f"tokens,{c['now']},{c['start']},{c['end']},{c['secs']},{c['vault']},{c['unclaimed']},{c['claimed']},"
            f"{c['volume']},{c['last_update']},{days}")


def sync_line(c):
    return f"sync,{bytes(incentives.USER).hex()},{c['claimed']},{c['last_update']},{c['now']},{c['start']}"


def cashback_line(c):
    return f"cashback,{c['lamports']},{c['size']}"


def cashback_v2_line(c):
    if c['native']:
        return f"cashback,{cashback_v2.rent(cashback_v2.UVA_LEN) + c['extra']},{cashback_v2.UVA_LEN}"
    return f"cashback_token,{'-' if c['uva_ata'] is None else c['uva_ata']}"


def collect_line(c):
    fields = collect.host_line(c).split(',')
    quote = fields[5]
    if quote.startswith('spl'):
        tokens = quote.split(':')[1]
        quote = f"token:{0 if tokens == '-' else tokens}"
    return f"collect,{fields[1]},{fields[2]},{fields[3]},{fields[4]},{quote}"


def extend_line(c):
    return f"extend,{c['len']},{c['kind']}"


def creator_line(c):
    # A curve cut before its creator field reads as having none.
    has_creator = c['curve_creator'] != 0 and c['curve_len'] >= 81
    return f"creator,{int(c['op'] != 'set')},{int(has_creator)},{int(c['creators'] is not None)}"


def migrate_line(c):
    return f"migrate,{c['vtr']},{c['vqr']},{c['rtr']},{c['rqr']}"


def migrate_cases(module):
    zero = dict(vtr=0, vqr=0, rtr=0, rqr=0)
    return [module.case(**zero), module.case(**dict(zero, complete=0)), module.case(**dict(zero, faults='W')),
            *(module.case(**dict(zero, **{field: 1})) for field in zero), module.case()]


def run_distribute_v2(item):
    """`distribute_creator_fees_v2` on the native quote, from the `distribute_creator_fees` fixture."""
    d = distribution
    vm = SharedVm()
    vm.add_program_from_file(d.PUMP, d.PUMP_ELF)
    vm.add_program_from_file(incentives.TOKEN, incentives.TOKEN_ELF)
    vm.add_program_from_file(incentives.ATA, incentives.ATA_ELF)
    vm.set_clock(d.Clock(100, d.TIMESTAMP, 0, 0, d.TIMESTAMP))
    wsol = Pubkey.from_string('So11111111111111111111111111111111111111112')
    vm.set_account(d.PAYER.pubkey(), Account(10**12, b'', d.SYSTEM))
    vm.set_account(d.MINT, Account(10**9, d.mint_data(), d.TOKEN))
    vm.set_account(wsol, Account(10**9, d.mint_data(), d.TOKEN))
    vm.set_account(d.CURVE, Account(10**9, d.curve_data(item), d.PUMP))
    vm.set_account(d.SHARING, Account(10**9, d.sharing_data(item), d.FEES))
    if item['vault']:
        vm.set_account(d.VAULT, Account(item['vault'], b'', d.SYSTEM))
    recipients = []
    for i, h in enumerate(item['holders'][:item['remaining']]):
        recipients.append(d.holder_key(i, h))
        if h['lamports'] and h['key'] == 'own':
            vm.set_account(recipients[-1], Account(h['lamports'], bytes(h['data_len']), d.SYSTEM))
    vault_ata = Pubkey.find_program_address([bytes(d.VAULT), bytes(d.TOKEN), bytes(wsol)], incentives.ATA)[0]
    names = {'payer': d.PAYER.pubkey(), 'mint': d.MINT, 'bonding_curve': d.CURVE, 'sharing_config': d.SHARING,
             'creator_vault': d.VAULT, 'system_program': d.SYSTEM, 'event_authority': d.EVENT_AUTHORITY, 'program': d.PUMP,
             'creator_vault_quote_token_account': vault_ata, 'quote_mint': wsol, 'quote_token_program': d.TOKEN,
             'associated_token_program': incentives.ATA}
    ix = d.IX['distribute_creator_fees_v2']
    metas = [AccountMeta(names[a['name']], bool(a.get('signer')), bool(a.get('writable'))) for a in ix['accounts']]
    metas += [AccountMeta(key, False, True) for key in recipients]
    tx = Transaction.new_signed_with_payer(
        [set_compute_unit_limit(1_400_000), Instruction(d.PUMP, bytes(ix['discriminator']) + bytes([0]), metas)], d.PAYER.pubkey(),
        [d.PAYER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        code = re.search(r'Custom\((\d+)\)', str(result.err()))
        return {'error': int(code.group(1)) if code else str(result.err())}
    return {'error': None}


def distribute_line(c):
    return f'distribute,{distribution.host_line(c)},{bytes(distribution.PUMP).hex()}'


def schedule_line(c):
    fields = [schedule.gva_data(c).hex(), c['start'], c['end'], c['seconds'], c['day'], c['supply'],
              bytes(schedule.MINT).hex(), schedule.NOW, bytes(schedule.GVA).hex(), bytes(schedule.PUMP).hex(), 10**9]
    return 'schedule,' + ','.join(str(f) for f in fields)


def routes():
    claims = incentives.fixed_cases() + incentives.random_cases()
    return (
        (sweep.run_captured, sweep.fixed_cases() + sweep.random_cases(), sweep_line),
        (incentives.run_captured, [c for c in claims if c['op'] == 'claim'], tokens_line),
        (incentives.run_captured, [c for c in claims if c['op'] == 'sync'], sync_line),
        (cashback.run_captured, cashback.fixed_cases() + cashback.random_cases(), cashback_line),
        (cashback_v2.run_captured, cashback_v2.fixed_cases() + cashback_v2.random_cases(), cashback_v2_line),
        (collect.run_captured, collect.fixed_cases() + collect.random_cases(), collect_line),
        (lifecycle.run_captured, [c for c in lifecycle.fixed_cases() + lifecycle.random_cases() if c['op'] == 'extend'],
         extend_line),
        (assignment.run_captured, [c for c in assignment.fixed_cases() + assignment.random_cases()
                                   if c['op'] != 'migrate'], creator_line),
        (distribution.run_captured, distribution.fixed_cases() + distribution.random_cases(), distribute_line),
        (run_distribute_v2, [c for c in distribution.fixed_cases() + distribution.random_cases()
                             if c['op'] == 'distribute'], distribute_line),
        (schedule.run_captured, schedule.fixed_cases() + schedule.random_cases(), schedule_line),
        (migrate.run_captured, migrate_cases(migrate), migrate_line),
        (migrate_v2.run_captured, migrate_cases(migrate_v2), migrate_line),
    )


class HandlerLogsCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest() == ELF_SHA256
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'handler-logs-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.patches = [mock.patch.object(m, 'LiteSVM', SharedVm) for m in MODULES]
        cls.patches += [mock.patch.object(m, 'LiteSVM', RecordingVm) for m in (migrate, migrate_v2)]
        for patch in cls.patches:
            patch.start()
        cls.seen, cls.seen_v2 = set(), set()

    @classmethod
    def tearDownClass(cls):
        for patch in cls.patches:
            patch.stop()
        cls.tmp.cleanup()

    def host_answers(self, lines):
        text = ''.join(line + '\n' for line in lines)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def compare(self, lines, runs):
        answers = self.host_answers(lines)
        self.assertEqual(len(answers), len(lines))
        for line, answer, run in zip(lines, answers, runs):
            with self.subTest(case=line[:200]):
                reached, logged = run()
                self.assertEqual(logged, answer if reached else '-')
        return answers

    def run_route(self, run, cases, line):
        def one(case):
            def captured():
                error = run(case)['error']
                logged = handler_lines()
                type(self).seen.update(m for m in MESSAGES if m in logged)
                if run is run_distribute_v2:
                    type(self).seen_v2.update(m for m in MESSAGES if m in logged)
                # A short curve fails when it is stored, after the handler has logged.
                return error in (None, EXECUTABLE_RECIPIENT, 'borsh_write'), logged
            return captured
        self.compare([line(c) for c in cases], [one(c) for c in cases])

    def test_every_route_matches_captured_program(self):
        for run, cases, line in routes():
            self.run_route(run, cases, line)
        self.assertEqual(type(self).seen, set(MESSAGES))
        self.assertEqual(type(self).seen_v2, {'Insufficient fees for distribution.', 'Unable to distribute to '})

    def test_messages_are_in_the_elf(self):
        data = PUMP_ELF.read_bytes()
        for message in MESSAGES:
            self.assertIn(message.encode(), data)

    def test_checker_rejects_an_altered_line(self):
        # Negative control: one changed digit of the dump is not equal.
        item = schedule.case()
        answer = self.host_answers([schedule_line(item)])[0]
        schedule.run_captured(item)
        self.assertEqual(handler_lines(), answer)
        self.assertNotEqual(handler_lines(), answer.replace('start_time: 1699568000', 'start_time: 1699568001'))


if __name__ == '__main__':
    unittest.main()
