"""Certificate-bound ordering of one evidenced pair of main Pump data sections."""

import collections
import bisect
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import struct

from build_source_manifest import source_manifest
from pump_compare_function_bytes import normalize
from pump_dependency_cache import digest
import pump_target_library_profile as profiles

ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "evidence/original/pump/deployed.so").is_file()
)
HERE = Path(__file__).resolve().parent
ORIGINAL_SHA = "7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"
DATA_RULE = "  .data.rel.ro : { *(.data.rel.ro*) } :rodata"
ROLES = (
    {
        "role": "borsh_array_location",
        "original": 0x1BD930,
        "owner": 0x101448,
        "bytes": 1640,
        "offset": 1616,
        "footprint": 24,
    },
    {
        "role": "debug_argument_table",
        "original": 0x1BD948,
        "owner": 0x10C20,
        "bytes": 88,
        "offset": 56,
        "footprint": 32,
    },
)
MAP_LINE = re.compile(r"^\s*([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+(\d+) (.*)$")
SELECTOR = re.compile(
    r'\*[A-Za-z0-9_.:$+@/-]+\("\.data\.rel\.ro[A-Za-z0-9_.$:+@/-]*"\)'
)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Elf:
    def __init__(self, path):
        self.path = Path(path)
        self.raw = self.path.read_bytes()
        b = self.raw
        assert b[:6] == b"\x7fELF\x02\x01"
        self.entry, self.phoff, off = struct.unpack_from("<QQQ", b, 24)
        self.phsize, self.phcount, width, count, ni = struct.unpack_from(
            "<HHHHH", b, 54
        )
        headers = [
            struct.unpack_from("<IIQQQQIIQQ", b, off + i * width) for i in range(count)
        ]
        h = headers[ni]
        names = b[h[4] : h[4] + h[5]]
        self.sections = {}
        for h in headers:
            name = names[h[0] :].split(b"\0", 1)[0].decode()
            self.sections[name] = dict(
                name=name,
                type=h[1],
                flags=h[2],
                addr=h[3],
                offset=h[4],
                size=h[5],
                link=h[6],
                info=h[7],
                align=h[8],
                entsize=h[9],
            )

    def data(self, name):
        s = self.sections[name]
        return self.raw[s["offset"] : s["offset"] + s["size"]]

    def read(self, address, size):
        matches = [
            s
            for s in self.sections.values()
            if s["addr"]
            and s["type"] != 8
            and s["addr"] <= address
            and address + size <= s["addr"] + s["size"]
        ]
        assert len(matches) == 1, "field is not in one file-backed section"
        s = matches[0]
        at = s["offset"] + address - s["addr"]
        return self.raw[at : at + size]

    def relocations(self):
        raw = self.data(".rel.dyn")
        return dict(struct.unpack_from("<QQ", raw, i) for i in range(0, len(raw), 16))


def map_rows(path):
    result = []
    output = None
    for line in Path(path).read_text().splitlines()[1:]:
        m = MAP_LINE.match(line)
        if not m:
            continue
        addr, _, size, align, rest = m.groups()
        depth = len(rest) - len(rest.lstrip())
        rest = rest.strip()
        if depth == 0:
            output = rest
        elif depth == 8 and ":(" in rest and rest.endswith(")"):
            file, section = rest[:-1].rsplit(":(", 1)
            member = None
            if file.endswith(")") and "(" in file:
                # The archive member is the final suffix; parent directories
                # may themselves contain parentheses.
                file, member = file[:-1].rsplit("(", 1)
            result.append(
                dict(
                    out=output,
                    address=int(addr, 16),
                    size=int(size, 16),
                    align=int(align),
                    file=file,
                    member=member,
                    section=section,
                )
            )
    return result


def owner(row):
    name = Path(row["file"]).name
    return name + ":" + row["member"] if row["member"] else name


def section_key(row):
    return owner(row), row["section"]


def source_identity(path):
    path = Path(path).resolve()
    manifest = source_manifest(path, path, ROOT)
    result = {}
    for name, value in manifest.items():
        p = ROOT / name
        key = (
            str(p.relative_to(path)) if p.is_relative_to(path) else "repository:" + name
        )
        result[key] = value
    return result


