"""Exercise a real producer receipt against two byte-identical candidate pins."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
sys.path.insert(0, str(a.repo / 'scripts'))
import pump_validate_parallel as validator
from pump_amm_reusable_harness import pin_program

a.output.mkdir(parents=True, exist_ok=False)
original = a.repo / 'evidence/original/pump/deployed.so'
rows = []
for name, script in [
    ('creator_collection', 'pump_creator_collect_differential.py'),
    ('creator_collection_v2', 'pump_creator_collect_v2_differential.py'),
    ('fee_sweeps', 'pump_fee_sweep_differential.py'),
    ('minimum_distribution', 'pump_minimum_fee_differential.py'),
    ('set_params', 'pump_set_params_differential.py'),
]:
    with tempfile.TemporaryDirectory() as temporary:
        copied = Path(temporary) / 'same-image.so'
        shutil.copyfile(original, copied)
        first, second = pin_program(original), pin_program(copied)
        assert first != second and first.read_bytes() == second.read_bytes()
        receipt = a.output / (name + '.json')
        command = [sys.executable, str(a.repo / 'scripts' / script), '--candidate', str(first), '--output', str(receipt)]
        completed = subprocess.run(command, capture_output=True, text=True, check=True)
        (a.output / (name + '.log')).write_text(completed.stdout + completed.stderr)
        raw = receipt.read_bytes()
        result = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        admitted = validator.validate_result(name, result, first, original)
        try:
            replayed = validator.validate_result(name, result, second, original)
            replay_error = None
        except AssertionError as error:
            replayed, replay_error = None, repr(error)
        wrong_image = a.repo / 'evidence/original/pump_fees/deployed.so'
        rejected = {}
        for control, candidate_path, original_path in [('different_candidate', wrong_image, original),
                                                          ('different_original', first, wrong_image)]:
            try:
                validator.validate_result(name, result, candidate_path, original_path)
                rejected[control] = False
            except AssertionError:
                rejected[control] = True
        rows.append({'suite': name, 'producer_returncode': completed.returncode,
                     'first_admission': admitted, 'same_byte_second_pin_admission': replayed,
                     'same_byte_second_pin_error': replay_error,
                     'original_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
                     'receipt_sha256': hashlib.sha256(receipt.read_bytes()).hexdigest(),
                     'negative_controls_rejected': rejected,
                     'first_pin': str(first), 'second_pin': str(second)})
(a.output / 'results.json').write_text(json.dumps({'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=a.repo, text=True).strip(), 'rows': rows}, indent=2) + '\n')
print(json.dumps(rows))
