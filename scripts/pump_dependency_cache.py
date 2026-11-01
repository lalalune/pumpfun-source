"""Immutable external-dependency snapshots for fresh main Pump Cargo targets.

Main artifacts, all incremental/build directories, and build-script fingerprints
are excluded. Cargo remains responsible for rebuilding the main crate and any
external dependency whose fresh-target inputs are incomplete or invalidated.
"""

import ctypes, hashlib, json, os, re, shutil, stat, subprocess, sys, tempfile, tarfile, tomllib
from pathlib import Path, PurePosixPath, PureWindowsPath


def check(condition, message):
    """Fail closed under optimized Python, where assert statements vanish."""
    if not condition:
        raise AssertionError(message)


def sha(p):
    result = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            result.update(block)
    return result.hexdigest()


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


def dep_info_environment(text):
    """Read rustc's env!/option_env! bindings without recording unrelated env."""
    def unescape(value):
        result, index = [], 0
        escapes = {"n": "\n", "r": "\r", "\\": "\\"}
        while index < len(value):
            char = value[index]
            if char == "\\":
                index += 1
                if index == len(value) or value[index] not in escapes:
                    raise ValueError("invalid rustc env-dep escape")
                char = escapes[value[index]]
            result.append(char)
            index += 1
        return "".join(result)

    result = {}
    for line in text.split("\n"):
        if not line.startswith("# env-dep:"):
            continue
        name, separator, value = line[len("# env-dep:"):].partition("=")
        name = unescape(name)
        value = unescape(value) if separator else None
        if name in result and result[name] != value:
            raise ValueError("conflicting rustc env-dep bindings")
        result[name] = value
    return result


