#!/usr/bin/env python3
"""Resolve defined dynamic call targets in fresh static roadmap diagnostics."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
REVIEWED = {
    'scripts/reconstruction_roadmap.py': '529e187a98c05fc83cb17b80972594897d23a9eef75e30cb55b76341b05bc88a',
    'scripts/window_elf_reader.py': 'd3b57510531d7977110e73474cf89310b68bf6705d134ffb3bc759e18d30bedd',
    'research/tooling-roadmap-call-classification-20261029/proof.py': '4acff7a33fff43773b730b4518a8beb8685abc683740945f27c9296ab4031800',
}


def load_sources(root):
    modules, bindings, admitted = [], {}, {}
    # Admit every source before executing any of them.
    for name, expected in REVIEWED.items():
        raw = (root / name).read_bytes()
        if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != expected:
            raise ValueError(f'unreviewed source: {name}')
        bindings[name] = hashlib.sha256(raw).hexdigest()
        admitted[name] = raw
    sys.path.insert(0, str(root / 'scripts'))
    for index, name in enumerate(REVIEWED):
        module = types.ModuleType(f'reviewed_dynamic_calls_{index}')
        module.__file__ = str(root / name)
        exec(compile(admitted[name], module.__file__, 'exec'), module.__dict__)
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
    root, output = Path(root).resolve(), Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('output already exists; preserve prior packets')
    roadmap, reader, proof, bindings = load_sources(root)
    roadmap.Elf = resolved_reader(reader)
    classify = classifier(roadmap)
    roadmap.analyze_window_patterns = lambda elf, start, end: proof.window_patterns(
        roadmap, elf, start, end, classify)
    # Match the other maintained roadmap adapters: publish only the complete
    # roadmap plus this adapter's attribution, without replacing a late writer.
    from deep_disassembly import rename_directory, temporary_sibling
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = temporary_sibling(output, 'staging')
    try:
        roadmap.generate_roadmap(stage)
        bindings['adapter_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        (stage / 'dynamic-call-inputs.json').write_text(json.dumps(bindings, indent=2) + '\n',
                                                                   encoding='utf-8', newline='\n')
        manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.iterdir())
                    if p.is_file() and p.name != 'manifest.json'}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n',
                                                   encoding='utf-8', newline='\n')
        rename_directory(stage, output)
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        generate(args.repo, args.output)
    except ValueError as error:
        parser.exit(1, str(error) + '\n')
