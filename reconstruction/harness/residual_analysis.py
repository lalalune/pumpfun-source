#!/usr/bin/env python3
"""Compare two exact legacy-SBPF function windows; diagnostic, never a score.

The official ``score.py`` normalization is used verbatim.  Similarity and block
matching in this module are explanatory heuristics and never establish byte
identity, normalized identity, source attribution, or scorer acceptance.
"""
import argparse
from collections import Counter, defaultdict
import difflib
import hashlib
import json
from io import BytesIO
import struct
import tempfile
from pathlib import Path

from compare_scores import load_report, publish_report
from control_flow import LEGACY_CONDITIONAL_JUMPS, analyze as analyze_control_flow
from elf_symbols import function_symbols
from instruction_stream import decode_instructions, instruction_boundaries, require_instruction_range
from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFError
from score import body, normalize, sections
from score_admission import report_destination


SCHEMA = 'sbpf-residual-analysis-v1'
BRANCH_OPCODES = LEGACY_CONDITIONAL_JUMPS | {0x05}


def unique_json_fields(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f'duplicate JSON field: {key}')
        result[key] = value
    return result


def parse_window(value):
    """Parse an exact START:SIZE selector using Python-style integer prefixes."""
    try:
        start_text, size_text = value.split(':')
        start, size = int(start_text, 0), int(size_text, 0)
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError('window must be START:SIZE (for example 0x22a10:27400)')
    if start < 0 or size <= 0 or start % 8 or size % 8:
        raise argparse.ArgumentTypeError('window start and size must describe positive aligned 8-byte slots')
    return start, size


def load_image(path, role):
    """Read and validate one immutable in-memory ELF snapshot."""
    path = Path(path)
    return load_image_bytes(path.read_bytes(), role, path)


def load_image_bytes(blob, role, path):
    """Validate bytes already snapshotted by an offline caller or test."""
    path = Path(path)
    secs = sections(blob)
    if struct.unpack_from('<H', blob, 18)[0] not in (247, 263):
        raise ValueError(f'{role} is not an EM_BPF or EM_SBPF image')
    if struct.unpack_from('<I', blob, 20)[0] != 1:
        raise ValueError(f'{role} ELF header version is not 1')
    if struct.unpack_from('<I', blob, 0x30)[0] not in (0, 1):
        raise ValueError(f'{role} is not a legacy SBPFv0/v1 image')
    symbols = function_symbols(blob)
    if role == 'candidate' and not symbols:
        raise ValueError('candidate has no function symbols; use an unstripped reconstruction ELF')
    return {
        'role': role,
        'path': path,
        'blob': blob,
        'sections': secs,
        'symbols': symbols,
        'sha256': hashlib.sha256(blob).hexdigest(),
        'relocated_calls': relocated_call_symbols(blob, secs),
    }


def relocated_call_symbols(blob, secs):
    """Bind legacy type-10 call sites to their actual linked symbol table.

    A placeholder immediate is not a syscall identity. Symbol labels remain
    diagnostic evidence and do not prove the target's behavior or provenance.
    """
    try:
        elf = ELFFile(BytesIO(blob))
        rel = elf.get_section_by_name('.rel.dyn')
        if rel is None:
            return {}
        if rel['sh_type'] != 'SHT_REL' or rel['sh_entsize'] != 16 or rel['sh_size'] % 16:
            raise ValueError('unsupported call relocation table')
        if rel['sh_link'] >= elf.num_sections():
            raise ValueError('call relocation linked table is out of bounds')
        symbols = elf.get_section(rel['sh_link'])
        if symbols['sh_type'] not in ('SHT_SYMTAB', 'SHT_DYNSYM') or symbols['sh_entsize'] != 24:
            raise ValueError('call relocation requires a linked symbol table')
        text = secs['.text']
        boundaries = instruction_boundaries(body(blob, secs, text['addr'], text['size']))
        result = {}
        for row in rel.iter_relocations():
            if row['r_info_type'] != 10:
                continue
            address, index = row['r_offset'], row['r_info_sym']
            relative = address - text['addr']
            if (relative not in boundaries or relative < 0 or relative + 8 > text['size']
                    or blob[text['offset'] + relative] != 0x85):
                raise ValueError('call relocation is not at a logical call instruction')
            if index >= symbols.num_symbols() or address in result:
                raise ValueError('invalid or duplicate call relocation symbol')
            result[address] = symbols.get_symbol(index).name
        return result
    except (ELFError, IndexError, TypeError) as error:
        raise ValueError('invalid linked call relocations') from error


