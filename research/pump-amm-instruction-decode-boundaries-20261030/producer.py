#!/usr/bin/env python3
"""PumpSwap (pump_amm) instruction dispatch, Borsh argument decoding and first-account checks.

Builds a plan of malformed / minimal instructions for all 38 pump_amm IDL
instructions plus the Anchor dispatcher, runs every step on the original and the
rebuilt image in LiteSVM (one fresh VM per step, only the pump_amm image loaded),
and writes deterministic receipts and a report under --out/runtime/.

A third run per step uses a control image: the original with every reference to a
'programs/pump-amm/src/*.rs' string moved past the 18-byte 'programs/pump-amm/'
prefix (length immediate lowered by 18). It tests whether any CU/log difference is
fully explained by the AnchorError file-path string.

Usage: producer.py --root <repo> --images '{"original": P, "candidate": P}' --out <dir>
"""
import argparse, gzip, hashlib, io, json, pathlib, re, struct, sys

from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PAYER = Keypair.from_seed(bytes([229]) * 32)
PAYER_LAMPORTS = 10 ** 12
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
IDL_IX_TAG = bytes.fromhex('40f4bc78a7e9690a')
BEHAVIOR = ['tx_sha256', 'error', 'return_data', 'events', 'inner_instructions', 'payer_lamports', 'accounts']
PREFIX = b'programs/pump-amm/'


def unfunded(i):
    return Pubkey.from_bytes(hashlib.sha256(b'pump-amm-decode-unfunded-%d' % i).digest())


# ---------------------------------------------------------------- arguments
def scalar(t):
    return {'u8': b'\x01', 'u16': b'\x02\x00', 'u64': struct.pack('<Q', 3), 'i64': struct.pack('<q', 4),
            'u128': (5).to_bytes(16, 'little'), 'bool': b'\x01', 'pubkey': bytes([7]) * 32}.get(t)


def encode(t, types):
    """Return (bytes, parts); parts lists mutable spans: (kind, offset)."""
    if isinstance(t, str):
        return scalar(t), ([('bool', 0)] if t == 'bool' else [])
    if 'option' in t:
        body, parts = encode(t['option'], types)
        return b'\x01' + body, [('opt', 0)] + [(k, o + 1) for k, o in parts]
    if 'array' in t:
        et, n = t['array']
        body, parts = encode(et, types)
        return body * n, []
    if 'defined' in t:
        name = t['defined']['name']
        d = types[name]['type']
        out = b''
        for f in d['fields']:
            b, _ = encode(f if isinstance(f, str) else f['type'], types)
            out += b
        if name == 'OptionBool':
            return out, [('optbool', 0)]
        if name == 'OptionU64':
            return out, [('optu64', 0)]
        return out, []
    raise ValueError(t)


def args_layout(ix, types):
    out, spans = b'', []
    for a in ix['args']:
        b, parts = encode(a['type'], types)
        spans += [(a['name'], k, o + len(out), len(b)) for k, o in parts]
        out += b
    return out, spans


# ---------------------------------------------------------------- accounts
def resolve(acc, program):
    if acc.get('signer'):
        return PAYER.pubkey()
    if 'address' in acc:
        return Pubkey.from_string(acc['address'])
    if acc['name'] == 'program':
        return program
    pda = acc.get('pda')
    if pda and all(s['kind'] == 'const' for s in pda['seeds']):
        owner = program
        if 'program' in pda:
            if pda['program']['kind'] != 'const':
                return None
            owner = Pubkey.from_bytes(bytes(pda['program']['value']))
        return Pubkey.find_program_address([bytes(s['value']) for s in pda['seeds']], owner)[0]
    return None


