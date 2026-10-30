"""Positional field differences of normalized legacy SBF instructions, diagnostic only."""
import struct
from collections import Counter
from instruction_stream import instruction_offsets


def decode(raw, offset):
    op, regs, displacement, immediate = struct.unpack_from('<BBhi', raw, offset)
    if op == 0x18:
        immediate = (immediate & 0xffffffff) | (struct.unpack_from('<I', raw, offset + 12)[0] << 32)
    return dict(opcode=op, dst=regs & 15, src=regs >> 4,
                displacement=displacement, immediate=immediate)


def field_differences(original, candidate, limit=12):
    """Inputs must already use score.normalize; never align LDDW payloads as opcodes."""
    if limit < 0:
        raise ValueError('limit must be nonnegative')
    left, right = list(instruction_offsets(original)), list(instruction_offsets(candidate))
    if len(original) != len(candidate) or left != right:
        return {'comparable': False, 'reason': 'instruction boundaries or byte lengths differ'}
    counts, rows = Counter(), []
    for offset in left:
        a, b = decode(original, offset), decode(candidate, offset)
        fields = {key: {'original': a[key], 'candidate': b[key]} for key in a if a[key] != b[key]}
        # Preserve visibility of changed reserved LDDW continuation fields.
        if original[offset] == candidate[offset] == 0x18 and original[offset+8:offset+12] != candidate[offset+8:offset+12]:
            fields['lddw_reserved'] = {'original': original[offset+8:offset+12].hex(),
                                       'candidate': candidate[offset+8:offset+12].hex()}
        counts.update(fields.keys())
        if fields and len(rows) < limit:
            rows.append({'offset': offset, 'fields': fields})
    return {'comparable': True, 'field_counts': dict(sorted(counts.items())), 'first_differences': rows}