def select_window(image, exact_window=None, exact_symbol=None):
    """Resolve a selector and bind candidate ranges to a complete function symbol."""
    if (exact_window is None) == (exact_symbol is None):
        raise ValueError(f"{image['role']} requires exactly one window or symbol selector")
    symbols = image['symbols']
    if exact_symbol is not None:
        matches = [(start, size) for start, size, name in symbols if name == exact_symbol]
        ranges = sorted(set(matches))
        if not ranges:
            raise ValueError(f"{image['role']} symbol not found: {exact_symbol!r}")
        if len(ranges) != 1:
            raise ValueError(f"{image['role']} symbol has ambiguous ranges: {exact_symbol!r}")
        start, size = ranges[0]
    else:
        start, size = exact_window
    text = image['sections']['.text']
    text_raw = body(image['blob'], image['sections'], text['addr'], text['size'])
    require_instruction_range(text_raw, start - text['addr'], size)
    raw = body(image['blob'], image['sections'], start, size)
    if len(raw) != size:
        raise ValueError(f"{image['role']} window is truncated")
    symbol_names = sorted({name for address, length, name in symbols
                           if (address, length) == (start, size)})
    if image['role'] == 'candidate' and not symbol_names:
        raise ValueError('candidate window must exactly match a function symbol range')
    if exact_symbol is not None and exact_symbol not in symbol_names:
        raise ValueError(f"{image['role']} symbol identity changed while selecting its range")
    return {
        'start': start,
        'size': size,
        'end': start + size,
        'raw': raw,
        'normalized': normalize(raw, start, image['sections']),
        'symbols': symbol_names,
        'selector': {'kind': 'symbol', 'value': exact_symbol} if exact_symbol is not None else {
            'kind': 'window', 'value': f'{start:#x}:{size}'},
    }


def _receipt_candidate_digest(document):
    values = []
    if isinstance(document, dict):
        if isinstance(document.get('candidate_sha256'), str):
            values.append(document['candidate_sha256'])
        summary = document.get('summary')
        if isinstance(summary, dict) and isinstance(summary.get('candidate_sha256'), str):
            values.append(summary['candidate_sha256'])
    values = sorted(set(values))
    if len(values) != 1 or not all(len(value) == 64 for value in values):
        raise ValueError('score receipt must contain one candidate_sha256 identity')
    try:
        bytes.fromhex(values[0])
    except ValueError as error:
        raise ValueError('score receipt candidate_sha256 is not hexadecimal') from error
    return values[0]


def admit_receipt(path, candidate, original_window):
    """Bind a standard score receipt to the candidate bytes and selected original window."""
    path = Path(path)
    receipt_blob = path.read_bytes()
    text = receipt_blob.decode('utf-8')
    document = json.loads(text, object_pairs_hook=unique_json_fields)
    digest = _receipt_candidate_digest(document)
    if digest != candidate['sha256']:
        raise ValueError(f'score receipt candidate_sha256 does not match candidate bytes: {path}')
    # The identity and memberships must describe one read cohort.
    with tempfile.TemporaryDirectory(prefix='sbpf-residual-receipt-') as temporary:
        snapshot = Path(temporary) / 'score.json'
        snapshot.write_bytes(receipt_blob)
        snapshot.chmod(0o400)
        windows = load_report(snapshot)
    start = original_window['start']
    if start not in windows:
        raise ValueError(f'score receipt does not contain selected original window {start:#x}: {path}')
    if windows[start]['bytes'] != original_window['size']:
        raise ValueError(f'score receipt window size differs at {start:#x}: {path}')
    return {
        'path': str(path.resolve()),
        'sha256': hashlib.sha256(receipt_blob).hexdigest(),
        'candidate_sha256': digest,
        'selected_window': {'start': start, **windows[start]},
    }


def public_image(image, window):
    return {
        'path': str(image['path'].resolve()),
        'sha256': image['sha256'],
        'bytes': len(image['blob']),
        'machine': struct.unpack_from('<H', image['blob'], 18)[0],
        'sbpf_version': struct.unpack_from('<I', image['blob'], 0x30)[0],
        'text': {key: image['sections']['.text'][key] for key in ('addr', 'offset', 'size')},
        'window': {key: window[key] for key in ('start', 'end', 'size', 'symbols', 'selector')},
    }


def admit_inputs(original_path, candidate_path, original_selector, candidate_selector, receipts=()):
    original = load_image(original_path, 'original')
    candidate = load_image(candidate_path, 'candidate')
    original_window = select_window(original, **original_selector)
    candidate_window = select_window(candidate, **candidate_selector)
    admitted_receipts = [admit_receipt(path, candidate, original_window) for path in receipts]
    return original, candidate, original_window, candidate_window, admitted_receipts


def _digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _call_kind(row):
    if row['opcode'] == 0x8d:
        return 'indirect'
    if row['opcode'] != 0x85:
        return None
    if 'relocated_symbol' in row:
        return 'syscall_or_relocated'
    if row['src'] == 1 and row['immediate'] != -1:
        return 'direct'
    return 'syscall_or_relocated'


