"""Bounded ELF64 little-endian symbol reader for unstripped SBF candidates.

No SDK subprocess is required. Deliberately reads SHT_SYMTAB, like objdump -t;
export-only dynamic tables are not substitutes for a complete function inventory.
"""
import struct


def function_symbols(blob):
    def span(offset, size, label):
        if offset < 0 or size < 0 or offset > len(blob) or size > len(blob) - offset:
            raise ValueError(f'{label} extends outside the ELF file')
        return blob[offset:offset + size]

    if len(blob) < 64 or blob[:7] != b'\x7fELF\x02\x01\x01':
        raise ValueError('expected an ELF64 little-endian version-1 image')
    if struct.unpack_from('<H', blob, 18)[0] not in (247, 263):
        raise ValueError('expected an EM_BPF or EM_SBPF candidate image')
    shoff = struct.unpack_from('<Q', blob, 40)[0]
    entry_size, count, names_index = struct.unpack_from('<HHH', blob, 58)
    if entry_size != 64 or not count or names_index >= count:
        raise ValueError('unsupported or invalid ELF section table')
    span(shoff, count * entry_size, 'section table')
    headers = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * entry_size) for i in range(count)]

    def section_data(header, label):
        return span(header[4], header[5], label)

    def string(table, offset, label):
        if offset >= len(table):
            raise ValueError(f'{label} string offset is outside its table')
        end = table.find(b'\0', offset)
        if end < 0:
            raise ValueError(f'{label} string is unterminated')
        return table[offset:end].decode('utf-8')

    if headers[names_index][1] != 3:
        raise ValueError('section names must reference a string table')
    names = section_data(headers[names_index], 'section names')
    section_names = [string(names, h[0], 'section name') for h in headers]
    text_indices = {i for i, name in enumerate(section_names) if name == '.text'}
    if len(text_indices) != 1:
        raise ValueError('expected exactly one .text section')
    text_index = next(iter(text_indices))
    text = headers[text_index]
    if text[1] != 1 or not text[2] & 4:
        raise ValueError('.text must contain executable PROGBITS')
    section_data(text, '.text')
    functions = []
    seen = set()
    for header in headers:
        if header[1] != 2:  # SHT_SYMTAB
            continue
        if header[9] != 24 or header[5] % 24 or header[6] >= count:
            raise ValueError('invalid symbol-table entry size or linked string table')
        strings_header = headers[header[6]]
        if strings_header[1] != 3:
            raise ValueError('symbol names must reference a string table')
        strings = section_data(strings_header, 'symbol strings')
        symbols = section_data(header, 'symbol table')
        for offset in range(0, len(symbols), 24):
            name_offset, info, visibility, section_index, address, size = struct.unpack_from('<IBBHQQ', symbols, offset)
            if info & 15 != 2 or section_index != text_index or not size:
                continue
            if address < text[3] or address - text[3] + size > text[5]:
                raise ValueError('function symbol extends outside .text')
            if address % 8 or size % 8:
                raise ValueError('SBF function symbols must contain aligned instruction slots')
            name = string(strings, name_offset, 'symbol name')
            row = (address, size, name)
            if row not in seen:
                seen.add(row)
                functions.append(row)
    return functions
