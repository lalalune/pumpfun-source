"""Captured-program checks for PumpSwap LP `deposit` and `withdraw`.

Each case builds a synthetic pool, global config, mints and token accounts,
runs the instruction on `evidence/original/pump_amm/deployed.so` in LiteSVM
(with the captured SPL Token and Token-2022 programs), and feeds the same
bytes to `programs/pump-amm/recovered/liquidity_host.rs`. Owners, the user
signature, writable flags and the pool-signer classification are worked out
here. The error, the committed account bytes, the logged event and the token
and event CPIs must agree, and failed calls must roll the accounts back. This
is matching behaviour on these inputs only, not a byte-identity claim.

Quote transfer fees use one amount TLV placed directly after the account-type
byte. Base mints are not fee-bearing and token accounts are not native SOL.
"""
from pathlib import Path
from unittest import mock
import hashlib
import random
import re
import struct
import subprocess
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
AMM_ELF = ROOT / 'evidence/original/pump_amm/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
AMM_SHA256 = '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7'
TOKEN_SHA256 = '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697'
TOKEN22_SHA256 = '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d'
HOST_SOURCE = ROOT / 'programs/pump-amm/recovered/liquidity_host.rs'

AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
SYSTEM = Pubkey.default()
DEPOSIT = hashlib.sha256(b'global:deposit').digest()[:8]
WITHDRAW = hashlib.sha256(b'global:withdraw').digest()[:8]
DEPOSIT_EVENT = hashlib.sha256(b'event:DepositEvent').digest()[:8]
WITHDRAW_EVENT = hashlib.sha256(b'event:WithdrawEvent').digest()[:8]
EVENT = Pubkey.find_program_address([b'__event_authority'], AMM)[0]
NOW = 1_700_000_000
PAYER = Keypair.from_seed(bytes([7]) * 32)
USER = Keypair.from_seed(bytes([8]) * 32)
CREATOR = Pubkey.from_bytes(bytes([9]) * 32)
BASE = Pubkey.from_bytes(bytes([10]) * 32)
QUOTE = Pubkey.from_bytes(bytes([11]) * 32)
INDEX = 7
POOL, BUMP = Pubkey.find_program_address(
    [b'pool', struct.pack('<H', INDEX), bytes(CREATOR), bytes(BASE), bytes(QUOTE)], AMM)
LP = Pubkey.from_bytes(bytes([12]) * 32)
UB, UQ, UL = (Pubkey.from_bytes(bytes([13 + i]) * 32) for i in range(3))
VB = Pubkey.from_bytes(bytes([16]) * 32)
VQ = Pubkey.from_bytes(bytes([17]) * 32)
CONFIG = Pubkey.from_bytes(bytes([18]) * 32)
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
OTHER = Pubkey.from_bytes(bytes([78]) * 32)
U64_MAX = 2**64 - 1


def owner_tag(owner):
    return {AMM: 1, TOKEN: 2, TOKEN22: 3}.get(owner, 0)


def token_account(mint, owner, amount, state=1, extension=False):
    data = bytearray(165)
    data[:32] = bytes(mint)
    data[32:64] = bytes(owner)
    struct.pack_into('<Q', data, 64, amount)
    data[108] = state
    if extension:
        data += bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    return bytes(data)


def mint_account(authority, supply, decimals, tag=1):
    data = bytearray(82)
    struct.pack_into('<I', data, 0, tag)
    if tag == 1:
        data[4:36] = bytes(authority)
    struct.pack_into('<Q', data, 36, supply)
    data[44] = decimals
    data[45] = 1
    return bytes(data)


def fee_mint(bps, maximum):
    data = bytearray(mint_account(SYSTEM, 10**15, 9, 0))
    data += bytes(83) + bytes([1])
    conf = bytes(72) + struct.pack('<QQH', 0, maximum, bps) * 2
    data += struct.pack('<HH', 1, len(conf)) + conf
    return bytes(data)


