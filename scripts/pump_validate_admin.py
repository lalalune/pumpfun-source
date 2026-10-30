#!/usr/bin/env python3
"""Offline original-vs-recovered Pump administrative instruction differential tests."""
import argparse, base64, hashlib, json, pathlib
from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_amm_reusable_harness import pin_program

ROOT = pathlib.Path(__file__).resolve().parents[1]
IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PROGRAM = Pubkey.from_string(IDL['address'])
GLOBAL = Pubkey.find_program_address([b'global'], PROGRAM)[0]
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
AUTHORITY = Keypair.from_seed(bytes([201]) * 32)
PAYER = Keypair.from_seed(bytes([203]) * 32)
OUTSIDER = Keypair.from_seed(bytes([202]) * 32)
CAPTURE = next(x for x in json.loads((ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name'] == 'pump')
DATA = bytearray(base64.b64decode(CAPTURE['data_base64']))
DATA[9:41] = bytes(AUTHORITY.pubkey())


def execute(binary, instruction, arg, mutation):
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(PROGRAM, binary)
    vm.airdrop(PAYER.pubkey(), 10**12)
    vm.airdrop(AUTHORITY.pubkey(), 10**12)
    vm.airdrop(OUTSIDER.pubkey(), 10**12)
    data = bytearray(DATA)
    owner = PROGRAM
    global_key, event_key, program_key = GLOBAL, EVENT, PROGRAM
    authority = AUTHORITY
    signed = True
    global_write = authority_write = True
    if mutation == 'global_owner': owner = Pubkey.default()
    if mutation == 'global_discriminator': data[0] ^= 1
    if mutation == 'initialized_invalid': data[8] = 2
    if mutation.startswith('length_'): data = data[:int(mutation[7:])]
    if mutation == 'state_disabled':
        data[{'toggle_create_v2':450,'toggle_mayhem_mode':515,'toggle_cashback_enabled':740}[instruction]] = 0
    if mutation == 'global_truncated': data = data[:40]
    if mutation == 'global_address': global_key = Pubkey(bytes([91])*32)
    if mutation == 'global_readonly': global_write = False
    if mutation == 'authority_readonly': authority_write = False
    if mutation == 'authority_unsigned': signed = False
    if mutation == 'authority_wrong': authority = OUTSIDER
    if mutation == 'event_wrong': event_key = Pubkey(bytes([92])*32)
    if mutation == 'program_wrong': program_key = Pubkey.default()
    vm.set_account(global_key, Account(10**10, bytes(data), owner))
    metas = [AccountMeta(global_key, False, global_write), AccountMeta(authority.pubkey(), signed, authority_write), AccountMeta(event_key, False, False), AccountMeta(program_key, False, False)]
    if mutation == 'missing_event': metas = metas[:2]
    if mutation == 'missing_program': metas = metas[:3]
    discriminator = bytes(next(x['discriminator'] for x in IDL['instructions'] if x['name'] == instruction))
    payload = arg if mutation == 'raw_instruction_data' else discriminator + arg
    ix = Instruction(PROGRAM, payload, metas)
    tx = Transaction.new_signed_with_payer([ix], PAYER.pubkey(), [PAYER, authority] if signed else [PAYER], vm.latest_blockhash())
    r = vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    result = {'error': str(r.err()) if failed else None,
              'data_hex': vm.get_account(global_key).data.hex(),
              'lamports': vm.get_account(global_key).lamports,
              'logs': meta.logs()}
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--candidate', type=pathlib.Path, required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    a = p.parse_args()
    a.candidate = pin_program(a.candidate)
    original = ROOT / 'evidence/original/pump/deployed.so'
    cases = []
    names = ['toggle_create_v2', 'toggle_mayhem_mode', 'toggle_cashback_enabled', 'set_max_curve_depth']
    mutations = ['none', 'global_owner', 'global_discriminator', 'global_truncated', 'global_address', 'global_readonly', 'authority_readonly', 'authority_unsigned', 'authority_wrong', 'event_wrong', 'program_wrong', 'missing_event', 'missing_program','initialized_invalid','length_1087','length_1088']
    for name in names:
        for value in ([0, 1, 2] if name.startswith('toggle') else [0, 1, 2, 255]):
            for mutation in mutations if value == 1 else ['none']:
                args = bytes([value])
                results = [execute(binary, name, args, mutation) for binary in [original, a.candidate]]
                same = all(results[0][k] == results[1][k] for k in ['error', 'data_hex', 'lamports'])
                cases.append({'instruction': name, 'value': value, 'mutation': mutation, 'match': same, 'original': results[0], 'candidate': results[1]})
        if name.startswith('toggle'):
            results = [execute(binary, name, b'\x01', 'state_disabled') for binary in [original, a.candidate]]
            same = all(results[0][k] == results[1][k] for k in ['error', 'data_hex', 'lamports'])
            cases.append({'instruction':name, 'value':1, 'mutation':'state_disabled', 'match':same, 'original':results[0], 'candidate':results[1]})
        for args in [b'', b'\x01\x05']:
            results = [execute(binary, name, args, 'none') for binary in [original, a.candidate]]
            same = all(results[0][k] == results[1][k] for k in ['error', 'data_hex', 'lamports'])
            cases.append({'instruction': name, 'args_hex': args.hex(), 'mutation': 'none', 'match': same, 'original': results[0], 'candidate': results[1]})
    for n in range(9):
        args = bytes([255])*n
        results = [execute(binary, names[0], args, 'raw_instruction_data') for binary in [original, a.candidate]]
        same = all(results[0][k] == results[1][k] for k in ['error', 'data_hex', 'lamports'])
        cases.append({'instruction':'raw', 'args_hex':args.hex(), 'mutation':'raw_instruction_data', 'match':same, 'original':results[0], 'candidate':results[1]})
    mismatches = [i for i,c in enumerate(cases) if not c['match']]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = {'scope':'Four recovered administrative handlers only; local synthetic-authority state, not full program equivalence.', 'original_sha256':sha(original), 'candidate_sha256':sha(a.candidate), 'source_sha256':sha(ROOT/'programs/pump/src/lib.rs'), 'case_count':len(cases), 'mismatches':mismatches, 'cases':cases}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'case_count':len(cases), 'mismatches':mismatches}))
    for i in mismatches:
        c=cases[i];print(c['instruction'],c.get('value'),c['mutation'],c['original']['error'],c['candidate']['error'])
    if mismatches: raise SystemExit(1)

if __name__ == '__main__': main()
