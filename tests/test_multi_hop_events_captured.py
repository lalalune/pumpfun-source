"""Captured-program checks for the events of `multi_hop_curve_swap` on
Token-2022 mints.

`tests/test_multi_hop_token2022_captured.py` runs the same routes and
compares the error, the curve bytes, the vaults, the withheld fees, the
user's accounts and the returned `CurveRunResult` — and says there that
events are not compared. This packet compares them: every successful route
must also emit exactly the events `programs/pump/recovered/multi_hop_events.rs`
records, byte for byte, both in the transaction logs (`Program data:` lines)
and in the program's self-CPI copies of them. The state comparison itself is
reused unchanged, and the recording model cross-checks its settlement
against the Token-2022 model on every route, so the two cannot drift apart.
Signature verification is off and account state is synthetic, exactly as in
the packet this extends. This shows matching behavior on these inputs only;
it is not a byte-identity claim.

Unconfirmed: the events of a route that fails after an earlier hop (they
appear in the failed transaction's logs but commit nothing, so they are not
compared), and a completion event for a buy that drains a curve whose real
reserves were already zero, and exact-drain/no-post-completion routes not exercised here. The fee recipient, the volume accumulator,
cashback, holder rewards and the shareholder list are pinned at what these
fixtures emit: the fixture Global never sets a fee recipient, no volume
account is seeded, and a cashback coin that would charge the creator fee is
refused before any event.

One self-CPI is not an event: a native hop that pays a nonzero buyback in
lamports first calls the program with the event tag as the call's entire
data, before its trade event. It leaves no log line. This packet pins its
presence, position and condition only; what the call does is not modelled.
"""
from pathlib import Path
import base64
import json
import struct
import subprocess
import sys
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.message import Message
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_multi_hop_token2022_captured as t22  # noqa: E402

base = t22.base
ROOT = Path(__file__).resolve().parents[1]
HOST_SOURCE = ROOT / 'programs/pump/recovered/multi_hop_events_host.rs'

PUMP, TOKEN, TOKEN22, SYSTEM = t22.PUMP, t22.TOKEN, t22.TOKEN22, t22.SYSTEM
USER, MINTS, TS = base.USER, base.MINTS, base.TS
USER_LAMPORTS, TX_FEE = base.USER_LAMPORTS, base.TX_FEE
TOKEN_RENT = base.TOKEN_RENT
EVENT_IX_TAG = bytes([228, 69, 165, 46, 81, 203, 154, 29])
ZERO_KEY = bytes(32)
TRADE_DISC = bytes.fromhex('bddb7fd34ee661ee')
COMPLETE_DISC = bytes.fromhex('5f72619cd42e9808')
POST_DISC = bytes.fromhex('6fb06d8b316cd5fb')
FIXED_EVENTS = (1648, 129, 129, 94)  # trades, completes, posts, bare self-CPIs over the fixed routes
RANDOM_EVENTS = (616, 67, 67, 61)


def flat(data):
    return bytes(data[1:]) if data and isinstance(data[0], list) else bytes(data)


def self_cpi_payloads(inner, keys):
    """Only Pump-targeted instructions are Pump self-CPI copies."""
    out = []
    for item in inner:
        ix = item['instruction']
        if keys[ix['programIdIndex']] != PUMP:
            continue
        data = flat(ix['data'])
        if data.startswith(EVENT_IX_TAG):
            out.append(data)
    return out


_HOST = None


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'multi_hop_events_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def events_model(routes):
    text = ''.join(t22.host_line(r) + '\n' for r in routes)
    answers = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    if len(answers) != len(routes):
        raise ValueError(f'events host returned {len(answers)} answers for {len(routes)} routes')
    return answers


