"""Real signed Mayhem trade receipts must retain their actual executed image.

Six short-payload trade selectors execute in independent real LiteSVMs. Genuine
captured-Mayhem controls are verified unchanged. Explicit negative copies then
contradict their real executable snapshots; none is positive VM evidence.
This proves bounded saved-receipt admission, not rebuilt-program equivalence.
"""
if not __debug__:
    raise SystemExit('Normal Python is required for this reproduction')

import ast
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
PROOF.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'scripts'))
import test_mayhem_receipt_admission as fixtures
import solders.solders

FAMILIES = (
    ('verify_mayhem_buy.py', 'buy'),
    ('verify_mayhem_sell.py', 'sell'),
    ('verify_mayhem_buy_v2.py', 'buy_v2'),
    ('verify_mayhem_sell_v2.py', 'sell_v2'),
    ('verify_mayhem_pump_swap.py', 'buy_pump_swap'),
    ('verify_mayhem_pump_swap.py', 'sell_pump_swap'),
)
assert set(FAMILIES) <= set(fixtures.FAMILIES)
ORIGINAL = ROOT / 'evidence/original/mayhem/deployed.so'
OTHER_ELF = ROOT / 'evidence/original/pump_fees/deployed.so'
PROGRAM = str(fixtures.PROGRAM)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


original_sha, other_sha = sha(ORIGINAL), sha(OTHER_ELF)
assert original_sha != other_sha
assert ORIGINAL.read_bytes().startswith(b'\x7fELF')
assert OTHER_ELF.read_bytes().startswith(b'\x7fELF')
helper = Path(fixtures.__file__).resolve()
tree = ast.parse(helper.read_text(encoding='utf-8'))
producer = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == 'execute_rejection')
binding = {
    'fixture_helper_path': helper.relative_to(ROOT).as_posix(),
    'fixture_helper_sha256': sha(helper),
    'actual_vm_producer_ast_sha256': hashlib.sha256(
        ast.dump(producer, include_attributes=False).encode()).hexdigest(),
    'original_sha256': original_sha,
    'other_actual_elf_sha256': other_sha,
    'solders_version': importlib.metadata.version('solders'),
    'solders_binary_sha256': sha(solders.solders.__file__),
    'verifier_sha256': {name: sha(ROOT / 'scripts' / name) for name, _ in FAMILIES},
}
(PROOF / 'runtime-bindings.json').write_text(json.dumps(binding, indent=2) + '\n', encoding='utf-8')
env = dict(os.environ, PYTHONUTF8='1')
env.pop('PYTHONOPTIMIZE', None)
results = []


def invoke(instruction, tag, verifier, document, candidate):
    stem = instruction + '-' + tag
    receipt = PROOF / (stem + '.receipt.json')
    output = PROOF / (stem + '.verification.json')
    receipt.write_text(json.dumps(document, indent=2) + '\n', encoding='utf-8')
    command = [sys.executable, '-B', str(ROOT / 'scripts' / verifier),
               '--candidate', str(candidate), '--receipts', str(receipt),
               '--output', str(output)]
    completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=60)
    (PROOF / (stem + '.stdout.log')).write_bytes(completed.stdout)
    (PROOF / (stem + '.stderr.log')).write_bytes(completed.stderr)
    row = {'instruction': instruction, 'control': tag, 'verifier': verifier,
           'candidate_sha256': sha(candidate), 'receipt_sha256': sha(receipt),
           'returncode': completed.returncode, 'output_exists': output.is_file(),
           'command': command}
    if output.is_file():
        row['output_sha256'] = sha(output)
    return row


