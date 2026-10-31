#!/usr/bin/env python3
"""Read-only instruction-window matching; no executable or normalized bytes are written.

Public window, call and relocation coordinates are file offsets. ELF symbol,
entry and relocation virtual addresses are translated before they are used.
"""
from pathlib import Path
import hashlib
import struct

REPO = next((p for p in Path(__file__).resolve().parents
             if (p / 'evidence/original/pump_fees/deployed.so').is_file()), Path.cwd())


class Elf:
    def __init__(self, path):
        self.path = path
        self.b = b = path.read_bytes()
        if len(b) < 64 or b[:7] != b'\x7fELF\x02\x01\x01':
            raise ValueError('expected ELF64 little endian')
        if struct.unpack_from('<H', b, 18)[0] not in (247, 263):
            raise ValueError('expected BPF or SBPF ELF machine')
        off = struct.unpack_from('<Q', b, 40)[0]
        size, count, ni = struct.unpack_from('<HHH', b, 58)
        if size != 64 or not count or ni >= count or off + size * count > len(b):
            raise ValueError('invalid section table')
        self.raw = [struct.unpack_from('<IIQQQQIIQQ', b, off + i * size) for i in range(count)]
        for section in self.raw:
            if section[1] != 8 and section[4] + section[5] > len(b):
                raise ValueError('section extent exceeds file bytes')
        ns = self.raw[ni]
        if ns[1] != 3:
            raise ValueError('section names must use a string table')
        names = b[ns[4]:ns[4] + ns[5]]
        def string(table, index):
            if index >= len(table) or table.find(b'\0', index) < 0:
                raise ValueError('invalid ELF string offset or missing terminator')
            return table[index:table.index(b'\0', index)].decode()
        self.secs = {}
        for section in self.raw:
            name = string(names, section[0])
            if name and name in self.secs:
                raise ValueError('duplicate named sections are unsupported')
            self.secs[name] = section
        self.text = self.secs['.text']
        self.lo = self.text[4]
        self.hi = self.lo + self.text[5]
        if self.text[1] != 1 or not self.text[2] & 4 or self.text[5] % 8:
            raise ValueError('invalid text extent')
        # LDDW's second slot contains immediate data, regardless of whether its
        # bytes happen to resemble an opcode. Never decode or normalize it alone.
        instructions = set()
        at = self.lo
        while at < self.hi:
            instructions.add(at)
            width = 16 if b[at] == 0x18 else 8
            if at + width > self.hi:
                raise ValueError('truncated SBF instruction in text')
            at += width

        self.symbols, self.funcs = {}, []
        symbol_tables = {}
        for kind in ('.dynsym', '.symtab'):
            if kind not in self.secs:
                continue
            section = self.secs[kind]
            expected_type = 11 if kind == '.dynsym' else 2
            if section[1] != expected_type or section[9] != 24 or section[5] % 24 or section[6] >= count:
                raise ValueError('invalid symbol table')
            strings_section = self.raw[section[6]]
            if strings_section[1] != 3:
                raise ValueError('symbol names must use a string table')
            strings = b[strings_section[4]:strings_section[4] + strings_section[5]]
            table_symbols = {}
            for index, pos in enumerate(range(section[4], section[4] + section[5], 24)):
                n, info, _, idx, value, length = struct.unpack_from('<IBBHQQ', b, pos)
                name = string(strings, n)
                table_symbols[index] = name
                if kind == '.dynsym':
                    self.symbols[index] = name
                if info & 15 == 2 and length and idx < count and self.raw[idx] == self.text:
                    start = self.lo + value - self.text[3]
                    end = start + length
                    if (start not in instructions or end > self.hi or
                            (end != self.hi and end not in instructions)):
                        raise ValueError(f'invalid function extent for {name!r}')
                    self.funcs.append({'name': name, 'start': start, 'size': length})
            symbol_tables[self.raw.index(section)] = table_symbols
        self.relocations = {}
        self.entries = {f['start'] for f in self.funcs}
        entry = self.text_offset(struct.unpack_from('<Q', b, 24)[0])
        if entry in instructions:
            self.entries.add(entry)
        if '.rel.dyn' in self.secs:
            section = self.secs['.rel.dyn']
            if section[1] != 9 or section[9] != 16 or section[5] % 16:
                raise ValueError('invalid relocation table')
            if section[5] and section[6] not in symbol_tables:
                raise ValueError('relocation table must link to a supported symbol table')
            relocation_symbols = symbol_tables.get(section[6], {})
            for pos in range(section[4], section[4] + section[5], 16):
                address, info = struct.unpack_from('<QQ', b, pos)
                at = self.file_offset(address, 8)
                if info >> 32 not in relocation_symbols:
                    raise ValueError('relocation symbol index is outside the linked table')
                typ, symbol = info & 0xffffffff, relocation_symbols[info >> 32]
                if self.lo <= at < self.hi and typ in (8, 10):
                    expected_opcode = 0x18 if typ == 8 else 0x85
                    if at not in instructions or b[at] != expected_opcode:
                        raise ValueError('text relocation does not target a logical instruction')
                self.relocations[at] = {'type': typ, 'symbol': symbol}
                if typ == 8:
                    if at in instructions and b[at] == 0x18:
                        ptr = struct.unpack_from('<I', b, at + 4)[0] | (struct.unpack_from('<I', b, at + 12)[0] << 32)
                    else:
                        if at + 8 > len(b):
                            raise ValueError('relocation extent exceeds file bytes')
                        ptr = struct.unpack_from('<Q', b, at)[0] >> 32
                    target = self.text_offset(ptr)
                    if target in instructions:
                        self.entries.add(target)
        self.calls = {}
        norm = bytearray(b)
        for at in sorted(instructions):
            relocation = self.relocations.get(at, {}).get('type')
            # Relocated external calls are not self-calls or entry evidence.
            if b[at] == 0x85 and b[at + 1] == 0x10 and relocation != 10:
                immediate = struct.unpack_from('<i', b, at + 4)[0]
                target = at + 8 + immediate * 8
                self.calls[at] = target
                norm[at + 4:at + 8] = bytes(4)
                if target in instructions:
                    self.entries.add(target)
            if relocation == 8 and b[at] == 0x18:
                norm[at + 4:at + 8] = bytes(4)
                norm[at + 12:at + 16] = bytes(4)
            elif relocation == 10 and b[at] == 0x85:
                norm[at + 4:at + 8] = bytes(4)
        self.normalized = bytes(norm)
        self.entries = sorted(self.entries)

    def text_offset(self, address):
        if self.text[3] <= address < self.text[3] + self.text[5]:
            return self.lo + address - self.text[3]
        return None

    def file_offset(self, address, size=1):
        for section in self.raw:
            if (section[2] & 2 and section[1] != 8 and
                    section[3] <= address and address + size <= section[3] + section[5]):
                return section[4] + address - section[3]
        raise ValueError(f'relocation extent is not in a file-backed section: {address:#x}+{size}')

    def pattern(self, start, size):
        selected = ((at, r) for at, r in self.relocations.items()
                    if start <= at < start + size)
        return [{'offset': at - start, **r} for at, r in sorted(selected)]

    def callsites(self, start, size):
        return [{'offset': at - start, 'target': target} for at, target in self.calls.items()
                if start <= at < start + size]

    def identity(self):
        return {'path': self.path.relative_to(REPO).as_posix(),
                'sha256': hashlib.sha256(self.b).hexdigest(),
                'text_sha256': hashlib.sha256(self.b[self.lo:self.hi]).hexdigest()}
