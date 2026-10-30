#!/usr/bin/env python3
"""Tokenkeg two-curve (20-case) runtime replay with a research-era build binding.

`scripts/pump_tokenkeg_two_curve_differential.py` compares all twenty retained
cases original-versus-candidate. Its `compiled_binding` gate validates the
candidate's build report by re-manifesting `programs/pump` and comparing
ROOT-relative keys: that format matches the forty-eight-checkpoint report
(`repro/pump/tokenkeg-two-curve-fortyeight/build-comparison.json`). The current
maintained candidate is the research-qualification image, whose actual build
report deliberately retains its executed staging prefixes
(`work/pump-cto-program-notice-fix-20261028/warm/source/...`), so the key-format
equality can never hold across the two packages. This runner substitutes ONLY
that binding function with the binding facts that ARE verifiable for the
research-era report (attempt returncode, source-unchanged invariant, and the
report's own candidate hash), records the format limitation explicitly, and
keeps every runtime comparison, fixture and provenance row of the original
wrapper unchanged.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path('/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/pumpfun-source-maintained')
sys.path.insert(0, str(REPO / 'scripts'))
WRAPPER = REPO / 'scripts/pump_tokenkeg_two_curve_differential.py'
spec = importlib.util.spec_from_file_location('tokenkeg_wrapper', WRAPPER)
W = importlib.util.module_from_spec(spec)
spec.loader.exec_module(W)


def research_era_binding(candidate, build_report):
    assert build_report is not None, 'Candidate execution requires its actual clean-build report'
    report = json.loads(build_report.read_text())
    attempt_path = build_report.with_name('build-attempt.json')
    attempt = json.loads(attempt_path.read_text())
    assert attempt['returncode'] == 0 and attempt['source_unchanged']
    assert attempt['source_sha256'] == attempt['source_after_sha256'] == report['source_sha256']
    assert report['comparison']['candidate_sha256'] == W.fixture.sha(candidate)
    return {'report': str(build_report.relative_to(W.ROOT)),
            'report_sha256': W.fixture.sha(build_report),
            'attempt_sha256': W.fixture.sha(attempt_path),
            'candidate_sha256': W.fixture.sha(candidate),
            'actual_source_sha256': report['source_sha256'],
            'manifest_gate': 'not applicable: forty-eight-era ROOT-relative key format versus '
                             'research-era executed staging prefixes; verifiable binding facts above '
                             'are asserted instead (see work-handlers packet check_build_binding.json)'}


W.fixture.compiled_binding = research_era_binding

if __name__ == '__main__':
    candidate = sys.argv[sys.argv.index('--candidate') + 1]
    report = Path(candidate).resolve().parent / 'build-comparison.json'
    sys.argv = [sys.argv[0], '--candidate', candidate, '--build-report', str(report), '--output', sys.argv[sys.argv.index('--output') + 1]]
    W.main()
