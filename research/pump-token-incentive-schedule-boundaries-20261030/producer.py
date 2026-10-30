#!/usr/bin/env python3
"""Pump Main admin_update_token_incentives (incentive schedule setter), original vs rebuild.

The handler checks `global.authority`, creates the GlobalVolumeAccumulator's incentive ATA with
init_if_needed, and then calls update_schedule. That function:

  writes seconds_in_a_day and mint unconditionally;
  if start_time != 0 and end_time != 0, updates the time range:
    a new start must be > now (6031) and zeroes both day arrays;
    end > now (6032); end > start (6033); end - start <= secs*30 - 1 (6034);
    while running, zeroes sol_volumes[current+1..=end_day] after requiring end_day > current (6035);
  if supply > 0, updates the daily token supply:
    before start: day < 30 must be <= end_day (6037), day >= 30 fills 0..=end_day;
    after start: now <= end (6036), end_day >= day (6037), day >= current (6038),
    day >= 30 fills current..=end_day.
It then emits AdminUpdateTokenIncentivesEvent and logs the accumulator with {:?}.

The repository harnesses for this handler (scripts/pump_admin_token_incentives_differential.py,
pump_incentives_admin_differential.py, pump_incentive_schedule_differential.py) load
`research/imported-lab/...`, which is not in the git tree, so they cannot be rerun. This packet
builds Global (1,088 bytes, authority at offset 9) and the accumulator synthetically from the IDL
layout. Two cases chain the setter with claim_token_incentives in one transaction.

Only the Pump image is loaded (upgradeable loader layout). System, SPL Token, Token-2022 and
ATA are LiteSVM built-ins. All state is synthetic, keys come from fixed seeds, the clock is fixed
per case, and there is no network. The full initial account set and instruction list of every
case is written to runtime/plan.json.gz, so verify.py replays without the repository.

Usage:
  python3 producer.py --root <repo> --images '{"original": "...", "candidate": "..."}' --out <packet dir>
"""
import argparse
import base64
import gzip
import hashlib
import json
import struct
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
PAYER_SEED = bytes([234]) * 32
PAYER = Keypair.from_seed(PAYER_SEED).pubkey()  # also Global.authority unless stated
OTHER = Pubkey(bytes([80]) * 32)
USER = Pubkey(bytes([81]) * 32)
INCENTIVE = Keypair.from_seed(bytes([82]) * 32).pubkey()
OTHER_MINT = Keypair.from_seed(bytes([83]) * 32).pubkey()
DAY = 86_400
NOW = 1_800_000_000
START = NOW  # Clock.epoch_start_timestamp
U64 = 2**64 - 1
I64 = 2**63 - 1
GVA_LEN = 600
UVA_LEN = 137
GLOBAL_LEN = 1088

IX = {'admin_update_token_incentives': bytes.fromhex('d10b7357d5177ccc'),
      'claim_token_incentives': bytes.fromhex('1004471ccc01281b')}
IX_ACCOUNTS = {'admin_update_token_incentives': 10, 'claim_token_incentives': 12}
GVA_DISC = bytes.fromhex('ca2af62b8ebe1eff')
UVA_DISC = bytes.fromhex('56ff700e66359afa')
GLOBAL_DISC = bytes.fromhex('a7e8e8b1c86c727f')

pda = lambda seeds, program=PROGRAM: Pubkey.find_program_address(seeds, program)[0]
EVENT_AUTHORITY = pda([b'__event_authority'])
GVA = pda([b'global_volume_accumulator'])
GLOBAL = pda([b'global'])


def rent(n):
    return (128 + n) * 6960


def uva_of(user):
    return pda([b'user_volume_accumulator', bytes(user)])


def ata(owner, mint, program=TOKEN):
    return pda([bytes(owner), bytes(program), bytes(mint)], ATA_PROGRAM)


def mint_data(decimals):
    d = bytearray(82)
    struct.pack_into('<Q', d, 36, 10**15)
    d[44] = decimals
    d[45] = 1
    return bytes(d)


