"""Fresh signed original/control/candidate comparisons for the five-function union.

Existing public fixture run APIs supply every instruction and account setup.
Bootstrap sends are retained separately. Case labels are intended boundaries,
not instruction traces; actual original errors and wire state remain visible.
Import, --help and --list-cases execute no proposal transactions.
"""
from pathlib import Path
import argparse, base64, gzip, hashlib, json, re, sys
if not __debug__:
    raise RuntimeError('Run without Python -O')
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'scripts'))
import pump_captured_loader as loader
loader.install()
BaseVM = loader.CapturedLiteSVM
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from solders.pubkey import Pubkey

sha = lambda raw: hashlib.sha256(raw).hexdigest()
CU = re.compile(r'^Program [1-9A-HJ-NP-Za-km-z]+ consumed [0-9]+ of [0-9]+ compute units$')
SENDS = []; CURRENT = {}; PHASE = 'target'
ALLOWED_SIGNERS = set()


def snapshot(account):
    if account is None: return None
    return dict(lamports=account.lamports, owner=str(account.owner), executable=account.executable,
                data_hex=None if account.executable else account.data.hex())


def verify_transaction(encoded):
    raw = base64.b64decode(encoded, validate=True); tx = Transaction.from_bytes(raw)
    tx.verify(); checks = tx.verify_with_results()
    assert bytes(tx) == raw and checks and all(checks)
    signers = list(tx.message.account_keys[:tx.message.header.num_required_signatures])
    assert signers and set(signers) <= ALLOWED_SIGNERS, 'Unexpected signer; no PDA substitution is permitted'
    return dict(transaction_sha256=sha(raw), signatures=[str(value) for value in tx.signatures],
                signature_count=len(checks), signer_keys=[str(key) for key in signers], all_verified=True)


class ObservedVM(BaseVM):
    def add_program_from_file(self, program, path):
        path = Path(path).resolve(); raw = path.read_bytes()
        answer = super().add_program_from_file(program, path)
        assert path.read_bytes() == raw
        if not hasattr(self, 'observed_loads'):
            self.observed_loads = []; self.active_loads = {}; self.pump_receipts = []
        self.observed_loads.append(dict(program=str(program), path=str(path), sha256=sha(raw), bytes=len(raw)))
        self.active_loads[str(program)] = sha(raw)
        if program == loader.PROGRAM:
            receipt = dict(loader.LOADS[-1])
            assert receipt['elf_sha256'] == sha(raw) and receipt['elf_prefix_unchanged'] and receipt['zero_allocation_tail']
            self.pump_receipts.append(receipt)
        return answer

    def send_transaction(self, tx):
        encoded = base64.b64encode(bytes(tx)).decode(); verification = verify_transaction(encoded)
        phase = PHASE
        if CURRENT.get('driver') == 'sweep':
            # The public sweep fixture genuinely bootstraps sharing through
            # Fees first, then invokes the selected Pump image at top level.
            top_pump = any(tx.message.account_keys[ix.program_id_index] == loader.PROGRAM for ix in tx.message.instructions)
            phase = 'target' if top_pump else 'bootstrap'
        keys = list(tx.message.account_keys)
        before = {str(key): snapshot(self.get_account(key)) for key in keys}
        result = super().send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata); meta = result.meta() if failed else result
        metadata = json.loads(meta.to_json())
        SENDS.append(dict(phase=phase, error=str(result.err()) if failed else None,
                          transaction_base64=encoded, signature_verification=verification,
                          before=before, after={str(key): snapshot(self.get_account(key)) for key in keys},
                          logs=meta.logs(), events=[line for line in meta.logs() if line.startswith('Program data:')],
                          inner=metadata['inner_instructions'], return_data=metadata.get('return_data'), metadata=metadata,
                          active_program_sha256=dict(self.active_loads), actual_program_loads=list(self.observed_loads),
                          captured_loader_loads=list(self.pump_receipts)))
        return result


def verified_vm():
    return ObservedVM().with_sigverify(True)


import solders.litesvm
solders.litesvm.LiteSVM = verified_vm
sys.path.insert(0, str(HERE))
import case_manifest as cases
for keypair in [cases.create.USER, cases.create.MINT, cases.create.OTHER,
                cases.sweep.PAYER, cases.sweep.AUTH, cases.sweep.OTHER, cases.v3.user, cases.sell.USER]:
    ALLOWED_SIGNERS.add(keypair.pubkey())
