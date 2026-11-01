#!/usr/bin/env python3
"""Recount defined dynamic calls in the complete retained-input disassembly CLI."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

PROGRAMS = ('pump', 'pump_amm', 'pump_fees', 'mayhem', 'donation_relay')
SOURCES = ('deep_disassembly.py', 'window_elf_reader.py', 'analyze_program.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def raw_calls(blob):
    """Read linked symbol/relocation tables without importing the producer."""
    table_at = struct.unpack_from('<Q', blob, 40)[0]
    size, count, names_index = struct.unpack_from('<HHH', blob, 58)
    sections = [struct.unpack_from('<IIQQQQIIQQ', blob, table_at + index * size)
                for index in range(count)]
    strings = sections[names_index]
    names = blob[strings[4]:strings[4] + strings[5]]
    named = {names[section[0]:names.index(0, section[0])].decode(): (index, section)
             for index, section in enumerate(sections)}
    text_index, text = named['.text']
    relocation = named['.rel.dyn'][1]
    symbol = sections[relocation[6]]
    string_section = sections[symbol[6]]
    strings = blob[string_section[4]:string_section[4] + string_section[5]]
    require(symbol[1] == 11 and symbol[9] == 24 and relocation[9] == 16,
            'retained table format changed')
    instructions = set()
    position = text[4]
    while position < text[4] + text[5]:
        instructions.add(position)
        position += 16 if blob[position] == 0x18 else 8
    dynamic, defined, undefined = {}, [], []
    for position in range(relocation[4], relocation[4] + relocation[5], 16):
        address, info = struct.unpack_from('<QQ', blob, position)
        if info & 0xffffffff != 10:
            continue
        index = info >> 32
        symbol_at = symbol[4] + index * 24
        name, kind, _, section, value, length = struct.unpack_from('<IBBHQQ', blob, symbol_at)
        label = strings[name:strings.index(0, name)].decode()
        offset = text[4] + address - text[3]
        require(offset in instructions and blob[offset] == 0x85, 'invalid call site')
        dynamic[offset] = label
        row = {'call_offset': hex(offset), 'symbol': label, 'symbol_index': index,
               'symbol_type': kind & 15, 'section_index': section,
               'symbol_value': hex(value), 'symbol_size': length,
               'call_bytes': blob[offset:offset + 8].hex(),
               'relocation_bytes': blob[position:position + 16].hex(),
               'dynamic_symbol_bytes': blob[symbol_at:symbol_at + 24].hex()}
        target = text[4] + value - text[3]
        if (section == text_index and kind & 15 == 2 and value > 0 and length > 0
                and target in instructions
                and (target + length in instructions or target + length == text[4] + text[5])):
            row['target_offset'] = hex(target)
            defined.append(row)
        elif section == 0:
            undefined.append(row)
    direct = sum(blob[at] == 0x85 and blob[at + 1] >> 4 == 1 and at not in dynamic
                 for at in instructions)
    return {'defined': defined, 'undefined_count': len(undefined),
            'dynamic_calls': len(dynamic), 'direct_calls': direct,
            'logical_instructions': len(instructions)}


def unrelated_hashes(output, witnesses):
    sites = {row['call_offset'] for row in witnesses}
    windows = {row['window_address'] for row in witnesses}
    symbols = {row['symbol'] for row in witnesses}
    hashes = {}
    for path in sorted(output.iterdir()):
        if path.name == 'manifest.json':
            continue
        data = path.read_bytes()
        if path.name == 'disassembly.json.gz':
            value = json.loads(gzip.decompress(data))
            for window in value:
                for insn in window['instructions']:
                    if insn['addr'] in sites:
                        insn['mnemonic'] = 'DEFINED_CALL'
            data = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
        elif path.suffix == '.json':
            value = json.loads(data)
            if path.name == 'windows-deep.json':
                for window in value:
                    if window['address'] in windows:
                        del window['internal_calls']
                        window['extern_calls'] = [name for name in window['extern_calls']
                                                  if name not in symbols]
            elif path.name == 'summary.json':
                del value['total_internal_calls']
                del value['total_extern_calls']
                for name in symbols:
                    value['extern_breakdown'].pop(name, None)
            elif path.name == 'extern-usage.json':
                for name in symbols:
                    value.pop(name, None)
            data = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
        elif path.name == 'README.md':
            data = '\n'.join(line for line in data.decode().splitlines()
                             if not line.startswith(('| Internal calls |', '| External calls |'))).encode()
        hashes[path.name] = sha(data)
    return hashes


def analyzer_unrelated_hashes(output, witness):
    hashes = {}
    for path in sorted(output.iterdir()):
        if path.name == 'manifest.json':
            continue
        data = path.read_bytes()
        if path.suffix == '.json':
            value = json.loads(data)
            if path.name == 'window-inventory.json':
                for window in value:
                    if window['address'] == witness['window_address']:
                        del window['calls_out'], window['call_targets']
                    if window['address'] == witness['target_offset']:
                        del window['calls_in'], window['callers']
            elif path.name == 'summary.json':
                del value['total_call_edges']
            elif path.name == 'call-graph.json':
                value = [edge for edge in value if not (
                    edge['from'] == witness['window_address']
                    and edge['to'] == witness['target_offset'])]
            data = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
        elif path.name == 'README.md':
            data = '\n'.join(line for line in data.decode().splitlines()
                             if not line.startswith('| Total call edges |')).encode()
        hashes[path.name] = sha(data)
    return hashes


def collect(repo, *, revision=None, expected='fixed'):
    repo = Path(repo).resolve()
    sources = {name: subprocess.check_output(['git', '-C', str(repo), 'show',
               f'{revision}:scripts/{name}']) if revision else (repo / 'scripts' / name).read_bytes()
               for name in SOURCES}
    paths = {name: Path('evidence') / ('dependencies' if name == 'donation_relay' else 'original')
             / name / 'deployed.so' for name in PROGRAMS}
    inputs = {name: (repo / path).read_bytes() for name, path in paths.items()}
    idls = {path.relative_to(repo): path.read_bytes() for name in PROGRAMS
            if (path := repo / 'evidence/upstream' / (name + '.json')).is_file()}
    result = {'expectation': expected, 'source_sha256': {name: sha(data) for name, data in sources.items()},
              'input_sha256': {name: sha(data) for name, data in inputs.items()},
              'idl_sha256': {str(path): sha(data) for path, data in idls.items()}, 'programs': {}}
    with tempfile.TemporaryDirectory(prefix='deep-defined-calls-') as temporary:
        root = Path(temporary)
        for name, data in sources.items():
            path = root / 'scripts' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for path, data in {**{paths[name]: data for name, data in inputs.items()}, **idls}.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for name, blob in inputs.items():
            raw = raw_calls(blob)
            require(len(raw['defined']) == 1, 'retained defined-call census changed')
            output = root / 'packets' / name
            run = subprocess.run([sys.executable, '-B', str(root / 'scripts/deep_disassembly.py'),
                                  '--program', name, '--output', str(output)], cwd=root,
                                 capture_output=True, text=True, timeout=90)
            require(run.returncode == 0, run.stdout + run.stderr)
            verify = subprocess.run([sys.executable, '-B', str(output / 'verify.py')], cwd=root,
                                    capture_output=True, text=True, timeout=30)
            require(verify.returncode == 0, verify.stdout + verify.stderr)
            windows = json.loads((output / 'windows-deep.json').read_bytes())
            disassembly = json.loads(gzip.decompress((output / 'disassembly.json.gz').read_bytes()))
            summary = json.loads((output / 'summary.json').read_bytes())
            externs = json.loads((output / 'extern-usage.json').read_bytes())
            syscalls = json.loads((output / 'syscall-usage.json').read_bytes())
            fixed = expected == 'fixed'
            for witness in raw['defined']:
                found = [(window, insn) for window in disassembly for insn in window['instructions']
                         if insn['addr'] == witness['call_offset']]
                require(len(found) == 1, 'defined call is missing or duplicated')
                window, insn = found[0]
                wanted = ('call ' if fixed else 'call_extern ') + witness['symbol']
                require(insn['mnemonic'] == wanted, 'defined call has the wrong classification')
                witness['window_address'] = window['address']
                witness['reported_mnemonic'] = insn['mnemonic']
                per_window = next(row for row in windows if row['address'] == window['address'])
                require(per_window['internal_calls'] == int(fixed), 'window internal count differs')
                require((witness['symbol'] in per_window['extern_calls']) != fixed,
                        'window external classification differs')
                require(externs.get(witness['symbol'], 0) == int(not fixed), 'external frequency differs')
                require(witness['symbol'] not in syscalls, 'defined hook was counted as a syscall')
            require(summary['total_internal_calls'] == raw['direct_calls'] + int(fixed),
                    'total internal calls differ')
            require(summary['total_extern_calls'] == raw['dynamic_calls'] - int(fixed),
                    'total external calls differ')
            require(summary['total_instructions'] == raw['logical_instructions'], 'instruction count differs')
            result['programs'][name] = {'raw': raw, 'summary': summary,
                'packet_sha256': {path.name: sha(path.read_bytes()) for path in sorted(output.iterdir())},
                'unrelated_report_sha256': unrelated_hashes(output, raw['defined']),
                'generated_verifier_exit': verify.returncode}
            if name != 'donation_relay':
                analysis = root / 'analysis' / name
                run = subprocess.run([sys.executable, '-B', str(root / 'scripts/analyze_program.py'),
                    '--program', name, '--output', str(analysis)], cwd=root,
                    capture_output=True, text=True, timeout=60)
                require(run.returncode == 0, run.stdout + run.stderr)
                verified = subprocess.run([sys.executable, '-B', str(analysis / 'verify.py')],
                    capture_output=True, text=True, timeout=30)
                require(verified.returncode == 0, verified.stdout + verified.stderr)
                inventory = json.loads((analysis / 'window-inventory.json').read_bytes())
                graph = json.loads((analysis / 'call-graph.json').read_bytes())
                totals = json.loads((analysis / 'summary.json').read_bytes())
                witness = raw['defined'][0]
                caller = next(row for row in inventory if row['address'] == witness['window_address'])
                callee = next(row for row in inventory if row['address'] == witness['target_offset'])
                edges = [edge for edge in graph if edge['from'] == witness['window_address']
                         and edge['to'] == witness['target_offset']]
                require(caller['calls_out'] == callee['calls_in'] == len(edges) == int(fixed),
                        'analyzer defined call edge or incoming/outgoing counts differ')
                require(totals['total_call_edges'] == raw['direct_calls'] + int(fixed),
                        'analyzer total call count differs')
                if fixed:
                    require(caller['call_targets'] == [{'offset': 0,
                        'target_address': witness['target_offset'], 'target_name': witness['symbol']}],
                        'analyzer resolved target differs')
                    require(callee['callers'] == [{'caller_address': witness['call_offset'],
                                                  'caller_name': None}], 'analyzer caller differs')
                result['programs'][name]['analyzer'] = {
                    'total_call_edges': totals['total_call_edges'], 'defined_edges': edges,
                    'generated_verifier_exit': verified.returncode,
                    'packet_sha256': {path.name: sha(path.read_bytes()) for path in sorted(analysis.iterdir())},
                    'unrelated_report_sha256': analyzer_unrelated_hashes(analysis, witness)}
        require(all((root / paths[name]).read_bytes() == blob for name, blob in inputs.items()),
                'private input bytes changed')
    require(all((repo / paths[name]).read_bytes() == blob for name, blob in inputs.items()),
            'retained input bytes changed')
    require(all((repo / path).read_bytes() == data for path, data in idls.items()), 'retained IDLs changed')
    result['all_input_bytes_preserved'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--expect', choices=('base', 'fixed'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.repo, revision=args.revision, expected=args.expect)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({name: {'internal_calls': row['summary']['total_internal_calls'],
                            'external_calls': row['summary']['total_extern_calls']}
                      for name, row in result['programs'].items()}))


if __name__ == '__main__':
    main()
