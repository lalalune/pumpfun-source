#!/usr/bin/env python3
"""Pump Fees instruction dispatch, Borsh argument decoding and first-account checks.

Builds a plan of malformed / minimal instructions for all 31 pump_fees IDL
instructions plus the Anchor dispatcher, runs every step on the original and the
rebuilt image in LiteSVM (one fresh VM per step, only the pump_fees image loaded),
and writes deterministic receipts and a report under --out/runtime/.
"""
import argparse, gzip, hashlib, io, json, pathlib, re, struct, sys

from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PAYER = Keypair.from_seed(bytes([231]) * 32)
PAYER_LAMPORTS = 10 ** 12
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
IDL_IX_TAG = bytes.fromhex('40f4bc78a7e9690a')
BEHAVIOR = ['tx_sha256', 'error', 'return_data', 'events', 'inner_instructions', 'payer_lamports', 'accounts']


def unfunded(i):
    return Pubkey.from_bytes(hashlib.sha256(b'pump-fees-decode-unfunded-%d' % i).digest())


# ---------------------------------------------------------------- arguments
def scalar(t):
    return {'u8': b'\x01', 'u16': b'\x02\x00', 'u64': struct.pack('<Q', 3), 'i64': struct.pack('<q', 4),
            'u128': (5).to_bytes(16, 'little'), 'bool': b'\x01', 'pubkey': bytes([7]) * 32}.get(t)


def encode(t, types):
    """Return (bytes, parts) where parts lists mutable spans: (kind, offset, length-of-full-encoding)."""
    if isinstance(t, str):
        if t == 'string':
            return struct.pack('<I', 3) + b'abc', [('len', 0)]
        return scalar(t), ([('bool', 0)] if t == 'bool' else [])
    if 'option' in t:
        body, parts = encode(t['option'], types)
        return b'\x01' + body, [('opt', 0)] + [(k, o + 1) for k, o in parts]
    if 'vec' in t:
        body, parts = encode(t['vec'], types)
        return struct.pack('<I', 1) + body, [('len', 0)] + [(k, o + 4) for k, o in parts]
    if 'defined' in t:
        d = types[t['defined']['name']]['type']
        out, parts = b'', []
        for f in d['fields']:
            ft = f if isinstance(f, str) else f['type']
            b, p = encode(ft, types)
            if t['defined']['name'] == 'OptionBool':
                p = [('optbool', 0)]
            parts += [(k, o + len(out)) for k, o in p]
            out += b
        return out, parts
    raise ValueError(t)


def args_layout(ix, types):
    out, spans = b'', []
    for a in ix['args']:
        b, parts = encode(a['type'], types)
        spans += [(a['name'], k, o + len(out), len(b)) for k, o in parts]
        out += b
    return out, spans


# ---------------------------------------------------------------- accounts
def resolve(acc, program, used):
    if acc.get('signer'):
        return PAYER.pubkey(), 'payer'
    if 'address' in acc:
        return Pubkey.from_string(acc['address']), 'address'
    if acc['name'] == 'program':
        return program, 'program'
    pda = acc.get('pda')
    if pda and all(s['kind'] == 'const' for s in pda['seeds']):
        owner = program
        if 'program' in pda:
            if pda['program']['kind'] != 'const':
                return None, None
            owner = Pubkey.from_bytes(bytes(pda['program']['value']))
        return Pubkey.find_program_address([bytes(s['value']) for s in pda['seeds']], owner)[0], 'pda'
    return None, None


def metas(keys):
    return [[str(k), bool(s), bool(w)] for k, s, w in keys]