def pool_bytes(c):
    n = c.get('pool_len', 300)
    data = bytearray(max(n, 300))
    data[:8] = hashlib.sha256(b'account:Pool').digest()[:8]
    data[8] = c.get('bump', BUMP)
    struct.pack_into('<H', data, 9, c.get('index', INDEX))
    data[11:43] = bytes(c.get('creator', CREATOR))
    data[43:75] = bytes(c.get('base', BASE))
    data[75:107] = bytes(c.get('quote', QUOTE))
    data[107:139] = bytes(c.get('lp', LP))
    data[139:171] = bytes(c.get('vb_key', VB))
    data[171:203] = bytes(c.get('vq_key', VQ))
    struct.pack_into('<Q', data, 203, c.get('supply', 1_000_000))
    data[211:243] = bytes(c.get('coin', OTHER))
    data[243] = c.get('mayhem', 1)
    data[244] = c.get('cashback', 0)
    data[245:261] = int(c.get('virtual', 0)).to_bytes(16, 'little', signed=True)
    struct.pack_into('<Q', data, 261, c.get('creator_bps', 30))
    data[269] = c.get('edit', 1)
    data[270] = c.get('holder', 0)
    struct.pack_into('<Q', data, 271, c.get('pfee', 0))
    struct.pack_into('<Q', data, 279, c.get('cfee', 0))
    data[287:300] = bytes([0xAB]) * 13
    for at, value in c.get('pool_patches', ()):
        data[at:at + len(value)] = value
    return bytes(data[:n])


def config_bytes(c):
    n = c.get('config_len', 949)
    data = bytearray(n)
    if n >= 8:
        data[:8] = hashlib.sha256(b'account:GlobalConfig').digest()[:8]
    if n > 56:
        data[56] = c.get('flags', 0)
    for at in (417, 642, 939, 940):
        if at < n:
            data[at] = 0
    for at, value in c.get('config_patches', ()):
        if at < n:
            data[at:at + len(value)] = value
    return bytes(data)


def signer_status(pool_data, pool_key):
    raw = bytes(pool_data).ljust(107, b'\0')
    seeds = [b'pool', raw[9:11], raw[11:43], raw[43:75], raw[75:107], bytes([raw[8]])]
    try:
        derived = Pubkey.create_program_address(seeds, AMM)
    except Exception as exc:
        if type(exc).__name__ != 'PubkeyError':
            raise
        return 1
    return 0 if derived == pool_key else 2


