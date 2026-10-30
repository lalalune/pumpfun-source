"""Retryable RPC capture using a hash-bound, in-memory archived-source adapter."""
import hashlib
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA256 = '71e28a5fb815a45664f06d6902ef1437f469a4d3c99a00e221efe583daa11905'
source_path = ROOT / 'scripts/capture.py'
raw = source_path.read_bytes()
if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
    raise ValueError('archived capture source changed; review the adapter before use')

lines = []
deferred = {}
for line in raw.decode('utf-8').splitlines(keepends=True):
    indent = line[:len(line) - len(line.lstrip())]
    if line == '    out.mkdir(parents=True,exist_ok=False)\n':
        lines.append('    if out.exists(): raise FileExistsError(out)\n')
    elif line.lstrip().startswith("(out/'program-account.bin').write_bytes"):
        deferred[indent] = line
    else:
        lines.append(line)
        if line.lstrip().startswith('report='):
            lines.extend([indent + 'out.mkdir(parents=True,exist_ok=False)\n',
                          deferred.pop(indent)])
if deferred:
    raise ValueError('capture write adaptation is incomplete')

module = types.ModuleType('capture_rpc_retry')
module.__file__ = str(source_path)
exec(compile(''.join(lines), str(source_path), 'exec', optimize=0), module.__dict__)
capture = module.capture
