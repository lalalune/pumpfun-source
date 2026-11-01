"""Conservative CFG-aware register, stack-alias, and liveness analysis for legacy SBPF.

This module reports static facts only.  It does not prove runtime memory safety,
source-variable identity, compiler allocation intent, or complete aliasing.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass, replace
from typing import Any

from control_flow import LEGACY_CONDITIONAL_JUMPS, analyze as analyze_control_flow
from instruction_stream import decode_instructions


REGISTER_COUNT = 11
CALLER_SAVED = frozenset(range(0, 6))
CALL_ARGUMENTS = frozenset(range(1, 6))
MEMORY_WIDTHS = {0x60: 4, 0x68: 2, 0x70: 1, 0x78: 8}
MAX_EVIDENCE = 24
MAX_STACK_CANDIDATES = 16


def _bounded(values, limit=MAX_EVIDENCE):
    rows = sorted(set(values), key=lambda value: (isinstance(value, str), str(value)))
    return tuple(rows[:limit]), len(rows) > limit


@dataclass(frozen=True)
class Fact:
    kind: str = 'unknown'  # unknown, constant, stack_pointer
    value: int | None = None
    stack_candidates: tuple[int, ...] = ()
    definitions: tuple[int | str, ...] = ()
    ambiguous: bool = False
    evidence_truncated: bool = False

    def public(self):
        row: dict[str, Any] = {'kind': self.kind}
        if self.value is not None:
            row['value'] = self.value
        if self.stack_candidates:
            row['stack_candidates'] = list(self.stack_candidates)
        if self.definitions:
            row['reaching_definitions'] = list(self.definitions)
        if self.ambiguous:
            row['path_ambiguous'] = True
        if self.evidence_truncated:
            row['evidence_truncated'] = True
        return row


def unknown(definition=None, *, candidates=(), ambiguous=False):
    defs = () if definition is None else (definition,)
    bounded, truncated = _bounded(candidates, MAX_STACK_CANDIDATES)
    return Fact('unknown', stack_candidates=tuple(int(value) for value in bounded),
                definitions=defs, ambiguous=ambiguous, evidence_truncated=truncated)


def constant(value, definition):
    return Fact('constant', value=value & ((1 << 64) - 1), definitions=(definition,))


def stack_pointer(displacement, definition='entry:r10'):
    return Fact('stack_pointer', value=displacement, definitions=(definition,))


def with_definition(fact, definition, *, ambiguous=None):
    definitions, truncated = _bounded((*fact.definitions, definition))
    return replace(fact, definitions=definitions,
                   ambiguous=fact.ambiguous if ambiguous is None else ambiguous,
                   evidence_truncated=fact.evidence_truncated or truncated)


def derived_fact(kind, value, inputs):
    definitions, truncated = _bounded(item for fact in inputs for item in fact.definitions)
    return Fact(kind, value=value, definitions=definitions,
                ambiguous=any(fact.ambiguous for fact in inputs),
                evidence_truncated=truncated or any(fact.evidence_truncated for fact in inputs))


def join_facts(facts):
    facts = tuple(facts)
    if not facts:
        return unknown(ambiguous=True)
    definitions, truncated = _bounded(value for fact in facts for value in fact.definitions)
    semantic = {(fact.kind, fact.value) for fact in facts}
    if len(semantic) == 1:
        first = facts[0]
        candidates, candidate_truncated = _bounded(
            (value for fact in facts for value in fact.stack_candidates), MAX_STACK_CANDIDATES)
        return Fact(first.kind, first.value, tuple(int(value) for value in candidates), definitions,
                    any(fact.ambiguous for fact in facts) or len({fact.definitions for fact in facts}) > 1,
                    truncated or candidate_truncated or any(fact.evidence_truncated for fact in facts))
    candidates = []
    for fact in facts:
        if fact.kind == 'stack_pointer':
            candidates.append(fact.value)
        candidates.extend(fact.stack_candidates)
    candidates, candidate_truncated = _bounded(candidates, MAX_STACK_CANDIDATES)
    return Fact('unknown', stack_candidates=tuple(int(value) for value in candidates),
                definitions=definitions, ambiguous=True,
                evidence_truncated=truncated or candidate_truncated
                or any(fact.evidence_truncated for fact in facts))


@dataclass(frozen=True)
class MemoryFact:
    fact: Fact
    stores: tuple[int, ...]
    source_registers: tuple[int, ...] = ()
    ambiguous: bool = False


@dataclass(frozen=True)
class State:
    registers: tuple[Fact, ...]
    memory: tuple[tuple[tuple[int, int], MemoryFact], ...] = ()

    def memory_dict(self):
        return dict(self.memory)


def state(registers, memory):
    return State(tuple(registers), tuple(sorted(memory.items())))


def entry_state():
    registers = [unknown(f'entry:r{register}') for register in range(REGISTER_COUNT)]
    registers[10] = stack_pointer(0)
    return state(registers, {})


def join_states(states):
    states = tuple(states)
    if len(states) == 1:
        return states[0]
    registers = [join_facts(row.registers[index] for row in states)
                 for index in range(REGISTER_COUNT)]
    memories = [row.memory_dict() for row in states]
    common = set(memories[0])
    for memory in memories[1:]:
        common &= set(memory)
    result = {}
    for key in sorted(common):
        values = [memory[key] for memory in memories]
        joined = join_facts(value.fact for value in values)
        stores, truncated = _bounded(store for value in values for store in value.stores)
        sources, _ = _bounded(register for value in values for register in value.source_registers)
        result[key] = MemoryFact(
            replace(joined, evidence_truncated=joined.evidence_truncated or truncated),
            tuple(int(value) for value in stores), tuple(int(value) for value in sources),
            any(value.ambiguous for value in values) or len({value.stores for value in values}) > 1)
    return state(registers, result)


def _overlaps(left, right):
    return left[0] < right[0] + right[1] and right[0] < left[0] + left[1]


def _signed(value, bits):
    sign = 1 << (bits - 1)
    return (value & (sign - 1)) - (value & sign)


def _constant_binary(operation, left, right, bits):
    mask = (1 << bits) - 1
    left, right = left & mask, right & mask
    if operation == 0x00:
        value = left + right
    elif operation == 0x10:
        value = left - right
    elif operation == 0x20:
        value = left * right
    elif operation == 0x30:
        if right == 0:
            return None
        value = left // right
    elif operation == 0x40:
        value = left | right
    elif operation == 0x50:
        value = left & right
    elif operation == 0x60:
        value = left << (right & (bits - 1))
    elif operation == 0x70:
        value = left >> (right & (bits - 1))
    elif operation == 0x90:
        if right == 0:
            return None
        value = left % right
    elif operation == 0xa0:
        value = left ^ right
    elif operation == 0xc0:
        value = _signed(left, bits) >> (right & (bits - 1))
    else:
        return None
    return value & mask


def _memory_access(row, fact, width, kind):
    base, displacement = row['src'] if kind == 'read' else row['dst'], row['displacement']
    common = {
        'instruction_offset': row['offset'], 'address': row['address'],
        'opcode': row['opcode'], 'kind': kind, 'width': width,
        'base_register': base, 'encoded_displacement': displacement,
    }
    if fact.kind == 'stack_pointer':
        offset = fact.value + displacement
        return {**common, 'classification': 'proven',
                'alias_kind': 'direct' if base == 10 else 'derived',
                'stack_offset': offset, 'stack_end': offset + width,
                'reaching_definition_evidence': fact.public()}
    if fact.stack_candidates:
        offsets = sorted({value + displacement for value in fact.stack_candidates})
        return {**common, 'classification': 'potential',
                'candidate_stack_offsets': offsets,
                'cfg_path_ambiguity': True,
                'reaching_definition_evidence': fact.public()}
    return {**common, 'classification': 'unknown',
            'reaching_definition_evidence': fact.public()}


def _condition(row, registers):
    left = registers[row['dst']]
    right = registers[row['src']] if row['opcode'] & 0x08 else constant(row['immediate'], row['offset'])
    operation = row['opcode'] & 0xf0
    if operation in (0x10, 0x50) and left.kind == right.kind \
            and left.kind in ('constant', 'stack_pointer'):
        equal = left.value == right.value
        return equal if operation == 0x10 else not equal
    if left.kind != 'constant' or right.kind != 'constant':
        return None
    a, b = left.value, right.value
    if operation == 0x10:
        return a == b
    if operation == 0x20:
        return a > b
    if operation == 0x30:
        return a >= b
    if operation == 0x40:
        return bool(a & b)
    if operation == 0x50:
        return a != b
    if operation == 0x60:
        return _signed(a, 64) > _signed(b, 64)
    if operation == 0x70:
        return _signed(a, 64) >= _signed(b, 64)
    if operation == 0xa0:
        return a < b
    if operation == 0xb0:
        return a <= b
    if operation == 0xc0:
        return _signed(a, 64) < _signed(b, 64)
    if operation == 0xd0:
        return _signed(a, 64) <= _signed(b, 64)
    return None


class Transfer:
    def __init__(self, *, collect=False):
        self.collect = collect
        self.accesses = []
        self.aliases = []
        self.escapes = []
        self.diagnostics = []

    def set_register(self, registers, register, fact, row, reason):
        fact = with_definition(fact, row['offset'])
        registers[register] = fact
        if self.collect and fact.kind == 'stack_pointer':
            self.aliases.append({
                'instruction_offset': row['offset'], 'address': row['address'],
                'register': register, 'stack_displacement': fact.value,
                'reason': reason, 'reaching_definition_evidence': fact.public(),
            })

    def instruction(self, current, row):
        registers, memory = list(current.registers), current.memory_dict()
        opcode, cls = row['opcode'], row['opcode'] & 7
        if opcode == 0x18:  # LDDW
            self.set_register(registers, row['dst'], constant(row['immediate'], row['offset']), row, 'lddw_constant')
            return state(registers, memory)
        if cls in (1, 2, 3):
            width = MEMORY_WIDTHS.get(opcode & 0xf8)
            base = row['src'] if cls == 1 else row['dst']
            kind = 'read' if cls == 1 else 'write'
            if width is None:
                if self.collect:
                    self.diagnostics.append({'instruction_offset': row['offset'], 'opcode': opcode,
                                             'kind': 'unsupported_memory_opcode'})
                if cls == 1:
                    registers[row['dst']] = unknown(row['offset'], ambiguous=True)
                else:
                    memory.clear()
                return state(registers, memory)
            access = _memory_access(row, registers[base], width, kind)
            if self.collect:
                self.accesses.append(access)
            if cls == 1:
                loaded = unknown(row['offset'])
                if access['classification'] == 'proven':
                    stored = memory.get((access['stack_offset'], width))
                    if stored is not None:
                        loaded = with_definition(stored.fact, row['offset'], ambiguous=stored.ambiguous)
                        if self.collect:
                            access['reloaded_value'] = loaded.public()
                            access['reaching_stores'] = list(stored.stores)
                            if loaded.kind == 'stack_pointer':
                                access['recovered_stack_pointer'] = True
                self.set_register(registers, row['dst'], loaded, row,
                                  'proven_stack_reload' if loaded.kind == 'stack_pointer' else 'memory_load')
            else:
                if access['classification'] != 'proven':
                    memory.clear()  # Unknown store may alias any tracked stack value.
                else:
                    key = (access['stack_offset'], width)
                    for existing in list(memory):
                        if _overlaps(existing, key):
                            del memory[existing]
                    if cls == 2:
                        value = constant(row['immediate'] & ((1 << (width * 8)) - 1), row['offset'])
                        sources = ()
                    else:
                        value = registers[row['src']]
                        sources = (row['src'],)
                        # Narrow stores retain only their low bytes. A partial
                        # pointer cannot be reconstructed as the original pointer.
                        if value.kind == 'constant':
                            value = replace(value, value=value.value & ((1 << (width * 8)) - 1))
                        elif width != 8:
                            value = unknown(row['offset'])
                    memory[key] = MemoryFact(with_definition(value, row['offset']), (row['offset'],), sources)
            return state(registers, memory)
        if cls in (4, 7):
            dst, operation, bits = row['dst'], opcode & 0xf0, 32 if cls == 4 else 64
            if operation == 0xb0:  # MOV
                if opcode & 0x08:
                    source = registers[row['src']]
                    if bits == 32 and source.kind == 'constant':
                        source = constant(source.value & 0xffffffff, row['offset'])
                    elif bits == 32 and source.kind == 'stack_pointer':
                        source = unknown(row['offset'], ambiguous=True)
                    reason = 'register_copy'
                else:
                    source = constant(row['immediate'] & ((1 << bits) - 1), row['offset'])
                    reason = 'immediate_constant'
                self.set_register(registers, dst, source, row, reason)
            elif operation == 0x80:  # NEG
                source = registers[dst]
                result = ((-source.value) & ((1 << bits) - 1)) if source.kind == 'constant' else None
                self.set_register(registers, dst,
                                  constant(result, row['offset']) if result is not None else unknown(row['offset']),
                                  row, 'constant_arithmetic' if result is not None else 'unsupported_value')
            else:
                left = registers[dst]
                right = registers[row['src']] if opcode & 0x08 else constant(row['immediate'], row['offset'])
                result = None
                reason = 'unsupported_value'
                if bits == 64 and left.kind == 'stack_pointer' and right.kind == 'constant' \
                        and operation in (0x00, 0x10):
                    delta = right.value if operation == 0x00 else -right.value
                    result = derived_fact('stack_pointer', _signed(left.value + delta, 64), (left, right))
                    reason = 'stack_pointer_arithmetic'
                elif left.kind == right.kind == 'constant':
                    value = _constant_binary(operation, left.value, right.value, bits)
                    if value is not None:
                        result, reason = derived_fact('constant', value, (left, right)), 'constant_arithmetic'
                self.set_register(registers, dst, result or unknown(row['offset']), row, reason)
            if dst == 10 and self.collect:
                self.diagnostics.append({'instruction_offset': row['offset'], 'opcode': opcode,
                                         'kind': 'frame_pointer_write'})
            return state(registers, memory)
        if cls == 5:
            if opcode in (0x85, 0x8d):
                escaped = []
                for register in sorted(CALL_ARGUMENTS):
                    fact = registers[register]
                    if fact.kind == 'stack_pointer' or fact.stack_candidates:
                        escaped.append({'register': register, 'fact': fact.public()})
                if escaped:
                    if self.collect:
                        self.escapes.append({'instruction_offset': row['offset'], 'address': row['address'],
                                             'call_kind': 'indirect' if opcode == 0x8d else 'direct_or_syscall',
                                             'arguments': escaped,
                                             'effect': 'tracked_stack_memory_invalidated'})
                # Unknown arguments or an earlier escaped alias can also let a
                # callee write the frame. Retain no stack-memory value across a call.
                memory.clear()
                for register in CALLER_SAVED:
                    registers[register] = unknown(row['offset'], ambiguous=True)
            return state(registers, memory)
        # Unsupported legacy instructions conservatively destroy their encoded destination.
        if 0 <= row['dst'] < REGISTER_COUNT:
            registers[row['dst']] = unknown(row['offset'], ambiguous=True)
        if self.collect:
            self.diagnostics.append({'instruction_offset': row['offset'], 'opcode': opcode,
                                     'kind': 'unsupported_opcode'})
        return state(registers, memory)


def _block_rows(instructions, block):
    end = block['offset'] + block['bytes']
    return [row for row in instructions if block['offset'] <= row['offset'] < end]


def _active_successors(block, rows, before_last):
    successors = [edge['target'] for edge in block['successors'] if edge['internal']]
    if not rows or rows[-1]['opcode'] not in LEGACY_CONDITIONAL_JUMPS:
        return successors, []
    result = _condition(rows[-1], before_last.registers)
    if result is None:
        return successors, []
    wanted = 'taken' if result else 'fallthrough'
    active = [edge['target'] for edge in block['successors']
              if edge['internal'] and edge['kind'] == wanted]
    pruned = [edge['target'] for edge in block['successors']
              if edge['internal'] and edge['kind'] != wanted]
    return active, pruned


def _transfer_block(block, rows, incoming, *, collect=False):
    transfer = Transfer(collect=collect)
    current, before_last = incoming, incoming
    for index, row in enumerate(rows):
        if index == len(rows) - 1:
            before_last = current
        current = transfer.instruction(current, row)
    active, pruned = _active_successors(block, rows, before_last)
    return current, active, pruned, transfer


def fixed_point(raw, start=0, *, iteration_limit=None):
    instructions = decode_instructions(raw, start)
    cfg = analyze_control_flow(raw, start)
    blocks = {block['offset']: block for block in cfg['blocks']}
    rows = {offset: _block_rows(instructions, block) for offset, block in blocks.items()}
    incoming: dict[int, dict[int | str, State]] = defaultdict(dict)
    incoming[0]['entry'] = entry_state()
    in_states: dict[int, State] = {0: entry_state()}
    out_states: dict[int, State] = {}
    outgoing: dict[int, set[int]] = defaultdict(set)
    pruned_by_block: dict[int, list[int]] = {}
    pending, queued = deque([0]), {0}
    steps = 0
    limit = iteration_limit or max(1024, len(blocks) * 64)
    while pending:
        block_offset = pending.popleft()
        queued.discard(block_offset)
        steps += 1
        if steps > limit:
            raise ValueError('register dataflow did not converge within the bounded iteration limit')
        current_in = join_states(incoming[block_offset].values())
        in_states[block_offset] = current_in
        current_out, active, pruned, _ = _transfer_block(
            blocks[block_offset], rows[block_offset], current_in)
        out_states[block_offset] = current_out
        new_targets = set(active)
        for target in outgoing[block_offset] - new_targets:
            incoming[target].pop(block_offset, None)
            if incoming[target]:
                updated = join_states(incoming[target].values())
                if in_states.get(target) != updated and target not in queued:
                    pending.append(target); queued.add(target)
            else:
                in_states.pop(target, None); out_states.pop(target, None)
        for target in new_targets:
            previous = incoming[target].get(block_offset)
            incoming[target][block_offset] = current_out
            updated = join_states(incoming[target].values())
            if previous != current_out or in_states.get(target) != updated:
                if target not in queued:
                    pending.append(target); queued.add(target)
        outgoing[block_offset] = new_targets
        pruned_by_block[block_offset] = pruned
    return instructions, cfg, blocks, rows, in_states, out_states, pruned_by_block, steps


def instruction_use_def(row):
    opcode, cls = row['opcode'], row['opcode'] & 7
    if opcode == 0x18:
        return set(), {row['dst']}
    if cls == 1:
        return {row['src']}, {row['dst']}
    if cls == 2:
        return {row['dst']}, set()
    if cls == 3:
        return {row['dst'], row['src']}, set()
    if cls in (4, 7):
        operation = opcode & 0xf0
        if operation == 0xb0:
            uses = {row['src']} if opcode & 0x08 else set()
        else:
            uses = {row['dst']} | ({row['src']} if opcode & 0x08 else set())
        return uses, {row['dst']}
    if cls == 5:
        if opcode == 0x95:
            return {0}, set()
        if opcode == 0x8d:
            return set(CALL_ARGUMENTS) | {row['immediate']}, set(CALLER_SAVED)
        if opcode == 0x85:
            return set(CALL_ARGUMENTS), set(CALLER_SAVED)
        if opcode in LEGACY_CONDITIONAL_JUMPS:
            return {row['dst']} | ({row['src']} if opcode & 0x08 else set()), set()
        return set(), set()
    return set(), {row['dst']} if 0 <= row['dst'] < REGISTER_COUNT else set()


def liveness(cfg, rows):
    blocks = {block['offset']: block for block in cfg['blocks']}
    block_use, block_def = {}, {}
    for offset in blocks:
        uses, definitions = set(), set()
        for row in rows[offset]:
            row_use, row_def = instruction_use_def(row)
            uses |= row_use - definitions
            definitions |= row_def
        block_use[offset], block_def[offset] = uses, definitions
    live_in = {offset: set() for offset in blocks}
    live_out = {offset: set() for offset in blocks}
    changed = True
    iterations = 0
    while changed:
        changed = False
        iterations += 1
        if iterations > max(64, len(blocks) * 4):
            raise ValueError('register liveness did not converge')
        for offset in reversed(list(blocks)):
            successors = [edge['target'] for edge in blocks[offset]['successors'] if edge['internal']]
            outgoing = set().union(*(live_in[target] for target in successors)) if successors else set()
            incoming = block_use[offset] | (outgoing - block_def[offset])
            if incoming != live_in[offset] or outgoing != live_out[offset]:
                live_in[offset], live_out[offset] = incoming, outgoing
                changed = True
    details, dead_definitions = [], []
    for offset in blocks:
        live = set(live_out[offset])
        pressure = len(live)
        for row in reversed(rows[offset]):
            row_use, row_def = instruction_use_def(row)
            for register in sorted(row_def - live):
                dead_definitions.append({'instruction_offset': row['offset'], 'register': register})
            live = row_use | (live - row_def)
            pressure = max(pressure, len(live))
        details.append({'block_offset': offset, 'live_in': sorted(live_in[offset]),
                        'live_out': sorted(live_out[offset]),
                        'maximum_live_registers': pressure})
    return {'iterations': iterations, 'blocks': details,
            'maximum_register_pressure': max((row['maximum_live_registers'] for row in details), default=0),
            'dead_definitions': dead_definitions}


def suspected_spills(accesses):
    stores = {row['instruction_offset']: row for row in accesses
              if row['classification'] == 'proven' and row['kind'] == 'write'}
    result = []
    for row in accesses:
        if row['kind'] != 'read' or not row.get('reaching_stores'):
            continue
        for store_offset in row['reaching_stores']:
            store = stores.get(store_offset)
            if store is None or store['stack_offset'] != row['stack_offset'] or store['width'] != row['width']:
                continue
            result.append({
                'classification': 'suspected_spill_reload',
                'confidence': 'diagnostic',
                'stack_offset': row['stack_offset'], 'width': row['width'],
                'store_instruction_offset': store_offset,
                'reload_instruction_offset': row['instruction_offset'],
                'note': 'Proven same-range store/reload; compiler spill intent is not proven.',
            })
    return result


def analyze(raw, start=0):
    (instructions, cfg, blocks, rows, in_states, out_states,
     pruned_by_block, steps) = fixed_point(raw, start)
    accesses, aliases, escapes, diagnostics = [], [], [], list(cfg['diagnostics'])
    block_states = []
    for offset in sorted(in_states):
        outgoing, _active, _pruned, transfer = _transfer_block(
            blocks[offset], rows[offset], in_states[offset], collect=True)
        accesses.extend(transfer.accesses)
        aliases.extend(transfer.aliases)
        escapes.extend(transfer.escapes)
        diagnostics.extend(transfer.diagnostics)
        block_states.append({
            'block_offset': offset,
            'entry_known_registers': {str(index): fact.public()
                                      for index, fact in enumerate(in_states[offset].registers)
                                      if fact.kind != 'unknown' or fact.stack_candidates},
            'exit_known_registers': {str(index): fact.public()
                                     for index, fact in enumerate(outgoing.registers)
                                     if fact.kind != 'unknown' or fact.stack_candidates},
            'tracked_stack_values_at_exit': len(outgoing.memory),
            'constant_pruned_successors': pruned_by_block.get(offset, []),
        })
    liveness_report = liveness(cfg, rows)
    counts = Counter(row['classification'] for row in accesses)
    kind_counts = Counter((row['classification'], row['kind']) for row in accesses)
    ambiguities = []
    for block in block_states:
        for register, fact in block['entry_known_registers'].items():
            if fact.get('path_ambiguous'):
                ambiguities.append({'block_offset': block['block_offset'], 'register': int(register), 'fact': fact})
    return {
        'instruction_count': len(instructions),
        'fixed_point_steps': steps,
        'reachable_block_count': len(in_states),
        'total_block_count': len(blocks),
        'register_states': block_states,
        'stack_pointer_aliases': aliases,
        'stack_accesses': {
            'counts': dict(sorted(counts.items())),
            'by_classification_and_direction': {
                f'{classification}_{kind}': count
                for (classification, kind), count in sorted(kind_counts.items())},
            'proven': [row for row in accesses if row['classification'] == 'proven'],
            'potential': [row for row in accesses if row['classification'] == 'potential'],
            'unknown': [row for row in accesses if row['classification'] == 'unknown'],
        },
        'pointer_escapes': escapes,
        'cfg_ambiguities': ambiguities,
        'liveness': liveness_report,
        'suspected_spill_reload_patterns': suspected_spills(accesses),
        'diagnostics': diagnostics,
        '_cfg': cfg,
        '_blocks': blocks,
        '_rows': rows,
        '_in_states': in_states,
        '_out_states': out_states,
    }


def public_analysis(report):
    return {key: value for key, value in report.items() if not key.startswith('_')}
