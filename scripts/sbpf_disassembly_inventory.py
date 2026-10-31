#!/usr/bin/env python3
"""Bind Blueshift raw disassembly to file offsets and unmodified ELF bytes.

Analyst evidence only: this does not produce a reconstructed executable.
Requires a separately built, pinned blueshift-gg/sbpf checkout.
"""
import argparse
from contextlib import contextmanager
import concurrent.futures
import gzip
import hashlib
import json
import re
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
from analyze import capture_directory, program_names


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_program_names(entries):
    """Preflight every portable output component before workers can write."""
    if not isinstance(entries, list) or not entries:
        raise ValueError('inventory must contain program entries')
    seen = set()
    for entry in entries:
        name = entry.get('name') if isinstance(entry, dict) else None
        reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {
            f'{prefix}{number}' for prefix in ('COM', 'LPT') for number in range(1, 10)
        }
        if (not isinstance(name, str)
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', name)
                or name.endswith('.') or name.split('.', 1)[0].upper() in reserved
                or name.casefold() == 'report.json'):
            raise ValueError(f'unsafe program output name: {name!r}')
        if name.casefold() in seen:
            raise ValueError(f'duplicate program output name: {name!r}')
        seen.add(name.casefold())


@contextmanager
def tool_snapshot(path, expected=None):
    """Execute a private admitted copy, independent of later rebuilds at path."""
    data = path.read_bytes()
    digest = sha(data)
    if expected is not None and digest != expected:
        raise ValueError('assembler/disassembler executable mismatch')
    with tempfile.TemporaryDirectory(prefix='sbpf-admitted-tool-') as directory:
        executable = Path(directory) / 'sbpf'
        executable.write_bytes(data)
        executable.chmod(0o500)
        yield executable, digest
        if executable.read_bytes() != data:
            raise ValueError('admitted tool snapshot changed during execution')


def program_inputs(root):
    """Capture paths for every selected program, in selector order."""
    return [(name, capture_directory(root, name) / 'deployed.so')
            for name in program_names(root)]


def capture_inputs(root):
    """Keep every selected contract, then dependencies not already selected.

    ``capture_directory`` already routes ``donation_relay`` to
    ``evidence/dependencies``, so the dependency sweep below re-finds it. The dependency sweep is
    deduplicated by resolved path (not by name); selector entries are preserved
    even when they alias one file. A genuine name collision still reaches
    ``validate_program_names``.
    """
    inputs = program_inputs(root)
    selected = {path.resolve() for _, path in inputs}
    inputs += [(path.parent.name, path)
               for path in sorted((root / 'evidence/dependencies').glob('*/deployed.so'))
               if path.resolve() not in selected]
    return inputs


def sections(data):
    if data[:7] != b'\x7fELF\x02\x01\x01':
        raise ValueError('expected ELF64 little endian')
    table = struct.unpack_from('<Q', data, 40)[0]
    size, count, names_index = struct.unpack_from('<HHH', data, 58)
    if size != 64 or not count or names_index >= count or table + count * size > len(data):
        raise ValueError('invalid section table')
    rows = [struct.unpack_from('<IIQQQQIIQQ', data, table + i * size) for i in range(count)]
    strings = rows[names_index]
    names = data[strings[4]:strings[4] + strings[5]]
    result = {}
    for row in rows:
        if row[1] != 8 and row[4] + row[5] > len(data):
            raise ValueError('section exceeds file')
        result[names[row[0]:].split(b'\0', 1)[0].decode()] = row
    return result


