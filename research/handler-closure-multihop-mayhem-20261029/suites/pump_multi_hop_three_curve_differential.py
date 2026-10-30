#!/usr/bin/env python3
"""Three Pump curve hops through the actual captured AMM, normally signed.

Bounded extension of the retained ordinary Tokenkeg chains: the retained
`tokenkeg_two_curve` corpus drives two Pump bonding-curve hop groups per AMM
multi_hop_swap (Pump CPI hop_fees length 2, 10 remaining accounts). This suite
adds ONE more hop level: three consecutive Pump curve hop groups (Pump CPI
hop_fees length 3, 15 remaining accounts, three `swap_hop` iterations), with the
native/WSOL curve at both chain endpoints (native input on buy, native output on
sell) and a middle non-native Tokenkeg hop carrying gates (0,0).

Offline synthetic local state. No RPC, privileged signer substitution,
initializer instruction, historical-payload modification or extension fixtures.
Each side has a fresh VM and loads exactly one selected Pump executable; the AMM
and dependency ELFs are always the captured originals. Outer signatures are
ordinary test-owned keys and are verified. No fabricated PDA signatures.
"""
from pathlib import Path
import argparse
import base64
import gzip
import hashlib
import importlib.util
import json
import re
import struct
import sys

sys.dont_write_bytecode = True
from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

W = Path(__file__).resolve().parent
REPO = Path('/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/pumpfun-source-maintained')
FROZEN = REPO / 'repro/pump/tokenkeg-two-curve-fortyeight/harness/pump_tokenkeg_two_curve_differential.py'
spec = importlib.util.spec_from_file_location('tokenkeg_two_curve_frozen', FROZEN)
tk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tk)

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
R = tk.R
PUMP, AMM, TOKEN, TOKEN22, ATA, FEES, WSOL = tk.PUMP, tk.AMM, tk.TOKEN, tk.TOKEN22, tk.ATA, tk.FEES, tk.WSOL
USER, KEYS, TEMPLATE = tk.USER, tk.KEYS, tk.TEMPLATE
ata, token, config, PROGRAMS = tk.ata, tk.token, tk.config, tk.PROGRAMS
PUMP_DISC = tk.PUMP_DISC

# Retained two-curve fixture anchors.
A, C_A, B, C_B, VB, VQB, UB, UW, VA, VQA = tk.A, tk.C_A, tk.B, tk.C_B, tk.VB, tk.VQB, tk.UB, tk.UW, tk.VA, tk.VQA
# One more hop level: third Tokenkeg curve C (base C, quote B).
C = Pubkey.from_bytes(bytes([85]) * 32)
C_C = Pubkey.find_program_address([b'bonding-curve', bytes(C)], PUMP)[0]
VC = ata(C_C, C)
VQC = ata(C_C, B)
UC = ata(USER.pubkey(), C)

FIXED = 16  # AMM MultiHop fixed account count before hop groups


