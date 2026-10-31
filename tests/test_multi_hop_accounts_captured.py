"""Captured-program checks for the accounts of `multi_hop_curve_swap`.

The routes of `tests/test_multi_hop_route_captured.py`, each with conditions put
on the accounts: the wrong owner, address or data, a missing signer or writable
flag, short curves, curves that need rent. Every case runs on the captured
`evidence/original/pump/deployed.so` (upgradeable loader) under LiteSVM with the
pinned ELFs of that test and on
`programs/pump/recovered/multi_hop_accounts_host.rs`. Pairs of conditions settle
which check fires first. A failure must give the model's error and restore every
account; a success must match all that the route test compares. Account state is
synthetic (IDL layouts). Token-2022 is not used. This shows matching behavior on
these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import itertools
import random
import re
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_multi_hop_route_captured as base

ELF_SHA256 = {base.PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
              base.TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697'}
HOST_SOURCE = base.ROOT / 'programs/pump/recovered/multi_hop_accounts_host.rs'
A, B, C, Q, TOKEN, SYSTEM, MINTS, USER = base.A, base.B, base.C, base.Q, base.TOKEN, base.SYSTEM, base.MINTS, base.USER
PAYER = Keypair.from_seed(bytes([201]) * 32)
OTHER = Keypair.from_seed(bytes([202]) * 32)
STRANGE_OWNER = Pubkey.from_bytes(bytes([203]) * 32)
SIGNATURE_FEE = 5_000
NAMED = dict(global_=0, fee=1, amm=2, user=3, authority=4, source=5, destination=6, recipient=7, token=8, token22=9, system=10,
             event=11, program=12)
HOP = dict(base_mint=0, quote_mint=1, curve=2, base_vault=3, quote_vault=4)
NAMED_FAULTS = [f'{kind}:{field}' for field in ('global_', 'fee') for kind in ('addr', 'owner', 'disc', 'empty', 'tiny', 'cut')]
NAMED_FAULTS += ['bump:fee', 'addr:amm', 'nosign:amm', 'ro:user', 'nosign:user', 'unauth:authority']
NAMED_FAULTS += [f'{kind}:{field}' for field in ('source', 'destination') for kind in ('owner', 'sys', 'empty', 'short', 'ro')]
NAMED_FAULTS += ['ro:recipient', 'prog:token', 'prog:token22', 'prog:system', 'addr:event', 'prog:program']
HOP_FAULTS = [f'{kind}:{field}' for field in ('base_mint', 'quote_mint') for kind in ('addr', 'owner', 'empty', 'short')]
HOP_FAULTS += ['addr:curve', 'owner:curve', 'disc:curve', 'tiny:curve', 'ro:curve']
HOP_FAULTS += ['addr:base_vault', 'owner:base_vault', 'sys:base_vault', 'empty:base_vault', 'short:base_vault', 'ro:base_vault']
HOP_FAULTS += ['addr:quote_vault', 'ro:quote_vault', 'sys:quote_vault', 'owner:quote_vault', 'cut:quote_vault', 'tdmint:quote_vault']
HOP_FAULTS += ['owner:recipient', 'sys:recipient', 'short:recipient', 'empty:recipient', 'tdmint:recipient', 'tdzero:recipient', 'tdowner:recipient',
               'stranger:recipient', 'addr:recipient']
UNCHECKED = ['addr:source', 'addr:destination', 'tdowner:destination', 'nosign:authority']
LATE = ['other:authority', 'tdowner:base_vault', 'tdowner:quote_vault']
SAME_ACCOUNT_KINDS = {'owner', 'addr', 'ro', 'nosign', 'prog'}
SINGLE, SINGLE_OK, PAIRS, ROUTE, RENT, RENT_OK, RANDOM_OK = 1017, 133, 6408, 2040, 672, 327, 331
SINGLE_OUTCOMES = ['error:2000', 'error:2006', 'error:3001', 'error:3002', 'error:3003', 'error:3007', 'error:3008', 'error:3010', 'error:3012',
                   'error:4', 'error:6004', 'error:6010', 'error:6057', 'error:6062', 'error:invalid-data', 'ok']
RENT_OUTCOMES = ['error:1', 'error:2000', 'error:2006', 'error:6004', 'error:6005', 'error:6024', 'error:6094', 'error:6108', 'error:invalid-data', 'ok']


def apply_fault(fault, state, metas, tx, r):
    name, hop = fault
    kind, _, field = name.partition(':')
    index = NAMED[field] if field in NAMED else 13 + 5 * hop + HOP[field]
    key = metas[index][0]
    if kind == 'owner':
        state[key][1] = STRANGE_OWNER
    elif kind == 'sys':
        state[key][1] = SYSTEM
    elif kind == 'disc':
        state[key][2] = bytes([state[key][2][0] ^ 1]) + state[key][2][1:]
    elif kind == 'empty':
        state[key][2] = b''
    elif kind == 'tiny':
        state[key][2] = state[key][2][:7]
    elif kind == 'short':
        state[key][2] = state[key][2][:40]
    elif kind == 'cut':
        state[key][2] = state[key][2][:100]
    elif kind == 'bump':
        state[key][2] = state[key][2][:8] + bytes([state[key][2][8] ^ 1]) + state[key][2][9:]
    elif kind == 'addr':
        stray = Pubkey.from_bytes(hashlib.sha256(name.encode() + bytes([hop])).digest())
        state[stray] = list(state.get(key, [10**9, SYSTEM, b'']))
        metas[index][0] = stray
    elif kind == 'ro':
        metas[index][2] = False
        if field == 'user':
            metas[4][2] = False
            tx.update(payer=PAYER.pubkey(), signers=[PAYER, USER])
    elif kind == 'nosign':
        metas[index][1] = False
        if field == 'user':
            metas[4][1] = False
            tx.update(payer=PAYER.pubkey(), signers=[PAYER])
    elif kind == 'prog':
        stray = base.pda([b'stray', field.encode()])
        state[stray] = [10**9, SYSTEM, b'']
        metas[index][0] = stray
    elif kind == 'unauth':
        metas[index] = [OTHER.pubkey(), False, False]
    elif kind == 'other':
        metas[index] = [OTHER.pubkey(), True, False]
        tx['signers'] = tx['signers'] + [OTHER]
    elif kind == 'tdmint':
        state[key][2] = bytes(MINTS[C]) + state[key][2][32:]
    elif kind == 'tdowner':
        state[key][2] = state[key][2][:32] + bytes(OTHER.pubkey()) + state[key][2][64:]
    elif kind == 'tdzero':
        state[key][2] = state[key][2][:32] + bytes(32) + state[key][2][64:]
    elif kind == 'stranger':
        stray = base.ata(OTHER.pubkey(), MINTS[r['recipient']])
        state[stray] = [state[key][0], TOKEN, state[key][2][:32] + bytes(OTHER.pubkey()) + state[key][2][64:]]
        metas[index][0] = stray
    else:
        raise ValueError(fault)


def curve_lamports(c):
    return c.get('lamports', base.CURVE_RENT + (c['rqr'] + c['cf'] + c['pf'] if c['quote'] == 0 else 0))


class Vm:
    """One VM for all cases, cleared of the last case's accounts."""

    def __init__(self):
        pump, token = base.captured_program_bytes()
        self.vm = LiteSVM().with_transaction_history(0).with_sigverify(False)
        programdata = base.pda([bytes(base.PUMP)], base.UPGRADEABLE)
        self.vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + pump, base.UPGRADEABLE, False))
        self.vm.set_account(base.PUMP, Account(10**9, struct.pack('<I', 2) + bytes(programdata), base.UPGRADEABLE, True))
        self.vm.add_program(TOKEN, token)
        self.vm.set_clock(Clock(1000, 0, 0, 0, base.TS))
        self.keys = set()

    def run(self, r, faults):
        vm = self.vm
        for key in self.keys:
            vm.set_account(key, Account(0, b'', SYSTEM))
        vm.expire_blockhash()
        user = USER.pubkey()
        user_lamports = r.get('user_lamports', base.USER_LAMPORTS)
        state = {base.GLOBAL: [10**9, base.PUMP, base.global_data(r)], base.FEE_CONFIG: [10**9, base.FEES, base.fee_config_data()],
                 user: [user_lamports, SYSTEM, b''], PAYER.pubkey(): [10**10, SYSTEM, b''], OTHER.pubkey(): [10**10, SYSTEM, b'']}
        for i, m in enumerate(MINTS):
            state[m] = [10**9, TOKEN, base.mint_data(base.SUPPLY, 9 if i == 0 else 6)]
        for c in r['curves']:
            key = base.curve_key(c)
            size = c.get('size', 166)
            state[key] = [curve_lamports(c), base.PUMP, base.curve_data(c).ljust(size, b'\0')[:size]]
            state[base.ata(key, MINTS[c['base']])] = [10**9, TOKEN, base.token_data(MINTS[c['base']], key, c['base_vault'])]
            vault = base.token_data(base.WSOL, key, 0, base.TOKEN_RENT) if c['quote'] == 0 else base.token_data(MINTS[c['quote']], key, c['quote_vault'])
            state[base.ata(key, MINTS[c['quote']])] = [base.TOKEN_RENT, TOKEN, vault]

        def user_ata(mint_id, amount):
            key = base.ata(user, MINTS[mint_id])
            data = base.token_data(base.WSOL, user, amount, base.TOKEN_RENT) if mint_id == 0 else base.token_data(MINTS[mint_id], user, amount)
            state[key] = [base.TOKEN_RENT + (amount if mint_id == 0 else 0), TOKEN, data]
            return key

        source = user_ata(r['source'], r['source_balance'])
        if r['destination'] != r['source']:
            user_ata(r['destination'], 0)
        recipient = base.ata(base.BUYBACK, MINTS[r['recipient']])
        state[recipient] = [base.TOKEN_RENT, TOKEN, base.token_data(base.WSOL, base.BUYBACK, 0, base.TOKEN_RENT) if r['recipient'] == 0
                            else base.token_data(MINTS[r['recipient']], base.BUYBACK, 0)]
        metas = [[base.GLOBAL, False, False], [base.FEE_CONFIG, False, False], [base.AMM_CONFIG, True, False], [user, True, True], [user, True, False],
                 [source, False, True], [base.ata(user, MINTS[r['destination']]), False, True], [recipient, False, True], [TOKEN, False, False],
                 [base.TOKEN22, False, False], [SYSTEM, False, False], [base.pda([b'__event_authority']), False, False], [base.PUMP, False, False]]
        for i in r['hops']:
            c = r['curves'][i]
            key = base.curve_key(c)
            for j, k in enumerate([MINTS[c['base']], MINTS[c['quote']], key, base.ata(key, MINTS[c['base']]), base.ata(key, MINTS[c['quote']])]):
                metas.append([k, False, j >= 2])
        tx = dict(payer=user, signers=[USER])
        for fault in faults:
            apply_fault(fault, state, metas, tx, r)
        metas = metas[:13 + r['remaining']]
        self.keys = set(state)
        for key, (lamports, owner, data) in state.items():
            vm.set_account(key, Account(lamports, data, owner))
        data = bytes(base.SWAP['discriminator']) + struct.pack('<QI', r['amount'], len(r['flags'])) + bytes(r['flags'])
        message = Message.new_with_blockhash([set_compute_unit_limit(1_400_000), Instruction(base.PUMP, data, [AccountMeta(*m) for m in metas])],
                                             tx['payer'], vm.latest_blockhash())
        transaction = Transaction.new_unsigned(message)
        wanted = {str(m[0]) for m in metas if m[1]} | {str(tx['payer'])}
        transaction.partial_sign([k for k in tx['signers'] if str(k.pubkey()) in wanted], vm.latest_blockhash())
        paid = SIGNATURE_FEE * message.header.num_required_signatures
        result = vm.send_transaction(transaction)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        lamports_of = lambda key: getattr(vm.get_account(key), 'lamports', 0)
        amount = lambda key: int.from_bytes(bytes(vm.get_account(key).data)[64:72], 'little')
        rollback_errors = []
        if failed:
            for key, (lamports, owner, data) in state.items():
                after = vm.get_account(key)
                expected = lamports - paid if key == tx['payer'] else lamports
                if after is None or after.lamports != expected or after.owner != owner or bytes(after.data) != data:
                    rollback_errors.append(str(key))
            return dict(error=str(result.err()), rollback_errors=rollback_errors)
        curves = []
        for c in r['curves']:
            key = base.curve_key(c)
            a = vm.get_account(key)
            curves.append(dict(data=bytes(a.data), lamports=a.lamports - state[key][0], base_vault=amount(base.ata(key, MINTS[c['base']])),
                               quote_vault=amount(base.ata(key, MINTS[c['quote']]))))
        return dict(error=None, curves=curves, returned=bytes(meta.return_data().data), rollback_errors=[],
                    source=amount(metas[5][0]) - r['source_balance'], destination=amount(metas[6][0]),
                    recipient=lamports_of(metas[7][0]) - base.TOKEN_RENT if r['recipient'] == 0 else amount(metas[7][0]),
                    user_lamports=lamports_of(USER.pubkey()) - user_lamports + paid - base.TX_FEE)


