"""Run three comparison CLIs on retained ELF bytes using a real LLVM objdump."""
import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ('pump_compare_function_bytes.py', 'pump_exact_body_inventory.py',
           'pump_quote_control_function_match.py')
# Imported by pump_compare_function_bytes.py for its atomic report publication.
DEPENDENCIES = ('probe_report.py',)
LANE = 'reconstruction/pump-main/lanes/v3-sell-payment-layout'
EXPECTED_CANDIDATE = '969811b0e0f673b693695ea651008cacd93eafa5a663dd8bec0e61d3b22d09a9'
OBJDUMP = shutil.which('llvm-objdump')
SOURCE_REVISION = None
SCRIPT_DIRECTORY = None
RUNS = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ByteComparisonInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not OBJDUMP:
            raise RuntimeError('a real llvm-objdump is required; pass --objdump')
        cls.tool = Path(OBJDUMP).resolve()
        cls.sources = {}
        for name in SCRIPTS + DEPENDENCIES:
            if SCRIPT_DIRECTORY:
                content = (SCRIPT_DIRECTORY / name).read_bytes()
            elif SOURCE_REVISION:
                content = subprocess.check_output([
                    'git', '-C', str(ROOT), 'show', SOURCE_REVISION + ':scripts/' + name])
            else:
                content = (ROOT / 'scripts' / name).read_bytes()
            cls.sources[name] = content
        lane = ROOT / LANE
        manifest = json.loads((lane / 'manifest.json').read_text())
        compressed = (lane / 'candidate.so.gz').read_bytes()
        build_bytes = (lane / 'candidate-build.json').read_bytes()
        if sha(compressed) != manifest['packet']['candidate.so.gz']:
            raise RuntimeError('retained candidate archive hash differs')
        if sha(build_bytes) != manifest['packet']['candidate-build.json']:
            raise RuntimeError('retained candidate build record hash differs')
        cls.candidate_bytes = gzip.decompress(compressed)
        if sha(cls.candidate_bytes) != EXPECTED_CANDIDATE or json.loads(build_bytes)['unstripped_sha256'] != EXPECTED_CANDIDATE:
            raise RuntimeError('retained unstripped candidate binding differs')

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='byte-comparison-inputs-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name, content in self.sources.items():
            path = self.root / 'scripts' / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(content)
        # The maintained matcher shares logical instruction-boundary parsing.
        helper = self.root / 'reconstruction/harness/instruction_stream.py'
        helper.parent.mkdir(parents=True, exist_ok=True)
        helper.write_bytes((ROOT / 'reconstruction/harness/instruction_stream.py').read_bytes())
        for name in ('evidence/original/pump/deployed.so', 'reconstruction/base/functions.tsv'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)
        self.original = self.root / 'evidence/original/pump/deployed.so'
        self.inventory = self.root / 'reconstruction/base/functions.tsv'
        self.candidate = self.root / 'candidate.so'
        self.candidate.write_bytes(self.candidate_bytes)
        self.objdump = self.root / self.tool.name
        shutil.copy2(self.tool, self.objdump)
        # Owned copies may come from read-only package-manager installations.
        self.objdump.chmod(self.objdump.stat().st_mode | 0o200)
        with self.inventory.open() as stream:
            first = next(row for row in csv.DictReader(stream, delimiter='\t')
                         if row['program'] == 'pump' and row['variant'] == 'selected')
        self.start = first['original_start']

    def invoke(self, script, output, case):
        args = [sys.executable, '-B', str(self.root / 'scripts' / script)]
        pattern = '2e0b18c6f2883269E$'  # One genuine retained candidate symbol.
        if script == 'pump_quote_control_function_match.py':
            args += [str(self.candidate), '--pattern', pattern]
        else:
            args += ['--candidate', str(self.candidate)]
        if script == 'pump_compare_function_bytes.py':
            args += ['--original-start', self.start, '--symbol', pattern]
        args += ['--objdump', str(self.objdump), '--output', str(output)]
        result = subprocess.run(args, capture_output=True, text=True, timeout=90)
        RUNS.append({'script': script, 'case': case, 'returncode': result.returncode,
                     'diagnostic': result.stderr.strip().splitlines()[-1:]})
        return result

    def test_regular_reports_are_nonempty_and_repeatable(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                output = self.root / (script + '.json')
                first = self.invoke(script, output, 'regular-first')
                self.assertEqual(first.returncode, 0, first.stderr)
                before = output.read_bytes()
                report = json.loads(before)
                self.assertEqual(report['candidate_sha256'], EXPECTED_CANDIDATE)
                if script == 'pump_compare_function_bytes.py':
                    self.assertEqual(len(report['candidates']), 1)
                elif script == 'pump_exact_body_inventory.py':
                    self.assertEqual(report['original_windows'], 1035)
                else:
                    self.assertEqual(len(report['functions']), 1)
                second = self.invoke(script, output, 'regular-repeat')
                # pump_exact_body_inventory.py publishes with exclusive create so
                # a prior report is never replaced; the other two rewrite the
                # same bytes. Either way the published report cannot change.
                if script == 'pump_exact_body_inventory.py':
                    self.assertNotEqual(second.returncode, 0, second.stdout)
                    self.assertIn('File exists', second.stderr)
                else:
                    self.assertEqual(second.returncode, 0, second.stderr)
                self.assertEqual(output.read_bytes(), before)

    def reject_alias(self, script, target, output, case):
        before = target.read_bytes()
        try:
            result = self.invoke(script, output, case)
            RUNS[-1].update(input_before_sha256=sha(before),
                            input_after_sha256=sha(target.read_bytes()))
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('report destination aliases an input', result.stderr)
            self.assertEqual(target.read_bytes(), before)
        finally:
            # Baseline runs deliberately demonstrate the defect only in these
            # disposable copies; restore each input before the next subcase.
            if output != target and (output.exists() or output.is_symlink()):
                output.unlink()
            target.write_bytes(before)

    def test_candidate_path_symlink_and_hardlink_aliases_are_rejected(self):
        for script in SCRIPTS:
            for kind in ('path', 'symlink', 'hardlink'):
                with self.subTest(script=script, kind=kind):
                    output = self.candidate if kind == 'path' else self.root / 'candidate-alias'
                    if kind == 'symlink':
                        output.symlink_to(self.candidate)
                    elif kind == 'hardlink':
                        os.link(self.candidate, output)
                    self.reject_alias(script, self.candidate, output, 'candidate-' + kind)

    def test_bare_path_tool_records_the_executed_binary(self):
        absolute = self.objdump
        output = self.root / 'path-tool.json'
        self.assertEqual(self.invoke(SCRIPTS[1], output, 'absolute-tool').returncode, 0)
        before = json.loads(output.read_bytes())
        previous = os.environ.get('PATH')
        try:
            os.environ['PATH'] = str(absolute.parent) + os.pathsep + (previous or '')
            self.objdump = Path(absolute.name)
            # A second run needs a fresh report path: this script refuses to
            # replace an existing one (exclusive create).
            bare = self.root / 'path-tool-bare.json'
            result = self.invoke(SCRIPTS[1], bare, 'bare-path-tool')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(bare.read_bytes()), before)
            self.assertEqual(before['objdump_sha256'], sha(absolute.read_bytes()))
        finally:
            self.objdump = absolute
            if previous is None:
                os.environ.pop('PATH', None)
            else:
                os.environ['PATH'] = previous

    def test_other_consumed_inputs_are_preserved(self):
        for script in SCRIPTS:
            inputs = [self.original, self.root / 'scripts' / script,
                      self.root / 'scripts/pump_quote_control_function_match.py', self.objdump]
            if script != 'pump_quote_control_function_match.py':
                inputs.append(self.inventory)
            if script == 'pump_compare_function_bytes.py':
                inputs.append(self.root / 'scripts/pump_exact_body_inventory.py')
                # Imported at startup and executed to publish the report.
                inputs.append(self.root / 'scripts/probe_report.py')
            for target in dict.fromkeys(inputs):
                with self.subTest(script=script, target=target.name):
                    self.reject_alias(script, target, target, 'input:' + str(target.relative_to(self.root)))

    def test_selected_archived_inventory_is_preserved(self):
        archived = self.root / 'repro/reconstruction-status-2026-10-26/functions.tsv'
        archived.parent.mkdir(parents=True)
        shutil.copyfile(self.inventory, archived)
        for script in SCRIPTS[:2]:
            with self.subTest(script=script):
                self.reject_alias(script, archived, archived, 'archived-inventory')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--objdump', default=OBJDUMP)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--source-revision', help='Read comparison scripts from this Git revision for before proof')
    source.add_argument('--script-directory', type=Path, help='Read exported before scripts from this directory')
    parser.add_argument('--report', type=Path)
    options, remaining = parser.parse_known_args()
    OBJDUMP = options.objdump
    SOURCE_REVISION = options.source_revision
    SCRIPT_DIRECTORY = options.script_directory
    run = unittest.main(argv=[sys.argv[0], *remaining], exit=False)
    # A renamed, emptied or silently skipped case still exits 0 through
    # wasSuccessful(); the package is checked for exactly five passing tests.
    passed = (run.result.wasSuccessful() and run.result.testsRun == 5
              and not run.result.skipped)
    if options.report:
        # setUpClass does not run for a filtered or wholly skipped suite.
        tool = getattr(ByteComparisonInputTests, 'tool', None)
        tool_metadata = {'objdump_sha256': None, 'objdump_version': None}
        if tool is not None:
            try:
                tool_metadata.update(
                    objdump_sha256=sha(tool.read_bytes()),
                    objdump_version=subprocess.check_output([OBJDUMP, '--version'], text=True).splitlines()[0])
            except (OSError, subprocess.SubprocessError, IndexError) as error:
                tool_metadata['objdump_error'] = str(error)
                passed = False
        with options.report.open('x', encoding='utf-8') as stream:
            json.dump({'python': sys.version, 'objdump': str(OBJDUMP),
                       **tool_metadata,
                       'candidate_sha256': EXPECTED_CANDIDATE,
                       'source_sha256': {name: sha(content) for name, content in
                                         getattr(ByteComparisonInputTests, 'sources', {}).items()},
                       'tests_run': run.result.testsRun,
                       'skipped': [case.id() for case, _ in run.result.skipped],
                       'passed': passed, 'runs': RUNS}, stream, indent=2)
            stream.write('\n')
    sys.exit(0 if passed else 1)
