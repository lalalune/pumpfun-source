"""Accepted local V0 transfers must not leak lookup-loaded state between cases."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_amm_reusable_harness as reusable
from pump_amm_admin_differential import PAYER, OUTSIDER, EVENT
from solders.address_lookup_table_account import AddressLookupTableAccount, LookupTableMeta, ADDRESS_LOOKUP_TABLE_ID
from solders.account import Account
from solders.instruction import Instruction, AccountMeta
from solders.message import MessageV0, MessageAddressTableLookup
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import Transaction, VersionedTransaction
from solders.transaction_metadata import FailedTransactionMetadata

BINARY = ROOT / 'evidence/original/pump_amm/deployed.so'


class VersionedResetTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {'PUMP_AMM_FRESH_VM': '0'})
        environment.start()
        self.addCleanup(environment.stop)

    def run_case(self, kind):
        reusable._cached.clear()
        self.addCleanup(reusable._cached.clear)
        harness = reusable.acquire_harness(BINARY)
        vm = harness.vm
        vm.warp_to_slot(1)
        watched = (PAYER.pubkey(), OUTSIDER.pubkey(), EVENT)
        snapshot = lambda: {str(key): json.loads(vm.get_account(key).to_json()) for key in watched}
        before = snapshot()
        ix = transfer(TransferParams(from_pubkey=PAYER.pubkey(), to_pubkey=OUTSIDER.pubkey(), lamports=123))
        if kind == 'readonly':
            ix = Instruction(ix.program_id, ix.data, [ix.accounts[0], AccountMeta(OUTSIDER.pubkey(), False, False)])
        instructions, tables = [ix], []
        if kind not in ('legacy', 'static'):
            targets = [OUTSIDER.pubkey(), EVENT] if kind == 'multiple' else [OUTSIDER.pubkey()]
            for index, recipient in enumerate(targets):
                key = Pubkey(bytes([73 + index]) * 32)
                raw = ((1).to_bytes(4, 'little') + bytes(LookupTableMeta())).ljust(56, b'\0') + bytes(recipient)
                if kind == 'invalid':
                    raw = b'\x01'
                if kind != 'missing':
                    vm.set_account(key, Account(10**9, raw, Pubkey.default() if kind == 'owner' else ADDRESS_LOOKUP_TABLE_ID))
                tables.append(AddressLookupTableAccount(key, [recipient]))
            if kind == 'multiple':
                instructions.append(transfer(TransferParams(from_pubkey=PAYER.pubkey(), to_pubkey=EVENT, lamports=456)))
        if kind == 'legacy':
            tx = Transaction.new_signed_with_payer(instructions, PAYER.pubkey(), [PAYER], vm.latest_blockhash())
        else:
            message = MessageV0.try_compile(PAYER.pubkey(), instructions, tables, vm.latest_blockhash())
            if kind == 'index':
                message = MessageV0(message.header, message.account_keys, message.recent_blockhash,
                                    message.instructions, [MessageAddressTableLookup(tables[0].key, b'\x01', b'')])
            tx = VersionedTransaction(message, [PAYER])
        # solders returns no results for a transaction that carries no
        # signature, and all([]) is true, so the results alone accept an
        # unsigned case as a verified one.
        self.assertTrue(tx.signatures and all(tx.verify_with_results()))
        result = vm.send_transaction(tx)
        error = str(result.err()) if isinstance(result, FailedTransactionMetadata) else None
        if kind in ('legacy', 'static', 'writable', 'multiple'):
            self.assertIsNone(error)
            self.assertEqual(vm.get_account(OUTSIDER.pubkey()).lamports, before[str(OUTSIDER.pubkey())]['lamports'] + 123)
            if kind == 'multiple':
                self.assertEqual(vm.get_account(EVENT).lamports, before[str(EVENT)]['lamports'] + 456)
        self.assertIs(reusable.acquire_harness(BINARY), harness)
        self.assertEqual(snapshot(), before)
        return error

    def test_static_legacy_and_v0_controls(self):
        for kind in ('legacy', 'static'):
            with self.subTest(kind=kind):
                self.run_case(kind)

    def test_writable_lookup_account_is_restored(self):
        self.run_case('writable')

    def test_multiple_lookup_tables_are_restored(self):
        self.run_case('multiple')

    def test_invalid_lookup_inputs_keep_litesvm_errors(self):
        expected = {'missing': 'AddressLookupTableNotFound', 'invalid': 'InvalidAddressLookupTableData',
                    'index': 'InvalidAddressLookupTableIndex', 'owner': 'InvalidAddressLookupTableOwner'}
        for kind, error in expected.items():
            with self.subTest(kind=kind):
                self.assertEqual(self.run_case(kind), 'TransactionErrorFieldless.' + error)

    def test_readonly_lookup_keeps_runtime_rejection(self):
        self.assertEqual(self.run_case('readonly'), 'TransactionErrorInstructionError((0, Fieldless(ReadonlyLamportChange)))')


if __name__ == '__main__':
    unittest.main()