def setup(c):
    kind = c.get('ix', 'deposit')
    fee = c.get('fee')
    supply = c.get('supply', 1_000_000)
    quote_data = fee_mint(*fee) if fee else c.get('quote_data', mint_account(SYSTEM, 10**15, c.get('quote_dec', 9), 0))
    quote_owner = TOKEN22 if fee or c.get('quote_owner') == TOKEN22 else c.get('quote_owner', TOKEN)
    base_owner = c.get('base_owner', TOKEN)
    lp_owner = c.get('lp_owner', TOKEN22)
    extend = fee is not None
    accounts = {
        POOL: Account(10**9, pool_bytes(c), c.get('pool_owner', AMM)),
        CONFIG: Account(10**9, config_bytes(c), c.get('config_owner', AMM)),
        BASE: Account(10**9, c.get('base_data', mint_account(SYSTEM, 10**15, c.get('base_dec', 6), 0)), base_owner),
        QUOTE: Account(10**9, quote_data, quote_owner),
        LP: Account(10**9, c.get('lp_data', mint_account(c.get('lp_auth', POOL), c.get('mint_supply', supply), 6, c.get('lp_tag', 1))), lp_owner),
        UB: Account(10**9, c.get('ub_data', token_account(c.get('ub_mint', BASE), c.get('ub_owner', USER.pubkey()), c.get('ub_amt', 10**12))), c.get('ub_prog', base_owner if base_owner in (TOKEN, TOKEN22) else TOKEN)),
        UQ: Account(10**9, c.get('uq_data', token_account(QUOTE, c.get('uq_owner', USER.pubkey()), c.get('uq_amt', 10**12), extension=extend)), quote_owner if quote_owner in (TOKEN, TOKEN22) else TOKEN),
        UL: Account(10**9, c.get('ul_data', token_account(LP, c.get('ul_owner', USER.pubkey()), c.get('ul_amt', supply), c.get('ul_state', 1))), c.get('ul_prog', lp_owner if lp_owner in (TOKEN, TOKEN22) else TOKEN22)),
        VB: Account(10**9, c.get('vb_data', token_account(BASE, c.get('vb_owner', POOL), c.get('vb_amt', 400_000_000))), c.get('vb_prog', base_owner if base_owner in (TOKEN, TOKEN22) else TOKEN)),
        VQ: Account(10**9, c.get('vq_data', token_account(QUOTE, c.get('vq_owner', POOL), c.get('vq_amt', 200_000_000), extension=extend)), quote_owner if quote_owner in (TOKEN, TOKEN22) else TOKEN),
    }
    order = [POOL, CONFIG, USER.pubkey(), BASE, QUOTE, LP, UB, UQ, UL, VB, VQ, TOKEN, TOKEN22, EVENT, AMM]
    if c.get('order'):
        order = list(c['order'])
    writable = {0, 5, 6, 7, 8, 9, 10}
    metas = []
    for i, key in enumerate(order):
        signer = i == 2 and not c.get('unsigned')
        write = i in writable and i not in set(c.get('readonly', ()))
        metas.append(AccountMeta(key, signer, write))
    metas = metas[:c.get('count', 15)]
    if 'replace' in c:
        index, key, signer, write, copy = c['replace']
        old = metas[index].pubkey
        if copy and old in accounts:
            accounts[key] = accounts[old]
        elif key not in accounts:
            accounts[key] = Account(10**9, b'', SYSTEM)
        metas[index] = AccountMeta(key, signer, write)
    if 'alias' in c:
        src, dst = c['alias']
        metas[src] = AccountMeta(metas[dst].pubkey, False, True)
    amount = c.get('amount', 1000)
    if kind == 'deposit':
        base_limit = c.get('base_limit', U64_MAX)
        quote_limit = c.get('quote_limit', U64_MAX)
        payload = DEPOSIT
    else:
        base_limit = c.get('base_limit', 0)
        quote_limit = c.get('quote_limit', 0)
        payload = WITHDRAW
    data = payload + struct.pack('<QQQ', amount, base_limit, quote_limit) + bytes.fromhex(c.get('trailing', ''))
    if 'raw' in c:
        data = c['raw']
    data = data[:c.get('payload', len(data))]
    signers = [USER] if any(m.pubkey == USER.pubkey() and m.is_signer for m in metas) else []
    return {'kind': kind, 'accounts': accounts, 'metas': metas, 'data': data, 'signers': signers,
            'epoch': c.get('epoch', 0)}


def host_line(c):
    built = setup(c)
    metas, accounts, data = built['metas'], built['accounts'], built['data']
    mask = 0
    for i, meta in enumerate(metas):
        if meta.is_writable:
            mask |= 1 << i

    def slot(i):
        if i >= len(metas):
            return ['0', '', '00' * 32]
        key = metas[i].pubkey
        account = accounts.get(key)
        if i == 2 or account is None:
            return ['0', '', bytes(key).hex()]
        return [str(owner_tag(account.owner)), bytes(account.data).hex(), bytes(key).hex()]

    pool_key = metas[0].pubkey if metas else SYSTEM
    pool_data = bytes(accounts[pool_key].data) if pool_key in accounts else b''
    fields = ['d' if built['kind'] == 'deposit' else 'w', data.hex(), str(len(metas)), str(mask),
              '1' if any(i == 2 and m.is_signer for i, m in enumerate(metas)) else '0',
              str(built['epoch']), str(NOW), str(signer_status(pool_data, pool_key) if metas else 1),
              '1' if len(metas) > 14 and metas[14].pubkey == AMM else '0',
              '1' if len(metas) > 13 and metas[13].pubkey == EVENT else '0',
              '1' if len(metas) > 11 and metas[11].pubkey == TOKEN else '0',
              '1' if len(metas) > 12 and metas[12].pubkey == TOKEN22 else '0']
    for i in range(11):
        fields.extend(slot(i))
    return ','.join(fields)


