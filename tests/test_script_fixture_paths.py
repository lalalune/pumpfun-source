"""Fixture paths named by the differential scripts exist and match the captured programs.

The four files under research/imported-lab/analysis/pump_fun/ are restored byte for
byte from d75184ea3 (the last commit before the fce9f28dd cleanup). This test keeps
them from going missing again and ties them to the pinned ELFs in evidence/original.
It does not run the scripts; it checks their inputs.
"""

import base64
import hashlib
import json
import re
import unittest
from pathlib import Path

try:
    from solders.pubkey import Pubkey
except ImportError:  # the PDA check needs solders; the rest does not
    Pubkey = None

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = 'research/imported-lab/analysis/pump_fun/'
REFERENCE = re.compile(r'research/imported-lab/[A-Za-z0-9_./-]+\.json')
PINNED = {
    'config-snapshot.json': '17b886a6b4aa7fdc89f2fca9a1b67b318d33998794da59fe4df1fe89ca70bd27',
    'amm-v2-trade-fixture.json': '2e775505852caf55203c826ee08b9341aa275f52f59a933c4fb0740535ee316f',
    'curve-fresh-trades-v3-signed-surfpool.json': '54d69dd4f11a61cc6cea3076e3e89fd4aa31ea6ff835f8ea316646a7b1642920',
    'curve-migrate-v2-signed-surfpool.json': 'b4894531409f1cb016c2993a061c99f4316140659f9cffb25cae0875b189dbfc',
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / FIXTURES / name).read_text())


def referenced_paths():
    found = {}
    sources = sorted((ROOT / 'scripts').glob('*.py')) + sorted((ROOT / '.github/workflows').glob('*.yml'))
    for source in sources:
        for match in REFERENCE.findall(source.read_text(errors='replace')):
            found.setdefault(match, []).append(source.relative_to(ROOT).as_posix())
    return found


class ScriptFixturePathTests(unittest.TestCase):
    def test_every_imported_lab_path_named_by_a_script_or_workflow_exists(self):
        found = referenced_paths()
        self.assertGreaterEqual(len(found), 4)
        missing = {path: users for path, users in found.items() if not (ROOT / path).is_file()}
        self.assertEqual(missing, {})

    def test_restored_fixtures_keep_their_pinned_bytes(self):
        for name, digest in PINNED.items():
            with self.subTest(name=name):
                self.assertEqual(sha256(ROOT / FIXTURES / name), digest)

    def test_surfpool_fixtures_name_the_captured_program_hashes(self):
        pump = sha256(ROOT / 'evidence/original/pump/deployed.so')
        fees = sha256(ROOT / 'evidence/original/pump_fees/deployed.so')
        amm = sha256(ROOT / 'evidence/original/pump_amm/deployed.so')
        trades = load('curve-fresh-trades-v3-signed-surfpool.json')
        self.assertEqual((trades['payload_sha256'], trades['fee_program_sha256']), (pump, fees))
        migrate = load('curve-migrate-v2-signed-surfpool.json')
        self.assertEqual((migrate['pump_program_sha256'], migrate['amm_program_sha256']), (pump, amm))

    def test_config_snapshot_accounts_are_owned_config_pdas_with_idl_discriminators(self):
        snapshot = load('config-snapshot.json')
        expected = {'pump': 'Global', 'pump_amm': 'GlobalConfig', 'pump_fees': 'FeeProgramGlobal'}
        self.assertEqual({a['program_name']: a['config_account_type'] for a in snapshot['accounts']}, expected)
        for account in snapshot['accounts']:
            with self.subTest(program=account['program_name']):
                idl = json.loads((ROOT / f"evidence/upstream/{account['program_name']}.json").read_text())
                self.assertEqual(account['owner'], idl['address'])
                self.assertEqual(account['program'], idl['address'])
                kind = next(a for a in idl['accounts'] if a['name'] == account['config_account_type'])
                self.assertEqual(base64.b64decode(account['data_base64'])[:8], bytes(kind['discriminator']))
                if Pubkey is not None:
                    address, bump = Pubkey.find_program_address(
                        [bytes.fromhex(account['pda_seed_hex'])], Pubkey.from_string(idl['address']))
                    self.assertEqual((str(address), bump), (account['address'], account['pda_bump']))


if __name__ == '__main__':
    unittest.main()
