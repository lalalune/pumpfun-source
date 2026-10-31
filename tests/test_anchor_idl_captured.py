"""Captured-program checks for the seven Anchor IDL commands of Pump Main.

The published IDL does not list them, but the captured
`evidence/original/pump/deployed.so` still answers the tag `40f4bc78a7e9690a`
with Anchor's `IdlInstruction` dispatcher: create, create_buffer, write,
set_buffer, set_authority, close and resize. Every case runs that program on
LiteSVM and `programs/pump/recovered/anchor_idl_host.rs` on the same accounts.
The error (with the account an Anchor log names), the `Instruction:` log line
and the owner, lamports and data of every account must agree. Faults go on
each account slot alone and in pairs, so the order of the checks is pinned;
the last test walks one VM through random commands so each starts from what
the previous one left, and another hands an IDL account made here to
`admin_set_idl_authority` and goes on with the new authority. This is matching behaviour on these inputs only, not a
byte-identity claim.
"""
from pathlib import Path
import hashlib
import json
import random
import re
import struct
import subprocess
import tempfile
import unittest

from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
PUMP_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
STUB_ELF = ROOT / 'scripts/fixtures/signer_stub.so'
HOST_SOURCE = ROOT / 'programs/pump/recovered/anchor_idl_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
OTHER_PROGRAM = Pubkey.from_bytes(bytes([12]) * 32)
# Anchor's IDL_IX_TAG, the u64 0x0a69e9a778bcf440 in little-endian order.
IDL_TAG = struct.pack('<Q', 0x0a69e9a778bcf440)
IDL_ACCOUNT_DISC = hashlib.sha256(b'internal:IdlAccount').digest()[:8]
PAYER = Keypair.from_seed(bytes([201]) * 32)
BASE = Pubkey.find_program_address([], PUMP)[0]
CANONICAL = Pubkey.create_with_seed(BASE, 'anchor:idl', PUMP)
AUTHORITY = Pubkey.from_bytes(bytes([41]) * 32)
ROGUE = Pubkey.from_bytes(bytes([42]) * 32)
IDL_KEY = Pubkey.from_bytes(bytes([43]) * 32)
BUFFER = Pubkey.from_bytes(bytes([44]) * 32)
DESTINATION = Pubkey.from_bytes(bytes([45]) * 32)
SPARE = Pubkey.from_bytes(bytes([46]) * 32)
SECOND_SPARE = Pubkey.from_bytes(bytes([47]) * 32)
LOCAL = (AUTHORITY, ROGUE, IDL_KEY, BUFFER, DESTINATION, SPARE, SECOND_SPARE, CANONICAL, BASE)
OWNERS = {'s': SYSTEM, 'p': PUMP, 'o': OTHER_PROGRAM}
ADMIN_SET = next(i for i in IDL['instructions'] if i['name'] == 'admin_set_idl_authority')
GLOBAL_DISC = next(bytes(a['discriminator']) for a in IDL['accounts'] if a['name'] == 'Global')
GLOBAL = Pubkey.find_program_address([b'global'], PUMP)[0]
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
RICH = 10**12


def rent(size):
    return (size + 128) * 6_960


def slot(key, signer=False, writable=False, owner='s', lamports=0, data=b'', executable=False):
    return dict(key=key, signer=signer, writable=writable, owner=owner, lamports=lamports, data=bytes(data),
                executable=executable)


def idl_bytes(authority=AUTHORITY, data_len=0, size=200, fill=0):
    head = IDL_ACCOUNT_DISC + bytes(authority) + struct.pack('<I', data_len)
    return (head + bytes((fill + i) % 251 if fill else 0 for i in range(size)))[:size] if size < 44 else (
        head + bytes((fill + i) % 251 if fill else 0 for i in range(size - 44)))


def idl_slot(key=IDL_KEY, lamports=None, **kwargs):
    data = idl_bytes(**kwargs)
    return slot(key, writable=True, owner='p', lamports=rent(len(data)) if lamports is None else lamports, data=data)


def authority_slot(key=AUTHORITY, writable=False, signer=True, lamports=RICH):
    return slot(key, signer=signer, writable=writable, lamports=lamports)


