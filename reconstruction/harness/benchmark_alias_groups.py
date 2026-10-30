"""Synthetic normalized-body grouping benchmark; no ELF or executable is run."""
import hashlib
import json
import statistics
import time
from types import SimpleNamespace
from pair_candidates import body_groups


def main():
    raw = b'\xb7\x00\x00\x00\x01\x00\x00\x00' * 2048
    symbols = [(0, len(raw), 'alias_' + str(i)) for i in range(500)]
    candidate = SimpleNamespace(funcs=symbols, fn=lambda start, size: raw,
                                secs={'.text': {'addr': 0, 'offset': 0, 'size': len(raw)}})
    expected = {(0, len(raw)): [{'start': start, 'bytes': size, 'symbol': name}
                              for start, size, name in symbols]}
    samples = []
    for _ in range(5):
        started = time.perf_counter()
        result = body_groups(candidate)
        samples.append(time.perf_counter() - started)
        if result != expected:
            raise RuntimeError('alias grouping changed')
    print(json.dumps({'aliases': len(symbols), 'bodyBytes': len(raw),
                      'medianSeconds': statistics.median(samples),
                      'resultSha256': hashlib.sha256(json.dumps(list(result.values()), sort_keys=True).encode()).hexdigest()}))


if __name__ == '__main__': main()
