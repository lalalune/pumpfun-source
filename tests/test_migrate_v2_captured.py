"""Captured-program checks for the recovered Pump `migrate_v2` rules.

Every case runs Pump `migrate_v2` from the captured
`evidence/original/pump/deployed.so` (upgradeable loader) on LiteSVM against
synthetic Global / BondingCurve / mint / token accounts built from the IDL
layouts, for a native-SOL curve (quote mint = WSOL) and for an SPL-token
quote curve. pump_amm's program id holds a generated no-op SBPFv0 program
(sets empty return data, returns 0), so each pump_amm CPI succeeds without
side effects and its instruction bytes are read back from the inner
instructions; the LP mint and the pool authority's LP account that
`create_pool` would leave behind are pre-seeded. The base-token ATA of the
curve is empty in every case, because a non-zero base amount would reach
the pool-authority close with tokens that the no-op pump_amm never took.
For the same reason a token-quote case that moves quote tokens pre-creates
the pool authority's quote account (Pump then leaves it open). The same
inputs go to `programs/pump/recovered/migrate_v2_host.rs`, and the error,
the `create_pool` / `init_boost` CPIs, the CompletePumpAmmMigrationEvent,
the quote tokens taken from the curve, and the curve afterwards must agree.
This shows matching behavior on these inputs only; it is not a
byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import json
import random
import struct
import subprocess
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/migrate_v2_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
AMM_IDL = json.loads((ROOT / 'programs/pump/idls/pump_amm.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
PUMP_AMM = Pubkey.from_string(AMM_IDL['address'])
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
RENT = Pubkey.from_string('SysvarRent111111111111111111111111111111111')
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
SYSTEM = Pubkey.default()
MIGRATE = next(i for i in IDL['instructions'] if i['name'] == 'migrate_v2')
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
CONFIG_DISC = bytes(next(a['discriminator'] for a in AMM_IDL['accounts'] if a['name'] == 'GlobalConfig'))
MIGRATION_EVENT = bytes(next(e['discriminator'] for e in IDL['events']
                             if e['name'] == 'CompletePumpAmmMigrationEvent'))
AMM_IX = {i['name']: bytes(i['discriminator']) for i in AMM_IDL['instructions']}

USER = Keypair.from_seed(bytes([223]) * 32)
MINT = Pubkey.from_bytes(bytes([73]) * 32)
QUOTE = Pubkey.from_bytes(bytes([74]) * 32)
OTHER = Pubkey.from_bytes(bytes([75]) * 32)
CREATOR = Pubkey.from_bytes(bytes([62]) * 32)
WITHDRAW = Pubkey.from_bytes(bytes([63]) * 32)
STRANGER = Pubkey.from_bytes(bytes([201]) * 32)
BOOST = [Pubkey.from_bytes(bytes([91 + i]) * 32) for i in range(3)]
TS = 1_800_000_000
U64 = 2**64 - 1


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(seeds, program)[0]


def ata(owner, mint, program=TOKEN):
    return pda([bytes(owner), bytes(program), bytes(mint)], ATA)


GLOBAL = pda([b'global'])
CURVE = pda([b'bonding-curve', bytes(MINT)])
POOL_AUTHORITY = pda([b'pool-authority', bytes(MINT)])
AMM_CONFIG = pda([b'global_config'], PUMP_AMM)


def accounts(quote):
    pool = pda([b'pool', struct.pack('<H', 0), bytes(POOL_AUTHORITY), bytes(MINT), bytes(quote)], PUMP_AMM)
    lp_mint = pda([b'pool_lp_mint', bytes(pool)], PUMP_AMM)
    return {
        'global': GLOBAL, 'withdraw_authority': WITHDRAW, 'base_mint': MINT, 'quote_mint': quote,
        'bonding_curve': CURVE, 'associated_base_bonding_curve': ata(CURVE, MINT),
        'associated_quote_bonding_curve': ata(CURVE, quote), 'user': USER.pubkey(), 'system_program': SYSTEM,
        'pump_amm': PUMP_AMM, 'pool': pool, 'pool_authority': POOL_AUTHORITY,
        'pool_authority_mint_account': ata(POOL_AUTHORITY, MINT),
        'pool_authority_quote_account': ata(POOL_AUTHORITY, quote), 'amm_global_config': AMM_CONFIG,
        'lp_mint': lp_mint, 'user_pool_token_account': ata(POOL_AUTHORITY, lp_mint, TOKEN22),
        'pool_base_token_account': ata(pool, MINT), 'pool_quote_token_account': ata(pool, quote),
        'base_token_program': TOKEN, 'quote_token_program': TOKEN, 'token_2022_program': TOKEN22,
        'associated_token_program': ATA, 'pump_amm_event_authority': pda([b'__event_authority'], PUMP_AMM),
        'rent': RENT, 'event_authority': pda([b'__event_authority']), 'program': PUMP,
    }


# Host fault letter -> (account, how it is wrong); `M` passes OTHER as quote_mint.
FAULTS = {'W': ('withdraw_authority', 'key'), 'R': ('withdraw_authority', 'readonly'), 'M': ('quote_mint', 'mint'),
          'A': ('associated_quote_bonding_curve', 'key'), 'P': ('pool', 'key'),
          'O': ('pool_authority_quote_account', 'key'), 'C': ('amm_global_config', 'key'),
          'L': ('lp_mint', 'key'), 'V': ('pool_quote_token_account', 'key'),
          'E': ('pump_amm_event_authority', 'key'), 'T': ('rent', 'key')}


def insn(op, dst=0, src=0, off=0, imm=0):
    return struct.pack('<BBhi', op, dst | (src << 4), off, imm)


def noop_program():
    """SBPFv0 ELF: sol_set_return_data(r10, 0); return 0 (one R_BPF_64_32 relocation)."""
    text = insn(0xbf, 1, 10) + insn(0xb7, 2) + insn(0x85, imm=-1) + insn(0xb7) + insn(0x95)
    names = [b'', b'.text', b'.dynamic', b'.dynsym', b'.dynstr', b'.rel.dyn', b'.shstrtab']
    shstr = b'\0'.join(names) + b'\0'
    name_off = [sum(len(n) + 1 for n in names[:i]) for i in range(len(names))]
    dynstr = b'\0sol_set_return_data\0'
    dynsym = bytes(24) + struct.pack('<IBBHQQ', 1, 0x10, 0, 0, 0, 0)
    text_off = 64 + 56
    dyn_off = text_off + len(text)
    sym_off = dyn_off + 16 * 7
    str_off = sym_off + len(dynsym)
    rel_off = (str_off + len(dynstr) + 7) & ~7
    shs_off = rel_off + 16
    sh_off = (shs_off + len(shstr) + 7) & ~7
    dynamic = b''.join(struct.pack('<QQ', t, v) for t, v in [
        (17, rel_off), (18, 16), (19, 16), (6, sym_off), (5, str_off), (10, len(dynstr)), (0, 0)])
    body = b'\x7fELF' + bytes([2, 1, 1, 0]) + bytes(8)
    body += struct.pack('<HHIQQQIHHHHHH', 3, 247, 1, text_off, 64, sh_off, 0, 64, 56, 1, 64, 7, 6)
    body += struct.pack('<IIQQQQQQ', 2, 6, dyn_off, dyn_off, dyn_off, len(dynamic), len(dynamic), 8)
    body += text + dynamic + dynsym + dynstr
    body += bytes(rel_off - len(body)) + struct.pack('<QQ', text_off + 16, (1 << 32) | 10) + shstr
    body += bytes(sh_off - len(body))

    def sh(i, typ, flags, off, size, link=0, info=0, align=1, entsize=0):
        return struct.pack('<IIQQQQIIQQ', name_off[i], typ, flags, off, off, size, link, info, align, entsize)
    return (body + bytes(64) + sh(1, 1, 6, text_off, len(text), align=8)
            + sh(2, 6, 3, dyn_off, len(dynamic), link=4, align=8, entsize=16)
            + sh(3, 11, 2, sym_off, len(dynsym), link=4, info=1, align=8, entsize=24)
            + sh(4, 3, 2, str_off, len(dynstr)) + sh(5, 9, 2, rel_off, 16, link=3, align=8, entsize=16)
            + struct.pack('<IIQQQQIIQQ', name_off[6], 3, 0, 0, shs_off, len(shstr), 0, 0, 1, 0))


def mint_data(decimals=6, supply=10**15):
    return struct.pack('<I32sQBBI32s', 0, bytes(32), supply, decimals, 1, 0, bytes(32))


def token_data(mint, owner, amount, native=None):
    head = struct.pack('<32s32sQI32sB', bytes(mint), bytes(owner), amount, 0, bytes(32), 1)
    if native is None:
        return head + struct.pack('<IQQI32s', 0, 0, 0, 0, bytes(32))
    return head + struct.pack('<IQQI32s', 1, native, 0, 0, bytes(32))


def global_data(fee):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    struct.pack_into('<QQQQQ', data, 73, 1_073_000_000_000_000, 30_000_000_000, 793_100_000_000_000, 10**15, 95)
    data[113:145] = bytes(WITHDRAW)
    data[145] = 1   # enable_migrate; the handler does not read it
    struct.pack_into('<QQ', data, 146, fee, 30)
    data[450] = 1
    struct.pack_into('<Q', data, 1005, 4_000_000_000)
    return bytes(data)


def curve_data(item):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, item['vtr'], item['vqr'], item['rtr'], item['rqr'], 10**15)
    data[48] = item['complete']
    data[49:81] = bytes(CREATOR)
    data[81], data[82] = item['mayhem'], item['cashback']
    if item['quote'] == 'spl':
        data[83:115] = bytes(QUOTE)
    struct.pack_into('<Q', data, 115, item['cfb'])
    data[123], data[124] = item['can_edit'], item['holder']
    struct.pack_into('<QQ', data, 125, item['cf'], item['pf'])
    struct.pack_into('<QQ', data, 150, 0, item['pcqi'])
    return bytes(data)


def config_data(config):
    length, disc_ok, byte = config
    data = bytearray(max(length, 949))
    data[:8] = CONFIG_DISC if disc_ok else bytes(8)
    data[939] = byte
    return bytes(data[:length])


DEFAULTS = dict(faults='', quote='sol', complete=1, vtr=279_900_000_000_000, vqr=115_005_359_056, rtr=0,
                rqr=85_005_359_056, pcqi=0, fee=15_000_001, mayhem=0, cashback=0, cfb=0, can_edit=0, holder=0, cf=0, pf=0,
                config=None, remaining=0, slack=10_000_000, lamports=None, vault=None, pa_quote=0)


def case(**changes):
    unknown = set(changes) - set(DEFAULTS)
    assert not unknown, unknown
    item = dict(DEFAULTS, **changes)
    if item['quote'] == 'spl':
        if item['vault'] is None:
            # The curve's quote ATA holds exactly what the curve accounts for.
            item['vault'] = min(item['rqr'] + item['pcqi'], U64)
        if 'pa_quote' not in changes:
            # Pre-created, so the no-op pump_amm's untaken quote never reaches a close.
            item['pa_quote'] = 1
    return item


def host_line(item):
    config = '-' if item['config'] is None else ':'.join(map(str, item['config']))
    return ','.join(map(str, [item['faults'] or '-', int(item['quote'] == 'spl'), item['complete'], item['vtr'],
                              item['vqr'], item['rtr'], item['rqr'], item['pcqi'], item['fee'], item['cf'],
                              item['pf'], item['mayhem'], item['cashback'], item['cfb'], item['can_edit'],
                              item['holder'], config, item['remaining'], curve_lamports(item), item['vault'] or 0]))


def curve_lamports(item):
    if item['lamports'] is not None:
        return item['lamports']
    if item['quote'] == 'spl':
        return 1_900_000 + item['slack']
    return item['rqr'] + item['pcqi'] + item['cf'] + item['pf'] + item['slack']


def run_captured(item, index=0):
    vm = LiteSVM().with_transaction_history(0)
    programdata = pda([bytes(PUMP)], UPGRADEABLE)
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + PUMP_ELF.read_bytes(),
                                        UPGRADEABLE, False))
    vm.set_account(PUMP, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    vm.add_program(PUMP_AMM, noop_program())
    vm.set_clock(Clock(1000 + index, 0, 0, 0, TS))
    quote = QUOTE if item['quote'] == 'spl' else WSOL
    acc = accounts(quote)
    state = {GLOBAL: (10**9, PUMP, global_data(item['fee'])), USER.pubkey(): (10**12, SYSTEM, b''),
             WITHDRAW: (1_000_000, SYSTEM, b''), MINT: (1_461_600, TOKEN, mint_data()),
             WSOL: (1_461_600, TOKEN, mint_data(9, 0)), QUOTE: (1_461_600, TOKEN, mint_data()),
             OTHER: (1_461_600, TOKEN, mint_data()),
             CURVE: (curve_lamports(item), PUMP, curve_data(item)),
             acc['associated_base_bonding_curve']: (2_039_280, TOKEN, token_data(MINT, CURVE, 0)),
             acc['lp_mint']: (1_461_600, TOKEN22, mint_data(9, 0)),
             acc['user_pool_token_account']: (2_074_080, TOKEN22, token_data(acc['lp_mint'], POOL_AUTHORITY, 0))}
    if item['quote'] == 'spl':
        state[acc['associated_quote_bonding_curve']] = (2_039_280, TOKEN, token_data(QUOTE, CURVE, item['vault']))
        if item['pa_quote']:
            state[acc['pool_authority_quote_account']] = (2_039_280, TOKEN, token_data(QUOTE, POOL_AUTHORITY, 0))
    if item['config'] is not None:
        state[AMM_CONFIG] = (10**7, PUMP_AMM, config_data(item['config']))
    for key, (lamports, owner, data) in state.items():
        vm.set_account(key, Account(lamports, data, owner))
    wrong = {FAULTS[f][0] for f in item['faults'] if FAULTS[f][1] == 'key'}
    readonly = {FAULTS[f][0] for f in item['faults'] if FAULTS[f][1] == 'readonly'}
    swap = {name: STRANGER for name in wrong} | {FAULTS[f][0]: OTHER for f in item['faults'] if FAULTS[f][1] == 'mint'}
    metas = [AccountMeta(swap.get(a['name'], acc[a['name']]), a.get('signer', False),
                         a.get('writable', False) and a['name'] not in readonly) for a in MIGRATE['accounts']]
    metas += [AccountMeta(key, False, True) for key in BOOST[:item['remaining']]]
    ix = Instruction(PUMP, bytes(MIGRATE['discriminator']), metas)
    tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), ix], USER.pubkey(), [USER],
                                           vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    cpis = []
    for group in json.loads(meta.to_json())['inner_instructions'] or []:
        for inner in group:
            data = bytes(inner['instruction']['data'][1:])
            if data[:8] in (AMM_IX['create_pool'], AMM_IX['init_boost']):
                cpis.append(data)
    curve = vm.get_account(CURVE)
    vault = vm.get_account(acc['associated_quote_bonding_curve']) if item['quote'] == 'spl' else None
    return {'error': str(result.err()) if failed else None, 'cpis': cpis, 'logs': meta.logs(),
            'events': [base64.b64decode(line[14:]) for line in meta.logs() if line.startswith('Program data: ')],
            'curve': (curve.lamports, bytes(curve.data)) if curve is not None else None,
            'vault': struct.unpack_from('<Q', bytes(vault.data), 64)[0] if vault is not None else None}


def fixed_cases():
    cases = [case(), case(quote='spl')]
    add = lambda **k: cases.append(case(**k))
    zero = dict(vtr=0, vqr=0, rtr=0, rqr=0)
    boost = dict(config=(949, 1, 1))
    # Account checks, one at a time and in pairs (IDL order decides).
    for f in 'WRMAPOCLVTE':
        add(faults=f)
    for f in 'MAOE':
        add(faults=f, quote='spl')
    add(faults='WR')
    add(faults='RM')
    add(faults='MW')
    add(faults='ME')
    add(faults='TE')
    add(faults='PT', quote='spl')
    # Invalid bool first; the rent top-up overflow comes before the event
    # authority, and both before the completion gate.
    add(complete=2)
    add(complete=2, faults='W')
    add(complete=2, faults='E', quote='spl')
    add(cf=U64, pf=1, lamports=10**12)
    add(rqr=U64, cf=1, lamports=10**12)
    add(cf=U64, pf=1, faults='E', lamports=10**12)
    add(cf=U64, pf=1, complete=0, lamports=10**12)
    add(cf=U64, pf=1, faults='T', lamports=10**12)
    add(quote='spl', cf=U64, pf=1, lamports=10**12)
    add(faults='E', complete=0)
    add(complete=0)
    add(complete=0, quote='spl')
    add(complete=0, **zero)
    add(**zero)
    add(**zero, pcqi=5)
    add(**zero, quote='spl', pcqi=9)
    add(**zero, **boost)
    add(vtr=1, vqr=0, rtr=0, rqr=20_000_000)
    add(vtr=0, vqr=1, rtr=0, rqr=20_000_000)
    add(vtr=0, vqr=0, rtr=1, rqr=20_000_000)
    # Rent top-up: native reserves real_quote_reserves + creator_fee + protocol_fees.
    add(slack=0)
    add(slack=2_046_239)
    add(slack=2_046_240)
    add(slack=5, cf=7, pf=11)
    add(slack=1, cf=3)
    add(slack=0, pcqi=1)
    add(slack=0, pcqi=1_000_000)
    add(slack=0, pcqi=2_046_240)
    add(slack=0, pcqi=2_046_241)
    add(quote='spl', slack=0)
    add(quote='spl', slack=146_239)
    add(quote='spl', slack=0, cf=5, pf=6)
    add(**zero, slack=0, cf=1)
    # Native quote: real_quote_reserves + post_complete_quote_in - fee, checked;
    # the curve pays the fee, so it must cover the pool authority's account rent.
    add(pcqi=1_234_567)
    add(rqr=15_000_001)
    add(rqr=15_000_000)
    add(rqr=15_000_000, pcqi=1)
    add(rqr=0, vqr=1, fee=15_000_000)
    add(rqr=U64, pcqi=1, lamports=10**12)
    add(rqr=U64 - 30_000_000, pcqi=10, lamports=10**12)
    add(fee=8_157_120, rqr=8_157_120)
    add(fee=8_157_119, rqr=8_157_119)
    add(fee=8_157_120, rqr=8_157_120, pcqi=7)
    add(fee=0)
    add(fee=50_000_000, rqr=50_000_000, pcqi=7)
    # Token quote: the user pays the fee; the whole sum moves from the vault.
    add(quote='spl', fee=0)
    add(quote='spl', fee=10**9)
    add(quote='spl', rqr=5)
    add(quote='spl', rqr=5, vault=4)
    add(quote='spl', rqr=5, vault=9)
    add(quote='spl', rqr=0, pcqi=3, vqr=0)
    add(quote='spl', rqr=2, pcqi=3, vault=4)
    add(quote='spl', rqr=0, pcqi=0, pa_quote=0)
    add(quote='spl', rqr=U64, pcqi=1)
    add(quote='spl', rqr=U64 - 5, pcqi=5, vault=U64)
    # Creator flags go into create_pool.
    add(cashback=1, cfb=123, can_edit=1, holder=1)
    add(quote='spl', cashback=1, cfb=U64, can_edit=1, holder=1)
    add(mayhem=1)
    # Boost gate (after create_pool).
    add(**boost)
    add(**boost, quote='spl')
    add(**boost, remaining=1)
    add(**boost, remaining=2)
    add(**boost, remaining=2, quote='spl')
    add(**boost, remaining=3)
    add(remaining=2)
    add(remaining=3)
    add(config=(939, 1, 1))
    add(config=(940, 1, 1), remaining=3)
    add(config=(949, 1, 2))
    add(config=(949, 0, 1))
    add(**boost, mayhem=1)
    add(**boost, mayhem=1, remaining=2)
    return cases


def random_cases(count=40, seed=639):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        spl = rng.random() < 0.5
        fee = rng.choice([8_157_120, 15_000_001, rng.randrange(8_157_120, 10**10)])
        rqr = rng.choice([fee - 1, fee, rng.randrange(fee, 10**12)])
        pcqi = rng.choice([0, 0, rng.randrange(10**9)])
        item = dict(quote='spl' if spl else 'sol', faults=rng.choice(['', '', '', '', 'W', 'M', 'E', 'T']),
                    complete=rng.choice([1, 1, 1, 1, 0]), rqr=rqr, fee=fee, pcqi=pcqi,
                    cf=rng.choice([0, rng.randrange(10**8)]), pf=rng.choice([0, rng.randrange(10**8)]),
                    vtr=rng.choice([0, 279_900_000_000_000]), vqr=rng.choice([0, 115_005_359_056]),
                    mayhem=int(rng.random() < 0.2), cashback=rng.randrange(2), cfb=rng.randrange(10_001),
                    can_edit=rng.randrange(2), holder=rng.randrange(2),
                    config=rng.choice([None, (949, 1, 1), (949, 1, 0), (940, 0, 1)]),
                    remaining=rng.randrange(4), slack=rng.choice([2_046_240, 10_000_000, rng.randrange(10**10)]))
        if spl:
            item['vault'] = rqr + pcqi + rng.choice([0, 0, 1, rng.randrange(10**6)])
        cases.append(case(**item))
    return cases


class MigrateV2CapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'migrate-v2-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_unchanged(self, item, captured):
        self.assertEqual(captured['curve'], (curve_lamports(item), curve_data(item)))
        self.assertEqual(captured['vault'], item['vault'] if item['quote'] == 'spl' else None)
        self.assertEqual(captured['events'], [])

    def assert_matches(self, item, answer, captured):
        stops = {'borsh': 'BorshIoError', 'arith': 'ArithmeticOverflow', 'rent': 'InsufficientFundsForRent'}
        if answer in stops:
            self.assertIn(stops[answer], str(captured['error']))
            # The rent check runs after the handler, so its event is already logged.
            self.assertEqual(len(captured['events']), int(answer == 'rent'))
            return
        if answer.startswith('error:'):
            self.assertIn(f'InstructionErrorCustom({answer[6:]})', str(captured['error']))
            self.assert_unchanged(item, captured)
            # Only the boost gate fails after create_pool was sent.
            self.assertEqual(len(captured['cpis']), int(answer == 'error:6027'))
            return
        self.assertIsNone(captured['error'])
        if answer.startswith('noop,'):
            self.assertEqual(captured['cpis'], [])
            self.assertEqual(captured['events'], [])
            self.assertEqual(captured['curve'], (int(answer[5:]), curve_data(item)))
            return
        quote, mayhem, cashback, cfb, can_edit, holder, boost, lamports, vault = map(int, answer.split(',')[1:])
        create_pool = (AMM_IX['create_pool'] + struct.pack('<HQQ', 0, 0, quote) + bytes(CREATOR)
                       + struct.pack('<BBQBB', mayhem, cashback, cfb, can_edit, holder))
        self.assertEqual(captured['cpis'], [create_pool] + ([AMM_IX['init_boost']] if boost else []))
        after = bytearray(curve_data(item))
        struct.pack_into('<QQQQ', after, 8, 0, 0, 0, 0)
        self.assertEqual(captured['curve'], (lamports, bytes(after)) if lamports else None)
        self.assertEqual(captured['vault'], vault if item['quote'] == 'spl' else None)
        self.assertEqual(len(captured['events']), 1)
        event = captured['events'][0]
        self.assertEqual(event[:72], MIGRATION_EVENT + bytes(USER.pubkey()) + bytes(MINT))
        self.assertEqual(struct.unpack_from('<QQQ', event, 72), (0, quote, item['fee']))
        self.assertEqual(struct.unpack_from('<q', event, 128)[0], TS)
        self.assertEqual(event[-32:], bytes(QUOTE) if item['quote'] == 'spl' else bytes(32))

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for index, (item, answer) in enumerate(zip(cases, answers)):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, run_captured(item, index))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_shifted_quote_amount(self):
        # Negative control: a passing migration must fail once the host's quote is off by one.
        for item in (case(pcqi=1_234_567), case(quote='spl', pcqi=1_234_567)):
            answer = self.host_answers([item])[0]
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            fields = answer.split(',')
            for delta in (-1, 1):
                with self.subTest(quote=item['quote'], delta=delta), self.assertRaises(AssertionError):
                    self.assert_matches(item, ','.join([fields[0], str(int(fields[1]) + delta)] + fields[2:]),
                                        captured)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a in self.host_answers(fixed_cases())}
        self.assertEqual(outcomes, {'ok', 'noop', 'borsh', 'arith', 'rent', 'error:1', 'error:2000', 'error:2006',
                                    'error:2012', 'error:6000', 'error:6004', 'error:6006', 'error:6024',
                                    'error:6027'})


if __name__ == '__main__':
    unittest.main()
