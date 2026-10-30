#!/usr/bin/env python3
"""Time complete analysis CLIs and require byte-identical eight-file packets.

Example: python scripts/benchmark_program_analysis.py --before ../main --after .
Run both checkouts with the same Python and captured original. Timings are local
observations, not a CI threshold or a bytecode reconstruction score.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time


def benchmark(root, program, repeats):
    timings = []
    expected = None
    with tempfile.TemporaryDirectory(prefix="program-analysis-benchmark-") as temporary:
        for index in range(repeats):
            output = Path(temporary) / str(index)
            start = time.perf_counter()
            subprocess.run([
                sys.executable, "-I", "-B", "-X", "utf8",
                str(root / "scripts/analyze_program.py"),
                "--program", program, "--output", str(output),
            ], check=True, stdout=subprocess.DEVNULL)
            timings.append(time.perf_counter() - start)
            hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in sorted(output.iterdir())}
            if expected is not None and hashes != expected:
                raise ValueError("analysis packets differ between repeated runs")
            expected = hashes
            subprocess.run([sys.executable, "-I", "-B", str(output / "verify.py")],
                           check=True, stdout=subprocess.DEVNULL)
    return {"seconds": timings, "median_seconds": statistics.median(timings),
            "packet_sha256": expected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--program", default="pump")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    roots = [args.before.resolve(), args.after.resolve()]
    inputs = [hashlib.sha256((root / "evidence/original" / args.program / "deployed.so")
                            .read_bytes()).hexdigest() for root in roots]
    if inputs[0] != inputs[1]:
        raise ValueError("benchmark checkouts use different captured originals")
    before, after = [benchmark(root, args.program, args.repeats) for root in roots]
    if before["packet_sha256"] != after["packet_sha256"]:
        raise ValueError("before and after analysis packets are not byte-identical")
    print(json.dumps({"python": sys.version, "program": args.program,
                      "input_sha256": inputs[0], "before": before, "after": after,
                      "speedup": before["median_seconds"] / after["median_seconds"]},
                     indent=2))


if __name__ == "__main__":
    main()