for verifier, instruction in FAMILIES:
    # Existing repository helper executes actual captured SBF with real normal
    # signatures and runtime sigverify/blockhash checking enabled. No VM calls,
    # accounts, results or transaction metadata are mocked or manufactured.
    original = fixtures.execute_rejection(instruction)
    candidate = fixtures.execute_rejection(instruction)
    assert original['transaction_base64'] == candidate['transaction_base64']
    for outcome in (original, candidate):
        for phase in ('before', 'after'):
            account = outcome[phase][PROGRAM]
            assert account['executable'] is True and account['data_sha256'] == original_sha
    document = {
        'scope': 'Genuine captured-Mayhem short-payload signed rejection control; not a rebuilt-candidate comparison.',
        'original_sha256': original_sha, 'candidate_sha256': original_sha,
        'harness_sha256': {helper.relative_to(ROOT).as_posix(): sha(helper)},
        'case_count': 1, 'mismatches': [],
        'cases': [{'case': {'name': 'short-payload', 'instruction': instruction},
                   'original': original, 'candidate': candidate, 'different_fields': []}],
    }
    control = invoke(instruction, 'genuine-control', verifier, document, ORIGINAL)
    control['expected'] = 'accept genuine real-VM receipt'
    control['passed'] = control['returncode'] == 0 and control['output_exists']
    results.append(control)

    # A deliberate receipt-integrity negative, not an asserted VM outcome:
    # only its header is relabelled to name another actual captured ELF. The
    # signed wire bytes, actual outcomes and executable snapshots stay intact.
    relabelled = copy.deepcopy(document)
    relabelled['candidate_sha256'] = other_sha
    relabelled['negative_control'] = 'Header names actual Fees ELF; candidate snapshots still identify actual Mayhem ELF.'
    negative = invoke(instruction, 'relabelled-candidate-header', verifier, relabelled, OTHER_ELF)
    negative['expected'] = 'reject candidate image inconsistent with real retained snapshots'
    negative['passed'] = negative['returncode'] != 0 and not negative['output_exists']
    results.append(negative)

    # Independent per-phase checks keep a valid header from masking a changed
    # original or candidate snapshot. These are explicitly tampered negatives.
    for side in ('original', 'candidate'):
        for phase in ('before', 'after'):
            changed = copy.deepcopy(document)
            changed['negative_control'] = f'Changed only {side} {phase} executable digest to another actual ELF hash.'
            changed['cases'][0][side][phase][PROGRAM]['data_sha256'] = other_sha
            negative = invoke(instruction, side + '-' + phase + '-wrong-image', verifier, changed, ORIGINAL)
            negative['expected'] = 'reject changed executable digest in either side or phase'
            negative['passed'] = negative['returncode'] != 0 and not negative['output_exists']
            results.append(negative)

    marker = copy.deepcopy(document)
    marker['negative_control'] = 'Executable marker is integer 1 instead of JSON boolean true.'
    marker['cases'][0]['candidate']['before'][PROGRAM]['executable'] = 1
    negative = invoke(instruction, 'nonboolean-executable-marker', verifier, marker, ORIGINAL)
    negative['expected'] = 'reject a nonboolean executable marker'
    negative['passed'] = negative['returncode'] != 0 and not negative['output_exists']
    results.append(negative)

assert sha(ORIGINAL) == original_sha and sha(OTHER_ELF) == other_sha
assert sha(helper) == binding['fixture_helper_sha256']
assert all(sha(ROOT / 'scripts' / name) == digest
           for name, digest in binding['verifier_sha256'].items())
summary = {
    'scope': __doc__, 'real_vm_executions': 12, 'trade_selectors': 6,
    'verifier_files': 5, 'genuine_controls': 6, 'marked_negative_controls': 36,
    'genuine_controls_passed': sum(row['passed'] for row in results if row['control'] == 'genuine-control'),
    'negative_controls_rejected': sum(row['passed'] for row in results if row['control'] != 'genuine-control'),
    'unexpectedly_accepted_negative_controls': [row for row in results
        if row['control'] != 'genuine-control' and not row['passed']],
    'results': results,
}
# Save every outcome, including successful verifier outputs on the faulty base,
# before failing the check. Those accepted negatives are never positive proof.
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in summary.items()
                  if key not in ('scope', 'results', 'unexpectedly_accepted_negative_controls')}, indent=2))
assert summary['genuine_controls_passed'] == 6
assert summary['negative_controls_rejected'] == 36, 'saved trade verifier accepted contradictory executed-image evidence'