cases.create.LiteSVM = verified_vm
cases.control.LiteSVM = verified_vm
cases.sweep.f.LiteSVM = verified_vm
cases.v3.f.LiteSVM = verified_vm
cases.sell.f.LiteSVM = verified_vm


def run(row, image):
    global PHASE
    CURRENT.clear(); CURRENT.update(row); PHASE = 'target'
    SENDS.clear(); loader.LOADS.clear()
    driver, case = row['driver'], row['case']
    if driver in ['create', 'control', 'sweep', 'sell']:
        result = getattr(cases, driver).run(case, image)
        bootstrap = None
    elif driver == 'v3':
        result = cases.v3.run(image, case); bootstrap = None
    elif driver == 'nested':
        boot = cases.nested.load(); boot.LiteSVM = verified_vm
        boot.MINT = boot.OTHER
        boot.CURVE = boot.Pubkey.find_program_address([b'bonding-curve', bytes(boot.MINT.pubkey())], boot.PROGRAM)[0]
        PHASE = 'bootstrap'
        bootstrap = boot.run(dict(instruction='create_v2', name='Synthetic Quote', symbol='QUOTE', **case.get('root', {})), image)
        assert bootstrap['error'] is None, 'Nested quote bootstrap failed; preserve this as a real failure'
        accounts = {key: value for key, value in bootstrap['after'].items()
                    if value is not None and value != bootstrap['before'][key]}
        child = dict(instruction='create_v2', quote=True, quote_token22=True, quote_whitelisted=False,
                     quote_control=True, control_entries=[], nested=True, bootstrap_accounts=accounts, **case.get('child', {}))
        target = cases.nested.load(); target.LiteSVM = verified_vm
        PHASE = 'target'; result = target.run(child, image)
    else:
        raise ValueError(driver)
    targets = [value for value in SENDS if value['phase'] == 'target']
    assert len(targets) == 1
    return dict(fixture_result=result, fixture_bootstrap=bootstrap, sends=list(SENDS), target=targets[0])


def create_wire(run_result):
    value = run_result['fixture_result']['after'].get(str(cases.create.CURVE))
    if value is None or not value.get('data'):
        return dict(created=False)
    raw = bytes.fromhex(value['data'])
    expected = next(row['discriminator'] for row in cases.create.IDL['accounts'] if row['name'] == 'BondingCurve')
    if raw[:8] != bytes(expected):
        return dict(created=False, allocated_bytes=len(raw), discriminator_hex=raw[:8].hex())
    fields = next(row for row in cases.create.IDL['types'] if row['name'] == 'BondingCurve')['type']['fields']
    offset = 8; decoded = {}
    for field in fields:
        kind = field['type']; width = {'u64': 8, 'u8': 1, 'bool': 1, 'pubkey': 32}[kind]
        data = raw[offset:offset+width]; assert len(data) == width
        if kind == 'pubkey': result = str(Pubkey(data))
        elif kind == 'bool': assert data[0] in [0, 1]; result = bool(data[0])
        else: result = int.from_bytes(data, 'little')
        decoded[field['name']] = result; offset += width
    return dict(created=True, allocated_bytes=len(raw), decoded_bytes=offset, wire_sha256=sha(raw),
                owner=value['owner'], lamports=value['lamports'], fields=decoded)


def dependency_map():
    result = {}
    for category in ['original', 'dependencies']:
        for capture in sorted((ROOT/'evidence'/category).glob('*/capture.json')):
            record = json.loads(capture.read_bytes()); elf = capture.with_name('deployed.so')
            assert sha(elf.read_bytes()) == record['payload_sha256']
            result[record['program']] = dict(payload_sha256=record['payload_sha256'],
                                           capture_sha256=sha(capture.read_bytes()), path=str(elf.relative_to(ROOT)))
    return result


def check_loads(outcome, role_sha, dependencies, original_sha):
    for send in outcome['sends']:
        expected_pump = role_sha
        if CURRENT['driver'] == 'sweep' and send['phase'] == 'bootstrap': expected_pump = original_sha
        assert send['active_program_sha256'][str(loader.PROGRAM)] == expected_pump
        assert send['captured_loader_loads'][-1]['elf_sha256'] == expected_pump
        for program, digest in send['active_program_sha256'].items():
            if program != str(loader.PROGRAM): assert digest == dependencies[program]['payload_sha256']
        assert send['signature_verification']['all_verified']


