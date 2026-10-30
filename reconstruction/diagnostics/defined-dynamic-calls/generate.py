#!/usr/bin/env python3
"""Resolve defined dynamic call targets in fresh static roadmap diagnostics."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
REVIEWED = {
    'scripts/reconstruction_roadmap.py': '7ff87816fe95ceb4b4f3540a34256a5a906665fc9cbe6ae42852c64c27b75f4e',
    'scripts/window_elf_reader.py': 'df1c2b1369e996146f05bd9f9714b112a013550fa25d1206f6b29e3ef079dd74',
    'research/tooling-roadmap-call-classification-20261029/proof.py': '4acff7a33fff43773b730b4518a8beb8685abc683740945f27c9296ab4031800',
}


def load_sources(root):
    modules, bindings = [], {}
    # Admit every source before executing any of them.
    for name, expected in REVIEWED.items():
        raw = (root / name).read_bytes()
        if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != expected:
            raise ValueError(f'unreviewed source: {name}')
        bindings[name] = hashlib.sha256(raw).hexdigest()
    sys.path.insert(0, str(root / 'scripts'))
    for index, name in enumerate(REVIEWED):
        module = types.ModuleType(f'reviewed_dynamic_calls_{index}')
        module.__file__ = str(root / name)
        exec(compile((root / name).read_bytes(), module.__file__, 'exec'), module.__dict__)
        modules.append(module)
    return (*modules, bindings)


def resolved_reader(legacy):
    class Elf(legacy.Elf):
        def __init__(self, path):
            super().__init__(path)
            # The retained inputs use one address/file-offset space. Refuse to
            # extend the archived reader's assumptions to other ELF layouts.
            if self.text[3] != self.lo:
                raise ValueError('non-identity-mapped text is not qualified')
            self.external_symbols, self.defined_calls = {}, {}
            relocations, symbols = self.secs.get('.rel.dyn'), self.secs.get('.dynsym')
            if not relocations or not symbols:
                return
            text_index = self.raw.index(self.text)
            for position in range(relocations[4], relocations[4] + relocations[5], 16):
                at, info = struct.unpack_from('<QQ', self.b, position)
                if info & 0xffffffff != 10 or not self.lo <= at <= self.hi - 8 or self.b[at] != 0x85:
                    continue
                index = info >> 32
                if index * 24 + 24 > symbols[5]:
                    raise ValueError('dynamic symbol index exceeds its section')
                _, kind, _, section, target, size = struct.unpack_from('<IBBHQQ', self.b, symbols[4] + index * 24)
                if section == 0:
                    self.external_symbols[at] = self.symbols.get(index) or f'symbol_{index}'
                elif section == text_index and kind & 15 == 2 and size > 0 and self.lo <= target < self.hi and target % 8 == 0:
                    self.defined_calls[at] = target
            self.calls.update(self.defined_calls)
            # Entries, relocation patterns and normalized bytes remain exactly
            # those supplied by the archived reader; this is diagnostic topology.
    return Elf


def classifier(archived):
    original = archived.classify_instruction

    def classify(data, offset, elf):
        if offset + 8 > len(data):
            return 'truncated'
        if data[offset] == 0x8d:
            return 'call_indirect'
        if data[offset] != 0x85:
            return original(data, offset, elf)
        if offset in elf.external_symbols:
            return 'syscall_' + elf.external_symbols[offset]
        if offset in elf.defined_calls:
            return 'call_internal'
        if elf.relocations.get(offset, {}).get('type') == 10:
            return 'call_unresolved_dynamic'
        source = data[offset + 1] >> 4
        if source == 1:
            return 'call_internal'
        if source == 0:
            return 'syscall_' + str(struct.unpack_from('<i', data, offset + 4)[0])
        return 'call_other'
    return classify


def generate(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('output already exists; preserve prior packets')
    roadmap, reader, proof, bindings = load_sources(root)
    roadmap.Elf = resolved_reader(reader)
    classify = classifier(roadmap)
    roadmap.analyze_window_patterns = lambda elf, start, end: proof.window_patterns(
        roadmap, elf, start, end, classify)
    roadmap.generate_roadmap(output)
    bindings['adapter_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (output / 'dynamic-call-inputs.json').write_text(json.dumps(bindings, indent=2) + '\n', encoding='utf-8')
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())
                if p.is_file() and p.name != 'manifest.json'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        generate(args.repo, args.output)
    except ValueError as error:
        parser.exit(1, str(error) + '\n')