def token_data(mint, owner, amount, state=1):
    d = bytearray(165)
    d[:32] = bytes(mint)
    d[32:64] = bytes(owner)
    struct.pack_into('<Q', d, 64, amount)
    d[108] = state
    return bytes(d)


def global_data(authority=PAYER):
    d = bytearray(GLOBAL_LEN)
    d[:8] = GLOBAL_DISC
    d[8] = 1
    d[9:41] = bytes(authority)
    return bytes(d)


def gva_data(start=0, end=0, secs=0, mint=SYSTEM, supply=None, volumes=None, length=GVA_LEN):
    d = bytearray(GVA_DISC + struct.pack('<qqq', start, end, secs) + bytes(mint))
    d += struct.pack('<30Q', *(supply or [0] * 30)) + struct.pack('<30Q', *(volumes or [0] * 30))
    return bytes(d + bytes(max(0, length - len(d))))[:length]


def decode_gva(hexdata):
    d = bytes.fromhex(hexdata)
    if len(d) < 544 or d[:8] != GVA_DISC:
        return None
    start, end, secs = struct.unpack_from('<qqq', d, 8)
    return {'start_time': start, 'end_time': end, 'seconds_in_a_day': secs, 'mint': str(Pubkey(d[32:64])),
            'total_token_supply': list(struct.unpack_from('<30Q', d, 64)),
            'sol_volumes': list(struct.unpack_from('<30Q', d, 304))}


def uva_data(user=USER, volume=0, last=0):
    d = UVA_DISC + bytes(user) + struct.pack('<BQQQqBQQQQ', 1, 0, 0, volume, last, 0, 0, 0, 0, 0)
    return bytes(d + bytes(UVA_LEN - len(d)))


# ---- plan: cases are pure data (accounts + instruction list) ----

def acct(key, lamports, owner=SYSTEM, data=b''):
    return [str(key), lamports, str(owner), data.hex()]


def ix(kind, keys, args=b''):
    return {'program': str(PROGRAM), 'data_hex': (IX[kind] + args).hex(),
            'metas': [[str(k), k == PAYER, w] for k, w in keys]}


def update(start, end, secs, day=0, supply=0, mint=INCENTIVE, tprog=TOKEN, authority=PAYER, sub=None):
    keys = [(authority, True), (GLOBAL, False), (GVA, True), (mint, False), (ata(GVA, mint, tprog), True),
            (ATA_PROGRAM, False), (SYSTEM, False), (tprog, False), (EVENT_AUTHORITY, False), (PROGRAM, False)]
    for i, k in (sub or {}).items():
        keys[i] = (k, keys[i][1])
    return ix('admin_update_token_incentives', keys, struct.pack('<qqqQQ', start, end, secs, day, supply))


def claim(user=USER, mint=INCENTIVE, tprog=TOKEN):
    keys = [(user, False), (ata(user, mint, tprog), True), (GVA, False), (ata(GVA, mint, tprog), True),
            (uva_of(user), True), (mint, False), (tprog, False), (SYSTEM, False), (ATA_PROGRAM, False),
            (EVENT_AUTHORITY, False), (PROGRAM, False), (PAYER, True)]
    return ix('claim_token_incentives', keys)


# Accumulator states (relative to the fixed clock NOW)
FRESH = gva_data()
FUTURE_START = NOW + DAY
FUTURE = gva_data(FUTURE_START, FUTURE_START + 10 * DAY, DAY, INCENTIVE)
RUN_START = NOW - 3 * DAY - 100  # now is on day 3
RUNNING = gva_data(RUN_START, RUN_START + 10 * DAY, DAY, INCENTIVE, [7] * 30, [5] * 30)
FINISHED = gva_data(NOW - 20 * DAY, NOW - 10 * DAY, DAY, INCENTIVE, [7] * 30, [5] * 30)