class Chain(t22.Chain):
    """The Token-2022 packet's chain, also returning each run's events."""

    def run(self, r):
        vm = self.vm
        self.slot += 1
        vm.set_clock(Clock(self.slot, 0, r['epoch'], 0, TS))
        vm.expire_blockhash()
        for key in self.stale:
            vm.set_account(key, Account(0, b'', SYSTEM))
        user = USER.pubkey()
        state = {base.GLOBAL: (10**9, PUMP, base.global_data(r)), base.FEE_CONFIG: (10**9, t22.FEES, base.fee_config_data()),
                 user: (USER_LAMPORTS, SYSTEM, b'')}
        for i, m in enumerate(MINTS):
            state[m] = (10**9, t22.program_of(r, i), t22.mint_data(t22.mint_spec(r, i), 9 if i == 0 else 6))
        vaults = []
        for c in r['curves']:
            key = base.curve_key(c)
            native = c['quote'] == 0
            state[key] = (base.CURVE_RENT + (c['rqr'] + c['cf'] + c['pf'] if native else 0), PUMP, base.curve_data(c))
            base_program = t22.program_of(r, c['base'])
            quote_program = t22.program_of(r, c['quote'])
            other = lambda p: TOKEN if p == TOKEN22 else TOKEN22
            bv = t22.ata(key, c['base'], other(base_program) if c['base_wrong'] else base_program)
            qv = t22.ata(key, c['quote'], other(quote_program) if c['quote_wrong'] else quote_program)
            state[bv] = (10**9, base_program, t22.token_data(r, c['base'], key, c['base_vault'], c['base_frozen'], c['base_bare']))
            state[qv] = (TOKEN_RENT, quote_program, t22.token_data(r, c['quote'], key, c['quote_vault'], c['quote_frozen'], c['quote_bare']))
            vaults.append((bv, qv))

        def user_ata(mint_id, amount, frozen, **ext):
            key = t22.ata(user, mint_id, t22.program_of(r, mint_id))
            state[key] = (TOKEN_RENT + (amount if mint_id == 0 else 0), t22.program_of(r, mint_id),
                          t22.token_data(r, mint_id, user, amount, frozen, **ext))
            return key

        source = user_ata(r['source'], r['source_balance'], r['source_frozen'], flags=t22.tlv(11, b'\1') if r['source_guard'] else b'')
        destination = source if r['destination'] == r['source'] else user_ata(r['destination'], 0, r['destination_frozen'], bare=r['destination_bare'],
                                                                              flags=t22.tlv(8, b'\1') if r['destination_memo'] else b'')
        recipient_program = t22.program_of(r, r['recipient'])
        recipient_owner = (TOKEN if recipient_program == TOKEN22 else TOKEN22) if r['recipient_wrong'] else recipient_program
        recipient = t22.ata(base.BUYBACK, r['recipient'], recipient_program)
        state[recipient] = (TOKEN_RENT, recipient_owner, t22.token_data(r, r['recipient'], base.BUYBACK, 0, bare=r['recipient_bare']))
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
        logs = meta.logs()
        inner = [i for group in json.loads(result.to_json()).get('inner_instructions') or [] for i in group]
        raw = lambda key: bytes(vm.get_account(key).data)
        amount = lambda key: struct.unpack_from('<Q', raw(key), 64)[0]
        curves = []
        for c, (bv, qv) in zip(r['curves'], vaults):
            key = base.curve_key(c)
            a = vm.get_account(key)
            curves.append(dict(data=bytes(a.data), lamports=a.lamports - state[key][0], base_vault=amount(bv), quote_vault=amount(qv),
                               base_withheld=t22.withheld_of(raw(bv)), quote_withheld=t22.withheld_of(raw(qv))))
        rollback_errors = []
        if failed:
            for key, (lamports, owner, data) in state.items():
                after = vm.get_account(key)
                expected = lamports - TX_FEE if key == user else lamports
                if after is None or after.lamports != expected or after.owner != owner or bytes(after.data) != data:
                    rollback_errors.append(str(key))
        return dict(error=t22.error_name(result.err()) if failed else None, curves=curves, returned=bytes(meta.return_data().data),
                    rollback_errors=rollback_errors, source=amount(source) - r['source_balance'], destination=amount(destination),
                    destination_withheld=t22.withheld_of(raw(destination)),
                    recipient=vm.get_account(recipient).lamports - TOKEN_RENT if r['recipient'] == 0 else amount(recipient),
                    recipient_withheld=t22.withheld_of(raw(recipient)), user_lamports=vm.get_account(user).lamports - USER_LAMPORTS,
                    events=[base64.b64decode(line[14:]) for line in logs if line.startswith('Program data: ')],
                    self_cpi=self_cpi_payloads(inner, list(tx.message.account_keys)))