def system_slot():
    return slot(SYSTEM, owner='o', lamports=1, executable=True)


def program_slot():
    return slot(PUMP, owner='o', lamports=1, executable=True)


def base_slot():
    return slot(BASE)


def command(tag, *payload):
    return bytes([tag]) + b''.join(payload)


def template(op):
    if op == 'create':
        return command(0, struct.pack('<Q', 100)), [
            slot(AUTHORITY, signer=True, writable=True, lamports=RICH), slot(CANONICAL, writable=True), base_slot(),
            system_slot(), program_slot()]
    if op == 'create_buffer':
        return command(1), [slot(BUFFER, writable=True, owner='p', lamports=rent(300), data=bytes(300)),
                            authority_slot()]
    if op == 'write':
        return command(2, struct.pack('<I', 9), b'nine byte'), [idl_slot(data_len=5, size=120, fill=3),
                                                                authority_slot()]
    if op == 'set_buffer':
        return command(3), [idl_slot(BUFFER, data_len=20, size=120, fill=7), idl_slot(data_len=2, size=200, fill=9),
                            authority_slot()]
    if op == 'set_authority':
        return command(4, bytes(ROGUE)), [idl_slot(data_len=5), authority_slot()]
    if op == 'close':
        return command(5), [idl_slot(data_len=5), authority_slot(),
                            slot(DESTINATION, writable=True, lamports=7)]
    return command(6, struct.pack('<Q', 500)), [idl_slot(), authority_slot(writable=True), system_slot()]


OPS = ('create', 'create_buffer', 'write', 'set_buffer', 'set_authority', 'close', 'resize')


def replace(account, **changes):
    return {**account, **changes}


def slot_faults(account, spare=SPARE):
    """Named ways to spoil one slot. Each maps to a replacement slot."""
    key = account['key']
    faults = {'signer-off': replace(account, signer=False), 'writable-off': replace(account, writable=False)}
    if key in (SYSTEM, PUMP):
        faults['wrong-key'] = slot(spare, lamports=1, owner='s')
        faults['other-program'] = slot(OTHER_PROGRAM, owner='o', lamports=1, executable=True)
        return faults
    faults['wrong-key'] = replace(account, key=spare)
    faults['absent'] = slot(key, signer=account['signer'], writable=account['writable'])
    faults['system-owned'] = replace(account, owner='s')
    faults['other-owned'] = replace(account, owner='o', lamports=max(account['lamports'], 1))
    faults['poor'] = replace(account, lamports=1)
    faults['data-carrying'] = replace(account, data=bytes(50), lamports=max(account['lamports'], 1))
    faults['bad-disc'] = replace(account, data=b'\x01' + account['data'][1:] if account['data'] else b'\x01' * 60,
                                 lamports=max(account['lamports'], 1))
    for size in (0, 7, 8, 43, 44):
        faults[f'short-{size}'] = replace(account, data=account['data'][:size])
    if account['data'][:8] == IDL_ACCOUNT_DISC:
        faults['other-stored-authority'] = replace(account, data=idl_bytes(ROGUE, data_len=5, size=len(account['data'])))
        faults['zero-stored-authority'] = replace(account, data=idl_bytes(SYSTEM, data_len=5, size=len(account['data'])))
    return faults


def host_line(args, slots):
    fields = [args.hex()]
    for a in slots:
        fields.append(','.join((bytes(a['key']).hex(), str(int(a['signer'])), str(int(a['writable'])), a['owner'],
                                str(a['lamports']), str(int(a['executable'])), a['data'].hex())))
    return ';'.join(fields)


