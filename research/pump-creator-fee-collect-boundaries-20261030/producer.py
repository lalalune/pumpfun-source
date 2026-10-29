#!/usr/bin/env python3
"""Pump Main creator-fee collection: payout-destination boundaries and in-transaction sequences,
original vs rebuild.

`collect_creator_fee` (v1) and `collect_creator_fee_v2` move the creator vault PDA's lamports
above rent_minimum(0) to `creator` with a System transfer signed by the vault seeds. Before the
transfer the handler checks, in this order:

  creator.owner == pump_fees           -> error 6050 UnableToDistributeCreatorVaultMigratedToSharingConfig
  creator.executable                   -> Ok, log "Creator account is executable ..."
  amount = vault - rent_min(0) == 0    -> Ok, log "No creator fee to collect"
  creator + amount < rent(creator.len) -> Ok, log "Creator account does not have enough rent-exemption lamports"
  System transfer, CollectCreatorFeeEvent (log + self-CPI)

The repository harnesses (scripts/pump_creator_collect_differential.py and
..._v2_differential.py) vary the vault balance and the account metas with a funded, data-less,
system-owned creator. This packet varies the destination instead (absent, short of rent, with
data, foreign owners, pump_fees owner, executable, near u64::MAX lamports), runs the
v2 SPL-quote path on small/large token amounts, and chains collections with deposits, rent
top-ups and failures inside one transaction.

Only the Pump image is loaded (upgradeable loader layout: program account + programdata). The
System, SPL Token and ATA programs are LiteSVM built-ins. pump_fees is never invoked; its id is
only used as an account owner. All state is synthetic, keys come from fixed seeds, the clock is
fixed per case, and there is no network. The full initial account set and instruction list of
every case is written to runtime/plan.json.gz, so verify.py replays without the repository.

Usage:
  python3 producer.py --root <repo> --images '{"original": "...", "candidate": "..."}' --out <packet dir>
"""
import argparse
import base64
import gzip
import hashlib
import json
import struct
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
PAYER_SEED = bytes([231]) * 32
PAYER = Keypair.from_seed(PAYER_SEED).pubkey()
CREATOR_A = Pubkey(bytes([60]) * 32)
CREATOR_B = Pubkey(bytes([61]) * 32)
QUOTE_SPL = Keypair.from_seed(bytes([64]) * 32).pubkey()
BASE_TS = 1_800_000_000
U64 = 2**64 - 1
R0 = 890_880  # rent_minimum(0) under LiteSVM's default Rent

IX = {'collect_creator_fee': bytes([20, 22, 86, 123, 198, 28, 219, 132]),
      'collect_creator_fee_v2': bytes([207, 17, 138, 242, 4, 34, 19, 56])}
IX_ACCOUNTS = {'collect_creator_fee': 5, 'collect_creator_fee_v2': 10}

pda = lambda seeds, program=PROGRAM: Pubkey.find_program_address(seeds, program)[0]
EVENT_AUTHORITY = pda([b'__event_authority'])


def rent(n):
    return (128 + n) * 6960


def vault_of(creator):
    return pda([b'creator-vault', bytes(creator)])


def ata(owner, mint, program=TOKEN):
    return pda([bytes(owner), bytes(program), bytes(mint)], ATA_PROGRAM)


def mint_data(decimals):
    d = bytearray(82)
    struct.pack_into('<Q', d, 36, 10**15)
    d[44] = decimals
    d[45] = 1
    return bytes(d)


def token_data(mint, owner, amount, native_reserve=None, state=1):
    d = bytearray(165)
    d[:32] = bytes(mint)
    d[32:64] = bytes(owner)
    struct.pack_into('<Q', d, 64, amount)
    d[108] = state
    if native_reserve is not None:
        struct.pack_into('<IQ', d, 109, 1, native_reserve)
    return bytes(d)


# ---- plan: cases are pure data (accounts + instruction list) ----

def acct(key, lamports, owner=SYSTEM, data=b''):
    return [str(key), lamports, str(owner), data.hex()]


