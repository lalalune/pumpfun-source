#!/usr/bin/env python3
"""Compare conservative register/stack provenance for two legacy-SBPF functions.

Exact per-image facts are separated from heuristic cross-image block and
instruction correspondence.  This is diagnostic only and never changes or
substitutes for the official scorer.
"""
from __future__ import annotations

import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import struct
import types

SCHEMA = 'sbpf-stack-register-provenance-v1'
SOURCE_FILES = (
    'stack_register_provenance.py', 'sbpf_provenance.py', 'residual_analysis.py',
    'control_flow.py', 'instruction_stream.py', 'elf_symbols.py', 'score.py',
    'compare_scores.py', 'score_admission.py', 'original_input.py', 'llvm_tools.py',
    'fresh_control_inputs.py',
)
_ROOT = Path(__file__).resolve().parent
_SELF_BYTES = globals().get('_ADMITTED_SOURCE_BYTES')
if _SELF_BYTES is None:
    _SELF_BYTES = Path(__file__).read_bytes()
# Reuse the maintained source-only context with this diagnostic's scoped graph.
_loader_path = _ROOT / 'fresh_control_inputs.py'
_loader_raw = _loader_path.read_bytes()
_loader = types.ModuleType('_pump_stack_provenance_source_context')
_loader.__file__ = str(_loader_path)
_loader.__dict__['_ADMITTED_SOURCE_BYTES'] = _loader_raw
exec(compile(_loader_raw, str(_loader_path), 'exec', dont_inherit=True), _loader.__dict__)
_loader.MODULES = tuple(Path(name).stem for name in SOURCE_FILES if name != 'fresh_control_inputs.py')
_SOURCE_CONTEXT = _loader.load_context()
_SOURCE_CONTEXT.raw['stack_register_provenance'] = _SELF_BYTES
_SOURCE_CONTEXT.hashes['stack_register_provenance.py'] = hashlib.sha256(_SELF_BYTES).hexdigest()
_SOURCE_CONTEXT.recheck()
_compare = _SOURCE_CONTEXT.load('compare_scores')
_residual = _SOURCE_CONTEXT.load('residual_analysis')
_provenance = _SOURCE_CONTEXT.load('sbpf_provenance')
publish_report = _compare.publish_report
admit_inputs, build_function_model, compare_graphs, parse_window, public_image = (
    getattr(_residual, name) for name in
    ('admit_inputs', 'build_function_model', 'compare_graphs', 'parse_window', 'public_image'))
analyze, public_analysis = _provenance.analyze, _provenance.public_analysis
report_destination = _SOURCE_CONTEXT.load('score_admission').report_destination


