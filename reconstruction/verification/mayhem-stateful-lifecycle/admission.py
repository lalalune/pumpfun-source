"""Source-only imports and immutable input closure for the Mayhem fixture."""
from pathlib import Path
from types import ModuleType
import hashlib
import sys

if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def source_module(name, path):
    raw = path.read_bytes()
    module = ModuleType(name)
    module.__file__ = str(path)
    module._ADMITTED_SOURCE_BYTES = raw
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def same_json(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_json(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return left == right


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bound_inputs():
    paths = [
        ROOT / "scripts/pump_trade_fixture.py",
        ROOT / "research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json",
        ROOT / "reconstruction/mayhem/native-linux-qualification/QUALIFICATION.json",
        ROOT / "evidence/original/mayhem/deployed.so",
        ROOT / "evidence/original/mayhem/capture.json",
    ]
    for group, names in (("original", ("pump", "pump_fees")),
                         ("dependencies", ("spl_token", "spl_token_2022", "associated_token"))):
        paths.extend(ROOT / f"evidence/{group}/{name}/{filename}"
                     for name in names for filename in ("capture.json", "deployed.so"))
    paths.extend(path for path in sorted((ROOT / "programs/mayhem").rglob("*")) if path.is_file())
    paths.extend(path for path in sorted(HERE.iterdir())
                 if path.is_file() and path.suffix in {".py", ".json", ".md"})
    if any(path.is_symlink() or not path.resolve().is_relative_to(ROOT) for path in paths):
        raise ValueError("input must be a regular repository file")
    return sorted(set(paths))


def snapshot_inputs():
    return {path.relative_to(ROOT).as_posix(): file_sha(path) for path in bound_inputs()}


def recheck_inputs(expected):
    if not same_json(snapshot_inputs(), expected):
        raise ValueError("input inventory or bytes changed after import")


def outside_repository(path):
    if path.resolve().is_relative_to(ROOT):
        raise ValueError("output must be outside the repository")