def trade_bytes(values):
    (base_i, quote_i, creator, mayhem, buy, token_amount, quote_amount, quote_fee, fee_bps, fee,
     creator_bps, creator_fee, buyback_bps, buyback_fee, vtr, vqr, rtr, rqr, cf_unclaimed) = values
    native = quote_i == 0
    return b''.join([
        TRADE_DISC, bytes(MINTS[base_i]),
        struct.pack('<Q', quote_amount if native else 0), struct.pack('<Q', token_amount),
        bytes([buy]), bytes(USER.pubkey()), struct.pack('<q', TS),
        struct.pack('<Q', vqr if native else 0), struct.pack('<Q', vtr),
        struct.pack('<Q', rqr if native else 0), struct.pack('<Q', rtr),
        ZERO_KEY, struct.pack('<Q', fee_bps), struct.pack('<Q', fee),
        bytes(base.CREATOR) if creator else ZERO_KEY,
        struct.pack('<Q', creator_bps), struct.pack('<Q', creator_fee),
        b'\0', struct.pack('<Q', 0), struct.pack('<Q', 0), struct.pack('<Q', 0), struct.pack('<q', 0),
        struct.pack('<I', len(b'multi_hop_swap')), b'multi_hop_swap', bytes([mayhem]),
        struct.pack('<Q', 0), struct.pack('<Q', 0),
        struct.pack('<Q', buyback_bps), struct.pack('<Q', buyback_fee),
        struct.pack('<I', 0),
        ZERO_KEY if native else bytes(MINTS[quote_i]), struct.pack('<Q', quote_amount),
        struct.pack('<Q', vqr), struct.pack('<Q', rqr),
        struct.pack('<Q', 0), struct.pack('<Q', 0), struct.pack('<Q', cf_unclaimed),
        struct.pack('<Q', quote_fee)])


def expected_events(r, line):
    """Assemble the expected payloads from one events-host answer: the log
    events, and the self-CPI payloads (a bare record contributes the event
    tag alone and has no log event)."""
    logged, called = [], []
    for record in line.split(';')[1:]:
        fields = record.split(',')
        kind, values = fields[0], [int(x) for x in fields[1:]]
        if kind == 'B':
            called.append(EVENT_IX_TAG)
            continue
        if kind == 'T':
            payload = trade_bytes(values)
        elif kind == 'C':
            c = r['curves'][values[0]]
            payload = b''.join([COMPLETE_DISC, bytes(USER.pubkey()), bytes(MINTS[c['base']]),
                                 bytes(base.curve_key(c)), struct.pack('<q', TS),
                                 ZERO_KEY if c['quote'] == 0 else bytes(MINTS[c['quote']])])
        elif kind == 'P':
            c = r['curves'][values[0]]
            payload = b''.join([POST_DISC, bytes(USER.pubkey()), bytes(MINTS[c['base']]),
                                 bytes(base.curve_key(c)),
                                 ZERO_KEY if c['quote'] == 0 else bytes(MINTS[c['quote']]), struct.pack('<q', TS),
                                 b''.join(struct.pack('<Q', v) for v in values[1:])])
        else:
            raise ValueError(f'unknown event record {record!r}')
        logged.append(payload)
        called.append(EVENT_IX_TAG + payload)
    return logged, called


def event_problems(r, line, got):
    if not line.startswith('ok'):
        return [f'events host answer {line!r}']
    want, want_cpi = expected_events(r, line)
    bad = []
    if got['events'] != want:
        detail = f"{len(got['events'])} captured vs {len(want)} modelled"
        for i, (a, b) in enumerate(zip(got['events'], want)):
            if a != b:
                detail += f'; first difference at event {i}'
                break
        bad.append(f'log events differ: {detail}')
    if got['self_cpi'] != want_cpi:
        bad.append('self-CPI event payloads differ')
    return bad


