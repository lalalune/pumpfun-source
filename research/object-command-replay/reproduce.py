"""Actually compile and replay local-object receipts with normal path variants."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
BUILD = ROOT / 'work/object-command-proof'
PROOF.mkdir(parents=True, exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def process(name, command, cwd):
    with (PROOF / (name + '.log')).open('w') as stream:
        try:
            completed = subprocess.run(command, cwd=cwd, stdout=stream,
                                       stderr=subprocess.STDOUT, timeout=180)
            return completed.returncode, None
        except OSError as error:
            stream.write(str(error) + '\n')
            return None, str(error)


def build(name, script, sdk_arg, output, cwd):
    code, error = process(name + '-build', [sys.executable, '-B', str(ROOT / 'scripts' / script),
                           '--toolchain', str(sdk_arg), '--output', str(output)], cwd)
    assert code == 0 and error is None, 'actual supported object build failed: ' + name
    report = json.loads((output / 'comparison.json').read_text())
    obj = output / ('constant_product.o' if script.startswith('pump_') else 'fee_selection.o')
    assert sha(obj) == report['object_sha256']
    shutil.copyfile(output / 'comparison.json', PROOF / (name + '-comparison.json'))
    shutil.copyfile(obj, PROOF / (name + '-original.o'))
    return report, obj.name


def replay(name, report, filename, sdk, directory, cwd):
    directory.mkdir()
    expanded = [item.replace('<toolchain>', str(sdk)).replace('<repo>', str(ROOT))
                    .replace('<output>', str(directory)) for item in report['command']]
    (PROOF / (name + '-expanded-command.json')).write_text(json.dumps(expanded, indent=2) + '\n')
    code, error = process(name + '-replay', expanded, cwd)
    generated = directory / filename
    okay = code == 0 and generated.is_file() and sha(generated) == report['object_sha256']
    if generated.is_file():
        shutil.copyfile(generated, PROOF / (name + '-replayed.o'))
    return {'replay_exit_code': code, 'replay_launch_error': error,
            'fresh_output_exists': generated.is_file(), 'raw_object_reproduced': okay,
            'original_object_sha256': report['object_sha256']}


results = {}
with tempfile.TemporaryDirectory(prefix='object-command-proof-') as temporary:
    external = Path(temporary)
    # Existing absolute SDK/out usage is a successful real-compiler control.
    report, filename = build('fee-absolute', 'build_fee_selection.py', SDK,
                             external / 'fee-absolute', ROOT)
    results['fee-absolute'] = replay('fee-absolute', report, filename, SDK,
                                      external / 'fee-absolute-replay', ROOT)
    assert results['fee-absolute']['raw_object_reproduced']
    # A relative SDK '.' must not rewrite periods inside source/object names.
    report, filename = build('fee-dot-sdk', 'build_fee_selection.py', Path('.'),
                             external / 'fee-dot-sdk', SDK)
    results['fee-dot-sdk'] = replay('fee-dot-sdk', report, filename, SDK,
                                     external / 'fee-dot-sdk-replay', SDK)
    # An output below the repo must still be retargetable to a fresh output.
    report, filename = build('fee-nested-output', 'build_fee_selection.py', SDK,
                             BUILD / 'fee-nested-output', ROOT)
    results['fee-nested-output'] = replay('fee-nested-output', report, filename, SDK,
                                            external / 'fee-nested-output-replay', ROOT)
    # A supported SDK staged inside the repo must remain a toolchain operand,
    # even after moving that owned clone and expanding the receipt accordingly.
    nested_sdk, moved_sdk = BUILD / 'sdk-original', BUILD / 'sdk-relocated'
    subprocess.run(['cp', '-cR', str(SDK), str(nested_sdk)], check=True)
    report, filename = build('curve-nested-sdk', 'pump_build_constant_product.py', nested_sdk,
                             external / 'curve-nested-sdk', ROOT)
    nested_sdk.rename(moved_sdk)
    results['curve-nested-sdk'] = replay('curve-nested-sdk', report, filename, moved_sdk,
                                          external / 'curve-nested-sdk-replay', ROOT)
(PROOF / 'result.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
assert all(item['raw_object_reproduced'] for item in results.values()), 'portable receipts cannot replay their actual compiler commands'
