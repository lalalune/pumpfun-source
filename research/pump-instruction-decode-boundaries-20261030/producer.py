#!/usr/bin/env python3
"""Pump Main instruction-dispatch and argument-decoding boundaries, original vs rebuild.

For every instruction in the upstream IDL (evidence/upstream/pump.json) this sends
malformed or minimal instruction data, with no accounts or with placeholder
accounts, and records what the program does before any handler body can run:
the Anchor dispatcher (empty / short / unknown discriminators, event-CPI and
IDL discriminators), Borsh argument decoding (truncated args, trailing bytes,
the omittable OptionBool / CreationOptionU64 tails, bool and Option tags of 2)
and the first account-validation check.

Only the Pump program image under test is loaded. Nothing else is needed,
because no step gets past argument decoding or the first account constraint
far enough to make a CPI. Keys come from fixed seeds, the clock is fixed and
there is no network.

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
PAYER = Keypair.from_seed(bytes([231]) * 32)
PLACEHOLDER = Pubkey(bytes([77]) * 32)  # never funded: system-owned, 0 lamports
OTHER = Pubkey(bytes([78]) * 32)        # never funded; fills unresolvable non-signer slots
FOREIGN_AUTHORITY = Pubkey(bytes([79]) * 32)
GLOBAL = Pubkey.find_program_address([b'global'], PROGRAM)[0]
GLOBAL_DISC = bytes([167, 232, 232, 177, 200, 108, 114, 127])
GLOBAL_LEN = 1088
EVENT_IX_TAG = bytes.fromhex('e445a52e51cb9a1d')  # anchor event-CPI self-invoke tag
IDL_IX_TAG = bytes.fromhex('40f4bc78a7e9690a')    # anchor IDL-management tag
TAIL_TYPES = ('OptionBool', 'OptionU64')          # read as default when the data ends
BASE_TS = 1_800_000_000

# Anchor framework error codes (not part of the program IDL).
FRAMEWORK_ERRORS = {
    '100': 'InstructionMissing', '101': 'InstructionFallbackNotFound',
    '102': 'InstructionDidNotDeserialize', '103': 'InstructionDidNotSerialize',
    '1000': 'IdlInstructionStub', '1001': 'IdlInstructionInvalidProgram', '1002': 'IdlAccountNotEmpty',
    '1500': 'EventInstructionStub',
    '2000': 'ConstraintMut', '2001': 'ConstraintHasOne', '2002': 'ConstraintSigner',
    '2003': 'ConstraintRaw', '2004': 'ConstraintOwner', '2005': 'ConstraintRentExempt',
    '2006': 'ConstraintSeeds', '2007': 'ConstraintExecutable', '2009': 'ConstraintAssociated',
    '2011': 'ConstraintClose', '2012': 'ConstraintAddress', '2013': 'ConstraintZero',
    '2014': 'ConstraintTokenMint', '2015': 'ConstraintTokenOwner',
    '3000': 'AccountDiscriminatorAlreadySet', '3001': 'AccountDiscriminatorNotFound',
    '3002': 'AccountDiscriminatorMismatch', '3003': 'AccountDidNotDeserialize',
    '3004': 'AccountDidNotSerialize', '3005': 'AccountNotEnoughKeys', '3006': 'AccountNotMutable',
    '3007': 'AccountOwnedByWrongProgram', '3008': 'InvalidProgramId', '3009': 'InvalidProgramExecutable',
    '3010': 'AccountNotSigner', '3011': 'AccountNotSystemOwned', '3012': 'AccountNotInitialized',
    '3013': 'AccountNotProgramData', '3014': 'AccountNotAssociatedTokenAccount',
    '3015': 'AccountSysvarMismatch', '3016': 'AccountReallocExceedsLimit', '3017': 'AccountDuplicateReallocs',
    '4101': 'TryingToInitPayerAsProgramAccount',
}


def type_name(t):
    if isinstance(t, str):
        return t
    if 'defined' in t:
        return t['defined']['name']
    if 'option' in t:
        return 'option<' + type_name(t['option']) + '>'
    if 'vec' in t:
        return 'vec<' + type_name(t['vec']) + '>'
    raise ValueError(t)


def zero_arg(t):
    """Smallest valid Borsh encoding: zero numbers, empty strings/vecs, None, false."""
    name = type_name(t)
    fixed = {'u8': 1, 'bool': 1, 'u64': 8, 'i64': 8, 'pubkey': 32, 'OptionBool': 1, 'OptionU64': 8}
    if name in fixed:
        return bytes(fixed[name])
    if name in ('string', 'bytes') or name.startswith('vec<'):
        return bytes(4)
    if name.startswith('option<'):
        return b'\0'
    raise ValueError(name)


def variants(ins):
    """(label, data, account mode) steps for one IDL instruction."""
    disc = bytes(ins['discriminator'])
    args = ins['args']
    parts = [zero_arg(a['type']) for a in args]
    full = disc + b''.join(parts)
    out = [('disc-only', disc, 'none'), ('args-zero', full, 'none'),
           ('args-zero-plus-trailing-byte', full + b'\0', 'none')]
    if args:
        out.append(('args-zero-minus-last-byte', full[:-1], 'none'))
    tail = len(args)
    while tail and type_name(args[tail - 1]['type']) in TAIL_TYPES:
        tail -= 1
    if tail < len(args):
        out.append(('optional-tail-omitted', disc + b''.join(parts[:tail]), 'none'))
        if type_name(args[-1]['type']) == 'OptionU64' or any(type_name(a['type']) == 'OptionU64' for a in args[tail:]):
            # cut inside the first OptionU64 of the tail (3 of 8 bytes present)
            idx = next(i for i in range(tail, len(args)) if type_name(args[i]['type']) == 'OptionU64')
            out.append(('optional-u64-partial-3-bytes', disc + b''.join(parts[:idx]) + b'\x07\x00\x00', 'none'))
        for i in range(tail, len(args)):
            if type_name(args[i]['type']) == 'OptionBool':
                bad = list(parts)
                bad[i] = b'\x02'
                out.append((f'option-bool-2-{args[i]["name"]}', disc + b''.join(bad), 'none'))
                break
    for i, a in enumerate(args):
        if type_name(a['type']) == 'bool':
            bad = list(parts)
            bad[i] = b'\x02'
            out.append((f'bool-2-{a["name"]}', disc + b''.join(bad), 'none'))
            break
    for i, a in enumerate(args):
        if type_name(a['type']).startswith('option<'):
            bad = list(parts)
            bad[i] = b'\x02'
            out.append((f'option-tag-2-{a["name"]}', disc + b''.join(bad), 'none'))
            break
    for i, a in enumerate(args):
        if type_name(a['type']) in ('string', 'bytes') or type_name(a['type']).startswith('vec<'):
            bad = list(parts)
            bad[i] = b'\x01\x00\x00\x00'  # declares one element, supplies none
            out.append((f'length-1-no-body-{a["name"]}', disc + b''.join(bad), 'none'))
            break
    n = len(ins['accounts'])
    out += [('accounts-placeholder-readonly', full, ('placeholder', n)),
            ('accounts-payer-all', full, ('payer', n)),
            ('accounts-payer-one-short', full, ('payer', n - 1)),
            ('accounts-resolved-no-global', full, ('resolved', n)),
            ('accounts-resolved-global-foreign-authority', full, ('resolved+global:foreign', n)),
            ('accounts-resolved-global-payer-authority', full, ('resolved+global:payer', n))]
    return out


def resolve_slot(acct):
    """IDL account -> (pubkey, source): fixed address, const-seed PDA, payer for signers, else OTHER."""
    if 'address' in acct:
        return Pubkey.from_string(acct['address']), 'address'
    pda = acct.get('pda')
    if pda and all(s['kind'] == 'const' for s in pda['seeds']) and pda.get('program', {'kind': 'const'})['kind'] == 'const':
        program = Pubkey(bytes(pda['program']['value'])) if 'program' in pda else PROGRAM
        return Pubkey.find_program_address([bytes(s['value']) for s in pda['seeds']], program)[0], 'const-pda'
    if acct['name'] == 'program':
        return PROGRAM, 'program'
    if acct.get('signer'):
        return PAYER.pubkey(), 'payer'
    return OTHER, 'other'


def resolved_metas(ins):
    out = []
    for acct in ins['accounts']:
        key, _ = resolve_slot(acct)
        out.append(AccountMeta(key, key == PAYER.pubkey(), bool(acct.get('writable'))))
    return out


def initial_global(authority):
    """Synthetic Global (IDL layout, 1,088 bytes); same values as pump-global-admin-sequences."""
    d = bytearray(GLOBAL_LEN)
    d[:8] = GLOBAL_DISC
    d[8] = 1
    d[9:41] = bytes(authority)
    d[41:73] = bytes(Pubkey(bytes([90]) * 32))
    struct.pack_into('<QQQQQ', d, 73, 1_073_000_000_000_000, 30_000_000_000,
                     793_100_000_000_000, 1_000_000_000_000_000, 95)
    d[450] = 1  # create_v2_enabled
    for i in range(8):
        d[741 + 32 * i:773 + 32 * i] = bytes([100 + i]) * 32
    struct.pack_into('<QQ', d, 997, 5000, 30_000_000_000)
    d[1013:1045] = bytes(Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'))
    return bytes(d)


def framework_variants(idl):
    buy = bytes(next(i['discriminator'] for i in idl['instructions'] if i['name'] == 'buy'))
    return [('empty', b'', 'none'), ('one-byte', buy[:1], 'none'), ('four-bytes', buy[:4], 'none'),
            ('seven-bytes', buy[:7], 'none'), ('unknown-zeros', bytes(8), 'none'),
            ('unknown-ff', b'\xff' * 8, 'none'), ('unknown-zeros-with-payer', bytes(8), ('payer', 4)),
            ('event-tag-only', EVENT_IX_TAG, 'none'), ('event-tag-payer', EVENT_IX_TAG, ('payer', 1)),
            ('event-tag-placeholder', EVENT_IX_TAG + bytes(8), ('placeholder', 1)),
            ('idl-tag-only', IDL_IX_TAG, 'none'), ('idl-tag-create-payer', IDL_IX_TAG + b'\0' + bytes(8), ('payer', 5))]


def metas(mode, ins=None):
    if mode == 'none':
        return []
    kind, n = mode
    if kind == 'payer':
        return [AccountMeta(PAYER.pubkey(), True, True)] * n
    if kind.startswith('resolved'):
        return resolved_metas(ins)
    return [AccountMeta(PLACEHOLDER, False, False)] * n


def step_dict(variant, data, mode, ins=None):
    """A fully explicit step: verify.py replays these without the IDL."""
    authority = None
    if mode != 'none' and mode[0].startswith('resolved+global:'):
        authority = str(PAYER.pubkey() if mode[0].endswith(':payer') else FOREIGN_AUTHORITY)
    return {'variant': variant, 'data_hex': data.hex(),
            'accounts_mode': mode if mode == 'none' else mode[0],
            'metas': [[str(m.pubkey), m.is_signer, m.is_writable] for m in metas(mode, ins)],
            'global_authority': authority}


def cases(idl):
    out = [('framework-dispatch', [step_dict(*v) for v in framework_variants(idl)])]
    for ins in sorted(idl['instructions'], key=lambda i: i['name']):
        out.append((ins['name'], [step_dict(*v, ins) for v in variants(ins)]))
    return out


def run_step(vm, label, k, index, step):
    vm.expire_blockhash()
    vm.set_clock(Clock(1000 + index, 0, 0, 0, BASE_TS + index))
    if step['global_authority']:
        vm.set_account(GLOBAL, Account(10**10, initial_global(Pubkey.from_string(step['global_authority'])), PROGRAM))
    ix_metas = [AccountMeta(Pubkey.from_string(k_), s, w) for k_, s, w in step['metas']]
    tx = Transaction.new_signed_with_payer([Instruction(PROGRAM, bytes.fromhex(step['data_hex']), ix_metas)],
                                           PAYER.pubkey(), [PAYER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    details = json.loads(meta.to_json())
    logs = list(meta.logs())
    ret = meta.return_data()
    global_after = vm.get_account(GLOBAL)
    global_hex = bytes(global_after.data).hex() if global_after is not None else ''
    if step['global_authority']:
        vm.set_account(GLOBAL, Account(0, b'', Pubkey.default()))
    return {
        'case': label, 'step': k, 'variant': step['variant'], 'data_hex': step['data_hex'],
        'accounts_mode': step['accounts_mode'], 'account_count': len(step['metas']),
        'transaction_base64': base64.b64encode(bytes(tx)).decode(),
        'error': str(result.err()) if failed else None,
        'return_data_hex': bytes(ret.data).hex() if ret is not None else '',
        'events': [l[14:] for l in logs if l.startswith('Program data: ')],
        'inner_instructions': details['inner_instructions'],
        'global_after_hex': global_hex,
        'payer_lamports_after': vm.get_balance(PAYER.pubkey()),
        'compute_units': meta.compute_units_consumed(), 'logs': logs}


def run_plan(image, plan):
    vm = load_vm(image)
    receipts, index = [], 0
    for label, steps in plan:
        for k, step in enumerate(steps):
            receipts.append(run_step(vm, label, k, index, step))
            index += 1
    return receipts


def load_vm(image):
    vm = LiteSVM().with_transaction_history(0).with_sigverify(True)
    vm.add_program_from_file(PROGRAM, str(image))
    vm.airdrop(PAYER.pubkey(), 10**12)
    return vm


def custom_code(error):
    if error is None:
        return None
    marker = 'Custom('
    if marker in error:
        return int(error.split(marker, 1)[1].split(')', 1)[0])
    return error


SITE = 'Program log: AnchorError thrown in '
CAUSED = 'Program log: AnchorError caused by account: '
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
                        'original_site': sa, 'candidate_site': sb})
        elif a.startswith(CONSUMED) and b.startswith(CONSUMED):
            out.append({'kind': 'consumed', 'original': a[len(CONSUMED):], 'candidate': b[len(CONSUMED):]})
        else:
            out.append({'kind': 'other', 'original': a, 'candidate': b})
    return out


BEHAVIOR = ('transaction_base64', 'error', 'return_data_hex', 'events', 'inner_instructions',
            'global_after_hex', 'payer_lamports_after')


def global_reference(receipt):
    """Global bytes as written before the step (resolved+global modes only)."""
    mode = receipt['accounts_mode']
    if not mode.startswith('resolved+global:'):
        return ''
    return initial_global(PAYER.pubkey() if mode.endswith(':payer') else FOREIGN_AUTHORITY).hex()


def caused_by(logs):
    for line in logs:
        if line.startswith(CAUSED):
            return line[len(CAUSED):]
    return None


def summarize(images_sha, receipts, error_names):
    by = {}
    for r in receipts:
        by.setdefault(r['case'], {}).setdefault(r['image'], []).append(r)
    rows = []
    for label, imgs in by.items():
        steps = []
        for ro, rc in zip(imgs['original'], imgs['candidate']):
            code = custom_code(ro['error'])
            steps.append({'step': ro['step'], 'variant': ro['variant'], 'data_bytes': len(ro['data_hex']) // 2,
                          'accounts_mode': ro['accounts_mode'], 'account_count': ro['account_count'],
                          'global_changed': ro['global_after_hex'] not in ('', global_reference(ro)),
                          'error_original': ro['error'], 'error_candidate': rc['error'],
                          'custom_code': code,
                          'error_name': error_names.get(str(code)) if isinstance(code, int) else None,
                          'caused_by_account': {'original': caused_by(ro['logs']), 'candidate': caused_by(rc['logs'])},
                          'compute_units': {'original': ro['compute_units'], 'candidate': rc['compute_units']},
                          'logs_equal': ro['logs'] == rc['logs'],
                          'differing_log_lines': classify_logs(ro['logs'], rc['logs']),
                          'behavior_differences': [k for k in BEHAVIOR if ro[k] != rc[k]]})
        rows.append({'label': label, 'steps': steps, 'match': all(not s['behavior_differences'] for s in steps)})
    all_steps = [s for row in rows for s in row['steps']]
    by_error, deltas, kinds, sites, by_variant = {}, {}, {}, {}, {}
    for s in all_steps:
        key = s['error_name'] or str(s['custom_code'])
        by_error[key] = by_error.get(key, 0) + 1
        delta = s['compute_units']['original'] - s['compute_units']['candidate']
        dk = f"{delta}:{key}"
        deltas[dk] = deltas.get(dk, 0) + 1
        kind = ','.join(sorted(set(d['kind'] for d in s['differing_log_lines']))) or 'none'
        kinds[kind] = kinds.get(kind, 0) + 1
        for d in s['differing_log_lines']:
            if d['kind'] == 'anchor-error-site':
                sites[d['original_site'] + ' -> ' + d['candidate_site']] = 1
        v = next((p for p in ('bool-2', 'option-bool-2', 'option-tag-2', 'length-1-no-body')
                  if s['variant'].startswith(p + '-')), s['variant'])
        vk = v + ' => ' + key
        by_variant[vk] = by_variant.get(vk, 0) + 1
    return {'scope': 'Pump Main instruction dispatch, Borsh argument decoding and first account check; '
                     'original vs rebuild; only the pump image is loaded; no network.',
            'images': images_sha, 'behavior_fields': list(BEHAVIOR), 'case_count': len(rows),
            'step_count': len(all_steps),
            'mismatches': [row['label'] for row in rows if not row['match']],
            'mismatched_steps': [f"{row['label']}/{s['variant']}" for row in rows for s in row['steps']
                                 if s['behavior_differences']],
            'compute_units_equal_steps': sum(1 for s in all_steps if s['compute_units']['original'] == s['compute_units']['candidate']),
            'logs_equal_steps': sum(1 for s in all_steps if s['logs_equal']),
            'succeeded_steps': sum(1 for s in all_steps if s['error_original'] is None),
            'succeeded_step_names': [f"{row['label']}/{s['variant']}" for row in rows for s in row['steps']
                                     if s['error_original'] is None],
            'global_changed_step_names': [f"{row['label']}/{s['variant']}" for row in rows for s in row['steps']
                                          if s['global_changed']],
            'steps_by_error': dict(sorted(by_error.items())),
            'steps_by_variant_and_error': dict(sorted(by_variant.items())),
            'compute_unit_delta_by_error': dict(sorted(deltas.items())),
            'log_difference_kinds': dict(sorted(kinds.items())),
            'anchor_error_sites': sorted(sites),
            'error_names': error_names, 'cases': rows}


def produce(images, plan):
    shas = {name: hashlib.sha256(Path(images[name]).read_bytes()).hexdigest() for name in ('original', 'candidate')}
    receipts = []
    for image in ('original', 'candidate'):
        receipts += [{'image': image, **r} for r in run_plan(images[image], plan)]
    order = [p[0] for p in plan]
    receipts.sort(key=lambda r: (order.index(r['case']), r['step'], r['image']))
    return shas, receipts


def write_gz(path, text):
    path.write_bytes(gzip.compress(text.encode(), mtime=0))


def load_idl(root):
    idl = json.loads((root / 'evidence/upstream/pump.json').read_text())
    assert idl['address'] == str(PROGRAM)
    return idl


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    images = json.loads(args.images)
    idl = load_idl(args.root)
    error_names = dict(FRAMEWORK_ERRORS)
    error_names.update({str(e['code']): e['name'] for e in idl['errors']})
    plan = cases(idl)
    shas, receipts = produce(images, plan)
    runtime = args.out / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*'):
        old.unlink()
    # The explicit plan (data + account metas per step) lets verify.py replay without the IDL.
    write_gz(runtime / 'plan.json.gz',
             json.dumps([{'case': label, 'steps': steps} for label, steps in plan], sort_keys=True, indent=0) + '\n')
    parts = []
    per_part = 200
    for n in range(0, len(receipts), per_part):
        name = f'runtime/receipts-part{n // per_part + 1:02d}.jsonl.gz'
        chunk = receipts[n:n + per_part]
        write_gz(args.out / name, ''.join(json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n' for r in chunk))
        data = (args.out / name).read_bytes()
        parts.append({'file': name, 'count': len(chunk), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    report = summarize(shas, receipts, error_names)
    report['receipt_count'] = len(receipts)
    report['parts'] = parts
    report['idl_sha256'] = hashlib.sha256((args.root / 'evidence/upstream/pump.json').read_bytes()).hexdigest()
    write_gz(runtime / 'report.json.gz', json.dumps(report, sort_keys=True, indent=1) + '\n')
    print(json.dumps({'cases': report['case_count'], 'steps': report['step_count'], 'receipts': len(receipts),
                      'mismatches': report['mismatches'], 'mismatched_steps': report['mismatched_steps'][:20],
                      'cu_equal': report['compute_units_equal_steps'], 'logs_equal': report['logs_equal_steps'],
                      'succeeded': report['succeeded_steps'], 'by_error': report['steps_by_error'],
                      'log_kinds': report['log_difference_kinds']}, indent=1))


if __name__ == '__main__':
    main()