def inventory(tool, name, path, output):
    data = path.read_bytes()
    elf_sections = sections(data)
    text = elf_sections['.text']
    start, length = text[4:6]
    relocations = {}
    for section in elf_sections.values():
        if section[1] != 9:  # SHT_REL
            continue
        if section[5] % 16:
            raise ValueError('invalid relocation table')
        for pos in range(section[4], section[4] + section[5], 16):
            address, info = struct.unpack_from('<QQ', data, pos)
            if text[3] <= address < text[3] + length:
                relocations[start + address - text[3]] = dict(type=info & 0xffffffff,
                                                            symbol_index=info >> 32)
    if length % 8:
        raise ValueError('unaligned text length')
    with tempfile.TemporaryDirectory(prefix='sbpf-admitted-elf-') as directory:
        snapshot = Path(directory) / 'input.so'
        snapshot.write_bytes(data)
        command = [str(tool), 'disassemble', str(snapshot), '--raw']
        run = subprocess.run(command, capture_output=True, check=True)
        if snapshot.read_bytes() != data:
            raise ValueError(f'{name}: admitted ELF snapshot changed during disassembly')
    (output / (name + '.stderr')).write_bytes(run.stderr)
    lines = run.stdout.decode().splitlines()
    rows = []
    at = start
    for asm in lines:
        if at >= start + length or not asm.strip() or asm.startswith('//'):
            raise ValueError(f'{name}: unaccounted disassembler output at {at}: {asm}')
        opcode, regs, displacement, immediate = struct.unpack_from('<BBhi', data, at)
        size = 16 if opcode == 0x18 else 8
        if at + size > start + length:
            raise ValueError('truncated wide instruction')
        # Raw mode must emit exactly one line per decoded instruction, including lddw.
        if (size == 16) != asm.startswith('lddw '):
            raise ValueError(f'{name}: instruction width disagreement at {at}')
        row = dict(file_offset=at, text_offset=at-start, virtual_address=text[3]+at-start,
                   raw=data[at:at+size].hex(), assembly=asm, opcode=opcode,
                   dst=regs & 15, src=regs >> 4, displacement=displacement, immediate=immediate)
        if opcode & 7 in (5, 6) and opcode not in (0x85, 0x8d, 0x95):
            row['branch_target_file_offset'] = at + 8 + displacement * 8
        if at in relocations:
            row['loader_relocation'] = relocations[at]
        # External relocated calls can also have src=1 and immediate=-1.
        # Do not invent self-calls or function boundaries from those operands.
        if opcode == 0x85 and regs == 0x10 and relocations.get(at, {}).get('type') != 10:
            row['relative_call_target_file_offset'] = at + 8 + immediate * 8
        rows.append(row)
        at += size
    if at != start + length:
        raise ValueError(f'{name}: text coverage ends at {at}, expected {start+length}')
    if run.stderr:
        raise ValueError(f'{name}: disassembler emitted diagnostics; inspect {name}.stderr')
    record = dict(scope='Reference-derived analyst disassembly, not source recovery or a source build',
                  input=str(path.relative_to(ROOT)), input_sha256=sha(data),
                  input_bytes=len(data), text_offset=start, text_bytes=length,
                  text_sha256=sha(data[start:start+length]), instructions=rows)
    encoded = json.dumps(record, separators=(',', ':')).encode()
    compressed = gzip.compress(encoded, mtime=0)
    (output / (name + '.json.gz')).write_bytes(compressed)
    (output / (name + '.s.gz')).write_bytes(gzip.compress(run.stdout, mtime=0))
    return dict(name=name, input=record['input'], input_sha256=sha(data),
                text_sha256=record['text_sha256'], text_bytes=length,
                instruction_count=len(rows), instruction_slots=length//8,
                covered_text_bytes=at-start, diagnostics_bytes=len(run.stderr),
                inventory_sha256=sha(compressed), assembly_sha256=sha(run.stdout))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.tool_source.resolve()
    tool = source / 'target/release/sbpf'
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain', '--untracked-files=no']):
        raise ValueError('tool source has tracked modifications')
    output = args.output.resolve()
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Publish only a complete inventory: a failed program must not leave a
    # partial directory without manifest.json that blocks the next run.
    # A valid output basename can sit at the filesystem's component limit;
    # only the published name has to fit there, so keep the staging prefix short.
    staging = Path(tempfile.mkdtemp(prefix='.' + output.name[:32] + '.', dir=output.parent))
    try:
        inputs = capture_inputs(ROOT)
        validate_program_names([{'name': name} for name, _ in inputs])
        with tool_snapshot(tool) as (executable, tool_digest):
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(inventory, executable, name, path, staging) for name, path in inputs]
                results = [f.result() for f in futures]
            manifest = dict(scope='Complete original-text disassembly; no executable generation or modification',
                        tool_repository='https://github.com/blueshift-gg/sbpf', tool_revision=revision,
                        tool_version=subprocess.check_output([str(executable), '--version'], text=True).strip(),
                        tool_sha256=tool_digest,
                        tool_lockfile_sha256=sha((source / 'Cargo.lock').read_bytes()),
                        generator_sha256=sha(Path(__file__).read_bytes()), programs=results,
                        proves_byte_identical_reconstruction=False)
        (staging / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n',encoding='utf-8',newline='\n')
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