def _target_independent_token(row):
    token = bytearray(row['bytes'])
    if row['opcode'] in BRANCH_OPCODES:
        token[2:4] = b'\0\0'
    return token.hex()


def build_function_model(image, window):
    """Attach complete decoded instructions to the maintained CFG blocks."""
    raw_rows = decode_instructions(window['raw'], window['start'])
    normalized_rows = decode_instructions(window['normalized'], window['start'])
    if [row['offset'] for row in raw_rows] != [row['offset'] for row in normalized_rows]:
        raise ValueError(f"{image['role']} normalization changed instruction boundaries")
    for row in raw_rows:
        if row['address'] in image['relocated_calls']:
            row['relocated_symbol'] = image['relocated_calls'][row['address']]
    cfg = analyze_control_flow(window['raw'], window['start'])
    predecessors = defaultdict(list)
    for block in cfg['blocks']:
        for edge in block['successors']:
            if edge['internal']:
                predecessors[edge['target']].append({'source': block['offset'], 'kind': edge['kind']})
    blocks = []
    for block in cfg['blocks']:
        end = block['offset'] + block['bytes']
        indexes = [index for index, row in enumerate(raw_rows)
                   if block['offset'] <= row['offset'] < end]
        rows = [raw_rows[index] for index in indexes]
        norm = [normalized_rows[index] for index in indexes]
        successors = [dict(edge) for edge in block['successors']]
        predecessor_rows = sorted(predecessors[block['offset']], key=lambda row: (row['kind'], row['source']))
        content_material = {
            'tokens': [_target_independent_token(row) for row in norm],
            'successor_kinds': [edge['kind'] for edge in successors],
        }
        structural_material = {
            'opcodes': [row['opcode'] for row in rows],
            'widths': [row['width'] for row in rows],
            'calls': [_call_kind(row) for row in rows if _call_kind(row)],
            'successor_kinds': [edge['kind'] for edge in successors],
            'predecessor_kinds': [row['kind'] for row in predecessor_rows],
            'reachable': block['reachable'],
        }
        blocks.append({
            **block,
            'absolute_address': window['start'] + block['offset'],
            'predecessors': predecessor_rows,
            'content_fingerprint': _digest(content_material),
            'structural_fingerprint': _digest(structural_material),
            '_instructions': rows,
            '_normalized_instructions': norm,
            '_content_material': content_material,
            '_structural_material': structural_material,
        })
    return {
        'start': window['start'],
        'size': window['size'],
        'raw_equal_sha256': hashlib.sha256(window['raw']).hexdigest(),
        'normalized_sha256': hashlib.sha256(window['normalized']).hexdigest(),
        'instructions': raw_rows,
        'normalized_instructions': normalized_rows,
        'blocks': blocks,
        'calls': cfg['calls'],
        'call_sequence': [_call_descriptor(row, image['symbols']) for row in raw_rows if _call_kind(row)],
        'diagnostics': cfg['diagnostics'],
        'cyclic_regions': cfg['cyclic_regions'],
    }


def _call_descriptor(row, symbols):
    kind = _call_kind(row)
    descriptor = {'offset': row['offset'], 'kind': kind}
    if kind == 'direct':
        target = row['address'] + 8 + row['immediate'] * 8
        descriptor.update(target=target,
                          target_symbols=sorted({name for start, _size, name in symbols if start == target}))
    elif kind == 'syscall_or_relocated':
        descriptor['immediate'] = row['immediate']
        if 'relocated_symbol' in row:
            descriptor['relocated_symbol'] = row['relocated_symbol']
    elif kind == 'indirect':
        descriptor['register'] = row['immediate']
    return descriptor


def _multiset_jaccard(left, right):
    a, b = Counter(left), Counter(right)
    return sum((a & b).values()) / max(1, sum((a | b).values()))


def block_similarity(original, candidate):
    """Deterministic structural heuristic; it is never an equality predicate."""
    left = original['_structural_material']
    right = candidate['_structural_material']
    opcode_jaccard = _multiset_jaccard(left['opcodes'], right['opcodes'])
    length_ratio = min(len(left['opcodes']), len(right['opcodes'])) / max(1, len(left['opcodes']), len(right['opcodes']))
    order_ratio = difflib.SequenceMatcher(None, left['opcodes'], right['opcodes'], autojunk=False).ratio()
    successor_equal = left['successor_kinds'] == right['successor_kinds']
    predecessor_equal = left['predecessor_kinds'] == right['predecessor_kinds']
    calls_equal = left['calls'] == right['calls']
    terminal_equal = bool(left['opcodes'] and right['opcodes'] and left['opcodes'][-1] == right['opcodes'][-1])
    score = (0.25 * opcode_jaccard + 0.25 * order_ratio + 0.15 * length_ratio
             + 0.15 * successor_equal + 0.07 * predecessor_equal
             + 0.08 * calls_equal + 0.05 * terminal_equal)
    return round(score, 6)


