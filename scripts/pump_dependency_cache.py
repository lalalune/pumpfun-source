"""Immutable external-dependency snapshots for fresh main Pump Cargo targets.

Main artifacts, all incremental/build directories, and build-script fingerprints
are excluded. Cargo remains responsible for rebuilding the main crate and any
external dependency whose fresh-target inputs are incomplete or invalidated.
"""

import ctypes, hashlib, json, os, re, shutil, subprocess, sys, tempfile, tarfile, tomllib
from pathlib import Path


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def digest(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def tree(root):
    return {
        str(p.relative_to(root)): sha(p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
        and not p.is_symlink()
        and not {".git", "target", "__pycache__"}.intersection(
            p.relative_to(root).parts
        )
    }


def clone_file(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    method = "copy2"
    if sys.platform == "darwin":
        lib = ctypes.CDLL(None, use_errno=True)
        if (
            hasattr(lib, "clonefile")
            and lib.clonefile(os.fsencode(source), os.fsencode(dest), 0) == 0
        ):
            method = "apfs-clonefile"
    if not dest.exists():
        shutil.copy2(source, dest)
    assert not os.path.samefile(source, dest), "cache entries must never be hardlinked"
    assert sha(source) == sha(dest)
    return method


class DependencyCache:
    def __init__(
        self, cache_root, repository, crate, workspace, sdk, env, wrapper, direct=False,
        target_library_profile=None
    ):
        self.sdk = sdk
        self.target = (target_library_profile or {}).get("target", "sbf-solana-solana")
        assert self.target in ["sbf-solana-solana", "sbpf-solana-solana"]
        self.target_flags_key = "CARGO_TARGET_" + self.target.upper().replace("-", "_") + "_RUSTFLAGS"
        self.direct = direct
        self.root = Path(cache_root).resolve()
        self.repo = repository
        self.crate = crate
        self.workspace = workspace
        self.env = env
        cmd = [
            str(sdk / "rust/bin/cargo"),
            "metadata",
            "--manifest-path",
            str(crate / "Cargo.toml"),
            "--locked",
            "--offline",
            "--format-version",
            "1",
            "--filter-platform",
            self.target,
        ]
        metadata = json.loads(
            subprocess.check_output(cmd, cwd=workspace, env=env, text=True)
        )
        self.package_id = metadata["resolve"]["root"]
        packages = metadata["packages"]
        main = next(p for p in packages if p["id"] == self.package_id)
        assert not any("custom-build" in p["kind"] for p in main["targets"]), (
            "main build.rs is not cache supported"
        )
        external = [p for p in packages if p["id"] != self.package_id]
        assert all((p.get("source") or "").startswith("registry+") for p in external), (
            "local dependency caching is unsupported"
        )
        self.packages = {p["name"] for p in external}
        self.crates = {
            t["name"]
            for p in external
            for t in p["targets"]
            if "custom-build" not in t["kind"]
        }
        self.main_names = {main["name"], *(t["name"] for t in main["targets"])}
        self.sources = {
            str(Path(p["manifest_path"]).parent.resolve()): tree(
                Path(p["manifest_path"]).parent.resolve()
            )
            for p in external
        }
        self.tools = {
            str(p.relative_to(sdk)): sha(p)
            for p in sorted((sdk / "rust/lib").rglob("*"))
            if p.is_file()
        }
        for rel in [
            "rust/bin/rustc",
            "rust/bin/cargo",
            "llvm/bin/llvm-objcopy",
            "llvm/bin/ld.lld",
            "llvm/bin/clang",
            "llvm/bin/llvm-ar",
        ]:
            p = sdk / rel
            if p.exists():
                self.tools[rel] = sha(p)
        manifests = {
            str(p.relative_to(workspace)): sha(p)
            for p in {
                crate / "Cargo.toml",
                workspace / "Cargo.toml",
                workspace / "Cargo.lock",
                crate / "Cargo.lock",
            }
            if p.exists()
        }
        flags = {
            k: v
            for k, v in env.items()
            if k
            in [
                "RUSTFLAGS",
                "CARGO_ENCODED_RUSTFLAGS",
                self.target_flags_key,
                "RUSTC_BOOTSTRAP",
            ]
            or k.startswith("CARGO_PROFILE_")
        }
        ancestors = set()
        for start in [crate, workspace]:
            for directory in [start, *start.parents]:
                ancestors.add(directory)
                if directory == repository:
                    break
        configs = {
            str(p): sha(p)
            for directory in ancestors
            for p in [
                directory / ".cargo/config",
                directory / ".cargo/config.toml",
                directory / "rust-toolchain",
                directory / "rust-toolchain.toml",
            ]
            if p.exists()
        }
        configs.update(
            {
                str(p): sha(p)
                for p in [
                    Path(env["CARGO_HOME"]) / "config",
                    Path(env["CARGO_HOME"]) / "config.toml",
                ]
                if p.exists()
            }
        )
        self.configs = configs
        self.context = {
            "format": 3 if direct else 2,
            "execution": "fresh-cargo-plan-rustc" if direct else "cargo",
            "cargo_home": str(Path(env["CARGO_HOME"]).resolve()),
            "sdk": self.tools,
            "manifests": manifests,
            "flags": flags,
            "configs": configs,
            "wrapper_sha256": sha(wrapper),
            "external_sources": self.sources,
            "main_names": sorted(self.main_names),
            "packages": sorted(self.packages),
            "crates": sorted(self.crates),
        }
        if target_library_profile is not None:
            self.context["target_library_profile"] = target_library_profile
        self.key = digest(self.context)
        self.entry = self.root / self.key
        self.record = {
            "key": self.key,
            "cache_root": str(self.root),
            "status": "miss",
            "seeded_files": 0,
            "excluded": [
                "main project artifacts and fingerprints",
                "all build directories",
                "all incremental directories",
                "all build-script fingerprints",
            ],
            "source_integrity": "full external package file hashes before and after Cargo build",
        }

    def allowed(self, rel):
        path = Path(rel)
        parts = path.parts
        if path.is_absolute() or any(p in ["..", "."] for p in parts):
            return False
        prefix = parts[1:] if parts and parts[0] == self.target else parts
        if (
            len(prefix) < 3
            or prefix[0] != "release"
            or prefix[1] not in ["deps", ".fingerprint"]
        ):
            return False
        if any(p in ["build", "incremental"] for p in parts):
            return False
        if any(
            any(
                p == n
                or p.startswith(n + "-")
                or p.startswith("lib" + n + "-")
                or p == "lib" + n + ".rlib"
                for n in self.main_names
            )
            for p in parts
        ):
            return False
        if ".fingerprint" in parts:
            if self.direct:
                return False
            i = parts.index(".fingerprint")
            if i + 2 != len(parts) - 1:
                return False
            folder = parts[i + 1]
            name = parts[-1]
            return "build-script" not in name and any(
                re.fullmatch(re.escape(n) + r"-[0-9a-f]+", folder)
                for n in self.packages
            )
        if "deps" in parts:
            name = parts[-1]
            return any(
                re.match(
                    r"(?:lib)?"
                    + re.escape(n)
                    + r"-[0-9a-f]+\.(?:rlib|rmeta|dylib|so|d|a)$",
                    name,
                )
                for n in self.crates
            )
        return False

    def seed(self, target):
        if not self.entry.exists():
            return
        manifest = json.loads((self.entry / "MANIFEST.json").read_text())
        assert manifest["context"] == self.context and manifest["key"] == self.key
        methods = set()
        for rel, h in manifest["files"].items():
            assert self.allowed(rel), rel
            source = self.entry / "files" / rel
            assert source.is_file() and not source.is_symlink()
            assert sha(source) == h, rel
            methods.add(clone_file(source, target / rel))
        self.record.update(
            status="hit",
            seeded_files=len(manifest["files"]),
            manifest_sha256=sha(self.entry / "MANIFEST.json"),
            clone_methods=sorted(methods),
        )

    def finish(self, target, log, build_report):
        assert self.sources == {p: tree(Path(p)) for p in self.sources}, (
            "external dependency source changed during build"
        )
        assert all(
            sha(self.workspace / p) == h
            for p, h in self.context["manifests"].items()
        ), "Cargo manifests changed during build"
        assert all(sha(self.sdk / p) == h for p, h in self.tools.items()), (
            "SDK changed during build"
        )
        assert all(sha(p) == h for p, h in self.configs.items()), (
            "Cargo configuration changed during build"
        )
        artifacts = []
        for line in log.read_text().splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("reason") == "compiler-artifact":
                artifacts.append(r)
        if self.direct and self.record.get("main_command"):
            assert self.record.get("main_freshly_compiled")
        else:
            main = [r for r in artifacts if r["package_id"] == self.package_id]
            assert main and all(not r["fresh"] for r in main), (
                "main crate was not freshly compiled"
            )
            self.record.update(
                main_freshly_compiled=True,
                external_fresh=sum(
                    r["fresh"] for r in artifacts if r["package_id"] != self.package_id
                ),
                external_rebuilt=sum(
                    not r["fresh"]
                    for r in artifacts
                    if r["package_id"] != self.package_id
                ),
            )
        self.publish(target, build_report)

    def publish(self, target, build_report):
        if self.entry.exists():
            return
        self.root.mkdir(parents=True, exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix="pending-", dir=self.root))
        files = {}
        methods = set()
        try:
            for p in sorted(target.rglob("*")):
                if not p.is_file() or p.is_symlink():
                    continue
                rel = str(p.relative_to(target))
                if not self.allowed(rel):
                    continue
                # A folder containing a build-script action is never reusable as a lib fingerprint.
                if ".fingerprint" in p.parts and any(
                    "build-script" in q.name for q in p.parent.iterdir()
                ):
                    continue
                methods.add(clone_file(p, temp / "files" / rel))
                files[rel] = sha(p)
            assert files
            snapshot = json.loads(build_report.read_text())
            record = {
                "key": self.key,
                "context": self.context,
                "files": files,
                "producer_build_report": str(build_report),
                "producer_build_report_snapshot": snapshot,
                "producer_snapshot_sha256": digest(snapshot),
                "clone_methods": sorted(methods),
            }
            (temp / "MANIFEST.json").write_text(json.dumps(record, indent=2) + "\n")
            try:
                temp.rename(self.entry)
            except OSError:
                if not self.entry.is_dir():
                    raise
                winner = json.loads((self.entry / "MANIFEST.json").read_text())
                assert winner["key"] == self.key and winner["context"] == self.context
                assert winner["files"] == files, (
                    "conflicting dependency-cache publication"
                )
                assert all(
                    sha(self.entry / "files" / rel) == value
                    for rel, value in files.items()
                )
                shutil.rmtree(temp)
            self.record.update(
                published_files=len(files),
                manifest_sha256=sha(self.entry / "MANIFEST.json"),
            )
        except BaseException:
            if temp.exists():
                shutil.rmtree(temp)
            raise

    def import_clean_build(self, build):
        report = build / "build-comparison.json"
        r = json.loads(report.read_text())
        assert r["returncode"] == 0 and r["source_unchanged"]
        assert r.get("target_library_profile", {}).get("cache_context") == self.context.get("target_library_profile"), (
            "seed target-library profile differs"
        )
        assert all(sha(self.repo / k) == v for k, v in r["source_sha256"].items())
        assert sha(build / "candidate.so") == r["comparison"]["candidate_sha256"]
        assert sha(build / "unstripped.so") == r["unstripped_sha256"]
        tools = r.get("tool_sha256", {})
        assert tools.get("rustc", r.get("rustc_sha256")) == self.tools["rust/bin/rustc"]
        assert tools.get("cargo", r.get("cargo_sha256")) == self.tools["rust/bin/cargo"]
        assert r["source_wrapper_sha256"] == self.context["wrapper_sha256"]
        assert (
            Path(r["environment"]["CARGO_HOME"]).resolve()
            == Path(self.env["CARGO_HOME"]).resolve()
        ), "seed Cargo registry path differs"
        command = r["command"]
        source = Path(command[command.index("--manifest-path") + 1]).parent

        def package_and_profile(crate):
            d = tomllib.loads((crate / "Cargo.toml").read_text())
            package = {k: v for k, v in d.items() if k not in ["workspace", "profile"]}
            workspace = crate
            if "workspace" not in d:
                workspace = next(
                    p
                    for p in crate.parents
                    if (p / "Cargo.toml").is_file()
                    and "workspace" in tomllib.loads((p / "Cargo.toml").read_text())
                )
            w = tomllib.loads((workspace / "Cargo.toml").read_text())
            lock = workspace / "Cargo.lock"
            return package, w.get("profile", {}), sha(lock)

        assert package_and_profile(source) == package_and_profile(self.crate), (
            "seed dependency/profile context differs"
        )
        for name in [
            self.target_flags_key,
            "RUSTFLAGS",
            "CARGO_ENCODED_RUSTFLAGS",
        ]:
            assert r["environment"].get(name) == self.env.get(name), (
                "seed compiler flags differ"
            )
        # Independently bind every current external source file to its official locked
        # registry archive before accepting artifacts from this older clean build.
        lock = tomllib.loads(
            next(
                p
                for p in [self.workspace / "Cargo.lock", self.crate / "Cargo.lock"]
                if p.exists()
            ).read_text()
        )
        checks = {(p["name"], p["version"]): p.get("checksum") for p in lock["package"]}
        files = 0
        for directory in self.sources:
            directory = Path(directory)
            meta = tomllib.loads((directory / "Cargo.toml").read_text())["package"]
            name, version = meta["name"], meta["version"]
            archive = next(
                (Path(self.env["CARGO_HOME"]) / "registry/cache").glob(
                    "*/" + name + "-" + version + ".crate"
                )
            )
            assert sha(archive) == checks[(name, version)]
            with tarfile.open(archive, "r:gz") as t:
                for member in t:
                    if not member.isfile():
                        continue
                    relative = Path(member.name).relative_to(name + "-" + version)
                    file = directory / relative
                    assert (
                        file.is_file()
                        and t.extractfile(member).read() == file.read_bytes()
                    ), str(file)
                    files += 1
        self.publish(build / "target", report)
        self.record["imported_clean_build"] = {
            "path": str(build),
            "report_sha256": sha(report),
            "archive_files_verified": files,
        }

    def compile_main(self, target, log):
        cargo = Path(self.env["RUSTC"]).with_name("cargo")
        command = [
            str(cargo),
            "build",
            "--manifest-path",
            str(self.crate / "Cargo.toml"),
            "--release",
            "--target",
            self.target,
            "--locked",
            "--offline",
            "-Z",
            "unstable-options",
            "--build-plan",
        ]
        plan_run = subprocess.run(
            command,
            cwd=self.workspace,
            env=self.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if plan_run.returncode:
            raise RuntimeError("Cargo build plan failed: " + plan_run.stderr)
        plan = json.loads(plan_run.stdout)
        # Cargo planning may remove outputs for units it marks dirty. Restore only
        # verified external libraries after the plan, before invoking main rustc.
        self.seed(target)
        plan_path = target.parent / "build-plan.json"
        plan_path.write_text(json.dumps(plan, indent=2) + "\n")
        package = tomllib.loads((self.crate / "Cargo.toml").read_text())["package"][
            "name"
        ]
        options = [
            x
            for x in plan["invocations"]
            if x["package_name"] == package
            and x["compile_mode"] == "build"
            and "cdylib" in x["target_kind"]
        ]
        assert len(options) == 1
        main = options[0]
        args = main["args"]
        program = main["program"]
        cwd = Path(main["cwd"]).resolve()
        cwd.relative_to(self.repo)
        assert "OUT_DIR" not in main["env"], "main build script outputs are unsupported"
        assert Path(program).resolve() in [
            Path(self.env["RUSTC"]).resolve(),
            Path(self.env["RUSTC_WRAPPER"]).resolve(),
        ]
        for i, arg in enumerate(args):
            if arg == "-L":
                assert args[i + 1].startswith("dependency=" + str(target)), (
                    "native/outside search path is unsupported"
                )
            if arg == "--extern":
                path = Path(args[i + 1].split("=", 1)[1])
                path.relative_to(target)
                assert path.is_file(), path
        for output in main["outputs"]:
            path = Path(output)
            path.relative_to(target)
            assert not path.exists(), "main artifact already existed before compiler"
            path.parent.mkdir(parents=True, exist_ok=True)
        env = self.env.copy()
        env.update(main["env"])
        self.record.update(
            execution="fresh-cargo-plan-rustc",
            build_plan_command=command,
            build_plan_sha256=sha(plan_path),
            main_command=[program, *args],
            main_cwd=str(cwd),
            main_environment=main["env"],
        )
        result = subprocess.run(
            [program, *args], cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT
        )
        if result.returncode == 0:
            for dest, source in main["links"].items():
                if Path(source).exists():
                    shutil.copy2(source, dest)
            self.record["main_freshly_compiled"] = True
        return result
