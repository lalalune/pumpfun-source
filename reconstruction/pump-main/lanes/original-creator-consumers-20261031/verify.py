#!/usr/bin/env python3
"""Read-only, fixed-original, two-body direct-dataflow replay. Stdlib only."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC_SHA256 = '527bd086508ea5fda0a595c1014f1bea836db712427adb10de6f1acc8bbb186e'
INPUTS_SHA256 = '1706472e074420c43aeef24c79c84d3af621084a54ad5044172ffc528a598a3d'
# A domain commitment is independent of vectors in queries.json.
QUERY_DOMAIN = (('cto-abort_cut-frame-4b08--1408-8', 'cto', 'abort_cut', 'frame', 19208, -1408, 8, None, None), ('cto-abort_cut-frame-4b18--1400-8', 'cto', 'abort_cut', 'frame', 19224, -1400, 8, None, None), ('cto-abort_cut-frame-4b28--1392-8', 'cto', 'abort_cut', 'frame', 19240, -1392, 8, None, None), ('cto-abort_cut-frame-4b38--1384-8', 'cto', 'abort_cut', 'frame', 19256, -1384, 8, None, None), ('cto-abort_cut-frame-4a78--1617-1', 'cto', 'abort_cut', 'frame', 19064, -1617, 1, None, None), ('cto-abort_cut-frame-3d28--1360-4', 'cto', 'abort_cut', 'frame', 15656, -1360, 4, None, None), ('cto-abort_cut-frame-3d38--1357-4', 'cto', 'abort_cut', 'frame', 15672, -1357, 4, None, None), ('cto-abort_cut-frame-3d48--2376-8', 'cto', 'abort_cut', 'frame', 15688, -2376, 8, None, None), ('cto-abort_cut-frame-3d58--2304-8', 'cto', 'abort_cut', 'frame', 15704, -2304, 8, None, None), ('cto-abort_cut-frame-3d68--1376-8', 'cto', 'abort_cut', 'frame', 15720, -1376, 8, None, None), ('cto-abort_cut-frame-3d78--1368-1', 'cto', 'abort_cut', 'frame', 15736, -1368, 1, None, None), ('cto-abort_cut-frame-4a78--1616-32', 'cto', 'abort_cut', 'frame', 19064, -1616, 32, None, None), ('cto-abort_cut-frame-1538--2376-8', 'cto', 'abort_cut', 'frame', 5432, -2376, 8, None, None), ('cto-abort_cut-frame-1858--1621-4', 'cto', 'abort_cut', 'frame', 6232, -1621, 4, None, None), ('cto-abort_cut-frame-1868--1624-4', 'cto', 'abort_cut', 'frame', 6248, -1624, 4, None, None), ('cto-abort_cut-frame-1878--1640-8', 'cto', 'abort_cut', 'frame', 6264, -1640, 8, None, None), ('cto-abort_cut-frame-1888--1632-1', 'cto', 'abort_cut', 'frame', 6280, -1632, 1, None, None), ('cto-uncut-frame-3d48--2376-8', 'cto', 'uncut', 'frame', 15688, -2376, 8, None, None), ('cto-uncut-frame-3d58--2304-8', 'cto', 'uncut', 'frame', 15704, -2304, 8, None, None), ('cto-reg-0xc60_r3', 'cto', 'abort_cut', 'reg', 3168, None, None, 3, None), ('cto-reg-0x5e8_r9', 'cto', 'abort_cut', 'reg', 1512, None, None, 9, None), ('cto-reg-0x10f0_r3', 'cto', 'abort_cut', 'reg', 4336, None, None, 3, None), ('cto-reg-0x1808_r3', 'cto', 'abort_cut', 'reg', 6152, None, None, 3, None), ('cto-reg-0x3d20_r6', 'cto', 'abort_cut', 'reg', 15648, None, None, 6, None), ('cto-reg-0x4ac0_r3', 'cto', 'abort_cut', 'reg', 19136, None, None, 3, None), ('cto-value-reg-4f0-2', 'cto', 'abort_cut', 'reg', 1264, None, None, 2, None), ('cto-value-reg-500-2', 'cto', 'abort_cut', 'reg', 1280, None, None, 2, None), ('cto-value-reg-510-2', 'cto', 'abort_cut', 'reg', 1296, None, None, 2, None), ('cto-value-reg-528-2', 'cto', 'abort_cut', 'reg', 1320, None, None, 2, None), ('cto-value-reg-538-2', 'cto', 'abort_cut', 'reg', 1336, None, None, 2, None), ('cto-value-reg-c60-3', 'cto', 'abort_cut', 'reg', 3168, None, None, 3, None), ('cto-value-reg-10f0-3', 'cto', 'abort_cut', 'reg', 4336, None, None, 3, None), ('cto-value-reg-1808-3', 'cto', 'abort_cut', 'reg', 6152, None, None, 3, None), ('cto-value-reg-19d8-1', 'cto', 'abort_cut', 'reg', 6616, None, None, 1, None), ('cto-value-reg-19e8-1', 'cto', 'abort_cut', 'reg', 6632, None, None, 1, None), ('cto-value-reg-19f8-1', 'cto', 'abort_cut', 'reg', 6648, None, None, 1, None), ('cto-value-reg-1a08-1', 'cto', 'abort_cut', 'reg', 6664, None, None, 1, None), ('cto-value-reg-1a18-1', 'cto', 'abort_cut', 'reg', 6680, None, None, 1, None), ('cto-value-reg-1a28-1', 'cto', 'abort_cut', 'reg', 6696, None, None, 1, None), ('cto-value-reg-1a38-1', 'cto', 'abort_cut', 'reg', 6712, None, None, 1, None), ('cto-value-reg-1a48-1', 'cto', 'abort_cut', 'reg', 6728, None, None, 1, None), ('cto-value-reg-3d20-6', 'cto', 'abort_cut', 'reg', 15648, None, None, 6, None), ('cto-value-reg-3d30-1', 'cto', 'abort_cut', 'reg', 15664, None, None, 1, None), ('cto-value-reg-3d40-1', 'cto', 'abort_cut', 'reg', 15680, None, None, 1, None), ('cto-value-reg-3d50-1', 'cto', 'abort_cut', 'reg', 15696, None, None, 1, None), ('cto-value-reg-3d60-1', 'cto', 'abort_cut', 'reg', 15712, None, None, 1, None), ('cto-value-reg-3d70-1', 'cto', 'abort_cut', 'reg', 15728, None, None, 1, None), ('cto-value-reg-3d80-1', 'cto', 'abort_cut', 'reg', 15744, None, None, 1, None), ('cto-value-reg-4a78-3', 'cto', 'abort_cut', 'reg', 19064, None, None, 3, None), ('cto-value-reg-4a70-3', 'cto', 'abort_cut', 'reg', 19056, None, None, 3, None), ('cto-value-reg-4b10-1', 'cto', 'abort_cut', 'reg', 19216, None, None, 1, None), ('cto-value-reg-4b10-2', 'cto', 'abort_cut', 'reg', 19216, None, None, 2, None), ('cto-value-reg-4b20-2', 'cto', 'abort_cut', 'reg', 19232, None, None, 2, None), ('cto-value-reg-4b30-2', 'cto', 'abort_cut', 'reg', 19248, None, None, 2, None), ('cto-value-reg-4b40-2', 'cto', 'abort_cut', 'reg', 19264, None, None, 2, None), ('helper-constructed-frame--96', 'helper', 'uncut', 'frame', 2456, -96, 8, None, 680), ('helper-constructed-frame--88', 'helper', 'uncut', 'frame', 2456, -88, 8, None, 672), ('helper-value-reg-2a8-6', 'helper', 'uncut', 'reg', 680, None, None, 6, None), ('helper-value-reg-2a0-9', 'helper', 'uncut', 'reg', 672, None, None, 9, None), ('helper-value-reg-998-2', 'helper', 'uncut', 'reg', 2456, None, None, 2, None), ('helper-value-reg-978-2', 'helper', 'uncut', 'reg', 2424, None, None, 2, None), ('helper-value-reg-e0-4', 'helper', 'uncut', 'reg', 224, None, None, 4, None), ('helper-value-reg-100-3', 'helper', 'uncut', 'reg', 256, None, None, 3, None), ('helper-value-reg-110-3', 'helper', 'uncut', 'reg', 272, None, None, 3, None), ('helper-value-reg-118-1', 'helper', 'uncut', 'reg', 280, None, None, 1, None), ('helper-value-reg-128-1', 'helper', 'uncut', 'reg', 296, None, None, 1, None), ('helper-value-reg-138-1', 'helper', 'uncut', 'reg', 312, None, None, 1, None), ('helper-value-reg-148-1', 'helper', 'uncut', 'reg', 328, None, None, 1, None), ('helper-length-spill-before-restore', 'helper', 'uncut', 'frame', 1368, -176, 8, None, None), ('helper-length-source-before-spill', 'helper', 'uncut', 'reg', 904, None, None, 9, None))


class Refusal(Exception):
    pass


def require(condition, label):
    if not condition:
        raise Refusal(label)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_file(path, expected):
    data = path.read_bytes()
    require(len(data) == expected['bytes'] and digest(data) == expected['sha256'], 'input bytes: ' + str(path))
    return data


class ELF:
    def __init__(self, data):
        self.data = data
        require(data[:7] == b'\x7fELF\x02\x01\x01' and len(data) >= 64, 'ELF64 little endian')
        require(struct.unpack_from('<H', data, 18)[0] in (247, 263), 'ELF SBF machine')
        require(struct.unpack_from('<I', data, 48)[0] in (0, 1), 'legacy SBPFv0/v1 only')
        shoff = struct.unpack_from('<Q', data, 40)[0]
        width, count, names = struct.unpack_from('<HHH', data, 58)
        require(width == 64 and count > 0 and names < count, 'section table shape')
        self.span(shoff, width * count)
        self.headers = [struct.unpack_from('<IIQQQQIIQQ', data, shoff + i * width) for i in range(count)]
        strings = self.payload(self.headers[names])
        self.sections = {}
        for h in self.headers:
            name = self.string(strings, h[0])
            require(name not in self.sections, 'duplicate ELF section')
            self.sections[name] = h
        require('.text' in self.sections and self.sections['.text'][2] & 4, 'executable text')

    def span(self, offset, count):
        require(0 <= offset <= len(self.data) and 0 <= count <= len(self.data) - offset, 'file span bounds')
        return self.data[offset:offset + count]

    def payload(self, h):
        require(h[1] != 8, 'file-backed section')
        return self.span(h[4], h[5])

    @staticmethod
    def string(table, offset):
        require(0 <= offset < len(table), 'string offset')
        end = table.find(b'\0', offset)
        require(end >= 0, 'unterminated string')
        return table[offset:end].decode('utf-8')

    def at(self, address, count):
        candidates = [h for h in self.headers if h[1] != 8 and h[2] & 2 and h[3] <= address and count <= h[3] + h[5] - address]
        require(len(candidates) == 1, 'ambiguous/unmapped VA range')
        h = candidates[0]
        return self.span(h[4] + address - h[3], count)

    def abort_binding(self):
        require('.rel.dyn' in self.sections and '.dynsym' in self.sections, 'dynamic relocation sections')
        rel, dyn = self.sections['.rel.dyn'], self.sections['.dynsym']
        require(rel[1] == 9 and rel[9] == 16 and rel[5] % 16 == 0, 'REL entry format')
        require(rel[6] < len(self.headers) and self.headers[rel[6]] == dyn, 'REL sh_link must identify the named dynamic symbol table')
        require(dyn[1] == 11 and dyn[9] == 24 and dyn[5] % 24 == 0 and dyn[6] < len(self.headers), 'dynamic symbol format')
        strings = self.payload(self.headers[dyn[6]])
        found = []
        for offset in range(rel[4], rel[4] + rel[5], 16):
            address, info = struct.unpack('<QQ', self.span(offset, 16))
            if address != 0x250f0:
                continue
            index, kind = info >> 32, info & 0xffffffff
            require(index < dyn[5] // 24, 'dynamic symbol index')
            symbol = struct.unpack('<IBBHQQ', self.span(dyn[4] + 24 * index, 24))
            found.append((kind, self.string(strings, symbol[0])))
        require(found == [(10, 'abort')], 'exact abort relocation VA250f0/type10/symbol')
        require(self.at(0x250f0, 8).hex() == '85100000ffffffff', 'exact relocated abort call bytes')
        return {'va': '0x250f0', 'relative_cto': '0x26e0', 'type': 10, 'symbol': 'abort'}


LOAD = {0x61: 4, 0x69: 2, 0x71: 1, 0x79: 8}
STORE_IMM = {0x62: 4, 0x6a: 2, 0x72: 1, 0x7a: 8}
STORE_REG = {0x63: 4, 0x6b: 2, 0x73: 1, 0x7b: 8}
STORE = STORE_IMM.copy()
STORE.update(STORE_REG)
ALU = {cls + operation + src for cls in (4, 7) for operation in (0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x90, 0xa0, 0xb0, 0xc0) for src in (0, 8)} | {0x84, 0x87, 0xd4, 0xdc}
COND = {cls + condition + src for cls in (5, 6) for condition in (0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0xa0, 0xb0, 0xc0, 0xd0) for src in (0, 8)}


def decode(raw, base):
    rows = {}
    offset = 0
    while offset < len(raw):
        require(offset + 8 <= len(raw), 'truncated instruction')
        op, regs, displacement, immediate = struct.unpack_from('<BBhi', raw, offset)
        dst, src = regs & 15, regs >> 4
        require(dst <= 10 and src <= 10, 'register domain')
        width = 16 if op == 0x18 else 8
        require(offset + width <= len(raw), 'truncated LDDW')
        row = {'pc': offset, 'op': op, 'dst': dst, 'src': src, 'disp': displacement, 'imm': immediate, 'size': width, 'raw': raw[offset:offset + width].hex()}
        if op == 0x18:
            require(dst < 10 and src == 0 and displacement == 0 and raw[offset + 8:offset + 12] == b'\0' * 4, 'LDDW encoding')
            row['value'] = (immediate & 0xffffffff) | (struct.unpack_from('<I', raw, offset + 12)[0] << 32)
        elif op in LOAD:
            require(dst < 10 and immediate == 0, 'LDX encoding')
        elif op in STORE_IMM:
            require(src == 0, 'store-immediate encoding')
        elif op in STORE_REG:
            require(immediate == 0, 'store-register encoding')
        elif op in ALU:
            require(dst < 10 and displacement == 0, 'ALU encoding')
            if op in (0xd4, 0xdc):
                require(src == 0 and immediate in (16, 32, 64), 'endian encoding')
            elif op in (0x84, 0x87):
                require(src == 0 and immediate == 0, 'negation encoding')
            elif op & 8:
                require(immediate == 0, 'ALU register encoding')
            else:
                require(src == 0, 'ALU immediate encoding')
        elif op == 0x05:
            require(dst == src == immediate == 0, 'JA encoding')
            row['jump'] = offset + 8 + displacement * 8
        elif op in COND:
            require(immediate == 0 if op & 8 else src == 0, 'conditional encoding')
            row['jump'] = offset + 8 + displacement * 8
        elif op == 0x85:
            require(dst == 0 and src == 1 and displacement == 0, 'relative/relocated CALL only')
            if immediate != -1:
                row['call'] = base + offset + 8 + immediate * 8
        elif op == 0x95:
            require(dst == src == displacement == immediate == 0, 'EXIT encoding')
        else:
            raise Refusal('unsupported affecting opcode 0x%x at 0x%x' % (op, base + offset))
        rows[offset] = row
        offset += width
    require(offset == len(raw), 'complete fixed body')
    return rows


class Graph:
    def __init__(self, rows, cuts=()):
        self.rows = rows
        self.succ = {}
        self.pred = {pc: [] for pc in rows}
        for pc, row in rows.items():
            op, nextpc = row['op'], pc + row['size']
            if op == 0x95 or pc in cuts:
                dest = []
            elif op == 0x05:
                dest = [row['jump']]
            elif op in COND:
                dest = [row['jump'], nextpc]
            else:
                dest = [nextpc]
            require(all(d in rows for d in dest), 'branch/fallthrough into continuation or outside fixed body')
            self.succ[pc] = dest
            for d in dest:
                self.pred[d].append(pc)

    def reachable(self, start):
        pending, seen = [start], set()
        while pending:
            pc = pending.pop()
            if pc not in seen:
                seen.add(pc)
                pending.extend(self.succ[pc])
        return seen

    def nearest(self, pc, predicate, anchor=None):
        require(pc in self.rows and (anchor is None or anchor in self.rows), 'query logical boundary')
        permitted = self.reachable(anchor) if anchor is not None else set(self.rows)
        require(pc in permitted, 'anchor cannot reach consumer')
        pending, seen, found, missing = list(self.pred[pc]), set(), set(), False
        while pending:
            q = pending.pop()
            if q not in permitted or q in seen:
                continue
            seen.add(q)
            if predicate(self.rows[q]):
                found.add(q)
                continue
            predecessors = [p for p in self.pred[q] if p in permitted]
            if q == anchor or not predecessors:
                missing = True
                continue
            pending.extend(predecessors)
        return sorted(found), missing

    def frame_byte(self, pc, address, anchor=None):
        return self.nearest(pc, lambda r: r['op'] in STORE and r['dst'] == 10 and r['disp'] <= address < r['disp'] + STORE[r['op']], anchor)

    def register(self, pc, register):
        return self.nearest(pc, lambda r: (r['dst'] == register and (r['op'] in LOAD or r['op'] in ALU or r['op'] == 0x18)) or (r['op'] == 0x85 and register < 6))


def compare_witness(rows, values):
    require(len({w['pc'] for w in values}) == len(values), 'unique raw witness PCs')
    for witness in values:
        pc = witness['pc']
        require(pc in rows and rows[pc]['raw'] == witness['raw'], 'raw operand witness %x' % pc)


def run(repo):
    spec_bytes = (HERE / 'queries.json').read_bytes()
    input_bytes = (HERE / 'inputs.json').read_bytes()
    require(digest(spec_bytes) == SPEC_SHA256 and digest(input_bytes) == INPUTS_SHA256, 'fixed packet spec/input commitment')
    spec, inputs = json.loads(spec_bytes), json.loads(input_bytes)
    require(tuple((q['id'], q['body'], q['graph'], q['kind'], q['pc'], q.get('frame'), q.get('bytes'), q.get('reg'), q.get('anchor')) for q in spec['queries']) == QUERY_DOMAIN, 'complete fixed query domain/order/dimensions')
    elfdata = checked_file(repo / inputs['original']['path'], inputs['original'])
    elf = ELF(elfdata)
    abort = elf.abort_binding()
    bodies = {}
    for name in ('cto', 'helper'):
        item = inputs['bodies'][name]
        raw = elf.at(item['address'], item['bytes'])
        require(digest(raw) == item['sha256'], 'fixed ' + name + ' body hash')
        bodies[name] = decode(raw, item['address'])
        require(len(bodies[name]) == item['instructions'], 'fixed logical instruction count')
        compare_witness(bodies[name], spec['witnesses'][name])
    graphs = {('cto', 'uncut'): Graph(bodies['cto']), ('cto', 'abort_cut'): Graph(bodies['cto'], (0x26e0,)), ('helper', 'uncut'): Graph(bodies['helper'])}
    reports = []
    for q in spec['queries']:
        graph = graphs[q['body'], q['graph']]
        if q['kind'] == 'frame':
            require(len(q['expected']) == q['bytes'] and q['bytes'] > 0, 'full byte vector')
            actual = [graph.frame_byte(q['pc'], q['frame'] + i, q.get('anchor')) for i in range(q['bytes'])]
        else:
            require(q['kind'] == 'reg' and len(q['expected']) == 1 and 0 <= q['reg'] <= 10 and q.get('anchor') is None, 'register query schema')
            actual = [graph.register(q['pc'], q['reg'])]
        expected = [(entry['writers'], entry['entry']) for entry in q['expected']]
        require(all(sorted(set(w)) == w for w, _ in expected), 'canonical expected writer sets')
        require(actual == expected, 'exact reaching set/entry result: ' + q['id'])
        reports.append({'id': q['id'], 'body': q['body'], 'graph': q['graph'], 'conditional_anchor': q.get('anchor'), 'actual': [{'writers': w, 'entry': e} for w, e in actual]})
    # Every claimed direct-FP helper persistence store is inventoried too.
    helper = bodies['helper']
    for address, expected in ((-96, [0x2a8]), (-88, [0x2a0])):
        actual = [pc for pc, r in helper.items() if pc < 0x998 and r['op'] in STORE and r['dst'] == 10 and r['disp'] < address + 8 and address < r['disp'] + STORE[r['op']]]
        require(actual == expected, 'helper direct store census')
    cto = bodies['cto']
    require(cto[0x4a78].get('call') == 0x116718 and helper[0x998].get('call') == 0x1a0530, 'actual call targets')
    require(helper[0xb8]['value'].to_bytes(8, 'little') == bytes(inputs['Fees_method']['discriminator']), 'actual method discriminator')
    # The raw gates and complete graph prove reset skips payload on the declared valid tag path.
    require(helper[0xe0]['op'] == 0x55 and helper[0xe0]['dst'] == 4 and helper[0xe0]['imm'] == 0 and helper[0xe0]['jump'] == 0x100, 'helper Some/None gate')
    require(helper[0xf8]['op'] == 0x05 and helper[0xf8]['jump'] == 0x158, 'None skips payload block')
    def operands(rows, pc, op, dst, src, disp, imm):
        row = rows[pc]
        require([row[k] for k in ('op', 'dst', 'src', 'disp', 'imm')] == [op, dst, src, disp, imm], 'typed operand relation at %x' % pc)
    operands(helper, 0x98, 0x71, 4, 3, 0, 0)
    operands(helper, 0x100, 0x07, 3, 0, 0, 1)
    operands(helper, 0xe8, 0x72, 6, 0, 8, 0)
    operands(helper, 0x108, 0x72, 6, 0, 8, 1)
    operands(helper, 0xf0, 0xb7, 9, 0, 0, 9)
    operands(helper, 0x150, 0xb7, 9, 0, 0, 41)
    for load, store, source, destination in ((0x110, 0x118, 0, 9), (0x120, 0x128, 8, 17), (0x130, 0x138, 16, 25), (0x140, 0x148, 24, 33)):
        operands(helper, load, 0x79, 1, 3, source, 0)
        operands(helper, store, 0x7b, 6, 1, destination, 0)
    # Account-meta iteration saves the selected 9/41 length and restores R9.
    # The two fixed reaching queries prove this is a value relay, not a new length.
    operands(helper, 0x388, 0x7b, 10, 9, -176, 0)
    operands(helper, 0x558, 0x79, 9, 10, -176, 0)
    operands(helper, 0x2a8, 0x7b, 10, 6, -96, 0)
    operands(helper, 0x2a0, 0x7b, 10, 9, -88, 0)
    operands(helper, 0x970, 0xbf, 2, 10, 0, 0)
    operands(helper, 0x978, 0x07, 2, 0, 0, -128)
    operands(cto, 0x4a68, 0xbf, 3, 10, 0, 0)
    operands(cto, 0x4a70, 0x07, 3, 0, 0, -1617)
    operands(cto, 0x4ac0, 0x79, 1, 3, 56, 0)
    for load, store, frame, destination in ((0x4b08, 0x4b10, -1408, 8), (0x4b18, 0x4b20, -1400, 16), (0x4b28, 0x4b30, -1392, 24), (0x4b38, 0x4b40, -1384, 32)):
        operands(cto, load, 0x79, 2, 10, frame, 0)
        operands(cto, store, 0x7b, 1, 2, destination, 0)
    require(cto[0x3d10]['op'] == 0x55 and cto[0x3d10]['imm'] == 2 and cto[0x3d18]['op'] == 0x05 and cto[0x3d18]['jump'] == 0x4aa8, 'outer skip gate')
    return {'status': 'PASS_BOUNDED_BYTES_CFG_DIRECT_FP_CONDITIONAL_ROLES', 'original': inputs['original'], 'body_hashes': {k: v['sha256'] for k, v in inputs['bodies'].items()}, 'abort': abort, 'queries': reports, 'query_count': len(reports), 'external_premises': inputs['external_premises'], 'scope': 'Packed objects to instruction-data construction/handoff; initial producer relay/persistence is externally credited to05e4/phase proofs. Not successful Fees state mutation, original Rust type/private signature/lifetime or arbitrary alias theorem.', 'actions': 'Read-only stdlib replay; no compiler/scorer/metric/VM/tests/subprocess/network/source/Git/PR action.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.repo.resolve())
    except (Refusal, ValueError, KeyError, IndexError, struct.error, OSError) as exc:
        print(json.dumps({'status': 'FAIL_CLOSED', 'reason': str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