def match_blocks(original_model, candidate_model):
    """Match blocks in reproducible stages and retain every uncertain choice."""
    originals = {block['offset']: block for block in original_model['blocks']}
    candidates = {block['offset']: block for block in candidate_model['blocks']}
    mapping, reverse, matches, ambiguities = {}, {}, [], []

    def claim(original_offset, candidate_offset, method, confidence, score, evidence):
        if original_offset in mapping or candidate_offset in reverse:
            return False
        mapping[original_offset] = candidate_offset
        reverse[candidate_offset] = original_offset
        matches.append({
            'original_offset': original_offset,
            'candidate_offset': candidate_offset,
            'method': method,
            'confidence': confidence,
            'similarity': round(score, 6),
            'evidence': evidence,
        })
        return True

    def unique_fingerprints(field, method, confidence, score):
        left, right = defaultdict(list), defaultdict(list)
        for offset, block in originals.items():
            if offset not in mapping:
                left[block[field]].append(offset)
        for offset, block in candidates.items():
            if offset not in reverse:
                right[block[field]].append(offset)
        for fingerprint in sorted(left.keys() & right.keys()):
            if len(left[fingerprint]) == len(right[fingerprint]) == 1:
                claim(left[fingerprint][0], right[fingerprint][0], method, confidence, score,
                      [f'unique_{field}'])

    # Equal offsets are useful only when target-independent normalized content
    # is also equal; physical position alone never establishes correspondence.
    for offset in sorted(originals.keys() & candidates.keys()):
        if originals[offset]['content_fingerprint'] == candidates[offset]['content_fingerprint']:
            claim(offset, offset, 'equal_offset_content', 'high', 1.0,
                  ['equal_relative_offset', 'equal_target_independent_content'])

    unique_fingerprints('content_fingerprint', 'unique_content', 'high', 1.0)
    unique_fingerprints('structural_fingerprint', 'unique_structure', 'high', 0.95)
    if 0 in originals and 0 in candidates and 0 not in mapping and 0 not in reverse:
        claim(0, 0, 'entry_anchor', 'medium', block_similarity(originals[0], candidates[0]),
              ['function_entry_anchor'])

    # A matched predecessor can identify a changed successor without relying on
    # physical layout, but only when an edge kind is singular on both sides.
    changed = True
    while changed:
        changed = False
        for original_offset, candidate_offset in sorted(mapping.items()):
            left_edges, right_edges = defaultdict(list), defaultdict(list)
            for edge in originals[original_offset]['successors']:
                if edge['internal'] and edge['target'] not in mapping:
                    left_edges[edge['kind']].append(edge['target'])
            for edge in candidates[candidate_offset]['successors']:
                if edge['internal'] and edge['target'] not in reverse:
                    right_edges[edge['kind']].append(edge['target'])
            for kind in sorted(left_edges.keys() & right_edges.keys()):
                if len(left_edges[kind]) != 1 or len(right_edges[kind]) != 1:
                    continue
                left_offset, right_offset = left_edges[kind][0], right_edges[kind][0]
                similarity = block_similarity(originals[left_offset], candidates[right_offset])
                if similarity >= 0.55 and claim(left_offset, right_offset, 'edge_context', 'medium', similarity,
                                                [f'unique_{kind}_edge_from_matched_blocks']):
                    changed = True

    # Last resort: only accept a mutual unique best with a visible margin.
    remaining_left = [offset for offset in originals if offset not in mapping]
    remaining_right = [offset for offset in candidates if offset not in reverse]
    scores = {}
    for left_offset in remaining_left:
        left_block = originals[left_offset]
        for right_offset in remaining_right:
            right_block = candidates[right_offset]
            length_ratio = min(left_block['instructions'], right_block['instructions']) / max(
                1, left_block['instructions'], right_block['instructions'])
            if length_ratio >= 0.35 and left_block['reachable'] == right_block['reachable']:
                scores[left_offset, right_offset] = block_similarity(left_block, right_block)

    def ranked_for_left(offset):
        return sorted(((score, right) for (left, right), score in scores.items() if left == offset),
                      key=lambda row: (-row[0], row[1]))

    def ranked_for_right(offset):
        return sorted(((score, left) for (left, right), score in scores.items() if right == offset),
                      key=lambda row: (-row[0], row[1]))

    left_best, right_best = {}, {}
    for offset in remaining_left:
        ranked = ranked_for_left(offset)
        if ranked:
            margin = ranked[0][0] - (ranked[1][0] if len(ranked) > 1 else 0)
            if ranked[0][0] >= 0.58 and margin >= 0.05:
                left_best[offset] = ranked[0]
            elif ranked[0][0] >= 0.58:
                ambiguities.append({
                    'original_offset': offset,
                    'reason': 'heuristic candidate margin below 0.05',
                    'candidates': [{'candidate_offset': right, 'similarity': score}
                                   for score, right in ranked[:5]],
                })
    for offset in remaining_right:
        ranked = ranked_for_right(offset)
        if ranked:
            margin = ranked[0][0] - (ranked[1][0] if len(ranked) > 1 else 0)
            if ranked[0][0] >= 0.58 and margin >= 0.05:
                right_best[offset] = ranked[0]
    for left_offset, (score, right_offset) in sorted(left_best.items()):
        if right_best.get(right_offset) == (score, left_offset):
            confidence = 'medium' if score >= 0.8 else 'low'
            claim(left_offset, right_offset, 'mutual_best_heuristic', confidence, score,
                  ['mutual_unique_best', 'minimum_margin_0.05'])

    matches.sort(key=lambda row: (row['original_offset'], row['candidate_offset']))
    ambiguities.sort(key=lambda row: row['original_offset'])
    return {
        'matches': matches,
        'mapping': mapping,
        'reverse_mapping': reverse,
        'ambiguities': ambiguities,
        'unmatched_original': sorted(set(originals) - set(mapping)),
        'unmatched_candidate': sorted(set(candidates) - set(reverse)),
    }


