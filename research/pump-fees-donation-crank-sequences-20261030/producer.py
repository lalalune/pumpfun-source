#!/usr/bin/env python3
"""Run pump_fees crank_donation_fee_pda sequences against two pump_fees images.

Each case is a sequence of steps on a fresh LiteSVM: account setup, state
patches, clock moves and crank transactions. The donation-relay, SPL Token and
Associated Token programs are the repository's captured dependency ELFs; only
the pump_fees image differs between the two sides. All keys come from fixed
seeds, so the output bytes depend only on the images and this file.
"""
import argparse, gzip, hashlib, json, pathlib, sys
from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

P = Pubkey.from_string
PROGRAM = P('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
RELAY = P('RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu')
TOKEN = P('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = P('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
RENT = P('SysvarRent111111111111111111111111111111111')
SYSTEM = Pubkey.default()
WSOL = P('So11111111111111111111111111111111111111112')
DEPS = {'donation_relay': RELAY, 'spl_token': TOKEN, 'associated_token': ATA}
CRANK_DISC = bytes([220, 10, 189, 167, 169, 17, 25, 69])
# IDL order of crank_donation_fee_pda accounts: (name, writable, signer).
CRANK_ACCOUNTS = [('event_authority', 0, 0), ('program', 0, 0), ('payer', 1, 1), ('system_program', 0, 0), ('token_program', 0, 0), ('associated_token_program', 0, 0), ('rent', 0, 0), ('fee_program_global', 0, 0), ('donation_fee_pda', 1, 0), ('quote_mint', 1, 0), ('donation_fee_pda_ata', 1, 0), ('donation_relay_program', 0, 0), ('donation_relay_event_authority', 0, 0), ('mint_whitelist', 0, 0), ('epoch_tracker', 1, 0), ('debouncer', 1, 0), ('debouncer_ata', 1, 0)]

def disc(name): return hashlib.sha256(b'account:' + name.encode()).digest()[:8]
def pda(seeds, prog): return Pubkey.find_program_address(seeds, prog)
def ata_of(owner, mint): return pda([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]

EVENT = pda([b'__event_authority'], PROGRAM)[0]
RELAY_EVENT = pda([b'__event_authority'], RELAY)[0]
GLOBAL, GLOBAL_BUMP = pda([b'fee-program-global'], PROGRAM)
WHITELIST, WL_BUMP = pda([b'mint_whitelist_v1'], RELAY)
TX_PAYER = Keypair.from_seed(bytes([71]) * 32)
CRANKER = Keypair.from_seed(bytes([72]) * 32)
CRANKER2 = Keypair.from_seed(bytes([73]) * 32)
GLOBAL_AUTH = Keypair.from_seed(bytes([74]) * 32)
CREATOR = Pubkey.from_bytes(bytes([75]) * 32)
BASES = {'b1': Pubkey.from_bytes(bytes([81]) * 32), 'b2': Pubkey.from_bytes(bytes([82]) * 32)}
CONFIGS = {'c1': Pubkey.from_bytes(bytes([91]) * 32), 'c2': Pubkey.from_bytes(bytes([92]) * 32)}
SPL_QUOTE = Pubkey.from_bytes(bytes([101]) * 32)
SIGNERS = {'cranker': CRANKER, 'cranker2': CRANKER2}
U64 = 2 ** 64 - 1
T0 = 1_700_000_000

def donation_key(b, c): return pda([b'donation-fee-pda', bytes(BASES[b]), bytes(CONFIGS[c])], PROGRAM)
def epoch_key(c, q): return pda([b'epoch_tracker_v1', bytes(CONFIGS[c]), bytes(q)], RELAY)[0]
def debouncer_key(c, q): return pda([b'debouncer_v1', bytes(CONFIGS[c]), bytes(q)], RELAY)[0]

def mint_data(decimals, freeze=None, supply=0):
    d = bytearray(82); d[36:44] = supply.to_bytes(8, 'little'); d[44] = decimals; d[45] = 1
    if freeze: d[46:50] = (1).to_bytes(4, 'little'); d[50:82] = bytes(freeze)
    return bytes(d)

def token_data(mint, owner, amount, native_reserve=None):
    d = bytearray(165); d[0:32] = bytes(mint); d[32:64] = bytes(owner); d[64:72] = amount.to_bytes(8, 'little'); d[108] = 1
    if native_reserve is not None: d[109:113] = (1).to_bytes(4, 'little'); d[113:121] = native_reserve.to_bytes(8, 'little')
    return bytes(d)

class Sim:
    def __init__(self, image, deps):
        self.vm = LiteSVM().with_transaction_history(0).with_log_bytes_limit(None)
        for name, key in DEPS.items(): self.vm.add_program_from_file(key, str(deps[name]))
        self.vm.add_program_from_file(PROGRAM, str(image))
        self.vm.set_clock(Clock(1000, 0, 0, 0, T0))
        self.rent218 = self.vm.minimum_balance_for_rent_exemption(218)
        self.rent165 = self.vm.minimum_balance_for_rent_exemption(165)
        for kp in [TX_PAYER, CRANKER, CRANKER2, GLOBAL_AUTH]: self.vm.set_account(kp.pubkey(), Account(10 ** 12, b'', SYSTEM))
        self.set_global(0)
        self.vm.set_account(WSOL, Account(self.vm.minimum_balance_for_rent_exemption(82), mint_data(9), TOKEN))
        self.vm.set_account(SPL_QUOTE, Account(10 ** 9, mint_data(6), TOKEN))
        self.set_whitelist([])

    def set_global(self, flags):
        d = disc('FeeProgramGlobal') + bytes([GLOBAL_BUMP]) + bytes(GLOBAL_AUTH.pubkey()) + bytes([flags]) + bytes([44]) * 32 + (123).to_bytes(8, 'little') + bytes(256)
        self.vm.set_account(GLOBAL, Account(10 ** 9, d, PROGRAM))

    def set_whitelist(self, mints):
        d = disc('MintWhitelistV1') + bytes([WL_BUMP]) + len(mints).to_bytes(4, 'little') + b''.join(bytes(m) for m in mints)
        self.vm.set_account(WHITELIST, Account(10 ** 9, d, RELAY))

    def quote(self, q): return WSOL if q == 'wsol' else SPL_QUOTE

    def donation(self, b, c, q, total=0, last=0, extra=0):
        key, bump = donation_key(b, c)
        d = disc('DonationFeePda') + bytes([bump, 1]) + bytes(CONFIGS[c]) + bytes(BASES[b]) + bytes(self.quote(q)) + bytes(CREATOR) + total.to_bytes(8, 'little') + last.to_bytes(8, 'little', signed=True) + bytes(64)
        self.vm.set_account(key, Account(self.rent218 + extra, d, PROGRAM))

    def step(self, s):
        op = s['op']
        if op == 'create': self.donation(s.get('b', 'b1'), s.get('c', 'c1'), s.get('q', 'wsol'), s.get('total', 0), s.get('last', 0), s.get('extra', 0)); return None
        if op == 'fund':  # SOL sent straight to the donation PDA
            key = donation_key(s.get('b', 'b1'), s.get('c', 'c1'))[0]; a = self.vm.get_account(key)
            self.vm.set_account(key, Account(a.lamports + s['lamports'], bytes(a.data), a.owner)); return None
        if op == 'fund_ata':  # tokens already in the donation PDA ATA (non-native quote)
            b, c = s.get('b', 'b1'), s.get('c', 'c1'); q = self.quote(s.get('q', 'spl')); owner = donation_key(b, c)[0]; key = ata_of(owner, q)
            a = self.vm.get_account(key); amt = s['amount'] + (int.from_bytes(bytes(a.data)[64:72], 'little') if a and a.data else 0)
            if q == WSOL: self.vm.set_account(key, Account(self.rent165 + amt + s.get('unsynced', 0), token_data(q, owner, amt, self.rent165), TOKEN))
            else: self.vm.set_account(key, Account(self.rent165, token_data(q, owner, amt), TOKEN))
            return None
        if op == 'flags': self.set_global(s['flags']); return None
        if op == 'clock': self.vm.set_clock(Clock(1000 + s['dt'], 0, 0, 0, T0 + s['dt'])); return None
        if op == 'whitelist': self.set_whitelist([self.quote(x) for x in s['mints']]); return None
        if op == 'mint_freeze': self.vm.set_account(SPL_QUOTE, Account(10 ** 9, mint_data(6, CREATOR), TOKEN)); return None
        if op == 'relay_state':  # pre-existing relay epoch tracker / debouncer
            c = s.get('c', 'c1'); q = self.quote(s.get('q', 'wsol')); cfg = CONFIGS[s.get('cfg', c)]; m = self.quote(s.get('mint', s.get('q', 'wsol')))
            if s['kind'] == 'epoch':
                key, bump = pda([b'epoch_tracker_v1', bytes(CONFIGS[c]), bytes(q)], RELAY)
                d = disc('EpochTrackerV1') + bytes([bump, s.get('state', 1)]) + bytes(cfg) + bytes(m) + s.get('epoch', 0).to_bytes(16, 'little')
            else:
                key, bump = pda([b'debouncer_v1', bytes(CONFIGS[c]), bytes(q)], RELAY)
                d = disc('DebouncerV1') + bytes([bump, s.get('state', 1)]) + bytes(cfg) + bytes(m) + s.get('total', 0).to_bytes(8, 'little')
            self.vm.set_account(key, Account(self.vm.minimum_balance_for_rent_exemption(len(d)), d, RELAY)); return None
        if op == 'freeze_ata':  # set the donation ATA state byte to Frozen
            key = self.keys(s.get('b', 'b1'), s.get('c', 'c1'), s.get('q', 'spl'))['donation_fee_pda_ata']; a = self.vm.get_account(key); d = bytearray(a.data); d[108] = 2
            self.vm.set_account(key, Account(a.lamports, bytes(d), a.owner)); return None
        if op == 'debouncer_ata':  # pre-existing relay debouncer ATA holding tokens
            q = self.quote(s.get('q', 'wsol')); deb = debouncer_key(s.get('c', 'c1'), q)
            reserve = self.rent165 if q == WSOL else None
            self.vm.set_account(ata_of(deb, q), Account(self.rent165 + (s['amount'] if q == WSOL else 0), token_data(q, deb, s['amount'], reserve), TOKEN)); return None
        if op == 'payer_lamports':
            kp = SIGNERS[s.get('signer', 'cranker')]; self.vm.set_account(kp.pubkey(), Account(s['lamports'], b'', SYSTEM)); return None
        if op == 'crank': return self.crank(s)
        raise ValueError(op)

    def keys(self, b, c, q):
        don = donation_key(b, c)[0]; qk = self.quote(q); deb = debouncer_key(c, qk)
        return {'donation_fee_pda': don, 'quote_mint': qk, 'donation_fee_pda_ata': ata_of(don, qk), 'epoch_tracker': epoch_key(c, qk), 'debouncer': deb, 'debouncer_ata': ata_of(deb, qk)}

    def crank(self, s):
        b, c, q = s.get('b', 'b1'), s.get('c', 'c1'), s.get('q', 'wsol'); kp = SIGNERS[s.get('signer', 'cranker')]
        names = {'event_authority': EVENT, 'program': PROGRAM, 'payer': kp.pubkey(), 'system_program': SYSTEM, 'token_program': TOKEN, 'associated_token_program': ATA, 'rent': RENT, 'fee_program_global': GLOBAL, 'donation_relay_program': RELAY, 'donation_relay_event_authority': RELAY_EVENT, 'mint_whitelist': WHITELIST}
        names.update(self.keys(b, c, q))
        for k, (ob, oc) in s.get('swap', {}).items():  # take a relay account from another (base, config)
            names[k] = self.keys(ob, oc, q)[k]
        metas = [AccountMeta(names[n], bool(sg), bool(w)) for n, w, sg in CRANK_ACCOUNTS]
        self.vm.expire_blockhash()
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(PROGRAM, CRANK_DISC, metas)], TX_PAYER.pubkey(), [TX_PAYER, kp], self.vm.latest_blockhash())
        watch = ['donation_fee_pda', 'donation_fee_pda_ata', 'epoch_tracker', 'debouncer', 'debouncer_ata', 'payer']
        before = {n: self.snap(names[n]) for n in watch}
        r = self.vm.send_transaction(tx); failed = isinstance(r, FailedTransactionMetadata); meta = r.meta() if failed else r
        after = {n: self.snap(names[n]) for n in watch}
        return {'error': str(r.err()) if failed else None, 'logs': list(meta.logs()), 'cu': meta.compute_units_consumed(),
                'before': before, 'after': after, 'inner': json.loads(meta.to_json())['inner_instructions']}

    def snap(self, k):
        a = self.vm.get_account(k)
        return None if a is None or (a.lamports == 0 and not a.data) else {'lamports': a.lamports, 'owner': str(a.owner), 'data': bytes(a.data).hex()}

def C(name, note, *steps): return {'name': name, 'note': note, 'steps': list(steps)}
CR = lambda **k: dict(op='crank', **k)
NEW = lambda **k: dict(op='create', **k)
FUND = lambda n, **k: dict(op='fund', lamports=n, **k)

def cases():
    out = [
        C('n-basic', 'native: fund 1,000,000 then crank', NEW(), FUND(1_000_000), CR()),
        C('n-empty-first', 'native: crank with no excess, then fund and crank', NEW(), CR(), FUND(500_000), CR()),
        C('n-repeat', 'native: two cranks, second has nothing', NEW(), FUND(1_000_000), CR(), CR()),
        C('n-accumulate', 'native: three funded cranks, clock moves', NEW(), FUND(1_000_000), CR(), dict(op='clock', dt=60), FUND(2_500_000), CR(), dict(op='clock', dt=120), FUND(1), CR()),
        C('n-one-lamport', 'native: excess of 1 lamport', NEW(), FUND(1), CR()),
        C('n-large', 'native: excess of 10^11 lamports', NEW(), FUND(10 ** 11), CR()),
        C('n-below-rent', 'native: PDA holds rent - 1 (saturating excess = 0)', NEW(), FUND(-1), CR()),
        C('n-ata-tokens', 'native: ATA already holds 777 synced WSOL, PDA has no excess', NEW(), dict(op='fund_ata', q='wsol', amount=777), CR()),
        C('n-ata-unsynced', 'native: ATA has 0 amount but 4,321 unsynced lamports, no PDA excess', NEW(), dict(op='fund_ata', q='wsol', amount=0, unsynced=4321), CR()),
        C('n-ata-plus-excess', 'native: ATA holds 100, PDA excess 900', NEW(), dict(op='fund_ata', q='wsol', amount=100), FUND(900), CR()),
        C('flag-8-set', 'disable flag 8 set; the donation ATA init_if_needed runs before the flag check', NEW(), dict(op='flags', flags=8), FUND(1_000_000), CR()),
        C('flag-8-toggle', 'crank ok, flag 8 set, crank blocked, flag cleared, crank ok', NEW(), FUND(1_000_000), CR(), dict(op='flags', flags=8), FUND(2_000_000), CR(), dict(op='flags', flags=0), CR()),
        C('flag-others', 'flags 0xF7 (all but bit 3) do not block', NEW(), dict(op='flags', flags=0xF7), FUND(1_000_000), CR()),
        C('flag-ff', 'flags 0xFF block', NEW(), dict(op='flags', flags=0xFF), FUND(1_000_000), CR()),
        C('flag-8-empty', 'flag 8 with nothing to donate still errors', NEW(), dict(op='flags', flags=8), CR()),
        C('total-max-minus-1', 'total_donated = 2^64-2, donate 1 -> max, then donate 1 -> overflow', NEW(total=U64 - 1), FUND(1), CR(), FUND(1), CR()),
        C('total-max', 'total_donated = 2^64-1, donate 1,000 -> overflow after relay CPI', NEW(total=U64), FUND(1000), CR()),
        C('total-max-empty', 'total_donated = 2^64-1, nothing to donate -> early ok', NEW(total=U64), CR()),
        C('ts-backwards', 'last_crank_ts set in the future; crank overwrites it with current clock', NEW(last=T0 + 10 ** 6), FUND(10), CR()),
        C('ts-negative', 'clock moved before stored ts, negative stored ts', NEW(last=-5), dict(op='clock', dt=-100), FUND(10), CR()),
        C('ts-same-second', 'two cranks in the same second (no debounce in pump_fees)', NEW(), FUND(10), CR(), FUND(20), CR()),
        C('two-crankers', 'permissionless: different signers pay relay init then reuse', NEW(), FUND(1000), CR(signer='cranker'), FUND(2000), CR(signer='cranker2')),
        C('payer-zero', 'cranker has 0 lamports: ATA init fails', NEW(), dict(op='payer_lamports', lamports=0), FUND(1000), CR()),
        C('payer-ata-only', 'cranker can fund the donation ATA but not relay accounts', NEW(), dict(op='payer_lamports', lamports=2_039_280), FUND(1000), CR()),
        C('payer-ata-plus-one', 'cranker has ATA rent + 1', NEW(), dict(op='payer_lamports', lamports=2_039_281), FUND(1000), CR()),
        C('payer-after-init', 'first crank inits everything, then a 0-lamport cranker succeeds', NEW(), FUND(1000), CR(), dict(op='payer_lamports', signer='cranker2', lamports=0), FUND(1000), CR(signer='cranker2')),
        C('payer-zero-empty', 'cranker has 0 lamports, ATA exists, nothing to donate', NEW(), dict(op='fund_ata', q='wsol', amount=0), dict(op='payer_lamports', lamports=0), CR()),
        C('shared-debouncer', 'two donation PDAs (base b1,b2) same config share epoch/debouncer', NEW(b='b1'), NEW(b='b2'), FUND(1000, b='b1'), CR(b='b1'), FUND(3000, b='b2'), CR(b='b2')),
        C('split-config', 'same base, configs c1/c2 use separate relay accounts', NEW(c='c1'), NEW(c='c2'), FUND(1000, c='c1'), CR(c='c1'), FUND(3000, c='c2'), CR(c='c2')),
        C('swap-debouncer', 'pass config c2 debouncer for a c1 donation PDA', NEW(), FUND(1000), CR(swap={'debouncer': ('b1', 'c2'), 'debouncer_ata': ('b1', 'c2')})),
        C('swap-epoch', 'pass config c2 epoch tracker for a c1 donation PDA', NEW(), FUND(1000), CR(swap={'epoch_tracker': ('b1', 'c2')})),
        C('swap-ata', 'pass b2 donation ATA for b1 donation PDA', NEW(b='b1'), NEW(b='b2'), FUND(1000, b='b2'), CR(b='b2'), FUND(1000), CR(swap={'donation_fee_pda_ata': ('b2', 'c1')})),
        C('relay-epoch-5', 'existing epoch tracker at epoch 5', NEW(), dict(op='relay_state', kind='epoch', epoch=5), FUND(1000), CR()),
        C('relay-debouncer-total', 'existing debouncer total 10^9', NEW(), dict(op='relay_state', kind='debouncer', total=10 ** 9), FUND(1000), CR()),
        C('relay-debouncer-overflow', 'existing debouncer total 2^64-1 -> relay overflow', NEW(), dict(op='relay_state', kind='debouncer', total=U64), FUND(1000), CR()),
        C('relay-debouncer-wrong-config', 'debouncer stores config c2', NEW(), dict(op='relay_state', kind='debouncer', cfg='c2'), FUND(1000), CR()),
        C('relay-epoch-wrong-config', 'epoch tracker stores config c2', NEW(), dict(op='relay_state', kind='epoch', cfg='c2'), FUND(1000), CR()),
        C('relay-debouncer-wrong-mint', 'debouncer stores the SPL quote mint', NEW(), dict(op='relay_state', kind='debouncer', mint='spl'), FUND(1000), CR()),
        C('relay-epoch-wrong-mint', 'epoch tracker stores the SPL quote mint', NEW(), dict(op='relay_state', kind='epoch', mint='spl'), FUND(1000), CR()),
        C('relay-debouncer-state-2', 'debouncer state byte 2', NEW(), dict(op='relay_state', kind='debouncer', state=2), FUND(1000), CR()),
        C('relay-epoch-state-2', 'epoch tracker state byte 2', NEW(), dict(op='relay_state', kind='epoch', state=2), FUND(1000), CR()),
        C('relay-debouncer-state-0', 'debouncer present but Uninitialized (re-initialised by relay)', NEW(), dict(op='relay_state', kind='debouncer', state=0, cfg='c2', total=55), FUND(1000), CR()),
        C('spl-unlisted', 'SPL quote, no freeze authority, not whitelisted', NEW(q='spl'), dict(op='fund_ata', amount=1000), CR(q='spl')),
        C('spl-listed', 'SPL quote whitelisted', NEW(q='spl'), dict(op='whitelist', mints=['spl']), dict(op='fund_ata', amount=1000), CR(q='spl')),
        C('spl-freeze-unlisted', 'SPL quote with freeze authority, not whitelisted', NEW(q='spl'), dict(op='mint_freeze'), dict(op='fund_ata', amount=1000), CR(q='spl')),
        C('spl-freeze-listed', 'SPL quote with freeze authority, whitelisted', NEW(q='spl'), dict(op='mint_freeze'), dict(op='whitelist', mints=['spl']), dict(op='fund_ata', amount=1000), CR(q='spl')),
        C('spl-no-ata', 'SPL quote, no donation ATA yet: init then nothing to donate', NEW(q='spl'), CR(q='spl'), dict(op='fund_ata', amount=5), CR(q='spl')),
        C('spl-lamports-ignored', 'SPL quote: SOL sent to the PDA is not donated', NEW(q='spl'), FUND(10 ** 6), dict(op='fund_ata', amount=0), CR(q='spl')),
        C('spl-repeat', 'SPL quote: donate, refill, donate', NEW(q='spl'), dict(op='fund_ata', amount=7), CR(q='spl'), dict(op='fund_ata', amount=u64h()), CR(q='spl')),
        C('spl-overflow', 'SPL quote: total 2^64-8, donate 7 ok then 1 overflows', NEW(q='spl', total=U64 - 7), dict(op='fund_ata', amount=7), CR(q='spl'), dict(op='fund_ata', amount=1), CR(q='spl')),
        C('spl-ata-frozen', 'SPL quote: donation ATA frozen', NEW(q='spl'), dict(op='fund_ata', amount=1000), dict(op='freeze_ata'), CR(q='spl')),
        C('spl-whitelist-removed', 'freeze-authority mint: listed crank ok, whitelist emptied, next crank', NEW(q='spl'), dict(op='mint_freeze'), dict(op='whitelist', mints=['spl']), dict(op='fund_ata', amount=10), CR(q='spl'), dict(op='whitelist', mints=[]), dict(op='fund_ata', amount=10), CR(q='spl')),
        C('debouncer-ata-balance', 'relay debouncer ATA already holds 5,000 WSOL', NEW(), dict(op='debouncer_ata', amount=5000), FUND(1000), CR()),
        C('shared-debouncer-overflow', 'debouncer at 2^64-1001: b1 adds 1000, then b2 adds 1 -> relay overflow', NEW(b='b1'), NEW(b='b2'), dict(op='relay_state', kind='debouncer', total=U64 - 1000), FUND(1000, b='b1'), CR(b='b1'), FUND(1, b='b2'), CR(b='b2')),
        C('relay-epoch-max', 'epoch tracker at 2^128-1', NEW(), dict(op='relay_state', kind='epoch', epoch=2 ** 128 - 1), FUND(1000), CR()),
        C('flag-8-then-unsynced', 'funded while disabled, then enabled: whole PDA excess donated once', NEW(), dict(op='flags', flags=8), FUND(400), CR(), FUND(600), CR(), dict(op='flags', flags=0), CR(), CR()),
    ]
    return out

def u64h(): return 2 ** 63

def run_case(image, deps, case):
    sim = Sim(image, deps); out = []
    for s in case['steps']:
        r = sim.step(s)
        if r is not None: out.append(r)
    return out

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def decoded(acc, name):
    if acc is None: return None
    d = bytes.fromhex(acc['data'])
    if name == 'donation_fee_pda': return {'lamports': acc['lamports'], 'total_donated': int.from_bytes(d[138:146], 'little'), 'last_crank_ts': int.from_bytes(d[146:154], 'little', signed=True)}
    if name in ('donation_fee_pda_ata', 'debouncer_ata'): return {'lamports': acc['lamports'], 'amount': int.from_bytes(d[64:72], 'little')}
    if name == 'debouncer': return {'state': d[9], 'total_amount': int.from_bytes(d[74:82], 'little')}
    if name == 'epoch_tracker': return {'state': d[9], 'current_epoch': int.from_bytes(d[74:90], 'little')}
    return {'lamports': acc['lamports']}

def summary(r):
    data = [l for l in r['logs'] if l.startswith('Program data:')]
    msgs = [l for l in r['logs'] if l.startswith('Program log:')]
    return {'error': r['error'], 'cu': r['cu'], 'program_data': data, 'log_messages': msgs,
            'after': {n: decoded(a, n) for n, a in r['after'].items()}}

def build(root, images):
    deps = {n: pathlib.Path(root) / 'evidence/dependencies' / n / 'deployed.so' for n in DEPS}
    rows = []
    for case in cases():
        o = run_case(images['original'], deps, case); c = run_case(images['candidate'], deps, case)
        diffs = [i for i, (a, b) in enumerate(zip(o, c)) if a != b]
        rows.append({'name': case['name'], 'note': case['note'], 'steps': case['steps'], 'original': o, 'candidate': c, 'match': not diffs and len(o) == len(c), 'diff_steps': diffs})
    report = {'program': 'pump_fees', 'instruction': 'crank_donation_fee_pda',
              'images': {k: sha(v) for k, v in images.items()}, 'dependencies': {n: sha(p) for n, p in deps.items()},
              'cases': len(rows), 'cranks': sum(len(r['original']) for r in rows),
              'matching_cases': sum(r['match'] for r in rows),
              'compared': ['error', 'full logs', 'compute units', 'inner instructions', 'watched accounts before/after'],
              'per_case': [{'name': r['name'], 'match': r['match'], 'diff_steps': r['diff_steps'], 'cranks': [summary(x) for x in r['original']], 'candidate_cranks': [summary(x) for x in r['candidate']]} for r in rows]}
    return rows, report

def write(out, rows, report):
    rt = pathlib.Path(out) / 'runtime'; rt.mkdir(parents=True, exist_ok=True)
    body = ''.join(json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n' for r in rows).encode()
    (rt / 'receipts.jsonl.gz').write_bytes(gzip.compress(body, mtime=0))
    (rt / 'report.json.gz').write_bytes(gzip.compress((json.dumps(report, sort_keys=True, indent=1) + '\n').encode(), mtime=0))

def main():
    a = argparse.ArgumentParser(); a.add_argument('--root', required=True); a.add_argument('--images', required=True); a.add_argument('--out', required=True); a = a.parse_args()
    images = json.loads(a.images); rows, report = build(a.root, images); write(a.out, rows, report)
    print('cases', report['cases'], 'cranks', report['cranks'], 'matching', report['matching_cases'])

if __name__ == '__main__':
    main()