def sdk_identity(native, profile_name=None, library_directory=None):
    native = Path(native).resolve()
    before = profiles.inventory(native)
    if profile_name is None:
        assert library_directory is None
        return {"profile": None, "sdk_manifest_sha256": digest(before)}
    assert library_directory
    spec_path, spec = profiles.specification(profile_name)
    libraries = Path(library_directory).resolve()
    profiles.validate_libraries(
        libraries, spec["target_libraries"], spec["empty_directories"]
    )
    for tool, expected in spec["native_tools"].items():
        assert sha(native / tool) == expected
    prefix = str(profiles.target_library_path(spec["target"])) + "/"
    after = {p: v for p, v in before.items() if not p.startswith(prefix)}
    for p in libraries.iterdir():
        if p.is_file():
            after[prefix + p.name] = {
                "sha256": sha(p),
                "mode": p.stat().st_mode & 0o777,
            }
    context = {
        "name": profile_name,
        "target": spec["target"],
        "profile_spec_sha256": sha(spec_path),
        "native_sdk_manifest_sha256": digest(before),
        "prepared_sdk_manifest_sha256": digest(after),
        "target_libraries": spec["target_libraries"],
        "empty_directories": spec["empty_directories"],
    }
    return {"profile": context, "sdk_manifest_sha256": digest(after)}


def graph(records):
    return sorted(
        [
            {"kind": r["kind"], "bytes": r["bytes"], "sha256": r["sha256"]}
            for r in records.values()
        ],
        key=lambda r: (r["kind"], r["sha256"], r["bytes"]),
    )


def argument_identity(args, records):
    out = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-o", "--output", "-L", "--library-path"):
            out.extend([a, "<output>" if a in ("-o", "--output") else "<search-path>"])
            i += 2
            continue
        if a in ("--script", "-T"):
            out.extend([a, "<sdk-script>"])
            i += 2
            continue
        if a.startswith(("--script=", "-Map=")):
            out.append(a.split("=", 1)[0] + "=<path>")
        elif a.startswith("--version-script="):
            p = a.split("=", 1)[1]
            out.append("--version-script=" + records[p]["sha256"])
        elif a in records:
            out.append("<" + records[a]["kind"] + ":" + records[a]["sha256"] + ">")
        else:
            out.append(a)
        i += 1
    return out


def implementation_hashes():
    names = [
        "pump_data_order.py",
        "pump_derive_data_order.py",
        "pump_compare_function_bytes.py",
        "pump_quote_control_function_match.py",
        "build_source_manifest.py",
        "pump_build_verified.py",
        "pump_text_layout.py",
        "pump_text_layout_default.ld",
        "pump_target_library_profile.py",
        "pump_linux_v144_sbf_libraries.json",
        "pump_linux_v144_sbpf_libraries.json",
        "pump_dependency_cache.py",
    ]
    return {n: sha(HERE / n) for n in names}