class Vm:
    def __init__(self):
        self.vm = LiteSVM().with_sigverify(False).with_transaction_history(0)
        self.vm.add_program_from_file(PUMP, PUMP_ELF)
        self.vm.add_program_from_file(OTHER_PROGRAM, STUB_ELF)
        self.vm.set_account(PAYER.pubkey(), Account(10**15, b'', SYSTEM))

    def load(self, slots):
        for key in LOCAL:
            self.vm.set_account(key, Account(0, b'', SYSTEM))
        for a in slots:
            if a['key'] in LOCAL and a['lamports'] + len(a['data']):
                self.vm.set_account(a['key'], Account(a['lamports'], a['data'], OWNERS[a['owner']], a['executable']))

    def send(self, args, slots):
        metas = [AccountMeta(a['key'], a['signer'], a['writable']) for a in slots]
        self.vm.expire_blockhash()
        message = Message.new_with_blockhash([Instruction(PUMP, IDL_TAG + args, metas)], PAYER.pubkey(),
                                             self.vm.latest_blockhash())
        tx = Transaction.new_unsigned(message)
        tx.partial_sign([PAYER], self.vm.latest_blockhash())
        return self.vm.send_transaction(tx)

    def state(self, key):
        account = self.vm.get_account(key)
        if account is None or (account.lamports == 0 and not bytes(account.data)):
            return 's', 0, b''
        owner = next((k for k, v in OWNERS.items() if v == account.owner), 'o')
        return owner, account.lamports, bytes(account.data)

    def run(self, args, slots):
        result = self.send(args, slots)
        if isinstance(result, FailedTransactionMetadata):
            logs = result.meta().logs()
            text = str(result.err())
            if 'ProgramFailedToComplete' in text:
                return 'panic'
            if 'InsufficientFundsForRent' in text:
                return 'runtime:InsufficientFundsForRent'
            custom = re.search(r'InstructionErrorCustom\((\d+)\)', text)
            if custom is None:
                name = re.search(r'Fieldless\((\w+)\)', text)
                return 'runtime:' + (name.group(1) if name else text)
            number = int(custom.group(1))
            if number < 100:
                return f'system:{number}'
            named = next((re.search(r'caused by account: (\w+)\.', line) for line in logs
                          if 'caused by account' in line), None)
            return f'error:{number}:{named.group(1) if named else "-"}'
        log = next(line[len('Program log: Instruction: '):] for line in result.logs()
                   if line.startswith('Program log: Instruction: '))
        seen = []
        answer = f'ok:{log}'
        for a in slots:
            if a['key'] in seen:
                continue
            seen.append(a['key'])
            if a['key'] in LOCAL:
                owner, lamports, data = self.state(a['key'])
            else:
                owner, lamports, data = a['owner'], a['lamports'], a['data']
            answer += f';{bytes(a["key"]).hex()},{owner},{lamports},{data.hex()}'
        return answer


