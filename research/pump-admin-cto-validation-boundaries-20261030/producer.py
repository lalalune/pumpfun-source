#!/usr/bin/env python3
"""Pump Main admin_cto (community takeover of a bonding-curve creator): validation layer and
curve-only outcomes, original vs rebuild.

admin_cto (signed by Global.admin_set_creator_authority) replaces a curve's creator, optionally
converting the coin to holder rewards and/or setting creator_fee_bps. Before any value moves,
validate() rejects in this order: mayhem coin (6088); creator change on a holder-reward coin
(6083); holder conversion while Global holder rewards are disabled (6084); new_creator with a
holder conversion (6090) or missing without one (6089); new_creator = default (6030),
holder-rewards PDA or sharing-config PDA (6019); then, if a fee is given: quote-locked curve
(native SOL / whitelisted quote, 6091), cashback coin (6080), Global creator_fee_configurable
off (6077), fee 0 or > Global max (6078). After that the handler requires creator_fee == 0
(6095), collects the old creator's vault, and, when a canonical pump_amm pool or a pump_fees
sharing config exists, CPIs into those programs.

pump_amm and pump_fees are replaced by an in-memory no-op SBPFv0 program (noop_stub below);
no case here has a pool or a sharing config, so every success ends on the curve-only path
("No canonical pump pool for this mint; curve only"). The repository harness
(scripts/pump_admin_cto_differential.py) imports scripts/pump_validate_admin.py, which reads
`research/imported-lab/...config-snapshot.json`, not in the git tree, so it cannot be rerun.

Only the Pump image is loaded (upgradeable loader layout) plus the two stubs; System, SPL Token
and ATA are LiteSVM built-ins. All state is synthetic (Global 1,088 bytes with
admin_set_creator_authority at offset 418, creator_fee_configurable 1045, max fee bps 1046,
holder rewards enabled 1086; BondingCurve 166 bytes), keys come from fixed seeds, the clock is
fixed, there is no network. Every case's accounts and instructions are in runtime/plan.json.gz.

Usage:
  python3 producer.py --root <repo> --images '{"original": "...", "candidate": "..."}' --out <packet dir>
"""
import argparse
import base64
import gzip
import hashlib
import json
import struct
import sys
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
AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
PAYER_SEED = bytes([236]) * 32
PAYER = Keypair.from_seed(PAYER_SEED).pubkey()
START = 1_800_000_000
MINT = Keypair.from_seed(bytes([101]) * 32).pubkey()
CREATOR = Pubkey(bytes([102]) * 32)
NEWC = Pubkey(bytes([103]) * 32)
pda = lambda seeds, program=PROGRAM: Pubkey.find_program_address(seeds, program)[0]
EVENT_AUTHORITY = pda([b'__event_authority'])
GLOBAL = pda([b'global'])
CURVE = pda([b'bonding-curve', bytes(MINT)])
HOLDER = pda([b'holder-rewards', bytes(MINT)])
GLOBAL_DISC = bytes.fromhex('a7e8e8b1c86c727f')
CURVE_DISC = bytes([23, 183, 248, 55, 96, 216, 172, 96])


def rent(n):
    return (128 + n) * 6960


def ata(owner, mint, program=TOKEN):
    return pda([bytes(owner), bytes(program), bytes(mint)], ATA_PROGRAM)


def mint_data(decimals):
    d = bytearray(82)
    struct.pack_into('<Q', d, 36, 10**15)
    d[44] = decimals
    d[45] = 1
    return bytes(d)


def global_data(fee_configurable=1, max_fee=500, holder_enabled=1):
    d = bytearray(1088)
    d[:8] = GLOBAL_DISC
    d[8] = 1
    d[9:41] = bytes(PAYER)
    d[418:450] = bytes(PAYER)
    d[1045] = fee_configurable
    struct.pack_into('<Q', d, 1046, max_fee)
    d[1086] = holder_enabled
    return bytes(d)