def derive_payload(build, text_order):
    if not __debug__:
        raise RuntimeError("data-order admission requires Python assertions enabled")
    build = Path(build).resolve()
    text_order = Path(text_order).resolve()
    rec_path = build / "build-comparison.json"
    attempt_path = build / "build-attempt.json"
    rec = json.loads(rec_path.read_text())
    attempt = json.loads(attempt_path.read_text())
    assert (
        rec["returncode"] == attempt["returncode"] == 0
        and rec["source_unchanged"]
        and attempt["source_unchanged"]
    )
    assert rec["dependency_cache"]["main_freshly_compiled"], (
        "baseline must be a verified fresh-main cache build"
    )
    assert sha(build / "candidate.so") == rec["comparison"]["candidate_sha256"]
    assert sha(build / "unstripped.so") == rec["unstripped_sha256"]
    source = Path(rec["primary_source_directory"])
    expected = {}
    for name, h in rec["primary_source_sha256"].items():
        p = ROOT / name
        assert sha(p) == h
        expected[
            str(p.relative_to(source))
            if p.is_relative_to(source)
            else "repository:" + name
        ] = h
    assert source_identity(source) == expected
    cache = rec["dependency_cache"]
    cm = Path(cache["cache_root"]) / cache["key"] / "MANIFEST.json"
    assert sha(cm) == cache["manifest_sha256"]
    context = json.loads(cm.read_text())["context"]
    inv_path = build / "link/linker-invocation.json"
    inv = json.loads(inv_path.read_text())
    assert digest(context) == cache["key"], (
        "baseline cache context does not match its key"
    )
    assert rec["source_wrapper_sha256"] == context["wrapper_sha256"], (
        "baseline source-wrapper context differs"
    )
    for r in inv["link_inputs"].values():
        assert (
            sha(r["copy"]) == r["sha256"]
            and Path(r["copy"]).stat().st_size == r["bytes"]
        )
    assert sha(inv["real_linker"]) == inv["real_linker_sha256"]
    from pump_text_layout import check_script

    text = text_order.read_text()
    check_script((HERE / "pump_text_layout_default.ld").read_text(), text)
    original_path = ROOT / "evidence/original/pump/deployed.so"
    assert sha(original_path) == ORIGINAL_SHA
    o, c = Elf(original_path), Elf(build / "unstripped.so")
    rows = map_rows(build / "link/link.map")
    text_rows = [r for r in rows if r["out"] == ".text"]
    data = [r for r in rows if r["out"] == ".data.rel.ro"]
    position = c.sections[".text"]["addr"]
    for r in text_rows:
        assert r["address"] == position
        position += r["size"]
    assert position == c.sections[".text"]["addr"] + c.sections[".text"]["size"]
    roles = []
    for role in ROLES:
        on = normalize(o.read(role["owner"], role["bytes"]), role["owner"], o.sections)[
            0
        ]
        matches = [
            r
            for r in text_rows
            if r["size"] == role["bytes"]
            and normalize(c.read(r["address"], r["size"]), r["address"], c.sections)[0]
            == on
        ]
        assert len(matches) == 1, "stable original role is absent or ambiguous"
        r = matches[0]
        old = o.read(role["owner"] + role["offset"], 16)
        now = c.read(r["address"] + role["offset"], 16)
        ptr = lambda b: (
            struct.unpack_from("<I", b, 4)[0] | struct.unpack_from("<I", b, 12)[0] << 32
        )
        assert old[0] == now[0] == 0x18 and ptr(old) == role["original"]
        target = ptr(now)
        hits = [
            (i, d)
            for i, d in enumerate(data)
            if d["address"] == target and d["size"] == role["footprint"]
        ]
        assert len(hits) == 1
        i, d = hits[0]
        roles.append(
            dict(
                role,
                candidate=target,
                candidate_owner=r["address"],
                data_index=i,
                input_owner=owner(d),
                input_section=d["section"],
            )
        )

    def loc(image, addr):
        ptr, n, line, column = struct.unpack("<QQII", image.read(addr, 24))
        assert image.relocations().get(addr) == 8 and ptr & 0xFFFFFFFF == 0, (
            "Location has an invalid pointer relocation"
        )
        return image.read(ptr >> 32, n).decode(), line, column

    assert (
        loc(o, ROLES[0]["original"])
        == loc(c, roles[0]["candidate"])
        == ("src/de/mod.rs", 637, 21)
    )
    table = roles[1]
    assert (
        o.read(table["original"] + 8, 16)
        == c.read(table["candidate"] + 8, 16)
        == struct.pack("<QQ", 8, 8)
    )
    for off, original_target, size in [(0, 0xAEF0, 8), (24, 0xA8F0, 48)]:
        for image, address in [
            (o, table["original"] + off),
            (c, table["candidate"] + off),
        ]:
            assert (
                image.relocations().get(address) == 8
                and struct.unpack("<Q", image.read(address, 8))[0] & 0xFFFFFFFF == 0
            ), "vtable has an invalid pointer relocation"
        assert (
            struct.unpack("<Q", o.read(table["original"] + off, 8))[0] >> 32
            == original_target
        )
        target = struct.unpack("<Q", c.read(table["candidate"] + off, 8))[0] >> 32
        assert any(r["address"] == target and r["size"] == size for r in text_rows)
        assert (
            normalize(o.read(original_target, size), original_target, o.sections)[0]
            == normalize(c.read(target, size), target, c.sections)[0]
        )
    li, ti = roles[0]["data_index"], roles[1]["data_index"]
    assert li == ti + 1, "objects are not reversed and adjacent"
    assert data[ti]["address"] + 32 == data[li]["address"]
    prefix = list(data[: li + 1])
    prefix[ti], prefix[li] = prefix[li], prefix[ti]
    selectors = ["*" + owner(r) + '("' + r["section"] + '")' for r in prefix]
    assert all(SELECTOR.fullmatch(s) for s in selectors) and len(selectors) == len(
        set(selectors)
    )
    sdk = Path(rec["environment"]["RUSTC"]).parents[2]
    profile = rec.get("target_library_profile", {}).get("cache_context")
    assert context.get("target_library_profile") == profile, (
        "baseline target-library profile context differs"
    )
    assert context["sdk"], 'baseline SDK binding is empty'
    assert all(sha(sdk / name) == h for name, h in context["sdk"].items()), (
        "baseline SDK differs from cache context"
    )
    sdk_hash = digest(profiles.inventory(sdk))
    if profile:
        assert sdk_hash == profile["prepared_sdk_manifest_sha256"]
    bindings = [
        rec_path,
        attempt_path,
        build / "candidate.so",
        build / "unstripped.so",
        build / "link/link.map",
        inv_path,
        cm,
        text_order,
    ]
    return {
        "baseline_build": str(build),
        "text_order": str(text_order),
        "source": expected,
        "workspace_layout": rec["workspace_layout"],
        "toolchain": {"profile": profile, "sdk_manifest_sha256": sdk_hash},
        "cache_context": context,
        "roles": roles,
        "data_selectors": selectors,
        "link_graph": graph(inv["link_inputs"]),
        "link_arguments": argument_identity(inv["incoming"], inv["link_inputs"]),
        "bindings": {str(p): sha(p) for p in bindings},
        "implementation": implementation_hashes(),
    }