def fixed_cases():
    cases = []
    # Decode: every length around each argument, unknown variants, trailing bytes.
    keep = {op: template(op) for op in OPS}
    for op, length in (('create', 9), ('write', 5), ('set_authority', 33), ('resize', 9)):
        args, slots = keep[op]
        cases += [(args[:n], slots) for n in range(length)]
        cases.append((args + b'trailing', slots))
    cases += [(b'', []), (b'', keep['close'][1])]
    cases += [(bytes([tag]) + bytes(64), keep['close'][1]) for tag in (7, 8, 100, 255)]
    cases.append((command(2, struct.pack('<I', 10), b'nine byte'), keep['write'][1]))
    cases.append((command(2, struct.pack('<I', 2**32 - 1), b'nine byte'), keep['write'][1]))
    # The stated length is allocated first: 120 bytes per account, 48 per repeat.
    args, slots = keep['write']
    extra = [slot(SPARE, lamports=5), slot(DESTINATION, lamports=5)]
    for accounts in (slots, slots + extra[:1], slots + extra, slots + [slots[0]], slots[:1], [], slots[:1] * 2,
                     slots + slots, slots + extra[:1] * 3, slots + extra[:1] + slots[:1]):
        room = 32_030 - 120 * len({bytes(a['key']) for a in accounts})
        room -= 48 * (len(accounts) - len({bytes(a['key']) for a in accounts}))
        for stated in (room - 1, room, room + 1, 2**31):
            cases.append((command(2, struct.pack('<I', stated), b'nine byte'), accounts))
    # Missing accounts and extra accounts.
    for op in OPS:
        args, slots = keep[op]
        cases += [(args, slots[:n]) for n in range(len(slots))]
        cases.append((args, slots + [slot(SPARE, lamports=5)]))
    # create: size arguments around the cap.
    args, slots = keep['create']
    for size in (0, 1, 9_955, 9_956, 9_957, 10_000, 100_000, 2**64 - 45, 2**64 - 44, 2**64 - 1):
        cases.append((command(0, struct.pack('<Q', size)), slots))
    cases.append((args, [replace(slots[0], lamports=rent(144) - 1)] + slots[1:]))
    cases.append((args, [replace(slots[0], lamports=rent(144))] + slots[1:]))
    cases.append((args, [replace(slots[0], data=bytes(4))] + slots[1:]))
    cases.append((args, [replace(slots[0], owner='p')] + slots[1:]))
    cases.append((args, [slots[0], replace(slots[1], lamports=1)] + slots[2:]))
    cases.append((args, [slots[0], replace(slots[1], lamports=rent(144), owner='p', data=bytes(144))] + slots[2:]))
    # create_buffer: stored bytes kept, rent edge, sizes around the header.
    args, slots = keep['create_buffer']
    for size in (0, 7, 8, 9, 43, 44, 45, 10_000):
        cases.append((args, [replace(slots[0], data=bytes(size), lamports=rent(size))] + slots[1:]))
    for lamports in (rent(300) - 1, rent(300), rent(300) + 1):
        cases.append((args, [replace(slots[0], lamports=lamports)] + slots[1:]))
    tail = bytes(8) + bytes([9] * 32) + struct.pack('<I', 77) + b'kept' + bytes(100)
    cases.append((args, [replace(slots[0], data=tail, lamports=rent(len(tail)))] + slots[1:]))
    # write: lengths around the room left, stored data_len beyond the room.
    args, slots = keep['write']
    for size, data_len, n in ((60, 5, 11), (60, 5, 12), (44, 0, 0), (44, 0, 1), (50, 6, 0), (50, 7, 0), (50, 2**32 - 1, 0),
                              (50, 2**32 - 1, 1), (50, 2**31, 2), (200, 0, 156), (200, 0, 157)):
        body = command(2, struct.pack('<I', n), bytes(range(n % 251)) + bytes(max(0, n - 251)))
        cases.append((body, [idl_slot(data_len=data_len, size=size, fill=3)] + slots[1:]))
    # set_buffer: capacity, stored lengths, one account in both slots.
    args, slots = keep['set_buffer']
    for buffer_size, buffer_len, idl_size, idl_len in ((120, 20, 64, 2), (120, 20, 63, 2), (120, 76, 200, 2),
                                                       (120, 77, 200, 2), (44, 0, 44, 9), (100, 0, 200, 90),
                                                       (120, 2**32 - 1, 200, 2)):
        cases.append((args, [idl_slot(BUFFER, data_len=buffer_len, size=buffer_size, fill=7),
                             idl_slot(data_len=idl_len, size=idl_size, fill=9), slots[2]]))
    cases.append((args, [slots[1], slots[1], slots[2]]))
    cases.append((args, [idl_slot(BUFFER, authority=ROGUE, data_len=20, size=120, fill=7), slots[1], slots[2]]))
    # set_authority: to self, to the zero key, then the erased key cannot sign.
    args, slots = keep['set_authority']
    cases.append((command(4, bytes(AUTHORITY)), slots))
    cases.append((command(4, bytes(32)), slots))
    # close: destination aliases and balances.
    args, slots = keep['close']
    cases.append((args, [slots[0], slots[1], slots[0]]))
    cases.append((args, [slots[0], replace(slots[1], writable=True), slot(AUTHORITY, writable=True, lamports=RICH)]))
    cases.append((args, slots[:2] + [slot(DESTINATION, writable=True)]))
    cases.append((args, slots[:2] + [slot(DESTINATION, writable=True, owner='p', lamports=rent(4), data=b'abcd')]))
    cases.append((args, slots[:2] + [slot(BUFFER, writable=True, owner='p', lamports=rent(50), data=idl_bytes(size=50))]))
    cases.append((args, [idl_slot(data_len=2**32 - 1, size=44)] + slots[1:]))
    cases.append((args, [idl_slot(lamports=2)] + slots[1:]))
    for owner in 'spo':
        for data in (b'', b'1'):
            poor = slot(DESTINATION, writable=True, owner=owner, lamports=7, data=data)
            cases.append((args, [idl_slot(lamports=2, data_len=5), slots[1], poor]))
            enough = slot(DESTINATION, writable=True, owner=owner, lamports=rent(len(data)) - 2, data=data)
            cases.append((args, [idl_slot(lamports=2, data_len=5), slots[1], enough]))
    # resize: smaller, equal, one more, the step cap, stored data_len, funds.
    args, slots = keep['resize']
    for size in (0, 199, 200, 201, 10_199, 10_200, 10_201, 2**63, 2**64 - 1):
        cases.append((command(6, struct.pack('<Q', size)), slots))
    cases.append((args, [idl_slot(data_len=1)] + slots[1:]))
    cases.append((args, [slots[0], authority_slot(writable=True, lamports=rent(500) - rent(200) - 1), slots[2]]))
    cases.append((args, [slots[0], authority_slot(writable=True, lamports=rent(500) - rent(200)), slots[2]]))
    cases.append((args, [idl_slot(lamports=rent(500)), authority_slot(writable=True, lamports=0), slots[2]]))
    cases.append((args, [idl_slot(lamports=rent(500) + 1)] + slots[1:]))
    cases.append((args, [idl_slot(lamports=rent(500) - 1)] + slots[1:]))
    cases.append((args, [slots[0], replace(slots[1], data=bytes(3)), slots[2]]))
    cases.append((args, [slots[0], replace(slots[1], owner='p'), slots[2]]))
    # The zero key as authority: a signature from it passes every other check.
    zero = slot(SYSTEM, signer=True, owner='o', lamports=1, executable=True)
    zero_idl = idl_slot(authority=SYSTEM, data_len=5, size=120, fill=3)
    frozen = replace(zero_idl, writable=False)
    rogue_idl = idl_slot(authority=ROGUE, data_len=5, size=120, fill=3)
    for op in ('write', 'set_authority'):
        args = keep[op][0]
        cases += [(args, [zero_idl, zero]), (args, [frozen, zero]), (args, [rogue_idl, zero])]
    args = keep['set_buffer'][0]
    zero_buffer = idl_slot(BUFFER, authority=SYSTEM, data_len=5, size=120, fill=3)
    cases += [(args, [zero_buffer, zero_idl, zero]), (args, [zero_buffer, frozen, zero]),
              (args, [replace(zero_buffer, writable=False), zero_idl, zero]),
              (args, [idl_slot(BUFFER, authority=ROGUE, size=120), rogue_idl, zero])]
    args = keep['create_buffer'][0]
    blank = slot(BUFFER, writable=True, owner='p', lamports=rent(300), data=bytes(300))
    cases += [(args, [blank, zero]), (args, [replace(blank, lamports=1), zero]),
              (args, [replace(blank, writable=False), zero])]
    args = keep['close'][0]
    open_end = slot(DESTINATION, writable=True, lamports=7)
    cases += [(args, [zero_idl, zero, open_end]), (args, [zero_idl, zero, zero_idl]),
              (args, [zero_idl, zero, replace(open_end, writable=False)]), (args, [frozen, zero, open_end]),
              (args, [rogue_idl, keep['close'][1][1], rogue_idl]), (args, [rogue_idl, zero, rogue_idl]),
              (args, [frozen, keep['close'][1][1], frozen])]
    args = keep['resize'][0]
    system = keep['resize'][1][2]
    cases += [(args, [zero_idl, zero, system]), (args, [zero_idl, replace(zero, writable=True), system]),
              (args, [frozen, replace(zero, writable=True), system]),
              (args, [idl_slot(lamports=rent(500)), authority_slot(writable=True, lamports=5) | {'owner': 'o'}, system]),
              (args, [idl_slot(lamports=rent(500) - 1), authority_slot(writable=True, lamports=5) | {'owner': 'o'},
                      system]),
              (command(6, struct.pack('<Q', 200)), [idl_slot(lamports=rent(200) + 1)] + keep['resize'][1][1:]),
              (command(6, struct.pack('<Q', 200)), [idl_slot(lamports=1)] + keep['resize'][1][1:])]
    return cases