def curve_data(creator=CREATOR, mayhem=0, cashback=0, holder=0, creator_fee=0, quote=SYSTEM):
    d = bytearray(166)
    d[:8] = CURVE_DISC
    struct.pack_into('<QQQQQ', d, 8, 10**15, 3 * 10**10, 7 * 10**14, 0, 10**15)
    d[49:81] = bytes(creator)
    d[81] = mayhem
    d[82] = cashback
    d[83:115] = bytes(quote)
    d[124] = holder
    struct.pack_into('<Q', d, 125, creator_fee)
    return bytes(d)


def acct(key, lamports, owner=SYSTEM, data=b''):
    return [str(key), lamports, str(owner), data.hex()]


def opt_bool(v):
    return b'\0' if v is None else b'\1' + bytes([v])


def opt_u64(v):
    return b'\0' if v is None else b'\1' + struct.pack('<Q', v)


def opt_key(v):
    return b'\0' if v is None else b'\1' + bytes(v)


def cto(holder=None, fee=None, new=None, creator=CREATOR, quote=WSOL, tprog=TOKEN):
    vault = pda([b'creator-vault', bytes(creator)])
    pool_auth = pda([b'pool-authority', bytes(MINT)])
    ccva = pda([b'creator_vault', bytes(creator)], AMM)
    keys = [(PAYER, True, True), (GLOBAL, False, False), (MINT, False, False), (quote, False, False),
            (tprog, False, False), (ATA_PROGRAM, False, False), (SYSTEM, False, False), (CURVE, False, True),
            (creator, False, True), (ata(creator, quote, tprog), False, True), (vault, False, True),
            (ata(vault, quote, tprog), False, True), (HOLDER, False, True), (ata(HOLDER, quote, tprog), False, True),
            (AMM, False, False), (pda([b'global_config'], AMM), False, False), (pool_auth, False, False),
            (pda([b'pool', struct.pack('<H', 0), bytes(pool_auth), bytes(MINT), bytes(quote)], AMM), False, True),
            (pda([b'__event_authority'], AMM), False, False), (ccva, False, True), (ata(ccva, quote, tprog), False, True),
            (pda([b'sharing-config', bytes(MINT)], FEES), False, True), (FEES, False, False),
            (pda([b'__event_authority'], FEES), False, False), (EVENT_AUTHORITY, False, False), (PROGRAM, False, False)]
    return {'program': str(PROGRAM), 'data_hex': (bytes.fromhex('7d7ed6864de5bc59') + opt_bool(holder) + opt_u64(fee)
                                                 + opt_key(new)).hex(),
            'metas': [[str(k), s, w] for k, s, w in keys]}


QUOTE = Keypair.from_seed(bytes([104]) * 32).pubkey()
SHARING = pda([b'sharing-config', bytes(MINT)], FEES)
OTHER = Pubkey(bytes([105]) * 32)