def _is_link_or_reparse(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_reparse_tag", 0))


def _confined_target_path(raw_path, target, cwd):
    check(
        isinstance(raw_path, str) and bool(raw_path) and "\0" not in raw_path,
        "invalid target path in build plan",
    )
    raw = Path(raw_path)
    check(".." not in raw.parts, "path traversal in target path is unsupported")
    abs_target = Path(os.path.abspath(target))
    try:
        target_info = abs_target.lstat()
    except FileNotFoundError:
        target_info = None
    if target_info is not None:
        check(
            not _is_link_or_reparse(target_info),
            "symlinked target path is unsupported: " + str(target),
        )
    resolved_target = abs_target.resolve()
    candidate = raw if raw.is_absolute() else Path(cwd) / raw
    abs_candidate = Path(os.path.abspath(candidate))
    for root_prefix in (abs_target, resolved_target):
        try:
            rel = abs_candidate.relative_to(root_prefix)
            break
        except ValueError:
            continue
    else:
        raise AssertionError("native/outside target path is unsupported: " + str(raw_path))
    cursor = root_prefix
    for part in rel.parts:
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except FileNotFoundError:
            continue
        check(
            not _is_link_or_reparse(info),
            "symlinked target path is unsupported: " + str(raw_path),
        )
    resolved = abs_candidate.resolve()
    check(
        resolved.is_relative_to(resolved_target),
        "native/outside target path is unsupported: " + str(raw_path),
    )
    return resolved


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
    check(not os.path.samefile(source, dest), "cache entries must never be hardlinked")
    check(sha(source) == sha(dest), "cache verification failed: sha(source) == sha(dest)")
    return method


class DependencyCache:
    def __init__(
        self, cache_root, repository, crate, workspace, sdk, env, wrapper, direct=False,
        target_library_profile=None, wrapper_launcher=None
    ):
        self.sdk = sdk
        self.target = (target_library_profile or {}).get("target", "sbf-solana-solana")
        check(self.target in ["sbf-solana-solana", "sbpf-solana-solana"], "cache verification failed: self.target in ['sbf-solana-solana', 'sbpf-solana-solana']")
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
        check(not any("custom-build" in p["kind"] for p in main["targets"]), (
            "main build.rs is not cache supported"
        ))
        external = [p for p in packages if p["id"] != self.package_id]
        check(all((p.get("source") or "").startswith("registry+") for p in external), (
            "local dependency caching is unsupported"
        ))
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
        # Cargo reads every parent of its working directory, including above the repository.
        for start in [crate, workspace]:
            ancestors.update([start, *start.parents])
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
        if wrapper_launcher is not None:
            self.context["wrapper_launcher_sha256"] = sha(wrapper_launcher)
            self.context["wrapper_python"] = env["PUMP_VERIFIED_PYTHON"]
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
        if not isinstance(rel, str) or not rel or "\0" in rel:
            return False
        posix_rel = PurePosixPath(rel)
        windows_rel = PureWindowsPath(rel)
        if (
            rel.startswith(("/", "\\"))
            or posix_rel.is_absolute()
            or windows_rel.is_absolute()
            or windows_rel.drive
            or windows_rel.root
        ):
            return False
        parts = tuple(rel.replace("\\", "/").split("/"))
        if any(p in ["", "..", "."] for p in parts):
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
        if prefix[1] == "deps":
            if len(prefix) != 3:
                return False
            name = prefix[2]
            return any(
                re.fullmatch(
                    r"(?:lib)?"
                    + re.escape(n)
                    + r"-[0-9a-f]+\.(?:rlib|rmeta|dylib|so|d|a)",
                    name,
                )
                for n in self.crates
            )
        return False

    def seed(self, target):
        if not self.entry.exists():
            return
        manifest = json.loads((self.entry / "MANIFEST.json").read_text())
        check(manifest["context"] == self.context and manifest["key"] == self.key, "cache verification failed: manifest['context'] == self.context and manifest['key'] == self.key")
        methods = set()
        for rel, h in manifest["files"].items():
            check(self.allowed(rel), rel)
            source = self.entry / "files" / rel
            check(source.is_file() and not source.is_symlink(), "cache verification failed: source.is_file() and not source.is_symlink()")
            check(sha(source) == h, rel)
            methods.add(clone_file(source, target / rel))
        self.record.update(
            status="hit",
            seeded_files=len(manifest["files"]),
            manifest_sha256=sha(self.entry / "MANIFEST.json"),
            clone_methods=sorted(methods),
        )

    def finish(self, target, log, build_report):
        check(self.sources == {p: tree(Path(p)) for p in self.sources}, (
            "external dependency source changed during build"
        ))
        check(all(
            sha(self.workspace / p) == h
            for p, h in self.context["manifests"].items()
        ), "Cargo manifests changed during build")
        check(all(sha(self.sdk / p) == h for p, h in self.tools.items()), (
            "SDK changed during build"
        ))
        check(all(sha(p) == h for p, h in self.configs.items()), (
            "Cargo configuration changed during build"
        ))
        artifacts = []
        for line in log.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict):
                # A torn JSON line can be valid but not an object (e.g. a bare
                # number); skip it like any other non-artifact line.
                continue
            if r.get("reason") == "compiler-artifact":
                artifacts.append(r)
        if self.direct and self.record.get("main_command"):
            check(self.record.get("main_freshly_compiled"), "cache verification failed: self.record.get('main_freshly_compiled')")
        else:
            main = [r for r in artifacts if r["package_id"] == self.package_id]
            check(main and all(not r["fresh"] for r in main), (
                "main crate was not freshly compiled"
            ))
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
            check(files, "cache verification failed: files")
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
            (temp / "MANIFEST.json").write_text(json.dumps(record, indent=2) + "\n",encoding='utf-8',newline='\n')
            try:
                temp.rename(self.entry)
            except OSError:
                if not self.entry.is_dir():
                    raise
                winner = json.loads((self.entry / "MANIFEST.json").read_text())
                check(winner["key"] == self.key and winner["context"] == self.context, "cache verification failed: winner['key'] == self.key and winner['context'] == self.context")
                check(winner["files"] == files, (
                    "conflicting dependency-cache publication"
                ))
                check(all(
                    sha(self.entry / "files" / rel) == value
                    for rel, value in files.items()
                ), "cache verification failed: all(")
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
        check(r["returncode"] == 0 and r["source_unchanged"], "cache verification failed: r['returncode'] == 0 and r['source_unchanged']")
        check(r.get("target_library_profile", {}).get("cache_context") == self.context.get("target_library_profile"), (
            "seed target-library profile differs"
        ))
        check(r["source_sha256"], "cache verification failed: clean build binds no source")
        check(all(sha(self.repo / k) == v for k, v in r["source_sha256"].items()), "cache verification failed: all(sha(self.repo / k) == v for k, v in r['source_sha256'].items())")
        check(sha(build / "candidate.so") == r["comparison"]["candidate_sha256"], "cache verification failed: sha(build / 'candidate.so') == r['comparison']['candidate_sha256']")
        check(sha(build / "unstripped.so") == r["unstripped_sha256"], "cache verification failed: sha(build / 'unstripped.so') == r['unstripped_sha256']")
        tools = r.get("tool_sha256", {})
        check(tools.get("rustc", r.get("rustc_sha256")) == self.tools["rust/bin/rustc"], "cache verification failed: tools.get('rustc', r.get('rustc_sha256')) == self.tools['rust/bin/rust")
        check(tools.get("cargo", r.get("cargo_sha256")) == self.tools["rust/bin/cargo"], "cache verification failed: tools.get('cargo', r.get('cargo_sha256')) == self.tools['rust/bin/carg")
        check(r["source_wrapper_sha256"] == self.context["wrapper_sha256"], "cache verification failed: r['source_wrapper_sha256'] == self.context['wrapper_sha256']")
        check(r.get("source_wrapper_launcher_sha256") == self.context.get("wrapper_launcher_sha256"),
              "seed compiler wrapper launcher differs")
        if "wrapper_python" in self.context:
            check(r["environment"].get("PUMP_VERIFIED_PYTHON") == self.context["wrapper_python"],
                  "seed compiler wrapper Python differs")
        check((
            Path(r["environment"]["CARGO_HOME"]).resolve()
            == Path(self.env["CARGO_HOME"]).resolve()
        ), "seed Cargo registry path differs")
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

        check(package_and_profile(source) == package_and_profile(self.crate), (
            "seed dependency/profile context differs"
        ))
        for name in [
            self.target_flags_key,
            "RUSTFLAGS",
            "CARGO_ENCODED_RUSTFLAGS",
        ]:
            check(r["environment"].get(name) == self.env.get(name), (
                "seed compiler flags differ"
            ))
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
            check(sha(archive) == checks[(name, version)], "cache verification failed: sha(archive) == checks[(name, version)]")
            archived = set()
            with tarfile.open(archive, "r:gz") as t:
                for member in t:
                    if not member.isfile():
                        continue
                    relative = Path(member.name).relative_to(name + "-" + version)
                    archived.add(relative.as_posix())
                    file = directory / relative
                    check((
                        file.is_file()
                        and t.extractfile(member).read() == file.read_bytes()
                    ), str(file))
                    files += 1
            # The archive check above only proves archived files are present; Cargo also
            # compiles files that are not in it (an added build.rs runs at build time).
            present = {
                Path(d, n).relative_to(directory).as_posix()
                for d, dirs, names in os.walk(directory)
                for n in names + [x for x in dirs if Path(d, x).is_symlink()]
            }
            extra = present - archived - {".cargo-ok"}
            if extra:
                raise AssertionError(
                    f"{name}-{version}: files absent from locked archive: {sorted(extra)}"
                )
        self.publish(build / "target", report)
        self.record["imported_clean_build"] = {
            "path": str(build),
            "report_sha256": sha(report),
            "archive_files_verified": files,
        }

    def dependency_environment_changes(self, plan, target):
        """Compare cached rustc bindings with each fresh Cargo unit's environment."""
        changes = set()
        for invocation in plan["invocations"]:
            if invocation["package_name"] not in self.packages:
                continue
            effective = self.env | invocation["env"]
            dep_infos = set()
            for raw in invocation["outputs"]:
                output = _confined_target_path(raw, target, invocation["cwd"])
                if output.suffix not in {".rlib", ".rmeta", ".dylib", ".so", ".a"}:
                    continue
                info = output.with_name(output.stem.removeprefix("lib") + ".d")
                if self.allowed(info.relative_to(target).as_posix()):
                    dep_infos.add(info)
            for info in dep_infos:
                try:
                    bindings = dep_info_environment(info.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, ValueError):
                    changes.add("unavailable compiler env-dep information")
                    continue
                changes.update(name for name, value in bindings.items()
                               if effective.get(name) != value)
        return sorted(changes)

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
        plan_path.write_text(json.dumps(plan, indent=2) + "\n",encoding='utf-8',newline='\n')
        changed = self.dependency_environment_changes(plan, target)
        if changed:
            # A fresh plan does not execute Cargo's dependency invalidation.
            # Let Cargo rebuild instead of linking the old restored rlibs.
            # Keep the immutable entry for callers whose bindings still match.
            self.record.update(status="bypass", execution="cargo-environment-rebuild",
                               changed_environment_dependencies=changed)
            cargo_command = command[:-3] + ["--message-format=json-render-diagnostics"]
            return subprocess.run(cargo_command, cwd=self.workspace, env=self.env,
                                  stdout=log, stderr=subprocess.STDOUT)
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
        check(len(options) == 1, "cache verification failed: len(options) == 1")
        main = options[0]
        args = main["args"]
        program = main["program"]
        cwd = Path(main["cwd"]).resolve()
        cwd.relative_to(Path(self.repo).resolve())
        check("OUT_DIR" not in main["env"], "main build script outputs are unsupported")
        check(Path(program).resolve() in [
            Path(self.env["RUSTC"]).resolve(),
            Path(self.env["RUSTC_WRAPPER"]).resolve(),
        ], "cache verification failed: Path(program).resolve() in [")
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "-L":
                check(i + 1 < len(args), "missing -L search path argument")
                spec = args[i + 1]
                i += 2
            elif arg.startswith("-L"):
                spec = arg[2:]
                i += 1
            elif arg == "--extern":
                check(i + 1 < len(args), "missing --extern crate argument")
                spec = args[i + 1]
                i += 2
                check("=" in spec, "unsupported --extern specification")
                ext_path = _confined_target_path(spec.split("=", 1)[1], target, cwd)
                check(ext_path.is_file(), ext_path)
                continue
            elif arg.startswith("--extern="):
                spec = arg[len("--extern="):]
                i += 1
                check("=" in spec, "unsupported --extern specification")
                ext_path = _confined_target_path(spec.split("=", 1)[1], target, cwd)
                check(ext_path.is_file(), ext_path)
                continue
            elif arg in ("--out-dir", "-o"):
                check(i + 1 < len(args), f"missing {arg} path argument")
                _confined_target_path(args[i + 1], target, cwd)
                i += 2
                continue
            elif arg.startswith("--out-dir="):
                _confined_target_path(arg[len("--out-dir="):], target, cwd)
                i += 1
                continue
            elif arg.startswith("-o") and len(arg) > 2:
                _confined_target_path(arg[2:], target, cwd)
                i += 1
                continue
            else:
                i += 1
                continue
            check(spec.startswith("dependency="), (
                "native/outside search path is unsupported"
            ))
            _confined_target_path(spec[len("dependency="):], target, cwd)
        confined_outputs = []
        for output in main["outputs"]:
            out_path = _confined_target_path(output, target, cwd)
            check(
                not out_path.exists() and not out_path.is_symlink(),
                "main artifact already existed before compiler",
            )
            confined_outputs.append(out_path)
        confined_links = []
        for dest, source in main.get("links", {}).items():
            dest_path = _confined_target_path(dest, target, cwd)
            source_path = _confined_target_path(source, target, cwd)
            confined_links.append((dest_path, source_path))
        for out_path in confined_outputs:
            out_path.parent.mkdir(parents=True, exist_ok=True)
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
            for dest_path, source_path in confined_links:
                checked_source = _confined_target_path(str(source_path), target, cwd)
                checked_dest = _confined_target_path(str(dest_path), target, cwd)
                if checked_source.is_file():
                    checked_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(checked_source, checked_dest)
            self.record["main_freshly_compiled"] = True
        return result