def public_block(block):
    return {key: value for key, value in block.items() if not key.startswith('_')}


def compare_graphs(original, candidate):
    matching = match_blocks(original, candidate)
    confidence_counts = Counter(row['confidence'] for row in matching['matches'])
    method_counts = Counter(row['method'] for row in matching['matches'])
    return {
        'original': {
            'block_count': len(original['blocks']),
            'blocks': [public_block(block) for block in original['blocks']],
            'diagnostics': original['diagnostics'],
            'cyclic_regions': original['cyclic_regions'],
        },
        'candidate': {
            'block_count': len(candidate['blocks']),
            'blocks': [public_block(block) for block in candidate['blocks']],
            'diagnostics': candidate['diagnostics'],
            'cyclic_regions': candidate['cyclic_regions'],
        },
        'matching': {key: value for key, value in matching.items()
                     if key not in ('mapping', 'reverse_mapping')},
        'matching_summary': {
            'by_confidence': dict(sorted(confidence_counts.items())),
            'by_method': dict(sorted(method_counts.items())),
            'matched': len(matching['matches']),
            'ambiguous': len(matching['ambiguities']),
            'unmatched_original': len(matching['unmatched_original']),
            'unmatched_candidate': len(matching['unmatched_candidate']),
        },
        '_mapping': matching['mapping'],
        '_reverse_mapping': matching['reverse_mapping'],
    }


def _residual(kind, classification, severity, **details):
    return {'kind': kind, 'classification': classification, 'severity': severity, **details}


def _field_value(row, field):
    value = row.get(field)
    return value.hex() if isinstance(value, bytes) else value


def _compare_instruction_fields(original_block, candidate_block):
    """Align equal opcodes, then report normalized fields and raw register use."""
    original = original_block['_instructions']
    candidate = candidate_block['_instructions']
    original_norm = original_block['_normalized_instructions']
    candidate_norm = candidate_block['_normalized_instructions']
    matcher = difflib.SequenceMatcher(None, [row['opcode'] for row in original],
                                      [row['opcode'] for row in candidate], autojunk=False)
    residuals, field_counts, examples = [], Counter(), []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            count = (i2 - i1) + (j2 - j1)
            residuals.append(_residual(
                'instruction_sequence', 'structural', 800 + count,
                original_block=original_block['offset'], candidate_block=candidate_block['offset'],
                operation=tag,
                original_offsets=[row['offset'] for row in original[i1:i2]],
                candidate_offsets=[row['offset'] for row in candidate[j1:j2]],
                original_opcodes=[row['opcode'] for row in original[i1:i2]],
                candidate_opcodes=[row['opcode'] for row in candidate[j1:j2]],
            ))
            continue
        for left_index, right_index in zip(range(i1, i2), range(j1, j2)):
            left_raw, right_raw = original[left_index], candidate[right_index]
            left, right = original_norm[left_index], candidate_norm[right_index]
            changed = {}
            for field in ('dst', 'src'):
                if left_raw[field] != right_raw[field]:
                    changed[field] = {'original': left_raw[field], 'candidate': right_raw[field]}
            # Branch displacement is classified with CFG evidence below.
            if left['opcode'] not in BRANCH_OPCODES and left['displacement'] != right['displacement']:
                changed['displacement'] = {'original': left['displacement'], 'candidate': right['displacement']}
            if left['immediate'] != right['immediate']:
                changed['immediate'] = {'original': left['immediate'], 'candidate': right['immediate']}
            if left.get('lddw_reserved') != right.get('lddw_reserved'):
                changed['lddw_reserved'] = {
                    'original': _field_value(left, 'lddw_reserved'),
                    'candidate': _field_value(right, 'lddw_reserved'),
                }
            field_counts.update(changed.keys())
            if changed and len(examples) < 12:
                examples.append({'original_offset': left_raw['offset'],
                                 'candidate_offset': right_raw['offset'], 'fields': changed})
    if field_counts:
        register_count = field_counts['dst'] + field_counts['src']
        if register_count:
            residuals.append(_residual(
                'register_usage', 'structural', 400 + register_count,
                original_block=original_block['offset'], candidate_block=candidate_block['offset'],
                field_counts={key: field_counts[key] for key in ('dst', 'src') if field_counts[key]},
                examples=[row for row in examples if set(row['fields']) & {'dst', 'src'}],
            ))
        other = {key: value for key, value in sorted(field_counts.items()) if key not in ('dst', 'src')}
        if other:
            residuals.append(_residual(
                'instruction_fields', 'structural', 350 + sum(other.values()),
                original_block=original_block['offset'], candidate_block=candidate_block['offset'],
                field_counts=other,
                examples=[row for row in examples if set(row['fields']) - {'dst', 'src'}],
                evidence='values are compared after official score.normalize',
            ))
    return residuals


