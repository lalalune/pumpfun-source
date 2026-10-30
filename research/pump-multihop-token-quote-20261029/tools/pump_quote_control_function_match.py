#!/usr/bin/env python3
"""Compare candidate quote-control function bodies with the captured Pump executable.

For every candidate function whose symbol mentions quote_control (plus explicitly
requested symbols), search the captured .text for windows with the same length and
the same instructions after masking only:
  * lddw immediates (loader-relocated addresses), and
  * immediates of internal relative calls (src register 1 / pc-relative call).
Every other byte (opcodes, registers, offsets, branch displacements, constants) must
be identical. Raw-byte equality is reported separately. This is analysis only; no
executable is written or patched.
"""
import argparse, hashlib, json, pathlib, re, struct, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'


def sections(blob):
    shoff, = struct.unpack_from('<Q', blob, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    hdrs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    strtab = hdrs[shstrndx]
    name = lambda off: blob[strtab[4] + off:blob.index(b'\0', strtab[4] + off)].decode()
    return {name(h[0]): {'addr': h[3], 'offset': h[4], 'size': h[5]} for h in hdrs}


def mask(code):
    out = bytearray(code)
    i = 0
    while i + 8 <= len(out):
        op = out[i]
        if op == 0x18:  # lddw spans two slots
            out[i + 4:i + 8] = b'\0' * 4
            out[i + 12:i + 16] = b'\0' * 4
            i += 16
            continue
        if op == 0x85 and (out[i + 1] >> 4) in (0, 1) and struct.unpack_from('<i', out, i + 4)[0] != -1:
            out[i + 4:i + 8] = b'\0' * 4  # internal relative call target
        i += 8
    return bytes(out)


def candidate_functions(path, objdump, pattern):
    text = subprocess.check_output([objdump, '-t', str(path)], text=True)
    funcs = []
    for line in text.splitlines():
        m = re.match(r'^([0-9a-f]+) .* F \.text\s+([0-9a-f]+)\s+(?:\.hidden\s+)?(\S+)$', line)
        if m:
            addr, size, name = int(m.group(1), 16), int(m.group(2), 16), m.group(3)
            if size and re.search(pattern, name):
                funcs.append((addr, size, name))
    return funcs


def main():
    p = argparse.ArgumentParser()
    p.add_argument('candidate', type=pathlib.Path, help='unstripped candidate .so')
    p.add_argument('--objdump', default=str(pathlib.Path.home() / '.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objdump'))
    p.add_argument('--pattern', default='quote_control|QuoteControl')
    p.add_argument('--output', type=pathlib.Path)
    a = p.parse_args()
    orig = ORIGINAL.read_bytes()
    cand = a.candidate.read_bytes()
    os_, cs = sections(orig)['.text'], sections(cand)['.text']
    otext = orig[os_['offset']:os_['offset'] + os_['size']]
    omask = mask(otext)
    rows = []
    for addr, size, name in candidate_functions(a.candidate, a.objdump, a.pattern):
        off = addr - cs['addr'] + cs['offset']
        body = cand[off:off + size]
        mb = mask(body)
        hits = [m.start() for m in re.finditer(re.escape(mb), omask) if m.start() % 8 == 0]
        raw = [h for h in hits if otext[h:h + size] == body]
        rows.append({'symbol': name, 'size': size, 'masked_matches': [os_['addr'] + h for h in hits],
                     'raw_matches': [os_['addr'] + h for h in raw], 'sha256': hashlib.sha256(body).hexdigest()})
        short = re.sub(r'17h[0-9a-f]{16}E$', '', name)[-90:]
        print(f"{size:6d} masked={len(hits)} raw={len(raw)} {short}")
    print(f"{sum(1 for r in rows if r['masked_matches'])}/{len(rows)} functions have masked matches")
    if a.output:
        a.output.write_text(json.dumps({'candidate': str(a.candidate), 'candidate_sha256': hashlib.sha256(cand).hexdigest(),
                                        'original_sha256': hashlib.sha256(orig).hexdigest(), 'functions': rows}, indent=1))


if __name__ == '__main__':
    main()
