"""Captured-program checks for the order of Pump trade CPIs.

Reuses the inputs of the legacy, v2 and v3 captured trade tests. Each passing
case runs on `evidence/original/pump/deployed.so` on LiteSVM, and the program's
direct inner instructions (who is called, in what order, for how much) must
equal the list from `programs/pump/recovered/trade_cpi_order_host.rs`. The
amounts given to that host come from the existing trade models, so this test
adds order, not pricing. This shows matching behavior on these inputs only; it
is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.litesvm import LiteSVM
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_buy_v2_captured as buy_v2
import test_legacy_buy_captured as legacy_buy
import test_legacy_sell_captured as legacy_sell
import test_sell_v2_captured as sell_v2
import test_v2_token_quote_captured as v2_quote
import test_v3_trade_accounting_captured as v3

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = {
    ROOT / 'evidence/original/pump/deployed.so': '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    ROOT / 'evidence/original/pump_fees/deployed.so': '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e',
    ROOT / 'evidence/dependencies/spl_token/deployed.so': '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ROOT / 'evidence/dependencies/spl_token_2022/deployed.so': '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ROOT / 'evidence/dependencies/associated_token/deployed.so': '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/trade_cpi_order_host.rs'
SYSTEM_ID = '11111111111111111111111111111111'


class Recorder:
    """One LiteSVM per base test: programs stay loaded, accounts are wiped."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.loaded = set()
        self.touched = set()
        self.steps = []

    def __call__(self):
        for key in self.touched:
            if key not in self.loaded:
                self.vm.set_account(key, Account(0, b'', v3.SYSTEM))
        self.touched.clear()
        self.vm.expire_blockhash()
        return self

    def with_sigverify(self, _):
        return self

    def with_transaction_history(self, _):
        return self

    def add_program_from_file(self, key, path):
        if key not in self.loaded:
            self.vm.add_program_from_file(key, path)
            self.loaded.add(key)

    def add_program(self, key, image):
        if key not in self.loaded:
            self.vm.add_program(key, image)
            self.loaded.add(key)

    def set_account(self, key, account):
        self.touched.add(key)
        self.vm.set_account(key, account)

    def __getattr__(self, name):
        return getattr(self.vm, name)

    def send_transaction(self, tx):
        result = self.vm.send_transaction(tx)
        meta = result.meta() if isinstance(result, FailedTransactionMetadata) else result
        keys = list(tx.message.account_keys)
        self.touched.update(k for k in keys if self.is_data_account(k))
        self.steps = []
        for group in meta.inner_instructions():
            for inner in group:
                if inner.stack_height() == 2:
                    ix = inner.instruction()
                    self.steps.append((keys[ix.program_id_index], bytes(ix.data), [keys[i] for i in bytes(ix.accounts)]))
        return result

    def is_data_account(self, key):
        account = self.vm.get_account(key)
        return (account is None or not account.executable) and not str(key).startswith('Sysvar') \
            and str(key) != SYSTEM_ID and key not in self.loaded


def step_text(step, names):
    program, data, accounts = step
    label = str(program)
    if label == SYSTEM_ID:
        if data[0] == 2:
            return f'system:{names[accounts[0]]}>{names[accounts[1]]}:{struct.unpack_from("<Q", data, 4)[0]}'
        return 'init'
    if label.startswith('Token'):
        assert data[0] == 12, data
        return f'token:{names[accounts[0]]}>{names[accounts[2]]}:{struct.unpack_from("<Q", data, 1)[0]}'
    if label.startswith('pfee'):
        return 'fees'
    if label.startswith('AToken'):
        return 'ata'
    return 'event'


def line(*fields):
    return ','.join(str(int(f)) if not isinstance(f, str) else f for f in fields)


def native_names(base, vault):
    return {base.USER.pubkey(): 'user', base.CURVE: 'curve', base.FEE_RECIPIENT: 'recipient', base.BUYBACK: 'buyback',
            vault: 'vault', base.ata(base.USER.pubkey()): 'user_base', base.ata(base.CURVE): 'curve_base'}


