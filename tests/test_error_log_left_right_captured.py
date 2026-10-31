"""Captured-program checks for the Pump `Left:` / `Right:` error log lines.

Recording VMs run the failing cases of the other captured tests on
`evidence/original/pump/deployed.so`. When a Pump instruction fails, the error
line is sometimes followed at once by `Left:` / key / `Right:` / key while Pump
is the running program. Every such pair is checked against
`programs/pump/recovered/error_log_left_right.rs`: the host must name the two
side forms the model assigns to the site, must rebuild the logged block from
the printed values (rejecting a value that violates a constant side), and the
sides the test can evaluate — a passed slot key, a slot account's owner, a
field stored in the global or sharing-config account — must equal the printed
keys. Error lines with no pair must belong to sites outside the table, and
every table row must be reached. The `trade_v3.rs:172` owner check is reached
through a small fixture of this test, which puts a system-owned and a
Token-2022-owned account in the v3 buyback-recipient slot. This shows matching
behavior on these inputs only; it is not a byte-identity claim.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import collections
import hashlib
import importlib
import io
import json
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import solders.litesvm
from solders.pubkey import Pubkey
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
PUMP_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/error_log_left_right_host.rs'
MODEL_SOURCE = ROOT / 'programs/pump/recovered/error_log_left_right.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = IDL['address']
HANDLERS = {bytes(i['discriminator']): i['name'] for i in IDL['instructions']}
SLOT_NAMES = {i['name']: [a['name'] for a in i['accounts']] for i in IDL['instructions']}

LINE = re.compile(r'^(?:AnchorError thrown in programs/pump/src/(?P<thrown>\S+?)\.'
                  r'|AnchorError caused by account: (?P<account>[\w\[\]]+)\.'
                  r'|ProgramError caused by account: (?P<program>[\w\[\]]+)\.'
                  r'|AnchorError occurred\.) Error Code: \w+\. Error Number: (?P<code>\d+)\. Error Message: ')
DATA_SLOTS = ('global', 'sharing_config', 'bonding_curve')

# Module (test_<name>_captured), case list, indices: the base error-sites
# packet's selection, without the token-incentives handler's module, whose
# logged pairs this packet does not pin.
CASES = {
    'account_lifecycle': {
        'fixed_cases': [12, 14, 16, 20, 22, 24, 33, 35, 39, 40, 41, 43, 77, 81, 83, 86],
    },
    'buy_v2': {
        'fixed_cases': [17, 18, 20, 21, 22, 23, 24, 25, 31, 32, 33, 48, 51, 52, 53, 54, 56, 57, 62, 63, 67, 70, 71],
    },
    'claim_cashback': {
        'fixed_cases': [23, 30, 31, 33, 34, 36, 42, 43, 44],
    },
    'create_v2': {
        'fixed_cases': [3, 4, 16, 17, 18, 19, 20, 22, 24, 25, 26, 27, 28, 29, 30, 54, 57, 60, 61, 69, 80, 85, 100,
            108, 109, 111, 112, 115, 120, 125, 130, 149, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 167,
            172, 175, 179, 195, 196, 197, 200, 204, 206],
    },
    'creator_assignment': {
        'fixed_cases': [21, 23, 24, 25, 29, 33, 34, 70, 71, 74, 75, 77, 101, 105, 107, 108, 109, 111, 113, 115,
            116, 127, 128],
    },
    'creator_fee_collect': {
        'fixed_cases': [7, 39],
    },
    'creator_fee_distribution': {
        'fixed_cases': [10, 11, 12, 14, 15, 17, 20, 21, 22, 26, 65, 69, 72, 74, 76, 77, 81],
    },
    'creator_fee_distribution_quote': {
        'fixed_cases': [9, 10, 11, 12, 16, 17, 21, 22, 23, 25, 30, 33, 34],
    },
    'fee_params': {
        'fixed_cases': [1, 2, 5, 8, 12, 26, 32, 33, 36, 39, 43, 68, 69, 72, 75, 78, 79, 82],
    },
    'global_admin': {
        'admission_cases': [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 13, 16, 17, 34],
        'business_cases': [3, 4, 5, 6, 8, 14, 16, 17, 22, 24, 29, 30, 32, 40, 43, 48, 52],
    },
    'holder_distribution': {
        'fixed_cases': [7, 41, 55, 58, 59, 60, 61],
    },
    'holder_distribution_token': {
        'fixed_cases': [13, 17, 25, 26, 27],
    },
    'idl_authority': {
        'fixed_cases': [25, 46, 49, 50, 51, 52],
    },
    'legacy_buy': {
        'fixed_cases': [26, 28, 30, 31, 32, 33, 34, 36, 42, 54, 61, 62, 63, 64, 66, 67, 68, 80, 84],
    },
    'legacy_cashback': {
        'fixed_cases': [10, 11, 12, 26, 34, 35, 36, 48, 57, 63, 96, 97, 98, 99, 106, 114, 135],
    },
    'legacy_create': {
        'fixed_cases': [2, 3, 4, 5, 6, 17],
    },
    'legacy_sell': {
        'fixed_cases': [5, 31, 40, 42, 43, 44, 46, 50, 52, 53, 63],
    },
    'mayhem_virtual_params': {
        'fixed_cases': [47, 54, 55, 60],
    },
    'migrate': {
        'fixed_cases': [1, 2, 3, 4, 6, 7, 8, 15, 26, 38, 41, 48],
    },
    'migrate_v2': {
        'fixed_cases': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 26, 27, 33, 58, 61, 81],
    },
}
SUITE_MODULES = ('test_global_lifecycle_captured', 'test_sweep_fees_captured', 'test_quote_control_captured',
                 'test_v3_trade_accounting_captured', 'test_v3_vault_refactor_captured',
                 'test_v3_exact_quote_captured')

# Sites that do log a pair but whose operands this packet does not pin (see the
# model file): the create_v2 quote-chain guards, one v3 buy guard whose
# expected side was not identified, and the holder-distribution list guard.
EXCLUDED = {
    ('create_v2', 'thrown', 'create_v2.rs:220', 6063),
    ('create_v2', 'thrown', 'create_v2.rs:243', 6063),
    ('create_v2', 'thrown', 'create_v2.rs:258', 6065),
    ('create_v2', 'thrown', 'create_v2.rs:348', 6075),
    ('create_v2', 'thrown', 'create_v2.rs:353', 6075),
    ('create_v2', 'thrown', 'create_v2.rs:437', 6099),
    ('create_v2', 'thrown', 'create_v2.rs:442', 6099),
    ('buy_v3', 'thrown', 'buy_v2.rs:121', 6010),
    ('distribute_fee_to_holders', 'thrown', 'creator/distribute_fee_to_holders.rs:122', 6085),
}

CONSTANTS = {
    'zero': '11111111111111111111111111111111',
    'wsol': 'So11111111111111111111111111111111111111112',
    'pump': '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P',
    'token': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
    'token2022': 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb',
    'ata_program': 'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL',
    'fees_program': 'pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ',
    'metaplex_program': 'metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s',
    'rent_sysvar': 'SysvarRent111111111111111111111111111111111',
    'mayhem_program': 'MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e',
    'idl_account': 'AYgC53tU5BbP2NAnv5nConJxAdpQZctvmZK88pu69xRs',
}
FORM_NAMES = {'Zero': 'zero', 'Wsol': 'wsol', 'Pump': 'pump', 'Token': 'token', 'Token2022': 'token2022',
              'AtaProgram': 'ata_program', 'FeesProgram': 'fees_program', 'MetaplexProgram': 'metaplex_program',
              'RentSysvar': 'rent_sysvar', 'MayhemProgram': 'mayhem_program', 'IdlAccount': 'idl_account',
              'StoredAuthority': 'stored_authority', 'StoredSharingMint': 'stored_sharing_mint',
              'StoredWithdrawAuthority': 'stored_withdraw_authority',
              'StoredSetCreatorAuthority': 'stored_set_creator_authority',
              'StoredHolderRewardClaimAuthority': 'stored_holder_reward_claim_authority',
              'Derived': 'derived', 'Slot': 'slot:', 'OwnerOf': 'owner:'}
# Stored global-account fields, by byte range in the account data.
STORED_GLOBAL = {'stored_authority': (9, 41), 'stored_withdraw_authority': (113, 145),
                 'stored_set_creator_authority': (386, 418),
                 'stored_holder_reward_claim_authority': (1054, 1086)}

RealVm = solders.litesvm.LiteSVM
RECORDED = []


def pump_top_lines(logs):
    """Log lines printed while Pump itself is the running program."""
    stack, lines = [], []
    for line in logs:
        called = re.match(r'Program (\w+) invoke', line)
        if called:
            stack.append(called.group(1))
        elif re.match(r'Program \w+ (success|failed)', line):
            if stack:
                stack.pop()
        elif line.startswith('Program log: ') and stack and stack[-1] == PUMP:
            lines.append(line[len('Program log: '):])
    return lines


class RecordingVm:
    """LiteSVM with a builder chain; failed single-Pump-instruction
    transactions are recorded with their account slots and pre-state."""

    def __init__(self):
        object.__setattr__(self, 'vm', RealVm())

    def __getattr__(self, name):
        attribute = getattr(self.vm, name)
        if not callable(attribute):
            return attribute

        def call(*args, **kwargs):
            result = attribute(*args, **kwargs)
            if isinstance(result, RealVm):
                object.__setattr__(self, 'vm', result)
                return self
            return result
        return call

    def send_transaction(self, tx):
        keys = [str(key) for key in tx.message.account_keys]
        pump_ix = [ix for ix in tx.message.instructions if keys[ix.program_id_index] == PUMP]
        handler = slots = None
        owners, data = {}, {}
        if len(pump_ix) == 1:
            handler = HANDLERS.get(bytes(pump_ix[0].data)[:8])
            if handler is not None:
                names = SLOT_NAMES[handler]
                slots = {name: keys[index] for name, index in
                         zip(names, (i for i in pump_ix[0].accounts))}
                for key in keys:
                    account = self.vm.get_account(Pubkey.from_string(key))
                    owners[key] = str(account.owner) if account is not None else CONSTANTS['zero']
                for slot in DATA_SLOTS:
                    if slot in slots:
                        account = self.vm.get_account(Pubkey.from_string(slots[slot]))
                        if account is not None and len(account.data) <= 5000:
                            data[slot] = bytes(account.data).hex()
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata) and handler is not None:
            RECORDED.append({'handler': handler, 'slots': slots, 'owners': owners, 'data': data,
                             'lines': pump_top_lines(result.meta().logs())})
        return result


def harvest_cases():
    for name, lists in CASES.items():
        module = importlib.import_module(f'test_{name}_captured')
        with mock.patch.object(module, 'LiteSVM', RecordingVm):
            for list_name, indices in lists.items():
                items = getattr(module, list_name)()
                for index in indices:
                    module.run_captured(items[index])
    print(json.dumps({'records': RECORDED}))


def harvest_suite(name):
    module = importlib.import_module(name)
    module.LiteSVM = RecordingVm
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    outcome = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    print(json.dumps({'ok': outcome.wasSuccessful(), 'ran': outcome.testsRun, 'records': RECORDED}))


def own_fixture_records():
    """The v3 trade fixture of the vault-refactor packet, with the account in
    the buyback-recipient slot replaced by a system-owned, then a
    Token-2022-owned, account at the same address."""
    import test_v3_vault_refactor_captured as vault
    from solders.account import Account
    from solders.instruction import AccountMeta
    elf = vault.PUMP_ELF
    start = len(RECORDED)
    with mock.patch.object(vault, 'LiteSVM', RecordingVm):
        for ix in ('buy_v3', 'buy_exact_quote_in_v3'):
            for owner in (vault.SYSTEM, vault.TOKEN22):
                case = dict(kind='v3', label=f'own-{ix}-{owner}', quote='token', ix=ix,
                            args=(10 ** 9, 10 ** 15) if ix == 'buy_v3' else (10 ** 9, 1), buyback=0,
                            accounts={vault.ata(vault.BUYBACK, vault.QUOTE): Account(2_039_280, b'', owner)})
                vault.run_case(elf, case)
        # sell_v3: the vault packet builds buys only, so mirror its state by
        # hand with a funded user base account.
        for owner in (vault.SYSTEM, vault.TOKEN22):
            vm = vault.new_vm(elf)
            _, quote_mint = vault.common_state(vm, {'quote': 'token', 'buyback': 0})
            user = vault.USER.pubkey()
            volume = bytearray(137)
            volume[:8] = vault.ACCOUNT_DISC['UserVolumeAccumulator']
            volume[8:40] = bytes(user)
            vm.set_account(vault.USER_VOLUME, Account(vm.minimum_balance_for_rent_exemption(137), bytes(volume), vault.PUMP))
            vm.set_account(vault.ata(user, vault.BASE), Account(2_039_280, vault.token(vault.BASE, user, 10 ** 12), vault.TOKEN))
            vm.set_account(vault.ata(user, vault.QUOTE), Account(2_039_280, vault.token(vault.QUOTE, user, 0), vault.TOKEN))
            recipient = vault.ata(vault.BUYBACK, vault.QUOTE)
            vm.set_account(recipient, Account(2_039_280, b'', owner))
            names = {
                'global': vault.GLOBAL, 'base_mint': vault.BASE, 'quote_mint': quote_mint,
                'base_token_program': vault.TOKEN, 'quote_token_program': vault.TOKEN,
                'bonding_curve': vault.CURVE, 'associated_base_bonding_curve': vault.ata(vault.CURVE, vault.BASE),
                'associated_quote_bonding_curve': vault.ata(vault.CURVE, quote_mint), 'user': user,
                'associated_base_user': vault.ata(user, vault.BASE),
                'associated_quote_user': vault.ata(user, quote_mint),
                'user_volume_accumulator': vault.USER_VOLUME, 'fee_config': vault.FEE_CONFIG,
                'buyback_fee_recipient': recipient, 'system_program': vault.SYSTEM,
                'event_authority': vault.EVENT_AUTHORITY, 'program': vault.PUMP,
            }
            ix = vault.IX['sell_v3']
            metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False))
                     for a in ix['accounts']]
            data = bytes(ix['discriminator']) + struct.pack('<QQ', 10 ** 9, 0)
            vault.execute(vm, vault.PUMP, data, metas)
    return RECORDED[start:]


def events(record):
    """(site, left, right) per error line in a record; left/right None when the
    line is not followed by a pair."""
    lines = record['lines']
    found = []
    for index, line in enumerate(lines):
        match = LINE.match(line)
        if not match:
            continue
        for kind in ('thrown', 'account', 'program'):
            if match[kind]:
                site = (record['handler'], kind, match[kind], int(match['code']))
                break
        else:
            site = (record['handler'], 'occurred', '', int(match['code']))
        if index + 4 < len(lines) and lines[index + 1] == 'Left:' and lines[index + 3] == 'Right:':
            found.append((site, lines[index + 2], lines[index + 4]))
        else:
            found.append((site, None, None))
    return found


def evaluate(form, record):
    """The value a side form reads from a record; None for a derived address,
    which this test pins by position only."""
    if form in CONSTANTS:
        return CONSTANTS[form]
    if form.startswith('slot:'):
        return record['slots'][form[5:]]
    if form.startswith('owner:'):
        return record['owners'][record['slots'][form[6:]]]
    if form in STORED_GLOBAL:
        start, end = STORED_GLOBAL[form]
        return str(Pubkey.from_bytes(bytes.fromhex(record['data']['global'])[start:end]))
    if form == 'stored_sharing_mint':
        return str(Pubkey.from_bytes(bytes.fromhex(record['data']['sharing_config'])[11:43]))
    assert form == 'derived', form
    return None


def table():
    rows = {}
    pattern = re.compile(r'^    \("(\w+)", Kind::(\w+), "([^"]*)", (\d+), Side::(\w+)(?:\("([^"]*)"\))?, '
                         r'Side::(\w+)(?:\("([^"]*)"\))?\),$', re.M)
    for handler, kind, place, code, left, left_arg, right, right_arg in pattern.findall(MODEL_SOURCE.read_text()):
        forms = []
        for name, arg in ((left, left_arg), (right, right_arg)):
            forms.append(FORM_NAMES[name] + arg if FORM_NAMES[name].endswith(':') else FORM_NAMES[name])
        rows[(handler, kind.lower(), place, int(code))] = tuple(forms)
    return rows


class ErrorLogLeftRightCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest() == PUMP_SHA256
        cls.tmp = tempfile.TemporaryDirectory()
        cls.host = Path(cls.tmp.name) / 'error-log-left-right-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(cls.host)],
                       check=True)
        cls.rows = table()

        def run(args):
            done = subprocess.run([sys.executable, '-I', '-B', __file__, *args], stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, check=True)
            return json.loads(done.stdout.splitlines()[-1])
        with ThreadPoolExecutor(len(SUITE_MODULES) + 1) as pool:
            futures = [pool.submit(run, ['--harvest-suite', name]) for name in SUITE_MODULES]
            futures.append(pool.submit(run, ['--harvest-cases']))
            reports = [future.result() for future in futures]
        cls.suites = dict(zip(SUITE_MODULES, reports))
        cls.records = [record for report in reports for record in report['records']]
        cls.records += own_fixture_records()
        cls.events = [event for record in cls.records for event in events(record)]
        cls.record_of = [record for record in cls.records for _ in events(record)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def answers(self, queries):
        text = ''.join('\t'.join(map(str, query)) + '\n' for query in queries)
        result = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True)
        return result.stdout.splitlines()

    def test_source_suites_still_pass(self):
        for name, report in self.suites.items():
            self.assertTrue(report['ok'], name)
        self.assertGreater(len(self.records), 400)

    def test_every_paired_block_matches_the_model(self):
        paired = [(site, left, right, record) for (site, left, right), record
                  in zip(self.events, self.record_of) if left is not None]
        self.assertGreater(len(paired), 100)
        form_queries = [('forms', *site) for site, *_ in paired]
        form_answers = self.answers(form_queries)
        block_queries = [('block', *site, left, right) for site, left, right, _ in paired]
        block_answers = self.answers(block_queries)
        self.assertEqual(len(form_answers), len(paired), 'one form answer is required per paired block')
        self.assertEqual(len(block_answers), len(paired), 'one block answer is required per paired block')
        wrong = []
        for (site, left, right, record), forms_answer, block_answer in zip(paired, form_answers, block_answers):
            if site in EXCLUDED:
                if forms_answer != 'unknown':
                    wrong.append((site, 'excluded site modeled'))
                continue
            if site not in self.rows:
                wrong.append((site, 'paired site missing from the table'))
                continue
            if forms_answer != ','.join(self.rows[site]):
                wrong.append((site, f'forms {forms_answer} != {self.rows[site]}'))
                continue
            for form, printed in zip(self.rows[site], (left, right)):
                expected = evaluate(form, record)
                if expected is not None and expected != printed:
                    wrong.append((site, f'{form} evaluates to {expected}, printed {printed}'))
            if block_answer != f'Left:\t{left}\tRight:\t{right}':
                wrong.append((site, f'block answer {block_answer!r}'))
        self.assertEqual(wrong[:6], [], f'{len(wrong)} of {len(paired)} paired blocks differ')

    def test_truncated_paired_answers_are_rejected(self):
        count = sum(left is not None for _site, left, _right in self.events)
        for forms, blocks in (([], ['unused'] * count), (['unused'] * count, [])):
            with self.subTest(forms=len(forms), blocks=len(blocks)), \
                    mock.patch.object(self, 'answers', side_effect=[forms, blocks]), \
                    self.assertRaisesRegex(AssertionError, 'one .* answer is required'):
                self.test_every_paired_block_matches_the_model()

    def test_unpaired_sites_log_no_pair(self):
        unpaired = {site for site, left, _ in self.events if left is None}
        self.assertEqual(unpaired & set(self.rows), set())
        self.assertEqual(unpaired & EXCLUDED, set())
        self.assertGreater(len(unpaired), 200)

    def test_every_row_and_exclusion_is_reached(self):
        reached = {site for (site, left, _) in self.events if left is not None}
        self.assertEqual(set(self.rows) - reached, set())
        self.assertEqual(EXCLUDED - reached, set())

    def test_host_rejects_wrong_values(self):
        site = ('add_quote_control_mint', 'thrown', 'quote_control/state.rs:67', 6069)
        left, right = CONSTANTS['wsol'], CONSTANTS['wsol']
        queries = [('block', *site, left, right),
                   ('block', *site, CONSTANTS['zero'], right),
                   ('forms', 'buy_v3', 'thrown', 'buy_v2.rs:121', 6010),
                   ('forms', 'no_such_handler', 'account', 'global', 6000)]
        self.assertEqual(self.answers(queries),
                         [f'Left:\t{left}\tRight:\t{right}', 'unknown', 'unknown', 'unknown'])


if __name__ == '__main__':
    if sys.argv[1:2] == ['--harvest-cases']:
        harvest_cases()
    elif sys.argv[1:2] == ['--harvest-suite']:
        harvest_suite(sys.argv[2])
    else:
        unittest.main()