def plan_for(idl):
    program = Pubkey.from_string(idl['address'])
    types = {t['name']: t for t in idl['types']}
    cases = []
    payer = str(PAYER.pubkey())

    def step(label, data, accs):
        return {'label': label, 'data': data.hex(), 'accounts': accs}

    # Anchor dispatcher
    disc0 = bytes(idl['instructions'][0]['discriminator'])
    first_unfunded = [[str(unfunded(0)), False, True]]
    ev = str(Pubkey.find_program_address([b'__event_authority'], program)[0])
    d = [step('empty-data', b'', []), step('one-byte', disc0[:1], []), step('four-bytes', disc0[:4], []),
         step('seven-bytes', disc0[:7], []), step('zero-disc', bytes(8), []), step('ff-disc', b'\xff' * 8, []),
         step('zero-disc-with-account', bytes(8), first_unfunded),
         step('event-cpi-tag-no-accounts', EVENT_CPI_TAG, []),
         step('event-cpi-tag-unsigned-event-authority', EVENT_CPI_TAG, [[ev, False, False]]),
         step('event-cpi-tag-payer-signer', EVENT_CPI_TAG, [[payer, True, True]]),
         step('event-cpi-tag-seven-bytes', EVENT_CPI_TAG[:7], []),
         step('idl-tag-no-accounts', IDL_IX_TAG, []), step('idl-tag-create-payload', IDL_IX_TAG + b'\x00' + struct.pack('<Q', 64), [[payer, True, True]]),
         step('idl-tag-seven-bytes', IDL_IX_TAG[:7], [])]
    cases.append({'name': 'dispatcher', 'instruction': None, 'steps': d})

    for ix in sorted(idl['instructions'], key=lambda x: x['name']):
        disc = bytes(ix['discriminator'])
        args, spans = args_layout(ix, types)
        n = len(ix['accounts'])
        s = [step('disc-only', disc, []), step('valid-args', disc + args, []),
             step('trailing-byte', disc + args + b'\x00', [])]
        if args:
            s.append(step('last-byte-removed', disc + args[:-1], []))
        for name, kind, off, full in spans:
            if kind in ('bool', 'opt', 'optbool'):
                bad = bytearray(args); bad[off] = 2
                s.append(step('%s-%s-tag-2' % (name, kind), disc + bytes(bad), []))
            if kind == 'opt':
                s.append(step('%s-none' % name, disc + args[:off] + b'\x00' + args[off + full:], []))
                s.append(step('%s-none-with-stale-body' % name, disc + args[:off] + b'\x00' + args[off + 1:], []))
            if kind == 'optbool':
                s.append(step('%s-omitted' % name, disc + args[:off], []))
            if kind == 'len' and name == 'user_id':
                rest = args[off + full:]
                s.append(step('%s-invalid-utf8' % name, disc + args[:off] + struct.pack('<I', 3) + b'\xff\xfe\xfd' + rest, []))
                s.append(step('%s-len-3-only-2-body-bytes' % name, disc + args[:off] + struct.pack('<I', 3) + b'ab', []))
            if kind == 'len':
                rest = args[off + full:]
                s.append(step('%s-len-0' % name, disc + args[:off] + struct.pack('<I', 0) + rest, []))
                s.append(step('%s-len-1-no-body' % name, disc + args[:off] + struct.pack('<I', 1) + rest, []))
                s.append(step('%s-len-max' % name, disc + args[:off] + struct.pack('<I', 0xffffffff) + rest, []))
                s.append(step('%s-len-3-bytes' % name, disc + args[:off] + struct.pack('<I', 1)[:3], []))
        valid = disc + args
        if n:
            s.append(step('one-account-short', valid, [[str(unfunded(i)), False, True] for i in range(n - 1)]))
        s.append(step('unfunded-accounts', valid, [[str(unfunded(i)), False, True] for i in range(max(n, 1))]))
        s.append(step('payer-every-slot', valid, [[payer, True, True] for _ in range(max(n, 1))]))
        if n:
            res, i = [], 0
            for acc in ix['accounts']:
                k, how = resolve(acc, program, res)
                if k is None:
                    k = unfunded(100 + i); i += 1
                res.append([str(k), k == PAYER.pubkey(), bool(acc.get('writable')) or k == PAYER.pubkey()])
            s.append(step('idl-resolved', valid, res))
            s.append(step('idl-resolved-extra-account', valid, res + [[str(unfunded(99)), False, False]]))
        cases.append({'name': ix['name'], 'instruction': ix['name'], 'steps': s})
    return {'program_id': idl['address'], 'payer_seed': 231, 'payer_lamports': PAYER_LAMPORTS, 'cases': cases}


