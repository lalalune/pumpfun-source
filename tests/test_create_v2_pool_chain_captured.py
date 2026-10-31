"""Captured-program checks for pool records in a `create_v2` quote chain.

`tests/test_create_v2_quote_pool_captured.py` prices a coin quoted by one
migrated curve from that curve's pool record. Every case here runs
`create_v2` from the captured `evidence/original/pump/deployed.so` on
LiteSVM, through the fixture of `tests/test_create_v2_captured.py`, on a
quote chain of two or three curves: the passed curve's stored depth says
how many curves stand under it, each empty curve is priced from its own
pool record, and the root curve seeds the price. Vaults may hold genuine
Token-2022 extension bytes past the account-type byte. The same chain goes
to `programs/pump/recovered/create_v2_pool_chain_host.rs`, and the error
code or the new curve's virtual quote reserves and depth must agree. This
shows matching behavior on these inputs only; it is not a byte-identity
claim.
"""
from pathlib import Path
import hashlib
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.instruction import AccountMeta
from solders.pubkey import Pubkey

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_create_v2_captured as base  # noqa: E402
import test_create_v2_quote_pool_captured as pool_base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOST_SOURCE = ROOT / 'programs/pump/recovered/create_v2_pool_chain_host.rs'
AMM = pool_base.AMM
POOL_DISC = pool_base.POOL_DISCRIMINATOR
ELSEWHERE = pool_base.ELSEWHERE
STRANGER = base.STRANGER
D_MINT = Pubkey.from_bytes(bytes([73]) * 32)
U64 = 2**64 - 1
I128 = 2**127 - 1
PROGRAMS = {'token': base.TOKEN, 'token22': base.TOKEN22, 'system': base.SYSTEM}
original_setup = base.quote_setup

PB = (3 * 10**14, 5 * 10**10)
PC = (7 * 10**14, 2 * 10**10)
PD = (9 * 10**14, 4 * 10**10)


def canonical(mint, quote):
    authority = base.pda(b'pool-authority', bytes(mint))
    return Pubkey.find_program_address([b'pool', bytes(2), bytes(authority), bytes(mint), bytes(quote)], AMM)[0]


def curve_data(spec, root_key):
    data = bytearray(166)
    data[:8] = base.ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, spec['vt'], spec['vq'], spec['rt'], spec['rq'], spec['supply'])
    data[48] = spec['complete']
    data[49:81] = bytes(base.CREATOR)
    data[81] = spec['mayhem']
    if root_key is not None:
        data[83:115] = bytes(root_key)
    data[141] = spec['depth']
    return bytes(data)


def pool_data(spec, bv_key, qv_key):
    data = bytearray(max(spec['len'], 301))
    data[:8] = POOL_DISC if spec['disc_ok'] else bytes(8)
    data[139:171] = bytes(bv_key if spec['base_key_ok'] else ELSEWHERE)
    data[171:203] = bytes(qv_key if spec['quote_key_ok'] else ELSEWHERE)
    data[245:261] = spec['adj'].to_bytes(16, 'little', signed=True)
    return bytes(data[:spec['len']])


def vault_data(spec):
    data = bytearray(max(spec['len'], 166))
    data[32:64] = bytes(base.USER.pubkey())
    struct.pack_into('<Q', data, 64, spec['amount'])
    data[108] = spec['state']
    if spec['len'] > 165:
        data[165] = spec['atype']
        data[166:166 + len(spec['tlv'])] = spec['tlv']
    return bytes(data[:spec['len']])


def vault(amount, owner='token', length=165, state=1, atype=2, tlv=b''):
    return dict(owner=owner, len=length, state=state, atype=atype, amount=amount, tlv=tlv)


def record(base_amt, quote_amt, adj=0, parts=3, bv=None, qv=None, **pool):
    spec = dict(parts=parts, key_ok=1, owner_ok=1, len=301, disc_ok=1, base_key_ok=1, quote_key_ok=1, adj=adj)
    spec.update(pool)
    spec['bv'] = bv if bv is not None else vault(base_amt)
    spec['qv'] = qv if qv is not None else vault(quote_amt)
    return spec


def curve(depth=0, mayhem=0, complete=0, vt=0, vq=0, rt=0, rq=0, supply=10**15, root='unlisted'):
    return dict(depth=depth, mayhem=mayhem, complete=complete, vt=vt, vq=vq, rt=rt, rq=rq,
                supply=supply, root=root)


