"""Retryable RPC capture using a hash-bound, in-memory archived-source adapter."""
import ast
import ctypes
import errno
import hashlib
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA256 = '44bf6a2cdc987eeea9c5947bdd89f9b9fbd263d62cbc4876966125f1f5d3a482'
source_path = ROOT / 'scripts/capture.py'
raw = source_path.read_bytes()
if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
    raise ValueError('archived capture source changed; review the adapter before use')

# Since 77e3ff4ce the archived capture publishes through
# deep_disassembly.rename_directory (native no-replace rename). Admit only that
# function's reviewed source, not the whole analysis module and its imports, so
# the adapter still executes nothing but hash-bound bytes.
RENAME_PATH = ROOT / 'scripts/deep_disassembly.py'
RENAME_SHA256 = '36cbb216db93f59f699edbd8c46f798f8fdbf180bfcfa20fefd2a645a06d6cde'
rename_text = RENAME_PATH.read_bytes().decode('utf-8')
rename_nodes = [node for node in ast.parse(rename_text).body
                if isinstance(node, ast.FunctionDef) and node.name == 'rename_directory']
rename_source = ast.get_source_segment(rename_text, rename_nodes[0]) if len(rename_nodes) == 1 else None
if rename_source is None or hashlib.sha256(rename_source.encode('utf-8')).hexdigest() != RENAME_SHA256:
    raise ValueError('reviewed no-replace rename changed; review the adapter before use')
rename_namespace = {'__builtins__': __builtins__, 'ctypes': ctypes, 'errno': errno, 'os': os, 'sys': sys}
exec(compile(rename_source, str(RENAME_PATH), 'exec', optimize=0), rename_namespace)

module = types.ModuleType('capture_rpc_retry')
module.__file__ = str(source_path)
module.rename_directory = rename_namespace['rename_directory']
text = raw.decode('utf-8')
rename_import = "        from deep_disassembly import rename_directory\n"
if text.count(rename_import) != 1:
    raise ValueError('reviewed no-replace rename import is not unique')
text = text.replace(rename_import, '')
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
metadata_checks = {
    "after,p2=account(url,key,before['context']['slot']); check(p==p2)":
        "after,p2=account(url,key,before['context']['slot']); check(p==p2); check(account_metadata_matches(after, before, True), 'deployment account metadata changed during capture')",
    "    after,p2=account(url,key,data['context']['slot'])":
        "    after,p2=account(url,key,data['context']['slot'])\n    check(account_metadata_matches(after, before, True), 'deployment account metadata changed during capture')",
    "    check(p==p2 and base64.b64decode(meta['value']['data'][0])==d[:45], 'deployment changed during capture')":
        "    check(account_metadata_matches(meta, data, False), 'programdata account metadata changed during capture')\n    check(p==p2 and base64.b64decode(meta['value']['data'][0])==d[:45], 'deployment changed during capture')",
}
for anchor, replacement in metadata_checks.items():
    if text.count(anchor) != 1:
        raise ValueError('reviewed account metadata substitution is not unique')
    text = text.replace(anchor, replacement)


def account_metadata_matches(current, previous, executable):
    value = current.get('value') if isinstance(current, dict) else None
    return (isinstance(value, dict) and value.get('owner') == previous['value']['owner']
            and value.get('executable') is executable)


module.account_metadata_matches = account_metadata_matches
slot_anchor = "    slot=struct.unpack_from('<Q',d,4)[0]; payload=d[45:]; check(payload[:4]==b'\\x7fELF')"
if text.count(slot_anchor) != 1:
    raise ValueError('reviewed deployment-slot substitution is not unique')
text = text.replace(slot_anchor, slot_anchor + "\n    check(slot <= before['context']['slot'], 'deployment slot is newer than initial capture context')")
exec(compile(text, str(source_path), 'exec', optimize=0), module.__dict__)
capture = module.capture


_archived_rpc = module.rpc


def contextual_rpc(url, method, params):
    result = _archived_rpc(url, method, params)
    if method == 'getAccountInfo':
        value = result.get('value') if isinstance(result, dict) else None
        if value is not None:
            data = value.get('data') if isinstance(value, dict) else None
            if (not isinstance(data, list) or len(data) != 2
                    or not isinstance(data[0], str) or data[1] != 'base64'):
                raise ValueError('account response requires a base64 data tuple')
        context = result.get('context') if isinstance(result, dict) else None
        slot = context.get('slot') if isinstance(context, dict) else None
        if type(slot) is not int or not 0 <= slot < 2**64:
            raise ValueError('account response requires a u64 integer context slot')
        options = params[1] if len(params) > 1 else None
        minimum = options.get('minContextSlot') if isinstance(options, dict) else None
        if minimum is not None and (type(minimum) is not int or not 0 <= minimum < 2**64):
            raise ValueError('account response minContextSlot must be a u64 integer')
        if minimum is not None and slot < minimum:
            raise ValueError('account response context slot is below requested minContextSlot')
    return result


module.rpc = contextual_rpc
