#!/usr/bin/env python3
"""Immutable input snapshots and crash-visible campaign publication."""
from __future__ import annotations

import builtins
import fcntl
import gzip
import hashlib
import json
import math
import os
import re
import stat
import sys
import tempfile
import types
import uuid
from pathlib import Path

SCHEMA = "pump-admin-cto-campaign-attempt-v1"
ROOT = Path(__file__).absolute().parents[3]
OPERATIONAL = {"attempt.json", "summary.json", "complete.json", "artifacts.json"}


def regular_bytes(path: Path, *, root: Path | None = None) -> bytes:
    """Read stable regular bytes, without traversing report/source symlinks."""
    path = Path(os.path.abspath(path))
    boundary = Path(os.path.abspath(root)) if root is not None else path.parent
    path.relative_to(boundary)
    current = path
    while True:
        if current.is_symlink():
            raise ValueError(f"symlink input: {current}")
        if current == boundary:
            break
        current = current.parent
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"nonregular input: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as handle:
        opened = os.fstat(handle.fileno())
        raw = handle.read()
        after = os.fstat(handle.fileno())
    final = os.lstat(path)
    key = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if not stat.S_ISREG(final.st_mode) or any(key(s) != key(before) for s in (opened, after, final)):
        raise ValueError(f"input changed during read: {path}")
    return raw


