"""Captured-program checks for the stored length of token accounts and mints.

Every case replays a fixed case of an existing captured test, on the captured
`evidence/original/pump/deployed.so` under LiteSVM, with one token account or
mint rewritten to another length just as the fixture stores it. The run on the
standard length is the twin: `programs/pump/recovered/token_lengths_host.rs`
says whether that outcome holds or turns into a given failure. This shows
matching behavior on these inputs only; it is not a byte-identity claim.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import collections
import hashlib
import importlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/token_lengths_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
INS = {bytes(i['discriminator']): i for i in IDL['instructions']}
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
T22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
SYSTEM = Pubkey.default()
SYSVAR = Pubkey.from_string('Sysvar1111111111111111111111111111111111111')
MODULES = ('v2_token_quote', 'sell_v2', 'buy_v2', 'legacy_buy', 'legacy_sell', 'v3_trade_accounting',
           'v3_exact_quote', 'token_incentives', 'claim_cashback_v2', 'creator_fee_collect', 'sweep_fees',
           'creator_fee_distribution_quote', 'migrate', 'migrate_v2', 'multi_hop_hop', 'holder_distribution_token')
LENGTHS = (0, 4, 45, 81, 82, 83, 164, 165, 166, 167, 200)
# A route decides how these slots are read, so one table row cannot name them.
SKIPPED = [('distribute_creator_fees_v2', 'creator_vault_quote_token_account'), ('migrate', 'user_pool_token_account'), ('multi_hop_curve_swap', 'buyback_fee_recipient')]
# The first passing case of these two opens no ATA.
PER_ROUTE = {'migrate_v2': 2, 'holder_distribution_token': 2}
SHAPE = {'key': None, 'length': None, 'tagged': False}
SEEN = {}
LOG = []


def rent(length):
    return (128 + length) * 6_960


def kind_of(owner, data):
    if owner not in (TOKEN, T22):
        return None
    if len(data) == 165 or (len(data) > 165 and data[165] == 2):
        return 'token'
    if len(data) == 82 or (len(data) > 165 and data[165] == 1):
        return 'mint'
    return None


def reshape(kind, data, length, tagged):
    body = data[:165 if kind == 'token' else 82]
    if length <= len(body):
        return body[:length]
    out = bytearray(body.ljust(length, b'\0'))
    if tagged:
        out[165] = 2 if kind == 'token' else 1
    return bytes(out)


class SharedVm:
    """LiteSVM with the programs loaded once; the fixture still writes through
    `set_account`, and reads the shaped account back at its standard length."""
    vm = None
    fresh = True
    loaded = set()
    touched = set()

    def __init__(self):
        c = SharedVm
        if c.vm is None:
            c.vm, c.fresh, c.loaded, c.touched = LiteSVM(), True, set(), set()
        for key in c.touched:
            account = c.vm.get_account(key)
            if account is not None and not account.executable and account.owner != SYSVAR:
                c.vm.set_account(key, Account(0, b'', SYSTEM))
        c.touched = set()
        c.vm.expire_blockhash()
        SEEN.clear()
        LOG.clear()

    def with_sigverify(self, value):
        if SharedVm.fresh:
            SharedVm.vm = SharedVm.vm.with_sigverify(value)
        return self

    def with_transaction_history(self, value):
        if SharedVm.fresh:
            SharedVm.vm = SharedVm.vm.with_transaction_history(value)
        return self

    def add_program_from_file(self, key, path):
        SharedVm.fresh = False
        if key not in SharedVm.loaded:
            SharedVm.loaded.add(key)
            SharedVm.vm.add_program_from_file(key, path)

    def add_program(self, key, data):
        SharedVm.fresh = False
        if key not in SharedVm.loaded:
            SharedVm.loaded.add(key)
            SharedVm.vm.add_program(key, data)

    def set_account(self, key, account):
        SharedVm.touched.add(key)
        data = bytes(account.data)
        kind = kind_of(account.owner, data)
        if kind:
            SEEN[key] = (kind, account.owner, len(data))
            if SHAPE['key'] == key:
                new = reshape(kind, data, SHAPE['length'], SHAPE['tagged'])
                account = Account(account.lamports + max(rent(len(new)) - account.lamports, 0), new, account.owner,
                                  account.executable, account.rent_epoch)
        SharedVm.vm.set_account(key, account)

    def get_account(self, key):
        account = SharedVm.vm.get_account(key)
        if account is not None and key == SHAPE['key']:
            stored = SEEN.get(key, (0, 0, 0))[2]
            data = bytes(account.data)
            if len(data) != stored:
                return Account(account.lamports, data[:stored].ljust(stored, b'\0'), account.owner,
                               account.executable, account.rent_epoch)
        return account

    def send_transaction(self, tx):
        keys = list(tx.message.account_keys)
        SharedVm.touched |= set(keys)
        result = SharedVm.vm.send_transaction(tx)
        slots = [(bytes(i.data)[:8], [keys[k] for k in bytes(i.accounts)]) for i in tx.message.instructions
                 if keys[i.program_id_index] == PUMP]
        LOG.append((slots, result, keys))
        return result

    def __getattr__(self, name):
        return getattr(SharedVm.vm, name)


def outcome(result):
    """`None` on success, else `<failing program>:<error>`."""
    if not type(result).__name__.startswith('Failed'):
        return None
    text = repr(result.err())
    logs = list(result.meta().logs())
    if any('panicked' in line for line in logs):
        return 'panic'
    code = re.search(r'Custom\(\s*(?:code:\s*)?(\d+)', text)
    what = code.group(1) if code else re.findall(r'[A-Z]\w+', text)[-1]
    names = {str(TOKEN): 'token', str(T22): 't22', str(PUMP): 'pump'}
    for line in logs:
        failed = re.match(r'Program (\S+) failed', line)
        if failed:
            return f"{names.get(failed.group(1), failed.group(1)[:6])}:{what}"
    return f'?:{what}'


def first_ops(result, keys):
    """The first token instruction of the run that names each account."""
    out = {}
    meta = result.meta() if type(result).__name__.startswith('Failed') else result
    for group in meta.inner_instructions():
        for inner in group:
            item = inner.instruction()
            if keys[item.program_id_index] in (TOKEN, T22):
                for index in bytes(item.accounts):
                    out.setdefault(keys[index], bytes(item.data)[0])
    return out


def run(module, item):
    LOG.clear()
    try:
        module.run_captured(item)
    except BaseException:
        if not LOG:
            return 'unsent'
    for _, result, _ in LOG:
        found = outcome(result)
        if found is not None:
            return found
    return None


def replay(name):
    """One row per (base case, token account or mint, length)."""
    SharedVm.vm = None
    module = importlib.import_module(f'test_{name}_captured')
    rows, chosen = [], collections.Counter()
    with mock.patch.object(module, 'LiteSVM', SharedVm):
        for item in module.fixed_cases():
            item = item[1] if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str) else item
            SHAPE.update(key=None)
            SharedVm()
            twin = run(module, item)
            if twin == 'unsent' or not LOG or not LOG[-1][0]:
                continue
            found = twin.split(':')[-1] if twin else ''
            if twin is not None and not (found.isdigit() and int(found) >= 6000):
                continue
            disc, keys = LOG[-1][0][-1]
            instruction = INS.get(disc)
            if instruction is None:
                continue
            tag = (instruction['name'], twin is None, any(v[1] == T22 for v in SEEN.values()))
            if chosen[tag] >= PER_ROUTE.get(name, 1):
                continue
            chosen[tag] += 1
            names = [a['name'] for a in instruction['accounts']]
            seen, first = dict(SEEN), first_ops(LOG[-1][1], LOG[-1][2])
            where = {}
            for index, key in enumerate(keys):
                where.setdefault(key, names[index] if index < len(names) else f'rem{index - len(names)}')
            for key, (kind, owner, stored) in seen.items():
                slot = where.get(key)
                if slot is None or stored != (165 if kind == 'token' else 82) or (instruction['name'], slot) in SKIPPED:
                    continue
                for length in LENGTHS:
                    for tagged in (False, True) if length > 165 else (False,):
                        SHAPE.update(key=key, length=length, tagged=tagged)
                        SharedVm()
                        result = run(module, item)
                        SHAPE.update(key=None)
                        rows.append({'module': name, 'request': ','.join(map(str, (
                            instruction['name'], slot, kind, 't22' if owner == T22 else 'spl', length, int(tagged),
                            int(twin is None), '-' if key not in first else first[key]))),
                            'program': 't22' if owner == T22 else 'token', 'twin': twin, 'result': result})
    return rows


def expected_text(answer, row):
    if answer == 'same':
        return row['twin']
    return {'pump:data': 'pump:InvalidAccountData', 'ata:owner': 'AToken:IllegalOwner',
            'token:data': f"{row['program']}:InvalidAccountData"}.get(
                answer, answer.replace('token:', f"{row['program']}:"))


def replay_all():
    def one(name):
        done = subprocess.run([sys.executable, '-I', '-B', __file__, '--replay', name], capture_output=True, text=True,
                              check=True, timeout=900)
        return json.loads(done.stdout.splitlines()[-1])
    with ThreadPoolExecutor(4) as pool:
        return [row for rows in pool.map(one, MODULES) for row in rows]


class TokenLengths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'host'
        subprocess.run(['rustc', '--edition=2021', '-D', 'warnings', '-A', 'dead_code', str(HOST_SOURCE), '-o', str(host)],
                       check=True, capture_output=True)
        cls.rows = replay_all()
        request = ''.join(r['request'] + '\n' for r in cls.rows)
        out = subprocess.run([str(host)], input=request, capture_output=True, text=True, check=True).stdout.splitlines()
        cls.answers = out
        print(f'{len(cls.rows)} cases', file=sys.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_captured_elf_is_pinned(self):
        self.assertEqual(hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest(), ELF_SHA256)

    def test_every_length_matches_the_captured_program(self):
        self.assertGreaterEqual(len(self.rows), 30)
        wrong = [(r['request'], r['twin'], r['result'], a) for r, a in zip(self.rows, self.answers)
                 if r['result'] != expected_text(a, r)]
        self.assertEqual(len(self.rows), len(self.answers))
        self.assertEqual(wrong[:5], [])
        self.assertEqual(len(wrong), 0)

    def test_every_answer_was_reached(self):
        reached = collections.Counter(self.answers)
        for answer in ('same', 'pump:data', 'pump:6070', 'ata:owner', 'token:data', 'token:2'):
            self.assertGreater(reached[answer], 0, answer)
        self.assertEqual({r['module'] for r in self.rows}, set(MODULES))

    def test_passing_decoder_is_not_enough_for_spl_token(self):
        rows = [r for r, a in zip(self.rows, self.answers)
                if a == 'token:data' and r['request'].split(',')[3] == 'spl' and r['request'].split(',')[4:6] == ['167', '1']]
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(r['result'] == 'token:InvalidAccountData' for r in rows))


if __name__ == '__main__':
    if sys.argv[1:2] == ['--replay']:
        print(json.dumps(replay(sys.argv[2])))
    else:
        unittest.main()