def load_certificate(path):
    path = Path(path).resolve()
    cert = json.loads(path.read_text())
    assert set(cert) == {"schema", "payload"} and cert["schema"] == 1, (
        "unsupported data-order certificate"
    )
    p = cert["payload"]
    assert p["implementation"] == implementation_hashes(), (
        "data-order implementation changed"
    )
    for name, h in p["bindings"].items():
        assert sha(name) == h, "stale data-order baseline or text recipe"
    assert derive_payload(p["baseline_build"], p["text_order"]) == p, (
        "invalid data-order object/selector identity"
    )
    return cert


def check_request(
    path, source, sdk, profile_name, libraries, registry, workspace_layout, text_order
):
    cert = load_certificate(path)
    p = cert["payload"]
    assert source_identity(source) == p["source"], (
        "data-order source differs from identity build"
    )
    assert workspace_layout == p["workspace_layout"], (
        "data-order workspace layout differs"
    )
    flags = {
        k: v
        for k, v in os.environ.items()
        if k in ("RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC_BOOTSTRAP")
        or k.startswith("CARGO_PROFILE_")
    }
    target = p["toolchain"]["profile"]["target"] if p["toolchain"]["profile"] else "sbf-solana-solana"
    target_flags_key = "CARGO_TARGET_" + target.upper().replace("-", "_") + "_RUSTFLAGS"
    flags[target_flags_key] = "-Zremap-cwd-prefix="
    assert flags == p["cache_context"]["flags"], "data-order compiler flags differ"
    assert (
        sha(ROOT / "scripts/pump_physical_source_wrapper.py")
        == p["cache_context"]["wrapper_sha256"]
    ), "data-order source wrapper differs"
    assert all(sha(name) == h for name, h in p["cache_context"]["configs"].items()), (
        "data-order Cargo configuration differs"
    )
    assert sdk_identity(sdk, profile_name, libraries) == p["toolchain"], (
        "data-order SDK/profile differs"
    )
    assert str(Path(registry).resolve()) == p["cache_context"]["cargo_home"], (
        "data-order registry differs"
    )
    assert sha(text_order) == p["bindings"][p["text_order"]], (
        "data-order text recipe differs"
    )
    return cert


def render(text, cert):
    p = cert["payload"]
    assert hashlib.sha256(text.encode()).hexdigest() == p["bindings"][p["text_order"]]
    assert text.count(DATA_RULE) == 1
    replacement = (
        "  .data.rel.ro : {\n"
        + "".join("    " + s + "\n" for s in p["data_selectors"])
        + "    *(.data.rel.ro*)\n  } :rodata"
    )
    return text.replace(DATA_RULE, replacement)