def tally(lines):
    counts = {'T': 0, 'C': 0, 'P': 0, 'B': 0}
    for line in lines:
        if line.startswith('ok'):
            for record in line.split(';')[1:]:
                counts[record[0]] += 1
    return counts['T'], counts['C'], counts['P'], counts['B']


class MultiHopEventsCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chain = Chain()

    def run_all(self, labelled):
        routes = [r for _, r in labelled]
        answers = t22.model(routes)
        lines = events_model(routes)
        self.assertEqual(len(answers), len(labelled), 'one model answer is required per captured route')
        self.assertEqual(len(lines), len(labelled), 'one events answer is required per captured route')
        for (label, r), answer, line in zip(labelled, answers, lines):
            with self.subTest(label):
                got = self.chain.run(r)
                problems = t22.check(r, got, answer)
                if answer.startswith('ok'):
                    problems += event_problems(r, line, got)
                elif line != answer:
                    problems.append(f'events host {line!r} != model {answer!r}')
                self.assertEqual(problems, [], (label, answer, line))
        return answers, lines

    def test_fixed_cases(self):
        cases = t22.fixed_cases()
        self.assertEqual(len(cases), t22.FIXED_COUNT)
        _, lines = self.run_all(cases)
        self.assertEqual(tally(lines), FIXED_EVENTS, 'events over the fixed routes')

    def test_random_cases(self):
        cases = t22.random_cases()
        self.assertEqual(len(cases), 400)
        _, lines = self.run_all(cases)
        self.assertEqual(tally(lines), RANDOM_EVENTS, 'events over the random routes')

    def test_events_host_never_drifts(self):
        routes = [r for _, r in t22.fixed_cases()] + [r for _, r in t22.random_cases()]
        for line in events_model(routes):
            self.assertNotEqual(line, 'error:model-drift')

    def test_checker_rejects_tampered_events(self):
        routes = [
            t22.route([t22.curve(t22.A, t22.Q), t22.curve(t22.B, t22.Q)], [0, 1],
                      mints={t22.Q: dict(fee=t22.FEE_250)}, source=t22.A, destination=t22.B, flags=(3, 3), recipient=t22.Q),
            t22.route([t22.curve(t22.A, t22.Q, rtr=10**12)], [0],
                      mints={t22.Q: dict(fee=t22.FEE_250)}, amount=10**9, source=t22.Q, destination=t22.A, flags=(3,), recipient=t22.Q),
        ]
        for r, line in zip(routes, events_model(routes)):
            got = self.chain.run(r)
            self.assertEqual(event_problems(r, line, got), [])
            want, _ = expected_events(r, line)
            bent = bytearray(want[0])
            bent[20] ^= 1
            self.assertNotEqual(event_problems(r, line, dict(got, events=[bytes(bent)] + want[1:])), [])
            self.assertNotEqual(event_problems(r, line, dict(got, events=want[:-1])), [])
            self.assertNotEqual(event_problems(r, line, dict(got, events=want + [want[0]])), [])
            if len(want) > 1:
                self.assertNotEqual(event_problems(r, line, dict(got, events=[want[1], want[0]] + want[2:])), [])
            self.assertNotEqual(event_problems(r, line, dict(got, self_cpi=[])), [])
            self.assertNotEqual(event_problems(r, 'error:6024', got), [])


class SelfCpiTargetTests(unittest.TestCase):
    def test_same_payload_under_another_program_is_not_a_self_cpi(self):
        payload = EVENT_IX_TAG + b'event'
        ix = lambda index: {'instruction': {'programIdIndex': index, 'data': list(payload)}}
        self.assertEqual(self_cpi_payloads([ix(0), ix(1)], [TOKEN, PUMP]), [payload])
        self.assertEqual(self_cpi_payloads([ix(0)], [TOKEN]), [])


if __name__ == '__main__':
    unittest.main()