def _edges_by_kind(block):
    result = defaultdict(list)
    for edge in block['successors']:
        result[edge['kind']].append(edge)
    return result


def _compare_branches(original_block, candidate_block, mapping):
    residuals = []
    original_edges, candidate_edges = _edges_by_kind(original_block), _edges_by_kind(candidate_block)
    for kind in sorted(original_edges.keys() | candidate_edges.keys()):
        left, right = original_edges[kind], candidate_edges[kind]
        if len(left) != len(right):
            residuals.append(_residual(
                'branch_edge_count', 'structural', 720 + abs(len(left) - len(right)),
                original_block=original_block['offset'], candidate_block=candidate_block['offset'],
                edge_kind=kind, original_count=len(left), candidate_count=len(right),
            ))
            continue
        for original_edge, candidate_edge in zip(left, right):
            if original_edge == candidate_edge and original_block['offset'] == candidate_block['offset']:
                continue
            mapped_target = mapping.get(original_edge['target']) if original_edge['internal'] else None
            if (original_edge['internal'] and candidate_edge['internal']
                    and mapped_target == candidate_edge['target']):
                if (original_edge['target'] != candidate_edge['target']
                        or original_block['offset'] != candidate_block['offset']):
                    residuals.append(_residual(
                        'branch_displacement_shift', 'positional', 110,
                        original_block=original_block['offset'], candidate_block=candidate_block['offset'],
                        edge_kind=kind, original_target=original_edge['target'],
                        candidate_target=candidate_edge['target'],
                        evidence='branch endpoints are matched blocks',
                    ))
            elif original_edge != candidate_edge:
                residuals.append(_residual(
                    'branch_target', 'structural', 700,
                    original_block=original_block['offset'], candidate_block=candidate_block['offset'],
                    edge_kind=kind, original=original_edge, candidate=candidate_edge,
                    mapped_original_target=mapped_target,
                ))
    return residuals


def _call_identity(call):
    if call['kind'] == 'direct' and call['target_symbols']:
        return call['kind'], tuple(call['target_symbols'])
    if call['kind'] == 'syscall_or_relocated':
        return call['kind'], ('symbol', call['relocated_symbol']) if 'relocated_symbol' in call else ('immediate', call['immediate'])
    if call['kind'] == 'indirect':
        return call['kind'], call['register']
    return call['kind'], None