def check_combined(script, cert):
    text = Path(cert["payload"]["text_order"]).read_text()
    assert render(text, cert) == script, "unadmitted data-order linker statement"
    return text


def check_link(args, records, cert):
    p = cert["payload"]
    assert graph(records) == p["link_graph"], (
        "fresh linker inputs differ from identity build"
    )
    assert argument_identity(args, records) == p["link_arguments"], (
        "linker arguments differ from identity build"
    )


def verify_transform(cert, output):
    """Check every allocated byte plus symbols/file gaps against the identity ELF."""
    baseline = Path(cert["payload"]["baseline_build"])
    output = Path(output)
    a, b = Elf(baseline / "unstripped.so"), Elf(output / "unstripped.so")
    assert a.sections == b.sections, "output section layout changed"
    maps = [map_rows(baseline / "link/link.map"), map_rows(output / "link/link.map")]
    groups = []
    for rows in maps:
        selected = [r for r in rows if r["out"] in (".text", ".data.rel.ro")]
        group = {(r["out"], *section_key(r)): r for r in selected}
        assert len(group) == len(selected), "duplicate input-section identity"
        groups.append(group)
    assert groups[0].keys() == groups[1].keys(), "extra or missing input section"
    by_output = {}
    counts = collections.Counter()
    moved_data = []
    for name in (".text", ".data.rel.ro"):
        rows = sorted(
            (r for r in groups[0].values() if r["out"] == name),
            key=lambda r: r["address"],
        )
        for source, target in zip(maps, [a, b]):
            pos = target.sections[name]["addr"]
            for row in sorted(
                (r for r in source if r["out"] == name), key=lambda r: r["address"]
            ):
                assert row["address"] == pos
                pos += row["size"]
            assert pos == target.sections[name]["addr"] + target.sections[name]["size"]
        by_output[name] = rows
        for row in rows:
            other = groups[1][(name, *section_key(row))]
            assert (row["size"], row["align"]) == (other["size"], other["align"])
            if row["address"] != other["address"]:
                counts["moved_" + name] += 1
                if name == ".data.rel.ro":
                    moved_data.append(section_key(row))
    roles = cert["payload"]["roles"]
    assert set(moved_data) == {(r["input_owner"], r["input_section"]) for r in roles}, (
        "data permutation exceeds admitted pair"
    )

    def translate(address):
        for name, rows in by_output.items():
            s = a.sections[name]
            if s["addr"] <= address < s["addr"] + s["size"]:
                row = rows[
                    bisect.bisect_right([r["address"] for r in rows], address) - 1
                ]
                return (
                    groups[1][(name, *section_key(row))]["address"]
                    + address
                    - row["address"]
                )
        return address

    assert b.entry == translate(a.entry)
    assert a.raw[:24] == b.raw[:24] and a.raw[32:64] == b.raw[32:64]
    assert (
        a.raw[a.phoff : a.phoff + a.phcount * a.phsize]
        == b.raw[b.phoff : b.phoff + b.phcount * b.phsize]
    )
    for row in by_output[".text"]:
        other = groups[1][(".text", *section_key(row))]
        raw = a.read(row["address"], row["size"])
        expected = bytearray(raw)
        i = 0
        while i < len(raw):
            op, reg, off, imm = struct.unpack_from("<BBhi", raw, i)
            if op == 0x18:
                value = (
                    struct.unpack_from("<I", raw, i + 4)[0]
                    | struct.unpack_from("<I", raw, i + 12)[0] << 32
                )
                want = translate(value)
                struct.pack_into("<I", expected, i + 4, want & 0xFFFFFFFF)
                struct.pack_into("<I", expected, i + 12, want >> 32)
                counts["lddw_checked"] += 1
                i += 16
                continue
            if op == 0x85 and reg >> 4 == 1 and imm != -1:
                target = row["address"] + i + 8 + imm * 8
                want = (translate(target) - (other["address"] + i + 8)) // 8
                struct.pack_into("<i", expected, i + 4, want)
                counts["calls_checked"] += 1
            elif op & 7 in (5, 6) and op not in (0x85, 0x8D, 0x95):
                assert 0 <= i + 8 + off * 8 < row["size"]
                counts["branches_checked"] += 1
            i += 8
        assert bytes(expected) == b.read(other["address"], other["size"]), (
            "unaccounted instruction bytes"
        )
    rels = [
        struct.unpack_from("<QQ", a.data(".rel.dyn"), i)
        for i in range(0, len(a.data(".rel.dyn")), 16)
    ]
    sites = dict(rels)
    for row in by_output[".data.rel.ro"]:
        other = groups[1][(".data.rel.ro", *section_key(row))]
        assert row["size"] % 8 == 0
        expected = bytearray(a.read(row["address"], row["size"]))
        for i in range(0, row["size"], 8):
            if row["address"] + i in sites:
                value = struct.unpack_from("<Q", expected, i)[0]
                assert sites[row["address"] + i] == 8 and value & 0xFFFFFFFF == 0
                struct.pack_into("<Q", expected, i, translate(value >> 32) << 32)
                counts["data_pointers_checked"] += 1
            else:
                counts["data_scalars_checked"] += 1
        assert bytes(expected) == b.read(other["address"], other["size"]), (
            "unaccounted data bytes"
        )
    expected = collections.Counter((translate(at), kind) for at, kind in rels)
    actual = collections.Counter(
        struct.unpack_from("<QQ", b.data(".rel.dyn"), i)
        for i in range(0, len(b.data(".rel.dyn")), 16)
    )
    assert expected == actual, "relocation sites/values differ"
    counts["relocations_checked"] = len(rels)
    for name in (".symtab", ".dynsym"):
        raw = a.data(name)
        expected = bytearray(raw)
        for at in range(0, len(raw), 24):
            value = struct.unpack_from("<Q", raw, at + 8)[0]
            struct.pack_into("<Q", expected, at + 8, translate(value))
        assert bytes(expected) == b.data(name), "unaccounted symbol bytes"
    changed = {".text", ".data.rel.ro", ".rel.dyn", ".symtab", ".dynsym"}
    mask = bytearray(len(a.raw))
    mask[24:32] = bytes([1]) * 8
    for name, s in a.sections.items():
        if name in changed:
            mask[s["offset"] : s["offset"] + s["size"]] = bytes([1]) * s["size"]
        elif s["type"] != 8:
            assert a.data(name) == b.data(name), "other section changed: " + name
    assert len(a.raw) == len(b.raw) and all(
        x == y or mask[i] for i, (x, y) in enumerate(zip(a.raw, b.raw))
    ), "unaccounted file bytes"
    return {
        "status": "passed",
        "counts": dict(counts),
        "all_allocated_bytes_checked": True,
        "all_other_file_bytes_checked": True,
        "baseline_sha256": sha(a.path),
        "candidate_sha256": sha(b.path),
    }