def invoke(sell, amount, mode, limit=1, candidate=None, mutation=None, label='', compute_limit=0):
    """One AMM multi_hop_swap driving a three-curve-hop Pump CPI run.

    `compute_limit` 0 leaves LiteSVM's default 200,000-unit budget untouched;
    any other value is requested explicitly with a compute-budget instruction
    (the create suites use 1,400,000 the same way).
    """
    vm = LiteSVM().with_transaction_history(0)
    vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
    selected = [(pid, R / p) for pid, p in PROGRAMS] + [(PUMP, candidate or R / 'evidence/original/pump/deployed.so')]
    for pid, path in selected:
        vm.add_program_from_file(pid, path)
    for key, row in TEMPLATE['accounts'].items():
        if row is not None:
            vm.set_account(Pubkey.from_string(key), Account(row['lamports'], bytes.fromhex(row['data_hex']), Pubkey.from_string(row['owner'])))
    vol = bytes(next(x for x in tk.IDL['accounts'] if x['name'] == 'UserVolumeAccumulator')['discriminator']) + bytes(USER.pubkey()) + bytes(97)
    vm.set_account(KEYS[5], Account(10**9, vol, AMM))
    # Native curve A exactly as the retained fixture (quote_mint = default).
    raw_a = bytearray(vm.get_account(C_A).data)
    assert len(raw_a) == 166 and raw_a[48] == 0 and raw_a[81:83] == b'\0\0' and raw_a[83:115] == bytes(32) and raw_a[124] == 0
    # Second and third curves copy the same canonical recipe with their quote mints.
    def curve_data(quote):
        raw = bytearray(vm.get_account(C_A).data)
        for offset in [8, 16, 24, 32, 40, 142]:
            struct.pack_into('<Q', raw, offset, 10**15)
        raw[83:115] = bytes(quote)
        raw[125:141] = bytes(16)
        raw[141] = 1
        return bytes(raw)
    vm.set_account(C_B, Account(10**9, curve_data(A), PUMP))
    vm.set_account(C_C, Account(10**9, curve_data(B), PUMP))
    mint_a = vm.get_account(A)
    assert mint_a.owner == TOKEN and len(mint_a.data) == 82
    vm.set_account(B, Account(mint_a.lamports, bytes(mint_a.data), TOKEN))
    vm.set_account(C, Account(mint_a.lamports, bytes(mint_a.data), TOKEN))
    vm.set_account(VB, Account(10**9, token(B, C_B, 10**15), TOKEN))
    vm.set_account(VQB, Account(10**9, token(A, C_B, 10**15), TOKEN))
    vm.set_account(VC, Account(10**9, token(C, C_C, 10**15), TOKEN))
    vm.set_account(VQC, Account(10**9, token(B, C_C, 10**15), TOKEN))
    vm.set_account(UB, Account(10**9, token(B, USER.pubkey(), 10**15), TOKEN))
    vm.set_account(UC, Account(10**9, token(C, USER.pubkey(), 10**15), TOKEN))
    old = vm.get_account(KEYS[1])
    vm.set_account(UW, Account(old.lamports, bytes(old.data), TOKEN))
    fee = vm.get_account(KEYS[14])
    vm.set_account(KEYS[14], Account(fee.lamports, config(mode), fee.owner))
    fixed = KEYS[:FIXED]
    fixed = list(fixed)
    fixed[1] = UC if sell else UW
    fixed[2] = UW if sell else UC
    metas = [AccountMeta(k, bool(spec_.get('signer')), bool(spec_.get('writable'))) for k, spec_ in zip(fixed, tk.IX['accounts'])]
    group_a = [A, WSOL, C_A, VA, VQA]
    group_b = [B, A, C_B, VB, VQB]
    group_c = [C, B, C_C, VC, VQC]
    for group in [group_c, group_b, group_a] if sell else [group_a, group_b, group_c]:
        metas.extend(AccountMeta(key, False, i >= 2) for i, key in enumerate(group))
    assert all(not m.is_signer for m in metas if m.pubkey == KEYS[3])
    if mutation:
        mutation(vm, metas)

    def snapshot():
        rows = {}
        for key in sorted({m.pubkey for m in metas}, key=str):
            acc = vm.get_account(key)
            if not acc or acc.executable:
                continue
            rows[str(key)] = None if not acc else {'lamports': acc.lamports, 'owner': str(acc.owner), 'data_hex': bytes(acc.data).hex()}
        return rows

    before = snapshot()
    data = bytes(tk.IX['discriminator']) + struct.pack('<QQ', amount, limit)
    instructions = []
    if compute_limit:
        instructions.append(set_compute_unit_limit(compute_limit))
    instructions.append(Instruction(AMM, data, metas))
    tx = Transaction.new_signed_with_payer(instructions, USER.pubkey(), [USER], vm.latest_blockhash())
    assert all(tx.verify_with_results()) and len(tx.signatures) == 1
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    encoded = json.loads(meta.to_json())
    inner = encoded['inner_instructions']
    keys = tx.message.account_keys
    pump_calls, token_calls = [], []
    for group in inner:
        for entry in group:
            ix = entry['instruction']
            payload = bytes(ix['data'][1:])
            accounts = [str(keys[i]) for i in ix['accounts'][1:]]
            pid = keys[ix['programIdIndex']]
            if pid == PUMP and payload.startswith(PUMP_DISC):
                length = struct.unpack_from('<I', payload, 16)[0]
                flags = list(payload[20:20 + length])
                assert flags == ([2, 0, 1] if sell else [1, 0, 2]), flags
                assert len(accounts) == 28 and accounts[2] == str(KEYS[3])
                pump_calls.append({'amount': struct.unpack_from('<Q', payload, 8)[0], 'hop_fees': flags, 'accounts': accounts})
            if pid == TOKEN:
                token_calls.append({'data_hex': payload.hex(), 'accounts': accounts})
    return {'case': label, 'error': str(result.err()) if failed else None, 'logs': meta.logs(),
            'events': [x for x in meta.logs() if x.startswith('Program data: ')], 'inner': inner,
            'return_data': encoded.get('return_data'), 'before': before, 'after': snapshot(),
            'compute': parse_compute(meta.logs()),
            'transaction_base64': base64.b64encode(bytes(tx)).decode(),
            'transaction_sha256': hashlib.sha256(bytes(tx)).hexdigest(),
            'verified_signature_count': len(tx.signatures), 'fresh_vm': True,
            'pump_calls': pump_calls, 'token_calls': token_calls,
            'program_sha256': {str(pid): sha(path) for pid, path in selected}}