def compare_calls(original, candidate):
    left, right = original['call_sequence'], candidate['call_sequence']
    residuals = []
    left_kinds, right_kinds = [row['kind'] for row in left], [row['kind'] for row in right]
    if left_kinds != right_kinds:
        matcher = difflib.SequenceMatcher(None, left_kinds, right_kinds, autojunk=False)
        residuals.append(_residual(
            'call_ordering', 'structural', 680 + abs(len(left) - len(right)),
            original_count=len(left), candidate_count=len(right),
            operations=[{'operation': tag, 'original_range': [i1, i2], 'candidate_range': [j1, j2]}
                        for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != 'equal'],
            original_kinds=left_kinds, candidate_kinds=right_kinds,
        ))
    left_identities, right_identities = list(map(_call_identity, left)), list(map(_call_identity, right))
    if left_identities != right_identities and Counter(left_identities) == Counter(right_identities):
        residuals.append(_residual(
            'call_identity_ordering', 'structural', 670,
            original=[list(value) for value in left_identities],
            candidate=[list(value) for value in right_identities],
            evidence='resolved symbol/syscall/register identities form equal multisets in a different order',
        ))
    for index, (original_call, candidate_call) in enumerate(zip(left, right)):
        if original_call['kind'] != candidate_call['kind']:
            continue
        kind = original_call['kind']
        if kind == 'direct' and original_call['target'] != candidate_call['target']:
            left_names, right_names = original_call['target_symbols'], candidate_call['target_symbols']
            common = sorted(set(left_names) & set(right_names))
            if left_names and right_names and set(left_names) == set(right_names):
                classification, residual_kind, severity = 'positional', 'call_target_shift', 105
                evidence = 'both ELF symbol tables identify the same complete target-name set'
            elif common:
                classification, residual_kind, severity = 'ambiguous', 'call_target_difference', 250
                evidence = 'ELF target symbol aliases overlap but are not identical'
            elif left_names and right_names:
                classification, residual_kind, severity = 'structural', 'call_target', 650
                evidence = 'ELF target symbol-name sets differ'
            else:
                classification, residual_kind, severity = 'ambiguous', 'call_target_difference', 250
                evidence = 'one or both call targets lack an exact ELF function symbol'
            residuals.append(_residual(
                residual_kind, classification, severity, call_index=index,
                original=original_call, candidate=candidate_call, evidence=evidence,
            ))
        elif kind == 'syscall_or_relocated' and _call_identity(original_call) != _call_identity(candidate_call):
            residuals.append(_residual(
                'call_target', 'structural', 650, call_index=index,
                original=original_call, candidate=candidate_call,
                evidence='linked relocation symbol or unrelocated call immediate differs',
            ))
        elif kind == 'indirect' and original_call['register'] != candidate_call['register']:
            residuals.append(_residual(
                'call_register', 'structural', 430, call_index=index,
                original=original_call, candidate=candidate_call,
            ))
    return residuals


def classify_residuals(original, candidate, mapping):
    original_blocks = {block['offset']: block for block in original['blocks']}
    candidate_blocks = {block['offset']: block for block in candidate['blocks']}
    residuals = []
    for offset in sorted(set(original_blocks) - set(mapping)):
        block = original_blocks[offset]
        residuals.append(_residual('unmatched_original_block', 'structural', 1000 + block['instructions'],
                                   original_block=offset, instructions=block['instructions']))
    reverse = {value: key for key, value in mapping.items()}
    for offset in sorted(set(candidate_blocks) - set(reverse)):
        block = candidate_blocks[offset]
        residuals.append(_residual('unmatched_candidate_block', 'structural', 1000 + block['instructions'],
                                   candidate_block=offset, instructions=block['instructions']))
    for original_offset, candidate_offset in sorted(mapping.items()):
        original_block, candidate_block = original_blocks[original_offset], candidate_blocks[candidate_offset]
        if (original_block['content_fingerprint'] == candidate_block['content_fingerprint']
                and original_offset != candidate_offset):
            residuals.append(_residual(
                'block_position_shift', 'positional', 100,
                original_block=original_offset, candidate_block=candidate_offset,
                delta=candidate_offset - original_offset,
                evidence='target-independent normalized block content and edge kinds are equal',
            ))
        residuals.extend(_compare_instruction_fields(original_block, candidate_block))
        residuals.extend(_compare_branches(original_block, candidate_block, mapping))
    residuals.extend(compare_calls(original, candidate))
    residuals.sort(key=lambda row: (-row['severity'], row['classification'], row['kind'],
                                    row.get('original_block', 1 << 63), row.get('candidate_block', 1 << 63)))
    for rank, row in enumerate(residuals, 1):
        row['rank'] = rank
    classifications = Counter(row['classification'] for row in residuals)
    kinds = Counter(row['kind'] for row in residuals)
    return {
        'ranking': ('severity descending; then classification, kind, original block and candidate block. '
                    'Severity ranks structural gaps above ambiguous evidence and positional shifts.'),
        'count': len(residuals),
        'by_classification': dict(sorted(classifications.items())),
        'by_kind': dict(sorted(kinds.items())),
        'ranked': residuals,
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path, help='captured original ELF')
    parser.add_argument('candidate', type=Path, help='unstripped reconstruction ELF')
    original = parser.add_mutually_exclusive_group(required=True)
    original.add_argument('--original-window', type=parse_window, metavar='START:SIZE')
    original.add_argument('--original-symbol', help='exact ELF symbol name')
    candidate = parser.add_mutually_exclusive_group(required=True)
    candidate.add_argument('--candidate-window', type=parse_window, metavar='START:SIZE')
    candidate.add_argument('--candidate-symbol', help='exact ELF symbol name')
    parser.add_argument('--score-receipt', action='append', default=[], type=Path,
                        help='optional score.py JSON receipt (repeatable)')
    parser.add_argument('--json', type=Path, help='write the complete machine-readable report')
    parser.add_argument('--format', choices=('text', 'json'), default='text', help='stdout format')
    parser.add_argument('--top', type=int, default=20, help='residual rows in the text report')
    return parser


def _selector_args(args, role):
    window = getattr(args, role + '_window')
    symbol = getattr(args, role + '_symbol')
    return {'exact_window': window, 'exact_symbol': symbol}