def plan_for(idl):
    program = Pubkey.from_string(idl['address'])
    types = {t['name']: t for t in idl['types']}
    cases = []
    payer = str(PAYER.pubkey())

    def step(label, data, accs):
        return {'label': label, 'data': data.hex(), 'accounts': accs}

    disc0 = bytes(sorted(idl['instructions'], key=lambda x: x['name'])[0]['discriminator'])
    ev = str(Pubkey.find_program_address([b'__event_authority'], program)[0])
    d = [step('empty-data', b'', []), step('one-byte', disc0[:1], []), step('four-bytes', disc0[:4], []),
         step('seven-bytes', disc0[:7], []), step('zero-disc', bytes(8), []), step('ff-disc', b'\xff' * 8, []),
         step('zero-disc-with-account', bytes(8), [[str(unfunded(0)), False, True]]),
         step('event-cpi-tag-no-accounts', EVENT_CPI_TAG, []),
         step('event-cpi-tag-unsigned-event-authority', EVENT_CPI_TAG, [[ev, False, False]]),
         step('event-cpi-tag-payer-signer', EVENT_CPI_TAG, [[payer, True, True]]),
         step('event-cpi-tag-seven-bytes', EVENT_CPI_TAG[:7], []),
         dict(step('event-cpi-tag-signed-event-authority', EVENT_CPI_TAG, [[ev, True, False]]), sigverify_off=True),
         dict(step('event-cpi-tag-signed-event-authority-with-payload', EVENT_CPI_TAG + bytes(range(32)), [[ev, True, False]]), sigverify_off=True),
         dict(step('event-cpi-tag-signed-event-authority-extra-account', EVENT_CPI_TAG, [[ev, True, False], [str(unfunded(1)), False, True]]), sigverify_off=True),
         step('idl-tag-no-accounts', IDL_IX_TAG, []),
         step('idl-tag-create-payload', IDL_IX_TAG + b'\x00' + struct.pack('<Q', 64), [[payer, True, True]]),
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
            if kind in ('optbool', 'optu64'):
                s.append(step('%s-omitted' % name, disc + args[:off], []))
                if full > 1:
                    s.append(step('%s-half-present' % name, disc + args[:off + full // 2], []))
        valid = disc + args
        if n:
            s.append(step('one-account-short', valid, [[str(unfunded(i)), False, True] for i in range(n - 1)]))
        s.append(step('unfunded-accounts', valid, [[str(unfunded(i)), False, True] for i in range(max(n, 1))]))
        s.append(step('payer-every-slot', valid, [[payer, True, True] for _ in range(max(n, 1))]))
        if n:
            res, i = [], 0
            for acc in ix['accounts']:
                k = resolve(acc, program)
                if k is None:
                    k = unfunded(100 + i); i += 1
                res.append([str(k), k == PAYER.pubkey(), bool(acc.get('writable')) or k == PAYER.pubkey()])
            s.append(step('idl-resolved', valid, res))
            s.append(step('idl-resolved-extra-account', valid, res + [[str(unfunded(99)), False, False]]))
        cases.append({'name': ix['name'], 'instruction': ix['name'], 'steps': s})
    return {'program_id': idl['address'], 'payer_seed': 229, 'payer_lamports': PAYER_LAMPORTS, 'cases': cases}


# ---------------------------------------------------------------- control image
def elf_sections(blob):
    shoff, = struct.unpack_from('<Q', blob, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    hs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    st = hs[shstrndx]; names = blob[st[4]:st[4] + st[5]]
    return {names[h[0]:names.index(b'\0', h[0])].decode(): (h[4], h[5]) for h in hs if h[0]}


def strip_prefix(blob):
    """The original with every lddw of a 'programs/pump-amm/src/*.rs' string moved 18 bytes
    later (past the prefix) and the matching length immediate lowered by 18."""
    b = bytearray(blob)
    secs = elf_sections(bytes(b))
    ro_off, ro_len = secs['.rodata']; tx_off, tx_len = secs['.text']
    starts = {}
    for m in re.finditer(re.escape(PREFIX) + rb'src/[A-Za-z0-9_/]+\.rs', bytes(b[ro_off:ro_off + ro_len])):
        starts[ro_off + m.start()] = len(m.group(0))  # sh_addr == sh_offset for .rodata here
    sites = 0
    for i in range(tx_off, tx_off + tx_len - 16, 8):
        if b[i] != 0x18:
            continue
        imm = struct.unpack_from('<I', b, i + 4)[0] | (struct.unpack_from('<I', b, i + 12)[0] << 32)
        if imm not in starts:
            continue
        n = starts[imm]
        for j in range(i + 16, i + 16 + 8 * 12, 8):
            if b[j] in (0x7a, 0x62, 0xb7, 0xb4) and struct.unpack_from('<i', b, j + 4)[0] == n:
                struct.pack_into('<i', b, j + 4, n - len(PREFIX))
                new = imm + len(PREFIX)
                struct.pack_into('<I', b, i + 4, new & 0xffffffff); struct.pack_into('<I', b, i + 12, new >> 32)
                sites += 1
                break
    return bytes(b), sites


# ---------------------------------------------------------------- execution
def run_step(binary, program_id, st):
    program = Pubkey.from_string(program_id)
    vm = LiteSVM().with_log_bytes_limit(None).with_transaction_history(0)
    if st.get('sigverify_off'):
        vm = vm.with_sigverify(False)
    if isinstance(binary, bytes):
        vm.add_program(program, binary)
    else:
        vm.add_program_from_file(program, binary)
    vm.airdrop(PAYER.pubkey(), PAYER_LAMPORTS)
    accs = [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in st['accounts']]
    ix = Instruction(program, bytes.fromhex(st['data']), accs)
    bh = vm.latest_blockhash()
    if st.get('sigverify_off'):
        # Non-payer signers (the event-authority PDA) cannot sign; signature checks are off.
        tx = Transaction.new_unsigned(Message.new_with_blockhash([ix], PAYER.pubkey(), bh))
        tx.partial_sign([PAYER], bh)
    else:
        tx = Transaction.new_signed_with_payer([ix], PAYER.pubkey(), [PAYER], bh)
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


def run_plan(plan, images, control):
    out = []
    for case in plan['cases']:
        for st in case['steps']:
            rec = {'case': case['name'], 'label': st['label']}
            for side in ('original', 'candidate'):
                rec[side] = run_step(images[side], plan['program_id'], st)
            s = run_step(control, plan['program_id'], st)
            c = rec['candidate']
            rec['control'] = {'cu': s['cu'], 'same_logs_as_candidate': s['logs'] == c['logs'],
                              'same_behavior_as_candidate': all(s[k] == c[k] for k in BEHAVIOR)}
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
    m = re.search(r'InstructionError\(\s*\d+,\s*(\w+)', err)
    return m.group(1) if m else err


def site(line):
    return re.sub(r'AnchorError thrown in [^ ]+:\d+\.', 'AnchorError thrown in <site>.', line)


def anchor_site(logs):
    for l in logs:
        m = re.search(r'AnchorError thrown in ([^ ]+):(\d+)\.', l)
        if m:
            return '%s:%s' % m.groups()
    return None


VARIANTS = ('-bool-tag-2', '-opt-tag-2', '-optbool-tag-2', '-none-with-stale-body', '-none', '-omitted', '-half-present')


def report(plan, receipts, shas, control_sites):
    behavior_diff, logcu_diff, site_rows = [], [], []
    hist, per_label, per_ix, blamed = {}, {}, {}, {}
    ctrl_cu = ctrl_logs = ctrl_beh = 0
    for r in receipts:
        o, c = r['original'], r['candidate']
        if any(o[k] != c[k] for k in BEHAVIOR):
            behavior_diff.append([r['case'], r['label'], [k for k in BEHAVIOR if o[k] != c[k]]])
        d = c['cu'] - o['cu']
        hist[str(d)] = hist.get(str(d), 0) + 1
        if o['logs'] != c['logs'] or d:
            same_norm = [site(x) for x in o['logs'] if 'compute units' not in x] == [site(x) for x in c['logs'] if 'compute units' not in x]
            logcu_diff.append([r['case'], r['label'], d, same_norm, anchor_site(o['logs']), anchor_site(c['logs'])])
            for a, b in zip(o['logs'], c['logs']):
                if a != b:
                    site_rows.append([r['case'], r['label'], a, b]); break
        ctrl_cu += r['control']['cu'] == c['cu']
        ctrl_logs += r['control']['same_logs_as_candidate']
        ctrl_beh += r['control']['same_behavior_as_candidate']
        per_ix.setdefault(r['case'], {})[r['label']] = code(o['error'])
        for line in o['logs']:
            m = re.search(r'caused by account: (\w+)\. Error Code: (\w+)', line)
            if m:
                blamed.setdefault(r['case'], {})[r['label']] = '%s:%s' % (m.group(1), m.group(2))
        if r['case'] == 'dispatcher':
            continue
        lab = r['label']
        for pre in VARIANTS:
            if lab.endswith(pre):
                lab = '*' + pre; break
        per_label.setdefault(lab, {}).setdefault(code(o['error']), 0)
        per_label[lab][code(o['error'])] += 1
    by_delta = {}
    for row in logcu_diff:
        by_delta.setdefault(str(row[2]), []).append('%s/%s' % (row[0], row[1]))
    return {
        'program': 'pump_amm', 'program_id': plan['program_id'],
        'original_sha256': shas['original'], 'candidate_sha256': shas['candidate'],
        'cases': len(plan['cases']), 'steps': len(receipts), 'receipts': 2 * len(receipts),
        'behavior_compared_fields': BEHAVIOR,
        'behavior_mismatch_steps': behavior_diff,
        'cu_delta_histogram_candidate_minus_original': dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
        'log_or_cu_mismatch_steps': logcu_diff,
        'log_or_cu_mismatch_by_delta': by_delta,
        'first_differing_log_line': site_rows,
        'control': {'sites_patched': control_sites, 'cu_equal_to_candidate': ctrl_cu,
                    'logs_equal_to_candidate': ctrl_logs, 'behavior_equal_to_candidate': ctrl_beh},
        'outcome_by_variant': {k: dict(sorted(v.items())) for k, v in sorted(per_label.items())},
        'outcome_by_instruction': per_ix,
        'blamed_account_by_instruction': blamed,
    }


def gz(b):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0, filename='') as f:
        f.write(b)
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
    idl = json.loads((a.root / 'evidence/upstream/pump_amm.json').read_text())
    plan = plan_for(idl)
    control, sites = strip_prefix(pathlib.Path(images['original']).read_bytes())
    receipts = run_plan(plan, images, control)
    shas = {k: sha(images[k]) for k in ('original', 'candidate')}
    rep = report(plan, receipts, shas, sites)
    rt = a.out / 'runtime'
    rt.mkdir(parents=True, exist_ok=True)
    (rt / 'plan.json.gz').write_bytes(gz(dumps(plan).encode()))
    (rt / 'receipts.jsonl.gz').write_bytes(gz(''.join(dumps(r) + '\n' for r in receipts).encode()))
    (rt / 'report.json.gz').write_bytes(gz(json.dumps(rep, sort_keys=True, indent=1).encode()))
    print(json.dumps({'cases': rep['cases'], 'steps': rep['steps'], 'behavior_mismatch': len(rep['behavior_mismatch_steps']),
                      'log_or_cu_mismatch': len(rep['log_or_cu_mismatch_steps']),
                      'cu_hist': rep['cu_delta_histogram_candidate_minus_original'], 'control': rep['control']}))


if __name__ == '__main__':
    main()
