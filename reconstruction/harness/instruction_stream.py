"""Walk instruction boundaries for diagnostic metrics, without normalizing bytes."""


def instruction_offsets(raw):
    offset = 0
    while offset < len(raw):
        width = 16 if raw[offset] == 0x18 else 8
        if offset + width > len(raw):
            raise ValueError(f'truncated instruction at byte {offset}: need {width} bytes')
        yield offset
        offset += width


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
