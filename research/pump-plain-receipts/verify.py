"""Verify retained wire receipts; no VM, source build or network access."""
import gzip
import hashlib
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
sha = lambda value: hashlib.sha256(value).hexdigest()


def main():
    hashes = json.loads((HERE/'receipt-files.json').read_text(encoding='utf-8'))
    for name, digest in hashes.items():
        assert sha((HERE/name).read_bytes()) == digest, name
    transition = json.loads((HERE/'proposed-asset-transition.json').read_text(encoding='utf-8'))
    comparison = json.loads((HERE/'comparison.json').read_text(encoding='utf-8'))
    aliases = {digest: 'PRODUCER_SHA256:'+name for stage in ('before','after')
               for name,digest in transition[stage].items()}

    def normalize(value):
        if isinstance(value,str): return aliases.get(value,value)
        if isinstance(value,list): return [normalize(v) for v in value]
        if isinstance(value,dict): return {k:normalize(v) for k,v in value.items()}
        return value

    retained = {}
    for stage in ('before','after'):
        summary = json.loads((HERE/f'receipts/{stage}-summary.json').read_text(encoding='utf-8'))
        assert summary['revision'] == comparison['tested_revisions'][stage]
        assert summary['stage'] == stage and not summary['errors']
        assert summary['producer_sha256'] == transition[stage]
        retained[stage] = {}
        with tarfile.open(HERE/f'receipts/{stage}-reports.tar.gz') as archive:
            def read(name):
                return archive.extractfile(name).read()
            assert json.loads(read('summary.json')) == summary
            for script in transition[stage]:
                name = Path(script).stem
                payloads = []
                for label,filename in (('plain','report.json'),('gzip','report.json.gz')):
                    wire = read(name+'/'+filename)
                    row = summary['producers'][script][label]
                    assert sha(wire) == row['wire_sha256']
                    assert row['returncode'] == 0
                    compressed = wire.startswith(b'\x1f\x8b')
                    assert compressed == (stage == 'before' or label == 'gzip')
                    if compressed: assert wire[4:8] == bytes(4)
                    decoded = gzip.decompress(wire) if compressed else wire
                    assert sha(decoded) == row['decoded_sha256']
                    payloads.append(decoded)
                assert payloads[0] == payloads[1]
                assert summary['producers'][script]['plain']['plain_reader']['returncode'] == (1 if stage=='before' else 0)
                report = json.loads(payloads[0])
                assert report['candidate_sha256'] == report['original_sha256'] == summary['capture_sha256']
                assert report['cases'] and not report['mismatches']
                assert len(report['cases']) == comparison['comparison'][script]['case_count']
                retained[stage][script] = report
    for script in transition['before']:
        left,right = retained['before'][script],retained['after'][script]
        assert left['cases'] == right['cases']
        assert left.get('calibration') == right.get('calibration')
        assert normalize(left) == normalize(right), script
    assert sum(len(r['cases']) for r in retained['after'].values()) == comparison['total_cases_per_output_format'] == 1366
    print('Retained eleven-producer before/after wire reports verified: 1,366 cases per format.')


if __name__ == '__main__':
    main()