def collect_ix(kind, creator, quote=WSOL):
    vault = vault_of(creator)
    if kind == 'collect_creator_fee':
        keys = [(creator, True), (vault, True), (SYSTEM, False), (EVENT_AUTHORITY, False), (PROGRAM, False)]
    else:
        keys = [(creator, True), (ata(creator, quote), True), (vault, True), (ata(vault, quote), True),
                (quote, False), (TOKEN, False), (ATA_PROGRAM, False), (SYSTEM, False),
                (EVENT_AUTHORITY, False), (PROGRAM, False)]
    return {'program': str(PROGRAM), 'data_hex': IX[kind].hex(),
            'metas': [[str(k), k == PAYER, w] for k, w in keys]}


def transfer_ix(src, dst, lamports):
    return {'program': str(SYSTEM), 'data_hex': struct.pack('<IQ', 2, lamports).hex(),
            'metas': [[str(src), True, True], [str(dst), False, True]]}


def base_accounts(quote_spl=False):
    out = [acct(PAYER, 10**12), acct(WSOL, 10**9, TOKEN, mint_data(9))]
    if quote_spl:
        out.append(acct(QUOTE_SPL, 10**9, TOKEN, mint_data(6)))
    return out


def plan():
    cases = []

    def add(name, note, accounts, ixs, ts=None):
        cases.append({'case': name, 'note': note, 'accounts': accounts, 'instructions': ixs,
                      'unix_timestamp': BASE_TS if ts is None else ts})

    kinds = (('v1', 'collect_creator_fee'), ('v2', 'collect_creator_fee_v2'))
    A, VA = CREATOR_A, vault_of(CREATOR_A)
    # (name, note, creator account or None (absent), vault lamports)
    single = [
        ('absent-creator-amount-r0-minus-1', 'creator absent; amount = rent(0) - 1', None, R0 + R0 - 1),
        ('absent-creator-amount-r0', 'creator absent; amount = rent(0)', None, R0 + R0),
        ('absent-creator-amount-1', 'creator absent; amount = 1', None, R0 + 1),
        ('creator-1-lamport-amount-r0-minus-1', 'creator 1 lamport; 1 + amount = rent(0)',
         acct(A, 1), R0 + R0 - 1),
        ('creator-1-lamport-amount-r0-minus-2', 'creator 1 lamport; 1 + amount = rent(0) - 1',
         acct(A, 1), R0 + R0 - 2),
        ('creator-data165-short-by-1', 'system-owned creator with 165 data bytes; lamports + amount = rent(165) - 1',
         acct(A, rent(165) - 1000, SYSTEM, bytes(165)), R0 + 999),
        ('creator-data165-exact', 'system-owned creator with 165 data bytes; lamports + amount = rent(165)',
         acct(A, rent(165) - 1000, SYSTEM, bytes(165)), R0 + 1000),
        ('creator-owner-token-165', 'creator owned by SPL Token (token-account layout), rent-exempt',
         acct(A, rent(165), TOKEN, token_data(WSOL, PAYER, 5)), R0 + 10**6),
        ('creator-owner-pump-8', 'creator owned by the Pump program, 8 data bytes',
         acct(A, rent(8), PROGRAM, bytes(range(8))), R0 + 10**6),
        ('creator-owner-pump-fees-funded-vault', 'creator owned by pump_fees; vault holds 1,000,000 above rent',
         acct(A, rent(0), FEES), R0 + 10**6),
        ('creator-owner-pump-fees-empty-vault', 'creator owned by pump_fees; vault exactly rent(0)',
         acct(A, rent(0), FEES), R0),
        ('creator-owner-pump-fees-absent-vault', 'creator owned by pump_fees; vault absent',
         acct(A, rent(0), FEES), 0),
        ('creator-executable-ata-program', 'creator is the ATA program (executable built-in)',
         'EXEC', R0 + 10**6),
        ('creator-lamports-max-minus-10-amount-10', 'creator lamports = u64::MAX - 10; amount 10',
         acct(A, U64 - 10), R0 + 10),
        ('creator-lamports-max-minus-10-amount-11', 'creator lamports = u64::MAX - 10; amount 11 (overflow)',
         acct(A, U64 - 10), R0 + 11),
        ('vault-2pow62', 'vault holds 2^62 lamports', acct(A, 10**9), 2**62),
        ('vault-owner-pump', 'vault owned by Pump (not System), 1,000,000 above rent', acct(A, 10**9), -1),
        ('vault-with-1-data-byte', 'vault system-owned with 1 data byte, 1,000,000 above rent(0)',
         acct(A, 10**9), -2),
    ]
    for name, note, creator, vault_lamports in single:
        key = ATA_PROGRAM if creator == 'EXEC' else A
        vault = vault_of(key)
        for tag, kind in kinds:
            accounts = base_accounts()
            if creator not in (None, 'EXEC'):
                accounts.append(creator)
            if vault_lamports == -1:
                accounts.append(acct(vault, R0 + 10**6, PROGRAM))
            elif vault_lamports == -2:
                accounts.append(acct(vault, R0 + 10**6, SYSTEM, b'\x00'))
            elif vault_lamports:
                accounts.append(acct(vault, vault_lamports))
            add(f'{tag}-{name}', note, accounts, [collect_ix(kind, key)])

    # creator = the fee payer (signer, writable)
    for tag, kind in kinds:
        accounts = base_accounts() + [acct(vault_of(PAYER), R0 + 123_456)]
        add(f'{tag}-creator-is-fee-payer', 'creator is the transaction fee payer', accounts,
            [collect_ix(kind, PAYER)])
    # negative clock timestamp (event field)
    for tag, kind in kinds:
        add(f'{tag}-negative-unix-timestamp', 'clock unix_timestamp = -1',
            base_accounts() + [acct(A, 10**9), acct(VA, R0 + 777)], [collect_ix(kind, A)], ts=-1)

    # ---- sequences inside one transaction ----
    seq = []
    seq.append(('collect-twice', 'collect, collect', [acct(A, 10**9), acct(VA, R0 + 50_000)],
                lambda k: [collect_ix(k, A), collect_ix(k, A)]))
    seq.append(('collect-deposit-collect', 'collect, System transfer 5,000 payer->vault, collect',
                [acct(A, 10**9), acct(VA, R0 + 50_000)],
                lambda k: [collect_ix(k, A), transfer_ix(PAYER, VA, 5_000), collect_ix(k, A)]))
    seq.append(('deposit-into-rent-only-vault', 'vault exactly rent(0); transfer 1 payer->vault; collect',
                [acct(A, 10**9), acct(VA, R0)],
                lambda k: [collect_ix(k, A), transfer_ix(PAYER, VA, 1), collect_ix(k, A)]))
    seq.append(('rent-topup-then-collect', 'creator absent, amount 500,000 (skipped); payer tops creator '
                'up by 390,880; collect again', [acct(VA, R0 + 500_000)],
                lambda k: [collect_ix(k, A), transfer_ix(PAYER, A, 390_880), collect_ix(k, A)]))
    seq.append(('rent-topup-short-by-1', 'as rent-topup-then-collect but top-up 390,879',
                [acct(VA, R0 + 500_000)],
                lambda k: [collect_ix(k, A), transfer_ix(PAYER, A, 390_879), collect_ix(k, A)]))
    seq.append(('two-creators', 'collect for creator A then creator B',
                [acct(A, 10**9), acct(VA, R0 + 1_000), acct(CREATOR_B, 10**9), acct(vault_of(CREATOR_B), R0 + 2_000)],
                lambda k: [collect_ix(k, A), collect_ix(k, CREATOR_B)]))
    seq.append(('collect-then-failing-transfer', 'collect succeeds, then a payer->vault transfer larger '
                'than the payer balance fails; whole transaction rolled back',
                [acct(A, 10**9), acct(VA, R0 + 50_000)],
                lambda k: [collect_ix(k, A), transfer_ix(PAYER, VA, 10**13)]))
    seq.append(('drain-vault-below-rent-then-collect', 'vault holds rent(0)+10; collect; creator '
                'cannot pull more; second collect logs no fee', [acct(A, 10**9), acct(VA, R0 + 10)],
                lambda k: [collect_ix(k, A), collect_ix(k, A)]))
    for name, note, extra, build in seq:
        for tag, kind in kinds:
            add(f'{tag}-seq-{name}', note, base_accounts() + extra, build(kind))
    for name, note, extra in [('mixed-v1-then-v2', 'v1 collect, deposit 7,000, v2 collect', []),
                              ('mixed-v2-then-v1', 'v2 collect, deposit 7,000, v1 collect', [])]:
        order = ['collect_creator_fee', 'collect_creator_fee_v2']
        if 'v2-then' in name:
            order.reverse()
        add(f'seq-{name}', note, base_accounts() + [acct(A, 10**9), acct(VA, R0 + 40_000)],
            [collect_ix(order[0], A), transfer_ix(PAYER, VA, 7_000), collect_ix(order[1], A)])

    # ---- v2 SPL-quote path (token amount from the vault ATA) ----
    def spl_accounts(amount, dest=True, src_state=1):
        out = base_accounts(True) + [acct(A, 10**9), acct(VA, R0 + 99)]
        out.append(acct(ata(VA, QUOTE_SPL), rent(165), TOKEN, token_data(QUOTE_SPL, VA, amount, state=src_state)))
        if dest:
            out.append(acct(ata(A, QUOTE_SPL), rent(165), TOKEN, token_data(QUOTE_SPL, A, 0)))
        return out
    v2 = 'collect_creator_fee_v2'
    add('v2-spl-amount-1', 'SPL quote; vault ATA holds 1 token unit', spl_accounts(1), [collect_ix(v2, A, QUOTE_SPL)])
    add('v2-spl-amount-u64max', 'SPL quote; vault ATA holds u64::MAX', spl_accounts(U64), [collect_ix(v2, A, QUOTE_SPL)])
    add('v2-spl-amount-0', 'SPL quote; vault ATA empty (vault lamports above rent are not collected)',
        spl_accounts(0), [collect_ix(v2, A, QUOTE_SPL)])
    add('v2-spl-collect-twice', 'SPL quote; collect, collect', spl_accounts(4_242),
        [collect_ix(v2, A, QUOTE_SPL), collect_ix(v2, A, QUOTE_SPL)])
    add('v2-spl-destination-missing', 'SPL quote; creator ATA absent (not created by v2)', spl_accounts(4_242, dest=False),
        [collect_ix(v2, A, QUOTE_SPL)])
    add('v2-spl-source-frozen', 'SPL quote; vault ATA frozen, 4,242 units', spl_accounts(4_242, src_state=2),
        [collect_ix(v2, A, QUOTE_SPL)])
    add('v2-spl-then-native', 'SPL collect then WSOL-native collect for the same creator', spl_accounts(4_242),
        [collect_ix(v2, A, QUOTE_SPL), collect_ix(v2, A, WSOL)])
    add('v2-spl-owner-pump-fees', 'SPL quote; creator owned by pump_fees',
        [a if a[0] != str(A) else acct(A, 10**9, FEES) for a in spl_accounts(4_242)], [collect_ix(v2, A, QUOTE_SPL)])
    return cases