def publish_file(staged, path):
    """Publish without replacement; return whether staging was consumed.

    Rename on Windows, link elsewhere.

    Windows sandboxes refuse hard links (WinError 5); a same-directory
    rename refuses an existing destination, preserving no-replace.
    """
    if os.name == "nt":
        os.rename(staged, path)
        return True
    os.link(staged, path)
    return False


def publish_certificate(path, cert):
    """Publish a complete certificate into a new path; never replace an output."""
    staged = None
    try:
        # A plain exclusive open keeps the umask mode of the published
        # certificate. The hidden staged name is unique and links into an
        # absent output only, preserving the no-replace guarantee.
        temporary = path.with_name("." + path.name[:32] + "." + secrets.token_hex(8) + ".tmp")
        with open(temporary, "x", encoding="utf-8", newline="\n") as stream:
            staged = temporary
            stream.write(json.dumps(cert, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if publish_file(staged, path):
            staged = None  # Rename consumed this name; a new owner may recreate it.
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-build", type=Path, required=True)
    parser.add_argument("--text-section-order", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a new certificate output")
    cert = {
        "schema": 1,
        "payload": derive_payload(args.baseline_build, args.text_section_order),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    publish_certificate(args.output, cert)
    print(
        json.dumps(
            {
                "certificate": str(args.output),
                "sha256": sha(args.output),
                "roles": cert["payload"]["roles"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