def fault_cases():
    single, double = [], []
    for op in OPS:
        args, slots = template(op)
        spoiled = [list(slot_faults(a).values()) for a in slots]
        later = [list(slot_faults(a, SECOND_SPARE).values()) for a in slots]
        for i, faults in enumerate(spoiled):
            single += [(args, slots[:i] + [f] + slots[i + 1:]) for f in faults]
        for i in range(len(slots)):
            for j in range(i + 1, len(slots)):
                for first in spoiled[i]:
                    for second in later[j]:
                        changed = list(slots)
                        changed[i], changed[j] = first, second
                        double.append((args, changed))
    return single, double


def random_walk(vm, rng, steps):
    """Yield (args, slots, answer) with slots read from what the VM holds."""
    vm.load([])
    for key in (AUTHORITY, ROGUE):
        vm.vm.set_account(key, Account(RICH, b'', SYSTEM))
    vm.vm.set_account(BUFFER, Account(rent(600), bytes(600), PUMP))
    vm.vm.set_account(SPARE, Account(rent(44), bytes(44), PUMP))

    def account(key, signer=False, writable=False):
        owner, lamports, data = vm.state(key)
        return slot(key, signer, writable, owner, lamports, data)

    def fresh(*metas):
        return [system_slot() if m[0] == SYSTEM else program_slot() if m[0] == PUMP else account(*m) for m in metas]

    for _ in range(steps):
        target = rng.choice((CANONICAL, CANONICAL, BUFFER, SPARE))
        signer = rng.choice((AUTHORITY, AUTHORITY, ROGUE))
        roll = rng.randrange(7)
        if roll == 0:
            args = command(0, struct.pack('<Q', rng.choice((0, 50, 300, 20_000))))
            metas = ((signer, True, True), (CANONICAL, False, True), (BASE,), (SYSTEM,), (PUMP,))
        elif roll == 1:
            args = command(1)
            metas = ((target, False, True), (signer, True))
        elif roll == 2:
            body = rng.randbytes(rng.choice((0, 1, 40, 300)))
            args = command(2, struct.pack('<I', len(body)), body)
            metas = ((target, False, True), (signer, True))
        elif roll == 3:
            args = command(3)
            metas = ((BUFFER, False, True), (target, False, True), (signer, True))
        elif roll == 4:
            args = command(4, bytes(rng.choice((AUTHORITY, ROGUE))))
            metas = ((target, False, True), (signer, True))
        elif roll == 5:
            args = command(5)
            metas = ((target, False, True), (signer, True), (DESTINATION, False, True))
        else:
            current = len(vm.state(target)[2])
            args = command(6, struct.pack('<Q', max(current + rng.choice((-1, 0, 1, 500, 9_999, 10_000, 10_001)), 0)))
            metas = ((target, False, True), (signer, True, True), (SYSTEM,))
        slots = fresh(*metas)
        yield args, slots, vm.run(args, slots)