# ---- execution (verify.py imports this from the packet copy) ----

LOADERS = ('upgradeable',)


def load_vm(image):
    vm = LiteSVM().with_transaction_history(0).with_sigverify(True)
    elf = Path(image).read_bytes()
    programdata = Pubkey.find_program_address([bytes(PROGRAM)], UPGRADEABLE)[0]
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + elf, UPGRADEABLE, False))
    vm.set_account(PROGRAM, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    return vm


FIXED = {PROGRAM, TOKEN, ATA_PROGRAM, SYSTEM}


def run_case(vm, index, c):
    vm.expire_blockhash()
    vm.set_clock(Clock(1000 + index, BASE_TS, 0, 0, c['unix_timestamp']))
    keys = set()
    for k, lam, owner, data in c['accounts']:
        key = Pubkey.from_string(k)
        keys.add(key)
        vm.set_account(key, Account(lam, bytes.fromhex(data), Pubkey.from_string(owner)))
    ixs = []
    for ix in c['instructions']:
        metas = [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in ix['metas']]
        keys |= {m.pubkey for m in metas}
        ixs.append(Instruction(Pubkey.from_string(ix['program']), bytes.fromhex(ix['data_hex']), metas))
    payer = Keypair.from_seed(PAYER_SEED)
    tx = Transaction.new_signed_with_payer(ixs, payer.pubkey(), [payer], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    logs = list(meta.logs())
    after = {}
    for key in sorted(keys - FIXED, key=str):
        a = vm.get_account(key)
        if a is not None and (a.lamports or a.data):
            after[str(key)] = [a.lamports, str(a.owner), a.executable, hashlib.sha256(bytes(a.data)).hexdigest()]
    for key in keys - FIXED:  # reset so the next case starts from its own state only
        vm.set_account(key, Account(0, b'', SYSTEM))
    return {'case': c['case'],
            'transaction_base64': base64.b64encode(bytes(tx)).decode(),
            'error': str(result.err()) if failed else None,
            'events': [l[14:] for l in logs if l.startswith('Program data: ')],
            'handler_messages': [l[13:] for l in logs if l.startswith('Program log: ')
                                 and not l.startswith('Program log: Instruction: ')
                                 and not l.startswith('Program log: AnchorError')],
            'inner_instructions': json.loads(meta.to_json())['inner_instructions'],
            'accounts_after': after, 'compute_units': meta.compute_units_consumed(), 'logs': logs}


def run_plan(image, loader, cases):
    assert loader == 'upgradeable'
    vm = load_vm(image)
    return [run_case(vm, i, c) for i, c in enumerate(cases)]


BEHAVIOR = ('transaction_base64', 'error', 'events', 'handler_messages', 'inner_instructions', 'accounts_after')
SITE = 'Program log: AnchorError thrown in '


def classify_logs(original, candidate):
    if len(original) != len(candidate):
        return [{'kind': 'line-count', 'original': len(original), 'candidate': len(candidate)}]
    out = []
    for a, b in zip(original, candidate):
        if a == b:
            continue
        if a.startswith(SITE) and b.startswith(SITE) and a.split('. ', 1)[1:] == b.split('. ', 1)[1:]:
            out.append({'kind': 'anchor-error-site', 'original': a[len(SITE):].split('. ')[0],
                        'candidate': b[len(SITE):].split('. ')[0]})
        elif ' consumed ' in a and ' consumed ' in b:
            out.append({'kind': 'consumed', 'original': a, 'candidate': b})
        else:
            out.append({'kind': 'other', 'original': a, 'candidate': b})
    return out


def outcome(r):
    if r['error']:
        for line in r['logs']:
            if 'Error Code: ' in line:
                return 'error:' + line.split('Error Code: ', 1)[1].split('.', 1)[0]
        return 'error:' + r['error']
    return 'ok:' + ('|'.join(r['handler_messages']) or 'transferred')


def lamport_delta(c, r, key):
    before = next((a[1] for a in c['accounts'] if a[0] == key), 0)
    return r['accounts_after'].get(key, [0])[0] - before


def summarize(cases, original, candidate):
    rows = []
    for c, ro, rc in zip(cases, original, candidate):
        creator = c['instructions'][0]['metas'][0][0]
        rows.append({'case': c['case'], 'note': c['note'],
                     'outcome': {'original': outcome(ro), 'candidate': outcome(rc)},
                     'collect_events': {'original': len(ro['events']), 'candidate': len(rc['events'])},
                     'creator_lamport_delta': {'original': lamport_delta(c, ro, creator),
                                               'candidate': lamport_delta(c, rc, creator)},
                     'compute_units': {'original': ro['compute_units'], 'candidate': rc['compute_units'],
                                       'original_minus_candidate': ro['compute_units'] - rc['compute_units']},
                     'logs_equal': ro['logs'] == rc['logs'],
                     'differing_log_lines': classify_logs(ro['logs'], rc['logs']),
                     'behavior_differences': [k for k in BEHAVIOR if ro[k] != rc[k]]})
    outcomes, deltas, kinds = {}, {}, {}
    for r in rows:
        o = r['outcome']['original']
        outcomes[o] = outcomes.get(o, 0) + 1
        dk = str(r['compute_units']['original_minus_candidate'])
        deltas[dk] = deltas.get(dk, 0) + 1
        kind = ','.join(sorted({d['kind'] for d in r['differing_log_lines']})) or 'none'
        kinds[kind] = kinds.get(kind, 0) + 1
    return {'case_count': len(rows),
            'behavior_mismatches': [r['case'] for r in rows if r['behavior_differences']],
            'compute_units_equal_cases': sum(r['compute_units']['original_minus_candidate'] == 0 for r in rows),
            'logs_equal_cases': sum(r['logs_equal'] for r in rows),
            'cases_by_outcome': dict(sorted(outcomes.items())),
            'compute_unit_delta_counts': dict(sorted(deltas.items())),
            'log_difference_kinds': dict(sorted(kinds.items())),
            'cases': rows}


def write_gz(path, text):
    path.write_bytes(gzip.compress(text.encode(), mtime=0))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    images = json.loads(args.images)
    idl_path = args.root / 'evidence/upstream/pump.json'
    idl = json.loads(idl_path.read_text())
    assert idl['address'] == str(PROGRAM)
    for name, disc in IX.items():  # discriminators and account counts must match the upstream IDL
        ix = next(i for i in idl['instructions'] if i['name'] == name)
        assert bytes(ix['discriminator']) == disc and len(ix['accounts']) == IX_ACCOUNTS[name], name
    assert next(e['code'] for e in idl['errors']
                if e['name'] == 'UnableToDistributeCreatorVaultMigratedToSharingConfig') == 6050
    cases = plan()
    blobs = {n: Path(images[n]).read_bytes() for n in ('original', 'candidate')}
    runtime = args.out / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*'):
        old.unlink()
    write_gz(runtime / 'plan.json.gz', json.dumps(cases, sort_keys=True, indent=0) + '\n')
    report = {'scope': 'Pump Main collect_creator_fee / collect_creator_fee_v2: destination-account boundaries, '
                       'v2 SPL-quote amounts and in-transaction sequences; original vs rebuild; upgradeable '
                       'loader; synthetic state; no network.',
              'images': {n: hashlib.sha256(b).hexdigest() for n, b in blobs.items()},
              'image_bytes': {n: len(b) for n, b in blobs.items()},
              'behavior_fields': list(BEHAVIOR), 'loaders': {}, 'receipts': {},
              'idl_sha256': hashlib.sha256(idl_path.read_bytes()).hexdigest()}
    for loader in LOADERS:
        original = run_plan(images['original'], loader, cases)
        candidate = run_plan(images['candidate'], loader, cases)
        lines = []
        for ro, rc in zip(original, candidate):
            lines += [json.dumps({'loader': loader, 'image': 'original', **ro}, sort_keys=True, separators=(',', ':')),
                      json.dumps({'loader': loader, 'image': 'candidate', **rc}, sort_keys=True, separators=(',', ':'))]
        name = f'receipts-{loader}.jsonl.gz'
        write_gz(runtime / name, '\n'.join(lines) + '\n')
        report['receipts'][name] = {'count': len(lines),
                                    'sha256': hashlib.sha256((runtime / name).read_bytes()).hexdigest()}
        report['loaders'][loader] = summarize(cases, original, candidate)
    write_gz(runtime / 'report.json.gz', json.dumps(report, sort_keys=True, indent=1) + '\n')
    for loader, s in report['loaders'].items():
        print(loader, json.dumps({k: s[k] for k in ('case_count', 'behavior_mismatches', 'compute_units_equal_cases',
                                                    'logs_equal_cases', 'cases_by_outcome',
                                                    'compute_unit_delta_counts', 'log_difference_kinds')}, indent=1))


if __name__ == '__main__':
    main()