def analyze_admission(args):
    original, candidate, ow, cw, receipts = admit_inputs(
        args.original, args.candidate, _selector_args(args, 'original'),
        _selector_args(args, 'candidate'), args.score_receipt)
    original_model = build_function_model(original, ow)
    candidate_model = build_function_model(candidate, cw)
    control_flow = compare_graphs(original_model, candidate_model)
    matching = control_flow['matching']
    residuals = classify_residuals(original_model, candidate_model, control_flow['_mapping'])
    report = {
        'schema': SCHEMA,
        'scope': ('Diagnostic comparison. Heuristic similarity and block correspondence are not byte identity, '
                  'normalized identity, source attribution, or official score acceptance.'),
        'normalization': {
            'implementation': 'reconstruction/harness/score.py:normalize',
            'policy': 'official scorer normalization is invoked unchanged on each selected window',
        },
        'inputs': {'original': public_image(original, ow), 'candidate': public_image(candidate, cw)},
        'score_receipts': receipts,
        'identity': {
            'raw_equal': ow['raw'] == cw['raw'],
            'normalized_equal': ow['normalized'] == cw['normalized'],
            'equal_size': ow['size'] == cw['size'],
        },
        'instruction_counts': {
            'original': len(original_model['instructions']),
            'candidate': len(candidate_model['instructions']),
        },
        'control_flow': {key: value for key, value in control_flow.items() if not key.startswith('_')},
        'residuals': residuals,
    }
    report['_models'] = (original_model, candidate_model)
    report['_mapping'] = control_flow['_mapping']
    return report


def _location(row):
    locations = []
    if 'original_block' in row:
        locations.append(f"o+{row['original_block']:#x}")
    if 'candidate_block' in row:
        locations.append(f"c+{row['candidate_block']:#x}")
    if 'call_index' in row:
        locations.append(f"call[{row['call_index']}]")
    return ' '.join(locations) or '-'


def _detail(row):
    if 'field_counts' in row:
        return ','.join(f'{key}:{value}' for key, value in sorted(row['field_counts'].items()))
    if row['kind'] == 'instruction_sequence':
        return (f"{row['operation']} {len(row['original_offsets'])}=>{len(row['candidate_offsets'])} instructions")
    if 'edge_kind' in row:
        left = row.get('original_target', row.get('original'))
        right = row.get('candidate_target', row.get('candidate'))
        return f"{row['edge_kind']} {left}=>{right}"
    if row['kind'].startswith('unmatched_'):
        return f"instructions={row['instructions']}"
    if 'delta' in row:
        return f"delta={row['delta']:+#x}"
    return ''


def render_admission(report, top=20):
    original, candidate = report['inputs']['original'], report['inputs']['candidate']
    matching = report['control_flow']['matching']
    lines = [
        'SBPF residual analysis',
        f"original  {original['window']['start']:#x}+{original['window']['size']}  sha256={original['sha256']}",
        f"candidate {candidate['window']['start']:#x}+{candidate['window']['size']}  sha256={candidate['sha256']}",
        f"identity raw={report['identity']['raw_equal']} normalized={report['identity']['normalized_equal']}",
        (f"instructions {report['instruction_counts']['original']}/{report['instruction_counts']['candidate']}  "
         f"blocks {report['control_flow']['original']['block_count']}/{report['control_flow']['candidate']['block_count']}  "
         f"matched={len(matching['matches'])} ambiguous={len(matching['ambiguities'])} "
         f"unmatched={len(matching['unmatched_original'])}/{len(matching['unmatched_candidate'])}"),
        f"score receipts: {len(report['score_receipts'])}",
        (f"residuals={report['residuals']['count']} "
         + ' '.join(f'{key}={value}' for key, value in report['residuals']['by_classification'].items())),
        report['scope'],
    ]
    if top:
        lines.append('')
        lines.append(f'top residuals (showing {min(top, report["residuals"]["count"])}):')
        for row in report['residuals']['ranked'][:top]:
            lines.append(f"{row['rank']:>3}  {row['classification']:<10} {row['kind']:<28} "
                         f"severity={row['severity']:<4} {_location(row)} {_detail(row)}".rstrip())
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.top < 0:
        parser.error('--top must be nonnegative')
    try:
        report_destination(args.json, [args.original, args.candidate, *args.score_receipt])
        report = analyze_admission(args)
        public_report = {key: value for key, value in report.items() if not key.startswith('_')}
        output = json.dumps(public_report, indent=2, sort_keys=True) + '\n'
        if args.json:
            publish_report(args.json, output)
    except (OSError, ValueError, KeyError, struct.error, json.JSONDecodeError) as error:
        parser.exit(2, f'residual_analysis.py: error: {error}\n')
    print(output if args.format == 'json' else render_admission(report, args.top), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
