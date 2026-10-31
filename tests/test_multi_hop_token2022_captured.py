"""Captured-program checks for `multi_hop_curve_swap` on Token-2022 mints.

Every case runs Pump `multi_hop_curve_swap` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token and
Token-2022 programs, over routes whose base or quote mints are Token-2022 mints
with extensions. Signature verification is off, as in
`tests/test_multi_hop_route_captured.py`, so the AMM config PDA can sit in a
signer slot. Account state is synthetic (IDL layouts). The same inputs go to
`programs/pump/recovered/multi_hop_token2022_host.rs`, and the error, the bytes
of every curve, every vault balance, the fees withheld on each account, the
user's source and destination, the user's lamports, the buyback recipient and
the returned `CurveRunResult` must agree. Events are not compared. This shows
matching behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import copy
import hashlib
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_multi_hop_route_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = base.PUMP_ELF
TOKEN_ELF = base.TOKEN_ELF
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ELF_SHA256 = dict(base.ELF_SHA256)
ELF_SHA256[TOKEN22_ELF] = '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/multi_hop_token2022_host.rs'

PUMP, FEES, TOKEN, TOKEN22, SYSTEM = base.PUMP, base.FEES, base.TOKEN, base.TOKEN22, base.SYSTEM
USER, BUYBACK, MINTS, TS = base.USER, base.BUYBACK, base.MINTS, base.TS
TOKEN_RENT, USER_LAMPORTS, TX_FEE, U64 = base.TOKEN_RENT, base.USER_LAMPORTS, base.TX_FEE, base.U64
Q, A, B, C = base.Q, base.A, base.B, base.C
FEE_250 = (0, 0, 0, 250, 10**18)
FEE_ALL = (0, 0, 0, 10_000, U64)
FEE_CAP = (0, 0, 0, 500, 1_000)
FEE_EPOCH = (100, 10**18, 5, 700, 10**18)
MINT_DEFAULTS = dict(t22=True, fee=None, hook=False, paused=False, non_transferable=False, malformed=None, extra=())
# Mint extension type -> body, for kinds that do not change a transfer here.
FIXED_COUNT, FIXED_OK, FIXED_WITHHELD, FIXED_CROSSING, RANDOM_OK = 2302, 1086, 679, 129, 317
EXTENSIONS = {3: bytes(32), 4: bytes(65), 12: bytes(32), 16: bytes(64), 18: bytes(64)}


def tlv(kind, body=b''):
    return struct.pack('<HH', kind, len(body)) + body


def ata(owner, mint_id, program):
    return base.pda([bytes(owner), bytes(program), bytes(MINTS[mint_id])], base.ATA)


_FEE_TLV = tlv(1, bytes(108))
_TAG = bytes([1])
# Extension areas the fee reader refuses (a quote mint fails 6063), bytes Anchor
# cannot load as a mint at all, and an unknown extension that passes everywhere.
FEE_REFUSED = {'fee-short': _TAG + tlv(1, bytes(50)), 'fee-over': _TAG + struct.pack('<HH', 1, 108) + bytes(20),
               'other-over': _TAG + struct.pack('<HH', 3, 500) + bytes(20), 'dup-fee': _TAG + _FEE_TLV + _FEE_TLV,
               'trailing-3': _TAG + b'\1\0\0'}
UNREADABLE = {'tag-only': (165, _TAG), 'tag0': (165, b'\0'), 'tag2': (165, b'\2' + tlv(3, bytes(32))),
              'padding': (100, b'\1' + bytes(64) + _TAG + tlv(3, bytes(32))), 'len-100': (100, b''), 'len-170': (170, b''),
              'len-165': (165, b''), 'len-300': (300, b'')}


def mint_spec(r, i):
    return r['mints'].get(i, dict(MINT_DEFAULTS, t22=False))


def program_of(r, i):
    return TOKEN22 if mint_spec(r, i)['t22'] else TOKEN


def mint_data(spec, decimals):
    head = base.mint_data(base.SUPPLY, decimals)
    if not spec['t22']:
        return head
    if spec['malformed'] in FEE_REFUSED:
        return head.ljust(165, b'\0') + FEE_REFUSED[spec['malformed']]
    if spec['malformed'] in UNREADABLE:
        size, tail = UNREADABLE[spec['malformed']]
        return head.ljust(size, b'\0') + tail
    ext = b''
    if spec['fee']:
        older_bps, older_max, newer_epoch, newer_bps, newer_max = spec['fee']
        ext += tlv(1, bytes(64) + struct.pack('<QQQH', 0, 0, older_max, older_bps) + struct.pack('<QQH', newer_epoch, newer_max, newer_bps))
    if spec['hook']:
        ext += tlv(14, bytes(32) + bytes([7]) * 32)
    if spec['paused']:
        ext += tlv(26, bytes(32) + b'\1')
    if spec['non_transferable']:
        ext += tlv(9)
    for kind in spec['extra']:
        ext += tlv(kind, EXTENSIONS[kind])
    if spec['malformed'] == 'unknown':
        ext += tlv(99)
    return head.ljust(165, b'\0') + bytes([1]) + ext if ext else head


def token_data(r, mint_id, owner, amount, frozen=False, bare=False, flags=b''):
    spec = mint_spec(r, mint_id)
    tag, value = (1, TOKEN_RENT) if mint_id == 0 else (0, 0)
    data = bytearray(base.token_data(MINTS[mint_id], owner, amount, value if tag else None))
    data[108] = 2 if frozen else 1
    if not spec['t22']:
        return bytes(data)
    ext = b''
    if spec['fee'] and not bare:
        ext += tlv(2, bytes(8))
    if spec['hook']:
        ext += tlv(15, b'\0')
    ext += flags
    if spec['non_transferable']:
        ext += tlv(13)
    return bytes(data) + bytes([2]) + ext if ext else bytes(data)


def withheld_of(data):
    offset = 166
    while offset + 4 <= len(data):
        kind, length = struct.unpack_from('<HH', data, offset)
        if kind == 0:
            break
        if kind == 2:
            return struct.unpack_from('<Q', data, offset + 4)[0]
        offset += 4 + length
    return 0


def curve(b, q, **over):
    c = dict(base_frozen=0, quote_frozen=0, base_wrong=0, quote_wrong=0, base_bare=0, quote_bare=0)
    c.update(base.curve(b, q, **over))
    return c


def route(curves, hops, mints=None, epoch=0, source_frozen=0, destination_frozen=0, recipient_wrong=0, source_guard=0,
          destination_memo=0, destination_bare=0, recipient_bare=0, **over):
    r = base.route(curves, hops, **over)
    r.update(mints={k: dict(MINT_DEFAULTS, **v) for k, v in (mints or {}).items()}, epoch=epoch, source_frozen=source_frozen,
             destination_frozen=destination_frozen, recipient_wrong=recipient_wrong, source_guard=source_guard,
             destination_memo=destination_memo, destination_bare=destination_bare, recipient_bare=recipient_bare)
    return r


def host_line(r):
    join = lambda v: ':'.join(map(str, v)) or '-'
    head = [r['amount'], join(r['flags']), r['remaining'], r['source'], r['destination'], r['source_balance'], r['recipient'],
            r['pool_fee'], r['buyback_bps'], *base.TIER_BPS, *base.FLAT_BPS, join(r['hops']), r['epoch'], r['source_frozen'],
            r['destination_frozen'], r['recipient_wrong'], r['source_guard'], r['destination_memo'], r['destination_bare'],
            r['recipient_bare']]
    mints = []
    for i in range(len(MINTS)):
        m = mint_spec(r, i)
        mints.append(join([int(m['t22']), int(bool(m['fee'])), *(m['fee'] or (0, 0, 0, 0, 0)), int(m['hook']), int(m['paused']),
                           int(m['non_transferable']), int(m['malformed'] in FEE_REFUSED), int(m['malformed'] in UNREADABLE)]))
    blocks = [','.join(map(str, [c['vtr'], c['vqr'], c['rtr'], c['rqr'], c['cf'], c['pf'], c['creator'], c['cashback'], c['complete'],
                                 c['mayhem'], c['base'], c['quote'], c['base_vault'], c['quote_vault'], c['base_frozen'], c['quote_frozen'],
                                 c['base_wrong'], c['quote_wrong'], c['base_bare'], c['quote_bare']])) for c in r['curves']]
    return '|'.join([','.join(map(str, head)), ';'.join(mints)] + blocks)


_HOST = None


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'multi_hop_token2022_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def model(routes):
    text = ''.join(host_line(r) + '\n' for r in routes)
    answers = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    if len(answers) != len(routes):
        raise ValueError(f'host returned {len(answers)} answers for {len(routes)} routes')
    return answers


def pinned_bytes():
    out = {}
    for path, digest in ELF_SHA256.items():
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError(f'captured ELF digest mismatch: {path}')
        out[path] = payload
    return out


def error_name(err):
    if err is None:
        return None
    text = str(err)
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return f'error:{code.group(1)}'
    name = re.search(r'Fieldless\((\w+)\)', text)
    return f'error:{name.group(1)}' if name else text


class Chain:
    """One VM for every case: reloading the ELFs costs far more than a transaction."""

    def __init__(self):
        elfs = pinned_bytes()
        self.vm = vm = LiteSVM().with_transaction_history(0).with_sigverify(False)
        programdata = base.pda([bytes(PUMP)], base.UPGRADEABLE)
        vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + elfs[PUMP_ELF], base.UPGRADEABLE, False))
        vm.set_account(PUMP, Account(10**9, struct.pack('<I', 2) + bytes(programdata), base.UPGRADEABLE, True))
        vm.add_program(TOKEN, elfs[TOKEN_ELF])
        vm.add_program(TOKEN22, elfs[TOKEN22_ELF])
        self.stale = set()
        self.slot = 1000

    def run(self, r):
        vm = self.vm
        self.slot += 1
        vm.set_clock(Clock(self.slot, 0, r['epoch'], 0, TS))
        vm.expire_blockhash()
        for key in self.stale:
            vm.set_account(key, Account(0, b'', SYSTEM))
        user = USER.pubkey()
        state = {base.GLOBAL: (10**9, PUMP, base.global_data(r)), base.FEE_CONFIG: (10**9, FEES, base.fee_config_data()),
                 user: (USER_LAMPORTS, SYSTEM, b'')}
        for i, m in enumerate(MINTS):
            state[m] = (10**9, program_of(r, i), mint_data(mint_spec(r, i), 9 if i == 0 else 6))
        vaults = []
        for c in r['curves']:
            key = base.curve_key(c)
            native = c['quote'] == 0
            state[key] = (base.CURVE_RENT + (c['rqr'] + c['cf'] + c['pf'] if native else 0), PUMP, base.curve_data(c))
            base_program = program_of(r, c['base'])
            quote_program = program_of(r, c['quote'])
            other = lambda p: TOKEN if p == TOKEN22 else TOKEN22
            bv = ata(key, c['base'], other(base_program) if c['base_wrong'] else base_program)
            qv = ata(key, c['quote'], other(quote_program) if c['quote_wrong'] else quote_program)
            state[bv] = (10**9, base_program, token_data(r, c['base'], key, c['base_vault'], c['base_frozen'], c['base_bare']))
            state[qv] = (TOKEN_RENT, quote_program, token_data(r, c['quote'], key, c['quote_vault'], c['quote_frozen'], c['quote_bare']))
            vaults.append((bv, qv))

        def user_ata(mint_id, amount, frozen, **ext):
            key = ata(user, mint_id, program_of(r, mint_id))
            state[key] = (TOKEN_RENT + (amount if mint_id == 0 else 0), program_of(r, mint_id), token_data(r, mint_id, user, amount, frozen, **ext))
            return key

        source = user_ata(r['source'], r['source_balance'], r['source_frozen'], flags=tlv(11, b'\1') if r['source_guard'] else b'')
        destination = source if r['destination'] == r['source'] else user_ata(r['destination'], 0, r['destination_frozen'], bare=r['destination_bare'],
                                                                              flags=tlv(8, b'\1') if r['destination_memo'] else b'')
        recipient_program = program_of(r, r['recipient'])
        recipient_owner = (TOKEN if recipient_program == TOKEN22 else TOKEN22) if r['recipient_wrong'] else recipient_program
        recipient = ata(BUYBACK, r['recipient'], recipient_program)
        state[recipient] = (TOKEN_RENT, recipient_owner, token_data(r, r['recipient'], BUYBACK, 0, bare=r['recipient_bare']))
        for key, (lamports, owner, data) in state.items():
            vm.set_account(key, Account(lamports, data, owner))
        self.stale = set(state) - {user}
        metas = [AccountMeta(base.GLOBAL, False, False), AccountMeta(base.FEE_CONFIG, False, False), AccountMeta(base.AMM_CONFIG, True, False),
                 AccountMeta(user, True, True), AccountMeta(user, True, False), AccountMeta(source, False, True),
                 AccountMeta(destination, False, True), AccountMeta(recipient, False, True), AccountMeta(TOKEN, False, False),
                 AccountMeta(TOKEN22, False, False), AccountMeta(SYSTEM, False, False), AccountMeta(base.pda([b'__event_authority']), False, False),
                 AccountMeta(PUMP, False, False)]
        hop_keys = []
        for i in r['hops']:
            c = r['curves'][i]
            hop_keys += [MINTS[c['base']], MINTS[c['quote']], base.curve_key(c), *vaults[i]]
        metas += [AccountMeta(k, False, j % 5 >= 2) for j, k in enumerate(hop_keys)][:r['remaining']]
        data = bytes(base.SWAP['discriminator']) + struct.pack('<QI', r['amount'], len(r['flags'])) + bytes(r['flags'])
        ixs = [set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)]
        tx = Transaction.new_unsigned(Message.new_with_blockhash(ixs, user, vm.latest_blockhash()))
        tx.partial_sign([USER], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        raw = lambda key: bytes(vm.get_account(key).data)
        amount = lambda key: struct.unpack_from('<Q', raw(key), 64)[0]
        curves = []
        for c, (bv, qv) in zip(r['curves'], vaults):
            key = base.curve_key(c)
            a = vm.get_account(key)
            curves.append(dict(data=bytes(a.data), lamports=a.lamports - state[key][0], base_vault=amount(bv), quote_vault=amount(qv),
                               base_withheld=withheld_of(raw(bv)), quote_withheld=withheld_of(raw(qv))))
        rollback_errors = []
        if failed:
            for key, (lamports, owner, data) in state.items():
                after = vm.get_account(key)
                expected = lamports - TX_FEE if key == user else lamports
                if after is None or after.lamports != expected or after.owner != owner or bytes(after.data) != data:
                    rollback_errors.append(str(key))
        return dict(error=error_name(result.err()) if failed else None, curves=curves, returned=bytes(meta.return_data().data),
                    rollback_errors=rollback_errors, source=amount(source) - r['source_balance'], destination=amount(destination),
                    destination_withheld=withheld_of(raw(destination)),
                    recipient=vm.get_account(recipient).lamports - TOKEN_RENT if r['recipient'] == 0 else amount(recipient),
                    recipient_withheld=withheld_of(raw(recipient)), user_lamports=vm.get_account(user).lamports - USER_LAMPORTS)


def check(r, got, answer):
    """List mismatches; malformed or incomplete model/capture results fail closed."""
    if re.fullmatch(r'error:\w+', answer):
        bad = [] if got['error'] == answer else [f"error {got['error']} != {answer}"]
        if got.get('rollback_errors') != []:
            bad.append('failed transaction did not restore every seeded account')
        return bad
    if got['error'] is not None:
        return [f"captured failed with {got['error']}"]
    blocks = answer.split('|')
    fields = blocks[0].split(',')
    if len(fields) != 9 or fields[0] != 'ok':
        return ['malformed model status or output fields']
    if len(blocks) - 1 != len(r['curves']) or len(got['curves']) != len(r['curves']):
        return ['model/capture curve count does not match route']
    try:
        out, buyback, source, destination, lamports, recipient, dest_withheld, recipient_withheld = map(int, fields[1:])
        curves = [list(map(int, block.split(','))) for block in blocks[1:]]
    except ValueError:
        return ['noninteger model output']
    if any(len(values) != 14 for values in curves):
        return ['malformed model curve fields']
    bad = []
    if got['returned'] != struct.pack('<QQ', out, buyback):
        bad.append(f"return data {struct.unpack('<QQ', got['returned'])} != {(out, buyback)}")
    same = r['source'] == r['destination']
    want_source = source + destination if same else source
    want_destination = r['source_balance'] + want_source if same else destination
    for name, want in (('source', want_source), ('destination', want_destination), ('destination_withheld', dest_withheld),
                       ('recipient', recipient), ('recipient_withheld', recipient_withheld), ('user_lamports', lamports - TX_FEE)):
        if got[name] != want:
            bad.append(f'{name} {got[name]} != {want}')
    for c, g, values in zip(r['curves'], got['curves'], curves):
        vtr, vqr, rtr, rqr, cf, pf, post_base, post_quote, complete, base_vault, quote_vault, delta, base_withheld, quote_withheld = values
        after = bytearray(base.curve_data(c))
        struct.pack_into('<QQQQ', after, 8, vtr, vqr, rtr, rqr)
        after[48] = complete
        struct.pack_into('<QQ', after, 125, cf, pf)
        struct.pack_into('<QQ', after, 150, post_base, post_quote)
        if g['data'] != bytes(after):
            bad.append(f"curve {c['base']} bytes")
        for name, want in (('base_vault', base_vault), ('quote_vault', quote_vault), ('lamports', delta),
                           ('base_withheld', base_withheld), ('quote_withheld', quote_withheld)):
            if g[name] != want:
                bad.append(f"curve {c['base']} {name} {g[name]} != {want}")
    return bad


def fixed_cases():
    out = []
    add = lambda label, r: out.append((label, r))
    # Mint settings the route can meet on each of its three mints.
    fees = {'plain': None, 'f250': FEE_250, 'cap': FEE_CAP, 'all': FEE_ALL, 'epoch': FEE_EPOCH}
    shapes = {
        'sell-buy': lambda m, **k: route([curve(A, Q), curve(B, Q)], [0, 1], mints=m, source=A, destination=B, **k),
        'buy-sell-chain': lambda m, **k: route([curve(A, Q), curve(B, A, vqr=10**12, vtr=10**12, rtr=5 * 10**11, rqr=10**9, quote_vault=10**9)],
                                               [0, 1], mints=m, source=Q, destination=B, **k),
        'trip': lambda m, **k: route([curve(A, Q)], [0, 0], mints=m, source=Q, destination=Q, **k),
        'sell': lambda m, **k: route([curve(A, Q)], [0], mints=m, source=A, destination=Q, **k),
        'buy': lambda m, **k: route([curve(A, Q)], [0], mints=m, source=Q, destination=A, **k),
        'native-sell-buy': lambda m, **k: route([curve(A, 0), curve(B, 0)], [0, 1], mints=m, source=A, destination=B, **k),
    }
    for shape, make in shapes.items():
        for name, fee in fees.items():
            for who in ('quote', 'base', 'both'):
                mints = {}
                if who != 'base' and shape != 'native-sell-buy':
                    mints[Q] = dict(fee=fee)
                if who != 'quote':
                    mints[A] = dict(fee=fee)
                    mints[B] = dict(fee=fee)
                if not mints:
                    continue
                for flags in ((0,), (1,), (2,), (3,)):
                    n = 1 if shape in ('sell', 'buy') else 2
                    for epoch in (0, 5):
                        recipient = Q if shape != 'native-sell-buy' else 0
                        add(f'{shape}-{name}-{who}-{flags[0]}-e{epoch}', make(mints, flags=flags * n, epoch=epoch, recipient=recipient))
    sell_buy = lambda m, **k: route([curve(A, Q), curve(B, Q)], [0, 1], mints=m, **dict(dict(source=A, destination=B), **k))
    trip = lambda m, **k: route([curve(A, Q)], [0, 0], mints=m, **dict(dict(source=Q, destination=Q), **k))
    sell = lambda m, **k: route([curve(A, Q)], [0], mints=m, **dict(dict(source=A, destination=Q), **k))
    buy = lambda m, **k: route([curve(A, Q)], [0], mints=m, **dict(dict(source=Q, destination=A), **k))
    native = lambda m, **k: route([curve(A, 0)], [0], mints=m, **dict(dict(source=A, destination=0), **k))
    # Extensions that stop a transfer, on each mint a route moves.
    for kind in ('hook', 'paused', 'non_transferable'):
        for who, mints in (('quote', {Q: {kind: True}}), ('base', {A: {kind: True}}), ('second-base', {B: {kind: True}}),
                           ('quote-fee', {Q: {kind: True, 'fee': FEE_250}}), ('all', {Q: {kind: True}, A: {kind: True}, B: {kind: True}})):
            for flags in (0, 1):
                add(f'{kind}-{who}-sell-buy-{flags}', sell_buy(mints, flags=(flags, flags), recipient=Q))
                add(f'{kind}-{who}-trip-{flags}', trip(mints, flags=(flags, flags), recipient=Q))
                add(f'{kind}-{who}-sell-{flags}', sell(mints, flags=(flags,), recipient=Q))
                add(f'{kind}-{who}-buy-{flags}', buy(mints, flags=(flags,), recipient=Q))
            add(f'{kind}-{who}-native', native(mints))
            add(f'{kind}-{who}-short-source', sell_buy(mints, source_balance=10))
            add(f'{kind}-{who}-wrong-destination', sell_buy(mints, destination=C))
    # A mint that cannot move does not matter when the route never sends it.
    add('hook-quote-trip-same-vault', route([curve(A, Q)], [0, 0], mints={A: dict(hook=True)}, source=Q, destination=Q))
    add('paused-buyback-only', route([curve(A, Q)], [0], mints={Q: dict(paused=True)}, source=A, destination=C, flags=(1,)))
    add('sell-no-buyback-no-quote-move', sell_buy({Q: dict(hook=True), A: dict(fee=FEE_250)}, flags=(0, 0)))
    for extra in EXTENSIONS:
        for who in (Q, A):
            add(f'extra-{extra}-{who}', sell_buy({who: dict(extra=(extra,), fee=FEE_250)}, flags=(3, 3), recipient=Q))
    # Frozen accounts, one at a time and in pairs with a short balance.
    for mints_name, mints in (('t22', {Q: {}, A: {}, B: {}}), ('fee', {Q: dict(fee=FEE_250), A: dict(fee=FEE_250), B: dict(fee=FEE_250)}), ('base', {A: {}, B: {}})):
        for flags in (0, 1):
            f = (flags, flags)
            add(f'{mints_name}-frozen-source-{flags}', sell_buy(mints, flags=f, source_frozen=1))
            add(f'{mints_name}-frozen-destination-{flags}', sell_buy(mints, flags=f, destination_frozen=1))
            add(f'{mints_name}-frozen-both-{flags}', sell_buy(mints, flags=f, source_frozen=1, destination_frozen=1))
            add(f'{mints_name}-frozen-source-short-{flags}', sell_buy(mints, flags=f, source_frozen=1, source_balance=1))
            add(f'{mints_name}-frozen-dest-short-source-{flags}', sell_buy(mints, flags=f, destination_frozen=1, source_balance=1))
            for name, over in (('a-base', 0), ('a-quote', 1), ('b-base', 2), ('b-quote', 3)):
                curves = [curve(A, Q, base_frozen=int(over == 0), quote_frozen=int(over == 1)),
                          curve(B, Q, base_frozen=int(over == 2), quote_frozen=int(over == 3))]
                add(f'{mints_name}-frozen-{name}-{flags}', route(curves, [0, 1], mints=mints, source=A, destination=B, flags=f))
        add(f'{mints_name}-frozen-source-dest-mint', sell_buy(mints, destination=C, destination_frozen=1))
    # Vaults of the wrong program, recipient program and mint, and their order.
    t22 = {Q: {}, A: {}, B: {}}
    for mints_name, mints in (('t22', t22), ('base', {A: {}, B: {}}), ('quote', {Q: {}}), ('spl', {})):
        for name, over in (('base', dict(base_wrong=1)), ('quote', dict(quote_wrong=1))):
            add(f'{mints_name}-wrong-{name}-first', route([curve(A, Q, **over), curve(B, Q)], [0, 1], mints=mints, source=A, destination=B))
            add(f'{mints_name}-wrong-{name}-second', route([curve(A, Q), curve(B, Q, **over)], [0, 1], mints=mints, source=A, destination=B))
            add(f'{mints_name}-wrong-{name}-complete', route([curve(A, Q, complete=1, **over)], [0], mints=mints, source=A, destination=Q))
            add(f'{mints_name}-wrong-{name}-mayhem', route([curve(A, Q, mayhem=1, **over)], [0], mints=mints, source=A, destination=Q))
            add(f'{mints_name}-wrong-{name}-recipient', route([curve(A, Q, **over)], [0], mints=mints, source=A, destination=Q, flags=(1,), recipient=A))
            add(f'{mints_name}-wrong-{name}-discontinuous', route([curve(A, Q, **over), curve(B, Q)], [0], mints=mints, source=C, destination=Q))
        for flags in ((1, 0), (0, 1), (1, 1), (0, 0)):
            add(f'{mints_name}-recipient-program-{flags}', sell_buy(mints, flags=flags, recipient_wrong=1, recipient=Q))
            add(f'{mints_name}-recipient-mint-{flags}', sell_buy(mints, flags=flags, recipient=A))
            add(f'{mints_name}-recipient-both-{flags}', sell_buy(mints, flags=flags, recipient=A, recipient_wrong=1))
        add(f'{mints_name}-recipient-before-direction', route([curve(A, Q)], [0], mints=mints, source=C, destination=Q, flags=(1,), recipient_wrong=1, recipient=Q))
        add(f'{mints_name}-recipient-native-curve', route([curve(A, 0)], [0], mints=mints, source=A, destination=0, flags=(1,), recipient=0, recipient_wrong=1))
    # A malformed extension area: only a quote mint's is parsed by Pump.
    for kind in ['unknown'] + list(FEE_REFUSED) + list(UNREADABLE):
        for name, who in (('quote', Q), ('base', A), ('second', B)):
            mints = {who: dict(malformed=kind)}
            add(f'{kind}-{name}', sell_buy(mints))
            add(f'{kind}-{name}-complete', route([curve(A, Q, complete=1)], [0], mints=mints, source=A, destination=Q))
            add(f'{kind}-{name}-wrong-vault', route([curve(A, Q, base_wrong=1)], [0], mints=mints, source=A, destination=Q))
            add(f'{kind}-{name}-recipient', route([curve(A, Q)], [0], mints=mints, source=A, destination=Q, flags=(1,), recipient=A))
            add(f'{kind}-{name}-native', route([curve(A, 0)], [0], mints=mints, source=A, destination=0))
    # Account extensions a transfer stops on, and their order against each other.
    fee_all = {Q: dict(fee=FEE_250), A: dict(fee=FEE_250), B: dict(fee=FEE_250)}
    plain = {Q: {}, A: {}, B: {}}
    for name, mints in (('fee', fee_all), ('plain', plain), ('hook', {Q: dict(hook=True), A: dict(hook=True), B: dict(hook=True)}),
                        ('hook-fee', {Q: dict(hook=True, fee=FEE_250), A: dict(hook=True, fee=FEE_250), B: dict(hook=True, fee=FEE_250)})):
        make = lambda **k: sell_buy(mints, **k)
        add(f'{name}-guard', make(source_guard=1))
        add(f'{name}-guard-frozen-source', make(source_guard=1, source_frozen=1))
        add(f'{name}-guard-frozen-destination', make(source_guard=1, destination_frozen=1))
        add(f'{name}-guard-short', make(source_guard=1, source_balance=1))
        add(f'{name}-memo', make(destination_memo=1))
        add(f'{name}-memo-frozen', make(destination_memo=1, destination_frozen=1))
        add(f'{name}-memo-hop-order', make(destination_memo=1, source_guard=1))
        add(f'{name}-bare-destination', make(destination_bare=1))
        add(f'{name}-bare-destination-memo', make(destination_bare=1, destination_memo=1))
        add(f'{name}-bare-recipient', make(recipient_bare=1, flags=(1, 1), recipient=Q))
        add(f'{name}-bare-recipient-no-buyback', make(recipient_bare=1, flags=(1, 1), recipient=Q, buyback_bps=0))
        add(f'{name}-bare-base-a', route([curve(A, Q, base_bare=1), curve(B, Q)], [0, 1], mints=mints, source=A, destination=B))
        add(f'{name}-bare-quote-a', route([curve(A, Q, quote_bare=1), curve(B, Q)], [0, 1], mints=mints, source=A, destination=B))
        add(f'{name}-bare-quote-b', route([curve(A, Q), curve(B, Q, quote_bare=1)], [0, 1], mints=mints, source=A, destination=B))
        add(f'{name}-bare-base-b', route([curve(A, Q), curve(B, Q, base_bare=1)], [0, 1], mints=mints, source=A, destination=B))
    add('bare-free-when-capped-zero', sell_buy({A: dict(fee=(0, 0, 0, 500, 0))}, destination_bare=1))
    add('guard-buy-native', route([curve(A, 0)], [0], mints={A: {}}, source=0, destination=A, source_guard=1))
    # Curve guards run before any Token-2022 read.
    for name, mints in (('plain', {Q: {}}), ('refused', {Q: dict(malformed='fee-short')}), ('unreadable', {Q: dict(malformed='len-170')})):
        for flags in range(4):
            for over_name, over in (('cashback', dict(cashback=1)), ('mayhem', dict(mayhem=1)), ('both', dict(cashback=1, mayhem=1)),
                                    ('cashback-wrong-vault', dict(cashback=1, base_wrong=1))):
                add(f'guard-{name}-{over_name}-{flags}', route([curve(A, Q, **over)], [0], mints=mints, source=A, destination=Q, flags=(flags,)))
    add('hop-two-cashback-fee', route([curve(A, Q), curve(B, Q, cashback=1)], [0, 1], mints={Q: dict(fee=FEE_250)}, source=A, destination=B, flags=(0, 2)))
    add('hop-two-cashback-no-creator-flag', route([curve(A, Q), curve(B, Q, cashback=1)], [0, 1], mints={Q: dict(fee=FEE_250)}, source=A, destination=B, flags=(0, 1)))
    # A zero transfer is skipped, so it stops on nothing; one lamport more does.
    round_trip = lambda m, **k: route([curve(A, Q)], [0, 0], mints=m, source=A, destination=A, recipient=Q, **k)
    for kind in ('hook', 'paused', 'non_transferable'):
        for flags in ((0, 0), (1, 0), (0, 1), (1, 1)):
            for bps in (0, 5_000):
                add(f'zero-buyback-{kind}-{flags}-{bps}', round_trip({Q: {kind: True}}, flags=flags, buyback_bps=bps))
    for bps in (0, 5_000):
        add(f'zero-buyback-frozen-quote-{bps}', route([curve(A, Q, quote_frozen=1)], [0, 0], mints={Q: {}}, source=A, destination=A, recipient=Q,
                                                      flags=(1, 1), buyback_bps=bps))
    # The WSOL key on Token-2022: a native curve reads neither its fee nor its bytes.
    for name, wsol in (('plain', {}), ('fee', dict(fee=FEE_250)), ('refused', dict(malformed='fee-short')), ('hook', dict(hook=True))):
        for amount in (10**6, 10**9):
            add(f'wsol-t22-{name}-sell-{amount}', route([curve(A, 0)], [0], mints={0: wsol}, amount=amount, source=A, destination=0))
            add(f'wsol-t22-{name}-trip-{amount}', route([curve(A, 0)], [0, 0], mints={0: wsol}, amount=amount, source=A, destination=A))
    # Frozen receiver against a short sender: SPL Token checks frozen first.
    for name, mints in (('spl', {}), ('t22', {Q: {}, A: {}, B: {}})):
        add(f'{name}-frozen-vault-short-source', route([curve(A, Q, base_frozen=1), curve(B, Q)], [0, 1], mints=mints, source=A, destination=B, source_balance=1))
        add(f'{name}-frozen-second-vault-short', route([curve(A, Q, quote_vault=10), curve(B, Q, quote_frozen=1)], [0, 1], mints=mints, source=A, destination=B))
        add(f'{name}-frozen-destination-short-vault', route([curve(A, Q, base_vault=10, rtr=10)], [0], mints=mints, source=Q, destination=A, destination_frozen=1))
    # A destination of the other token program, from each side.
    for name, mints in (('spl-to-t22', {C: {}}), ('t22-to-spl', {B: {}}), ('both-t22', {B: {}, C: {}}), ('all-t22', {Q: {}, A: {}, B: {}, C: {}})):
        add(f'{name}-buy-destination', sell_buy(mints, destination=C))
        add(f'{name}-sell-destination', route([curve(B, Q)], [0], mints=mints, source=B, destination=C))
        add(f'{name}-buy-short-destination', route([curve(B, Q, base_vault=10, rtr=10)], [0], mints=mints, source=Q, destination=C))
    # Rounding, caps and the epoch boundary, against the amount each hop prices.
    for fee_name, fee in (('f1', (0, 0, 0, 1, 10**18)), ('f9999', (0, 0, 0, 9_999, 10**18)), ('cap1', (0, 0, 0, 10_000, 1)),
                          ('zero-cap', (0, 0, 0, 500, 0)), ('zero-bps', (0, 0, 0, 0, 10**18)), ('all', FEE_ALL)):
        for amount in (1, 2, 3, 19, 20, 21, 399, 400, 401, 9_999, 10_000, 10_001, 10**6, 10**9):
            for flags in (0, 3):
                add(f'buy-{fee_name}-{amount}-{flags}', buy({Q: dict(fee=fee)}, amount=amount, flags=(flags,), recipient=Q))
                add(f'sell-{fee_name}-{amount}-{flags}', sell({Q: dict(fee=fee)}, amount=amount, flags=(flags,), recipient=Q))
                add(f'trip-{fee_name}-{amount}-{flags}', trip({Q: dict(fee=fee)}, amount=amount, flags=(flags, flags), recipient=Q))
                add(f'base-{fee_name}-{amount}-{flags}', sell({A: dict(fee=fee)}, amount=amount, flags=(flags,), recipient=Q))
    for epoch in (0, 4, 5, 6):
        add(f'epoch-{epoch}', sell_buy({Q: dict(fee=FEE_EPOCH), A: dict(fee=(0, 0, 3, 900, 10**18))}, flags=(3, 3), epoch=epoch))
    # Crossing buys: pool base is the real vault balance, net of withheld tokens.
    for q_name, q, mints in (('t22', Q, {Q: dict(fee=FEE_250)}), ('cap', Q, {Q: dict(fee=FEE_CAP)}), ('base', Q, {A: dict(fee=FEE_250)}),
                             ('both', Q, {Q: dict(fee=FEE_250), A: dict(fee=FEE_250)}), ('native', 0, {A: dict(fee=FEE_250)})):
        for flags in range(4):
            for amount in (30_100_000, 31_000_000, 32_000_000, 40_000_000, 10**9):
                one = [curve(A, q, rtr=10**12)]
                add(f'cross-{q_name}-{amount}-{flags}', route(one, [0], mints=mints, amount=amount, source=q, destination=A, flags=(flags,), recipient=q))
                add(f'cross-trip-{q_name}-{amount}-{flags}', route(one, [0, 0], mints=mints, amount=amount, source=q, destination=q, flags=(flags, 0), recipient=q))
        add(f'cross-pool-base-short-{q_name}', route([curve(A, q, rtr=10**12, base_vault=10**12 - 1)], [0], mints=mints, source=q, destination=A, recipient=q))
        add(f'cross-sell-into-{q_name}', route([curve(B, q), curve(A, q, rtr=10**12)], [0, 1], mints=mints, amount=10**12, source=B, destination=A, flags=(3, 3), recipient=q))
    # Short vaults and sources: the fee never adds to what must be held.
    add('source-short-by-one', sell({A: dict(fee=FEE_250)}, source_balance=10**9 - 1))
    add('first-vault-short-fee', route([curve(A, Q, quote_vault=10), curve(B, Q)], [0, 1], mints={Q: dict(fee=FEE_250)}, source=A, destination=B))
    add('last-vault-short-fee', route([curve(A, Q, base_vault=100, rtr=100)], [0], mints={A: dict(fee=FEE_250)}, source=Q, destination=A))
    add('wrong-destination-fee', sell({Q: dict(fee=FEE_250)}, destination=C))
    add('wrong-destination-native-sell', native({A: dict(fee=FEE_250)}, destination=C))
    add('sell-all-then-buy-zero', route([curve(A, Q), curve(B, Q)], [0, 1], mints={Q: dict(fee=FEE_ALL)}, source=A, destination=B))
    add('sell-zero-t22', sell({Q: dict(fee=FEE_250)}, amount=1, flags=(3,)))
    three = [curve(A, Q), curve(B, Q)]
    mixed = {Q: dict(fee=FEE_250), A: dict(fee=FEE_CAP), B: dict(fee=FEE_EPOCH)}
    for f in ((0, 0, 0), (1, 1, 1), (3, 3, 3), (2, 0, 1)):
        add(f'three-{f}', route(three, [0, 1, 1], mints=mixed, source=A, destination=Q, flags=f, epoch=5))
        add(f'four-{f}', route(three, [0, 1, 1, 0], mints=mixed, source=A, destination=A, flags=f + (3,), epoch=5))
    return out


def random_cases(count=400, seed=20261031):
    rng = random.Random(seed)
    out = []
    fee = lambda: rng.choice([None, FEE_250, FEE_CAP, FEE_EPOCH, FEE_ALL, (rng.randrange(10_001), rng.randrange(10**7), rng.randrange(8),
                                                                           rng.randrange(10_001), rng.choice([rng.randrange(10**7), U64]))])
    for i in range(count):
        q = rng.choice([0, Q, Q, Q])
        rand_curve = lambda b: curve(b, q, vtr=rng.choice([10**15, 10**13]), vqr=rng.randrange(10**8, 10**11),
                                     rtr=rng.choice([10**12, rng.randrange(1, 10**12), 10**14]), rqr=rng.randrange(10**8, 10**12),
                                     creator=int(rng.random() < .8), cf=rng.randrange(10**6), pf=rng.randrange(10**6))
        curves = [rand_curve(A), rand_curve(B)]
        shape = rng.choice(['sell-buy', 'trip', 'three', 'cross'])
        hops, source, dest = {'sell-buy': ([0, 1], A, B), 'trip': ([0, 0], q, q), 'three': ([0, 1, 1], A, q), 'cross': ([0], q, A)}[shape]
        amount = rng.randrange(1, 10**6) if rng.random() < .4 else rng.randrange(10**6, 10**11)
        mints = {k: dict(fee=fee()) for k in (A, B) + ((Q,) if q else ()) if rng.random() < .75}
        r = route(curves, hops, mints=mints, amount=amount, flags=tuple(rng.randrange(4) for _ in hops), source=source, destination=dest,
                  epoch=rng.randrange(8), pool_fee=rng.choice([0, rng.randrange(10**9)]), buyback_bps=rng.choice([0, 5_000, 10_000, rng.randrange(10_001)]))
        out.append((f'random-{i}-{shape}', r))
    return out


class MultiHopToken2022Captured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chain = Chain()

    def run_all(self, labelled):
        answers = model([r for _, r in labelled])
        self.assertEqual(len(answers), len(labelled), 'one model answer is required per captured route')
        for (label, r), answer in zip(labelled, answers):
            with self.subTest(label):
                self.assertEqual(check(r, self.chain.run(r), answer), [], (label, answer))
        return answers

    def test_fixed_cases(self):
        cases = fixed_cases()
        self.assertEqual(len(cases), FIXED_COUNT)
        results = self.run_all(cases)
        outcomes = {a.split(',')[0] for a in results}
        for want in ('ok', 'error:1', 'error:13', 'error:17', 'error:36', 'error:37', 'error:42', 'error:67', 'error:2006',
                     'error:6004', 'error:6005', 'error:6010', 'error:6020', 'error:6021', 'error:6022', 'error:6024',
                     'error:6041', 'error:6042', 'error:6063', 'error:6094', 'error:6098', 'error:6108', 'error:IncorrectProgramId',
                     'error:InvalidAccountData', 'error:MissingAccount'):
            self.assertIn(want, outcomes)
        self.assertEqual(sum(a.startswith('ok,') for a in results), FIXED_OK)
        withheld = sum(a.startswith('ok,') and (sum(map(int, a.split('|')[0].split(',')[7:])) > 0
                                                or any(sum(map(int, b.split(',')[12:])) > 0 for b in a.split('|')[1:])) for a in results)
        self.assertEqual(withheld, FIXED_WITHHELD, 'successful routes on which a mint withheld a fee')
        self.assertEqual(sum(a.startswith('ok,') and any(int(b.split(',')[6]) > 0 for b in a.split('|')[1:]) for a in results),
                         FIXED_CROSSING, 'successful crossing fills')

    def test_random_cases(self):
        cases = random_cases()
        self.assertEqual(len(cases), 400)
        results = self.run_all(cases)
        self.assertEqual(sum(a.startswith('ok,') for a in results), RANDOM_OK)

    def test_every_elf_digest_is_pinned(self):
        self.assertEqual(set(pinned_bytes()), {PUMP_ELF, TOKEN_ELF, TOKEN22_ELF})
        wrong = dict(ELF_SHA256)
        wrong[TOKEN22_ELF] = '0' * 64
        with unittest.mock.patch.dict(globals(), {'ELF_SHA256': wrong}):
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                pinned_bytes()

    def test_checker_rejects_tampered_outcomes(self):
        routes = [route([curve(A, Q), curve(B, Q)], [0, 1], mints={Q: dict(fee=FEE_250), A: dict(fee=FEE_250), B: dict(fee=FEE_250)},
                        source=A, destination=B, flags=(3, 3), recipient=Q),
                  route([curve(A, 0)], [0], mints={A: dict(fee=FEE_250)}, source=0, destination=A, flags=(3,), recipient=0)]
        for r, answer in zip(routes, model(routes)):
            got = self.chain.run(r)
            self.assertEqual(check(r, got, answer), [])
            head, *curves = answer.split('|')
            fields = head.split(',')
            for i in range(1, len(fields)):
                bent = fields[:i] + [str(int(fields[i]) + 1)] + fields[i + 1:]
                self.assertNotEqual(check(r, got, '|'.join([','.join(bent)] + curves)), [], i)
            for j, block in enumerate(curves):
                parts = block.split(',')
                for i in range(len(parts)):
                    bent = parts[:i] + [str(int(parts[i]) + 1)] + parts[i + 1:]
                    self.assertNotEqual(check(r, got, '|'.join([head] + curves[:j] + [','.join(bent)] + curves[j + 1:])), [], (j, i))
            for bent in ('', head, answer.replace('ok,', 'unmodelled,', 1), 'error:6024'):
                self.assertNotEqual(check(r, got, bent), [], bent)

    def test_error_outcomes_require_rollback(self):
        r = route([curve(A, Q), curve(B, Q, complete=1)], [0, 1], mints={Q: dict(fee=FEE_250)}, source=A, destination=B)
        answer = model([r])[0]
        got = self.chain.run(r)
        self.assertEqual(answer, 'error:6005')
        self.assertEqual(check(r, got, answer), [])
        self.assertNotEqual(check(r, got, 'error:6004'), [])
        self.assertNotEqual(check(r, dict(copy.deepcopy(got), rollback_errors=['changed']), answer), [])


if __name__ == '__main__':
    unittest.main()