def inner(mint, root_key=None, valid='ok', raw=None, **fields):
    spec = curve(**fields)
    spec.update(mint=mint, root_key=root_key, valid=valid, raw=raw)
    return spec


def build(head, inners=(), records=None, max_depth=2, entries=None):
    item = base.case(quote='curve', max_depth=max_depth)
    item['curve'] = dict(depth=head['depth'], mayhem=head['mayhem'], complete=head['complete'],
                         vt=head['vt'], vq=head['vq'], rt=head['rt'], rq=head['rq'],
                         supply=head['supply'], root=head['root'])
    item['chain'] = dict(curves=[head] + list(inners), records=records or {}, entries=entries)
    return item


def root_key_of(spec):
    """The stored root key of a head curve spec (base fixture vocabulary)."""
    root = spec['root']
    if root == 'sol':
        return None
    if root == 'whitelisted':
        return base.WHITELISTED
    return base.ROOT_QUOTE


def root_token(spec, entries):
    """The host's root token for any curve spec in the chain."""
    if 'root_key' in spec:  # an inner curve
        key = spec['root_key']
        if key is None:
            return 'sol'
        if key == base.WHITELISTED:
            return 'whitelisted'
        listed = dict(entries or ())
        return f'listed:{listed[key]}' if key in listed else 'unlisted'
    root = spec['root']
    if root in ('sol', 'whitelisted', 'unlisted'):
        return root
    return f'listed:{root}'


def host_line(item):
    ch = item['chain']
    fields = [item['vtr'], item['vsr'], item['rtr'], item['ivqr'], item['migration_fee'],
              item['max_depth'], len(ch['curves'])]
    for spec in ch['curves']:
        valid = 1 if spec.get('valid', 'ok') == 'ok' and spec.get('raw') is None else 0
        fields += [spec['depth'], spec['mayhem'], spec['complete'], spec['vt'], spec['vq'],
                   spec['rt'], spec['rq'], spec['supply'], root_token(spec, ch['entries']), valid]
    # The account stream as chain_setup appends it: each curve, then the
    # record accounts passed after it. The walk reads the pool and vault
    # slots positionally, so a short record's slots are filled by whatever
    # account follows; a curve or pool account read as a vault is not a
    # token vault and fails the owner check there.
    stream = []
    for i, spec in enumerate(ch['curves']):
        stream.append(('curve', i, 0))
        rec = ch['records'].get(i)
        if rec is not None and spec.get('raw') is None:
            stream += [('rec', i, k) for k in range(rec['parts'])]
    at = {entry[1]: n for n, entry in enumerate(stream) if entry[0] == 'curve'}
    for i, spec in enumerate(ch['curves']):
        rec = ch['records'].get(i)
        has_pool = rec is not None and spec.get('raw') is None and rec['parts'] >= 1
        fields += [len(stream) - at[i], int(has_pool)]
        if not has_pool:
            continue
        fields += [rec['key_ok'], rec['owner_ok'], rec['len'], rec['disc_ok'], rec['base_key_ok'],
                   rec['quote_key_ok']]
        for slot in (at[i] + 2, at[i] + 3):
            entry = stream[slot] if slot < len(stream) else None
            if entry is not None and entry[0] == 'rec' and entry[1] == i and entry[2] in (1, 2):
                v = rec['bv'] if entry[2] == 1 else rec['qv']
                fields += [int(v['owner'] != 'system'), v['len'], v['state'], v['atype'], v['amount']]
            else:
                fields += [0, 166, 1, 2, 0]
        fields.append(rec['adj'])
    return ','.join(map(str, fields))


