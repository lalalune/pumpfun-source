#!/usr/bin/env python3
"""Validate reference-derived assembly by reassembling .text, not original ELF identity.

This deliberately uses disassembled target instructions as inputs. Outputs are
tool-validation artifacts and MUST NOT be counted as independent source builds.
"""
import argparse
import concurrent.futures
import gzip
import json
import os
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import stat
import struct
import subprocess
import tempfile

from sbpf_disassembly_inventory import ROOT, sections, sha, tool_snapshot, validate_program_names


# Default/raw mnemonics from crates/assembler/src/sbpf.pest in blueshift-gg/sbpf.
# The assembler
# still validates operands; directives and preprocessor inputs are not admitted.
MNEMONICS = ({op + str(bits) for op in ('add', 'sub', 'mul', 'div', 'mod', 'or', 'and',
                                      'xor', 'mov', 'lsh', 'rsh', 'arsh', 'neg') for bits in (32, 64)}
             | {op + suffix for op in ('jeq', 'jne', 'jgt', 'jge', 'jlt', 'jle', 'jsgt',
                                       'jsge', 'jslt', 'jsle', 'jset') for suffix in ('', '32')}
             | {op + width for op in ('ldx', 'st', 'stx') for width in ('b', 'h', 'w', 'dw')}
             | {order + str(bits) for order in ('be', 'le') for bits in (16, 32, 64)}
             | {'hor64', 'lddw', 'ja', 'call', 'callx', 'exit'})


def validate_instruction(assembly):
    if (not isinstance(assembly, str) or not assembly.split()
            or any(c in assembly for c in '\r\n\v\f\x85\u2028\u2029')
            or not re.fullmatch(r'[A-Za-z0-9_+*/\- \t,\[\]()]+', assembly)
            or '//' in assembly or assembly.split()[0] not in MNEMONICS):
        raise ValueError(f'expected one raw instruction mnemonic: {assembly!r}')


SHT_NOBITS = 8


def _is_link_or_reparse(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_reparse_tag', 0))


def _admitted_original_bytes(root, input_ref):
    if not isinstance(input_ref, str) or not input_ref or '\0' in input_ref:
        raise ValueError(f'unsafe inventory input path: {input_ref!r}')
    posix_ref = PurePosixPath(input_ref)
    windows_ref = PureWindowsPath(input_ref)
    if (input_ref.startswith(('/', '\\'))
            or posix_ref.is_absolute()
            or windows_ref.is_absolute()
            or windows_ref.drive
            or windows_ref.root):
        raise ValueError(f'inventory input path must be relative: {input_ref!r}')
    parts = input_ref.replace('\\', '/').split('/')
    if not parts or any(part in ('', '.', '..') for part in parts):
        raise ValueError(f'unsafe inventory input path: {input_ref!r}')
    root_path = Path(os.path.abspath(root))
    resolved_root = root_path.resolve()
    cursor = root_path
    for index, part in enumerate(parts):
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except OSError as error:
            raise ValueError(f'unreadable inventory input {input_ref!r}: {error}') from error
        if _is_link_or_reparse(info):
            raise ValueError(f'symlinked inventory input is not admitted: {input_ref!r}')
        is_last = index == len(parts) - 1
        if is_last:
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f'non-regular inventory input is not admitted: {input_ref!r}')
        elif not stat.S_ISDIR(info.st_mode):
            raise ValueError(f'non-directory ancestor in inventory input: {input_ref!r}')
    resolved = cursor.resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f'inventory input resolves outside repository: {input_ref!r}')
    return resolved.read_bytes()


def _text_section_bytes(blob, label):
    secs = sections(blob)
    if '.text' not in secs:
        raise ValueError(f'{label}: missing .text section')
    sec = secs['.text']
    if sec[1] == SHT_NOBITS:
        raise ValueError(f'{label}: .text section is SHT_NOBITS')
    offset, size = sec[4], sec[5]
    if offset < 0 or size < 0 or offset + size > len(blob):
        raise ValueError(f'{label}: .text section exceeds file')
    return blob[offset:offset + size]


