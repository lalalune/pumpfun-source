"""Reproduce the stdin-mode workflow false positive without executing project code."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checker', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'scripts/check_workflow_inputs.py')
    args = parser.parse_args()
    checker = args.checker.resolve()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        workflow = root / '.github/workflows/test.yml'
        workflow.parent.mkdir(parents=True)
        workflow.write_text('jobs:\n  audit:\n    steps:\n'
                            '      - run: bash -s -- scripts/not-a-file.sh < /dev/null\n', encoding='utf-8')
        result = subprocess.run([sys.executable, str(checker), '--repo', str(root), '--all'],
                                text=True, capture_output=True, check=False)
        controls = {}
        for shell in ('bash', 'sh'):
            if shutil.which(shell):
                actual = subprocess.run([shell, '-s', '--', 'scripts/not-a-file.sh'],
                                        cwd=root, input='', text=True, capture_output=True)
                controls[shell] = actual.returncode
        print(json.dumps({'checker_sha256': hashlib.sha256(checker.read_bytes()).hexdigest(),
                          'checker_exit': result.returncode, 'checker_report': json.loads(result.stdout),
                          'native_stdin_shell_exit': controls,
                          'positional_path_exists': (root / 'scripts/not-a-file.sh').exists()}, indent=2))


if __name__ == '__main__':
    main()
