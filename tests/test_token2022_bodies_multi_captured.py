"""Captured-program checks for Token-2022 bodies combined in one trade.

`tests/test_token2022_admission_captured.py` runs one account fault, one
Token-2022 account body, or both, and its model marks the rest
unconfirmed: two bad bodies in one trade, three or more faults, and other
extensions. Every case here runs a legacy, v2 or v3 trade from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured Pump
Fees, SPL Token, Token-2022 and Associated Token programs, on the same
fixtures as that packet:

- two bodies in two slots of one trade, on the routes that packet pairs
  bodies with faults on;
- the extension types that packet does not name — a transfer-fee config,
  a mint close authority, a confidential-transfer mint, a default account
  state (set, and set to a value that is not a state), an interest-bearing
  config, a permanent delegate, a transfer hook with no program, a group
  pointer, a withheld transfer-fee amount, a confidential-transfer
  account, a transfer-hook account with its in-hook flag set — alone on
  every route, and next to one standard body;
- two bodies and one account fault, and one body and two account faults,
  with the twin inputs `programs/pump/recovered/token2022_bodies_multi_host.rs`
  names: each body's own ending, the probes that place a load body, the
  fault's or fault pair's own ending, and the pair's captured ending.

This shows matching behavior on these inputs only; it is not a
byte-identity claim.
"""
from pathlib import Path
import itertools
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_token2022_admission_captured as adm  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOST_SOURCE = ROOT / 'programs/pump/recovered/token2022_bodies_multi_host.rs'
PAIR_ROUTES = adm.PAIR_ROUTES
NEW_PAIR_ROUTES = {
    'legacy': (('sell', 'sol'),),
    'v2': (('sell_v2', 't22'),),
    'v3': (('sell_v3', 'sol'), ('buy_v3', 't22')),
}
LOAD_LABELS = {
    'mint': ('len83', 'len165', 'len355', 'len166', 'type0', 'type2', 'uninit'),
    'token': ('len164', 'len200', 'len355', 'len166', 'type0', 'type1', 'uninit'),
}
PAIR_LABELS = {'mint': adm.PAIR_MINT_BODIES, 'token': adm.PAIR_TOKEN_BODIES}
NONLOAD_LABELS = {'mint': ('overrun', 'pause_on', 'hook'), 'token': ('frozen', 'cpi_guard', 'memo')}


def copt(tag, key=b''):
    return bytes([tag]) + bytes(key).ljust(32, b'\0')


def fee_config_body():
    older = struct.pack('<Q', 0) + struct.pack('<Q', 0) + struct.pack('<H', 0)
    newer = struct.pack('<Q', 0) + struct.pack('<Q', 10**12) + struct.pack('<H', 100)
    return copt(1, b'\x07' * 32) + copt(0) + struct.pack('<Q', 0) + older + newer


def confidential_account_body():
    data = bytearray(294)
    data[0] = 1  # approved
    return bytes(data)


NEW_MINT_BODIES = {
    'fee0': ('fee_config', lambda d: adm.mint_with(d, 1, adm.tlv(0, fee_config_body()))),
    'close3': ('close_authority', lambda d: adm.mint_with(d, 1, adm.tlv(3, copt(1, b'\x08' * 32)))),
    'confid4': ('confidential_mint', lambda d: adm.mint_with(d, 1, adm.tlv(4, copt(1, b'\x09' * 32) + b'\1' + bytes(32)))),
    'dstate2': ('default_state', lambda d: adm.mint_with(d, 1, adm.tlv(6, b'\2'))),
    'dstate9': ('default_state', lambda d: adm.mint_with(d, 1, adm.tlv(6, b'\x09'))),
    'interest10': ('interest_bearing', lambda d: adm.mint_with(d, 1, adm.tlv(10, copt(1, b'\x0a' * 32) + struct.pack('<qhh', 0, 100, 100)))),
    'delegate12': ('permanent_delegate', lambda d: adm.mint_with(d, 1, adm.tlv(12, b'\x0b' * 32))),
    'hook_none': ('hook_none', lambda d: adm.mint_with(d, 1, adm.tlv(14, copt(1, b'\x0c' * 32) + copt(0)))),
    'group20': ('group_pointer', lambda d: adm.mint_with(d, 1, adm.tlv(20, copt(1, b'\x0d' * 32) + copt(0)))),
}
NEW_TOKEN_BODIES = {
    'feeamt1': ('fee_amount', lambda d: adm.token_with(d, 2, adm.tlv(1, struct.pack('<Q', 12345)))),
    'confid5': ('confidential_account', lambda d: adm.token_with(d, 2, adm.tlv(5, confidential_account_body()))),
    'hook_on': ('hook_account_on', lambda d: adm.token_with(d, 2, adm.tlv(7) + adm.tlv(15, b'\1'))),
}
ALL_BODIES = {'mint': {**adm.MINT_BODIES, **NEW_MINT_BODIES}, 'token': {**adm.TOKEN_BODIES, **NEW_TOKEN_BODIES}}
NEW_BODIES = {'mint': NEW_MINT_BODIES, 'token': NEW_TOKEN_BODIES}