def hop_slots(r):
    """The key of each (field, hop) of the route."""
    slots = {}
    for hop, i in enumerate(r['hops'][:r['remaining'] // 5]):
        c = r['curves'][i]
        key = base.curve_key(c)
        slots.update({('base_mint', hop): MINTS[c['base']], ('quote_mint', hop): MINTS[c['quote']], ('curve', hop): key,
                      ('base_vault', hop): base.ata(key, MINTS[c['base']]), ('quote_vault', hop): base.ata(key, MINTS[c['quote']])})
    return slots


def as_seen(r, faults):
    """A fault on an account is seen in every place the route uses that account.

    The recipient is one account for all hops. A wrong address replaces one slot
    only, and a read-only slot stays writable if the key is writable elsewhere.
    """
    slots = hop_slots(r)
    seen = []
    for name, hop in faults:
        kind, _, field = name.partition(':')
        if field in ('source', 'destination') and kind == 'ro' and r['source'] == r['destination']:
            continue
        if field == 'recipient':
            seen += [(name, h) for h in range(len(r['hops']))]
        elif field not in HOP or kind == 'addr' or (field, hop) not in slots:
            seen.append((name, hop))
        else:
            same = [slot for slot, key in slots.items() if key == slots[(field, hop)]]
            if kind == 'ro':
                seen += [(name, hop)] if len(same) == 1 else []
            else:
                seen += [(f'{kind}:{f}', h) for f, h in same]
    return seen


def host_line(r, faults):
    named = ','.join(f'{name}:{hop}' for name, hop in as_seen(r, faults)) or '-'
    curves = ','.join(f"{c.get('size', 166)}:{curve_lamports(c)}" for c in r['curves'])
    return f"{base.host_line(r)};{named};{curves};{r.get('user_lamports', base.USER_LAMPORTS)}"


_HOST = None


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'multi_hop_accounts_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def model(cases):
    text = ''.join(host_line(r, faults) + '\n' for _, r, faults in cases)
    answers = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    if len(answers) != len(cases):
        raise ValueError(f'host returned {len(answers)} answers for {len(cases)} cases')
    return answers


def as_read(c):
    """The curve bytes a hop writes back: what it could not read is zero."""
    size = c.get('size', 166)
    read = dict(c)
    if size < 81:
        read['creator'] = 0
    if size < 82:
        read['mayhem'] = 0
    if size < 83:
        read['cashback'] = 0
    if size < 141:
        read.update(cf=0, pf=0)
    return read


def check(r, got, answer):
    """List mismatches between one model answer and one captured run."""
    if answer.startswith('error:'):
        code = answer.removeprefix('error:')
        captured = re.search(r'Custom\(([0-9]+)\)', got['error'] or '')
        if code == 'invalid-data':
            bad = [] if got['error'] and 'InvalidAccountData' in got['error'] else [f"error {got['error']} != {code}"]
        else:
            bad = [] if captured and captured.group(1) == code else [f"error {got['error']} != {code}"]
        if got['rollback_errors']:
            bad.append('failed transaction did not restore every seeded account')
        return bad
    if got['error'] is not None:
        return [f"captured failed with {got['error']}"]
    trimmed = []
    for c, g in zip(r['curves'], got['curves']):
        size = max(166, c.get('size', 166))
        if len(g['data']) != size or any(g['data'][166:]):
            return [f"curve {c['base']} length {len(g['data'])} != {size}"]
        trimmed.append(dict(g, data=g['data'][:166]))
    return base.check(dict(r, curves=[as_read(c) for c in r['curves']]), dict(got, curves=trimmed), answer)


def spl(**k):
    return base.route([base.curve(A, Q), base.curve(B, Q)], [0, 1], source=A, destination=B, **k)


def native(**k):
    return base.route([base.curve(A, 0), base.curve(B, 0)], [0, 1], source=A, destination=B, **k)


def spl_buy_sell(**k):
    return base.route([base.curve(A, Q), base.curve(B, A, vqr=10**12, vtr=10**12, rtr=5 * 10**11, rqr=10**9, quote_vault=10**9)], [0, 1],
                      source=Q, destination=B, recipient=Q, **k)


def native_buy(**k):
    return base.route([base.curve(A, 0)], [0, 0], source=0, destination=0, **k)


def single_cases():
    out = []
    shapes = dict(spl=spl, native=native, chain=spl_buy_sell)
    for (label, shape), flags in itertools.product(shapes.items(), ((0, 0), (1, 1), (3, 3))):
        for fault in NAMED_FAULTS + UNCHECKED + ['other:authority']:
            out.append((f'{label}-{flags}-{fault}', shape(flags=flags), [(fault, 0)]))
        for fault, hop in itertools.product(HOP_FAULTS + ['tdowner:base_vault', 'tdowner:quote_vault'], (0, 1)):
            out.append((f'{label}-{flags}-{fault}-{hop}', shape(flags=flags), [(fault, hop)]))
    for flags in ((0, 0), (1, 1), (3, 3)):
        for fault in ['other:authority', 'tdowner:quote_vault', 'tdowner:base_vault']:
            out.append((f'trip-{flags}-{fault}', native_buy(flags=flags), [(fault, 0)]))
            out.append((f'spl-trip-{flags}-{fault}', base.route([base.curve(A, Q)], [0, 0], source=Q, destination=Q, flags=flags), [(fault, 0)]))
    return out


def pair_allowed(one, two):
    kind1, field1 = one[0].split(':')
    kind2, field2 = two[0].split(':')
    if field1 != field2 or (one[1] != two[1] and field1 != 'recipient' and 'addr' not in (kind1, kind2)):
        return True
    # A wrong address on one hop hides the other hop's fault on the shared key.
    if one[1] != two[1] and field1 != 'recipient':
        return False
    if kind1 == kind2 or {kind1, kind2} == {'owner', 'sys'}:
        return False
    return kind1 in SAME_ACCOUNT_KINDS and kind2 in SAME_ACCOUNT_KINDS


def pair_cases():
    every = [(f, 0) for f in NAMED_FAULTS] + [(f, h) for f in HOP_FAULTS for h in (0, 1)]
    out = []
    for i, (one, two) in enumerate(itertools.combinations(every, 2)):
        if pair_allowed(one, two):
            out.append((f'spl-{one}-{two}', spl(flags=(1, 1)), [one, two]))
            if i % 3 == 0:
                out.append((f'native-{two}-{one}', native(flags=(1, 1)), [two, one]))
    return out


def route_cases():
    """An account fault on one hop against a refusal by the route or a curve."""
    out = []
    faults = [(f, 0) for f in NAMED_FAULTS] + [(f, h) for f in HOP_FAULTS for h in (0, 1)]
    make = dict(amount_zero=lambda s: s(amount=0), remaining=lambda s: s(remaining=9), flag_count=lambda s: s(flags=(0,)), flag_value=lambda s: s(flags=(0, 4)))
    for (label, change), (shape, build), fault in itertools.product(make.items(), dict(spl=spl, native=native).items(), faults):
        out.append((f'{label}-{shape}-{fault}', change(build), [fault]))

    def with_curve(q, hop, **flags):
        curves = [base.curve(A, q), base.curve(B, q)]
        curves[hop].update(flags)
        return base.route(curves, [0, 1], source=A, destination=B, flags=(3, 3))
    for q, hop, state in itertools.product((0, Q), (0, 1), (dict(complete=1), dict(mayhem=1), dict(cashback=1))):
        for fault in faults:
            out.append((f'{q}-{hop}-{sorted(state)}-{fault}', with_curve(q, hop, **state), [fault]))
    return out


def rent_cases():
    out = []
    add = lambda label, r, faults=(): out.append((label, r, list(faults)))
    lamports = lambda q, **k: base.CURVE_RENT + (k.get('rqr', 10**11) + k.get('cf', 0) + k.get('pf', 0) if q == 0 else 0)
    for q, size in itertools.product((0, Q), (8, 48, 49, 50, 80, 81, 82, 83, 84, 114, 115, 116, 124, 125, 132, 133, 140, 141, 149, 150, 157, 158, 165, 166, 167, 200, 400)):
        for flags in ((0, 0), (3, 3)):
            base_keys = dict(size=size, cf=7, pf=9)
            curves = [base.curve(A, q, **base_keys), base.curve(B, q)]
            add(f'size-{q}-{size}-{flags}', base.route(curves, [0, 1], source=A, destination=B, flags=flags))
            for over in (dict(mayhem=1), dict(cashback=1), dict(complete=1)):
                curves = [base.curve(A, q, **dict(base_keys, **over)), base.curve(B, q)]
                add(f'size-{q}-{size}-{flags}-{sorted(over)}', base.route(curves, [0, 1], source=A, destination=B, flags=flags))
            add(f'size-trip-{q}-{size}-{flags}', base.route([base.curve(A, q, size=size)], [0, 0], source=q, destination=q, flags=flags))
    for q, short, flags in itertools.product((0, Q), (1, 10, 2_046_239), ((0, 0), (1, 1), (3, 3))):
        for hop in (0, 1):
            curves = [base.curve(A, q), base.curve(B, q)]
            curves[hop]['lamports'] = lamports(q) - short
            add(f'short-{q}-{short}-{flags}-{hop}', base.route(curves, [0, 1], source=A, destination=B, flags=flags))
        add(f'short-both-{q}-{short}-{flags}', base.route([base.curve(A, q, lamports=lamports(q) - short), base.curve(B, q, lamports=lamports(q) - short)],
                                                          [0, 1], source=A, destination=B, flags=flags))
        add(f'short-trip-{q}-{short}-{flags}', base.route([base.curve(A, q, lamports=lamports(q) - short)], [0, 0], source=q, destination=q, flags=flags))
        add(f'short-buy-{q}-{short}-{flags[:1]}', base.route([base.curve(A, q, lamports=lamports(q) - short)], [0], source=q, destination=A, flags=flags[:1]))
    for extra in (0, 1, 10**9):
        for q in (0, Q):
            add(f'rich-{q}-{extra}', base.route([base.curve(A, q, lamports=lamports(q) + extra), base.curve(B, q)], [0, 1], source=A, destination=B))
    add('fee-buckets-counted', base.route([base.curve(A, 0, cf=5, pf=6, lamports=base.CURVE_RENT + 10**11), base.curve(B, 0)], [0, 1], source=A, destination=B))
    add('owed-overflow', base.route([base.curve(A, 0, rqr=base.U64, lamports=1)], [0], source=0, destination=A))
    add('owed-overflow-cf', base.route([base.curve(A, 0, cf=base.U64, pf=1, lamports=1)], [0], source=A, destination=0))
    add('owed-overflow-pf', base.route([base.curve(A, 0, rqr=1, pf=base.U64, lamports=1)], [0], source=A, destination=0))
    add('owed-overflow-complete', base.route([base.curve(A, 0, cf=base.U64, pf=1, lamports=1, complete=1)], [0], source=A, destination=0))
    add('owed-overflow-mayhem', base.route([base.curve(A, 0, cf=base.U64, pf=1, lamports=1, mayhem=1)], [0], source=A, destination=0))
    add('owed-overflow-late-fault', base.route([base.curve(A, 0, cf=base.U64, pf=1, lamports=1)], [0], source=A, destination=0), [('addr:base_vault', 0)])
    add('owed-overflow-early-fault', base.route([base.curve(A, 0, cf=base.U64, pf=1, lamports=1)], [0], source=A, destination=0), [('ro:curve', 0)])
    add('owed-overflow-second', base.route([base.curve(A, 0), base.curve(B, 0, cf=base.U64, pf=1, lamports=1)], [0, 1], source=A, destination=B))
    add('owed-saturates', base.route([base.curve(A, 0, rqr=10**15, lamports=1)], [0], source=0, destination=A))
    for user in (1_000_000, 2_046_238, 2_046_239 - 1 + 890_880, 2_056_239, 2_056_239 + 890_880, 2_056_239 + 890_879):
        for fault in ((), [('addr:base_vault', 0)], [('ro:base_vault', 0)]):
            add(f'poor-{user}-{len(fault)}-{fault}', base.route([base.curve(A, Q, lamports=1), base.curve(B, Q)], [0, 1], source=A, destination=B, user_lamports=user), fault)
        add(f'poor-complete-{user}', base.route([base.curve(A, Q, lamports=1, complete=1), base.curve(B, Q)], [0, 1], source=A, destination=B, user_lamports=user))
    # The curve grows on the first visit; a second visit pays nothing more.
    add('grow-revisit', base.route([base.curve(A, 0, size=100, lamports=base.CURVE_RENT + 10**11 - 3)], [0, 0], source=A, destination=A, flags=(3, 3)))
    add('grow-revisit-spl', base.route([base.curve(A, Q, size=120, lamports=5)], [0, 0], source=A, destination=A, flags=(3, 3)))
    return out


def random_cases(count=600, seed=20261031):
    rng = random.Random(seed)
    out = []
    sizes = [49, 81, 83, 115, 125, 141, 150, 165, 166, 200]
    every = [(f, 0) for f in NAMED_FAULTS] + [(f, h) for f in HOP_FAULTS for h in (0, 1)]
    for i in range(count):
        q = rng.choice([0, Q])
        whole = i % 2 == 0

        def rand_curve(b):
            c = base.curve(b, q, vqr=rng.randrange(10**9, 10**11), rqr=rng.randrange(10**9, 10**12), cf=rng.randrange(10**6), pf=rng.randrange(10**6),
                           creator=int(rng.random() < .8), size=166 if whole else rng.choice(sizes if q == 0 else sizes[3:]))
            if not whole and rng.random() < .5:
                c['lamports'] = max(0, curve_lamports(c) - rng.choice([1, 10**4, 10**6, 2_046_239]))
            return c
        hops, source, destination = rng.choice([([0, 1], A, B), ([0, 0], q, q), ([0, 1, 1], A, q), ([0], q, A), ([0, 0], A, A)])
        curves = [rand_curve(A), rand_curve(B)][:max(hops) + 1]
        flags = tuple(rng.randrange(4) for _ in hops)
        r = base.route(curves, hops, amount=rng.randrange(1, 10**10), flags=flags, source=source, destination=destination, buyback_bps=rng.choice([0, 5_000, 10_000]))
        # LiteSVM reports a rent error of its own when a topped-up route fails,
        # so faults go on the routes that need no top-up.
        faults = rng.sample(every, rng.choice([1, 2])) if whole else []
        faults = [f for f in faults if f[1] < len(hops)]
        if len(faults) == 2 and not pair_allowed(*faults):
            faults = faults[:1]
        out.append((f'random-{i}', r, faults))
    return out


class MultiHopAccountsCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            base.read_pinned_elf(path, digest)
        cls.vm = Vm()

    def run_all(self, cases):
        answers = model(cases)
        bad = []
        for (label, r, faults), answer in zip(cases, answers):
            problems = check(r, self.vm.run(r, faults), answer)
            if problems:
                bad.append((label, answer[:40], problems[:2]))
        self.assertEqual(bad[:12], [], f'{len(bad)} of {len(cases)}')
        return answers

    def test_single_faults(self):
        cases = single_cases()
        self.assertEqual(len(cases), SINGLE)
        answers = self.run_all(cases)
        self.assertEqual(sorted({a.split(',')[0] for a in answers}), SINGLE_OUTCOMES)
        self.assertEqual(sum(a.startswith('ok') for a in answers), SINGLE_OK)

    def test_pairs_of_faults(self):
        cases = pair_cases()
        self.assertEqual(len(cases), PAIRS)
        self.run_all(cases)

    def test_route_refusals_against_faults(self):
        cases = route_cases()
        self.assertEqual(len(cases), ROUTE)
        answers = self.run_all(cases)
        for want in ('error:6005', 'error:6020', 'error:6027', 'error:6094', 'error:6106', 'error:6108'):
            self.assertIn(want, answers)

    def test_short_curves_and_rent(self):
        cases = rent_cases()
        self.assertEqual(len(cases), RENT)
        answers = self.run_all(cases)
        self.assertEqual(sorted({a.split(',')[0] for a in answers}), RENT_OUTCOMES)
        self.assertEqual(sum(a.startswith('ok') for a in answers), RENT_OK)

    def test_random_cases(self):
        cases = random_cases()
        self.assertEqual(len(cases), 600)
        answers = self.run_all(cases)
        self.assertEqual(sum(a.startswith('ok') for a in answers), RANDOM_OK)

    def test_elf_pins_refuse_other_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'elf'
            path.write_bytes(b'not the program')
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                base.read_pinned_elf(path, ELF_SHA256[base.PUMP_ELF])

    def test_checker_rejects_wrong_outcomes(self):
        failing = ('fail', spl(), [('ro:curve', 0)])
        passing = ('pass', base.route([base.curve(A, Q, size=120, lamports=5)], [0], source=A, destination=Q), [])
        for (_, r, faults), answer in zip((failing, passing), model([failing, passing])):
            got = self.vm.run(r, faults)
            self.assertEqual(check(r, got, answer), [])
            self.assertNotEqual(check(r, got, 'error:6024'), [])
        got = self.vm.run(*failing[1:])
        self.assertNotEqual(check(failing[1], dict(got, rollback_errors=['seeded account']), 'error:2000'), [])
        self.assertNotEqual(check(failing[1], got, 'error:invalid-data'), [])
        self.assertNotEqual(check(failing[1], got, 'ok'), [])
        bent = self.vm.run(*passing[1:])
        answer = model([passing])[0]
        bent['user_lamports'] += 1
        self.assertNotEqual(check(passing[1], bent, answer), [])
        bent = self.vm.run(*passing[1:])
        bent['curves'][0]['data'] = bent['curves'][0]['data'][:150]
        self.assertNotEqual(check(passing[1], bent, answer), [])
        with self.assertRaisesRegex(ValueError, 'answers for'):
            with patch('subprocess.run', return_value=SimpleNamespace(stdout='')):
                model([failing])


if __name__ == '__main__':
    unittest.main()
