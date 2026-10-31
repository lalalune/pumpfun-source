#!/usr/bin/env python3
"""Compare candidate quote-control function bodies with the captured Pump executable.

For every candidate function whose symbol mentions quote_control (plus explicitly
requested symbols), search the captured .text for windows with the same length and
the same instructions after masking only:
  * both lddw immediate words (this heuristic also masks literal constants), and
  * non-sentinel call immediates with src register 0 or 1, following the
    unrelocated legacy-SBPF relative-call convention.
This is a legacy, pre-loader heuristic, not a version-aware decoder for modern
static syscalls or post-relocation call IDs. Every other byte (opcodes, registers,
offsets and branch displacements) must be identical. Raw equality is separate;
masked matches do not prove callee or data identity. This is analysis only; no
executable is written or patched.
"""
import argparse, hashlib, json, pathlib, re, shutil, struct, subprocess, sys, tempfile
from functools import lru_cache

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
from instruction_stream import instruction_boundaries


SHT_NOBITS = 8


@lru_cache(maxsize=2)
def _text_boundaries(image, offset, size):
    # Decode once per immutable image, not once per function in a full census.
    return instruction_boundaries(memoryview(image)[offset:offset + size])


_code_boundaries = lru_cache(maxsize=4)(instruction_boundaries)


def resolve_objdump(objdump):
    """Use the executable selected by PATH for both invocation and provenance."""
    return shutil.which(str(objdump)) or str(objdump)


def protect_report_output(output, inputs, objdump):
    """Reject report paths that alias consumed inputs before analysis or writing."""
    if output is None:
        return
    destination = pathlib.Path(output)
    tool = resolve_objdump(objdump)
    for value in [*inputs, pathlib.Path(__file__), pathlib.Path(tool),
                  pathlib.Path(instruction_boundaries.__code__.co_filename)]:
        source = pathlib.Path(value)
        if (destination.resolve() == source.resolve()
                or (destination.exists() and source.exists() and destination.samefile(source))):
            raise ValueError('report destination aliases an input: ' + str(source))


def sections(blob):
    if len(blob) < 64 or blob[:4] != b'\x7fELF' or blob[4] != 2 or blob[5] != 1:
        raise ValueError('expected a little-endian 64-bit ELF image')
    shoff, = struct.unpack_from('<Q', blob, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    if shnum == 0:
        return {}
    if shentsize < 64 or shoff < 0 or shoff + shnum * shentsize > len(blob):
        raise ValueError('truncated or invalid ELF section header table')
    if shstrndx >= shnum:
        raise ValueError('invalid ELF section header string table index')
    hdrs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    strtab = hdrs[shstrndx]
    if strtab[1] == SHT_NOBITS or strtab[4] < 0 or strtab[5] < 0 or strtab[4] + strtab[5] > len(blob):
        raise ValueError('invalid ELF section header string table payload')
    strtab_bytes = blob[strtab[4]:strtab[4] + strtab[5]]

    def name(off):
        if off < 0 or off >= len(strtab_bytes):
            raise ValueError('section name offset outside .shstrtab')
        end = strtab_bytes.find(b'\0', off)
        if end == -1:
            raise ValueError('unterminated section name in .shstrtab')
        return strtab_bytes[off:end].decode('utf-8')

    return {name(h[0]): {'type': h[1], 'addr': h[3], 'offset': h[4], 'size': h[5]} for h in hdrs}


def function_body(image, image_sections, address, size):
    """Read complete logical instructions from a physically present .text range."""
    text = image_sections['.text']
    if text.get('type') == SHT_NOBITS:
        raise ValueError('.text section is SHT_NOBITS without a file payload')
    relative = address - text['addr']
    if size <= 0 or size % 8 or relative % 8 or not 0 <= relative <= text['size'] - size:
        raise ValueError('function range must contain complete aligned slots within .text')
    if text['offset'] < 0 or text['size'] < 0 or text['offset'] + text['size'] > len(image):
        raise ValueError('truncated .text file payload')
    boundaries = _text_boundaries(bytes(image), text['offset'], text['size'])
    if relative not in boundaries or relative + size not in boundaries:
        raise ValueError('function range does not follow a logical instruction boundary')
    offset = text['offset'] + relative
    return image[offset:offset + size]


def mask(code):
    if len(code) % 8:
        raise ValueError("SBF code must contain complete 8-byte instruction slots")
    out = bytearray(code)
    i = 0
    while i + 8 <= len(out):
        op = out[i]
        if op == 0x18:  # lddw spans two slots
            if i + 16 > len(out):
                raise ValueError("truncated lddw instruction")
            out[i + 4:i + 8] = b'\0' * 4
            out[i + 12:i + 16] = b'\0' * 4
            i += 16
            continue
        if op == 0x85 and (out[i + 1] >> 4) in (0, 1) and struct.unpack_from('<i', out, i + 4)[0] != -1:
            out[i + 4:i + 8] = b'\0' * 4  # internal relative call target
        i += 8
    return bytes(out)


def _aligned_matches(needle, haystack):
    """Return every instruction-aligned occurrence, including overlapping ones."""
    if not needle:
        raise ValueError("candidate function body must not be empty")
    boundaries = _code_boundaries(bytes(haystack))
    hits = []
    start = haystack.find(needle)
    while start != -1:
        if start in boundaries and start + len(needle) in boundaries:
            hits.append(start)
        start = haystack.find(needle, start + 1)
    return hits


def candidate_functions(path, objdump, pattern, *, image=None):
    # Read symbols from the exact bytes the caller hashes and compares.
    if image is None:
        image = pathlib.Path(path).read_bytes()
    with tempfile.TemporaryDirectory(prefix='pump-symbols-') as directory:
        snapshot = pathlib.Path(directory) / 'candidate.so'
        snapshot.write_bytes(image)
        text = subprocess.check_output([objdump, '-t', str(snapshot)], text=True)
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
    protect_report_output(a.output, [ORIGINAL, a.candidate], a.objdump)
    orig = ORIGINAL.read_bytes()
    cand = a.candidate.read_bytes()
    os_, cs = sections(orig)['.text'], sections(cand)['.text']
    otext = function_body(orig, {'.text': os_}, os_['addr'], os_['size'])
    omask = mask(otext)
    rows = []
    for addr, size, name in candidate_functions(a.candidate, a.objdump, a.pattern, image=cand):
        body = function_body(cand, {'.text': cs}, addr, size)
        mb = mask(body)
        hits = _aligned_matches(mb, omask)
        raw = [h for h in hits if otext[h:h + size] == body]
        rows.append({'symbol': name, 'size': size, 'masked_matches': [os_['addr'] + h for h in hits],
                     'raw_matches': [os_['addr'] + h for h in raw], 'sha256': hashlib.sha256(body).hexdigest()})
        short = re.sub(r'17h[0-9a-f]{16}E$', '', name)[-90:]
        print(f"{size:6d} masked={len(hits)} raw={len(raw)} {short}")
    print(f"{sum(1 for r in rows if r['masked_matches'])}/{len(rows)} functions have masked matches")
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps({'candidate': str(a.candidate), 'candidate_sha256': hashlib.sha256(cand).hexdigest(),
                                        'original_sha256': hashlib.sha256(orig).hexdigest(), 'functions': rows}, indent=1),encoding='utf-8',newline='\n')


if __name__ == '__main__':
    main()
