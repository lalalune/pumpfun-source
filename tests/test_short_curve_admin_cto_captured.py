"""Captured-program checks for `admin_cto` on short `BondingCurve` accounts.

The short-curve packets cover the trades and the non-trade callers, and both
leave `admin_cto` out. Every case here runs `admin_cto` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, through the fixtures of the
existing `admin_cto` captured test, on a short synthetic curve. The bytes
also go to `programs/pump/recovered/short_curve_admin_cto_host.rs`, which
predicts the 166-byte account the short one is read as and the rent top-up.
The captured program then runs the predicted account too, already funded
with the top-up, and both runs must leave the same error, stored curve and
event, apart from the top-up itself. The handler's other behaviour stays
with the `admin_cto` model: this file pins how the account is read, not
what the takeover does. This shows matching behavior on these inputs only;
it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_admin_cto_captured as base  # noqa: E402

PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
HOST_SOURCE = ROOT / 'programs/pump/recovered/short_curve_admin_cto_host.rs'

LENGTHS = (0, 7, 8, 48, 49, 60, 80, 81, 82, 83, 100, 114, 115, 123, 124, 125, 140, 141, 165, 166, 167, 200)
BOOL_OFFSETS = (48, 81, 82, 123, 124)
U64 = 2**64 - 1
# Tail fields a shape may or may not read. Each stays valid if it is read.
PROFILES = {
    'mayhem': ((81, b'\1'),),
    'cashback': ((82, b'\1'),),
    'creator_bps': ((115, struct.pack('<Q', 500)), (123, b'\1')),
    'holder': ((124, b'\1'),),
    'accrued': ((125, struct.pack('<QQ', 3_000_000, 7_000_000)),),
}
# The last length that ignores a profile's fields and the first that reads them.
PROFILE_LENGTHS = {'mayhem': (81, 82), 'cashback': (82, 83), 'creator_bps': (123, 124),
                   'holder': (124, 125), 'accrued': (140, 141)}


def rent(length):
    return (length + 128) * 6960


def case(**changes):
    return base.default_case(**changes)


CONFIGS = {
    'native': case(creator=base.SYSTEM),
    'wallet': case(creator=base.OTHER.pubkey(), current_writable=True),
    'fee': case(creator=base.SHARING, quote=base.CUSTOM, quote_field=base.CUSTOM, fee=1),
    'fee_over': case(creator=base.SHARING, quote=base.CUSTOM, quote_field=base.CUSTOM, fee=301),
}


def full_curve(cfg):
    return base.curve_bytes({**CONFIGS[cfg], 'curve_len': 200})


def curve_of(cfg, length, fields=()):
    """The config's curve, with tail bytes set before it is cut to `length`."""
    data = bytearray(full_curve(cfg).ljust(max(length, 166), b'\0'))
    for offset, value in fields:
        data[offset:offset + len(value)] = value
    return bytes(data[:length])


def run(cfg, curve, lamports):
    item = {**CONFIGS[cfg], 'curve_lamports': lamports}
    with mock.patch.object(base, 'curve_bytes', lambda _case: curve):
        _line, captured, _logs = base.assemble(item)
    return captured


def split_ok(captured):
    kind, curve, event, rent_paid = captured.split(',')
    return bytes.fromhex(curve), bytes.fromhex(event), int(rent_paid)


class ShortCurveAdminCtoCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest() == base.ELF_SHA256[PUMP_ELF]
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'short-curve-admin-cto-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(f'{curve.hex()},{lamports}\n' for curve, lamports in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def check(self, cfg, curve, lamports):
        answer = self.host_answers([(curve, lamports)])[0]
        short = run(cfg, curve, lamports)
        if not answer.startswith('ok'):
            expected = {'invalid': 'error:InvalidAccountData', 'bool': 'error:BorshIoError'}.get(answer, answer)
            self.assertEqual(short, expected)
            return 'error'
        _, top_up, image = answer.split(',')
        top_up, image = int(top_up), bytes.fromhex(image)
        full = run(cfg, image, lamports + top_up)
        if short.startswith('error:'):
            self.assertEqual(full, short)
            return 'error'
        short_curve, short_event, short_rent = split_ok(short)
        full_curve, full_event, full_rent = split_ok(full)
        self.assertEqual(short_curve, full_curve)
        self.assertEqual(short_event, full_event)
        self.assertEqual(short_rent, top_up + full_rent)
        if len(curve) < 166:
            self.assertEqual(len(short_curve), 166)
        return 'ok'

    def run_batch(self, batch):
        outcomes = {'ok': 0, 'error': 0}
        for cfg, curve, lamports in batch:
            with self.subTest(cfg=cfg, length=len(curve), lamports=lamports):
                outcomes[self.check(cfg, curve, lamports)] += 1
        return outcomes

    def test_native_lengths_match_captured_program(self):
        batch = []
        for length in LENGTHS:
            batch.append(('native', curve_of('native', length), rent(length)))
            batch.append(('native', curve_of('native', length), rent(166) + 10_000_000))
        outcomes = self.run_batch(batch)
        self.assertGreater(outcomes['ok'], 20)

    def test_other_configs_match_captured_program(self):
        batch = []
        for cfg in ('wallet', 'fee', 'fee_over'):
            for length in LENGTHS:
                batch.append((cfg, curve_of(cfg, length), rent(166) + 10_000_000))
        self.run_batch(batch)

    def test_profiles_at_their_boundaries(self):
        batch = []
        for name, fields in PROFILES.items():
            for length in PROFILE_LENGTHS[name]:
                batch.append(('native', curve_of('native', length, fields), rent(166) + 10_000_000))
        self.run_batch(batch)

    def test_bad_bool_inside_the_read_prefix(self):
        batch = []
        for offset, length in zip(BOOL_OFFSETS * 2, (49, 82, 83, 124, 125, 60, 100, 100, 125, 140)):
            batch.append(('native', curve_of('native', length, ((offset, b'\2'),)), rent(166) + 10_000_000))
        outcomes = self.run_batch(batch)
        self.assertEqual(outcomes['error'], len(batch))

    def test_wrong_discriminator_is_refused(self):
        batch = []
        for length in (49, 124, 166):
            curve = b'\1' * 8 + curve_of('native', length)[8:]
            batch.append(('native', curve, rent(166) + 10_000_000))
        outcomes = self.run_batch(batch)
        self.assertEqual(outcomes['error'], len(batch))

    def test_reserved_fee_overflow_is_refused(self):
        batch = []
        for length in (141, 165, 166, 200):
            curve = curve_of('native', length, ((125, struct.pack('<Q', U64)), (133, struct.pack('<Q', 1))))
            batch.append(('native', curve, 10**9))
        for curve, lamports in [(c, l) for _cfg, c, l in batch]:
            answer = self.host_answers([(curve, lamports)])[0]
            self.assertEqual(answer, 'error:6024')
            self.assertEqual(run('native', curve, lamports), 'error:6024')


if __name__ == '__main__':
    unittest.main()
