"""Run the same actual audits with explicit expectations for two reviewed revisions."""
import hashlib
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'reconstruction/pump-main/lanes/callgraph-census/census.py'
expectations = {
    '111126000016915fd46fd93b116444b356cd8f63c65f5e9a951498f21f6d3bb4': 'before',
    '41a3030431363847bc56183da6d51604c0b5c45017cb2e5ba8d8eb83cce570d4': 'after',
}
expected = expectations[hashlib.sha256(source.read_bytes()).hexdigest()]
proof = Path(__file__).with_name('reproduce.py')
sys.argv = [str(proof), '--repo-root', str(ROOT), '--out', str(ROOT / 'work/scoped-proof'),
            '--expect', expected]
runpy.run_path(str(proof), run_name='__main__')