def differences(left, right):
    result = []
    if len(left['sends']) != len(right['sends']): return ['signed_send_count']
    for index, (a, b) in enumerate(zip(left['sends'], right['sends'])):
        for key in ['phase', 'error', 'before', 'after', 'events', 'inner', 'return_data', 'transaction_base64']:
            if a[key] != b[key]: result.append(f'sends/{index}/{key}')
        if [line for line in a['logs'] if not CU.fullmatch(line)] != [line for line in b['logs'] if not CU.fullmatch(line)]:
            result.append(f'sends/{index}/ordered_logs')
    if left.get('create_wire') != right.get('create_wire'): result.append('create_wire')
    return result


def input_bindings():
    paths = {Path(__file__), HERE/'case_manifest.py', ROOT/'scripts/pump_captured_loader.py',
             ROOT/'research/imported-lab/analysis/pump_fun/config-snapshot.json',
             ROOT/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',
             ROOT/'scripts/pump_create_nested_fixture.py', ROOT/'scripts/pump_trade_fixture.py',
             ROOT/'scripts/fees_sharing_create_differential.py', ROOT/'scripts/fees_donation_create_differential.py',
             ROOT/'scripts/fees_admin_differential.py', ROOT/'scripts/pump_validate_admin.py'}
    paths.update(Path(module.__file__) for module in [cases.create, cases.control, cases.nested, cases.sweep, cases.v3, cases.sell])
    paths.update((ROOT/'evidence/upstream'/name) for name in ['pump.json', 'pump_amm.json', 'pump_fees.json'])
    return {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in sorted(paths)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path); parser.add_argument('--candidate', type=Path)
    parser.add_argument('--output', type=Path); parser.add_argument('--list-cases', action='store_true')
    args = parser.parse_args(); rows = cases.manifest()
    if args.list_cases:
        print(json.dumps(dict(counts={group: sum(row['group'] == group for row in rows)
                                      for group in ['create', 'sweep', 'v3', 'sell']}, target_cases=len(rows), cases=rows), indent=2)); return
    if not all([args.control, args.candidate, args.output]): parser.error('--control, --candidate and --output required')
    assert not args.output.exists(), 'Retain every attempt; output must be fresh'
    images = dict(original=ROOT/'evidence/original/pump/deployed.so', control=args.control.resolve(), candidate=args.candidate.resolve())
    hashes = {role: sha(path.read_bytes()) for role, path in images.items()}
    assert hashes['original'] == loader.CAPTURE['payload_sha256']
    inputs = input_bindings(); dependencies = dependency_map(); retained = []
    report = dict(scope=__doc__, images_sha256=hashes, inputs_sha256=inputs, dependency_captures=dependencies,
                  excluded_log_pattern=CU.pattern, bootstrap_policy='Sweep uses the public original sharing bootstrap; nested creation builds its quote root independently with each selected role image.', cases=retained)
    for row in rows:
        runs = {}
        for role, image in images.items():
            runs[role] = run(row, image)
            check_loads(runs[role], hashes[role], dependencies, hashes['original'])
            if row['group'] == 'create': runs[role]['create_wire'] = create_wire(runs[role])
        retained.append(dict(case=row, runs=runs, control_differences=differences(runs['original'], runs['control']),
                             candidate_differences=differences(runs['original'], runs['candidate'])))
        report.update(target_case_count=len(retained), target_execution_count=len(retained)*3,
                      bootstrap_execution_count=sum(send['phase'] == 'bootstrap' for item in retained for value in item['runs'].values() for send in value['sends']),
                      signature_fields=sum(send['signature_verification']['signature_count'] for item in retained for value in item['runs'].values() for send in value['sends']))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0))
        print(json.dumps(dict(case=row['name'], group=row['group'], errors={role: value['target']['error'] for role, value in runs.items()},
                              control_differences=retained[-1]['control_differences'], candidate_differences=retained[-1]['candidate_differences'])), flush=True)
    assert inputs == input_bindings() and hashes == {role: sha(path.read_bytes()) for role, path in images.items()}
    assert all(not row['candidate_differences'] for row in retained), 'Original/candidate mismatch; raw report retained'


if __name__ == '__main__': main()