def admin_rewrite(vm, new_authority):
    """Run `admin_set_idl_authority` on the canonical account, authority ROGUE."""
    global_data = bytearray(1088)
    global_data[:8] = GLOBAL_DISC
    global_data[8] = 1
    global_data[9:41] = bytes(ROGUE)
    vm.vm.set_account(GLOBAL, Account(10**9, bytes(global_data), PUMP))
    keys = {'authority': ROGUE, 'global': GLOBAL, 'idl_account': CANONICAL, 'system_program': SYSTEM,
            'program_signer': BASE, 'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    metas = [AccountMeta(keys[a['name']], bool(a.get('signer')), bool(a.get('writable'))) for a in ADMIN_SET['accounts']]
    vm.vm.expire_blockhash()
    blockhash = vm.vm.latest_blockhash()
    data = bytes(ADMIN_SET['discriminator']) + bytes(new_authority)
    message = Message.new_with_blockhash([Instruction(PUMP, data, metas)], PAYER.pubkey(), blockhash)
    tx = Transaction.new_unsigned(message)
    tx.partial_sign([PAYER], blockhash)
    return vm.vm.send_transaction(tx)


class AnchorIdlCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest() == PUMP_SHA256
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'anchor-idl-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host
        cls.vm = Vm()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, lines):
        head = ','.join(bytes(k).hex() for k in (PUMP, BASE, CANONICAL))
        result = subprocess.run([str(self.host)], input='\n'.join([head] + lines) + '\n', capture_output=True,
                                text=True, check=True)
        return result.stdout.splitlines()

    def captured(self, cases):
        answers = []
        for args, slots in cases:
            self.vm.load(slots)
            answers.append(self.vm.run(args, slots))
        return answers

    def compare(self, cases, captured):
        hosted = self.host_answers([host_line(args, slots) for args, slots in cases])
        self.assertEqual(len(hosted), len(captured))
        wrong = [(i, cases[i][0].hex()[:40], h[:120], c[:120]) for i, (h, c) in enumerate(zip(hosted, captured))
                 if h != c]
        self.assertEqual(wrong[:6], [], f'{len(wrong)} of {len(captured)} differ')

    def test_every_command_succeeds_on_its_template(self):
        cases = [template(op) for op in OPS]
        answers = self.captured(cases)
        self.assertEqual([a.split(';')[0] for a in answers],
                         ['ok:IdlCreateAccount', 'ok:IdlCreateBuffer', 'ok:IdlWrite', 'ok:IdlSetBuffer',
                          'ok:IdlSetAuthority', 'ok:IdlCloseAccount', 'ok:IdlResizeAccount'])
        self.compare(cases, answers)

    def test_decode_sizes_and_balances(self):
        cases = fixed_cases()
        self.assertGreater(len(cases), 100)
        self.compare(cases, self.captured(cases))

    def test_each_slot_fault(self):
        cases = fault_cases()[0]
        self.compare(cases, self.captured(cases))

    def test_fault_pairs_pin_the_check_order(self):
        cases = fault_cases()[1]
        self.compare(cases, self.captured(cases))

    def test_commands_after_the_admin_rewrite(self):
        self.vm.load([])
        self.vm.vm.set_account(AUTHORITY, Account(RICH, b'', SYSTEM))
        self.vm.vm.set_account(ROGUE, Account(RICH, b'', SYSTEM))
        args, slots = template('create')
        self.assertTrue(self.vm.run(args, slots).startswith('ok:IdlCreateAccount'))
        owner, _lamports, data = self.vm.state(CANONICAL)
        self.vm.vm.set_account(CANONICAL, Account(rent(10_240), data, PUMP))
        self.assertNotIsInstance(admin_rewrite(self.vm, ROGUE), FailedTransactionMetadata)
        self.assertEqual(self.vm.state(CANONICAL)[2][8:40], bytes(ROGUE))
        self.assertEqual(len(self.vm.state(CANONICAL)[2]), 10_240)

        def account(key, signer=False, writable=False):
            state = self.vm.state(key)
            return slot(key, signer, writable, state[0], state[1], state[2])

        cases, answers = [], []
        body = command(2, struct.pack('<I', 5), b'after')
        for signer in (AUTHORITY, ROGUE):
            for args, writable in ((body, False), (command(6, struct.pack('<Q', 10_300)), True),
                                   (command(4, bytes(ROGUE)), False)):
                accounts = [account(CANONICAL, writable=True), account(signer, signer=True, writable=writable)]
                accounts += [system_slot()] if writable else []
                cases.append((args, accounts))
                answers.append(self.vm.run(args, accounts))
        self.assertEqual(answers[0], 'error:2001:idl')
        self.assertTrue(answers[3].startswith('ok:IdlWrite'))
        self.compare(cases, answers)

    def test_random_walk_on_one_vm(self):
        rng = random.Random(20261031)
        cases, answers = [], []
        for _ in range(60):
            for args, slots, answer in random_walk(self.vm, rng, 40):
                cases.append((args, slots))
                answers.append(answer)
        self.assertGreater(sum(a.startswith('ok:') for a in answers), 300)
        self.compare(cases, answers)


if __name__ == '__main__':
    unittest.main()