def parse_err(result):
    text = str(result.err())
    custom = re.search(r'InstructionErrorCustom\((\d+)\)', text)
    if custom:
        return str(int(custom.group(1)))
    named = re.search(r'Fieldless\((\w+)\)', text)
    if named:
        return named.group(1)
    return text


def cpi_text(tx, meta):
    keys = list(tx.message.account_keys)
    parts = []
    for group in meta.inner_instructions():
        for inner in group:
            ix = inner.instruction()
            pid = str(ix.program_id(keys))
            tag = {str(TOKEN): 's', str(TOKEN22): '2', str(AMM): 'a'}.get(pid, '?')
            parts.append(tag + ':' + bytes(ix.data).hex())
    return ';'.join(parts)


def run_captured(c):
    built = setup(c)
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program(AMM, AMM_ELF.read_bytes())
    vm.add_program(TOKEN, TOKEN_ELF.read_bytes())
    vm.add_program(TOKEN22, TOKEN22_ELF.read_bytes())
    clock = vm.get_clock()
    vm.set_clock(Clock(3, clock.epoch_start_timestamp, built['epoch'], clock.leader_schedule_epoch, NOW))
    vm.airdrop(PAYER.pubkey(), 10**10)
    vm.airdrop(USER.pubkey(), 10**10)
    before = {}
    for key, account in built['accounts'].items():
        vm.set_account(key, account)
        before[key] = account
    tx = Transaction.new_signed_with_payer(
        [Instruction(AMM, built['data'], built['metas'])], PAYER.pubkey(), [PAYER] + built['signers'], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    events = []
    for line in meta.logs():
        if line.startswith('Program data: '):
            import base64
            events.append(base64.b64decode(line.split('Program data: ', 1)[1]))
    after = {key: vm.get_account(key) for key in before}
    same = all(bytes(after[key].data) == bytes(before[key].data) for key in before)
    meta_same = all(
        (after[key].lamports, after[key].owner, after[key].executable) == (before[key].lamports, before[key].owner, before[key].executable)
        for key in before)
    return {'error': parse_err(result) if failed else None, 'events': events, 'cpi': cpi_text(tx, meta),
            'before': before, 'after': after, 'same': same, 'meta_same': meta_same, 'metas': built['metas']}


class PumpAmmLiquidityCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        images = [(AMM_ELF, AMM_SHA256), (TOKEN_ELF, TOKEN_SHA256), (TOKEN22_ELF, TOKEN22_SHA256)]
        for path, digest in images:
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('captured program hash mismatch')
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'liquidity-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(c) + '\n' for c in cases)
        answers = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(len(answers), len(cases), answers[:3])
        return answers

    def assert_matches(self, answer, captured):
        self.assertTrue(captured['meta_same'])
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], answer[6:])
            self.assertEqual(captured['events'], [])
            self.assertTrue(captured['same'])
            return
        if answer.startswith('event-then:'):
            name, event, cpi = answer[len('event-then:'):].split(',', 2)
            self.assertEqual(captured['error'], name)
            self.assertEqual(captured['events'], [bytes.fromhex(event)])
            self.assertEqual(captured['cpi'], cpi)
            self.assertTrue(captured['same'])
            return
        parts = answer.split(',')
        self.assertEqual(parts[0], 'ok')
        self.assertIsNone(captured['error'])
        pool, ub, uq, ul, vb, vq, lp, event, cpi = parts[1:]
        metas = captured['metas']
        expect = {}
        for index, blob in ((0, pool), (6, ub), (7, uq), (8, ul), (9, vb), (10, vq), (5, lp)):
            if index < len(metas):
                expect.setdefault(metas[index].pubkey, bytes.fromhex(blob))
        for key, before in captured['before'].items():
            after = captured['after'][key]
            if key in expect:
                self.assertEqual(bytes(after.data), expect[key])
            else:
                self.assertEqual(bytes(after.data), bytes(before.data))
        self.assertEqual(captured['events'], [bytes.fromhex(event)])
        self.assertEqual(captured['cpi'], cpi)

    def run_cases(self, cases):
        for case, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=repr(case)[:240], host=answer[:80]):
                self.assert_matches(answer, run_captured(case))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_delegated_transfers_match_captured_program(self):
        def delegated(mint, owner, allowance, delegate=USER.pubkey(), amount=10**12, extension=False):
            data = bytearray(token_account(mint, owner, amount, extension=extension))
            struct.pack_into('<I', data, 72, 1)
            data[76:108] = bytes(delegate)
            struct.pack_into('<Q', data, 121, allowance)
            return bytes(data)

        cases = []
        for program in (TOKEN, TOKEN22):
            for allowance in (0, 399_999, 400_000, 400_001):
                cases.append({'base_owner': program, 'ub_data': delegated(BASE, OTHER, allowance)})
            # A matching delegate takes precedence even when it is also owner.
            for allowance in (0, 400_000, 400_001):
                cases.append({'base_owner': program, 'ub_data': delegated(BASE, USER.pubkey(), allowance)})
            cases.append({'base_owner': program, 'ub_data': delegated(BASE, USER.pubkey(), 400_000, OTHER)})
            cases.append({'base_owner': program, 'ub_data': delegated(BASE, CREATOR, 400_000, OTHER)})
        for allowance in (202_020, 202_021, 202_022):
            cases.append({'fee': (100, 10**9), 'uq_data': delegated(QUOTE, OTHER, allowance, extension=True)})
        cases += [{'ub_amt': 1, 'ub_mint': OTHER}, {'ub_amt': 1, 'ub_owner': OTHER},
                  {'ub_data': delegated(BASE, OTHER, 400_000, amount=1)}]
        self.run_cases(cases)

    def test_captured_image_identity_is_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            wrong = Path(temporary) / 'wrong.so'
            wrong.write_bytes(AMM_ELF.read_bytes() + b'wrong capture')
            with mock.patch.dict(globals(), AMM_ELF=wrong):
                with self.assertRaisesRegex(ValueError, 'captured program hash mismatch'):
                    type(self).setUpClass()

    def test_checker_rejects_tampered_outcomes(self):
        samples = ({}, {'ix': 'withdraw'}, {'pool_len': 250}, {'program_key': True}, {'flags': 2}, {'fee': (100, 10**9)})
        # program_key is expressed as replace below; keep samples the model can run.
        samples = ({}, {'ix': 'withdraw'}, {'pool_len': 250}, {'flags': 2}, {'fee': (100, 10**9), 'amount': 10_000},
                   {'bump': (BUMP + 1) & 255})
        flip = lambda text, i: text[:2 * i] + format(int(text[2 * i:2 * i + 2], 16) ^ 1, '02x') + text[2 * i + 2:]
        for case, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(case)
            self.assert_matches(answer, captured)
            with self.assertRaises(AssertionError):
                self.assert_matches(answer, dict(captured, meta_same=False))
            if answer.startswith('ok,'):
                parts = answer.split(',')
                tampered = ['ok,' + flip(parts[1], 203) + ',' + ','.join(parts[2:]),
                            'ok,' + ','.join(parts[1:8]) + ',' + flip(parts[8], 0) + ',' + parts[9],
                            'error:6004']
            elif answer.startswith('event-then:'):
                name, event, cpi = answer[len('event-then:'):].split(',', 2)
                tampered = [f'event-then:{name},{flip(event, 0)},{cpi}', f'error:{name}', f'event-then:MissingAccount,{event},{cpi}']
            else:
                tampered = ['error:6004' if answer != 'error:6004' else 'error:6018', 'error:BorshIoError']
            for text in tampered:
                with self.subTest(case=repr(case), tampered=text[:50]):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        errors = {a for a in answers if a.startswith('error:')}
        for code in ('101', '102', '2000', '2006', '2015', '3005', '3007', '3008', '3010', '6004', '6007', '6008',
                     '6018', '6019', '6023', '6024', '6025', '6067', '6087', '1', '3', '4', '5', '13'):
            self.assertIn('error:' + code, errors)
        for name in ('InvalidAccountData', 'BorshIoError', 'ProgramFailedToComplete', 'IncorrectProgramId', 'PrivilegeEscalation'):
            self.assertIn('error:' + name, errors)
        kinds = {a.split(',')[0] for a in answers if a.startswith('event-then:')}
        self.assertEqual(kinds, {'event-then:MissingAccount', 'event-then:BorshIoError'})
        events = {bytes.fromhex(a.split(',')[8])[:8] for a in answers if a.startswith('ok,')}
        self.assertEqual(events, {DEPOSIT_EVENT, WITHDRAW_EVENT})
        self.assertGreater(sum(a.startswith('ok,') for a in answers), 15)


