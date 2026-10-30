#!/usr/bin/env python3
"""Measure real concurrent host builds with shared versus private outputs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time

HOST = "programs/pump/recovered/global_admin_host.rs"
MODULE = "programs/pump/recovered/global_admin.rs"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inputs(roots):
    return [{name: sha((root / name).read_bytes()) for name in (HOST, MODULE)}
            for root in roots]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root_a", type=Path)
    parser.add_argument("root_b", type=Path)
    parser.add_argument("--rustc", default="rustc")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.trials <= 10:
        parser.error("--trials must be between 1 and 10")
    roots = [args.root_a.resolve(), args.root_b.resolve()]
    if roots[0] == roots[1]:
        parser.error("two distinct resolved checkout roots are required")
    before = inputs(roots)
    if before[0] != before[1]:
        parser.error("the host and its module must have identical source bytes")
    expected = json.loads(Path(__file__).with_name("evidence.json").read_text())["sourceSha256"]
    if before[0] != expected:
        parser.error("host/module source bytes differ from the recorded evidence")
    compiler = shutil.which(args.rustc)
    if compiler is None:
        parser.error("rustc is not executable")
    version = subprocess.check_output([compiler, "--version"], text=True, timeout=30).strip()
    output = args.output_dir.resolve()
    output.mkdir(parents=False, exist_ok=False)
    started = time.monotonic()
    records = []

    def diagnostic(stderr):
        for root, label in zip(roots, ("<root-a>", "<root-b>")):
            stderr = stderr.replace(str(root), label)
        stderr = stderr.replace(str(output), "<output>")
        stderr = re.sub(r"/var/folders/[^'\"\s]+", "<system-temp>", stderr)
        return "\n".join(stderr.splitlines()[:32])

    with tempfile.TemporaryDirectory(prefix="build-", dir=output) as build:
        build = Path(build)
        for mode in ("shared", "private"):
            for trial in range(args.trials):
                folder = build / f"{mode}-{trial}"
                folder.mkdir()
                barrier = threading.Barrier(2)

                def worker(index):
                    parent = folder if mode == "shared" else folder / str(index)
                    parent.mkdir(exist_ok=True)
                    host = parent / "host"
                    command = [compiler, "--edition=2021", "-O",
                               str(roots[index] / HOST), "-o", str(host)]
                    barrier.wait(timeout=30)
                    begin = time.monotonic() - started
                    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
                    row = {"worker": index, "compile_exit": result.returncode,
                           "started_seconds": round(begin, 6),
                           "finished_seconds": round(time.monotonic() - started, 6),
                           "normalized_diagnostic_excerpt": diagnostic(result.stderr)}
                    if mode == "private" and result.returncode == 0:
                        run = subprocess.run([str(host)], input="", text=True,
                                             capture_output=True, timeout=30)
                        row.update(native_exit=run.returncode,
                                   binary_sha256=sha(host.read_bytes()))
                    return row

                with ThreadPoolExecutor(max_workers=2) as pool:
                    workers = list(pool.map(worker, (0, 1)))
                row = {"mode": mode, "trial": trial, "workers": workers}
                if mode == "shared":
                    row["output_exists"] = (folder / "host").exists()
                records.append(row)
    unchanged = inputs(roots) == before
    private_pass = all(worker["compile_exit"] == 0 and worker.get("native_exit") == 0
                       for row in records if row["mode"] == "private"
                       for worker in row["workers"])
    report = {"schemaVersion": 1, "compiler": version, "source_sha256": before[0],
              "compile_arguments": ["--edition=2021", "-O", "<root>/" + HOST,
                                    "-o", "<shared-or-private-output>/host"],
              "source_unchanged": unchanged, "trials_per_mode": args.trials,
              "private_control_passed": private_pass, "results": records}
    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"results": str(output / "results.json"),
                      "private_control_passed": private_pass,
                      "shared_compile_failures": sum(w["compile_exit"] != 0
                          for row in records if row["mode"] == "shared"
                          for w in row["workers"])}))
    return 0 if unchanged and private_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
