#!/usr/bin/env python3
"""Pump Main quote-control administration, original vs rebuild.

QuoteControl (PDA [b"quote-control"]) is the admin-managed list of quote mints that may back
bonding curves, each with its initial virtual quote reserves. Layout: discriminator | admin |
reserves_admin | 32 reserved | u32 count | count x (mint, u64 reserves). It is created at
8 + INIT_SPACE = 2,108 bytes (room for 50 entries) and grows by one 40-byte entry per add when
full, up to MAX_QUOTE_CONTROL_MINTS = 256. Six instructions manage it:

  initialize_quote_control           anyone pays; admin and reserves_admin start as the default key
  set_quote_control_admin            Global.authority only
  set_quote_control_reserves_admin   quote-control admin or Global.authority
  add_quote_control_mint             admin or Global.authority; rejects default/native mints (6069),
                                     duplicates (6067), a full list (6066); reallocs and tops up rent
  remove_quote_control_mint          admin or Global.authority; 6069 for the default key, 6068 if absent
  set_quote_control_mint_reserves    reserves admin, admin or Global.authority; 6068 if absent

pump-instruction-decode-boundaries-20261030 covers only argument decoding and first-account
checks of these instructions. The repository harnesses (scripts/pump_quote_control_differential.py,
pump_quote_control_fresh_differential.py) load `research/imported-lab/...`, which is not in the
git tree, so they cannot be rerun. This packet builds Global (1,088 bytes, authority at offset 9)
and QuoteControl synthetically from the IDL layout and runs single instructions, role checks,
growth/rent boundaries and in-transaction sequences.

Only the Pump image is loaded (upgradeable loader layout); System is the LiteSVM built-in. All
state is synthetic, keys come from fixed seeds, the clock is fixed per case, and there is no
network. The full initial account set, signer seeds and instruction list of every case is written
to runtime/plan.json.gz, so verify.py replays without the repository.

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
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
WSOL22 = Pubkey.from_string('9pan9bMn5HatX4EJdBwg9VgCa7Uz5HL8N1m5D3NdXejP')
SYSTEM = Pubkey.default()
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
PAYER_SEED = bytes([235]) * 32
PAYER = Keypair.from_seed(PAYER_SEED).pubkey()  # Global.authority
SEEDS = {'admin': bytes([91]) * 32, 'reserves': bytes([92]) * 32, 'stranger': bytes([93]) * 32}
KEY = {name: Keypair.from_seed(seed).pubkey() for name, seed in SEEDS.items()}
KEY['authority'] = PAYER
START = 1_800_000_000
U64 = 2**64 - 1
GLOBAL_LEN = 1088
QC_BASE = 8 + 32 + 32 + 32 + 4
ENTRY = 40
QC_INIT_LEN = QC_BASE + 50 * ENTRY  # 2,108

IX = {'initialize_quote_control': bytes.fromhex('ef49f5add1b15442'),
      'set_quote_control_admin': bytes.fromhex('3e4fa1d3a5aad6d2'),
      'set_quote_control_reserves_admin': bytes.fromhex('a1c3dea5e165c03e'),
      'add_quote_control_mint': bytes.fromhex('020e3d8aaa8e0e5f'),
      'remove_quote_control_mint': bytes.fromhex('df07fd1a51a5daa6'),
      'set_quote_control_mint_reserves': bytes.fromhex('74dc6b53bf2c2049')}
IX_ACCOUNTS = {'initialize_quote_control': 3, 'set_quote_control_admin': 5, 'set_quote_control_reserves_admin': 5,
               'add_quote_control_mint': 6, 'remove_quote_control_mint': 6, 'set_quote_control_mint_reserves': 5}
QC_DISC = bytes.fromhex('38f423eec1d5a2c9')
GLOBAL_DISC = bytes.fromhex('a7e8e8b1c86c727f')

pda = lambda seeds, program=PROGRAM: Pubkey.find_program_address(seeds, program)[0]
EVENT_AUTHORITY = pda([b'__event_authority'])
GLOBAL = pda([b'global'])
QC = pda([b'quote-control'])


def rent(n):
    return (128 + n) * 6960


def mint_key(i):
    return Pubkey(struct.pack('<H', i + 1) + bytes([100]) * 30)


def global_data(authority=PAYER):
    d = bytearray(GLOBAL_LEN)
    d[:8] = GLOBAL_DISC
    d[8] = 1
    d[9:41] = bytes(authority)
    return bytes(d)


def qc_data(admin=None, reserves=None, entries=(), length=None, count=None):
    d = QC_DISC + bytes(KEY['admin'] if admin is None else admin) + bytes(KEY['reserves'] if reserves is None else
                                                                         reserves)
    d += bytes(32) + struct.pack('<I', len(entries) if count is None else count)
    for m, r in entries:
        d += bytes(m) + struct.pack('<Q', r)
    size = max(QC_INIT_LEN, len(d)) if length is None else length
    return (d + bytes(max(0, size - len(d))))[:size]


def decode_qc(hexdata):
    d = bytes.fromhex(hexdata)
    if len(d) < QC_BASE or d[:8] != QC_DISC:
        return None
    n = struct.unpack_from('<I', d, 104)[0]
    entries = [(str(Pubkey(d[108 + ENTRY * i:140 + ENTRY * i])), struct.unpack_from('<Q', d, 140 + ENTRY * i)[0])
               for i in range(min(n, (len(d) - QC_BASE) // ENTRY))]
    return {'len': len(d), 'admin': str(Pubkey(d[8:40])), 'reserves_admin': str(Pubkey(d[40:72])), 'count': n,
            'entries': entries}


# ---- plan: cases are pure data (accounts + signer seeds + instruction list) ----

def acct(key, lamports, owner=SYSTEM, data=b''):
    return [str(key), lamports, str(owner), data.hex()]


def ix(kind, keys, args=b''):
    return {'program': str(PROGRAM), 'data_hex': (IX[kind] + args).hex(),
            'metas': [[str(k), s, w] for k, s, w in keys]}


def init(user=PAYER):
    return ix('initialize_quote_control', [(QC, False, True), (user, True, True), (SYSTEM, False, False)])


def set_admin(new, who='authority'):
    return ix('set_quote_control_admin', [(GLOBAL, False, False), (KEY[who], True, False), (QC, False, True),
                                          (EVENT_AUTHORITY, False, False), (PROGRAM, False, False)], bytes(new))


def set_reserves_admin(new, who='authority'):
    return ix('set_quote_control_reserves_admin', [(KEY[who], True, False), (GLOBAL, False, False), (QC, False, True),
                                                   (EVENT_AUTHORITY, False, False), (PROGRAM, False, False)], bytes(new))


def add(mint, reserves=1_000, who='admin', writable=True):
    return ix('add_quote_control_mint', [(KEY[who], True, writable), (GLOBAL, False, False), (QC, False, True),
                                         (SYSTEM, False, False), (EVENT_AUTHORITY, False, False),
                                         (PROGRAM, False, False)], bytes(mint) + struct.pack('<Q', reserves))


def remove(mint, who='admin'):
    return ix('remove_quote_control_mint', [(KEY[who], True, True), (GLOBAL, False, False), (QC, False, True),
                                            (SYSTEM, False, False), (EVENT_AUTHORITY, False, False),
                                            (PROGRAM, False, False)], bytes(mint))


def set_reserves(mint, reserves, who='reserves'):
    return ix('set_quote_control_mint_reserves', [(KEY[who], True, False), (GLOBAL, False, False), (QC, False, True),
                                                  (EVENT_AUTHORITY, False, False), (PROGRAM, False, False)],
              bytes(mint) + struct.pack('<Q', reserves))


def entries(n, reserves=1_000):
    return [(mint_key(i), reserves + i) for i in range(n)]


NEW = mint_key(999)


def plan():
    cases = []

    def case(name, note, qc, ixs, signers=(), extra=(), lamports=None):
        accounts = [acct(PAYER, 10**12), acct(GLOBAL, rent(GLOBAL_LEN), PROGRAM, global_data())]
        for who in sorted(set(signers)):
            accounts.append(acct(KEY[who], 10**10 if lamports is None else lamports))
        if qc is not None:
            accounts.append(acct(QC, rent(len(qc)), PROGRAM, qc))
        cases.append({'case': name, 'note': note, 'accounts': accounts + list(extra), 'instructions': ixs,
                      'signer_seeds': [SEEDS[w].hex() for w in sorted(set(signers))], 'unix_timestamp': START})

    base = qc_data(entries=entries(3))
    # ---- initialize ----
    case('init', 'initialize_quote_control by the fee payer', None, [init()])
    case('init-twice', 'initialize, initialize', None, [init(), init()])
    case('init-existing', 'quote-control account already exists', base, [init()])
    case('init-prefunded', 'PDA already holds 1,000,000 lamports (system-owned, no data)', None, [init()],
         extra=[acct(QC, 1_000_000)])
    case('init-by-stranger', 'any signer may initialize (stranger pays)', None, [init(KEY['stranger'])], ['stranger'])
    # ---- set_quote_control_admin (Global.authority only) ----
    case('admin-by-authority', 'Global.authority rotates admin to stranger', base, [set_admin(KEY['stranger'])])
    case('admin-by-admin', 'current admin tries to rotate admin', base, [set_admin(KEY['stranger'], 'admin')], ['admin'])
    case('admin-by-stranger', 'stranger tries to rotate admin', base, [set_admin(KEY['stranger'], 'stranger')],
         ['stranger'])
    case('admin-to-default', 'Global.authority sets admin to the default key', base, [set_admin(SYSTEM)])
    case('admin-qc-absent', 'quote-control account does not exist', None, [set_admin(KEY['stranger'])])
    # ---- set_quote_control_reserves_admin (admin or Global.authority) ----
    case('resadmin-by-authority', 'Global.authority sets reserves admin', base,
         [set_reserves_admin(KEY['stranger'])])
    case('resadmin-by-admin', 'admin sets reserves admin', base, [set_reserves_admin(KEY['stranger'], 'admin')],
         ['admin'])
    case('resadmin-by-reserves-admin', 'reserves admin tries to rotate itself', base,
         [set_reserves_admin(KEY['stranger'], 'reserves')], ['reserves'])
    case('resadmin-by-stranger', 'stranger', base, [set_reserves_admin(KEY['stranger'], 'stranger')], ['stranger'])
    # ---- add_quote_control_mint ----
    case('add-by-admin', 'admin adds a 4th mint', base, [add(NEW)], ['admin'])
    case('add-by-authority', 'Global.authority adds a 4th mint', base, [add(NEW, who='authority')])
    case('add-by-reserves-admin', 'reserves admin tries to add', base, [add(NEW, who='reserves')], ['reserves'])
    case('add-default-key', 'mint = default key', base, [add(SYSTEM)], ['admin'])
    case('add-wsol', 'mint = native mint (SPL Token)', base, [add(WSOL)], ['admin'])
    case('add-wsol-2022', 'mint = native mint (Token-2022)', base, [add(WSOL22)], ['admin'])
    case('add-duplicate', 'mint already listed (entry 2)', base, [add(mint_key(2))], ['admin'])
    case('add-reserves-zero', 'initial reserves 0', base, [add(NEW, 0)], ['admin'])
    case('add-reserves-u64max', 'initial reserves u64::MAX', base, [add(NEW, U64)], ['admin'])
    case('add-into-empty-after-init', 'initialize, then Global.authority adds (admin still default)', None,
         [init(), add(NEW, who='authority')])
    case('add-50th', '49 entries in 2,108 bytes: 50th fits without realloc', qc_data(entries=entries(49)),
         [add(NEW)], ['admin'])
    case('add-51st-realloc', '50 entries (full): realloc to 2,148 bytes, admin pays rent difference 278,400',
         qc_data(entries=entries(50)), [add(NEW)], ['admin'])
    case('add-51st-prefunded', '50 entries, account already funded for 2,148 bytes: no transfer',
         None, [add(NEW)], ['admin'], extra=[acct(QC, rent(QC_BASE + 51 * ENTRY), PROGRAM, qc_data(entries=entries(50)))])
    case('add-51st-admin-short', '50 entries; admin holds 278,399 lamports (one short of the rent difference)',
         qc_data(entries=entries(50)), [add(NEW)], ['admin'], lamports=278_399)
    case('add-51st-authority-readonly', '50 entries; authority passed read-only', qc_data(entries=entries(50)),
         [add(NEW, writable=False)], ['admin'])
    case('add-no-realloc-readonly', '3 entries (no realloc needed); authority passed read-only', base,
         [add(NEW, writable=False)], ['admin'])
    case('add-256th', '255 entries: 256th accepted (10,348 bytes)', qc_data(entries=entries(255)), [add(NEW)], ['admin'])
    case('add-257th', '256 entries: list full', qc_data(entries=entries(256)), [add(NEW)], ['admin'])
    case('add-into-oversized', '3 entries in a 4,000-byte account: no realloc, no transfer',
         qc_data(entries=entries(3), length=4000), [add(NEW)], ['admin'])
    case('add-five-in-one-tx', '48 entries; add five mints in one transaction (crosses 50)',
         qc_data(entries=entries(48)), [add(mint_key(900 + i)) for i in range(5)], ['admin'])
    # ---- remove_quote_control_mint ----
    case('remove-middle', 'remove entry 1 of 3 (order of the rest kept)', base, [remove(mint_key(1))], ['admin'])
    case('remove-last', 'remove entry 2 of 3', base, [remove(mint_key(2))], ['admin'])
    case('remove-absent', 'mint not listed', base, [remove(NEW)], ['admin'])
    case('remove-default', 'mint = default key', base, [remove(SYSTEM)], ['admin'])
    case('remove-empty', 'remove from an empty list', qc_data(), [remove(NEW)], ['admin'])
    case('remove-from-grown', '51 entries in 2,148 bytes: remove one (account length kept)',
         qc_data(entries=entries(51)), [remove(mint_key(0))], ['admin'])
    case('remove-by-stranger', 'stranger', base, [remove(mint_key(0), 'stranger')], ['stranger'])
    case('remove-by-authority', 'Global.authority removes', base, [remove(mint_key(0), 'authority')])
    # ---- set_quote_control_mint_reserves ----
    case('reserves-by-reserves-admin', 'reserves admin sets entry 1 to 5,555', base,
         [set_reserves(mint_key(1), 5_555)], ['reserves'])
    case('reserves-by-admin', 'admin sets entry 1', base, [set_reserves(mint_key(1), 5_555, 'admin')], ['admin'])
    case('reserves-by-authority', 'Global.authority sets entry 1', base,
         [set_reserves(mint_key(1), 5_555, 'authority')])
    case('reserves-by-stranger', 'stranger', base, [set_reserves(mint_key(1), 5_555, 'stranger')], ['stranger'])
    case('reserves-absent-mint', 'mint not listed', base, [set_reserves(NEW, 5_555)], ['reserves'])
    case('reserves-u64max-then-zero', 'set u64::MAX, then 0 (event carries the old value)', base,
         [set_reserves(mint_key(0), U64), set_reserves(mint_key(0), 0)], ['reserves'])
    case('reserves-duplicate-entries', 'synthetic list with the same mint twice: first entry updated',
         qc_data(entries=[(NEW, 1), (mint_key(0), 2), (NEW, 3)]), [set_reserves(NEW, 7)], ['reserves'])
    # ---- corrupt accounts ----
    case('qc-count-exceeds-data', 'count field 51 in a 2,108-byte account', qc_data(entries=entries(3), count=51),
         [set_reserves(mint_key(0), 9)], ['reserves'])
    case('qc-short-header', 'account 107 bytes', qc_data(length=107), [set_admin(KEY['stranger'])])
    case('qc-wrong-owner', 'quote-control data owned by System', None, [set_admin(KEY['stranger'])],
         extra=[acct(QC, rent(QC_INIT_LEN), SYSTEM, base)])
    # ---- sequences ----
    case('seq-rotate-then-old-admin-adds', 'Global.authority moves admin to stranger; old admin adds', base,
         [set_admin(KEY['stranger']), add(NEW)], ['admin'])
    case('seq-rotate-then-new-admin-adds', 'Global.authority moves admin to stranger; stranger adds', base,
         [set_admin(KEY['stranger']), add(NEW, who='stranger')], ['stranger'])
    case('seq-add-remove-add', 'add, remove, add the same mint', base, [add(NEW), remove(NEW), add(NEW, 2)], ['admin'])
    case('seq-admin-sets-reserves-admin-then-reserves', 'admin hands reserves role to stranger, stranger sets reserves',
         base, [set_reserves_admin(KEY['stranger'], 'admin'), set_reserves(mint_key(0), 42, 'stranger')],
         ['admin', 'stranger'])
    case('seq-init-full-lifecycle', 'init; authority sets admin and reserves admin; admin adds; reserves admin sets',
         None, [init(), set_admin(KEY['admin']), set_reserves_admin(KEY['reserves']), add(NEW, 10),
                set_reserves(NEW, 20)], ['admin', 'reserves'])
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
    signers = [payer] + [Keypair.from_seed(bytes.fromhex(s)) for s in c['signer_seeds']]
    tx = Transaction.new_signed_with_payer(ixs, payer.pubkey(), signers, vm.latest_blockhash())
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


def qc_view(c, r):
    if r is None:
        b = next((a for a in c['accounts'] if a[0] == str(QC)), None)
        lam = b[1] if b else 0
        q = decode_qc(b[3]) if b else None
    else:
        a = r['accounts_after'].get(str(QC))
        lam = a[0] if a else 0
        q = decode_qc(a[3]) if a else None
    if q is None:
        return None
    names = {str(v): k for k, v in KEY.items()}
    names[str(SYSTEM)] = 'default'
    short = lambda m: 'NEW' if m == str(NEW) else (f'm{struct.unpack("<H", bytes(Pubkey.from_string(m))[:2])[0] - 1}'
                                                   if bytes(Pubkey.from_string(m))[2:] == bytes([100]) * 30 else m)
    view = {'len': q['len'], 'lamports': lam, 'admin': names.get(q['admin'], q['admin']),
            'reserves_admin': names.get(q['reserves_admin'], q['reserves_admin']), 'count': q['count']}
    if q['count'] <= 6:
        view['entries'] = [[short(m), v] for m, v in q['entries']]
    else:
        view['entries'] = f"{q['count']} entries, last {short(q['entries'][-1][0])}={q['entries'][-1][1]}" \
            if q['entries'] else f"{q['count']} (beyond data)"
    return view


def summarize(cases, original, candidate):
    rows = []
    for c, ro, rc in zip(cases, original, candidate):
        row = {'case': c['case'], 'note': c['note'],
               'outcome': {'original': outcome(ro).replace('ok:paid', 'ok'), 'candidate': outcome(rc).replace('ok:paid', 'ok')},
               'events': {'original': len(ro['events']), 'candidate': len(rc['events'])},
               'quote_control_before': qc_view(c, None),
               'quote_control_after': {'original': qc_view(c, ro), 'candidate': qc_view(c, rc)},
               'compute_units': {'original': ro['compute_units'], 'candidate': rc['compute_units'],
                                 'original_minus_candidate': ro['compute_units'] - rc['compute_units']},
               'logs_equal': ro['logs'] == rc['logs'],
               'differing_log_lines': classify_logs(ro['logs'], rc['logs']),
               'behavior_differences': [k for k in BEHAVIOR if ro[k] != rc[k]]}
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
    assert (acc['QuoteControl'], acc['Global']) == (QC_DISC, GLOBAL_DISC)
    cases = plan()
    assert len(cases) <= 60 and len({c['case'] for c in cases}) == len(cases)
    blobs = {n: Path(images[n]).read_bytes() for n in ('original', 'candidate')}
    runtime = args.out / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*'):
        old.unlink()
    write_gz(runtime / 'plan.json.gz', json.dumps(cases, sort_keys=True, indent=0) + '\n')
    report = {'scope': 'Pump Main quote-control administration (initialize, admin / reserves-admin rotation, add / '
                       'remove mint, mint reserves): roles, eligibility, growth and rent, corrupt accounts, '
                       'sequences; original vs rebuild; upgradeable loader; synthetic state; no network.',
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
