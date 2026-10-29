#!/usr/bin/env python3
"""Authenticate this finite receipt and its source inputs; does not rerun tests."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def checked_path(root, name):
    p = root / name
    if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
        raise ValueError("Unsafe or absent input: " + name)
    return p

def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], env={**os.environ, "GIT_NO_LAZY_FETCH": "1"}).decode().strip()

manifest = json.loads((HERE / "MANIFEST.json").read_text())
actual = {str(p.relative_to(HERE)) for p in HERE.rglob("*") if p.is_file() and p.name != "MANIFEST.json"}
if actual != set(manifest):
    raise ValueError("Receipt file membership changed")
for name, row in manifest.items():
    data = checked_path(HERE, name).read_bytes()
    if len(data) != row["bytes"] or sha(data) != row["sha256"]:
        raise ValueError("Receipt bytes changed: " + name)
record = json.loads((HERE / "record.json").read_text())
if git("rev-parse", record["sourceCommit"] + "^{tree}") != record["sourceTree"]:
    raise ValueError("Qualified source tree changed")
for name, row in record["inputs"].items():
    data = checked_path(ROOT, name).read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if len(data) != row["bytes"] or sha(data) != row["sha256"] or blob != row["gitBlob"]:
        raise ValueError("Qualified input changed: " + name)
    if git("rev-parse", record["sourceCommit"] + ":" + name) != blob:
        raise ValueError("Input not bound to qualified Git source: " + name)
for name, row in record["artifacts"].items():
    data = checked_path(HERE, name).read_bytes()
    if len(data) != row["bytes"] or sha(data) != row["sha256"]:
        raise ValueError("Executed artifact changed: " + name)
print(f'Verified {len(record["inputs"])} qualified Git inputs and {len(manifest)} receipt files; recorded finite outcomes are not a new test execution')
