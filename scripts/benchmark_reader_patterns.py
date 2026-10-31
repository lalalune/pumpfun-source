"""Benchmark read-only window relocation extraction against retained programs."""
import hashlib
import json
from pathlib import Path
import time
from window_elf_reader import Elf


def main():
    root = Path(__file__).resolve().parents[1]
    queries = []
    relocations = 0
    for name in ('pump', 'pump_amm', 'pump_fees', 'mayhem'):
        elf = Elf(root / 'evidence/original' / name / 'deployed.so')
        relocations += len(elf.relocations)
        ends = elf.entries[1:] + [elf.hi]
        stride = max(1, len(elf.entries) // 64)
        for index in range(0, len(elf.entries), stride):
            queries.append((name, elf, elf.entries[index], ends[index] - elf.entries[index]))
    started = time.perf_counter()
    result = [(name, start, size, elf.pattern(start, size)) for name, elf, start, size in queries]
    elapsed = time.perf_counter() - started
    for (_, elf, start, size), (_, _, _, actual) in zip(queries, result):
        expected = [{'offset': at - start, **row}
                    for at, row in sorted(elf.relocations.items()) if start <= at < start + size]
        assert actual == expected
    # Include out-of-order insertion and boundaries that real ELF tables may not expose.
    reader = Elf.__new__(Elf)
    reader.relocations = {32: {'type': 8}, 16: {'type': 10}, 24: {'type': 8}, 8: {'type': 10}}
    assert reader.pattern(16, 16) == [{'offset': 0, 'type': 10}, {'offset': 8, 'type': 8}]
    assert reader.pattern(16, 0) == []
    print(json.dumps({'queries': len(queries), 'relocations': relocations, 'seconds': elapsed,
                      'result_sha256': hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()}))


if __name__ == '__main__': main()
