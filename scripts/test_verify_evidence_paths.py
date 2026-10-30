"""Every script the `evidence` suite in .github/workflows/verify.yml runs must exist.

The suite runs under `bash -e`, so one missing entrypoint stops it before the
remaining checks. This reads the workflow as text (stdlib only, no YAML library)
and checks the `python ... <path>.py` commands of that one suite. The broader,
all-workflow input check is #1447 (scripts/check_workflow_inputs.py).

Run from the repository root: python3 -I -B scripts/test_verify_evidence_paths.py
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'verify.yml'
COMMAND = re.compile(r'^\s*python3?\s+(?:-\S+\s+)*(\S+\.py)\b')


def suite_commands(text, suite):
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == f'- suite: {suite}')
    body = []
    for line in lines[start + 1:]:
        if line.strip().startswith('- suite:'):
            break
        body.append(line)
    return body


def referenced_scripts(lines):
    return [m.group(1) for m in map(COMMAND.match, lines) if m]


class EvidenceSuitePathTests(unittest.TestCase):
    def test_extractor_reads_flags_and_paths(self):
        self.assertEqual(referenced_scripts(['  python -I -B scripts/a.py --repo .', '  # python x.py', '  git diff']),
                         ['scripts/a.py'])

    def test_evidence_suite_scripts_exist(self):
        scripts = referenced_scripts(suite_commands(WORKFLOW.read_text(encoding='utf-8'), 'evidence'))
        self.assertTrue(scripts, 'evidence suite has no python commands; extractor out of date?')
        missing = [s for s in scripts if not (ROOT / s).is_file()]
        self.assertEqual(missing, [], 'evidence suite references missing scripts')


if __name__ == '__main__':
    unittest.main()