def chain_setup(vm, item):
    metas = original_setup(vm, item)
    ch = item['chain']
    if ch['entries'] is not None:
        vm.set_account(base.pda(b'quote-control'),
                       Account(10**9, base.control_data(ch['entries']), base.PUMP))
    out = list(metas)
    specs = ch['curves']
    mints = [base.CONTROLLED] + [s['mint'] for s in specs[1:]]
    root_keys = [root_key_of(specs[0])] + [s['root_key'] for s in specs[1:]]
    for i, spec in enumerate(specs):
        if i > 0:
            if spec['raw'] == 'pool':
                # A pool account where the walk expects the next curve.
                key = canonical(spec['mint'], root_keys[i] or base.NATIVE)
                fake = record(10**14, 10**10)
                bv_key = Pubkey.from_bytes(bytes([90 + 10 * i]) * 32)
                qv_key = Pubkey.from_bytes(bytes([91 + 10 * i]) * 32)
                vm.set_account(key, Account(10**7, pool_data(fake, bv_key, qv_key), AMM))
                out.append(AccountMeta(key, False, False))
                continue
            key = base.pda(b'bonding-curve', bytes(spec['mint'])) if spec['valid'] != 'key' else ELSEWHERE
            data = curve_data(spec, spec['root_key'])
            if spec['valid'] == 'data':
                data = bytes(8) + data[8:]
            owner = base.PUMP if spec['valid'] != 'owner' else STRANGER
            vm.set_account(key, Account(10**7, data, owner))
            out.append(AccountMeta(key, False, False))
        rec = ch['records'].get(i)
        if rec is None or rec['parts'] == 0:
            continue
        bv_key = Pubkey.from_bytes(bytes([90 + 10 * i]) * 32)
        qv_key = Pubkey.from_bytes(bytes([91 + 10 * i]) * 32)
        quote = root_keys[i] or base.NATIVE
        key = canonical(mints[i], quote) if rec['key_ok'] else ELSEWHERE
        vm.set_account(key, Account(10**7, pool_data(rec, bv_key, qv_key), AMM if rec['owner_ok'] else base.PUMP))
        accounts = [AccountMeta(key, False, False),
                    AccountMeta(bv_key, False, False), AccountMeta(qv_key, False, False)]
        vm.set_account(bv_key, Account(10**7, vault_data(rec['bv']), PROGRAMS[rec['bv']['owner']]))
        vm.set_account(qv_key, Account(10**7, vault_data(rec['qv']), PROGRAMS[rec['qv']['owner']]))
        out += accounts[:rec['parts']]
    return out


def tlv(etype, value):
    return struct.pack('<HH', etype, len(value)) + value


