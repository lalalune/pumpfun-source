#!/usr/bin/env python3
"""Pump Main `create_v2`, original vs rebuild, with synthetic state only.

The repository's create harnesses (scripts/pump_create_v2_differential.py,
pump_create_quote_differential.py, pump_create_mayhem_differential.py,
pump_create_control_differential.py, pump_create_nested_fixture.py) all start
from research/imported-lab/analysis/pump_fun/config-snapshot.json. That file is
not in the tree, so none of them runs today. This packet builds the Global
account from the IDL layout (1,088 bytes) instead and measures `create_v2`:
argument limits (byte lengths), option flags (cashback / holder reward / mayhem
/ creator fee bps), Global gates and numeric fields, the quote-mint
remaining-account path (SOL, whitelisted SPL / Token-2022, rejected mints), the
Anchor `init` constraints on pre-funded or pre-existing accounts and account
substitutions.

Token-2022, the ATA program and the system program are LiteSVM's built-ins
(identical for both images). The Mayhem program is not loaded: no case needs
it except one, which records that the handler reaches the Mayhem CPI. Pump runs
under the upgradeable loader (mainnet layout). Keys come from fixed seeds, the
clock is fixed, one fresh VM per case, no network. The full initial account set
of every case is written to runtime/plan.json.gz, so verify.py replays without
the repository.

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
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
MAYHEM = Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
UNSUPPORTED_QUOTE = Pubkey.from_string('9pan9bMn5HatX4EJdBwg9VgCa7Uz5HL8N1m5D3NdXejP')
SYSTEM = Pubkey.default()
USER_SEED, MINT_SEED = 211, 212
USER = Keypair.from_seed(bytes([USER_SEED]) * 32)
MINT = Keypair.from_seed(bytes([MINT_SEED]) * 32)
CREATOR = Pubkey(bytes([60]) * 32)
QUOTE = Pubkey(bytes([70]) * 32)        # synthetic quote mint (owner set per case)
STRANGER = Pubkey(bytes([200]) * 32)
BASE_TS = 1_800_000_000
IX_CREATE_V2 = bytes([214, 144, 76, 236, 95, 139, 49, 180])
DISC = {'Global': bytes([167, 232, 232, 177, 200, 108, 114, 127]),
        'BondingCurve': bytes([23, 183, 248, 55, 96, 216, 172, 96]),
        'QuoteControl': bytes([56, 244, 35, 238, 193, 213, 162, 201])}
CREATE_EVENT = bytes([27, 114, 169, 77, 222, 235, 99, 118])

pda = lambda seeds, program=PROGRAM: Pubkey.find_program_address(seeds, program)[0]
GLOBAL = pda([b'global'])
EVENT_AUTHORITY = pda([b'__event_authority'])
MINT_AUTHORITY = pda([b'mint-authority'])
CURVE = pda([b'bonding-curve', bytes(MINT.pubkey())])


def ata(owner, mint, program=TOKEN22):
    return pda([bytes(owner), bytes(program), bytes(mint)], ATA_PROGRAM)


G = {'vtr': 1_073_000_000_000_000, 'vsr': 30_000_000_000, 'rtr': 793_100_000_000_000,
     'supply': 1_000_000_000_000_000, 'ivqr': 4_000_000_000}


def global_data(**kw):
    g = dict(G, initialized=1, create_v2=1, mayhem=0, whitelist=QUOTE, configurable=0, max_bps=0,
             holder=0, depth=0)
    g.update(kw)
    d = bytearray(1088)
    d[:8] = DISC['Global']
    d[8] = g['initialized']
    d[9:41] = bytes(Pubkey(bytes([91]) * 32))
    d[41:73] = bytes(Pubkey(bytes([90]) * 32))
    struct.pack_into('<QQQQQ', d, 73, g['vtr'], g['vsr'], g['rtr'], g['supply'], 95)
    struct.pack_into('<Q', d, 154, 30)
    d[450] = g['create_v2']
    d[515] = g['mayhem']
    struct.pack_into('<Q', d, 1005, g['ivqr'])
    d[1013:1045] = bytes(g['whitelist'])
    d[1045] = g['configurable']
    struct.pack_into('<Q', d, 1046, g['max_bps'])
    d[1086] = g['holder']
    d[1087] = g['depth']
    return bytes(d)


def spl_mint(supply=10**15, decimals=6):
    return struct.pack('<I32sQBBI32s', 1, bytes(USER.pubkey()), supply, decimals, 1, 0, bytes(32))


def t22_mint(ext=None):
    """Token-2022 mint; ext = list of (type, value bytes) TLV entries (base padded to 165, account type 1)."""
    base = spl_mint()
    if not ext:
        return base
    tlv = b''.join(struct.pack('<HH', t, len(v)) + v for t, v in ext)
    return base + bytes(165 - len(base)) + bytes([1]) + tlv


QUOTE_CONTROL = pda([b'quote-control'])


def quote_control_data(entries, count=None):
    """QuoteControl: disc | admin | reserves_admin | reserved[32] | u32 count | (mint, u64 reserves)*."""
    d = DISC['QuoteControl'] + bytes(Pubkey(bytes([94]) * 32)) + bytes(Pubkey(bytes([95]) * 32)) + bytes(32)
    d += struct.pack('<I', len(entries) if count is None else count)
    return d + b''.join(bytes(m) + struct.pack('<Q', r) for m, r in entries)


TRANSFER_FEE = (1, bytes(32) + bytes(32) + struct.pack('<Q', 0) + (struct.pack('<QQH', 0, 0, 0) * 2))
NON_TRANSFERABLE = (9, b'')
PERMANENT_DELEGATE = (12, bytes(STRANGER))
METADATA_POINTER = (18, bytes(64))

IDL_ACCOUNTS = ['mint', 'mint_authority', 'bonding_curve', 'associated_bonding_curve', 'global', 'user',
                'system_program', 'token_program', 'associated_token_program', 'mayhem_program_id',
                'global_params', 'sol_vault', 'mayhem_state', 'mayhem_token_vault', 'event_authority', 'program']
WRITABLE = {'mint', 'bonding_curve', 'associated_bonding_curve', 'user', 'mayhem_program_id', 'sol_vault',
            'mayhem_state', 'mayhem_token_vault'}
SIGNERS = {'mint', 'user'}


def accounts_default():
    return {'mint': MINT.pubkey(), 'mint_authority': MINT_AUTHORITY, 'bonding_curve': CURVE,
            'associated_bonding_curve': ata(CURVE, MINT.pubkey()), 'global': GLOBAL, 'user': USER.pubkey(),
            'system_program': SYSTEM, 'token_program': TOKEN22, 'associated_token_program': ATA_PROGRAM,
            'mayhem_program_id': MAYHEM, 'global_params': pda([b'global-params'], MAYHEM),
            'sol_vault': pda([b'sol-vault'], MAYHEM),
            'mayhem_state': pda([b'mayhem-state', bytes(MINT.pubkey())], MAYHEM),
            'mayhem_token_vault': ata(pda([b'sol-vault'], MAYHEM), MINT.pubkey()),
            'event_authority': EVENT_AUTHORITY, 'program': PROGRAM}


def borsh_str(s):
    b = s.encode() if isinstance(s, str) else s
    return struct.pack('<I', len(b)) + b


def args_data(name='Synthetic Coin', symbol='SYNTH', uri='https://example.invalid/m.json', creator=CREATOR,
              mayhem=0, cashback=0, creator_fee_bps=0, holder=0, cut=0):
    d = IX_CREATE_V2 + borsh_str(name) + borsh_str(symbol) + borsh_str(uri) + bytes(creator)
    d += bytes([mayhem, cashback]) + struct.pack('<Q', creator_fee_bps) + bytes([holder])
    return d[:len(d) - cut]


def case(name, note, data=None, glob=None, over=None, remaining=(), extra=None, ro=()):
    accts = accounts_default()
    accts.update(over or {})
    metas = [[str(accts[n]), n in SIGNERS, n in WRITABLE and n not in ro] for n in IDL_ACCOUNTS]
    metas += [[str(k), False, w] for k, w in remaining]
    state = {GLOBAL: (10**9, PROGRAM, global_data(**(glob or {}))),
             USER.pubkey(): (10**12, SYSTEM, b'')}
    for k, v in (extra or {}).items():
        state[k] = v
    return {'case': name, 'note': note, 'data_hex': (data or args_data()).hex(), 'metas': metas,
            'signer_seeds': [USER_SEED, MINT_SEED],
            'accounts': [[str(k), lam, str(owner), d.hex()] for k, (lam, owner, d) in
                         sorted(state.items(), key=lambda kv: str(kv[0]))]}


def ctl_key(i):
    return Pubkey(struct.pack('<H', i + 1) + bytes([77]) * 30)


def plan():
    """create_v2 with a non-whitelisted SPL quote resolved through the quote-control list
    (`control_entry`, programs/pump/src/quote_control/state.rs: chunks_exact(40).find over `count`
    raw entries). Only the list length N and the position j of the quote mint vary."""
    out = []
    q_spl = {QUOTE: (10**9, TOKEN, spl_mint())}
    q_ata = ata(CURVE, QUOTE, TOKEN)
    qc = QUOTE_CONTROL
    rem = [(QUOTE, False), (q_ata, True), (TOKEN, False), (qc, False)]
    nw = {'whitelist': STRANGER}

    def add(label, n, j, note):
        entries = [(ctl_key(i), 1_000 + i) for i in range(n)]
        if j is not None:
            entries[j] = (QUOTE, 5_000_000_000)
        c = case(label, note, glob=nw, remaining=rem, extra={**q_spl, qc: (10**9, PROGRAM, quote_control_data(entries))})
        c['model'] = {'n': n, 'pos': j if j is not None else 'absent'}
        out.append(c)

    for j in (0, 1, 2, 4, 8, 16, 32, 64, 128, 255):
        add(f'ctl/n256/pos-{j}', 256, j, f'quote is entry {j} of 256')
    for n in (1, 2, 4, 8, 16, 32, 64, 128):
        add(f'ctl/n{n}/pos-0', n, 0, f'quote is the first of {n} entries')
        add(f'ctl/n{n}/pos-last', n, n - 1, f'quote is the last of {n} entries')
    for n in (1, 8, 64, 256):
        add(f'ctl/n{n}/absent', n, None, f'quote not among {n} entries')
    add('ctl/n1000/pos-999', 1000, 999, 'count 1000 (above MAX_QUOTE_CONTROL_MINTS 256): quote is the last entry')
    add('ctl/n1000/pos-0', 1000, 0, 'count 1000: quote is the first entry')
    return out


# ---- execution (verify.py imports this file; nothing below reads the repository) ----

# Two Token-2022 configurations, both with Pump under the upgradeable loader:
#  builtin-token-2022: LiteSVM's bundled Token-2022 (needs nothing outside this packet);
#  mainnet-token-2022: evidence/dependencies/spl_token_2022/deployed.so from the repository,
#                      loaded over the built-in (sha256 pinned in the report).
LOADERS = ('builtin-token-2022', 'mainnet-token-2022')
TOKEN22_DEPENDENCY = 'evidence/dependencies/spl_token_2022/deployed.so'
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')


def load_vm(image, token22=None):
    vm = LiteSVM().with_transaction_history(0).with_sigverify(True)
    elf = Path(image).read_bytes()
    programdata = Pubkey.find_program_address([bytes(PROGRAM)], UPGRADEABLE)[0]
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + elf, UPGRADEABLE, False))
    vm.set_account(PROGRAM, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    if token22 is not None:
        vm.add_program(TOKEN22, Path(token22).read_bytes())
    return vm


def run_case(vm, index, c):
    vm.expire_blockhash()
    vm.set_clock(Clock(1000 + index, 0, 0, 0, BASE_TS + index))
    keys = []
    for k, lam, owner, data in c['accounts']:
        key = Pubkey.from_string(k)
        keys.append(key)
        vm.set_account(key, Account(lam, bytes.fromhex(data), Pubkey.from_string(owner)))
    metas = [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in c['metas']]
    ixs = [set_compute_unit_limit(1_400_000), Instruction(PROGRAM, bytes.fromhex(c['data_hex']), metas)]
    signers = [Keypair.from_seed(bytes([s]) * 32) for s in c['signer_seeds']]
    tx = Transaction.new_signed_with_payer(ixs, signers[0].pubkey(), signers, vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    logs = list(meta.logs())
    ret = meta.return_data()
    after = {}
    for key in sorted(set(keys) | {m.pubkey for m in metas}, key=str):
        if key == PROGRAM:
            continue
        a = vm.get_account(key)
        if a is not None and not a.executable and (a.lamports or a.data):
            after[str(key)] = [a.lamports, str(a.owner), bytes(a.data).hex()]
    return {'case': c['case'], 'transaction_base64': base64.b64encode(bytes(tx)).decode(),
            'error': str(result.err()) if failed else None,
            'return_data_hex': bytes(ret.data).hex() if ret is not None else '',
            'events': [l[14:] for l in logs if l.startswith('Program data: ')],
            'inner_instructions': json.loads(meta.to_json())['inner_instructions'],
            'accounts_after': after, 'compute_units': meta.compute_units_consumed(), 'logs': logs}


def run_plan(image, loader, cases, token22=None):
    assert loader in LOADERS and (token22 is not None) == (loader == 'mainnet-token-2022')
    return [run_case(load_vm(image, token22), i, c) for i, c in enumerate(cases)]


BEHAVIOR = ('transaction_base64', 'error', 'return_data_hex', 'events', 'inner_instructions', 'accounts_after')
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


def custom_code(error):
    if error and 'Custom(' in error:
        return int(error.split('Custom(', 1)[1].split(')', 1)[0])
    return error


def anchor_name(logs):
    for line in logs:
        if 'Error Code: ' in line:
            return line.split('Error Code: ', 1)[1].split('.', 1)[0]
    return None


def curve_after(receipt):
    a = receipt['accounts_after'].get(str(CURVE))
    if a is None or a[1] != str(PROGRAM) or len(a[2]) != 332:
        return None
    d = bytes.fromhex(a[2])
    vtr, vqr, rtr, rqr, tts = struct.unpack_from('<QQQQQ', d, 8)
    return {'lamports': a[0], 'virtual_token_reserves': vtr, 'virtual_quote_reserves': vqr,
            'real_token_reserves': rtr, 'real_quote_reserves': rqr, 'token_total_supply': tts,
            'complete': d[48], 'creator': str(Pubkey(d[49:81])), 'is_mayhem_mode': d[81], 'is_cashback_coin': d[82],
            'quote_mint': str(Pubkey(d[83:115])), 'creator_fee_bps': struct.unpack_from('<Q', d, 115)[0],
            'is_holder_reward': d[124], 'depth': d[141],
            'initial_virtual_quote_reserves': struct.unpack_from('<Q', d, 142)[0]}


def created_accounts(c, receipt):
    before = {k for k, _, _, _ in c['accounts']}
    return sorted([LABELS.get(k, k), v[1], len(v[2]) // 2, v[0]] for k, v in receipt['accounts_after'].items()
                  if k not in before)


LABELS = {str(MINT.pubkey()): 'mint', str(CURVE): 'bonding_curve',
          str(ata(CURVE, MINT.pubkey())): 'associated_bonding_curve', str(ata(CURVE, QUOTE, TOKEN)): 'quote_ata_spl',
          str(ata(CURVE, QUOTE, TOKEN22)): 'quote_ata_t22', str(USER.pubkey()): 'user'}


def summarize(cases, original, candidate):
    rows = []
    for c, ro, rc in zip(cases, original, candidate):
        rows.append({'case': c['case'], 'note': c['note'], 'model': c['model'],
                     'error_original': ro['error'], 'error_candidate': rc['error'],
                     'custom_code': custom_code(ro['error']),
                     'error_name': {'original': anchor_name(ro['logs']), 'candidate': anchor_name(rc['logs'])},
                     'compute_units': {'original': ro['compute_units'], 'candidate': rc['compute_units'],
                                       'original_minus_candidate': ro['compute_units'] - rc['compute_units']},
                     'logs_equal': ro['logs'] == rc['logs'],
                     'differing_log_lines': classify_logs(ro['logs'], rc['logs']),
                     'behavior_differences': [k for k in BEHAVIOR if ro[k] != rc[k]],
                     'create_events': sum(1 for e in ro['events'] if base64.b64decode(e)[:8] == CREATE_EVENT),
                     'curve_after': curve_after(ro), 'created_accounts': created_accounts(c, ro)})
    stops, deltas, kinds = {}, {}, {}
    for r in rows:
        stop = 'success' if r['error_original'] is None else (r['error_name']['original'] or str(r['custom_code']))
        stops[stop] = stops.get(stop, 0) + 1
        dk = f"{r['compute_units']['original_minus_candidate']}:{stop}"
        deltas[dk] = deltas.get(dk, 0) + 1
        kind = ','.join(sorted({d['kind'] for d in r['differing_log_lines']})) or 'none'
        kinds[kind] = kinds.get(kind, 0) + 1
    cu_by_position = [[r['model']['n'], r['model']['pos'],
                       'success' if r['error_original'] is None else (r['error_name']['original'] or str(r['custom_code'])),
                       r['compute_units']['original'], r['compute_units']['candidate']] for r in rows]
    return {'case_count': len(rows),
            'cu_by_position': cu_by_position,
            'behavior_mismatches': [r['case'] for r in rows if r['behavior_differences']],
            'compute_units_equal_cases': sum(r['compute_units']['original_minus_candidate'] == 0 for r in rows),
            'logs_equal_cases': sum(r['logs_equal'] for r in rows),
            'cases_by_stop': dict(sorted(stops.items())),
            'compute_unit_delta_by_stop': dict(sorted(deltas.items())),
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
    idl = json.loads((args.root / 'evidence/upstream/pump.json').read_text())
    assert idl['address'] == str(PROGRAM)
    ix = next(i for i in idl['instructions'] if i['name'] == 'create_v2')
    assert bytes(ix['discriminator']) == IX_CREATE_V2
    assert [a['name'] for a in ix['accounts']] == IDL_ACCOUNTS
    assert {a['name'] for a in ix['accounts'] if a.get('writable')} == WRITABLE
    assert {a['name'] for a in ix['accounts'] if a.get('signer')} == SIGNERS
    assert bytes(next(e for e in idl['events'] if e['name'] == 'CreateEvent')['discriminator']) == CREATE_EVENT
    for a in idl['accounts']:
        if a['name'] in DISC:
            assert bytes(a['discriminator']) == DISC[a['name']]
    cases = plan()
    blobs = {n: Path(images[n]).read_bytes() for n in ('original', 'candidate')}
    runtime = args.out / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*'):
        old.unlink()
    write_gz(runtime / 'plan.json.gz', json.dumps(cases, sort_keys=True, indent=0) + '\n')
    token22 = args.root / TOKEN22_DEPENDENCY
    report = {'scope': 'Pump Main create_v2 (Token-2022 mint with metadata), original vs rebuild under the '
                       'upgradeable loader; synthetic Global from the IDL layout; LiteSVM built-in ATA; Token-2022 '
                       'either LiteSVM built-in or the repository mainnet dependency; Mayhem program not loaded; '
                       'no network.',
              'images': {n: hashlib.sha256(b).hexdigest() for n, b in blobs.items()},
              'image_bytes': {n: len(b) for n, b in blobs.items()},
              'token_2022_dependency': {'path': TOKEN22_DEPENDENCY,
                                        'sha256': hashlib.sha256(token22.read_bytes()).hexdigest()},
              'behavior_fields': list(BEHAVIOR), 'loaders': {}, 'receipts': {}}
    for loader in LOADERS:
        dep = token22 if loader == 'mainnet-token-2022' else None
        original = run_plan(images['original'], loader, cases, dep)
        candidate = run_plan(images['candidate'], loader, cases, dep)
        lines = []
        for ro, rc in zip(original, candidate):
            lines += [json.dumps({'loader': loader, 'image': 'original', **ro}, sort_keys=True, separators=(',', ':')),
                      json.dumps({'loader': loader, 'image': 'candidate', **rc}, sort_keys=True, separators=(',', ':'))]
        name = f'receipts-{loader}.jsonl.gz'
        write_gz(runtime / name, '\n'.join(lines) + '\n')
        report['receipts'][name] = {'count': len(lines),
                                    'sha256': hashlib.sha256((runtime / name).read_bytes()).hexdigest()}
        report['loaders'][loader] = summarize(cases, original, candidate)
    report['idl_sha256'] = hashlib.sha256((args.root / 'evidence/upstream/pump.json').read_bytes()).hexdigest()
    write_gz(runtime / 'report.json.gz', json.dumps(report, sort_keys=True, indent=1) + '\n')
    for loader, s in report['loaders'].items():
        print(loader, json.dumps({k: s[k] for k in ('case_count', 'behavior_mismatches', 'compute_units_equal_cases',
                                                    'logs_equal_cases', 'cases_by_stop', 'compute_unit_delta_by_stop',
                                                    'log_difference_kinds')}, indent=1))


if __name__ == '__main__':
    main()
