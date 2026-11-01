"""Walk and decode complete legacy-SBPF instructions for diagnostic metrics."""
import struct


def instruction_offsets(raw):
    offset = 0
    while offset < len(raw):
        width = 16 if raw[offset] == 0x18 else 8
        if offset + width > len(raw):
            raise ValueError(f'truncated instruction at byte {offset}: need {width} bytes')
        yield offset
        offset += width


def instruction_boundaries(raw):
    """Return every logical start plus the complete stream end."""
    boundaries = {0}
    for offset in instruction_offsets(raw):
        boundaries.add(offset)
    boundaries.add(len(raw))
    return frozenset(boundaries)


def decode_instructions(raw, start=0):
    """Decode a complete stream, treating two-slot LDDW as one instruction.

    The decoder deliberately preserves the continuation slot's reserved bytes.
    It describes the legacy instruction fields without interpreting them as
    source operations or changing the scorer's normalization.
    """
    if type(start) is not int or start < 0 or start % 8:
        raise ValueError('instruction stream start must be a nonnegative aligned address')
    result = []
    for offset in instruction_offsets(raw):
        opcode, registers, displacement, immediate = struct.unpack_from('<BBhi', raw, offset)
        width = 16 if opcode == 0x18 else 8
        row = {
            'offset': offset,
            'address': start + offset,
            'width': width,
            'opcode': opcode,
            'dst': registers & 15,
            'src': registers >> 4,
            'displacement': displacement,
            'immediate': immediate,
            'bytes': bytes(raw[offset:offset + width]),
        }
        if width == 16:
            row['immediate'] = ((immediate & 0xffffffff)
                                | (struct.unpack_from('<I', raw, offset + 12)[0] << 32))
            row['lddw_reserved'] = bytes(raw[offset + 8:offset + 12])
        result.append(row)
    return result


def require_instruction_range(raw, start, size):
    """Validate a slice against logical boundaries in its enclosing code stream."""
    end = start + size
    if start < 0 or size <= 0 or end > len(raw):
        raise ValueError('instruction range is outside the enclosing code stream')
    # Decode from the section origin, not from the requested slice: a slot at
    # start can be the continuation of an LDDW that began eight bytes earlier.
    starts = instruction_offsets(raw[:end])
    found_start = False
    for offset in starts:
        found_start |= offset == start
    if not found_start:
        raise ValueError('range start is not a logical instruction boundary (lddw continuation)')
