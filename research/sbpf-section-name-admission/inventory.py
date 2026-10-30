#!/usr/bin/env python3
"""Run the archived disassembly inventory with unambiguous section-name lookup."""
import hashlib
from pathlib import Path
import struct
import types

ROOT = Path(__file__).resolve().parents[2]
ARCHIVED_SHA256 = '831cee56ca07bba6be4b057dcf33873319e63cc27aa3d7b45a7f2ab66adaee6c'


def load_inventory(root=ROOT):
    path = root / 'scripts/sbpf_disassembly_inventory.py'
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != ARCHIVED_SHA256:
        raise ValueError('archived disassembly inventory source drift')
    module = types.ModuleType('archived_sbpf_inventory')
    module.__file__ = str(path)
    exec(compile(source, str(path), 'exec'), module.__dict__)
    reader = module.sections

    def sections(data):
        result = reader(data)
        count = struct.unpack_from('<H', data, 60)[0]
        if len(result) != count:
            raise ValueError('duplicate section names cannot be represented by inventory')
        return result

    module.sections = sections
    # ROOT was initialized from the archived location. The emitted generator
    # hash must identify this actual entrypoint and its admission rule.
    module.__file__ = __file__
    return module


if __name__ == '__main__':
    load_inventory().main()
