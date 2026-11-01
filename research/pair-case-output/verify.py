"""Verify retained preflight observations; no compiler, VM or network use."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O, -OO or PYTHONOPTIMIZE.')
import gzip
import hashlib
import json
from pathlib import Path
import tarfile

HERE=Path(__file__).resolve().parent


def main():
    hashes=json.loads((HERE/'receipt-files.json').read_text(encoding='utf-8'))
    for name,digest in hashes.items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
    transition=json.loads((HERE/'transition.json').read_text(encoding='utf-8'))
    comparison=json.loads((HERE/'comparison.json').read_text(encoding='utf-8'))
    originals=[]
    for stage in ('before','after'):
        summary=json.loads((HERE/f'receipts/{stage}-summary.json').read_text(encoding='utf-8'))
        assert summary['stage']==stage
        assert summary['revision']==comparison['tested_revisions'][stage]
        assert summary['paired_build_sha256']==transition[stage]
        assert all(row['returncode']==0 for row in summary['tests'])
        originals.append(summary['original_source'])
        with tarfile.open(HERE/f'receipts/{stage}-observations.tar.gz') as archive:
            assert json.load(archive.extractfile('summary.json'))==summary
            for label,observed in summary['rows'].items():
                row=json.load(archive.extractfile(label+'.json'))
                assert row['real_case_alias_verified'] is True
                assert row['returncode']==2
                assert {key:row[key] for key in observed}==observed
                assert row['source_before']['base']==row['source_before']['candidate']==summary['original_source']
                actual_unchanged={name:row['source_before'][name]==row['source_after'][name] for name in ('base','candidate')}
                assert actual_unchanged==row['source_unchanged']
                overlap='output must not overlap a Pump source tree' in row['stderr']
                if label=='disjoint-control':
                    assert not overlap and 'missing-hybrid' in row['stderr']
                    assert row['scoring_original_exists'] and all(actual_unchanged.values())
                elif stage=='before' and label.endswith('case-alias'):
                    selected='base' if label.startswith('base') else 'candidate'
                    assert not overlap and 'missing-hybrid' in row['stderr']
                    assert row['output_exists'] and row['scoring_original_exists']
                    assert actual_unchanged[selected] is False
                    assert actual_unchanged['candidate' if selected=='base' else 'base'] is True
                    old={item['path']:item for item in row['source_before'][selected]['files']}
                    new={item['path']:item for item in row['source_after'][selected]['files']}
                    assert all(new.get(name)==value for name,value in old.items())
                    assert 'new-evidence/scoring-inputs/original.so' in new.keys()-old.keys()
                else:
                    assert overlap and all(actual_unchanged.values())
                    assert row['output_exists']==row['output_existed']
    assert originals[0]==originals[1], 'different source inputs in before/after observations'
    print('Both real Mac preflight runs, six scenarios each, and original source inventories verified.')


if __name__=='__main__':main()
