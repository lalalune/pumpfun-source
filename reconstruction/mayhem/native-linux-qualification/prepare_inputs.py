#!/usr/bin/env python3
"""Download and authenticate the official v1.54 SDK and Mayhem crate closure."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tomllib
import urllib.request


SDK_URL = "https://github.com/anza-xyz/platform-tools/releases/download/v1.54/platform-tools-linux-x86_64.tar.bz2"
SDK_SHA256 = "fcc41631c7f77561bf5412218bf297501dccf0305ea280f338f0ace2aab9f31e"
VENDOR_CLOSURE_SHA256 = "c679e8263e597ef94ff3b0a518a6c56a5909188acee6693ccd554248d5746097"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe(name: str) -> str:
    path = PurePosixPath(name)
    require(name and not path.is_absolute() and ".." not in path.parts and path.as_posix() == name, "unsafe archive path")
    return name


def download(url: str, destination: Path, expected: str) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "pumpfun-source-mayhem-linux-qualification/1"})
    temporary = destination.with_suffix(destination.suffix + ".partial")
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("xb") as output:
        shutil.copyfileobj(response, output, 1024 * 1024)
    require(sha256(temporary) == expected, f"download digest differs: {url}")
    temporary.rename(destination)


def extract_crate(archive: Path, package: str, destination: Path, package_sha256: str, file_count: int) -> None:
    destination.mkdir()
    prefix = package + "/"
    with tarfile.open(archive, mode="r:*") as source:
        for member in source:
            if member.isdir():
                continue
            require(member.isfile() and member.name.startswith(prefix), f"nonregular crate member: {member.name}")
            relative = safe(member.name[len(prefix) :])
            extracted = source.extractfile(member)
            require(extracted is not None, f"unreadable crate member: {member.name}")
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(extracted.read())
    files = {
        path.relative_to(destination).as_posix(): sha256(path)
        for path in sorted(destination.rglob("*"))
        if path.is_file()
    }
    require(len(files) == file_count, f"crate file count differs: {package}")
    checksum = {"files": files, "package": package_sha256}
    (destination / ".cargo-checksum.json").write_text(
        json.dumps(checksum, separators=(",", ":")), encoding="utf-8", newline="\n"
    )


def prepare(repo: Path, output: Path) -> dict[str, object]:
    require(not output.exists(), "output directory must be absent")
    output.mkdir(parents=True)
    sdk = output / "platform-tools-linux-x86_64-v1.54.tar.bz2"
    download(SDK_URL, sdk, SDK_SHA256)

    controller = repo / "research/mayhem-fresh-host-20261028/controller"
    records = json.loads((controller / "vendor-inputs.json").read_text())["packages"]
    lock = tomllib.loads((repo / "programs/mayhem/Cargo.lock").read_text(encoding="utf-8"))
    registry = {
        row["checksum"]: (row["name"], row["version"])
        for row in lock["package"]
        if str(row.get("source", "")).startswith("registry+") and "checksum" in row
    }
    require(len(registry) == 214, "Cargo.lock registry closure differs")
    vendor = output / "vendor"
    archives = output / "crate-archives"
    vendor.mkdir()
    archives.mkdir()
    receipt = []
    closure = []
    for row in records:
        package_sha = row["package_sha256"]
        if package_sha in registry:
            name, version = registry[package_sha]
        else:
            require(row["directory"] == "anchor-lang-1.0.0", "vendor package absent from Cargo.lock")
            name, version = "anchor-lang", "1.0.0"
        package = f"{name}-{version}"
        require(package == row["directory"], f"vendor directory binding differs: {row['directory']}")
        archive = archives / f"{package}.crate"
        url = f"https://static.crates.io/crates/{name}/{package}.crate"
        download(url, archive, package_sha)
        extract_crate(archive, package, vendor / package, package_sha, row["file_count"])
        file_map = json.loads((vendor / package / ".cargo-checksum.json").read_text())["files"]
        closure.append({"directory": package, "package_sha256": package_sha, "files": file_map})
        receipt.append(
            {
                "directory": package,
                "url": url,
                "archive": {"bytes": archive.stat().st_size, "sha256": sha256(archive)},
                "source_files": row["file_count"],
            }
        )
    closure_sha256 = hashlib.sha256(
        json.dumps(closure, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    require(closure_sha256 == VENDOR_CLOSURE_SHA256, "complete vendor source closure differs")
    result = {
        "sdk": {"url": SDK_URL, "bytes": sdk.stat().st_size, "sha256": sha256(sdk)},
        "vendor_closure_sha256": closure_sha256,
        "vendor_packages": receipt,
    }
    (output / "receipt.json").write_text(json.dumps(result, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.repo.resolve(), args.output.resolve())
    print(json.dumps({"sdk": result["sdk"], "vendor_packages": len(result["vendor_packages"])}, indent=2))


if __name__ == "__main__":
    main()