def fixed_cases():
    cases = []
    add = lambda *a, **k: cases.append(build(*a, **k))
    empty_b = curve(depth=1)
    rich_c = dict(vt=10**15, vq=3 * 10**10, rt=8 * 10**14, rq=10**9)
    # Two empty curves, priced from two records.
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB, adj=10**9), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC, adj=-10**9)})
    add(empty_b, [inner(base.ROOT_QUOTE, root_key=base.WHITELISTED)], {0: record(*PB), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE, root_key=D_MINT)], {0: record(*PB), 1: record(*PC)},
        entries=[(D_MINT, 123_456_789)])
    add(empty_b, [inner(base.ROOT_QUOTE, root_key=D_MINT)], {0: record(*PB), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE, root_key=D_MINT)], {0: record(*PB), 1: record(*PC)},
        entries=[(D_MINT, 0)])
    # Mixed levels.
    add(empty_b, [inner(base.ROOT_QUOTE, **rich_c)], {0: record(*PB)})
    add(curve(depth=1, **rich_c), [inner(base.ROOT_QUOTE)], {1: record(*PC)})
    add(curve(depth=1, **rich_c), [inner(base.ROOT_QUOTE, **rich_c)], {})
    add(curve(depth=1, **rich_c), [inner(base.ROOT_QUOTE, **dict(rich_c, complete=1))], {})
    add(empty_b, [inner(base.ROOT_QUOTE, vt=10**15, vq=3 * 10**10, rt=10**12, rq=10**9)], {0: record(*PB)})
    # Staged accounts, in the order the walk reads them.
    add(empty_b, [], {})
    add(empty_b, [], {0: record(*PB)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC, parts=2)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB, parts=2), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB, parts=1), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB, key_ok=0), 1: record(*PC)})
    add(empty_b, [], {0: record(*PB, key_ok=0)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC, owner_ok=0)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB, owner_ok=0), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC, len=210)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB, disc_ok=0), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC, base_key_ok=0)})
    for valid in ('key', 'owner', 'data'):
        add(empty_b, [inner(base.ROOT_QUOTE, valid=valid)], {0: record(*PB), 1: record(*PC)})
    add(curve(depth=1, **rich_c), [inner(base.ROOT_QUOTE, raw='pool')], {})
    # Depth gates.
    add(curve(depth=2), [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC)}, max_depth=2)
    add(curve(depth=2), [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC)}, max_depth=3)
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC)}, max_depth=1)
    add(curve(depth=3), [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC)}, max_depth=5)
    # Level-0 order: mayhem and completion before the deeper checks.
    add(curve(depth=1, mayhem=1), [], {})
    add(curve(depth=1, mayhem=1), [inner(base.ROOT_QUOTE)], {0: record(*PB, key_ok=0), 1: record(*PC)})
    add(curve(depth=1, complete=1, **rich_c), [], {})
    add(curve(depth=1, complete=1), [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC)})
    # The root curve's root is resolved before its own record is required.
    add(curve(depth=0, root='unlisted'), [], {})
    add(curve(depth=0, root='unlisted'), [], {0: record(*PB, key_ok=0)})
    add(curve(depth=0, root='sol'), [], {})
    add(curve(depth=0, root='sol'), [], {0: record(*PB)})
    # Inner flags the walk does not read.
    add(empty_b, [inner(base.ROOT_QUOTE, mayhem=1, **rich_c)], {0: record(*PB)})
    add(empty_b, [inner(base.ROOT_QUOTE, mayhem=1)], {0: record(*PB), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE, depth=1)], {0: record(*PB), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE, depth=2)], {0: record(*PB), 1: record(*PC)})
    add(empty_b, [inner(base.ROOT_QUOTE, complete=1)], {0: record(*PB), 1: record(*PC)})
    # Three curves, three records.
    deep = [inner(base.ROOT_QUOTE, root_key=D_MINT), inner(D_MINT)]
    add(curve(depth=2), deep, {0: record(*PB), 1: record(*PC), 2: record(*PD)}, max_depth=3)
    add(curve(depth=2), [inner(base.ROOT_QUOTE, root_key=D_MINT, **rich_c), inner(D_MINT)],
        {0: record(*PB), 2: record(*PD)}, max_depth=3)
    add(curve(depth=2), deep, {0: record(*PB), 1: record(*PC, key_ok=0), 2: record(*PD)}, max_depth=3)
    add(curve(depth=2), [inner(base.ROOT_QUOTE, root_key=D_MINT),
                         inner(D_MINT, valid='key')], {0: record(*PB), 1: record(*PC), 2: record(*PD)},
        max_depth=3)
    add(curve(depth=2), deep, {0: record(*PB), 1: record(*PC), 2: record(*PD)}, max_depth=2)
    # Extra accounts past the depth are not read: the middle curve stays the
    # root, so its unlisted root decides, and a listing prices without them.
    add(empty_b, deep, {0: record(*PB), 1: record(*PC), 2: record(*PD)})
    add(empty_b, deep, {0: record(*PB), 1: record(*PC), 2: record(*PD)}, entries=[(D_MINT, 123_456_789)])
    # Token-2022 extension vaults, at the root record and inside a chain.
    ext = [dict(owner='token22', length=201, tlv=tlv(7, bytes(32))),
           dict(owner='token22', length=177, tlv=tlv(2, bytes(8))),
           dict(owner='token22', length=260, tlv=tlv(7, bytes(32)) + tlv(2, bytes(8))),
           dict(owner='token22', length=200, tlv=struct.pack('<HH', 7, 100) + bytes(30)),
           dict(owner='token22', length=180, tlv=tlv(0, bytes(10))),
           dict(owner='token22', length=168, tlv=b'\x07\x00'),
           dict(owner='token22', length=169, tlv=b'\x07\x00\x20'),
           dict(owner='token', length=201, tlv=tlv(7, bytes(32)))]
    for spec in ext:
        add(curve(depth=0, root='sol'), [], {0: record(*PB, qv=vault(PB[1], **spec))})
    add(curve(depth=0, root='sol'), [], {0: record(*PB, qv=vault(PB[1], owner='token22', length=355,
                                                     tlv=tlv(7, bytes(32))))})
    add(curve(depth=0, root='sol'), [], {0: record(*PB, qv=vault(PB[1], owner='token22', length=201,
                                                     atype=1, tlv=tlv(7, bytes(32))))})
    add(curve(depth=0, root='sol'), [], {0: record(*PB, bv=vault(PB[0], owner='token22', length=201,
                                                     tlv=tlv(7, bytes(32))))})
    add(empty_b, [inner(base.ROOT_QUOTE)],
        {0: record(*PB), 1: record(*PC, qv=vault(PC[1], owner='token22', length=201, tlv=tlv(7, bytes(32))))})
    # Value edges at the inner record price first.
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(PC[0], 0)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC, adj=-PC[1] - 1)})
    add(empty_b, [inner(base.ROOT_QUOTE)], {0: record(PB[0], 0), 1: record(*PC)})
    return cases