def fixed_cases():
    stray_order = [POOL, CONFIG, USER.pubkey(), BASE, QUOTE, LP, UB, UQ, UL, VB, VQ, TOKEN, TOKEN22, EVENT, AMM, STRAY]
    cases = [{}, {'ix': 'withdraw'}, {'trailing': 'ff'}, {'amount': 0}, {'ix': 'withdraw', 'amount': 0}, {'count': 16, 'order': stray_order}]
    cases += [{'payload': n} for n in (0, 7, 8, 24, 31)]
    cases += [{'raw': bytes([9]) * 32}]
    cases += [{'count': n} for n in range(15)]
    cases += [{'unsigned': True}, {'ix': 'withdraw', 'unsigned': True}]
    cases += [{'readonly': (i,)} for i in (0, 5, 6, 7, 8, 9, 10)]
    cases += [{'flags': n} for n in (0, 1, 2, 4, 6, 255)]
    cases += [{'ix': 'withdraw', 'flags': n} for n in (2, 4, 6)]
    cases += [{'pool_patches': [(0, bytes(8))]}]
    cases += [{'pool_len': n} for n in (200, 211, 243, 244, 260, 261, 270, 286, 287, 300)]
    cases += [{'pool_patches': [(243, bytes([2]))]}, {'pool_patches': [(269, bytes([2]))]}]
    cases += [{'config_len': n} for n in (56, 906, 907, 939, 940, 949)]
    cases += [{'config_patches': [(417, bytes([2]))]}, {'config_len': 940, 'config_patches': [(939, bytes([2]))]}]
    cases += [{'base_limit': n} for n in (399_999, 400_000)]
    cases += [{'quote_limit': n} for n in (199_999, 200_000)]
    cases += [{'ix': 'withdraw', 'base_limit': n} for n in (400_000, 400_001)]
    cases += [{'ix': 'withdraw', 'quote_limit': n} for n in (200_000, 200_001)]
    cases += [{'supply': 0, 'mint_supply': 0, 'ul_amt': 0}, {'ix': 'withdraw', 'supply': 0, 'mint_supply': 0, 'ul_amt': 0}]
    cases += [{'ix': 'withdraw', 'supply': 100, 'mint_supply': 101, 'ul_amt': 101},
              {'ix': 'withdraw', 'supply': 100, 'mint_supply': 100, 'ul_amt': 100, 'amount': 1}]
    cases += [{'supply': 3, 'mint_supply': 3, 'ul_amt': 3, 'vb_amt': 10, 'vq_amt': 10, 'amount': 2},
              {'ix': 'withdraw', 'supply': 3, 'mint_supply': 3, 'ul_amt': 3, 'vb_amt': 10, 'vq_amt': 10, 'amount': 2}]
    cases += [{'virtual': 1_000_000_000}, {'ix': 'withdraw', 'virtual': 1_000_000_000}, {'virtual': -50_000},
              {'pfee': 1000, 'cfee': 2000, 'amount': 10_000}, {'ix': 'withdraw', 'pfee': 1000, 'cfee': 2000, 'amount': 10_000},
              {'virtual': -3000, 'pfee': 3000}, {'virtual': -2999, 'pfee': 3000}]
    cases += [{'fee': fee, 'amount': amount} for fee, amount in (((100, 10**9), 10_000), ((0, 10**9), 1000), ((10000, 10**9), 100), ((5000, 5), 1000))]
    cases += [{'ix': 'withdraw', 'fee': (100, 10**9), 'amount': 10_000}]
    cases += [{'quote_data': mint_account(SYSTEM, 1, 9, 0) + bytes(83) + bytes([1, 9, 9, 9, 9]), 'quote_owner': TOKEN22}]
    cases += [{'fee': (100, 10**9), 'uq_data': token_account(QUOTE, USER.pubkey(), 10**12), 'vq_data': token_account(QUOTE, POOL, 200_000_000)}]
    cases += [{'alias': (6, 9)}, {'alias': (7, 10)}, {'ix': 'withdraw', 'alias': (6, 9)}]
    cases += [{'bump': (BUMP + 1) & 255}, {'bump': (BUMP + 1) & 255, 'amount': 0},
              {'ix': 'withdraw', 'bump': (BUMP + 1) & 255}, {'ix': 'withdraw', 'bump': (BUMP + 1) & 255, 'amount': 0}]
    cases += [{'replace': (0, STRAY, False, True, True)}, {'lp_tag': 0}, {'lp_auth': OTHER},
              {'ub_amt': 10}, {'ix': 'withdraw', 'ul_amt': 10}, {'ul_owner': STRAY},
              {'ub_mint': QUOTE}, {'pool_owner': SYSTEM}, {'base_owner': SYSTEM},
              {'replace': (13, STRAY, False, False, False)}, {'replace': (11, STRAY, False, False, False)},
              {'replace': (14, STRAY, False, False, False)}, {'replace': (3, STRAY, False, False, True)},
              {'base': OTHER}]
    cases += [{'supply': 2, 'mint_supply': 0, 'ul_amt': 0, 'vb_amt': 0, 'vq_amt': 0, 'amount': U64_MAX - 1, 'pfee': 0}]
    cases += [{'pool_len': 211, 'flags': 2}, {'readonly': (0,), 'base': OTHER}, {'unsigned': True, 'base': OTHER}]
    cases += [{'base_owner': TOKEN22}, {'quote_owner': TOKEN22}, {'lp_owner': TOKEN}]
    cases += [{'ub_data': token_account(BASE, USER.pubkey(), 10**12, state=0)}]
    cases += [{'amount': U64_MAX, 'supply': 2, 'mint_supply': 2, 'ul_amt': 2}]
    return cases


def random_cases():
    rng = random.Random(20261030)
    cases = []
    for _ in range(40):
        kind = rng.choice(('deposit', 'withdraw'))
        amount = rng.choice((0, 1, 2, 1000, 10_000, 50_000))
        case = {'ix': kind, 'amount': amount, 'supply': rng.choice((3, 1000, 1_000_000)),
                'virtual': rng.choice((0, 0, 1_000_000, -1_000, 2**40)),
                'pfee': rng.choice((0, 0, 1_000)), 'cfee': rng.choice((0, 500))}
        case['mint_supply'] = case['supply']
        case['ul_amt'] = case['supply']
        case['vb_amt'] = rng.choice((10, 400_000_000))
        case['vq_amt'] = rng.choice((10, 200_000_000))
        if rng.random() < 0.25:
            case['fee'] = (rng.choice((0, 100, 250)), 10**9)
        if kind == 'deposit':
            case['base_limit'] = U64_MAX
            case['quote_limit'] = U64_MAX
        cases.append(case)
    return cases


if __name__ == '__main__':
    unittest.main()