# ---------------------------------------------------------------- execution
def run_step(binary, program_id, st):
    program = Pubkey.from_string(program_id)
    vm = LiteSVM().with_log_bytes_limit(None).with_transaction_history(0)
    vm.add_program_from_file(program, binary)
    vm.airdrop(PAYER.pubkey(), PAYER_LAMPORTS)
    accs = [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in st['accounts']]
    tx = Transaction.new_signed_with_payer([Instruction(program, bytes.fromhex(st['data']), accs)],
                                           PAYER.pubkey(), [PAYER], vm.latest_blockhash())
    r = vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    rd = meta.return_data()
    keys = sorted({k for k, _, _ in st['accounts'] if k != program_id} | {str(PAYER.pubkey())})
    state = []
    for k in keys:
        a = vm.get_account(Pubkey.from_string(k))
        state.append(None if a is None else [k, a.lamports, str(a.owner), hashlib.sha256(bytes(a.data)).hexdigest(), len(a.data)])
    logs = list(meta.logs())
    return {
        'tx_sha256': hashlib.sha256(bytes(tx)).hexdigest(),
        'error': str(r.err()) if failed else None,
        'return_data': bytes(rd.data).hex() if rd is not None and bytes(rd.data) else None,
        'events': [l for l in logs if l.startswith('Program data:')],
        'inner_instructions': json.loads(meta.to_json()).get('inner_instructions'),
        'payer_lamports': vm.get_account(PAYER.pubkey()).lamports,
        'accounts': state,
        'logs': logs,
        'cu': meta.compute_units_consumed(),
    }


def panics(r):
    return r['error'] is not None and 'ProgramFailedToComplete' in r['error']


def add_length_boundaries(plan, binary):
    """Bisect, on the original image, the smallest declared length (no body) that makes
    Borsh decoding panic instead of returning 102. The two neighbouring lengths become
    plan steps; both images then run them."""
    out = []
    for case in plan['cases']:
        for st in list(case['steps']):
            if not st['label'].endswith('-len-max'):
                continue
            name = st['label'][:-len('-len-max')]
            data = bytes.fromhex(st['data'])
            pos = data.find(struct.pack('<I', 0xffffffff), 8)
            head, tail = data[:pos], data[pos + 4:]
            mk = lambda n: {'label': '%s-len-%d' % (name, n), 'data': (head + struct.pack('<I', n) + tail).hex(), 'accounts': []}
            if not panics(run_step(binary, plan['program_id'], st)):
                continue
            lo, hi = 1, 0xffffffff  # lo decodes to 102, hi panics
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if panics(run_step(binary, plan['program_id'], mk(mid))):
                    hi = mid
                else:
                    lo = mid
            case['steps'] += [mk(lo), mk(hi)]
            out.append([case['name'], name, lo, hi])
    plan['length_boundaries'] = out
    return plan


def run_plan(plan, images):
    out = []
    for case in plan['cases']:
        for st in case['steps']:
            rec = {'case': case['name'], 'label': st['label']}
            for side in ('original', 'candidate'):
                rec[side] = run_step(images[side], plan['program_id'], st)
            out.append(rec)
    return out


# ---------------------------------------------------------------- report
CODE = re.compile(r'Custom\((\d+)\)')


def code(err):
    if err is None:
        return 'ok'
    m = CODE.search(err)
    if m:
        return m.group(1)
    m = re.search(r'InstructionErrorMessage\s*\{?[^,]*,\s*(\w+)|InstructionError\(\s*\d+,\s*(\w+)', err)
    return (m.group(1) or m.group(2)) if m else err


def site(line):
    return re.sub(r'AnchorError thrown in [^ ]+:\d+\.', 'AnchorError thrown in <site>.', line)