TRIO_FAULTS = {
    'legacy': {('sell', 'sol'): ('h.limit', 'fee_recipient.zero', 'buyback.unlisted', 'curve_v2.key'),
               ('buy', 'sol'): ('h.limit', 'fee_recipient.zero', 'curve_v2.key'),
               ('buy_exact_sol_in', 'sol'): ('h.limit', 'fee_recipient.zero', 'curve_v2.key')},
    'v2': {(ix, quote): ('h.limit', 'fee_config.bump')
           for ix in ('sell_v2', 'buy_v2', 'buy_exact_quote_in_v2') for quote in ('sol', 't22')},
    # `h.overflow` stops nothing on sell_v3 with a Token-2022 quote (its
    # twin run passes), so that route leaves it out.
    'v3': {('sell_v3', 't22'): ('h.limit', 'fee_config.len2511'),
           ('sell_v3', 'sol'): ('h.limit', 'fee_config.len2511', 'h.overflow'),
           ('buy_v3', 't22'): ('h.limit', 'fee_config.len2511', 'h.overflow'),
           ('buy_exact_quote_in_v3', 'sol'): ('h.limit', 'fee_config.len2511', 'h.overflow')},
}
DUO_ROUTES = {
    'legacy': (('sell', 'sol', ('h.limit', 'fee_recipient.zero', 'buyback.unlisted',
                                'associated_bonding_curve.mint', 'associated_user.auth')),),
    'v2': (('sell_v2', 't22', ('h.limit', 'fee_config.bump', 'associated_base_bonding_curve.mint',
                               'associated_quote_bonding_curve.key')),
           ('buy_v2', 'sol', ('h.limit', 'fee_config.bump', 'associated_base_bonding_curve.mint'))),
    'v3': (('sell_v3', 't22', ('h.limit', 'fee_config.len2511',
                               'associated_base_bonding_curve.mint', 'associated_quote_bonding_curve.key')),
           ('buy_v3', 't22', ('h.limit', 'fee_config.len2511', 'h.overflow',
                              'associated_base_bonding_curve.mint', 'associated_quote_bonding_curve.key'))),
}


def table_of(bodies):
    return 'mint' if bodies is adm.MINT_BODIES else 'token'


# The quote move pays each destination in its own transfer. The order the
# sub-transfers run in, per route, recovered from body pairs: on v2 the
# creator vault is paid first, then the main destination, then the other
# payees (buyback before fee on a sell, fee before buyback on a buy); on
# v3 the main destination is paid first, then the recipient.
DESTINATION_ORDER = {
    ('v2', 'sell_v2', 't22'): {'associated_creator_vault': 0, 'associated_quote_user': 1,
                               'associated_quote_buyback_fee_recipient': 2, 'associated_quote_fee_recipient': 3},
    ('v2', 'buy_v2', 't22'): {'associated_creator_vault': 0, 'associated_quote_bonding_curve': 1,
                              'associated_quote_fee_recipient': 2, 'associated_quote_buyback_fee_recipient': 3},
    ('v2', 'buy_exact_quote_in_v2', 't22'): {'associated_creator_vault': 0, 'associated_quote_bonding_curve': 1,
                                             'associated_quote_fee_recipient': 2, 'associated_quote_buyback_fee_recipient': 3},
    ('v3', 'sell_v3', 't22'): {'associated_quote_user': 0, 'buyback_fee_recipient': 1},
    ('v3', 'buy_v3', 't22'): {'associated_quote_bonding_curve': 0, 'buyback_fee_recipient': 1},
}


