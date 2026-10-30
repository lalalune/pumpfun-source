"""Score a synthetic ELF with aliased symbols; never execute its instructions."""
import hashlib
import json
from pathlib import Path
import statistics
import struct
import tempfile
import time
from unittest.mock import patch
import score


def image(count=500):
    raw = b'\xb7\x00\x00\x00\x01\x00\x00\x00' * 2048
    names = b'\0.shstrtab\0.text\0.strtab\0.symtab\0'
    strings, offsets = bytearray(b'\0'), []
    for index in range(count):
        offsets.append(len(strings))
        strings.extend(('alias_' + str(index)).encode() + b'\0')
    text_at = 512
    strings_at = text_at + len(raw)
    symbols_at = (strings_at + len(strings) + 7) // 8 * 8
    blob = bytearray(symbols_at + (count + 1) * 24)
    blob[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHI', blob, 16, 3, 263, 1)
    struct.pack_into('<Q', blob, 40, 64)
    struct.pack_into('<H', blob, 52, 64)
    struct.pack_into('<HHH', blob, 58, 64, 5, 1)
    headers = [(0,0,0,0,0,0,0,0,0,0), (1,3,0,0,384,len(names),0,0,1,0),
               (11,1,6,0x1000,text_at,len(raw),0,0,8,0),
               (17,3,0,0,strings_at,len(strings),0,0,1,0),
               (25,2,0,0,symbols_at,(count+1)*24,3,0,8,24)]
    for i, values in enumerate(headers): struct.pack_into('<IIQQQQIIQQ', blob, 64+i*64, *values)
    blob[384:384+len(names)] = names
    blob[text_at:text_at+len(raw)] = raw
    blob[strings_at:strings_at+len(strings)] = strings
    for i, offset in enumerate(offsets, 1):
        struct.pack_into('<IBBHQQ', blob, symbols_at+i*24, offset, 18, 0, 2, 0x1000, len(raw))
    return bytes(blob), raw


def main():
    blob, raw = image()
    expected = {4096: {'normalized': True, 'raw': True, 'symbols': ['alias_'+str(i) for i in range(500)], 'bytes': len(raw)}}
    windows = [{'start':4096, 'bytes':len(raw), 'raw':raw, 'norm':raw}]
    samples = []
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'candidate.so'
        path.write_bytes(blob)
        for _ in range(5):
            with patch.object(score, 'original_windows', return_value=windows):
                started = time.perf_counter()
                result, candidate_hash = score.score_with_hash(path)
                samples.append(time.perf_counter()-started)
            if result != expected or candidate_hash != hashlib.sha256(blob).hexdigest():
                raise RuntimeError('synthetic score changed')
    print(json.dumps({'aliases':500, 'bodyBytes':len(raw), 'medianSeconds':statistics.median(samples),
                      'inputSha256':candidate_hash,
                      'resultSha256':hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()}))


if __name__ == '__main__': main()