def random_cases(count=24, seed=771):
    rng = random.Random(seed)
    cases = []
    amount = lambda: rng.choice((1, rng.randrange(1, 10**6), rng.randrange(1, 10**14), rng.randrange(1, U64)))
    for _ in range(count):
        three = rng.random() < 0.3
        inners, records = [], {}
        levels = 3 if three else 2
        for i in range(levels):
            base_amt, quote_amt = amount(), rng.randrange(1, 10**12)
            adj = rng.choice((0, rng.randrange(-10**9, 10**9)))
            if rng.random() < 0.5:
                records[i] = record(base_amt, quote_amt, adj=adj)
        if three:
            inners = [inner(base.ROOT_QUOTE, root_key=D_MINT), inner(D_MINT)]
            head = curve(depth=2)
            if 1 not in records:
                inners[0] = inner(base.ROOT_QUOTE, root_key=D_MINT, vt=10**15,
                                  vq=rng.randrange(1, 10**12), rt=rng.randrange(0, 10**14),
                                  rq=rng.randrange(0, 10**10))
            if 2 not in records:
                inners[1] = inner(D_MINT, vt=10**15, vq=rng.randrange(1, 10**12),
                                  rt=rng.randrange(0, 10**14), rq=rng.randrange(0, 10**10))
        else:
            root_key = rng.choice((None, base.WHITELISTED, D_MINT))
            inners = [inner(base.ROOT_QUOTE, root_key=root_key)]
            head = curve(depth=1)
            if 1 not in records:
                inners[0] = inner(base.ROOT_QUOTE, root_key=root_key, vt=10**15,
                                  vq=rng.randrange(1, 10**12), rt=rng.randrange(0, 10**14),
                                  rq=rng.randrange(0, 10**10))
        if 0 not in records:
            head = curve(depth=head['depth'], vt=10**15, vq=rng.randrange(1, 10**12),
                         rt=rng.randrange(0, 10**14), rq=rng.randrange(0, 10**10))
        entries = [(D_MINT, rng.randrange(1, 10**12))] if inners[-1].get('root_key') == D_MINT else None
        cases.append(build(head, inners, records, max_depth=3 if three else 2, entries=entries))
    return cases


class CreateV2PoolChainCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in base.ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'create-v2-pool-chain-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host
        cls.patch = mock.patch.object(base, 'quote_setup', chain_setup)
        cls.patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, answer, captured):
        if answer.startswith('error:'):
            code = re.search(r'Custom\((\d+)\)', str(captured['error']))
            self.assertEqual(int(code.group(1)) if code else captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        _, reserves, depth = answer.split(',')
        curve = bytes(captured['curve'].data)
        self.assertEqual(struct.unpack_from('<Q', curve, 16)[0], int(reserves))
        self.assertEqual(struct.unpack_from('<Q', curve, 142)[0], int(reserves))
        self.assertEqual(curve[141], int(depth))
        self.assertEqual(curve[83:115], bytes(base.CONTROLLED))

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(answer, base.run_captured(item))
        return answers

    def test_fixed_cases_match_captured_program(self):
        answers = self.run_cases(fixed_cases())
        self.assertEqual({a.split(',')[0] for a in answers},
                         {'ok', *(f'error:{c}' for c in (6024, 6026, 6099, 6100, 6101, 6102, 6103, 6104, 6105, 6107, 6109))})

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_inner_adjustment_changes_the_price(self):
        # Negative control: the checker must see the inner record's stored
        # adjustment, and must reject a reserves answer that is off by one.
        plain = build(curve(depth=1), [inner(base.ROOT_QUOTE)], {0: record(*PB), 1: record(*PC)})
        adjusted = build(curve(depth=1), [inner(base.ROOT_QUOTE)],
                         {0: record(*PB), 1: record(*PC, adj=10**9)})
        self.assertNotEqual(*self.host_answers([plain, adjusted]))
        answer = self.host_answers([plain])[0]
        kind, reserves, depth = answer.split(',')
        with self.assertRaises(AssertionError):
            self.assert_matches(f'{kind},{int(reserves) + 1},{depth}', base.run_captured(plain))


if __name__ == '__main__':
    unittest.main()
