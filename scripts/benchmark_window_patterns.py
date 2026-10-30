"""Read-only relocation-pattern query benchmark; never executes program bytes."""
import hashlib
import json
from pathlib import Path
import statistics
import time
from window_elf_reader import Elf


def main():
    path = Path(__file__).resolve().parents[1] / 'evidence/original/pump/deployed.so'
    elf = Elf(path)
    windows = list(zip(elf.entries, elf.entries[1:] + [elf.hi]))[:100]
    def query():
        return [elf.pattern(start, end-start) for start, end in windows]
    result = query()
    expected = [[{'offset': at-start, **row} for at, row in sorted(elf.relocations.items())
                 if start <= at < end] for start, end in windows]
    if result != expected:
        raise RuntimeError('relocation patterns differ from the reference query')
    samples = []
    for _ in range(5):
        started = time.perf_counter()
        if query() != result:
            raise RuntimeError('relocation patterns changed between repetitions')
        samples.append(time.perf_counter() - started)
    print(json.dumps({'queries': len(windows), 'relocations': len(elf.relocations),
                      'medianSeconds': statistics.median(samples),
                      'inputSha256': hashlib.sha256(elf.b).hexdigest(),
                      'resultSha256': hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()}))


if __name__ == '__main__': main()
