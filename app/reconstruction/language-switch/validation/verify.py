"""Check frozen finite receipts; this does not rerun the browser or source oracle."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]


def require(value, reason):
    if not value:
        raise SystemExit(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def safe(root, name):
    parts = Path(name).parts
    require(not Path(name).is_absolute() and parts and ".." not in parts,
            "unsafe validation path")
    current = root
    for part in parts:
        current = current / part
        require(not current.is_symlink(), "symlink validation path")
    require(current.is_file(), "missing regular file: " + name)
    return current


manifest = json.loads((HERE / "MANIFEST.json").read_text())
record = json.loads((HERE / "RECORD.json").read_text())
actual = set()
for path in HERE.rglob("*"):
    require(not path.is_symlink(), "symlink in receipt package")
    if path.is_file() and path.name != "MANIFEST.json":
        actual.add(path.relative_to(HERE).as_posix())
require(actual == set(manifest["files"]), "receipt manifest membership changed")
for name, entry in manifest["files"].items():
    data = safe(HERE, name).read_bytes()
    require(len(data) == entry["bytes"] and sha(data) == entry["sha256"],
            "receipt changed: " + name)

env = {**os.environ, "GIT_NO_LAZY_FETCH": "1"}
tree = subprocess.check_output(
    ["git", "rev-parse", record["testedHead"] + "^{tree}"], cwd=APP, env=env,
).decode().strip()
require(tree == record["testedTree"], "tested tree binding changed")
for name, entry in record["inputs"].items():
    expected = subprocess.check_output(
        ["git", "rev-parse", record["testedHead"] + ":app/" + name],
        cwd=APP, env=env,
    ).decode().strip()
    require(expected == entry["gitBlob"], "Git binding changed: " + name)
    data = safe(APP, name).read_bytes()
    require(len(data) == entry["bytes"] and sha(data) == entry["sha256"]
            and blob(data) == entry["gitBlob"], "executed input changed: " + name)

observations = json.loads((HERE / "browser/observations.json").read_text())
require(observations["bundleSha256"] == record["browserBundleSha256"],
        "browser bundle binding changed")
require([row["width"] for row in observations["results"]] == [390, 1280],
        "browser widths changed")
selected = lambda state: [step for step in state["steps"]
                          if step[0] in ["cookie", "change:start", "change:end", "refresh"]]
cookie = lambda locale: "pump_locale=" + locale + "; path=/; max-age=31536000; samesite=lax"
french = [["cookie", cookie("fr")], ["change:start", "fr"],
          ["change:end", "fr"], ["refresh"]]
rejected = french + [["cookie", cookie("de")], ["change:start", "de"]]
finished = rejected + [["cookie", cookie("de")], ["change:start", "de"],
                       ["change:end", "de"], ["refresh"],
                       ["cookie", cookie("it")], ["change:start", "it"],
                       ["change:end", "it"], ["refresh"]]
for row in observations["results"]:
    require(row["expectedErrors"] == ["synthetic provider rejection"],
            "expected synthetic error or unexpected page errors changed")
    require(row["overflow"] <= 1, "fixture overflow control changed")
    require(row["fetching"] == {"cookieText": "", "language": "en", "steps": []},
            "held GET observation changed")
    pending = row["pendingProvider"]
    require(pending["cookieText"] == cookie("fr") and pending["language"] == "en"
            and selected(pending) == french[:2], "held provider observation changed")
    require(row["success"]["language"] == "fr" and selected(row["success"]) == french,
            "successful selection order changed")
    require(row["rejected"]["language"] == "fr"
            and row["rejected"]["cookieText"] == cookie("de")
            and selected(row["rejected"]) == rejected, "rejection observation changed")
    require(row["afterUnmount"]["language"] == "it"
            and row["afterUnmount"]["cookieText"] == cookie("it")
            and selected(row["afterUnmount"]) == finished,
            "retry or continued-after-unmount observation changed")
requests = [{"method": "GET", "url": url} for url in
            ["/", "/fixture.js", "/api/i18n/fr?ns=__all__",
             "/api/i18n/de?ns=__all__", "/api/i18n/it?ns=__all__"]] * 2
require(observations["requests"] == requests, "owned GET ledger changed")
focused = gzip.decompress((HERE / "logs/focused-final.tap.gz").read_bytes()).decode()
browser = gzip.decompress((HERE / "logs/browser-final.tap.gz").read_bytes()).decode()
require("tests 25" in focused and "pass 25" in focused and "fail 0" in focused,
        "focused receipt count changed")
require("tests 1" in browser and "pass 1" in browser and "fail 0" in browser,
        "browser receipt count changed")
print("Verified", len(record["inputs"]), "selected Git-bound executed inputs and",
      len(manifest["files"]), "receipts; finite synthetic-port workflow only")
