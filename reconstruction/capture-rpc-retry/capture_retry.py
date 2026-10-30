"""Retryable RPC capture using a hash-bound, in-memory archived-source adapter."""
import hashlib
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA256 = '329eaa1bda93034ee4147b4a6a3bea66ddd5403c1e79bc591c58fc75942a8465'
source_path = ROOT / 'scripts/capture.py'
raw = source_path.read_bytes()
if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
    raise ValueError('archived capture source changed; review the adapter before use')

module = types.ModuleType('capture_rpc_retry')
module.__file__ = str(source_path)
text = raw.decode('utf-8')
anchor = "            if 'error' in result: raise RuntimeError(result['error'])"
replacement = """            check(isinstance(result, dict), 'RPC response must be an object')
            check(result.get('jsonrpc') == '2.0', 'unexpected RPC protocol version')
            response_id = result.get('id')
            check(type(response_id) in (int, float) and response_id == 1,
                  'RPC response ID does not match request')
""" + anchor
if text.count(anchor) != 1:
    raise ValueError('reviewed RPC envelope substitution is not unique')
text = text.replace(anchor, replacement)
exec(compile(text, str(source_path), 'exec', optimize=0), module.__dict__)
capture = module.capture


_archived_rpc = module.rpc


def contextual_rpc(url, method, params):
    result = _archived_rpc(url, method, params)
    if method == 'getAccountInfo':
        slot = result.get('context', {}).get('slot') if isinstance(result, dict) else None
        if type(slot) is not int or slot < 0:
            raise ValueError('account response requires a nonnegative integer context slot')
        options = params[1] if len(params) > 1 else None
        minimum = options.get('minContextSlot') if isinstance(options, dict) else None
        if minimum is not None and slot < minimum:
            raise ValueError('account response context slot is below requested minContextSlot')
    return result


module.rpc = contextual_rpc
