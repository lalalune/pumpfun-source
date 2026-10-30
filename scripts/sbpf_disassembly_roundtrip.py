#!/usr/bin/env python3
"""Validate reference-derived assembly by reassembling .text, not original ELF identity.

This deliberately uses disassembled target instructions as inputs. Outputs are
tool-validation artifacts and MUST NOT be counted as independent source builds.
"""
import argparse
import concurrent.futures
import gzip
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

from sbpf_disassembly_inventory import ROOT, sections, sha


def roundtrip(tool, inventory, entry, output):
    name = entry['name']
    compressed = (inventory / (name + '.json.gz')).read_bytes()
    if sha(compressed) != entry['inventory_sha256']:
        raise ValueError('inventory hash mismatch')
    record = json.loads(gzip.decompress(compressed))
    rows = record['instructions']
    offsets = {row['file_offset'] for row in rows}
    labels = {}
    for row in rows:
        if row['opcode'] == 0x85 and row['src'] == 1:
            # For this instruction encoding check, preserve even a relocated
            # call's placeholder immediate. No original relocations are linked.
            target = row['file_offset'] + 8 + row['immediate'] * 8
            if target not in offsets:
                raise ValueError(f'{name}: numeric call does not target an instruction')
            labels[target] = f'fn_{target:x}'
    lines = []
    for row in rows:
        at = row['file_offset']
        if at in labels:
            lines.append(labels[at] + ':')
        asm = row['assembly']
        if row['opcode'] == 0x85 and row['src'] == 1:
            asm = 'call ' + labels[at + 8 + row['immediate'] * 8]
        lines.append(asm)
    # No .byte/.quad/incbin directives: actual instruction mnemonics are assembled.
    assembly = ('\n'.join(lines) + '\n').encode()
    folder = output / name
    folder.mkdir()
    source = folder / 'reference-derived.s'
    source.write_bytes(assembly)
    original = (ROOT / record['input']).read_bytes()
    if sha(original) != record['input_sha256']:
        raise ValueError('original hash mismatch')
    flags = struct.unpack_from('<I', original, 48)[0]
    if flags not in (0, 3):
        raise ValueError(f'unsupported assembler architecture flags {flags}')
    command = [str(tool), 'build', '--arch', 'v0' if flags == 0 else 'v3',
               '--input', str(source), '--deploy-dir', str(folder / 'assembled')]
    result = subprocess.run(command, capture_output=True)
    (folder / 'build.log').write_bytes(result.stdout + result.stderr)
    result.check_returncode()
    candidate = (folder / 'assembled/reference-derived.so').read_bytes()
    section = sections(candidate)['.text']
    text = candidate[section[4]:section[4] + section[5]]
    target = sections(original)['.text']
    expected = original[target[4]:target[4] + target[5]]
    return dict(name=name, original_sha256=sha(original), assembly_sha256=sha(assembly),
                reassembled_elf_sha256=sha(candidate), original_text_bytes=len(expected),
                assembled_text_bytes=len(text), original_text_sha256=sha(expected),
                assembled_text_sha256=sha(text), full_text_equality=text == expected,
                full_elf_equality=original == candidate,
                differing_text_positions=sum(x != y for x, y in zip(text, expected)),
                text_length_difference=len(text)-len(expected),
                independent_source_reconstruction=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-source', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inventory = args.inventory.resolve()
    manifest = json.loads((inventory / 'manifest.json').read_text())
    if not manifest.get('programs'):
        parser.error('inventory must contain at least one program to validate')
    tool = args.tool_source.resolve() / 'target/release/sbpf'
    if sha(tool.read_bytes()) != manifest['tool_sha256']:
        raise ValueError('assembler/disassembler executable mismatch')
    output = args.output.resolve()
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Publish only a finished run: a raising program must not leave a partial
    # directory without report.json that blocks the next run.
    staging = Path(tempfile.mkdtemp(prefix='.' + output.name + '.', dir=output.parent))
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(roundtrip, tool, inventory, entry, staging)
                       for entry in manifest['programs']]
            results = [future.result() for future in futures]
        report = dict(scope='Reference-derived assembly tooling validation; not independent contract reconstruction',
                      tool_sha256=manifest['tool_sha256'], tool_revision=manifest['tool_revision'],
                      inventory_manifest_sha256=sha((inventory / 'manifest.json').read_bytes()),
                      generator_sha256=sha(Path(__file__).read_bytes()),
                      programs=results, all_text_roundtrips_exact=all(r['full_text_equality'] for r in results),
                      counts_toward_source_reconstruction_acceptance=False)
        (staging / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(json.dumps(report, indent=2))
    return 0 if report['all_text_roundtrips_exact'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