def build(source, name, directory):
    path = Path(directory) / name
    subprocess.run(['rustc', '--edition=2021', '-D', 'warnings', str(source), '-o', str(path)], check=True)
    return path


def base_answers(host, base, cases):
    text = ''.join(base.host_line(item) + '\n' for item in cases)
    return subprocess.run([str(host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()


def trade_rows(base, directory, name, cases, shape):
    """Runs the passing cases: (request line, captured steps) per case."""
    host = build(base.HOST_SOURCE, name, directory)
    recorder = Recorder()
    rows = []
    with mock.patch.object(base, 'LiteSVM', recorder):
        for item, answer in zip(cases, base_answers(host, base, cases)):
            if answer.startswith('ok') and base.run_captured(item)['error'] is None:
                request, names = shape(item, [int(v) for v in answer.split(',')[1:]])
                rows.append((request, [step_text(s, names) for s in recorder.steps]))
    return rows


def legacy_buy_shape(base, family):
    def shape(item, f):
        tokens, sol, fee, creator, buyback, credit, complete = f[0], f[1], f[3], f[5], f[6], f[7], f[12]
        vault = base.VAULT if item['creator'] else base.DEFAULT_VAULT
        request = line(family, 1, tokens, sol, fee - buyback, buyback, creator, 0, credit - creator, 0, 0, 0, 1, complete)
        return request, native_names(base, vault)
    return shape


def legacy_sell_shape(base, family, volume):
    def shape(item, f):
        vault = base.VAULT if item.get('creator', True) else base.DEFAULT_VAULT
        request = line(family, 0, item['args'][0], f[7], 0, 0, f[4], 0, f[6], 0, volume, 0, 1, 0)
        return request, native_names(base, vault)
    return shape


def v2_quote_rows(directory):
    recorder = Recorder()
    labelled = v2_quote.fixed_cases() + v2_quote.random_cases(120)
    rows = []
    with mock.patch.multiple(v2_quote, LiteSVM=recorder, _VM=None):
        answers = v2_quote.model([c for _, c in labelled])
        v2_quote._TOUCHED.clear()
        for (_, c), (kind, m) in zip(labelled, answers):
            if kind != 'ok':
                continue
            got = v2_quote.run_captured(c)
            if got['error'] is not None:
                continue
            r = got['roles']
            sell = c['op'] == 'sell'
            created = sum(got['before'][r[k]] is None for k in ('user_quote', 'curve_quote', 'vault_quote', 'uva_quote',
                                                                 'recipient_quote', 'buyback_quote'))
            names = {r[k]: k for k in ('user_quote', 'curve_quote', 'vault_quote', 'uva_quote', 'recipient_quote',
                                       'buyback_quote', 'user_base', 'curve_base')}
            names.update({v2_quote.USER.pubkey(): 'user', v2_quote.CURVE: 'curve', r['vault']: 'vault'})
            request = line('v2quote', not sell, m['base_moved'], m['user_sent'] if sell else m['curve_sent'],
                           m['recipient_sent'], m['buyback_sent'], m['creator_sent'], c['cashback'], m['vault_rent'],
                           m['curve_rent'], not c['uva'], created, not c['whitelisted'], m['completes'])
            rows.append((request, [step_text(s, names) for s in recorder.steps]))
    return rows


def v3_rows():
    recorder = Recorder()
    labelled = v3.fixed_cases() + v3.random_cases()
    rows = []
    with mock.patch.object(v3, 'LiteSVM', recorder):
        answers = v3.model([c for _, c in labelled])
        for (_, c), (kind, m) in zip(labelled, answers):
            if kind != 'ok' or c['tf'] is not None:
                continue
            got = v3.run_captured(c)
            if got['error'] is not None:
                continue
            r = got['roles']
            user = v3.USER.pubkey()
            names = {r['user_base']: 'user_base', r['curve_base']: 'curve_base', r['user_quote']: 'user_quote',
                     r['curve_quote']: 'curve_quote', user: 'user', v3.CURVE: 'curve', r['recipient']: 'buyback_quote'}
            native, buy = r['native'], c['buy']
            moved = -m['user_quote'] if buy else m['user_quote']
            if not native and buy:
                moved = m['curve_quote']
            request = line('v3' if native else 'v3quote', buy, m['base_moved'], moved, 0, m['buyback_recipient'], 0, 0, 0,
                           m['rent_top_up'], not c['uva'], 0, 0, m['completes'])
            rows.append((request, [step_text(s, names) for s in recorder.steps]))
    return rows


class TradeCpiOrderCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        directory = cls.tmp.name
        cls.host = build(HOST_SOURCE, 'trade-cpi-order-host', directory)
        cls.rows = {
            'legacy buy': trade_rows(legacy_buy, directory, 'legacy-buy', legacy_buy.fixed_cases() + legacy_buy.random_cases(),
                                     legacy_buy_shape(legacy_buy, 'legacy')),
            'legacy sell': trade_rows(legacy_sell, directory, 'legacy-sell', legacy_sell.fixed_cases() + legacy_sell.random_cases(),
                                      legacy_sell_shape(legacy_sell, 'legacy', 0)),
            'v2 buy': trade_rows(buy_v2, directory, 'buy-v2', buy_v2.fixed_cases() + buy_v2.random_cases(),
                                 legacy_buy_shape(buy_v2, 'v2')),
            'v2 sell': trade_rows(sell_v2, directory, 'sell-v2', sell_v2.fixed_cases() + sell_v2.random_cases(),
                                  legacy_sell_shape(sell_v2, 'v2', 1)),
            'v2 quote': v2_quote_rows(directory),
            'v3': v3_rows(),
        }

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def model(self, rows):
        text = ''.join(request + '\n' for request, _ in rows)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return [a.split() for a in out.split('\n')[:-1]]

    def test_every_family_matches_captured_order(self):
        for name, rows in self.rows.items():
            answers = self.model(rows)
            self.assertEqual(len(answers), len(rows))
            self.assertGreaterEqual(len(rows), 20, name)
            for (request, steps), answer in zip(rows, answers):
                with self.subTest(family=name, request=request):
                    self.assertEqual(steps, answer)

    def test_payment_order_is_pinned(self):
        # Legacy pays the buyback before the recipient, a v2 buy after it, and
        # the creator is paid before the curve in both.
        order = lambda t, a, b: t.index(a) < t.index(b)
        legacy = next(s for _, s in self.rows['legacy buy'] if any('>buyback:' in x for x in s) and any('>recipient:' in x for x in s))
        v2 = next(s for _, s in self.rows['v2 buy'] if any('>buyback:' in x for x in s) and any('>recipient:' in x for x in s))
        for steps, first in ((legacy, 'buyback'), (v2, 'recipient')):
            at = {key: next(x for x in steps if f'>{key}:' in x) for key in ('curve', 'recipient', 'buyback')}
            self.assertTrue(order(steps, at['curve'], at[first]))
            self.assertTrue(order(steps, at[first], at['recipient' if first == 'buyback' else 'buyback']))

    def test_checker_sees_a_swapped_pair(self):
        rows = self.rows['legacy buy']
        request, steps = next(r for r in rows if len(r[1]) >= 4)
        swapped = steps[:]
        swapped[2], swapped[3] = swapped[3], swapped[2]
        self.assertEqual(self.model([(request, steps)]), [steps])
        self.assertNotEqual(self.model([(request, steps)]), [swapped])

    def test_case_count(self):
        self.assertGreaterEqual(sum(len(r) for r in self.rows.values()), 300)


if __name__ == '__main__':
    unittest.main()