def plan():
    cases = []

    def add(name, note, ixs, g=None, c=None, extra=(), drop=()):
        accounts = [acct(PAYER, 10**12), acct(GLOBAL, rent(1088), PROGRAM, g or global_data()),
                    acct(CURVE, rent(166) + 10**9, PROGRAM, c or curve_data()), acct(MINT, 10**9, TOKEN, mint_data(6)),
                    acct(WSOL, 10**9, TOKEN, mint_data(9)), acct(QUOTE, 10**9, TOKEN, mint_data(6)), acct(CREATOR, 10**9)]
        accounts = [a for a in accounts if a[0] not in {str(k) for k in drop}]
        cases.append({'case': name, 'note': note, 'accounts': accounts + list(extra), 'instructions': ixs,
                      'signer_seeds': [], 'unix_timestamp': START})

    V = pda([b'creator-vault', bytes(CREATOR)])
    # ---- native-SOL curve ----
    add('native-new-creator', 'native curve: new_creator NEWC', [cto(new=NEWC)])
    add('native-no-new-creator', 'native curve: no new_creator, not holder', [cto()])
    add('native-new-default', 'new_creator = default key', [cto(new=SYSTEM)])
    add('native-new-holder-pda', 'new_creator = holder-rewards PDA', [cto(new=HOLDER)])
    add('native-new-sharing-pda', 'new_creator = sharing-config PDA', [cto(new=SHARING)])
    add('native-new-same-creator', 'new_creator = current creator', [cto(new=CREATOR)])
    add('mayhem', 'mayhem curve', [cto(new=NEWC)], c=curve_data(mayhem=1))
    add('mayhem-holder', 'mayhem curve, holder conversion', [cto(holder=True)], c=curve_data(mayhem=1))
    add('mayhem-unswept', 'mayhem curve with creator_fee 5 (validate runs first)', [cto(new=NEWC)],
        c=curve_data(mayhem=1, creator_fee=5))
    add('holder-convert', 'is_holder_reward = Some(true)', [cto(holder=True)])
    add('holder-convert-with-new', 'holder conversion with new_creator', [cto(holder=True, new=NEWC)])
    add('holder-false-explicit', 'is_holder_reward = Some(false) with new_creator', [cto(holder=False, new=NEWC)])
    add('holder-curve-new-creator', 'holder-reward curve, new_creator, holder None', [cto(new=NEWC)],
        c=curve_data(holder=1))
    add('holder-curve-reconvert', 'holder-reward curve, holder conversion again', [cto(holder=True)],
        c=curve_data(holder=1))
    add('holder-disabled', 'Global holder rewards disabled, holder conversion', [cto(holder=True)],
        g=global_data(holder_enabled=0))
    add('holder-disabled-holder-curve', 'holder rewards disabled, curve already holder-reward', [cto(holder=True)],
        g=global_data(holder_enabled=0), c=curve_data(holder=1))
    add('native-fee', 'native curve with creator_fee_bps 100 (quote locked)', [cto(new=NEWC, fee=100)])
    add('unswept', 'curve creator_fee 5', [cto(new=NEWC)], c=curve_data(creator_fee=5))
    add('not-authority', 'Global admin_set_creator_authority = OTHER', [cto(new=NEWC)],
        g=global_data()[:418] + bytes(OTHER) + global_data()[450:])
    add('cashback-coin-new', 'cashback curve, new_creator', [cto(new=NEWC)], c=curve_data(cashback=1))
    add('current-creator-mismatch', 'current_creator slot holds OTHER', [cto(new=NEWC, creator=OTHER)],
        extra=[acct(OTHER, 10**9)])
    add('creator-not-writable', 'current_creator passed read-only, vault holds 1,000,000 above rent',
        [dict(cto(new=NEWC), metas=[m if m[0] != str(CREATOR) else [m[0], False, False] for m in cto(new=NEWC)['metas']])],
        extra=[acct(V, 890_880 + 1_000_000)])
    add('creator-absent-vault-funded', 'current creator account absent (0 lamports); vault 1,000,000 above rent(0)',
        [cto(new=NEWC)], extra=[acct(V, 890_880 + 1_000_000)], drop=[CREATOR])
    add('creator-vault-funded', 'vault holds 1,000,000 above rent(0): paid to the old creator', [cto(new=NEWC)],
        extra=[acct(V, 890_880 + 1_000_000)])
    add('curve-creator-default', 'curve creator is the default key', [cto(new=NEWC, creator=SYSTEM)],
        c=curve_data(creator=SYSTEM))
    # ---- token-quote curve (QUOTE, not whitelisted) ----
    tq = curve_data(quote=QUOTE)
    add('tq-fee-100', 'token-quote curve, fee 100', [cto(new=NEWC, fee=100, quote=QUOTE)], c=tq)
    add('tq-fee-0', 'fee 0', [cto(new=NEWC, fee=0, quote=QUOTE)], c=tq)
    add('tq-fee-max', 'fee = Global max 500', [cto(new=NEWC, fee=500, quote=QUOTE)], c=tq)
    add('tq-fee-max-plus-1', 'fee 501', [cto(new=NEWC, fee=501, quote=QUOTE)], c=tq)
    add('tq-fee-not-configurable', 'Global creator_fee_configurable 0', [cto(new=NEWC, fee=100, quote=QUOTE)], c=tq,
        g=global_data(fee_configurable=0))
    add('tq-cashback-fee', 'cashback curve with fee', [cto(new=NEWC, fee=100, quote=QUOTE)],
        c=curve_data(quote=QUOTE, cashback=1))
    add('tq-holder-cashback-fee', 'cashback curve, holder conversion with fee', [cto(holder=True, fee=100, quote=QUOTE)],
        c=curve_data(quote=QUOTE, cashback=1))
    add('tq-quote-mismatch', 'curve quote QUOTE, WSOL passed', [cto(new=NEWC, quote=WSOL)], c=tq)
    add('tq-no-fee', 'token-quote curve, new_creator only', [cto(new=NEWC, quote=QUOTE)], c=tq)
    return cases