def _validate_rows(name, rows):
    if not isinstance(rows, list):
        raise ValueError(f'{name}: instructions must be a list')
    previous_offset = -1
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f'{name}: instruction row must be an object')
        for field in ('file_offset', 'opcode', 'src', 'immediate'):
            value = row.get(field)
            if type(value) is not int:
                raise ValueError(f'{name}: instruction {field} must be an integer')
        at = row['file_offset']
        if at < 0 or at <= previous_offset:
            raise ValueError(f'{name}: instruction file_offset must be non-negative and strictly increasing')
        previous_offset = at


def roundtrip(tool, inventory, entry, output):
    validate_program_names([entry])
    name = entry['name']
    compressed = (inventory / (name + '.json.gz')).read_bytes()
    if sha(compressed) != entry['inventory_sha256']:
        raise ValueError('inventory hash mismatch')
    record = json.loads(gzip.decompress(compressed))
    if not isinstance(record, dict):
        raise ValueError(f'{name}: inventory record must be an object')
    rows = record.get('instructions')
    _validate_rows(name, rows)
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
        asm = row.get('assembly')
        validate_instruction(asm)
        if row['opcode'] == 0x85 and row['src'] == 1:
            asm = 'call ' + labels[at + 8 + row['immediate'] * 8]
        lines.append(asm)
    original = _admitted_original_bytes(ROOT, record.get('input'))
    if sha(original) != record.get('input_sha256'):
        raise ValueError('original hash mismatch')
    if len(original) < 64:
        raise ValueError('truncated original ELF header')
    expected = _text_section_bytes(original, f'{name} original')
    flags = struct.unpack_from('<I', original, 48)[0]
    if flags not in (0, 3):
        raise ValueError(f'unsupported assembler architecture flags {flags}')
    # No .byte/.quad/incbin directives: actual instruction mnemonics are assembled.
    assembly = ('\n'.join(lines) + '\n').encode()
    folder = output / name
    folder.mkdir()
    source = folder / 'reference-derived.s'
    source.write_bytes(assembly)
    command = [str(tool), 'build', '--arch', 'v0' if flags == 0 else 'v3',
               '--input', str(source), '--deploy-dir', str(folder / 'assembled')]
    result = subprocess.run(command, capture_output=True)
    log = result.stdout + result.stderr
    (folder / 'build.log').write_bytes(log)
    if result.returncode:
        # A failed run discards its staging directory, including this log.
        raise ValueError(f'{name}: assembler exited {result.returncode}: '
                         + log.decode(errors='replace'))
    candidate = (folder / 'assembled/reference-derived.so').read_bytes()
    text = _text_section_bytes(candidate, f'{name} candidate')
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
    manifest_bytes = (inventory / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    if not manifest.get('programs'):
        parser.error('inventory must contain at least one program to validate')
    validate_program_names(manifest['programs'])
    tool = args.tool_source.resolve() / 'target/release/sbpf'
    output = args.output.resolve()
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Publish only a finished run: a raising program must not leave a partial
    # directory without report.json that blocks the next run. A valid output
    # basename can sit at the filesystem's component limit; only the published
    # name has to fit there, so keep the staging prefix short.
    staging = Path(tempfile.mkdtemp(prefix='.' + output.name[:32] + '.', dir=output.parent))
    try:
        with tool_snapshot(tool, manifest['tool_sha256']) as (executable, _):
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(roundtrip, executable, inventory, entry, staging)
                           for entry in manifest['programs']]
                results = [future.result() for future in futures]
        report = dict(scope='Reference-derived assembly tooling validation; not independent contract reconstruction',
                      tool_sha256=manifest['tool_sha256'], tool_revision=manifest['tool_revision'],
                      inventory_manifest_sha256=sha(manifest_bytes),
                      generator_sha256=sha(Path(__file__).read_bytes()),
                      programs=results, all_text_roundtrips_exact=all(r['full_text_equality'] for r in results),
                      counts_toward_source_reconstruction_acceptance=False)
        (staging / 'report.json').write_text(json.dumps(report, indent=2) + '\n',encoding='utf-8',newline='\n')
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(json.dumps(report, indent=2))
    return 0 if report['all_text_roundtrips_exact'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
