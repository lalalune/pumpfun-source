"""Captured-program checks for the whitelisted user of `sell_v2`, `buy_v2` and `buy_exact_quote_in_v2` on SOL.

Every case runs on the captured `evidence/original/pump/deployed.so` with the
captured Pump Fees, SPL Token and ATA programs and through
`programs/pump/recovered/v2_whitelist_native_host.rs`. State is synthetic.

A case passes when the captured program and the model agree on the error and committed-state rollback (apart from the transaction fee), or on
the lamports of the user and the curve, the base balances, the stored curve bytes
and the reserve and amount fields of the TradeEvent. This pins observed behavior
on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import json
import random
import re
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
FEES_ELF = ROOT / 'evidence/original/pump_fees/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    FEES_ELF: '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/v2_whitelist_native_host.rs'

_PROGRAM_BYTES = None


def admit_program_images(expected):
    images = {}
    for path, digest in expected.items():
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f'captured program hash mismatch: {path}')
        images[path] = raw
    return images


def program_images():
    global _PROGRAM_BYTES
    if _PROGRAM_BYTES is None:
        _PROGRAM_BYTES = admit_program_images(ELF_SHA256)
    return _PROGRAM_BYTES


def parse_model_output(text, count):
    lines = text.splitlines()
    if len(lines) != count:
        raise ValueError(f'model returned {len(lines)} answers for {count} cases')
    answers = []
    for line in lines:
        if line.startswith('error:'):
            answers.append(('error', int(line[6:])))
        elif line in ('panic', 'invalid-account-data'):
            answers.append(('error', line))
        elif line.startswith('ok '):
            fields = [word.split('=', 1) for word in line.split()[1:]]
            if any(len(field) != 2 for field in fields) or len({field[0] for field in fields}) != len(fields):
                raise ValueError('malformed or duplicate model answer field')
            answers.append(('ok', {key: int(value) for key, value in fields}))
        else:
            raise ValueError('unknown model answer: ' + line)
    return answers


def rollback_differences(before, after):
    expected = dict(before)
    payer = before[USER.pubkey()]
    if payer is not None:
        expected[USER.pubkey()] = (payer[0] - TX_FEE, *payer[1:])
    return [] if after == expected else ['failed transaction changed state beyond transaction fee']

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
IX = {ix['name']: ix for ix in IDL['instructions']}
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
TRADE_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'TradeEvent'))

PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()

USER = Keypair.from_seed(bytes([241]) * 32)
CREATOR = Pubkey.from_bytes(bytes([242]) * 32)
MINT = Pubkey.from_bytes(bytes([243]) * 32)
FEE_RECIPIENT = Pubkey.from_bytes(bytes([244]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([245]) * 32)
RESERVED = Pubkey.from_bytes(bytes([246]) * 32)
OTHER = Pubkey.from_bytes(bytes([247]) * 32)

pda = lambda program, *seeds: Pubkey.find_program_address(list(seeds), program)[0]
ata = lambda owner, mint=MINT: pda(ATA, bytes(owner), bytes(TOKEN), bytes(mint))
GLOBAL = pda(PUMP, b'global')
CURVE = pda(PUMP, b'bonding-curve', bytes(MINT))
EVENT_AUTHORITY = pda(PUMP, b'__event_authority')
GLOBAL_VOLUME = pda(PUMP, b'global_volume_accumulator')
USER_VOLUME = pda(PUMP, b'user_volume_accumulator', bytes(USER.pubkey()))
FEE_CONFIG, FEE_BUMP = Pubkey.find_program_address([b'fee_config', bytes(PUMP)], FEES)
SHARING = pda(FEES, b'sharing-config', bytes(MINT))
VAULT = pda(PUMP, b'creator-vault', bytes(CREATOR))

TX_FEE = 5_000
TIMESTAMP = 1_700_000_000
TOKEN_RENT = 2_039_280
CURVE_RENT = (166 + 128) * 6960
U64 = 2**64 - 1
OPS = ('sell', 'buy', 'exact')
IX_NAME = {'sell': 'sell_v2', 'buy': 'buy_v2', 'exact': 'buy_exact_quote_in_v2'}


def mint_bytes(supply, decimals):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', supply) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token_bytes(owner, amount):
    return (bytes(MINT) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def global_bytes():
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    data[41:73] = bytes(FEE_RECIPIENT)
    data[451:483] = bytes(USER.pubkey())
    data[483:515] = bytes(RESERVED)
    data[741:773] = bytes(BUYBACK)
    struct.pack_into('<Q', data, 1046, 10_000)
    return bytes(data)


def curve_bytes(c):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<5Q', data, 8, c['vtr'], c['vqr'], c['rtr'], c['rqr'], c['supply'])
    data[48] = c['complete']
    data[49:81] = bytes(CREATOR)
    data[81] = c['mayhem']
    struct.pack_into('<Q', data, 142, c['vqr'])
    return bytes(data)


def default_case(**over):
    c = dict(op='sell', amount=None, limit=None, partial=0, vtr=10**15, vqr=30_000_000_000, rtr=793_100_000_000_000,
             rqr=5_000_000_000, supply=2 * 10**15, complete=0, mayhem=1, user_base=10**13, curve_base=10**15,
             fee_recipient_ok=1, buyback_ok=1)
    c.update(over)
    if c['amount'] is None:
        c['amount'] = 10**8 if c['op'] == 'exact' else 10**12
    if c['limit'] is None:
        c['limit'] = {'sell': 0, 'buy': 10**15, 'exact': 1}[c['op']]
    return c


def host_line(c):
    return ' '.join(f'{k}={v}' for k, v in c.items())


_HOST = None


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'v2_whitelist_native_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def model(cases):
    text = ''.join(host_line(c) + '\n' for c in cases)
    out = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    return parse_model_output('\n'.join(out), len(cases))


_VM = None


def vm_for(c):
    global _VM
    if _VM is None:
        _VM = LiteSVM().with_sigverify(True).with_transaction_history(0)
        for key, path in ((PUMP, PUMP_ELF), (FEES, FEES_ELF), (TOKEN, TOKEN_ELF), (ATA, ATA_ELF)):
            _VM.add_program(key, program_images()[path])
        _VM.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    user = USER.pubkey()
    accounts = {
        user: Account(10**16, b'', SYSTEM),
        GLOBAL: Account(10**9, global_bytes(), PUMP),
        MINT: Account(10**9, mint_bytes(10**15, 6), TOKEN),
        WSOL: Account(10**9, mint_bytes(0, 9), TOKEN),
        CURVE: Account(CURVE_RENT + c['rqr'] % 10**15, curve_bytes(c), PUMP),
        ata(CURVE): Account(TOKEN_RENT, token_bytes(CURVE, c['curve_base']), TOKEN),
        ata(user): Account(TOKEN_RENT, token_bytes(user, c['user_base']), TOKEN),
        FEE_CONFIG: Account(10**9, (ACCOUNT_DISC['FeeConfig'] + bytes([FEE_BUMP])).ljust(4104, b'\0'), FEES),
        GLOBAL_VOLUME: Account(10**9, ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), PUMP),
        USER_VOLUME: Account(10**9, ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(user) + bytes(97), PUMP),
    }
    for key, account in accounts.items():
        _VM.set_account(key, account)
    return _VM


def run_captured(c):
    vm = vm_for(c)
    user = USER.pubkey()
    recipient = (RESERVED if c['mayhem'] else FEE_RECIPIENT) if c['fee_recipient_ok'] else OTHER
    buyback = BUYBACK if c['buyback_ok'] else OTHER
    names = {
        'global': GLOBAL, 'base_mint': MINT, 'quote_mint': WSOL, 'base_token_program': TOKEN,
        'quote_token_program': TOKEN, 'associated_token_program': ATA, 'fee_recipient': recipient,
        'associated_quote_fee_recipient': ata(recipient, WSOL), 'buyback_fee_recipient': buyback,
        'associated_quote_buyback_fee_recipient': ata(buyback, WSOL), 'bonding_curve': CURVE,
        'associated_base_bonding_curve': ata(CURVE), 'associated_quote_bonding_curve': ata(CURVE, WSOL),
        'user': user, 'associated_base_user': ata(user), 'associated_quote_user': ata(user, WSOL),
        'creator_vault': VAULT, 'associated_creator_vault': ata(VAULT, WSOL), 'sharing_config': SHARING,
        'global_volume_accumulator': GLOBAL_VOLUME, 'user_volume_accumulator': USER_VOLUME,
        'associated_user_volume_accumulator': ata(USER_VOLUME, WSOL), 'fee_config': FEE_CONFIG,
        'fee_program': FEES, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
    }
    ix = IX[IX_NAME[c['op']]]
    metas = [AccountMeta(names[a['name']], bool(a.get('signer')), bool(a.get('writable'))) for a in ix['accounts']]
    data = bytes(ix['discriminator']) + struct.pack('<QQ', c['amount'], c['limit'])
    if c['op'] != 'sell':
        data += bytes([c['partial']])
    lamports = lambda key: vm.get_account(key).lamports
    watched = sorted({user, *(meta.pubkey for meta in metas)}, key=bytes)
    def snap():
        result = {}
        for key in watched:
            account = vm.get_account(key)
            if account is None or account.lamports == 0:
                result[key] = None
            elif not account.executable:
                result[key] = (account.lamports, bytes(account.data), account.owner)
        return result
    before_state = snap()
    before = (lamports(user), lamports(CURVE))
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, data, metas)], user, [USER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return dict(error=int(code.group(1)) if code else text, before=before_state, after=snap())
    tokens = lambda key: struct.unpack_from('<Q', vm.get_account(key).data, 64)[0]
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    trade = next(e for e in events if e[:8] == TRADE_EVENT)
    return dict(error=None, before=before_state, after=snap(), user=lamports(user) - before[0], curve=lamports(CURVE) - before[1], stored=bytes(vm.get_account(CURVE).data),
                user_base=tokens(ata(user)), curve_base=tokens(ata(CURVE)),
                event=struct.unpack_from('<QQ', trade, 40) + struct.unpack_from('<4Q', trade, 97))


def check(c, got, answer):
    kind, m = answer
    if kind == 'error':
        bad = [] if got['error'] == m else [f"error {got['error']!r} != {m}"]
        return bad + rollback_differences(got['before'], got['after'])
    if got['error'] is not None:
        return [f"captured failed with {got['error']!r}"]
    bad = []
    sell = c['op'] == 'sell'
    quote, base = (m['quote'], -m['base_moved']) if sell else (-m['quote'], m['base_moved'])
    if got['user'] != quote - TX_FEE or got['curve'] != -quote:
        bad.append(f"lamports {got['user']} {got['curve']}")
    if (got['user_base'], got['curve_base']) != (c['user_base'] + base, c['curve_base'] - base):
        bad.append('base balances')
    curve = bytearray(curve_bytes(c))
    struct.pack_into('<4Q', curve, 8, m['vtr'], m['vqr'], m['rtr'], m['rqr'])
    curve[48] = m['completes']
    if got['stored'] != bytes(curve):
        bad.append('curve bytes')
    if got['event'] != (m['quote'], m['base_moved'], m['vqr'], m['vtr'], m['rqr'], m['rtr']):
        bad.append(f"event {got['event']}")
    return bad


def fixed_cases():
    out = []
    add = lambda label, **k: out.append((label, default_case(**k)))
    for op in OPS:
        add(f'{op}-resync', op=op)
        add(f'{op}-not-mayhem', op=op, mayhem=0)
        add(f'{op}-bad-recipient', op=op, fee_recipient_ok=0)
        add(f'{op}-bad-buyback', op=op, buyback_ok=0)
        add(f'{op}-both-recipients', op=op, fee_recipient_ok=0, buyback_ok=0)
        add(f'{op}-complete', op=op, complete=1)
        add(f'{op}-complete-recipient', op=op, complete=1, fee_recipient_ok=0)
        add(f'{op}-zero', op=op, amount=0)
        add(f'{op}-zero-recipient', op=op, amount=0, fee_recipient_ok=0)
        add(f'{op}-no-supply', op=op, supply=0)
        add(f'{op}-huge-supply', op=op, supply=U64)
        add(f'{op}-cap', op=op, rqr=3 * 10**12)
        add(f'{op}-under-cap', op=op, rqr=10**12)
        small = 10**5 if op == 'exact' else 10**8
        moved = model([default_case(op=op, amount=small)])[0][1]['quote']
        for real in (9_999_999, 10_000_000):
            add(f'{op}-real-{real}', op=op, amount=small, rqr=real + (moved if op == 'sell' else -moved))
        for gap in (-1, 0, 1):
            add(f'{op}-denominator{gap}', op=op, supply=10**15, curve_base=2 * 10**15 - 10**12 - gap - 10**13)
        add(f'{op}-conversion', op=op, supply=10**15, rqr=2**62, curve_base=2 * 10**15 - 10**12 - 10**13)
    add('sell-too-many', amount=10**13 + 1)
    add('sell-too-many-recipient', amount=10**13 + 1, fee_recipient_ok=0)
    add('sell-over-real-quote', amount=10**14, rqr=1_000)
    add('sell-limit-exact', limit=29_970_029)
    add('sell-limit-short', limit=29_970_030)
    add('sell-vtr-zero', vtr=0, vqr=10**10)
    add('buy-limit-exact', op='buy', limit=30_030_031)
    add('buy-limit-short', op='buy', limit=30_030_030)
    add('buy-over-real', op='buy', amount=10**13, rtr=10**12)
    add('buy-over-real-recipient', op='buy', amount=10**13, rtr=10**12, fee_recipient_ok=0)
    add('buy-partial', op='buy', partial=1, amount=10**13, rtr=10**12)
    add('buy-partial-zero', op='buy', partial=1, rtr=0)
    add('buy-completes', op='buy', amount=10**12, rtr=10**12)
    add('buy-completes-not-mayhem', op='buy', amount=10**12, rtr=10**12, mayhem=0)
    add('buy-vtr-equals-amount', op='buy', vtr=10**12, rtr=10**12)
    add('buy-vtr-below-amount', op='buy', vtr=10**11, rtr=10**12)
    add('exact-over-real', op='exact', amount=10**10, rtr=10**12)
    add('exact-partial', op='exact', partial=1, amount=10**10, rtr=10**12)
    add('exact-partial-completes', op='exact', partial=1, amount=10**10, rtr=10**12, mayhem=0)
    add('exact-dust', op='exact', amount=1, limit=1)
    add('exact-two', op='exact', amount=2)
    add('exact-limit-zero', op='exact', limit=0)
    add('exact-both-zero', op='exact', limit=0, amount=0)
    add('exact-limit-high', op='exact', limit=U64)
    return out


def random_cases(n=120, seed=20261030):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        op = rng.choice(OPS)
        vtr = rng.randrange(10**12, 2 * 10**15)
        rtr = rng.randrange(1, vtr)
        amount = rng.choice([rng.randrange(1, 10**13), rng.randrange(1, 10**6), rng.randrange(1, 10**10)])
        c = default_case(op=op, amount=amount, vtr=vtr, vqr=rng.randrange(10**8, 10**12), rtr=rtr, partial=rng.randrange(2),
                         rqr=rng.randrange(0, 10**13), supply=rng.randrange(5 * 10**14, 2 * 10**15), mayhem=int(rng.random() < .8),
                         user_base=rng.choice([10**13, amount, max(0, amount - 1), 10**15]))
        c['curve_base'] = rng.randrange(max(amount, rtr), 2 * 10**15)
        kind, ans = model([c])[0]
        if kind == 'ok':
            if op == 'sell':
                c['limit'] = rng.choice([0, ans['quote'], ans['quote'] + 1])
            elif op == 'buy':
                c['limit'] = rng.choice([U64, ans['quote'], ans['quote'] - 1])
            else:
                c['limit'] = rng.choice([1, ans['base_moved'], ans['base_moved'] + 1])
        out.append((f'random-{len(out)}', c))
    return out


class V2WhitelistNativeCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        program_images()

    def run_all(self, labelled):
        answers = model([c for _, c in labelled])
        results = []
        for (label, c), answer in zip(labelled, answers, strict=True):
            with self.subTest(label):
                self.assertEqual(check(c, run_captured(c), answer), [], label)
            results.append(answer)
        return results

    def test_fixed_cases(self):
        results = self.run_all(fixed_cases())
        outcomes = {a[1] if a[0] == 'error' else a[0] for a in results}
        for want in ('ok', 4102, 6000, 6002, 6003, 6005, 6020, 6021, 6022, 6023, 6024, 6026, 6041, 6042, 6057):
            self.assertIn(want, outcomes)
        self.assertTrue(any(a[0] == 'ok' and a[1]['completes'] for a in results))

    def test_random_cases(self):
        self.assertGreaterEqual(sum(a[0] == 'ok' for a in self.run_all(random_cases())), 30)

    def test_checker_rejects_tampered_outcomes(self):
        for op in OPS:
            c = default_case(op=op)
            answer = model([c])[0]
            got = run_captured(c)
            self.assertEqual(check(c, got, answer), [])
            for field in answer[1]:
                self.assertNotEqual(check(c, got, ('ok', dict(answer[1], **{field: answer[1][field] + 1}))), [], field)
            self.assertNotEqual(check(c, got, ('error', 6024)), [])


    def test_model_response_count_and_format_are_strict(self):
        case = default_case()
        raw = subprocess.run([str(host_binary())], input=host_line(case) + '\n', capture_output=True,
                             text=True, check=True).stdout
        self.assertEqual(len(parse_model_output(raw, 1)), 1)
        for output in ('', raw + raw, 'unexpected field=1\n', 'ok field=1 field=2\n'):
            with self.subTest(output=output):
                with self.assertRaises(ValueError):
                    parse_model_output(output, 1)
        with patch.dict(globals(), {'model': lambda cases: []}):
            with self.assertRaises(ValueError):
                self.run_all([('missing-response', case)])

    def test_captured_bytes_remain_pinned_after_path_replacement(self):
        with tempfile.TemporaryDirectory(prefix='pinned-v2-model-') as temporary:
            image = Path(temporary) / 'pump.so'
            image.write_bytes(PUMP_ELF.read_bytes())
            expected = {path: digest for path, digest in ELF_SHA256.items() if path != PUMP_ELF}
            expected[image] = ELF_SHA256[PUMP_ELF]
            images = admit_program_images(expected)
            image.write_bytes(b'replaced after admission')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                admit_program_images(expected)
            changes = {'PUMP_ELF': image, '_PROGRAM_BYTES': images, '_VM': None}
            if '_TOUCHED' in globals():
                changes['_TOUCHED'] = set()
            with patch.dict(globals(), changes):
                case = default_case()
                self.assertEqual(check(case, run_captured(case), model([case])[0]), [])

    def test_error_checker_rejects_committed_state_mutation(self):
        case = default_case(complete=1)
        answer = model([case])[0]
        self.assertEqual(answer, ('error', 6005))
        got = run_captured(case)
        self.assertEqual(check(case, got, answer), [])
        changed = dict(got)
        changed['after'] = dict(got['after'])
        lamports, data, owner = changed['after'][CURVE]
        changed['after'][CURVE] = (lamports, bytes([data[0] ^ 1]) + data[1:], owner)
        self.assertNotEqual(check(case, changed, answer), [])



if __name__ == '__main__':
    unittest.main()
