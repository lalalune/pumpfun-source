"""Real LiteSVM controls for PumpSwap and dependency program cache identity."""
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from solders.pubkey import Pubkey

import pump_amm_reusable_harness as reusable
from pump_amm_admin_differential import PROGRAM


ROOT = Path(__file__).resolve().parents[1]
AMM = ROOT / 'evidence/original/pump_amm/deployed.so'
FEES = ROOT / 'evidence/original/pump_fees/deployed.so'
TOKEN = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN_2022 = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'


class ContentCacheTests(unittest.TestCase):
    def setUp(self):
        reusable._cached.clear()
        self.directory = tempfile.TemporaryDirectory(prefix='amm-program-cache-')
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'program.so'
        self.env = mock.patch.dict(os.environ, {'PUMP_AMM_FRESH_VM': '0'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_primary_program_reuses_unchanged_bytes_and_reloads_changed_bytes(self):
        shutil.copyfile(AMM, self.path)
        first = reusable.acquire_harness(self.path)
        self.assertEqual(bytes(first.vm.get_account(PROGRAM).data), AMM.read_bytes())
        self.assertIs(reusable.acquire_harness(self.path), first)
        shutil.copyfile(FEES, self.path)
        second = reusable.acquire_harness(self.path)
        self.assertIsNot(second, first)
        self.assertEqual(bytes(second.vm.get_account(PROGRAM).data), FEES.read_bytes())
        self.assertIs(reusable.acquire_harness(self.path), second)

    def test_dependency_program_tracks_bytes_per_program_id(self):
        shutil.copyfile(AMM, self.path)
        vm = reusable.acquire_harness(self.path).vm
        key = Pubkey.new_unique()
        dependency = self.path.with_name('dependency.so')
        shutil.copyfile(TOKEN, dependency)
        vm.add_program_from_file(key, dependency)
        self.assertEqual(bytes(vm.get_account(key).data), TOKEN.read_bytes())
        vm.add_program_from_file(key, dependency)
        shutil.copyfile(TOKEN_2022, dependency)
        vm.add_program_from_file(key, dependency)
        self.assertEqual(bytes(vm.get_account(key).data), TOKEN_2022.read_bytes())
        shutil.copyfile(TOKEN, dependency)
        vm.add_program_from_file(key, dependency)
        self.assertEqual(bytes(vm.get_account(key).data), TOKEN.read_bytes())


if __name__ == '__main__':
    unittest.main()
