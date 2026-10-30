"""Walk instruction boundaries for diagnostic metrics, without normalizing bytes."""


def instruction_offsets(raw):
    offset = 0
    while offset < len(raw):
        width = 16 if raw[offset] == 0x18 else 8
        if offset + width > len(raw):
            raise ValueError(f'truncated instruction at byte {offset}: need {width} bytes')
        yield offset
        offset += width
