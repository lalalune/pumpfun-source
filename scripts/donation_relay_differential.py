#!/usr/bin/env python3
"""Donation-relay original-vs-candidate differential oracle (LiteSVM).

Loads the captured original relay binary and a rebuilt candidate into two
independent LiteSVM instances, seeds identical synthetic (locally-owned) fixture
state, submits the SAME signed transaction to both, and compares error, logs,
inner instructions, return data and full before/after account state. An
independent visible-effect check prevents two no-op implementations from both
"passing". No historical transaction is replayed or re-signed and no synthetic
signer is injected; every fixture key is a locally generated keypair.

The original binary is the ORACLE: it is loaded read-only from evidence and its
SHA-256 is asserted against the capture manifest. The candidate is a build
input only.

Usage:
  python3 scripts/donation_relay_differential.py \
      --candidate programs/donation-relay/target/deploy/donation_relay_source_proposal.so \
      --group ordinary --output <out.json>

Groups:
  ordinary            5 donation paths + 7 reserved-IDL ops (expected success)
  business_rejection  3 relay business-logic rejections (expected Custom errors)

Requires solders>=0.26 (bundled LiteSVM). Covers only instructions for which a
valid transaction can be built with locally-owned state (donations, reserved IDL
ops, and donation rejections). The swap/distribute family needs an external
Jupiter-style CPI target and is out of scope for this oracle.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse, base64, hashlib, json, re
from pathlib import Path
from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.rent import Rent
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT / 'repro/donation-relay/local-validation-proposal'
ORIGINAL = ROOT / 'evidence/dependencies/donation_relay/deployed.so'
ORIGINAL_SHA = '367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563'
SPL_TOKEN = VALID / 'artifacts/spl_token.so'
ASSOCIATED = VALID / 'artifacts/associated_token.so'
IDL = VALID / 'inputs/idl.json'
AMM_FIXTURE = VALID / 'inputs/amm-v2-trade-fixture.json'

RELAY = Pubkey.from_string('RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
IDL_SELECTOR = bytes([64, 244, 188, 120, 167, 233, 105, 10])
IDL_DISC = bytes([24, 70, 98, 191, 58, 144, 123, 158])
H = lambda b: hashlib.sha256(b).hexdigest()

DONATIONS = ['donate_v1', 'donate_pubkey_config_id_v1', 'donate_pubkey_config_id_with_payer_v1',
             'donate_native_v1', 'donate_native_pubkey_config_id_v1']
IDL_NAMES = ['create', 'create_buffer', 'write', 'set_buffer', 'set_authority', 'close', 'resize']
CASES = (
    [{'name': n, 'kind': 'donation', 'expected_error': None, 'group': 'ordinary'} for n in DONATIONS]
    + [{'name': 'idl_' + n, 'kind': 'idl', 'operation': i, 'expected_error': None, 'group': 'ordinary'}
       for i, n in enumerate(IDL_NAMES)]
    + [
        {'name': 'donation_message_too_long', 'kind': 'donation', 'instruction': 'donate_v1',
         'message': 'm' * 256, 'expected_error': 6009, 'group': 'business_rejection'},
        {'name': 'donation_tip_too_large', 'kind': 'donation', 'instruction': 'donate_v1',
         'tip': 10001, 'expected_error': 6018, 'group': 'business_rejection'},
        {'name': 'donation_insufficient_balance', 'kind': 'donation', 'instruction': 'donate_v1',
         'source_amount': 1, 'expected_error': 'token_insufficient_funds', 'group': 'business_rejection'},
    ]
)


def key(label):
    return Keypair.from_seed(hashlib.sha256(('relay-local-owned-fixture/' + label).encode()).digest())


def pub(label):
    return Pubkey.from_bytes(hashlib.sha256(('relay-local-data/' + label).encode()).digest())


def minimum(n):
    return Rent.default().minimum_balance(n)


def pd(seeds):
    return Pubkey.find_program_address(seeds, RELAY)


def ata(owner, mint):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]


def disc(name):
    return hashlib.sha256(('account:' + name).encode()).digest()[:8]


def account(lamports, data, owner):
    return {'lamports': lamports, 'data_base64': base64.b64encode(data).decode(),
            'owner': str(owner), 'executable': False, 'rent_epoch': 0}


def mint_data():
    b = bytearray(82)
    b[36:44] = (10 ** 12).to_bytes(8, 'little')
    b[44] = 6
    b[45] = 1
    return bytes(b)


def token_data(mint, authority, amount):
    b = bytearray(165)
    b[:32] = bytes(mint)
    b[32:64] = bytes(authority)
    b[64:72] = amount.to_bytes(8, 'little')
    b[108] = 1
    return bytes(b)


def header(authority, body=b'', capacity=128):
    assert len(body) <= capacity
    return IDL_DISC + bytes(authority) + len(body).to_bytes(4, 'little') + body + bytes(capacity - len(body))


def prepare(case):
    fee, owner, other, new = [key(n) for n in ['fee', 'owner', 'separate-payer', 'new-authority']]
    signers = [fee, owner, other, new]
    accounts = {str(k.pubkey()): account(10 ** 10, b'', SYSTEM) for k in signers}

    def put(k, data=b'', program=SYSTEM, lamports=None):
        accounts[str(k)] = account(minimum(len(data)) if lamports is None else lamports, data, program)

    proof = {'test_owned_pubkeys': [str(k.pubkey()) for k in signers], 'synthetic_starting_state': True,
             'canonical_pdas': {}, 'source_capture': None}
    if case['kind'] == 'donation':
        name = case.get('instruction', case['name'])
        native = 'native' in name
        mint = WSOL if native else pub('mint')
        config = bytes(pub('config'))
        epoch, eb = pd([b'epoch_tracker_v1', config, bytes(mint)])
        debouncer, db = pd([b'debouncer_v1', config, bytes(mint)])
        whitelist, wb = pd([b'mint_whitelist_v1'])
        event, eventb = pd([b'__event_authority'])
        source = pd([b'donate_native_wsol_tmp_v1', bytes(owner.pubkey()), bytes(TOKEN)])[0] if native else ata(owner.pubkey(), mint)
        target = ata(debouncer, mint)
        for k in [epoch, debouncer, event, target]:
            put(k, lamports=0)
        put(whitelist, disc('MintWhitelistV1') + bytes([wb]) + bytes(4) + bytes(1024), RELAY)
        if native:
            cap = json.loads(AMM_FIXTURE.read_text())['accounts']['quote_mint']
            put(mint, base64.b64decode(cap['data_base64']), TOKEN, cap['lamports'])
            put(source, lamports=0)
            proof['source_capture'] = {'path': str(AMM_FIXTURE.relative_to(ROOT)), 'sha256': H(AMM_FIXTURE.read_bytes())}
        else:
            put(mint, mint_data(), TOKEN)
            put(source, token_data(mint, owner.pubkey(), case.get('source_amount', 10 ** 9)), TOKEN)
        names = {'epoch_tracker': epoch, 'debouncer': debouncer, 'debouncer_token_account': target, 'mint': mint,
                 'from_token_account': source, 'temp_wsol_token_account': source, 'from': owner.pubkey(),
                 'payer': other.pubkey(), 'mint_whitelist': whitelist, 'associated_token_program': ATA,
                 'token_program': TOKEN, 'system_program': SYSTEM, 'event_authority': event, 'program': RELAY}
        ix = next(i for i in json.loads(IDL.read_text())['instructions'] if i['name'] == name)
        metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
        message = case.get('message', 'ordinary donation').encode()
        data = (bytes(ix['discriminator']) + (1_000_000).to_bytes(8, 'little') + config
                + case.get('tip', 125).to_bytes(2, 'little') + len(message).to_bytes(4, 'little')
                + message + bytes(other.pubkey()))
        proof['canonical_pdas'] = {n: str(names[n]) for n in
                                   ['epoch_tracker', 'debouncer', 'debouncer_token_account', 'mint_whitelist', 'event_authority']}
        proof['source_token_or_temp'] = str(source)
    else:
        op = case['operation']
        authority = owner.pubkey()
        idl = pub('idl-fixture')
        buffer = pub('idl-buffer')
        destination = other.pubkey()
        base, bump = pd([])
        canonical = Pubkey.create_with_seed(base, 'anchor:idl', RELAY)
        proof['canonical_pdas'] = {'base': str(base), 'canonical_idl': str(canonical)}
        if op == 0:
            put(canonical, lamports=0)
            put(base, lamports=0)
            metas = [AccountMeta(authority, True, True), AccountMeta(canonical, False, True),
                     AccountMeta(base, False, False), AccountMeta(SYSTEM, False, False), AccountMeta(RELAY, False, False)]
            payload = (128).to_bytes(8, 'little')
        elif op == 1:
            put(buffer, bytes(172), RELAY)
            metas = [AccountMeta(buffer, False, True), AccountMeta(authority, True, False)]
            payload = b''
        elif op == 3:
            put(buffer, header(authority, b'buffer contents'), RELAY)
            put(idl, header(authority), RELAY)
            metas = [AccountMeta(buffer, False, True), AccountMeta(idl, False, True), AccountMeta(authority, True, False)]
            payload = b''
        elif op == 5:
            put(idl, header(authority, b'closed bytes'), RELAY)
            metas = [AccountMeta(idl, False, True), AccountMeta(authority, True, False), AccountMeta(destination, False, True)]
            payload = b''
        elif op == 6:
            data_init = header(authority, capacity=20)
            put(idl, data_init, RELAY, minimum(len(data_init)))
            metas = [AccountMeta(idl, False, True), AccountMeta(authority, True, True), AccountMeta(SYSTEM, False, False)]
            payload = (128).to_bytes(8, 'little')
        else:
            put(idl, header(authority), RELAY)
            metas = [AccountMeta(idl, False, True), AccountMeta(authority, True, False)]
            body = b'ordinary idl bytes'
            payload = len(body).to_bytes(4, 'little') + body if op == 2 else bytes(new.pubkey())
        data = IDL_SELECTOR + bytes([op]) + payload
    proof['accounts'] = accounts
    proof['instruction_hex'] = data.hex()
    proof['instruction_accounts'] = [{'pubkey': str(a.pubkey), 'signer': a.is_signer, 'writable': a.is_writable} for a in metas]
    return accounts, Instruction(RELAY, data, metas), signers, fee, proof


def vm_for(binary, accounts):
    vm = LiteSVM().with_sigverify(True).with_blockhash_check(True).with_transaction_history(256)
    vm.set_clock(Clock(1000, 0, 0, 0, 1700000000))
    for pid, path in [(RELAY, binary), (TOKEN, SPL_TOKEN), (ATA, ASSOCIATED)]:
        vm.add_program_from_file(pid, path)
    for k, a in accounts.items():
        vm.set_account(Pubkey.from_string(k), Account(a['lamports'], base64.b64decode(a['data_base64']),
                                                       Pubkey.from_string(a['owner']), a['executable'], a['rent_epoch']))
    return vm


def snapshot(vm, keys):
    out = {}
    for k in sorted(keys, key=str):
        a = vm.get_account(k)
        out[str(k)] = None if a is None else {
            'lamports': a.lamports, 'owner': str(a.owner), 'executable': a.executable, 'rent_epoch': a.rent_epoch,
            'data_length': len(a.data), 'data_sha256': H(a.data),
            'data_base64': None if a.executable else base64.b64encode(a.data).decode()}
    return out


def run_one(vm, tx, keys):
    assert all(tx.verify_with_results()) and tx.message.recent_blockhash == vm.latest_blockhash()
    before = snapshot(vm, keys)
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    m = result.meta() if failed else result
    meta = json.loads(m.to_json())
    out = {'signature_verification': tx.verify_with_results(), 'error': str(result.err()) if failed else None,
           'before': before, 'after': snapshot(vm, keys), 'logs': m.logs(),
           'inner_instructions': meta['inner_instructions'], 'return_data': meta['return_data']}
    if failed:
        fee = str(tx.message.account_keys[0])
        assert all(out['before'][k] == out['after'][k] for k in out['before'] if k != fee), 'failed tx mutated non-fee state'
    return out


def comparable(row):
    out = {k: row[k] for k in ['error', 'inner_instructions', 'return_data']}
    out['logs'] = [x for x in row['logs'] if re.fullmatch(r'Program \S+ consumed \d+ of \d+ compute units', x) is None]
    for stage in ['before', 'after']:
        out[stage] = json.loads(json.dumps(row[stage]))
        a = out[stage].get(str(RELAY))
        if a:
            for field in ['data_length', 'data_sha256', 'data_base64']:
                a.pop(field)
            a['lamports'] -= row['before'][str(RELAY)]['lamports']
    return out


def check_effects(case, proof, row):
    out = []

    def demand(ok, label):
        if not ok:
            out.append(label)

    def data(k):
        a = row['after'].get(str(k))
        return b'' if not a else base64.b64decode(a['data_base64'])

    if case['kind'] == 'donation':
        p = proof['canonical_pdas']
        t = data(p['epoch_tracker'])
        d = data(p['debouncer'])
        v = data(p['debouncer_token_account'])
        demand(t[:8] == disc('EpochTrackerV1') and len(t) >= 90 and t[9] == 1 and int.from_bytes(t[74:90], 'little') == 0, 'initialized_epoch_zero')
        demand(d[:8] == disc('DebouncerV1') and len(d) >= 82 and d[9] == 1 and int.from_bytes(d[74:82], 'little') == 1_000_000, 'debouncer_total')
        demand(len(v) >= 165 and int.from_bytes(v[64:72], 'little') == 1_000_000, 'destination_tokens')
        source = proof['source_token_or_temp']
        a = row['after'].get(source)
        if 'native' in case.get('instruction', case['name']):
            demand(a is None or (a['lamports'] == 0 and a['data_length'] == 0), 'native_temp_closed')
        else:
            demand(int.from_bytes(data(source)[64:72], 'little') == 999_000_000, 'source_tokens_debited')
        demand(any(x.startswith('Program data: ') for x in row['logs']), 'event_log')
    else:
        op = case['operation']
        k = proof['instruction_accounts'][0]['pubkey']
        b = data(k)
        if op == 0:
            b = data(proof['canonical_pdas']['canonical_idl'])
            demand(len(b) == 172 and b == header(key('owner').pubkey()), 'created_idl')
        elif op == 1:
            demand(b == header(key('owner').pubkey()), 'initialized_buffer')
        elif op == 2:
            demand(b == header(key('owner').pubkey(), b'ordinary idl bytes'), 'written_idl')
        elif op == 3:
            demand(data(proof['instruction_accounts'][1]['pubkey']) == header(key('owner').pubkey(), b'buffer contents'), 'copied_buffer')
        elif op == 4:
            demand(b == header(key('new-authority').pubkey()), 'updated_authority')
        elif op == 5:
            a = row['after'].get(k)
            demand(a is None or (a['lamports'] == 0 and a['data_length'] == 0), 'closed_idl')
        elif op == 6:
            demand(b == header(key('owner').pubkey(), capacity=84), 'resized_idl')
    return out


def execute(candidate, group, output):
    assert H(ORIGINAL.read_bytes()) == ORIGINAL_SHA, 'original oracle sha mismatch'
    for p in [candidate, SPL_TOKEN, ASSOCIATED, IDL, AMM_FIXTURE]:
        assert Path(p).exists(), f'missing input {p}'
    rows = []
    for case in [c for c in CASES if c['group'] == group]:
        accounts, ix, available, fee, proof = prepare(case)
        a = vm_for(ORIGINAL, accounts)
        b = vm_for(candidate, accounts)
        assert a.latest_blockhash() == b.latest_blockhash()
        required = {m.pubkey for m in ix.accounts if m.is_signer} | {fee.pubkey()}
        signers = [s for s in available if s.pubkey() in required]
        assert {s.pubkey() for s in signers} == required
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), ix], fee.pubkey(), signers, a.latest_blockhash())
        assert all(tx.verify_with_results())
        keys = {Pubkey.from_string(k) for k in accounts} | set(tx.message.account_keys)
        left = run_one(a, tx, keys)
        right = run_one(b, tx, keys)
        x, y = comparable(left), comparable(right)
        mismatches = [k for k in x if x[k] != y[k]]
        if case['expected_error'] is None and left['error'] is not None:
            mismatches.append('original_expected_success')
        if isinstance(case['expected_error'], int) and ('Custom(' + str(case['expected_error']) + ')') not in (left['error'] or '').replace(' ', ''):
            mismatches.append('original_expected_error')
        if case['expected_error'] == 'token_insufficient_funds' and 'Custom(1)' not in (left['error'] or '').replace(' ', ''):
            mismatches.append('original_expected_token_rejection')
        if left['error'] is None and case['expected_error'] is None:
            mismatches.extend('original_effect:' + e for e in check_effects(case, proof, left))
            if right['error'] is None:
                mismatches.extend('candidate_effect:' + e for e in check_effects(case, proof, right))
        rows.append({'case': case, 'original_error': left['error'], 'candidate_error': right['error'],
                     'mismatches': mismatches, 'return_data_match': x['return_data'] == y['return_data'],
                     'logs_match': x['logs'] == y['logs'], 'state_match': x['after'] == y['after']})
    report = {
        'original_sha256': H(ORIGINAL.read_bytes()),
        'candidate_sha256': H(Path(candidate).read_bytes()),
        'group': group,
        'case_count': len(rows),
        'differential_matched': sum(not r['mismatches'] for r in rows),
        'mismatched_cases': [r['case']['name'] for r in rows if r['mismatches']],
        'cases': rows,
        'method': 'two independent LiteSVM instances (original vs candidate), identical signed tx, '
                  'byte-compared error/logs/inner-instructions/return-data/before/after + independent effect check',
    }
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(report, indent=2) + '\n',encoding='utf-8',newline='\n')
    print(json.dumps({k: report[k] for k in ['group', 'case_count', 'differential_matched', 'mismatched_cases',
                                             'original_sha256', 'candidate_sha256']}, indent=2))
    return report['differential_matched'] == report['case_count']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--group', choices=['ordinary', 'business_rejection'], default='ordinary')
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    ok = execute(a.candidate.resolve(), a.group, a.output.resolve())
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