def plan():
    cases = []

    def add(name, note, gva, ixs, extra=(), ts=NOW, authority=PAYER, incentive_ata=False, tprog=TOKEN):
        accounts = [acct(PAYER, 10**12), acct(GLOBAL, rent(GLOBAL_LEN), PROGRAM, global_data(authority)),
                    acct(INCENTIVE, 10**9, tprog, mint_data(6))]
        if gva is not None:
            accounts.append(acct(GVA, rent(GVA_LEN), PROGRAM, gva))
        if incentive_ata:
            accounts.append(acct(ata(GVA, INCENTIVE, tprog), rent(165), tprog, token_data(INCENTIVE, GVA, 10**9)))
        cases.append({'case': name, 'note': note, 'accounts': accounts + list(extra), 'instructions': ixs,
                      'unix_timestamp': ts})

    S = NOW + 100
    # ---- time range on a fresh (all-zero) accumulator ----
    add('fresh-set-range', 'fresh accumulator: start now+100, 10-day range, 86,400 s days', FRESH,
        [update(S, S + 10 * DAY, DAY)])
    add('start-equals-now', 'start = now', FRESH, [update(NOW, NOW + DAY, DAY)])
    add('start-now-plus-1', 'start = now + 1', FRESH, [update(NOW + 1, NOW + DAY, DAY)])
    add('end-equals-now', 'start now+100, end = now', FRESH, [update(S, NOW, DAY)])
    add('end-equals-start', 'end = start', FRESH, [update(S, S, DAY)])
    add('range-30-days-minus-1', 'end - start = 30 * 86,400 - 1 (largest accepted)', FRESH,
        [update(S, S + 30 * DAY - 1, DAY)])
    add('range-30-days', 'end - start = 30 * 86,400', FRESH, [update(S, S + 30 * DAY, DAY)])
    add('secs-zero', 'seconds_in_a_day 0, range 1 s', FRESH, [update(S, S + 1, 0)])
    add('secs-one-range-29', 'seconds_in_a_day 1, range 29 s', FRESH, [update(S, S + 29, 1)])
    add('secs-negative', 'seconds_in_a_day -1, range 1 s', FRESH, [update(S, S + 1, -1)])
    add('secs-mul-overflow', 'seconds_in_a_day = i64::MAX / 30 + 1 (secs * 30 overflows)', FRESH,
        [update(S, S + 1, I64 // 30 + 1)])
    add('secs-max-end-max', 'seconds_in_a_day = i64::MAX / 30, end = i64::MAX', FRESH,
        [update(S, I64, I64 // 30)])
    add('start-zero-skips-range', 'start 0, end set: range skipped, secs and mint still written', FRESH,
        [update(0, S + DAY, DAY)])
    add('end-zero-skips-range', 'end 0, start set: range skipped', FRESH, [update(S, 0, 123)])
    add('fresh-supply-only', 'fresh accumulator, no range, supply 1,000 for day 0 (now > end 0)', FRESH,
        [update(0, 0, DAY, 0, 1_000)])
    add('fresh-range-and-fill', 'fresh: set range and fill every day (day_number 30) with 1,000', FRESH,
        [update(S, S + 10 * DAY, DAY, 30, 1_000)])
    # ---- running accumulator (now on day 3 of 0..=10) ----
    add('running-same-start-shorter-end', 'running: same start, end_day 10 -> 5 (clears sol_volumes 4..=5 only)',
        RUNNING, [update(RUN_START, RUN_START + 5 * DAY, DAY)])
    add('running-end-on-current-day', 'running: same start, end_day = current day 3', RUNNING,
        [update(RUN_START, RUN_START + 3 * DAY + 200, DAY)])
    add('running-end-current-plus-1', 'running: same start, end_day = 4', RUNNING,
        [update(RUN_START, RUN_START + 4 * DAY, DAY)])
    add('running-end-in-past', 'running: same start, end = now', RUNNING, [update(RUN_START, NOW, DAY)])
    add('running-new-future-start', 'running: new start now+100 zeroes both arrays', RUNNING,
        [update(S, S + 10 * DAY, DAY)])
    add('running-new-past-start', 'running: start moved one day earlier (in the past)', RUNNING,
        [update(RUN_START - DAY, RUN_START + 10 * DAY, DAY)])
    add('running-halve-day-length', 'running: same start, seconds_in_a_day 43,200, end - start = 15 days '
        '(= 30 * 43,200)', RUNNING, [update(RUN_START, RUN_START + 15 * DAY, DAY // 2)])
    add('running-halve-day-length-ok', 'running: same start, seconds_in_a_day 43,200, end - start = 15 days - 1 '
        '(current day becomes 6)', RUNNING, [update(RUN_START, RUN_START + 15 * DAY - 1, DAY // 2)])
    # ---- supply before start ----
    add('future-supply-day-0', 'future range (end_day 10): supply 1,000 for day 0', FUTURE,
        [update(0, 0, DAY, 0, 1_000)])
    add('future-supply-end-day', 'future: supply for day 10 = end_day', FUTURE, [update(0, 0, DAY, 10, 1_000)])
    add('future-supply-after-end-day', 'future: supply for day 11', FUTURE, [update(0, 0, DAY, 11, 1_000)])
    add('future-supply-day-29', 'future: supply for day 29 (< 30, > end_day)', FUTURE, [update(0, 0, DAY, 29, 1_000)])
    add('future-supply-fill-u64max-day', 'future: day_number u64::MAX fills 0..=10', FUTURE,
        [update(0, 0, DAY, U64, 1_000)])
    add('future-supply-zero', 'future: supply 0 for day 0 (no-op)', FUTURE, [update(0, 0, DAY, 0, 0)])
    add('future-secs-zero-supply', 'future: seconds_in_a_day 0 then supply day 0 (end_day divisor 0)', FUTURE,
        [update(0, 0, 0, 0, 1_000)])
    add('future-40-day-fill', 'synthetic 40-day future range, fill (day 30)',
        gva_data(FUTURE_START, FUTURE_START + 40 * DAY, DAY, INCENTIVE), [update(0, 0, DAY, 30, 1_000)])
    # ---- supply after start ----
    add('running-supply-current-day', 'running: supply for current day 3', RUNNING, [update(0, 0, DAY, 3, 1_000)])
    add('running-supply-past-day', 'running: supply for day 2', RUNNING, [update(0, 0, DAY, 2, 1_000)])
    add('running-supply-after-end-day', 'running: supply for day 11', RUNNING, [update(0, 0, DAY, 11, 1_000)])
    add('running-supply-fill', 'running: fill (day 30) current..=end', RUNNING, [update(0, 0, DAY, 30, 1_000)])
    add('finished-supply', 'finished range (now > end): supply day 0', FINISHED, [update(0, 0, DAY, 0, 1_000)])
    add('supply-at-exact-end', 'clock = end_time exactly: supply for day 10', RUNNING,
        [update(0, 0, DAY, 10, 1_000)], ts=RUN_START + 10 * DAY)
    add('supply-at-exact-start', 'clock = start_time exactly: supply for day 0', RUNNING,
        [update(0, 0, DAY, 0, 1_000)], ts=RUN_START)
    add('running-negative-clock-start', 'synthetic running state, start -100, clock 50: fill',
        gva_data(-100, 5 * DAY, DAY, INCENTIVE), [update(0, 0, DAY, 30, 1_000)], ts=50)
    # ---- accounts ----
    add('not-authority', 'Global.authority = OTHER, payer signs', FUTURE, [update(0, 0, DAY, 0, 1_000)],
        authority=OTHER)
    add('authority-unsigned', 'authority slot = OTHER (Global.authority) without a signature', FUTURE,
        [update(0, 0, DAY, 0, 1_000, sub={0: OTHER})], authority=OTHER, extra=[acct(OTHER, 10**9)])
    add('mint-replaced', 'accumulator mint INCENTIVE, OTHER_MINT passed: mint overwritten, its ATA created', FUTURE,
        [update(0, 0, DAY, 0, 1_000, mint=OTHER_MINT)], extra=[acct(OTHER_MINT, 10**9, TOKEN, mint_data(9))])
    add('incentive-ata-exists', 'incentive ATA already exists', FUTURE, [update(0, 0, DAY, 0, 1_000)],
        incentive_ata=True)
    add('token-2022-mint', 'Token-2022 incentive mint: ATA created under Token-2022', FUTURE,
        [update(0, 0, DAY, 0, 1_000, tprog=TOKEN22)], tprog=TOKEN22)
    add('incentive-not-ata', 'incentive slot holds a token account of the accumulator that is not its ATA', FUTURE,
        [update(0, 0, DAY, 0, 1_000, sub={4: OTHER})],
        extra=[acct(OTHER, rent(165), TOKEN, token_data(INCENTIVE, GVA, 0))])
    add('accumulator-absent', 'GlobalVolumeAccumulator does not exist', None, [update(0, 0, DAY, 0, 1_000)])
    add('accumulator-wrong-owner', 'accumulator data owned by the System program', None,
        [update(0, 0, DAY, 0, 1_000)], extra=[acct(GVA, rent(GVA_LEN), SYSTEM, FUTURE)])
    add('accumulator-543-bytes', 'accumulator data 543 bytes', gva_data(FUTURE_START, FUTURE_START + 10 * DAY, DAY,
                                                                          INCENTIVE, length=543),
        [update(0, 0, DAY, 0, 1_000)])
    add('global-wrong-address', 'global slot holds a Global-shaped account at another address', FUTURE,
        [update(0, 0, DAY, 0, 1_000, sub={1: OTHER})], extra=[acct(OTHER, rent(GLOBAL_LEN), PROGRAM, global_data())])
    add('token-program-mismatch', 'SPL mint passed with the Token-2022 program', FUTURE,
        [update(0, 0, DAY, 0, 1_000, sub={4: ata(GVA, INCENTIVE), 7: TOKEN22})])
    # ---- sequences ----
    add('seq-update-twice-same-start', 'set range + day-0 supply, then same start with a longer end: supply kept',
        FRESH, [update(S, S + 5 * DAY, DAY, 0, 1_000), update(S, S + 9 * DAY, DAY)])
    add('seq-update-twice-new-start', 'set range + day-0 supply, then a later start: supply zeroed', FRESH,
        [update(S, S + 5 * DAY, DAY, 0, 1_000), update(S + 1, S + 5 * DAY, DAY)])
    add('seq-fill-then-claim', 'running: fill current..=end with 9, then a claim for a user active on day 2 '
        '(paid from day-2 supply 7)', RUNNING, [update(0, 0, DAY, 30, 9), claim()], incentive_ata=True,
        extra=[acct(uva_of(USER), rent(UVA_LEN), PROGRAM, uva_data(volume=5, last=RUN_START + 2 * DAY + 1))])
    add('seq-new-start-then-claim', 'running: new future start zeroes arrays, then the day-2 user claims', RUNNING,
        [update(S, S + 10 * DAY, DAY), claim()], incentive_ata=True,
        extra=[acct(uva_of(USER), rent(UVA_LEN), PROGRAM, uva_data(volume=5, last=RUN_START + 2 * DAY + 1))])
    return cases


# ---- execution (verify.py imports this from the packet copy) ----

LOADERS = ('upgradeable',)


def load_vm(image):
    vm = LiteSVM().with_transaction_history(0).with_sigverify(True)
    elf = Path(image).read_bytes()
    programdata = Pubkey.find_program_address([bytes(PROGRAM)], UPGRADEABLE)[0]
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + elf, UPGRADEABLE, False))
    vm.set_account(PROGRAM, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    return vm


FIXED = {PROGRAM, TOKEN, TOKEN22, ATA_PROGRAM, SYSTEM}
PANIC = 'Program log: panicked at '


def pump_messages(logs):
    """`msg!` lines logged while the Pump program itself is on top of the invoke stack."""
    stack, out = [], []
    for l in logs:
        parts = l.split(' ')
        if len(parts) == 4 and parts[0] == 'Program' and parts[2] == 'invoke':
            stack.append(parts[1])
        elif len(parts) >= 3 and parts[0] == 'Program' and parts[2] in ('success', 'failed:') and stack:
            stack.pop()
        elif (stack and stack[-1] == str(PROGRAM) and l.startswith('Program log: ')
              and not l.startswith('Program log: Instruction: ') and not l.startswith('Program log: AnchorError')
              and not l.startswith(PANIC)):
            out.append(l[13:])
    return out


def run_case(vm, index, c):
    vm.expire_blockhash()
    vm.set_clock(Clock(1000 + index, START, 0, 0, c['unix_timestamp']))
    keys = set()
    for k, lam, owner, data in c['accounts']:
        key = Pubkey.from_string(k)
        keys.add(key)
        vm.set_account(key, Account(lam, bytes.fromhex(data), Pubkey.from_string(owner)))
    ixs = []
    for i in c['instructions']:
        metas = [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in i['metas']]
        keys |= {m.pubkey for m in metas}
        ixs.append(Instruction(Pubkey.from_string(i['program']), bytes.fromhex(i['data_hex']), metas))
    payer = Keypair.from_seed(PAYER_SEED)
    tx = Transaction.new_signed_with_payer(ixs, payer.pubkey(), [payer], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    logs = list(meta.logs())
    after = {}
    for key in sorted(keys - FIXED, key=str):
        a = vm.get_account(key)
        if a is not None and (a.lamports or a.data):
            after[str(key)] = [a.lamports, str(a.owner), a.executable, bytes(a.data).hex()]
    for key in keys - FIXED:  # reset so the next case starts from its own state only
        vm.set_account(key, Account(0, b'', SYSTEM))
    return {'case': c['case'],
            'transaction_base64': base64.b64encode(bytes(tx)).decode(),
            'error': str(result.err()) if failed else None,
            'events': [l[14:] for l in logs if l.startswith('Program data: ')],
            'handler_messages': pump_messages(logs),
            'panic_messages': [l[len(PANIC):].split(':', 3)[-1] for l in logs if l.startswith(PANIC)],
            'inner_instructions': json.loads(meta.to_json())['inner_instructions'],
            'accounts_after': after, 'compute_units': meta.compute_units_consumed(), 'logs': logs}


def run_plan(image, loader, cases):
    assert loader == 'upgradeable'
    vm = load_vm(image)
    return [run_case(vm, i, c) for i, c in enumerate(cases)]


BEHAVIOR = ('transaction_base64', 'error', 'events', 'handler_messages', 'panic_messages', 'inner_instructions',
            'accounts_after')
SITE = 'Program log: AnchorError thrown in '


def classify_logs(original, candidate):
    if len(original) != len(candidate):
        return [{'kind': 'line-count', 'original': len(original), 'candidate': len(candidate)}]
    out = []
    for a, b in zip(original, candidate):
        if a == b:
            continue
        if a.startswith(SITE) and b.startswith(SITE) and a.split('. ', 1)[1:] == b.split('. ', 1)[1:]:
            out.append({'kind': 'anchor-error-site', 'original': a[len(SITE):].split('. ')[0],
                        'candidate': b[len(SITE):].split('. ')[0]})
        elif a.startswith(PANIC) and b.startswith(PANIC):
            out.append({'kind': 'panic-site', 'original': a[len(PANIC):], 'candidate': b[len(PANIC):]})
        elif ' consumed ' in a and ' consumed ' in b:
            out.append({'kind': 'consumed', 'original': a, 'candidate': b})
        else:
            out.append({'kind': 'other', 'original': a, 'candidate': b})
    return out


def outcome(r):
    if r['error']:
        for line in r['logs']:
            if 'Error Code: ' in line:
                return 'error:' + line.split('Error Code: ', 1)[1].split('.', 1)[0]
        if r['panic_messages']:
            return 'panic:' + r['panic_messages'][0].strip()
        return 'error:' + r['error']
    return 'ok:' + ('|'.join(r['handler_messages']) or 'paid')


def before_of(c, key):
    return next((a for a in c['accounts'] if a[0] == key), None)


def lamport_delta(c, r, key):
    b = before_of(c, key)
    return r['accounts_after'].get(key, [0])[0] - (b[1] if b else 0)


def token_amount(hexdata):
    d = bytes.fromhex(hexdata)
    return struct.unpack_from('<Q', d, 64)[0] if len(d) >= 165 else None


def token_delta(c, r, key):
    b = before_of(c, key)
    before = token_amount(b[3]) if b and len(b[3]) >= 330 else 0
    a = r['accounts_after'].get(key)
    after = token_amount(a[3]) if a and len(a[3]) >= 330 else 0
    return (after or 0) - (before or 0)


def compact(values):
    """[7, 7, 9, 9, 0] -> '7x2 9x2 0x1' (run-length) for readable report rows."""
    out, prev, n = [], None, 0
    for v in values + [None]:
        if v == prev:
            n += 1
            continue
        if prev is not None:
            out.append(f'{prev}x{n}')
        prev, n = v, 1
    return ' '.join(out)


def gva_view(c, r):
    if r is None:
        b = next((a for a in c['accounts'] if a[0] == str(GVA)), None)
        g = decode_gva(b[3]) if b else None
    else:
        a = r['accounts_after'].get(str(GVA))
        g = decode_gva(a[3]) if a else None
    if g is None:
        return None
    g['total_token_supply'] = compact(g['total_token_supply'])
    g['sol_volumes'] = compact(g['sol_volumes'])
    return g


def short_outcome(r):
    """outcome() without the setter's `GlobalVolumeAccumulator={:?}` dump (kept in the receipts)."""
    if r['error']:
        return outcome(r)
    msgs = [m for m in r['handler_messages'] if not m.startswith('GlobalVolumeAccumulator=')]
    return 'ok:' + ('|'.join(msgs) or 'updated')


def summarize(cases, original, candidate):
    rows = []
    for c, ro, rc in zip(cases, original, candidate):
        row = {'case': c['case'], 'note': c['note'],
               'outcome': {'original': short_outcome(ro), 'candidate': short_outcome(rc)},
               'events': {'original': len(ro['events']), 'candidate': len(rc['events'])},
               'accumulator_before': gva_view(c, None),
               'accumulator_after': {'original': gva_view(c, ro), 'candidate': gva_view(c, rc)},
               'compute_units': {'original': ro['compute_units'], 'candidate': rc['compute_units'],
                                 'original_minus_candidate': ro['compute_units'] - rc['compute_units']},
               'logs_equal': ro['logs'] == rc['logs'],
               'differing_log_lines': classify_logs(ro['logs'], rc['logs']),
               'behavior_differences': [k for k in BEHAVIOR if ro[k] != rc[k]]}
        if any(i['data_hex'].startswith(IX['claim_token_incentives'].hex()) for i in c['instructions']):
            dest = str(ata(USER, INCENTIVE))
            row['claim_token_delta'] = {'original': token_delta(c, ro, dest), 'candidate': token_delta(c, rc, dest)}
        rows.append(row)
    outcomes, deltas, kinds = {}, {}, {}
    for r in rows:
        o = r['outcome']['original']
        outcomes[o] = outcomes.get(o, 0) + 1
        dk = str(r['compute_units']['original_minus_candidate'])
        deltas[dk] = deltas.get(dk, 0) + 1
        kind = ','.join(sorted({d['kind'] for d in r['differing_log_lines']})) or 'none'
        kinds[kind] = kinds.get(kind, 0) + 1
    return {'case_count': len(rows),
            'behavior_mismatches': [r['case'] for r in rows if r['behavior_differences']],
            'outcome_mismatches': [r['case'] for r in rows if r['outcome']['original'] != r['outcome']['candidate']],
            'compute_units_equal_cases': sum(r['compute_units']['original_minus_candidate'] == 0 for r in rows),
            'logs_equal_cases': sum(r['logs_equal'] for r in rows),
            'cases_by_outcome': dict(sorted(outcomes.items())),
            'compute_unit_delta_counts': dict(sorted(deltas.items())),
            'log_difference_kinds': dict(sorted(kinds.items())),
            'cases': rows}


def write_gz(path, text):
    path.write_bytes(gzip.compress(text.encode(), mtime=0))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    images = json.loads(args.images)
    idl_path = args.root / 'evidence/upstream/pump.json'
    idl = json.loads(idl_path.read_text())
    assert idl['address'] == str(PROGRAM)
    for name, disc in IX.items():  # discriminators and account counts must match the upstream IDL
        i = next(i for i in idl['instructions'] if i['name'] == name)
        assert bytes(i['discriminator']) == disc and len(i['accounts']) == IX_ACCOUNTS[name], name
    acc = {a['name']: bytes(a['discriminator']) for a in idl['accounts']}
    assert (acc['GlobalVolumeAccumulator'], acc['UserVolumeAccumulator'], acc['Global']) == (GVA_DISC, UVA_DISC,
                                                                                               GLOBAL_DISC)
    cases = plan()
    assert len(cases) <= 60 and len({c['case'] for c in cases}) == len(cases)
    blobs = {n: Path(images[n]).read_bytes() for n in ('original', 'candidate')}
    runtime = args.out / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*'):
        old.unlink()
    write_gz(runtime / 'plan.json.gz', json.dumps(cases, sort_keys=True, indent=0) + '\n')
    report = {'scope': 'Pump Main admin_update_token_incentives: time-range and daily-supply boundaries, account '
                       'constraints, schedule->claim sequences; original vs rebuild; upgradeable loader; synthetic '
                       'state; no network.',
              'images': {n: hashlib.sha256(b).hexdigest() for n, b in blobs.items()},
              'image_bytes': {n: len(b) for n, b in blobs.items()},
              'behavior_fields': list(BEHAVIOR), 'loaders': {}, 'receipts': {},
              'idl_sha256': hashlib.sha256(idl_path.read_bytes()).hexdigest()}
    for loader in LOADERS:
        original = run_plan(images['original'], loader, cases)
        candidate = run_plan(images['candidate'], loader, cases)
        lines = []
        for ro, rc in zip(original, candidate):
            lines += [json.dumps({'loader': loader, 'image': 'original', **ro}, sort_keys=True, separators=(',', ':')),
                      json.dumps({'loader': loader, 'image': 'candidate', **rc}, sort_keys=True, separators=(',', ':'))]
        name = f'receipts-{loader}.jsonl.gz'
        write_gz(runtime / name, '\n'.join(lines) + '\n')
        report['receipts'][name] = {'count': len(lines),
                                    'sha256': hashlib.sha256((runtime / name).read_bytes()).hexdigest()}
        report['loaders'][loader] = summarize(cases, original, candidate)
    write_gz(runtime / 'report.json.gz', json.dumps(report, sort_keys=True, indent=1) + '\n')
    for loader, s in report['loaders'].items():
        print(loader, json.dumps({k: s[k] for k in ('case_count', 'behavior_mismatches', 'outcome_mismatches',
                                                    'compute_units_equal_cases', 'logs_equal_cases',
                                                    'cases_by_outcome', 'compute_unit_delta_counts',
                                                    'log_difference_kinds')}, indent=1))


if __name__ == '__main__':
    main()