def rank_of(family, ix, quote, slot):
    """The sub-transfer a stop on this slot lands in; 0 unless the slot is
    a quote destination on a route with a known order."""
    return DESTINATION_ORDER.get((family, ix, quote), {}).get(slot, 0)


def slots_of(family, quote):
    return [(slot, table_of(bodies)) for slot, bodies in adm.slots_of(family, quote)]


def role_of(slot):
    return adm.MINT_SLOTS.get(slot) or adm.TOKEN_ROLE[slot]


def side_of(ix):
    return 'sell' if ix.startswith('sell') else 'buy'


def build_two_faults(family, ix, quote, name_f, name_g):
    fixture, _, _, _, faults = adm.FAMILIES[family]
    over_f, edit_f = faults[name_f]
    over_g, edit_g = faults[name_g]
    fx = fixture(ix, quote, **{**over_f, **over_g})
    fx.to_token2022()
    edit_f(fx)
    edit_g(fx)
    return fx


class Token2022BodiesMultiCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import hashlib
        for path, digest in adm.ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        cls.host = Path(cls.tmp.name) / 'token2022-bodies-multi-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(cls.host)], check=True)
        cls.programs = {family: adm.Program(family) for family in adm.FAMILIES}
        cls.alone_cache, cls.probe_cache, cls.pair_cache = {}, {}, {}
        cls.plain_cache, cls.fg_cache, cls.fg_probe_cache = {}, {}, {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # Captured runs, cached.

    def apply_body(self, fx, slot, table, label):
        held = fx.held(slot)
        if held is None:
            return False
        fx.put(slot, data=ALL_BODIES[table][label][1](bytes(held.data)))
        return True

    def alone(self, family, ix, quote, slot, table, label):
        key = (family, ix, quote, slot, table, label)
        if key not in self.alone_cache:
            fx = adm.build(family, ix, quote)
            self.alone_cache[key] = self.programs[family].run(fx) if self.apply_body(fx, slot, table, label) else None
        return self.alone_cache[key]

    def probe(self, family, ix, quote, body_slot, body_table, body_label, owner_slot):
        """The body alone, with a wrong owner on the other slot."""
        key = (family, ix, quote, body_slot, body_table, body_label, owner_slot)
        if key not in self.probe_cache:
            fx = adm.build(family, ix, quote)
            if not self.apply_body(fx, body_slot, body_table, body_label) or fx.held(owner_slot) is None:
                self.probe_cache[key] = None
            else:
                fx.put(owner_slot, owner=adm.ALIEN)
                self.probe_cache[key] = self.programs[family].run(fx)
        return self.probe_cache[key]

    def pair_run(self, family, ix, quote, slot_a, table_a, label_a, slot_b, table_b, label_b):
        ends = sorted(((slot_a, table_a, label_a), (slot_b, table_b, label_b)))
        key = (family, ix, quote, *ends[0], *ends[1])
        if key not in self.pair_cache:
            fx = adm.build(family, ix, quote)
            ok = all(self.apply_body(fx, slot, table, label) for slot, table, label in ends)
            self.pair_cache[key] = self.programs[family].run(fx) if ok else None
        return self.pair_cache[key]

    def plain(self, family, ix, quote, name):
        key = (family, ix, quote, name)
        if key not in self.plain_cache:
            self.plain_cache[key] = self.programs[family].run(adm.build(family, ix, quote, name))
        return self.plain_cache[key]

    def fault_pair(self, family, ix, quote, name_f, name_g, owner_slot=None):
        cache = self.fg_probe_cache if owner_slot else self.fg_cache
        key = (family, ix, quote, name_f, name_g, owner_slot)
        if key not in cache:
            fx = build_two_faults(family, ix, quote, name_f, name_g)
            if owner_slot is not None:
                if fx.held(owner_slot) is None:
                    cache[key] = None
                    return None
                fx.put(owner_slot, owner=adm.ALIEN)
            cache[key] = self.programs[family].run(fx)
        return cache[key]

    # Host lines.

    def answers(self, lines):
        text = ''.join(line + '\n' for line in lines)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(len(out), len(lines))
        return out

    def compare(self, cases):
        """`cases` holds (line, captured); the host must name every captured ending."""
        kept = [(line, str(got)) for line, got in cases if got is not None]
        answers = self.answers([line for line, _ in kept])
        wrong = [(line, answer, got) for (line, got), answer in zip(kept, answers) if answer != got]
        self.assertEqual(wrong[:15], [], f'{len(wrong)} of {len(kept)} differ')
        return kept, answers

    def pair_case(self, family, ix, quote, slot_a, table_a, label_a, slot_b, table_b, label_b):
        a_alone = self.alone(family, ix, quote, slot_a, table_a, label_a)
        b_alone = self.alone(family, ix, quote, slot_b, table_b, label_b)
        captured = self.pair_run(family, ix, quote, slot_a, table_a, label_a, slot_b, table_b, label_b)
        if a_alone is None or b_alone is None or captured is None:
            return None, None
        probe_a = probe_b = '-'
        if label_a in LOAD_LABELS[table_a] or label_b in LOAD_LABELS[table_b]:
            probe_a = self.probe(family, ix, quote, slot_b, table_b, label_b, slot_a)
            probe_b = self.probe(family, ix, quote, slot_a, table_a, label_a, slot_b)
            if probe_a is None or probe_b is None:
                return None, None
        line = ' '.join(str(x) for x in ('pair', family, side_of(ix), role_of(slot_a), ALL_BODIES[table_a][label_a][0],
                                         rank_of(family, ix, quote, slot_a),
                                         role_of(slot_b), ALL_BODIES[table_b][label_b][0],
                                         rank_of(family, ix, quote, slot_b), a_alone, b_alone, probe_a, probe_b))
        return line, captured

    # Tests.

    def test_new_extensions_alone_change_no_ending(self):
        count = 0
        for family, (_, _, ixs, quotes, _) in adm.FAMILIES.items():
            for ix in ixs:
                for quote in quotes:
                    for slot, table in slots_of(family, quote):
                        for label in NEW_BODIES[table]:
                            got = self.alone(family, ix, quote, slot, table, label)
                            self.assertEqual(got, 'ok', (family, ix, quote, slot, label))
                            count += 1
        self.assertEqual(count, 351)

    def standard_pair_cases(self):
        cases = []
        for family, routes in PAIR_ROUTES.items():
            for ix, quote in routes:
                slots = slots_of(family, quote)
                for (slot_a, table_a), (slot_b, table_b) in itertools.combinations(slots, 2):
                    for label_a in PAIR_LABELS[table_a]:
                        for label_b in PAIR_LABELS[table_b]:
                            cases.append(self.pair_case(family, ix, quote, slot_a, table_a, label_a, slot_b, table_b, label_b))
        return [case for case in cases if case[0] is not None]

    def test_two_bodies_match_captured_program(self):
        kept, answers = self.compare(self.standard_pair_cases())
        self.assertEqual(len(kept), 4752)
        self.assertTrue({'17', '36', '42', '67', '6063', 'InvalidAccountData', 'UninitializedAccount'} <= set(answers))

    def new_pair_cases(self):
        cases = []
        for family, routes in NEW_PAIR_ROUTES.items():
            for ix, quote in routes:
                slots = slots_of(family, quote)
                for (slot_a, table_a), (slot_b, table_b) in itertools.combinations(slots, 2):
                    for new_slot, new_table, std_slot, std_table in ((slot_a, table_a, slot_b, table_b), (slot_b, table_b, slot_a, table_a)):
                        for new_label in NEW_BODIES[new_table]:
                            for std_label in PAIR_LABELS[std_table]:
                                cases.append(self.pair_case(family, ix, quote, new_slot, new_table, new_label,
                                                            std_slot, std_table, std_label))
        return [case for case in cases if case[0] is not None]

    def test_two_bodies_next_to_a_new_extension_match_captured_program(self):
        kept, _ = self.compare(self.new_pair_cases())
        self.assertEqual(len(kept), 3420)

    def trio_cases(self):
        cases = []
        for family, routes in PAIR_ROUTES.items():
            for ix, quote in routes:
                slots = slots_of(family, quote)
                for name in TRIO_FAULTS[family][(ix, quote)]:
                    f_plain = self.plain(family, ix, quote, name)
                    for (slot_a, table_a), (slot_b, table_b) in itertools.combinations(slots, 2):
                        for label_a in NONLOAD_LABELS[table_a]:
                            for label_b in NONLOAD_LABELS[table_b]:
                                pair = self.pair_run(family, ix, quote, slot_a, table_a, label_a, slot_b, table_b, label_b)
                                fx = adm.build(family, ix, quote, name)
                                if not (self.apply_body(fx, slot_a, table_a, label_a) and self.apply_body(fx, slot_b, table_b, label_b)):
                                    continue
                                captured = self.programs[family].run(fx)
                                line = ' '.join(str(x) for x in ('trio', family, side_of(ix), role_of(slot_a),
                                                                 ALL_BODIES[table_a][label_a][0],
                                                                 rank_of(family, ix, quote, slot_a), role_of(slot_b),
                                                                 ALL_BODIES[table_b][label_b][0],
                                                                 rank_of(family, ix, quote, slot_b),
                                                                 adm.model_fault(name), f_plain, pair))
                                cases.append((line, captured))
        return cases

    def test_two_bodies_and_a_fault_match_captured_program(self):
        kept, _ = self.compare(self.trio_cases())
        self.assertEqual(len(kept), 2727)

    def duo_cases(self):
        cases = []
        for family, routes in DUO_ROUTES.items():
            for ix, quote, fault_names in routes:
                slots = slots_of(family, quote)
                for name_f, name_g in itertools.combinations(fault_names, 2):
                    pair_plain = self.fault_pair(family, ix, quote, name_f, name_g)
                    touched = {name_f.split('.')[0], name_g.split('.')[0]}
                    for slot, table in slots:
                        if slot in touched:
                            continue
                        pair_probe = self.fault_pair(family, ix, quote, name_f, name_g, owner_slot=slot)
                        if pair_probe is None:
                            continue
                        for label in PAIR_LABELS[table]:
                            fx = build_two_faults(family, ix, quote, name_f, name_g)
                            if not self.apply_body(fx, slot, table, label):
                                continue
                            captured = self.programs[family].run(fx)
                            line = ' '.join(str(x) for x in ('duo', family, side_of(ix), role_of(slot),
                                                             ALL_BODIES[table][label][0],
                                                             rank_of(family, ix, quote, slot),
                                                             adm.model_fault(name_f),
                                                             adm.model_fault(name_g), pair_plain, pair_probe))
                            cases.append((line, captured))
        return cases

    def test_a_body_and_two_faults_match_captured_program(self):
        kept, _ = self.compare(self.duo_cases())
        self.assertEqual(len(kept), 1050)

    def test_checker_rejects_a_different_outcome(self):
        # Negative controls: the same inputs with another body give another answer.
        self.assertEqual(self.answers([
            'pair legacy sell user_base frozen 0 curve_base extended 0 17 ok - -',
            'pair legacy sell user_base extended 0 curve_base frozen 0 ok 17 - -',
            'pair legacy sell base_mint paused 0 user_base frozen 0 67 17 - -',
        ]), ['17', '17', '17'])
        self.assertEqual(self.answers([
            'pair legacy sell user_base uninitialized 0 curve_base bad_length 0 UninitializedAccount InvalidAccountData 6057 UninitializedAccount',
            'pair legacy sell user_base uninitialized 0 curve_base bad_length 0 UninitializedAccount InvalidAccountData InvalidAccountData 6057',
        ]), ['UninitializedAccount', 'InvalidAccountData'])
        self.assertEqual(self.answers([
            'duo legacy sell user_base extended 0 fee_recipient.zero buyback.unlisted 6057 6057',
            'duo legacy sell user_base frozen 0 fee_recipient.zero buyback.unlisted 6057 6057',
            'trio legacy sell user_base frozen 0 curve_base extended 0 fee_recipient.zero 6057 17',
            'trio legacy sell user_base frozen 0 curve_base extended 0 h.limit 6005 17',
        ]), ['6057', '17', '17', '6005'])
        # A later sub-transfer's frozen loses to the first sub-transfer's
        # hook, and wins once it sits in the first sub-transfer itself.
        self.assertEqual(self.answers([
            'pair v2 sell quote_mint hook_set 0 user_quote frozen 1 InvalidAccountData 17 - -',
            'pair v3 sell quote_mint hook_set 0 user_quote frozen 0 InvalidAccountData 17 - -',
        ]), ['InvalidAccountData', '17'])


if __name__ == '__main__':
    unittest.main()