IX = {'admin_cto': bytes.fromhex('7d7ed6864de5bc59')}
IX_ACCOUNTS = {'admin_cto': 26}


def insn(op, dst=0, src=0, off=0, imm=0):
    return struct.pack('<BBhi', op, dst | (src << 4), off, imm)


def noop_stub():
    """SBPFv0 ELF: sol_set_return_data(r10, 0); return 0. The single syscall needs an R_BPF_64_32
    relocation (.dynamic/.dynsym/.dynstr/.rel.dyn + PT_DYNAMIC); virtual addresses equal file offsets."""
    text = insn(0xbf, 1, 10) + insn(0xb7, 2, 0, 0, 0) + insn(0x85, 0, 0, 0, -1) + insn(0xb7, 0, 0, 0, 0) + insn(0x95)
    call_offset = 2 * 8
    shnames = [b'', b'.text', b'.dynamic', b'.dynsym', b'.dynstr', b'.rel.dyn', b'.shstrtab']
    shstr = b'\0'.join(shnames) + b'\0'
    name_off = [0]
    for n in shnames[1:]:
        name_off.append(name_off[-1] + len(shnames[len(name_off) - 1]) + 1)
    dynstr = b'\0sol_set_return_data\0'
    dynsym = bytes(24) + struct.pack('<IBBHQQ', 1, 0x10, 0, 0, 0, 0)
    text_off = 64 + 56
    dyn_off = text_off + len(text)
    sym_off = dyn_off + 16 * 7
    str_off = sym_off + len(dynsym)
    rel_off = (str_off + len(dynstr) + 7) & ~7
    shs_off = rel_off + 16
    sh_off = (shs_off + len(shstr) + 7) & ~7
    rel = struct.pack('<QQ', text_off + call_offset, (1 << 32) | 10)
    dynamic = b''.join(struct.pack('<QQ', t, v) for t, v in [
        (17, rel_off), (18, 16), (19, 16), (6, sym_off), (5, str_off), (10, len(dynstr)), (0, 0)])
    ehdr = b'\x7fELF' + bytes([2, 1, 1, 0]) + bytes(8)
    ehdr += struct.pack('<HHIQQQIHHHHHH', 3, 247, 1, text_off, 64, sh_off, 0, 64, 56, 1, 64, 7, 6)
    phdr = struct.pack('<IIQQQQQQ', 2, 6, dyn_off, dyn_off, dyn_off, len(dynamic), len(dynamic), 8)
    body = ehdr + phdr + text + dynamic + dynsym + dynstr
    body += bytes(rel_off - len(body)) + rel + shstr
    body += bytes(sh_off - len(body))

    def sh(i, typ, flags, off, size, link=0, info=0, align=1, entsize=0):
        return struct.pack('<IIQQQQIIQQ', name_off[i], typ, flags, off, off, size, link, info, align, entsize)
    return body + bytes(64) + sh(1, 1, 6, text_off, len(text), align=8) \
        + sh(2, 6, 3, dyn_off, len(dynamic), link=4, align=8, entsize=16) \
        + sh(3, 11, 2, sym_off, len(dynsym), link=4, info=1, align=8, entsize=24) \
        + sh(4, 3, 2, str_off, len(dynstr)) \
        + sh(5, 9, 2, rel_off, 16, link=3, align=8, entsize=16) \
        + struct.pack('<IIQQQQIIQQ', name_off[6], 3, 0, 0, shs_off, len(shstr), 0, 0, 1, 0)