# ---------------- negative mutations (same style as the retained harnesses) ----------------
def curve_field(key, offset, value):
    def action(vm, metas):
        acc = vm.get_account(key)
        data = bytearray(acc.data)
        data[offset:offset + len(value)] = value
        vm.set_account(key, Account(max(acc.lamports, 10**9), bytes(data), acc.owner))
    return action


def meta_readonly(index):
    def action(vm, metas):
        old = metas[index]
        metas[index] = AccountMeta(old.pubkey, old.is_signer, False)
    return action


def meta_replace(index, key):
    def action(vm, metas):
        old = metas[index]
        metas[index] = AccountMeta(key, old.is_signer, old.is_writable)
    return action


def truncate(n_remove):
    def action(vm, metas):
        del metas[len(metas) - n_remove:]
    return action


def extend_partial(n_add):
    def action(vm, metas):
        metas.extend(AccountMeta(Pubkey.from_bytes(bytes([90 + i]) * 32), False, True) for i in range(n_add))
    return action


def key_data(index, offset, value):
    def action(vm, metas):
        acc = vm.get_account(metas[index].pubkey)
        data = bytearray(acc.data)
        data[offset:offset + len(value)] = value
        vm.set_account(metas[index].pubkey, Account(acc.lamports, bytes(data), acc.owner))
    return action


def fixtures():
    for sell in [False, True]:
        side = 'sell' if sell else 'buy'
        for mode in ['captured', 'exotic', 'flat-fallback', 'legacy-flat']:
            for amount in [10**6, 10**9]:
                yield f'three-{side}-{mode}-{amount}', sell, amount, mode, 1, None
        # Positive boundaries.
        yield f'three-{side}-amount-one', sell, 1, 'captured', 1, None
        # Post-Pump slippage rollback at the AMM endpoint.
        yield f'three-{side}-final-slippage', sell, 10**9, 'captured', 2**64 - 1, None
        # AMM pre-Pump rejections of the chain shape.
        yield f'three-{side}-zero-input', sell, 0, 'captured', 1, None
        yield f'three-{side}-truncated-group', sell, 10**9, 'captured', 1, truncate(1)
        yield f'three-{side}-extra-partial-group', sell, 10**9, 'captured', 1, extend_partial(3)
        yield f'three-{side}-wrong-user-out', sell, 10**9, 'captured', 1, meta_replace(2, UB)
        yield f'three-{side}-huge-amount', sell, 2**64 - 1, 'captured', 1, None
        # Middle-hop Pump boundaries (hop 2 of 3) reached through the genuine CPI.
        yield f'three-{side}-mid-quote-mint-mismatch', sell, 10**9, 'captured', 1, curve_field(C_B, 83, bytes([7]) * 32)
        yield f'three-{side}-mid-curve-complete', sell, 10**9, 'captured', 1, curve_field(C_B, 48, b'\1')
        yield f'three-{side}-mid-curve-mayhem', sell, 10**9, 'captured', 1, curve_field(C_B, 81, b'\1')
        yield f'three-{side}-mid-curve-cashback', sell, 10**9, 'captured', 1, curve_field(C_B, 82, b'\1')
        yield f'three-{side}-mid-curve-substituted', sell, 10**9, 'captured', 1, meta_replace(23, C_C)
        yield f'three-{side}-mid-base-vault-substituted', sell, 10**9, 'captured', 1, meta_replace(24, VC)
        yield f'three-{side}-mid-quote-vault-readonly', sell, 10**9, 'captured', 1, meta_readonly(25)
        yield f'three-{side}-mid-vault-mint-corrupt', sell, 10**9, 'captured', 1, curve_field(VQB, 0, bytes([7]) * 32)
        # Pump account-parse boundaries forwarded unchanged by the AMM.
        yield f'three-{side}-fee-discriminator', sell, 10**9, 'captured', 1, key_data(14, 0, bytes(8))
        yield f'three-{side}-global-discriminator', sell, 10**9, 'captured', 1, key_data(13, 0, bytes(8))


COMPUTE_LINE = re.compile(r'Program (\w+) consumed (\d+) of (\d+) compute units')