def report(plan, receipts, shas):
    steps = len(receipts)
    behavior_diff, logcu_diff, codes = [], [], {}
    site_rows = []
    for r in receipts:
        o, c = r['original'], r['candidate']
        if any(o[k] != c[k] for k in BEHAVIOR):
            behavior_diff.append([r['case'], r['label'], [k for k in BEHAVIOR if o[k] != c[k]]])
        if o['logs'] != c['logs'] or o['cu'] != c['cu']:
            same_norm = [site(x) for x in o['logs']] == [site(x) for x in c['logs']]
            logcu_diff.append([r['case'], r['label'], o['cu'] - c['cu'], same_norm])
            for a, b in zip(o['logs'], c['logs']):
                if a != b:
                    site_rows.append([r['case'], r['label'], a, b]); break
        codes.setdefault(r['label'] if r['case'] != 'dispatcher' else 'dispatcher:' + r['label'], {}).setdefault(code(o['error']), []).append(r['case'])
    per_label = {}
    for r in receipts:
        if r['case'] == 'dispatcher':
            continue
        lab = r['label']
        for pre in ('-bool-tag-2', '-opt-tag-2', '-optbool-tag-2', '-len-0', '-len-1-no-body', '-len-max', '-len-3-bytes', '-none-with-stale-body', '-none', '-omitted'):
            if lab.endswith(pre):
                lab = '*' + pre; break
        else:
            if re.search(r'-len-\d+$', lab):
                lab = '*-len-bisected-neighbour'
        per_label.setdefault(lab, {}).setdefault(code(r['original']['error']), 0)
        per_label[lab][code(r['original']['error'])] += 1
    per_ix, blamed = {}, {}
    for r in receipts:
        per_ix.setdefault(r['case'], {})[r['label']] = code(r['original']['error'])
        for line in r['original']['logs']:
            m = re.search(r'caused by account: (\w+)\. Error Code: (\w+)', line)
            if m:
                blamed.setdefault(r['case'], {})[r['label']] = '%s:%s' % (m.group(1), m.group(2))
    return {
        'program': 'pump_fees', 'program_id': plan['program_id'],
        'original_sha256': shas['original'], 'candidate_sha256': shas['candidate'],
        'cases': len(plan['cases']), 'steps': steps, 'receipts': 2 * steps,
        'behavior_compared_fields': BEHAVIOR,
        'behavior_mismatch_steps': behavior_diff,
        'log_or_cu_mismatch_steps': logcu_diff,
        'first_differing_log_line': site_rows,
        'length_boundaries': plan.get('length_boundaries', []),
        'outcome_by_variant': {k: dict(sorted(v.items())) for k, v in sorted(per_label.items())},
        'outcome_by_instruction': per_ix,
        'blamed_account_by_instruction': blamed,
    }


def gz(obj_bytes):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0, filename='') as f:
        f.write(obj_bytes)
    return buf.getvalue()


def dumps(o):
    return json.dumps(o, sort_keys=True, separators=(',', ':'))


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', required=True, type=pathlib.Path)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', required=True, type=pathlib.Path)
    a = ap.parse_args()
    images = json.loads(a.images)
    idl = json.loads((a.root / 'evidence/upstream/pump_fees.json').read_text())
    plan = add_length_boundaries(plan_for(idl), images['original'])
    receipts = run_plan(plan, images)
    shas = {k: sha(images[k]) for k in ('original', 'candidate')}
    rep = report(plan, receipts, shas)
    rt = a.out / 'runtime'
    rt.mkdir(parents=True, exist_ok=True)
    (rt / 'plan.json.gz').write_bytes(gz(dumps(plan).encode()))
    (rt / 'receipts.jsonl.gz').write_bytes(gz(''.join(dumps(r) + '\n' for r in receipts).encode()))
    (rt / 'report.json.gz').write_bytes(gz(json.dumps(rep, sort_keys=True, indent=1).encode()))
    print(json.dumps({'cases': rep['cases'], 'steps': rep['steps'], 'behavior_mismatch': len(rep['behavior_mismatch_steps']),
                      'log_or_cu_mismatch': len(rep['log_or_cu_mismatch_steps'])}))


if __name__ == '__main__':
    main()
