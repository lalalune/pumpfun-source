#!/usr/bin/env python3
"""Pump Main Global admin-command sequences on persistent state, original vs rebuild.

Every case is a sequence of normally signed transactions sent to one LiteSVM
instance, so each step sees the Global account the previous step left behind.
Only the Pump program image under test is loaded; the Global account is built
from the IDL layout (1,088 bytes) with fixed-seed keypairs. No network.

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
GLOBAL = Pubkey.find_program_address([b'global'], PROGRAM)[0]
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
USDC = Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
KEYS = {name: Keypair.from_seed(bytes([seed]) * 32) for name, seed in
        (('payer', 240), ('A', 241), ('B', 242), ('C', 243))}
MINT_X = Pubkey(bytes([61]) * 32)
MINT_Y = Pubkey(bytes([62]) * 32)
BUYBACK = [Pubkey(bytes([100 + i]) * 32) for i in range(8)]
NEW_BUYBACK = [Pubkey(bytes([120 + i]) * 32) for i in range(9)]
FEE_RECIPIENT = Pubkey(bytes([90]) * 32)

GLOBAL_DISC = bytes([167, 232, 232, 177, 200, 108, 114, 127])
DISC = {
    'update_global_authority': [227, 181, 74, 196, 208, 21, 97, 213],
    'add_quote_mint': [111, 121, 21, 56, 40, 24, 94, 209],
    'remove_quote_mint': [177, 65, 223, 38, 88, 209, 158, 155],
    'toggle_create_v2': [28, 255, 230, 240, 172, 107, 203, 171],
    'toggle_mayhem_mode': [1, 9, 111, 208, 100, 31, 255, 163],
    'toggle_cashback_enabled': [115, 103, 224, 255, 189, 89, 86, 195],
    'set_max_curve_depth': [32, 154, 152, 219, 142, 108, 218, 165],
    'set_virtual_quote_reserves': [101, 135, 191, 104, 9, 88, 20, 96],
    'update_buyback_config': [251, 224, 171, 146, 160, 26, 113, 233],
    'update_creator_fee_config': [61, 175, 160, 249, 66, 66, 136, 175],
    'update_holder_reward_config': [225, 252, 66, 4, 199, 35, 236, 16],
}
# Global field offsets (IDL layout, 8-byte discriminator first).
OFF = {'authority': 9, 'create_v2_enabled': 450, 'mayhem_mode_enabled': 515,
       'is_cashback_enabled': 740, 'buyback_fee_recipients': 741,
       'buyback_basis_points': 997, 'initial_virtual_quote_reserves': 1005,
       'whitelisted_quote_mint': 1013, 'creator_fee_configurable': 1045,
       'max_configurable_creator_fee_bps': 1046, 'holder_reward_claim_authority': 1054,
       'is_holder_reward_enabled': 1086, 'max_curve_depth': 1087}
GLOBAL_LEN = 1088
U64 = 2**64 - 1
BASE_TS = 1_800_000_000


def initial_global():
    d = bytearray(GLOBAL_LEN)
    d[:8] = GLOBAL_DISC
    d[8] = 1
    d[9:41] = bytes(KEYS['A'].pubkey())
    d[41:73] = bytes(FEE_RECIPIENT)
    struct.pack_into('<QQQQQ', d, 73, 1_073_000_000_000_000, 30_000_000_000,
                     793_100_000_000_000, 1_000_000_000_000_000, 95)
    d[450] = 1  # create_v2_enabled
    for i, key in enumerate(BUYBACK):
        d[741 + 32 * i:773 + 32 * i] = bytes(key)
    struct.pack_into('<QQ', d, 997, 5000, 30_000_000_000)
    d[1013:1045] = bytes(USDC)
    return bytes(d)


def decode_global(raw):
    raw = bytes(raw)
    q = lambda off: struct.unpack_from('<Q', raw, off)[0]
    k = lambda off: str(Pubkey(raw[off:off + 32]))
    return {'len': len(raw), 'authority': k(9), 'create_v2_enabled': raw[450],
            'mayhem_mode_enabled': raw[515], 'is_cashback_enabled': raw[740],
            'buyback_fee_recipients': [k(741 + 32 * i) for i in range(8)],
            'buyback_basis_points': q(997), 'initial_virtual_quote_reserves': q(1005),
            'whitelisted_quote_mint': k(1013), 'creator_fee_configurable': raw[1045],
            'max_configurable_creator_fee_bps': q(1046),
            'holder_reward_claim_authority': k(1054),
            'is_holder_reward_enabled': raw[1086], 'max_curve_depth': raw[1087]}


def u64(n):
    return struct.pack('<Q', n)


def ix(name, signer='A', arg=b'', new_authority=None, remaining=(), authority_writable=True):
    """One admin instruction; signer is a key name or a raw Pubkey (unsigned)."""
    who = KEYS[signer].pubkey() if isinstance(signer, str) else signer
    signed = isinstance(signer, str)
    if name == 'update_global_authority':
        metas = [AccountMeta(GLOBAL, False, True), AccountMeta(who, signed, False),
                 AccountMeta(new_authority, False, False)]
    else:
        metas = [AccountMeta(GLOBAL, False, True), AccountMeta(who, signed, authority_writable)]
    metas += [AccountMeta(EVENT, False, False), AccountMeta(PROGRAM, False, False)]
    metas += [AccountMeta(key, False, False) for key in remaining]
    return {'name': name, 'signer': signer if signed else str(signer),
            'instruction': Instruction(PROGRAM, bytes(DISC[name]) + arg, metas)}


def boolean(b):
    return bytes([1 if b else 0])


def opt_u64(v):
    return b'\0' if v is None else b'\1' + u64(v)


def pk(name):
    return KEYS[name].pubkey()


def cases():
    """Returns [(label, [step, ...])]; a step is a list of instructions sent in one transaction."""
    A, B, C = 'A', 'B', 'C'
    out = []
    add = lambda label, *steps: out.append((label, [list(s) for s in steps]))
    t = lambda name, enabled, signer=A: ix(name, signer, boolean(enabled))
    rot = lambda signer, new: ix('update_global_authority', signer, new_authority=new)
    # authority rotation
    add('rotate-a-b-then-old-rejected', [rot(A, pk(B))], [t('toggle_mayhem_mode', True, A)],
        [t('toggle_mayhem_mode', True, B)])
    add('rotate-chain-a-b-c', [rot(A, pk(B))], [rot(B, pk(C))], [t('toggle_cashback_enabled', True, A)],
        [t('toggle_cashback_enabled', True, B)], [t('toggle_cashback_enabled', True, C)])
    add('rotate-to-self', [rot(A, pk(A))], [t('toggle_mayhem_mode', True, A)])
    add('rotate-by-non-authority', [rot(B, pk(B))], [t('toggle_mayhem_mode', True, B)],
        [t('toggle_mayhem_mode', True, A)])
    add('rotate-back-a-b-a', [rot(A, pk(B))], [rot(B, pk(A))], [t('toggle_mayhem_mode', True, B)],
        [t('toggle_mayhem_mode', True, A)])
    add('rotate-to-default-locks-admin', [rot(A, Pubkey.default())], [t('toggle_mayhem_mode', True, A)],
        [rot(A, pk(A))])
    add('rotate-to-global-pda', [rot(A, GLOBAL)], [rot(A, pk(A))])
    add('rotate-to-program-id', [rot(A, PROGRAM)], [t('toggle_create_v2', False, A)])
    add('rotate-twice-in-one-tx', [rot(A, pk(B)), rot(B, pk(C))], [t('toggle_mayhem_mode', True, C)])
    add('rotate-then-old-signs-same-tx', [rot(A, pk(B)), t('toggle_mayhem_mode', True, A)],
        [t('toggle_mayhem_mode', True, A)])
    add('rotate-then-new-signs-same-tx', [rot(A, pk(B)), t('toggle_mayhem_mode', True, B)],
        [t('toggle_mayhem_mode', False, B)])
    # toggles: require_neq on the stored flag
    for name, start in (('toggle_create_v2', True), ('toggle_mayhem_mode', False),
                        ('toggle_cashback_enabled', False)):
        add(f'{name.replace("_", "-")}-cycle', [t(name, start)], [t(name, not start)],
            [t(name, not start)], [t(name, start)], [t(name, start)])
    add('toggle-pair-in-one-tx', [t('toggle_mayhem_mode', True), t('toggle_mayhem_mode', False)],
        [t('toggle_mayhem_mode', True), t('toggle_mayhem_mode', True)])
    # single-slot quote-mint whitelist
    q = lambda name, mint, signer=A: ix(name, signer, bytes(mint))
    add('quote-mint-full-then-swap', [q('add_quote_mint', MINT_X)], [q('add_quote_mint', USDC)],
        [q('remove_quote_mint', USDC)], [q('add_quote_mint', MINT_X)], [q('add_quote_mint', MINT_Y)],
        [q('remove_quote_mint', MINT_Y)], [q('remove_quote_mint', MINT_X)], [q('remove_quote_mint', MINT_X)])
    add('quote-mint-ineligible-on-empty', [q('remove_quote_mint', USDC)], [q('add_quote_mint', Pubkey.default())],
        [q('add_quote_mint', WSOL)], [q('remove_quote_mint', Pubkey.default())], [q('remove_quote_mint', WSOL)],
        [q('add_quote_mint', USDC)])
    add('quote-mint-swap-in-one-tx', [q('remove_quote_mint', USDC), q('add_quote_mint', MINT_X)],
        [q('remove_quote_mint', MINT_X), q('add_quote_mint', MINT_Y), q('add_quote_mint', USDC)])
    add('quote-mint-non-authority', [q('remove_quote_mint', USDC, B)], [rot(A, pk(B))],
        [q('remove_quote_mint', USDC, B)], [q('add_quote_mint', MINT_X, A)])
    # buyback config
    bb = lambda value, remaining=(), signer=A: ix('update_buyback_config', signer, opt_u64(value), remaining=remaining)
    add('buyback-bps-bounds', [bb(10000)], [bb(10001)], [bb(None)], [bb(0)], [bb(U64)], [bb(9999)])
    add('buyback-recipients-rotate', [bb(None, NEW_BUYBACK[:8])], [bb(None, BUYBACK)], [bb(None, BUYBACK)])
    add('buyback-recipients-count', [bb(None, NEW_BUYBACK[:7])], [bb(None, NEW_BUYBACK[:9])],
        [bb(None, NEW_BUYBACK[:1])], [bb(7, NEW_BUYBACK[:8])])
    add('buyback-recipients-invalid-keep-bps', [bb(7000, NEW_BUYBACK[:7] + [NEW_BUYBACK[0]])],
        [bb(7000, NEW_BUYBACK[:7] + [Pubkey.default()])], [bb(10001, NEW_BUYBACK[:8])], [bb(7000)])
    # numeric setters
    add('creator-fee-config-sequence',
        [ix('update_creator_fee_config', A, boolean(True) + u64(U64))],
        [ix('update_creator_fee_config', A, boolean(False) + u64(0))],
        [ix('update_creator_fee_config', A, bytes([2]) + u64(1))],
        [ix('update_creator_fee_config', B, boolean(True) + u64(10000))])
    add('max-curve-depth-and-reserves',
        [ix('set_max_curve_depth', A, bytes([255]))], [ix('set_max_curve_depth', A, bytes([0]))],
        [ix('set_virtual_quote_reserves', A, u64(U64))], [ix('set_virtual_quote_reserves', A, u64(0))],
        [ix('set_virtual_quote_reserves', A, u64(1)[:7])])
    add('holder-reward-config-sequence',
        [ix('update_holder_reward_config', A, boolean(True) + bytes(pk(C)))],
        [ix('update_holder_reward_config', A, boolean(False) + bytes(32))],
        [ix('update_holder_reward_config', A, bytes([2]) + bytes(pk(C)))])
    # authority account metadata
    add('authority-readonly-then-writable',
        [ix('set_max_curve_depth', A, bytes([9]), authority_writable=False)],
        [ix('set_max_curve_depth', A, bytes([9]))])
    add('authority-unsigned-key', [ix('toggle_mayhem_mode', pk(A), boolean(True))],
        [t('toggle_mayhem_mode', True)])
    # whole-sequence atomicity: last instruction fails, earlier writes must roll back
    add('mixed-tx-rollback',
        [rot(A, pk(B)), t('toggle_cashback_enabled', True, B), bb(10000, signer=B),
         q('remove_quote_mint', USDC, B), q('remove_quote_mint', USDC, B)],
        [t('toggle_cashback_enabled', True, A)])
    return out


def load_vm(image):
    vm = LiteSVM().with_transaction_history(0).with_sigverify(True)
    vm.add_program_from_file(PROGRAM, str(image))
    for name in ('payer', 'A', 'B', 'C'):
        vm.airdrop(KEYS[name].pubkey(), 10**10)
    vm.set_account(GLOBAL, Account(10**10, initial_global(), PROGRAM))
    return vm


def run_case(image, label, steps):
    vm = load_vm(image)
    receipts = []
    for index, step in enumerate(steps):
        vm.expire_blockhash()
        vm.set_clock(Clock(1000 + index, 0, 0, 0, BASE_TS + index))
        signers = [KEYS['payer']] + [KEYS[n] for n in dict.fromkeys(s['signer'] for s in step) if n in KEYS]
        tx = Transaction.new_signed_with_payer([s['instruction'] for s in step], KEYS['payer'].pubkey(),
                                               signers, vm.latest_blockhash())
        before = vm.get_account(GLOBAL).data
        result = vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        details = json.loads(meta.to_json())
        logs = list(meta.logs())
        after = vm.get_account(GLOBAL).data
        receipts.append({
            'case': label, 'step': index, 'instructions': [s['name'] for s in step],
            'signers': [s['signer'] for s in step],
            'transaction_base64': base64.b64encode(bytes(tx)).decode(),
            'error': str(result.err()) if failed else None,
            'global_before_hex': bytes(before).hex(), 'global_after_hex': bytes(after).hex(),
            'events': [l[14:] for l in logs if l.startswith('Program data: ')],
            'inner_instructions': details['inner_instructions'],
            'compute_units': meta.compute_units_consumed(), 'logs': logs})
    return receipts


def custom_code(error):
    if error is None:
        return None
    marker = 'Custom('
    if marker in error:
        return int(error.split(marker, 1)[1].split(')', 1)[0])
    return error


SITE = 'Program log: AnchorError thrown in '
CONSUMED = 'Program ' + str(PROGRAM) + ' consumed '


def classify_logs(original, candidate):
    """Pairs differing log lines; kinds: anchor-error-site, consumed, other (or line-count)."""
    if len(original) != len(candidate):
        return [{'kind': 'line-count', 'original': len(original), 'candidate': len(candidate)}]
    out = []
    for a, b in zip(original, candidate):
        if a == b:
            continue
        if a.startswith(SITE) and b.startswith(SITE):
            sa, ra = a[len(SITE):].split('. ', 1)
            sb, rb = b[len(SITE):].split('. ', 1)
            out.append({'kind': 'anchor-error-site' if ra == rb else 'other',
                        'original_site': sa, 'candidate_site': sb,
                        'length_delta': len(a) - len(b)})
        elif a.startswith(CONSUMED) and b.startswith(CONSUMED):
            out.append({'kind': 'consumed', 'original': a[len(CONSUMED):], 'candidate': b[len(CONSUMED):]})
        else:
            out.append({'kind': 'other', 'original': a, 'candidate': b})
    return out


BEHAVIOR = ('transaction_base64', 'error', 'global_before_hex', 'global_after_hex', 'events', 'inner_instructions')


def summarize(images_sha, receipts, error_names):
    by = {}
    for r in receipts:
        by.setdefault(r['case'], {}).setdefault(r['image'], []).append(r)
    rows = []
    for label, imgs in by.items():
        o, c = imgs['original'], imgs['candidate']
        steps = []
        for ro, rc in zip(o, c):
            diff = [k for k in BEHAVIOR if ro[k] != rc[k]]
            code = custom_code(ro['error'])
            steps.append({'step': ro['step'], 'instructions': ro['instructions'], 'signers': ro['signers'],
                          'error_original': ro['error'], 'error_candidate': rc['error'],
                          'custom_code': code, 'error_name': error_names.get(str(code)) if isinstance(code, int) else None,
                          'global_changed': ro['global_before_hex'] != ro['global_after_hex'],
                          'global_after': decode_global(bytes.fromhex(ro['global_after_hex'])),
                          'events': len(ro['events']),
                          'compute_units': {'original': ro['compute_units'], 'candidate': rc['compute_units']},
                          'logs_equal': ro['logs'] == rc['logs'],
                          'differing_log_lines': classify_logs(ro['logs'], rc['logs']),
                          'behavior_differences': diff})
        rows.append({'label': label, 'steps': steps,
                     'match': all(not s['behavior_differences'] for s in steps)})
    cu_equal = sum(1 for row in rows for s in row['steps']
                   if s['compute_units']['original'] == s['compute_units']['candidate'])
    total = sum(len(row['steps']) for row in rows)
    deltas, kinds, sites = {}, {}, {}
    for row in rows:
        for s in row['steps']:
            delta = s['compute_units']['original'] - s['compute_units']['candidate']
            key = f"{delta}:{s['error_name']}"
            deltas[key] = deltas.get(key, 0) + 1
            kind = ','.join(sorted(set(d['kind'] for d in s['differing_log_lines']))) or 'none'
            kinds[kind] = kinds.get(kind, 0) + 1
            for d in s['differing_log_lines']:
                if d['kind'] == 'anchor-error-site':
                    sites[d['original_site'] + ' -> ' + d['candidate_site']] = 1
    return {'scope': 'Pump Main Global admin-command sequences on persistent state; original vs rebuild; '
                     'only the pump image is loaded; synthetic Global from the IDL layout; no network.',
            'images': images_sha, 'behavior_fields': list(BEHAVIOR), 'case_count': len(rows), 'step_count': total,
            'mismatches': [row['label'] for row in rows if not row['match']],
            'compute_units_equal_steps': cu_equal,
            'logs_equal_steps': sum(1 for row in rows for s in row['steps'] if s['logs_equal']),
            'failed_steps': sum(1 for row in rows for s in row['steps'] if s['error_original'] is not None),
            'compute_unit_delta_by_error': dict(sorted(deltas.items())),
            'log_difference_kinds': dict(sorted(kinds.items())),
            'anchor_error_sites': sorted(sites),
            'error_names': error_names, 'cases': rows}


def produce(images, error_names):
    shas = {name: hashlib.sha256(Path(images[name]).read_bytes()).hexdigest() for name in ('original', 'candidate')}
    receipts = []
    for label, steps in cases():
        for image in ('original', 'candidate'):
            for r in run_case(images[image], label, steps):
                receipts.append({'image': image, **r})
    return shas, receipts


def write_gz(path, text):
    path.write_bytes(gzip.compress(text.encode(), mtime=0))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    images = json.loads(args.images)
    idl = json.loads((args.root / 'evidence/upstream/pump.json').read_text())
    assert idl['address'] == str(PROGRAM)
    for name, disc in DISC.items():
        assert next(i['discriminator'] for i in idl['instructions'] if i['name'] == name) == disc, name
    assert next(a['discriminator'] for a in idl['accounts'] if a['name'] == 'Global') == list(GLOBAL_DISC)
    error_names = {str(e['code']): e['name'] for e in idl['errors']}
    # Anchor framework codes reached by these cases (not part of the program IDL).
    error_names.update({'102': 'InstructionDidNotDeserialize', '2000': 'ConstraintMut', '3010': 'AccountNotSigner'})
    shas, receipts = produce(images, error_names)
    runtime = args.out / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*'):
        old.unlink()
    parts = []
    per_part = 40
    for n in range(0, len(receipts), per_part):
        name = f'runtime/receipts-part{n // per_part + 1:02d}.jsonl.gz'
        chunk = receipts[n:n + per_part]
        write_gz(args.out / name, ''.join(json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n' for r in chunk))
        data = (args.out / name).read_bytes()
        parts.append({'file': name, 'count': len(chunk), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    report = summarize(shas, receipts, {k: v for k, v in error_names.items()})
    report['receipt_count'] = len(receipts)
    report['parts'] = parts
    write_gz(runtime / 'report.json.gz', json.dumps(report, sort_keys=True, indent=1) + '\n')
    print(json.dumps({'cases': report['case_count'], 'steps': report['step_count'], 'receipts': len(receipts),
                      'mismatches': report['mismatches'], 'cu_equal': report['compute_units_equal_steps'],
                      'logs_equal': report['logs_equal_steps'], 'failed_steps': report['failed_steps']}))


if __name__ == '__main__':
    main()