def source_module(name: str, path: Path, *, imports=None):
    """Use the existing raw-source pattern in a private, temporary namespace."""
    path = Path(os.path.abspath(path))
    if path.suffix != ".py":
        raise ValueError("source module must be a Python source file")
    raw = regular_bytes(path, root=ROOT)
    private = "_pump_fuzz_" + name.replace(".", "_") + "_" + uuid.uuid4().hex
    module = types.ModuleType(private)
    module.__file__ = str(path)
    module.__source_path__ = str(path)
    module.__source_sha256__ = hashlib.sha256(raw).hexdigest()
    module.__cached__ = None
    selected = dict(imports or {})
    def importing(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name in selected:
            return selected[name]
        return builtins.__import__(name, globals, locals, fromlist, level)
    module.__dict__["__builtins__"] = dict(vars(builtins), __import__=importing)
    sys.modules[private] = module
    try:
        exec(compile(raw, str(path), "exec", dont_inherit=True, optimize=0), module.__dict__)
    finally:
        sys.modules.pop(private, None)
    return module


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def read_json(path: Path):
    def constant(value):
        raise ValueError("nonfinite JSON constant: " + value)
    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("nonfinite JSON number")
        return result
    return json.loads(regular_bytes(path), object_pairs_hook=_pairs,
                      parse_constant=constant, parse_float=number)


def report_files_digest(root: Path) -> dict:
    root = Path(os.path.abspath(root))
    if root.is_symlink() or not root.is_dir():
        raise ValueError("report must be a regular directory")
    files, directories = {}, []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ValueError(f"symlink report member: {relative}")
        if path.is_dir():
            directories.append(relative)
        else:
            raw = regular_bytes(path, root=root)
            files[relative] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    return {"files": files, "directories": directories}


def verify_artifacts(root: Path, expected_sha256: str) -> dict:
    root = Path(os.path.abspath(root))
    raw = regular_bytes(root / "artifacts.json", root=root)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("artifact manifest hash differs")
    manifest = json.loads(raw, object_pairs_hook=_pairs)
    if not isinstance(manifest, dict) or set(manifest) != {"schema", "files"} or manifest["schema"] != "pump-admin-cto-fuzz-artifacts-v1":
        raise ValueError("artifact manifest schema differs")
    files = manifest["files"]
    if not isinstance(files, dict) or "cases.json" not in files or set(files) & OPERATIONAL:
        raise ValueError("artifact manifest membership differs")
    for name, entry in files.items():
        path = Path(name)
        if not isinstance(name, str) or path.is_absolute() or ".." in path.parts or path.as_posix() != name or not path.parts:
            raise ValueError("noncanonical artifact path")
        if not isinstance(entry, dict) or set(entry) != {"bytes", "sha256"} or type(entry["bytes"]) is not int or entry["bytes"] < 0 or not isinstance(entry["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise ValueError("artifact manifest entry differs")
    inventory = report_files_digest(root)
    if set(inventory["files"]) != set(files) | OPERATIONAL:
        raise ValueError("report contains missing or unlisted files")
    parents = {parent.as_posix() for name in files for parent in Path(name).parents if parent != Path(".")}
    if set(inventory["directories"]) != parents:
        raise ValueError("report contains missing or unlisted directories")
    if any(inventory["files"][name] != entry for name, entry in files.items()):
        raise ValueError("artifact bytes differ")
    return manifest


def artifact_manifest(root: Path) -> dict:
    inventory = report_files_digest(root)
    return {"schema": "pump-admin-cto-fuzz-artifacts-v1",
            "files": {name: row for name, row in inventory["files"].items()
                      if name not in OPERATIONAL}}


def file_sha(path: Path) -> str:
    return hashlib.sha256(regular_bytes(path)).hexdigest()


def canonical_json(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def compressed_json(value) -> bytes:
    return gzip.compress(canonical_json(value), mtime=0)


class InputSnapshot:
    """Copy declared inputs once, then detect mutation of their source paths."""

    def __init__(self, paths: dict[str, Path], expected: dict[str, str] | None = None):
        self.sources = {name: Path(path).resolve() for name, path in paths.items()}
        self.expected = expected or {}
        self.temp = None
        self.paths = {}
        self.hashes = {}

    def __enter__(self):
        unknown = sorted(set(self.expected) - set(self.sources))
        if unknown:
            raise ValueError(f"expected hashes name unknown inputs: {unknown}")
        self.temp = tempfile.TemporaryDirectory(prefix="pump-admin-cto-fuzz-inputs-")
        root = Path(self.temp.name)
        try:
            for index, (name, source) in enumerate(sorted(self.sources.items())):
                raw = regular_bytes(source)
                digest = hashlib.sha256(raw).hexdigest()
                if name in self.expected and self.expected[name] != digest:
                    raise ValueError(f"input hash mismatch for {name}: expected {self.expected[name]}, got {digest}")
                target = root / f"{index:02d}-{name}.bin"
                target.write_bytes(raw)
                self.paths[name] = target
                self.hashes[name] = digest
        except Exception:
            self.temp.cleanup()
            self.temp = None
            raise
        return self

    def changed_sources(self) -> dict[str, dict[str, str]]:
        changed = {}
        for name, path in self.sources.items():
            actual = file_sha(path)
            if actual != self.hashes[name]:
                changed[name] = {"before": self.hashes[name], "after": actual}
        return changed

    def __exit__(self, exc_type, exc, traceback):
        if self.temp is not None:
            self.temp.cleanup()


class CampaignPublisher:
    """Publish one immutable directory or retain a visible interrupted attempt."""

    def __init__(self, output: Path, attempt: dict):
        self.output = Path(output).resolve()
        self.attempt = dict(attempt)
        self.lock_handle = None
        self.stage = None
        self.committed = False

    def __enter__(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.output.parent / (self.output.name + ".lock")
        self.lock_handle = lock_path.open("a+b")
        try:
            fcntl.flock(self.lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.lock_handle.close()
            raise FileExistsError(f"campaign destination is locked: {self.output}") from error
        if self.output.exists() or self.output.is_symlink():
            self._unlock()
            raise FileExistsError(f"refusing to overwrite campaign: {self.output}")
        suffix = f".partial-{os.getpid()}-{uuid.uuid4().hex}"
        self.stage = self.output.parent / ("." + self.output.name + suffix)
        self.stage.mkdir(mode=0o700)
        self.attempt.update(schema=SCHEMA, status="in_progress", output_name=self.output.name)
        self.write_json("attempt.json", self.attempt)
        return self

    def _target(self, relative: str) -> Path:
        value = Path(relative)
        if value.is_absolute() or ".." in value.parts or not value.parts:
            raise ValueError("publication path must remain inside the campaign")
        target = self.stage / value
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def write_bytes(self, relative: str, raw: bytes) -> None:
        target = self._target(relative)
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"refusing to overwrite staged artifact: {relative}")
        with target.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())

    def write_json(self, relative: str, value, *, compressed=False) -> None:
        self.write_bytes(relative, compressed_json(value) if compressed else canonical_json(value))

    def write_manifest(self) -> str:
        self.write_json("artifacts.json", artifact_manifest(self.stage))
        return file_sha(self.stage / "artifacts.json")

    def commit(self, final_attempt: dict) -> Path:
        if self.committed:
            raise RuntimeError("campaign already committed")
        complete = dict(self.attempt)
        complete.update(final_attempt, status="complete")
        self.write_json("complete.json", complete)
        directory = os.open(self.stage, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        os.rename(self.stage, self.output)
        parent = os.open(self.output.parent, os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
        self.committed = True
        return self.output

    def _unlock(self):
        if self.lock_handle is not None and not self.lock_handle.closed:
            fcntl.flock(self.lock_handle.fileno(), fcntl.LOCK_UN)
            self.lock_handle.close()

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None and self.stage is not None and self.stage.exists() and not self.committed:
            try:
                self.write_json("interrupted.json", {"schema": SCHEMA, "status": "interrupted",
                                                       "error_type": exc_type.__name__})
            except (OSError, ValueError):
                pass
        self._unlock()


def find_partial_attempts(output: Path) -> list[Path]:
    output = Path(output).resolve()
    return sorted(output.parent.glob("." + output.name + ".partial-*"))