STUB = noop_stub()


# ---- execution (verify.py imports this from the packet copy) ----

LOADERS = ('upgradeable',)


def load_vm(image):
    vm = LiteSVM().with_transaction_history(0).with_sigverify(True)
    elf = Path(image).read_bytes()
    programdata = Pubkey.find_program_address([bytes(PROGRAM)], UPGRADEABLE)[0]
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + elf, UPGRADEABLE, False))
    vm.set_account(PROGRAM, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    vm.add_program(AMM, STUB)
    vm.add_program(FEES, STUB)
    return vm


FIXED = {PROGRAM, TOKEN, TOKEN22, ATA_PROGRAM, SYSTEM, AMM, FEES}
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



def curve_view(c, r):
    if r is None:
        b = next((a for a in c['accounts'] if a[0] == str(CURVE)), None)
        d = bytes.fromhex(b[3]) if b else b''
    else:
        a = r['accounts_after'].get(str(CURVE))
        d = bytes.fromhex(a[3]) if a else b''
    if len(d) < 166:
        return None
    names = {str(CREATOR): 'CREATOR', str(NEWC): 'NEWC', str(HOLDER): 'HOLDER_PDA', str(SYSTEM): 'default'}
    creator = str(Pubkey(d[49:81]))
    return {'creator': names.get(creator, creator), 'mayhem': d[81], 'cashback': d[82],
            'creator_fee_bps': struct.unpack_from('<Q', d, 115)[0], 'can_edit_creator_fee': d[123],
            'is_holder_reward': d[124], 'creator_fee': struct.unpack_from('<Q', d, 125)[0]}


def creator_delta(c, r):
    b = next((a for a in c['accounts'] if a[0] == str(CREATOR)), None)
    return r['accounts_after'].get(str(CREATOR), [0])[0] - (b[1] if b else 0)


def summarize(cases, original, candidate):
    rows = []
    for c, ro, rc in zip(cases, original, candidate):
        row = {'case': c['case'], 'note': c['note'],
               'outcome': {'original': outcome(ro).replace('ok:paid', 'ok'), 'candidate': outcome(rc).replace('ok:paid', 'ok')},
               'events': {'original': len(ro['events']), 'candidate': len(rc['events'])},
               'curve_before': curve_view(c, None),
               'curve_after': {'original': curve_view(c, ro), 'candidate': curve_view(c, rc)},
               'old_creator_lamport_delta': {'original': creator_delta(c, ro), 'candidate': creator_delta(c, rc)},
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
    assert (acc['BondingCurve'], acc['Global']) == (CURVE_DISC, GLOBAL_DISC)
    cases = plan()
    assert len(cases) <= 60 and len({c['case'] for c in cases}) == len(cases)
    blobs = {n: Path(images[n]).read_bytes() for n in ('original', 'candidate')}
    runtime = args.out / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*'):
        old.unlink()
    write_gz(runtime / 'plan.json.gz', json.dumps(cases, sort_keys=True, indent=0) + '\n')
    report = {'scope': 'Pump Main admin_cto: validation order, holder/fee/new-creator rules, curve-only '
                       'outcomes with no-op pump_amm/pump_fees stubs; original vs rebuild; upgradeable '
                       'loader; synthetic state; no network.',
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