def parse_compute(logs):
    rows = []
    for line in logs:
        m = COMPUTE_LINE.search(line)
        if m:
            rows.append({'program': m.group(1), 'consumed': int(m.group(2)), 'budget': int(m.group(3))})
    return rows


def compare(a, b):
    fields = ['error', 'events', 'inner', 'return_data', 'before', 'after', 'pump_calls', 'token_calls']
    return [k for k in fields if a[k] != b[k]]


def bindings(candidate):
    paths = {str(FROZEN.relative_to(R)), str((FROZEN.parent / 'base-fixture.json').relative_to(R)),
             'evidence/upstream/pump_amm.json', 'evidence/original/pump/deployed.so'} | {p for _, p in PROGRAMS}
    runtime = {}
    for name, module in sorted(sys.modules.items()):
        p = getattr(module, '__file__', None)
        if name.startswith('solders') and p and Path(p).is_file():
            runtime[str(Path(p).resolve())] = sha(p)
    runtime[str(Path(sys.executable).resolve())] = sha(Path(sys.executable).resolve())
    return {'repository_inputs': {p: sha(R / p) for p in sorted(paths)},
            'suite_script_sha256': sha(Path(__file__)),
            'runtime_files': runtime, 'python_version': sys.version,
            'candidate_sha256': sha(candidate) if candidate else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compute-limit', type=int, default=1_400_000,
                        help='0 keeps LiteSVM\'s default 200,000-unit budget (compute-bound observation mode)')
    parser.add_argument('--only', default='',
                        help='optional substring filter on case labels (debugging)')
    args = parser.parse_args()
    assert not args.output.exists(), 'Retain prior attempts; output must be fresh'
    candidate = args.candidate.resolve()
    before = bindings(candidate)
    rows = []
    for label, sell, amount, mode, limit, mutation in fixtures():
        if args.only and args.only not in label:
            continue
        original = invoke(sell, amount, mode, limit, None, mutation, label, args.compute_limit)
        current = invoke(sell, amount, mode, limit, candidate, mutation, label, args.compute_limit)
        mismatches = compare(original, current)
        logs_equal = original['logs'] == current['logs']
        rows.append({'case': label,
                     'parameters': {'sell': sell, 'amount': amount, 'fee_mode': mode, 'limit': limit,
                                    'mutation': None if mutation is None else label.split('-', 2)[-1],
                                    'compute_limit': args.compute_limit},
                     'original': original, 'candidate': current, 'mismatches': mismatches,
                     'ordered_logs_equal': logs_equal,
                     'completed_hop_events_equal_prefix': current['events'][:len(original['events'])] == original['events']})
        print(json.dumps({'case': label, 'original_error': original['error'], 'candidate_error': current['error'],
                          'pump_calls': len(original['pump_calls']), 'mismatches': mismatches,
                          'ordered_logs_equal': logs_equal}), flush=True)
    assert before == bindings(candidate), 'inputs changed during execution'
    out = {'scope': __doc__,
           'mode': 'original-versus-candidate',
           'compute_limit': args.compute_limit,
           'description': 'Three Pump curve hops per AMM multi_hop_swap (Pump CPI hop_fees length 3). '
                          'One hop level beyond the retained two-curve Tokenkeg chains (hop_fees length 2). '
                          'compute_limit 0 documents the default-200k compute-bound divergence; 1,400,000 gates semantics.',
           'provenance': before, 'inputs_unchanged': True,
           'candidate_sha256': sha(candidate),
           'original_pump_sha256': sha(R / 'evidence/original/pump/deployed.so'),
           'captured_amm_sha256': sha(R / 'evidence/original/pump_amm/deployed.so'),
           'case_count': len(rows),
           'original_successes': sum(r['original']['error'] is None for r in rows),
           'original_pump_cpi_cases': sum(bool(r['original']['pump_calls']) for r in rows),
           'verified_outer_signatures': sum(r['original']['verified_signature_count'] + r['candidate']['verified_signature_count'] for r in rows),
           'ordered_log_mismatches': [r['case'] for r in rows if not r['ordered_logs_equal']],
           'mismatches': [r['case'] for r in rows if r['mismatches']],
           'cases': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(out, separators=(',', ':')) + '\n').encode()
    args.output.write_bytes(gzip.compress(payload, mtime=0) if args.output.suffix == '.gz' else payload)
    print(json.dumps({k: v for k, v in out.items() if k not in ('cases', 'provenance', 'scope')}, indent=2))
    if out['mismatches']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