def source_provenance():
    _SOURCE_CONTEXT.recheck()
    rows = dict(_SOURCE_CONTEXT.hashes)
    digest = hashlib.sha256(json.dumps(
        rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'files': rows, 'manifest_sha256': digest}


def _selector(window, symbol):
    return {'exact_window': window, 'exact_symbol': symbol}


def _block_for(blocks, instruction_offset):
    for block in blocks:
        if block['offset'] <= instruction_offset < block['offset'] + block['bytes']:
            return block['offset']
    raise ValueError(f'instruction offset is outside every CFG block: {instruction_offset:#x}')


def _accesses_by_block(analysis):
    result = {}
    blocks = analysis['_cfg']['blocks']
    accesses = sum((analysis['stack_accesses'][name]
                    for name in ('proven', 'potential', 'unknown')), [])
    for row in accesses:
        result.setdefault(_block_for(blocks, row['instruction_offset']), []).append(row)
    for values in result.values():
        values.sort(key=lambda row: row['instruction_offset'])
    return result


def _instruction_token(row):
    cls = row['opcode'] & 7
    if cls in (1, 2, 3):
        return ('memory', 'read' if cls == 1 else 'write')
    return ('opcode', row['opcode'])


def _matched_instruction_offsets(left_rows, right_rows):
    matcher = difflib.SequenceMatcher(None, list(map(_instruction_token, left_rows)),
                                      list(map(_instruction_token, right_rows)), autojunk=False)
    pairs, left_only, right_only = {}, set(), set()
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for left, right in zip(left_rows[i1:i2], right_rows[j1:j2]):
                pairs[left['offset']] = right['offset']
        else:
            left_only.update(row['offset'] for row in left_rows[i1:i2])
            right_only.update(row['offset'] for row in right_rows[j1:j2])
            # A single memory operation replacing a single memory operation is
            # retained as a width/opcode comparison, not hidden as two absences.
            if i2 - i1 == j2 - j1 == 1 \
                    and _instruction_token(left_rows[i1])[0] == _instruction_token(right_rows[j1])[0] == 'memory':
                pairs[left_rows[i1]['offset']] = right_rows[j1]['offset']
                left_only.discard(left_rows[i1]['offset'])
                right_only.discard(right_rows[j1]['offset'])
    return pairs, left_only, right_only


def compare_stack_accesses(original, candidate, residual):
    left_by_block, right_by_block = _accesses_by_block(original), _accesses_by_block(candidate)
    left_access = {row['instruction_offset']: row for rows in left_by_block.values() for row in rows}
    right_access = {row['instruction_offset']: row for rows in right_by_block.values() for row in rows}
    match_rows = {row['original_offset']: row for row in residual['matching']['matches']}
    residuals, paired_left, paired_right = [], set(), set()
    for left_block, right_block in sorted(residual['_mapping'].items()):
        instruction_pairs, _left_only, _right_only = _matched_instruction_offsets(
            original['_rows'][left_block], candidate['_rows'][right_block])
        block_match = match_rows[left_block]
        for left_offset, right_offset in sorted(instruction_pairs.items()):
            left = left_access.get(left_offset)
            right = right_access.get(right_offset)
            if left is None or right is None:
                continue
            paired_left.add(left_offset); paired_right.add(right_offset)
            common = {
                'classification': 'heuristic_correspondence',
                'confidence': block_match['confidence'],
                'block_match_method': block_match['method'],
                'original_block': left_block, 'candidate_block': right_block,
                'original_instruction_offset': left_offset,
                'candidate_instruction_offset': right_offset,
            }
            if left['classification'] == right['classification'] == 'proven':
                if left['stack_offset'] != right['stack_offset']:
                    residuals.append({**common, 'kind': 'moved_frame_slot',
                                      'original_stack_offset': left['stack_offset'],
                                      'candidate_stack_offset': right['stack_offset'],
                                      'delta': right['stack_offset'] - left['stack_offset']})
                if left['width'] != right['width']:
                    residuals.append({**common, 'kind': 'access_width_difference',
                                      'original_width': left['width'], 'candidate_width': right['width']})
                if left['alias_kind'] != right['alias_kind']:
                    residuals.append({**common, 'kind': 'alias_formation_difference',
                                      'original_alias_kind': left['alias_kind'],
                                      'candidate_alias_kind': right['alias_kind']})
            elif left['classification'] != right['classification']:
                residuals.append({**common, 'kind': 'access_certainty_difference',
                                  'original_classification': left['classification'],
                                  'candidate_classification': right['classification']})
    unmatched_left = [row for offset, row in sorted(left_access.items()) if offset not in paired_left]
    unmatched_right = [row for offset, row in sorted(right_access.items()) if offset not in paired_right]
    for side, rows in (('original', unmatched_left), ('candidate', unmatched_right)):
        for row in rows:
            residuals.append({
                'kind': side + '_only_stack_operation',
                'classification': 'heuristic_correspondence',
                'confidence': 'low',
                side + '_instruction_offset': row['instruction_offset'],
                side + '_access': row,
                'note': 'Absence is relative to admitted heuristic block/instruction correspondence.',
            })
    residuals.sort(key=lambda row: (row['kind'], row.get('original_instruction_offset', 1 << 63),
                                    row.get('candidate_instruction_offset', 1 << 63)))
    return {
        'scope': ('Cross-image rows use residual_analysis block correspondence and local instruction alignment. '
                  'They are not exact equivalence facts.'),
        'count': len(residuals),
        'by_kind': dict(sorted(Counter(row['kind'] for row in residuals).items())),
        'rows': residuals,
    }


def compare_liveness(original, candidate, residual):
    left = {row['block_offset']: row for row in original['liveness']['blocks']}
    right = {row['block_offset']: row for row in candidate['liveness']['blocks']}
    matches = {row['original_offset']: row for row in residual['matching']['matches']}
    rows = []
    for left_offset, right_offset in sorted(residual['_mapping'].items()):
        a, b = left[left_offset], right[right_offset]
        if (a['live_in'], a['live_out'], a['maximum_live_registers']) == \
                (b['live_in'], b['live_out'], b['maximum_live_registers']):
            continue
        match = matches[left_offset]
        rows.append({
            'classification': 'heuristic_correspondence',
            'confidence': match['confidence'], 'block_match_method': match['method'],
            'original_block': left_offset, 'candidate_block': right_offset,
            'original_live_in': a['live_in'], 'candidate_live_in': b['live_in'],
            'original_live_out': a['live_out'], 'candidate_live_out': b['live_out'],
            'original_pressure': a['maximum_live_registers'],
            'candidate_pressure': b['maximum_live_registers'],
        })
    return {
        'scope': 'Differences are conditional on heuristic residual-analysis block correspondence.',
        'count': len(rows), 'rows': rows,
    }


def _summary(analysis):
    accesses = analysis['stack_accesses']
    known_entries = sum(len(row['entry_known_registers']) for row in analysis['register_states'])
    return {
        'instructions': analysis['instruction_count'],
        'reachable_blocks': analysis['reachable_block_count'],
        'fixed_point_steps': analysis['fixed_point_steps'],
        'known_block_entry_register_facts': known_entries,
        'proven_stack_accesses': len(accesses['proven']),
        'potential_stack_accesses': len(accesses['potential']),
        'unknown_memory_accesses': len(accesses['unknown']),
        'derived_stack_accesses': sum(row.get('alias_kind') == 'derived' for row in accesses['proven']),
        'stack_pointer_aliases': len(analysis['stack_pointer_aliases']),
        'pointer_escapes': len(analysis['pointer_escapes']),
        'maximum_register_pressure': analysis['liveness']['maximum_register_pressure'],
        'suspected_spill_reload_patterns': len(analysis['suspected_spill_reload_patterns']),
    }


def actionable_locations(stack_residuals, liveness_differences, starts, limit=50):
    confidence_rank = {'high': 0, 'medium': 1, 'low': 2}
    kind_rank = {'moved_frame_slot': 0, 'access_width_difference': 1,
                 'alias_formation_difference': 2, 'access_certainty_difference': 3,
                 'original_only_stack_operation': 4, 'candidate_only_stack_operation': 5}
    rows = []
    ranked = sorted(stack_residuals['rows'], key=lambda row: (
        confidence_rank.get(row.get('confidence'), 3), kind_rank.get(row['kind'], 9),
        row.get('original_instruction_offset', 1 << 63),
        row.get('candidate_instruction_offset', 1 << 63)))
    for row in ranked:
        if len(rows) >= limit:
            break
        selected = {key: value for key, value in row.items() if key in {
            'kind', 'classification', 'confidence', 'original_block', 'candidate_block',
            'original_instruction_offset', 'candidate_instruction_offset',
            'original_stack_offset', 'candidate_stack_offset', 'delta',
            'original_width', 'candidate_width', 'original_alias_kind', 'candidate_alias_kind',
        }}
        for side in ('original', 'candidate'):
            offset = selected.get(side + '_instruction_offset')
            if offset is not None:
                selected[side + '_address'] = starts[side] + offset
        rows.append(selected)
    if len(rows) < limit:
        for row in liveness_differences['rows'][:limit - len(rows)]:
            rows.append({'kind': 'block_liveness_difference',
                         **{key: row[key] for key in ('classification', 'confidence',
                                                      'original_block', 'candidate_block',
                                                      'original_pressure', 'candidate_pressure')}})
    return rows


def analyze_pair(original_path, candidate_path, original_selector, candidate_selector,
                 *, expected_original_sha256=None, expected_candidate_sha256=None,
                 score_receipts=()):
    _SOURCE_CONTEXT.recheck()
    original_image, candidate_image, ow, cw, receipts = admit_inputs(
        original_path, candidate_path, original_selector, candidate_selector, score_receipts)
    for role, image, expected in (('original', original_image, expected_original_sha256),
                                  ('candidate', candidate_image, expected_candidate_sha256)):
        if expected is not None and image['sha256'] != expected:
            raise ValueError(f'{role} SHA-256 does not match --expect-{role}-sha256')
    original_model, candidate_model = build_function_model(original_image, ow), build_function_model(candidate_image, cw)
    control_flow = compare_graphs(original_model, candidate_model)
    original_analysis = analyze(ow['raw'], ow['start'])
    candidate_analysis = analyze(cw['raw'], cw['start'])
    stack_residuals = compare_stack_accesses(original_analysis, candidate_analysis, control_flow)
    liveness_differences = compare_liveness(original_analysis, candidate_analysis, control_flow)
    report = {
        'schema': SCHEMA,
        'scope': ('Static legacy-SBPF diagnostic facts. No runtime safety, source-variable identity, '
                  'complete alias analysis, compiler allocation decision, bytecode equality, or runtime equivalence is claimed.'),
        'normalization': {'implementation': 'reconstruction/harness/score.py:normalize',
                          'policy': 'official scorer normalization is invoked unchanged by residual_analysis'},
        'analyzer_source': source_provenance(),
        'inputs': {'original': public_image(original_image, ow),
                   'candidate': public_image(candidate_image, cw)},
        'score_receipts': receipts,
        'identity': {'raw_equal': ow['raw'] == cw['raw'],
                     'normalized_equal': ow['normalized'] == cw['normalized'],
                     'equal_size': ow['size'] == cw['size']},
        'control_flow': {
            'original': {key: control_flow['original'][key]
                         for key in ('block_count', 'diagnostics', 'cyclic_regions')},
            'candidate': {key: control_flow['candidate'][key]
                          for key in ('block_count', 'diagnostics', 'cyclic_regions')},
            'matching': control_flow['matching'],
            'matching_summary': control_flow['matching_summary'],
        },
        'exact_facts': {
            'original': public_analysis(original_analysis),
            'candidate': public_analysis(candidate_analysis),
        },
        'register_state_summaries': {
            'original': _summary(original_analysis),
            'candidate': _summary(candidate_analysis),
        },
        'heuristic_correspondences': {
            'stack_frame_residuals': stack_residuals,
            'liveness_differences': liveness_differences,
        },
        'actionable_comparison_locations': actionable_locations(
            stack_residuals, liveness_differences,
            {'original': ow['start'], 'candidate': cw['start']}),
        'limitations': [
            'Potential and unknown accesses are never counted as proven stack accesses.',
            'Calls clobber r0-r5 and invalidate all tracked stack-memory values; known stack-pointer arguments are recorded.',
            'Suspected spill/reload patterns prove only a same-range reaching store and load.',
            'Cross-image frame and liveness rows depend on explicitly labelled heuristic block correspondence.',
        ],
    }
    _SOURCE_CONTEXT.recheck()
    return report


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('candidate', type=Path)
    original = parser.add_mutually_exclusive_group(required=True)
    original.add_argument('--original-window', type=parse_window, metavar='START:SIZE')
    original.add_argument('--original-symbol')
    candidate = parser.add_mutually_exclusive_group(required=True)
    candidate.add_argument('--candidate-window', type=parse_window, metavar='START:SIZE')
    candidate.add_argument('--candidate-symbol')
    parser.add_argument('--expect-original-sha256')
    parser.add_argument('--expect-candidate-sha256')
    parser.add_argument('--score-receipt', action='append', default=[], type=Path)
    parser.add_argument('--json', type=Path)
    return parser


def main(argv=None):
    _SOURCE_CONTEXT.recheck()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report_destination(args.json, [args.original, args.candidate, *args.score_receipt,
                                      *(_ROOT / name for name in SOURCE_FILES)])
        report = analyze_pair(
            args.original, args.candidate,
            _selector(args.original_window, args.original_symbol),
            _selector(args.candidate_window, args.candidate_symbol),
            expected_original_sha256=args.expect_original_sha256,
            expected_candidate_sha256=args.expect_candidate_sha256,
            score_receipts=args.score_receipt)
        output = json.dumps(report, indent=2, sort_keys=True) + '\n'
        if args.json:
            _SOURCE_CONTEXT.recheck()
            publish_report(args.json, output)
    except (OSError, ValueError, KeyError, struct.error, json.JSONDecodeError) as error:
        parser.exit(2, f'stack_register_provenance.py: error: {error}\n')
    print(output, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
