#!/usr/bin/env python3
"""Classify observed invocation errors without claiming no code executed."""
import json
import hashlib
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import revalidate_all as revalidate

REQUIRES_IMAGES = """import argparse
ap = argparse.ArgumentParser()
ap.add_argument('--images', required=True)
ap.parse_args()
print('ran')
"""

FAILS = """print('evidence differs')
raise SystemExit(1)
"""

PASSES = """print('ok')
"""


class RequiredArgumentTests(unittest.TestCase):
    def test_usage_error_names_every_required_option(self):
        output = ("usage: verify.py [-h] --images IMAGES [--root ROOT]\n"
                  "verify.py: error: the following arguments are required: "
                  "--images, --root")
        self.assertEqual(revalidate.required_arguments(output),
                         ['--images', '--root'])

    def test_phrase_without_usage_or_exact_error_marker_is_not_admitted(self):
        for text in ('the following arguments are required: --images',
                     'usage: verify.py [-h]\nverify.py: evidence differs: the following arguments are required: --images',
                     'usage: other.py [-h]\nverify.py: error: the following arguments are required: --images'):
            self.assertEqual(revalidate.required_arguments(text), [])

    def test_other_output_names_no_required_option(self):
        self.assertEqual(revalidate.required_arguments('evidence differs'), [])
        self.assertEqual(revalidate.required_arguments('Traceback (most recent call last):'), [])


class RunVerifyTests(unittest.TestCase):
    def packet(self, source):
        temporary = tempfile.TemporaryDirectory(prefix='revalidate-invocation-')
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        (directory / 'verify.py').write_text(source, encoding='utf-8')
        return directory

    def test_missing_required_argument_is_not_a_failure(self):
        result = revalidate.run_verify(self.packet(REQUIRES_IMAGES))
        self.assertEqual(result['status'], 'invocation_error')
        self.assertEqual(result['required'], ['--images'])

    def test_evidence_disagreement_stays_a_failure(self):
        result = revalidate.run_verify(self.packet(FAILS))
        self.assertEqual(result['status'], 'fail')

    def test_exit_two_plain_phrase_on_stdout_or_stderr_is_still_failure(self):
        full_stdout = 'print("usage: verify.py [-h] --images IMAGES\\nverify.py: error: the following arguments are required: --images")\nraise SystemExit(2)\n'
        self.assertEqual(revalidate.run_verify(self.packet(full_stdout))['status'], 'fail')
        for stream in ('sys.stdout', 'sys.stderr'):
            source = 'import sys\nprint("the following arguments are required: --images", file=' + stream + ')\nraise SystemExit(2)\n'
            self.assertEqual(revalidate.run_verify(self.packet(source))['status'], 'fail')

    def test_positional_argument_and_preparse_work_are_not_called_unexecuted(self):
        directory = self.packet('from pathlib import Path\n'
            'Path(__file__).with_name("executed").write_text("ran")\n'
            'import argparse\np=argparse.ArgumentParser()\np.add_argument("payload")\np.parse_args()\n')
        result = revalidate.run_verify(directory)
        self.assertEqual(result['status'], 'invocation_error')
        self.assertEqual(result['required'], ['payload'])
        self.assertEqual((directory/'executed').read_text(), 'ran')

    def test_successful_verifier_still_passes(self):
        result = revalidate.run_verify(self.packet(PASSES))
        self.assertEqual(result['status'], 'pass')


class ReportTests(unittest.TestCase):
    def results(self):
        return [
            {'packet': 'passes', 'has_verify': True, 'has_manifest': False,
             'manifest_check': {'status': 'skipped'},
             'verify_check': {'status': 'pass'}, 'overall': 'pass'},
            {'packet': 'uninvoked', 'has_verify': True, 'has_manifest': True,
             'manifest_check': {'status': 'pass', 'errors': []},
             'verify_check': {'status': 'invocation_error', 'required': ['--images']},
             'overall': 'invocation_error'},
            {'packet': 'fails', 'has_verify': True, 'has_manifest': False,
             'manifest_check': {'status': 'skipped'},
             'verify_check': {'status': 'fail', 'output': 'evidence differs'},
             'overall': 'fail'},
        ]

    def test_uninvoked_packets_are_listed_separately(self):
        temporary = tempfile.TemporaryDirectory(prefix='revalidate-report-')
        self.addCleanup(temporary.cleanup)
        output = Path(temporary.name)
        revalidate.write_reports(output, [], self.results(), 1, 1, 0, 1.0, invocation_error_count=1)
        summary = json.loads((output / 'summary.json').read_text())
        self.assertEqual(summary['invocation_error'], 1)
        self.assertEqual(summary['failed_packets'][0]['packet'], 'fails')
        self.assertEqual(summary['invocation_error_packets'],
                         [{'packet': 'uninvoked', 'required': ['--images']}])
        self.assertEqual(json.loads((output / 'failed.json').read_text()), ['fails'])
        self.assertEqual(json.loads((output / 'invocation-errors.json').read_text()),
                         ['uninvoked'])
        self.assertEqual(json.loads((output / 'passed.json').read_text()), ['passes'])
        self.assertIn('Invocation error', (output / 'README.md').read_text())


class InvocationCliTests(unittest.TestCase):
    def test_real_cli_partition_preserves_failures_and_outputs(self):
        with tempfile.TemporaryDirectory(prefix='invocation-cli-') as temporary:
            root=Path(temporary); scripts=root/'scripts'; scripts.mkdir(); research=root/'research'; research.mkdir()
            (scripts/'revalidate_all.py').write_bytes(Path(revalidate.__file__).read_bytes())
            sources={'pass':PASSES,'fail':FAILS,'needs':REQUIRES_IMAGES,'bad-manifest-needs':REQUIRES_IMAGES,
                     'spoof':'print("the following arguments are required: --images")\nraise SystemExit(2)\n'}
            for name,source in sources.items():
                packet=research/name; packet.mkdir(); (packet/'verify.py').write_text(source)
            bad=research/'bad-manifest-needs'; (bad/'data').write_bytes(b'wrong')
            (bad/'manifest.json').write_text(json.dumps({'data':hashlib.sha256(b'expected').hexdigest()}))
            (research/'empty').mkdir()
            output=root/'report'
            result=subprocess.run([sys.executable,'-B',str(scripts/'revalidate_all.py'),'--output',str(output)],
                                  cwd=root,capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            summary=json.loads((output/'summary.json').read_text()); rows=json.loads((output/'results.json').read_text())
            self.assertEqual((summary['pass'],summary['fail'],summary['invocation_error'],summary['skip_or_inconclusive']), (1,3,1,1))
            self.assertEqual(summary['total_packets'],6)
            self.assertEqual(json.loads((output/'invocation-errors.json').read_text()),['needs'])
            self.assertIn('bad-manifest-needs',json.loads((output/'failed.json').read_text()))
            self.assertEqual({r['packet']:r['overall'] for r in rows}['spoof'],'fail')
            self.assertNotIn('List of packets whose verifier was never invoked',(output/'README.md').read_text())
            verified=subprocess.run([sys.executable,'-B',str(output/'verify.py')],capture_output=True,text=True)
            self.assertEqual(verified.returncode,0,verified.stdout+verified.stderr)

    def test_old_write_reports_call_signature_remains_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)
            revalidate.write_reports(output, [], [], 0, 0, 0, 0.0)
            self.assertEqual(json.loads((output/'summary.json').read_text())['invocation_error'],0)


if __name__ == '__main__':
    unittest.main()
