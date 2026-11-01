#!/usr/bin/env python3
"""Normally signed offline Surfpool legacy buy / buy_exact_sol_in comparisons."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import base64
import hashlib
import json
import socket
import struct
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from solders.compute_budget import set_compute_unit_limit
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.transaction import Transaction

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_legacy_buy_differential as fixtures
from surfpool_recording_vm import RecordingVM, require_aligned_runs
PORT = 20211
COMPUTE = Pubkey.from_string('ComputeBudget111111111111111111111111111111')
DEPENDENCIES = [(n,Pubkey.from_string(json.loads((ROOT/('evidence/original' if n=='pump_fees' else 'evidence/dependencies')/n/'capture.json').read_text())['program'])) for n in ['pump_fees','spl_token','spl_token_2022','associated_token']]

def dependency_path(name):
    return ROOT / ('evidence/original' if name in ['pump','pump_amm','pump_fees'] else 'evidence/dependencies') / name / 'deployed.so'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CollectRecordingVM(RecordingVM):
    def with_sigverify(self, enabled):
        assert enabled
        self.vm.with_sigverify(enabled)
        return self
    def airdrop(self,key,amount):
        result=self.vm.airdrop(key,amount)
        a=self.vm.get_account(key)
        self.accounts[str(key)]={'lamports':a.lamports,'data':a.data.hex(),'owner':str(a.owner),'executable':a.executable}
        return result

def prepare(case):
    original_type = fixtures.f.LiteSVM
    recorded = []
    def factory():
        vm = CollectRecordingVM(original_type())
        recorded.append(vm)
        return vm
    fixtures.f.LiteSVM = factory
    try:
        receipt = fixtures.run(case)
    finally:
        fixtures.f.LiteSVM = original_type
    vm = recorded[0]
    return {'case': case, 'accounts': vm.accounts,
            'transaction_base64': base64.b64encode(bytes(vm.transaction)).decode(),
            'litesvm_error': receipt['error']}


def run(binary, cases, surfpool, output):
    def rpc(method, params=None):
        request = urllib.request.Request(f'http://127.0.0.1:{PORT}', data=json.dumps(
            {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or []}).encode(),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
        if 'error' in result:
            raise RuntimeError((method, result['error']))
        return result['result']

    def get(key):
        value = rpc('getAccountInfo', [key, {'encoding': 'base64'}])['value']
        if value is None:
            return None
        data = base64.b64decode(value['data'][0])
        result = {'lamports':value['lamports'], 'owner':value['owner'], 'executable':value['executable']}
        if value['executable']:
            result.update(data_sha256=hashlib.sha256(data).hexdigest(), data_length=len(data))
        else:
            result['data'] = data.hex()
        return result

    with (output / (binary.stem + '.log')).open('w') as log:
        process = subprocess.Popen([str(surfpool), 'start', '--offline', '--no-deploy', '--no-tui',
            '--no-studio', '--host', '127.0.0.1', '--port', str(PORT), '--ws-port', str(PORT + 1),
            '--airdrop-amount', '0', '--db', ':memory:'], cwd=output, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Surfpool terminated during startup')
                try:
                    if rpc('getHealth') == 'ok':
                        break
                except OSError:
                    pass
                time.sleep(.1)
            else:
                raise TimeoutError('Surfpool startup')
            programs = [(fixtures.P, binary)] + [(key, dependency_path(name))
                        for name, key in DEPENDENCIES]
            for key, path in programs:
                blob = path.read_bytes()
                extent = struct.unpack_from('<Q', blob, 40)[0] + struct.unpack_from('<H', blob, 58)[0] * struct.unpack_from('<H', blob, 60)[0]
                if any(blob[extent:]):
                    raise AssertionError(f'Nonzero bytes after ELF section table: {path}')
                rpc('surfnet_setAccount', [str(key), {'lamports': 10**10, 'data': blob[:extent].hex(),
                    'owner': 'BPFLoader2111111111111111111111111111111111', 'executable': True}])
            results = []
            for index, case in enumerate(cases):
                for key, account in case['accounts'].items():
                    rpc('surfnet_setAccount', [key, account])
                source = Transaction.from_bytes(base64.b64decode(case['transaction_base64']))
                message = source.message
                header, keys = message.header, message.account_keys
                snapshot_keys = sorted(set(case['accounts']) | {str(key) for key in keys})
                before = {key:get(key) for key in snapshot_keys}
                def writable(n):
                    if n < header.num_required_signatures:
                        return n < header.num_required_signatures - header.num_readonly_signed_accounts
                    return n < len(keys) - header.num_readonly_unsigned_accounts
                # The saved fixture already has a compute-budget instruction.
                # Replace it, rather than submitting duplicate limit settings.
                instructions = [set_compute_unit_limit(1_400_000 - index)]
                for ix in message.instructions:
                    if keys[ix.program_id_index] == COMPUTE:
                        continue
                    instructions.append(Instruction(keys[ix.program_id_index], bytes(ix.data),
                        [AccountMeta(keys[n], n < header.num_required_signatures, writable(n)) for n in ix.accounts]))
                signers = [kp for kp in [fixtures.USER]
                           if kp.pubkey() in keys[:header.num_required_signatures]]
                tx = Transaction.new_signed_with_payer(instructions, fixtures.USER.pubkey(), signers,
                    Hash.from_string(rpc('getLatestBlockhash')['value']['blockhash']))
                if not (tx.signatures and all(tx.verify_with_results())):
                    raise AssertionError('Transaction signatures failed verification')
                encoded = base64.b64encode(bytes(tx)).decode()
                simulation = rpc('simulateTransaction', [encoded, {'encoding': 'base64', 'sigVerify': True, 'innerInstructions': True}])['value']
                signature = rpc('sendTransaction', [encoded, {'encoding': 'base64', 'skipPreflight': True}])
                for _ in range(100):
                    status = rpc('getSignatureStatuses', [[signature]])['value'][0]
                    if status is not None:
                        break
                    time.sleep(.05)
                else:
                    raise TimeoutError('Transaction confirmation')
                if simulation['err'] != status['err']:
                    raise AssertionError('Simulation and committed transaction error differ')
                after = {key:get(key) for key in snapshot_keys}
                if status['err']:
                    assert all(before[key] == after[key] for key in before if key != str(fixtures.USER.pubkey())), 'Rejected transaction mutated non-fee-payer state'
                results.append({'case': case['case'], 'signature': signature, 'transaction_base64': encoded,
                    'signature_verification': True, 'message_keys':[str(k) for k in keys], 'error': status['err'], 'before': before, 'after': after,
                    'logs': simulation.get('logs', []), 'return_data': simulation.get('returnData'),
                    'simulation': simulation})
            return results
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def normalized(row):
    result = {'error':row['error'], 'return_data':row['return_data']}
    for stage in ['before','after']:
        state = json.loads(json.dumps(row[stage]))
        program = state.get(str(fixtures.P))
        if program:
            # Fees candidate executable bytes differ intentionally. Fixed load
            # funding is identical; preserve/compare its owner/lamports/flags.
            program.pop('data_sha256',None)
            program.pop('data_length',None)
        result[stage] = state
    stack, events = [], []
    for line in row['logs']:
        if line.startswith('Program ') and ' invoke [' in line:
            stack.append(line.split()[1])
        elif line.startswith('Program ') and (line.endswith(' success') or ' failed:' in line):
            program = line.split()[1]
            if stack and stack[-1] == program:
                stack.pop()
        elif line.startswith('Program data: '):
            if not stack:
                raise AssertionError('Cannot attribute event to emitting program')
            program = stack[-1]
            data = bytearray(base64.b64decode(line[len('Program data: '):]))
            discriminator = data[:8].hex()
            if program == str(fixtures.P) and discriminator == hashlib.sha256(b'event:TradeEvent').digest()[:8].hex():
                offset = 89
            elif program == str(fixtures.P) and discriminator == hashlib.sha256(b'event:CompleteEvent').digest()[:8].hex():
                offset = 104
            else:
                raise AssertionError('Unrecognized event: '+program+'/'+discriminator)
            assert len(data) >= offset+8
            data[offset:offset+8] = bytes(8)
            events.append({'program':program,'data_except_timestamp':data.hex()})
    result['events_except_timestamp'] = events
    if 'innerInstructions' not in row['simulation']:
        raise AssertionError('Surfpool did not retain requested inner instructions')
    inner=json.loads(json.dumps(row['simulation']['innerInstructions'] or []))
    alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    def decode(value):
        n=0
        for char in value:n=n*58+alphabet.index(char)
        return bytes(len(value)-len(value.lstrip('1')))+(n.to_bytes((n.bit_length()+7)//8,'big') if n else b'')
    tag=bytes([228,69,165,46,81,203,154,29])
    for group in inner:
        for ix in group['instructions']:
            if 'data' not in ix:
                assert 'parsed' in ix, 'Unrecognized inner instruction representation'
                continue
            data=bytearray(decode(ix['data']))
            program=ix.get('programId') or row['message_keys'][ix['programIdIndex']]
            if program==str(fixtures.P) and data[:8]==tag:
                offsets={hashlib.sha256(b'event:TradeEvent').digest()[:8]:89,hashlib.sha256(b'event:CompleteEvent').digest()[:8]:104}
                disc=bytes(data[8:16])
                if disc not in offsets:raise AssertionError('Unknown Pump event CPI')
                off=8+offsets[disc];assert len(data)>=off+8;data[off:off+8]=bytes(8)
            ix['data']=data.hex()
    result['inner_instructions_except_event_timestamps']=inner
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--surfpool', type=Path, default=ROOT / 'work/localnet/surfpool')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output, args.surfpool = args.output.resolve(), args.surfpool.resolve()
    if subprocess.check_output([str(args.surfpool), '--version'], text=True).strip() != 'surfpool 1.6.1':
        raise RuntimeError('Expected pinned Surfpool 1.6.1')
    for port in [PORT, PORT + 1]:
        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            sock.bind(('127.0.0.1', port))
    args.output.mkdir(parents=True, exist_ok=False)
    original, candidate = args.output / 'original.so', args.output / 'candidate.so'
    original.write_bytes((ROOT / 'evidence/original/pump/deployed.so').read_bytes())
    candidate.write_bytes(args.candidate.read_bytes())
    cases=[]
    for kind in ['buy','buy_exact_sol_in']:
        available=[c for c in fixtures.cases() if c['kind']==kind]
        wanted=[f'{kind}_500000000_[]',f'{kind}_0_[]','flags_[[81, 1]]_[]','flags_[[82, 1]]_[1, 0]','flags_[[124, 1]]_[]','creator_override_500_None','creator_override_500_82','creator_override_18446744073709551615_None','missing_remaining','missing_buyback',"mutate_global_volume_accumulator_{'length': 8}","mutate_user_volume_accumulator_{'system_owner': True}"]
        wanted += ['completion_793099000000000_0','completion_793099000000001_1'] if kind=='buy' else ['completion_100000000000_0','completion_1000000000000_1']
        selected=[c for c in available if c['name'] in wanted]
        assert len(selected)==len(wanted),(kind,len(selected),len(wanted))
        cases.extend(selected)
        cases.append({'name':'legacy_rent_'+kind,'kind':kind,'amount':500000000,'minimum':10**12 if kind=='buy' else 1,'account_mutations':{'bonding_curve':{'length':81,'lamports':100000}}})
    extremes={f'extreme_override_{bps}_{spend}' for bps,spend in [(2**63,1),(2**63,10**9),(2**64-1,1),(2**64-1,10**9)]}
    cases.extend(c for c in fixtures.cases() if c['name'] in extremes)
    fixture_hash, runner_hash = sha(Path(fixtures.__file__)), sha(Path(__file__))
    prepared = [prepare(case) for case in cases]
    (args.output / 'fixtures.json').write_text(json.dumps(prepared, indent=2) + '\n',encoding='utf-8',newline='\n')
    left = run(original, prepared, args.surfpool, args.output)
    right = run(candidate, prepared, args.surfpool, args.output)
    require_aligned_runs(prepared, left, right)
    (args.output / 'raw-transactions.json').write_text(json.dumps({'original': left, 'candidate': right}, indent=2) + '\n',encoding='utf-8',newline='\n')
    import re
    def expected_error(value):
        if value is None: return None
        custom = re.fullmatch(r'TransactionErrorInstructionError\(\((\d+), Tagged\(InstructionErrorCustom\((\d+)\)\)\)\)',value)
        if custom: return {'InstructionError':[int(custom[1]),{'Custom':int(custom[2])}]}
        named = re.fullmatch(r'TransactionErrorInstructionError\(\((\d+), Fieldless\((\w+)\)\)\)',value)
        if named: return {'InstructionError':[int(named[1]),named[2]]}
        raise AssertionError('Unhandled original error: '+value)
    unexpected = [i for i,(row,fixture) in enumerate(zip(left,prepared)) if row['error'] != expected_error(fixture['litesvm_error'])]
    mismatches = [i for i,(x,y) in enumerate(zip(left,right)) if normalized(x) != normalized(y)]
    assert fixture_hash == sha(Path(fixtures.__file__)), 'Fixture script changed during run'
    assert runner_hash == sha(Path(__file__)), 'Runner changed during run'
    assert sha(args.candidate) == sha(candidate), 'Candidate input changed during run'
    report = {'scope': 'Offline normally signed Pump legacy buy / buy_exact_sol_in comparisons. Synthetic state, normal fee payer; no direct PDA signatures. Account balances, errors, returns, events and inner instructions compared except schema-known event timestamps and executable image bytes. Active campaign accrual is not established by these fixtures. Raw evidence retained; full binary equality remains false.',
        'original_sha256': sha(original), 'candidate_sha256': sha(candidate), 'surfpool_sha256': sha(args.surfpool),
        'fixture_script_sha256': fixture_hash, 'runner_sha256': runner_hash,
        'dependency_sha256': {name: sha(dependency_path(name)) for name, _ in DEPENDENCIES},
        'cases': len(cases), 'signed_transactions': len(left) + len(right), 'mismatches': mismatches,
        'unexpected_original_errors': unexpected, 'original': left, 'candidate': right}
    (args.output / 'pump-legacy-buy-transactions.json').write_text(json.dumps(report, indent=2) + '\n',encoding='utf-8',newline='\n')
    print(json.dumps({key: report[key] for key in ['cases', 'signed_transactions', 'mismatches', 'unexpected_original_errors', 'original_sha256', 'candidate_sha256']}, indent=2))
    if mismatches or unexpected:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
