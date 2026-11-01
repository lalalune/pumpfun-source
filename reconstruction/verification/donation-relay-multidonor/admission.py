"""Raw-source loading and immutable finite Relay fixture input admission."""
from __future__ import annotations
import builtins
import hashlib
import json
import math
import os
import stat
import sys
import types
import uuid
from pathlib import Path
from importlib.metadata import version

if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
if version("solders") != "0.27.1":
    raise SystemExit("solders==0.27.1 is required for this finite fixture")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOADED = {str(Path(__file__).resolve()): globals().get("__source_sha256__", hashlib.sha256(Path(__file__).read_bytes()).hexdigest())}


def regular_bytes(path, *, root=None):
    path = Path(os.path.abspath(path))
    boundary = Path(root).absolute() if root is not None else path.parent
    path.relative_to(boundary)
    probe = path
    while True:
        if probe.is_symlink():
            raise ValueError("symlink input: " + str(probe))
        if probe == boundary:
            break
        probe = probe.parent
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("nonregular input: " + str(path))
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as handle:
        opened = os.fstat(handle.fileno())
        raw = handle.read()
        after = os.fstat(handle.fileno())
    final = path.lstat()
    sig = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if any(sig(s) != sig(before) for s in (opened, after, final)):
        raise ValueError("input changed while reading: " + str(path))
    return raw


def source_module(name, path, *, imports=None, bindings=None):
    path = Path(os.path.abspath(path))
    raw = regular_bytes(path, root=ROOT)
    digest = hashlib.sha256(raw).hexdigest()
    if str(path) in LOADED and LOADED[str(path)] != digest:
        raise ValueError("source changed between graph loads")
    LOADED[str(path)] = digest
    private = "_relay_multidonor_" + name + "_" + uuid.uuid4().hex
    module = types.ModuleType(private)
    module.__file__ = str(path)
    module.__source_sha256__ = digest
    module.__source_path__ = str(path)
    module.__dict__.update(bindings or {})
    selected = dict(imports or {})
    def importing(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name in selected:
            return selected[name]
        return builtins.__import__(name, globals, locals, fromlist, level)
    module.__dict__["__builtins__"] = dict(vars(builtins), __import__=importing)
    sys.modules[private] = module
    try:
        exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    finally:
        sys.modules.pop(private, None)
    return module


def same_json(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_json(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return left == right


def json_bytes(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def floating(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("nonfinite JSON number")
        return result
    def constant(value):
        raise ValueError("nonfinite JSON constant")
    return json.loads(raw, object_pairs_hook=pairs, parse_float=floating, parse_constant=constant)


def snapshot_inputs():
    paths = [ROOT / "Cargo.toml", ROOT / "Cargo.lock", ROOT / "scripts/pump_differential_output.py"]
    for path in (ROOT / "programs/donation-relay").rglob("*"):
        if path.is_symlink():
            raise ValueError("source symlink")
        if not path.is_dir():
            paths.append(path)
    paths += [p for p in HERE.iterdir() if p.suffix in {".py", ".json", ".md"}]
    for name in ("donation_relay", "spl_token", "associated_token"):
        paths += [ROOT / "evidence/dependencies" / name / f for f in ("deployed.so", "capture.json")]
    rows = {p.relative_to(ROOT).as_posix(): hashlib.sha256(regular_bytes(p, root=ROOT)).hexdigest()
            for p in sorted(set(paths))}
    for path, digest in LOADED.items():
        if rows.get(Path(path).relative_to(ROOT).as_posix()) != digest:
            raise ValueError("executed source differs from current admitted bytes: " + path)
    return rows


def recheck_inputs(expected):
    if not same_json(snapshot_inputs(), expected):
        raise ValueError("input inventory or bytes changed during operation")


def outside_repository(path):
    if Path(path).resolve().is_relative_to(ROOT):
        raise ValueError("output must remain outside repository")
