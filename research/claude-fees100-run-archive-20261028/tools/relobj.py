"""Minimal ELF64 little-endian relocatable object reader/writer (SBF) for diagnostic transplants."""
import struct

class Obj:
    def __init__(self, data):
        self.data = bytearray(data)
        h = struct.unpack_from('<HHIQQQIHHHHHH', data, 16)
        self.hdr = list(h)
        self.shoff, self.shentsize, self.shnum, self.shstrndx = h[5], h[10], h[11], h[12]
        self.sh = []
        for i in range(self.shnum):
            s = dict(zip(('name_off', 'type', 'flags', 'addr', 'offset', 'size', 'link', 'info', 'align', 'entsize'),
                         struct.unpack_from('<IIQQQQIIQQ', data, self.shoff + i * self.shentsize)))
            self.sh.append(s)
        ss = self.sh[self.shstrndx]
        for s in self.sh:
            s['name'] = bytes(data[ss['offset'] + s['name_off']:]).split(b'\0', 1)[0].decode()
        self.contents = [bytes(data[s['offset']:s['offset'] + s['size']]) if s['type'] != 8 else b'' for s in self.sh]
        self.symtab_i = next(i for i, s in enumerate(self.sh) if s['type'] == 2)
        st = self.sh[self.symtab_i]
        self.strtab_i = st['link']
        strs = self.contents[self.strtab_i]
        self.syms = []
        for p in range(0, st['size'], 24):
            nm, info, other, shndx, val, size = struct.unpack_from('<IBBHQQ', self.contents[self.symtab_i], p)
            self.syms.append(dict(name_off=nm, name=strs[nm:].split(b'\0', 1)[0].decode(), info=info, other=other,
                                  shndx=shndx, value=val, size=size))
        self.byname = {}
        for i, s in enumerate(self.sh):
            self.byname.setdefault(s['name'], i)
    def rels(self, i):
        """relocations of section i (the REL section whose sh_info == i)."""
        for j, s in enumerate(self.sh):
            if s['type'] == 9 and s['info'] == i:
                c = self.contents[j]
                return j, [struct.unpack_from('<QQ', c, p) for p in range(0, len(c), 16)]
        return None, []
    def sym_index(self, name):
        for k, s in enumerate(self.syms):
            if s['name'] == name: return k
        return None
    def serialize(self):
        """Lay out all sections afresh (keeping order), rewrite symtab/strtab, headers."""
        # rebuild symtab and strtab contents
        strs = bytearray(b'\0'); offs = {}
        def add(nm):
            if nm == '': return 0
            if nm not in offs:
                offs[nm] = len(strs); strs.extend(nm.encode() + b'\0')
            return offs[nm]
        # keep section-name strings if shstrtab == strtab
        shared = self.shstrndx == self.strtab_i
        if shared:
            for s in self.sh: s['name_off'] = add(s['name'])
        sym = bytearray()
        for s in self.syms:
            sym.extend(struct.pack('<IBBHQQ', add(s['name']), s['info'], s['other'], s['shndx'], s['value'], s['size']))
        self.contents[self.symtab_i] = bytes(sym)
        self.contents[self.strtab_i] = bytes(strs)
        if not shared:
            ss = bytearray(b'\0'); so = {}
            for s in self.sh:
                if s['name'] == '': s['name_off'] = 0; continue
                if s['name'] not in so: so[s['name']] = len(ss); ss.extend(s['name'].encode() + b'\0')
                s['name_off'] = so[s['name']]
            self.contents[self.shstrndx] = bytes(ss)
        out = bytearray(self.data[:64])
        for i, s in enumerate(self.sh):
            if i == 0: continue
            if s['type'] == 8:
                s['offset'] = len(out); continue
            al = max(1, s['align'])
            while len(out) % al: out.append(0)
            s['offset'] = len(out); s['size'] = len(self.contents[i]); out.extend(self.contents[i])
        while len(out) % 8: out.append(0)
        shoff = len(out)
        for s in self.sh:
            out.extend(struct.pack('<IIQQQQIIQQ', s['name_off'], s['type'], s['flags'], s['addr'], s['offset'], s['size'],
                                   s['link'], s['info'], s['align'], s['entsize']))
        h = self.hdr; h[5] = shoff; h[11] = len(self.sh)
        struct.pack_into('<HHIQQQIHHHHHH', out, 16, *h)
        return bytes(out)
