#!/usr/bin/env python3
"""Offline verifier for the Fees fresh Linux rebuild packet. Stdlib only; works under python -O.

Checks the packet against the repository's own pins (builder constants, toolchain pins,
the captured program and the checkpoint record). Optionally checks rebuilt files."""
import argparse,hashlib,importlib.util,json,re,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Fail(Exception): pass
def need(c,m):
    if not c: raise Fail(m)
def sha(b): return hashlib.sha256(b).hexdigest()
def current_inputs(repo,builder):
    spec=importlib.util.spec_from_file_location("fees_packet_builder",repo/builder)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    try:
        with tempfile.TemporaryDirectory(prefix="fees-packet-verify-") as directory:
            workspace,mapping,expected=module.stage(Path(directory))
            values={"source_inputs":module.inventory(workspace),"qualified_source_inputs":expected,
                    "input_mapping":mapping,"macro_inputs":module.inventory(module.HERE/"vendor/used-public")}
            return {key:sha(json.dumps(value,sort_keys=True,separators=(",",":")).encode()) for key,value in values.items()}
    except ValueError as error:
        raise Fail("canonical source validation failed: "+str(error)) from error
def check(repo,packet,candidate=None,symbols=None):
    res=json.loads((packet/"RESULT.json").read_text())
    for line in (packet/"SHA256SUMS").read_text().splitlines():
        h,name=line.split(None,1); name=name.lstrip("*")
        need(sha((packet/name).read_bytes())==h,"SHA256SUMS mismatch: "+name)
    names={l.split(None,1)[1].lstrip("*") for l in (packet/"SHA256SUMS").read_text().splitlines()}
    need({"RESULT.json","verify.py","podman-bwrap-shim.py","summarize.py","README.md"}<=names,"SHA256SUMS incomplete")
    src=(repo/res["builder"]).read_text()
    pin=lambda k: re.search(k+r' = "([0-9a-f]{64})"',src).group(1)
    need(pin("EXPECTED_SYMBOLS")==res["pinned"]["symbols_sha256"],"builder symbols pin differs from packet")
    need(pin("EXPECTED_CANDIDATE")==res["pinned"]["candidate_sha256"],"builder candidate pin differs from packet")
    tools=dict(re.findall(r'"(rust/[^"]+)": "([0-9a-f]{64})"',src.split("TOOLS = {",1)[1].split("}",1)[0]))
    need(len(tools)==3,"builder TOOLS parse")
    need(res["tools"]["sdk_archive_sha256"] in (repo/"reconstruction/harness/make_hybrid144.sh").read_text(),"SDK archive not the repo-pinned v1.44")
    pt=json.loads((repo/"scripts/core_linux_v144_inputs.json").read_text())["pipeline_tools"]
    need(pt["strip_sha256"]==res["tools"]["strip_archive_sha256"],"strip archive pin")
    need(pt["strip_selected_sha256"]["llvm/bin/llvm-objcopy"]==res["tools"]["objcopy_sha256"],"objcopy pin")
    need(sha((packet/"podman-bwrap-shim.py").read_bytes())==res["shim_sha256"],"shim hash")
    cap=res["capture"]; d=(repo/cap["path"]).read_bytes()
    need(len(d)==cap["bytes"] and sha(d)==cap["sha256"],"capture bytes/hash")
    n=cap["meaningful_prefix_bytes"]
    need(n+cap["zero_suffix_bytes"]==len(d) and not any(d[n:]),"capture suffix is not all zero")
    need(sha(d[:n])==res["pinned"]["candidate_sha256"],"capture meaningful prefix != pinned candidate")
    op=json.loads((repo/"reconstruction/pump-main/checkpoints/completion-20261030/other-programs.json").read_text())
    rec=[v for v in op["programs"].values() if isinstance(v,dict) and v.get("builder")==res["builder"]]
    need(len(rec)==1,"checkpoint has no single record for the builder")
    need(rec[0]["meaningful_elf_sha256"]==res["pinned"]["candidate_sha256"] and rec[0]["meaningful_elf_bytes"]==n,"checkpoint record differs from pin")
    current=current_inputs(repo,res["builder"])
    runs=res["runs"]; need(len(runs)>=2,"need two independent runs")
    for r in runs:
        tag=r["run"]+": "
        need(r["returncode"]==0 and r["clean_returncode"]==0,tag+"build failed")
        need(r["target_initially_empty"] is True,tag+"target not empty (not a cold build)")
        need(r["original_executable_is_build_input"] is False,tag+"capture used as input")
        for k in ("source_unchanged","macro_unchanged","sdk_libraries_unchanged","registry_unchanged","exact_symbols_equal","exact_candidate_equal"):
            need(r[k] is True,tag+k)
        need(r["symbols_sha256"]==res["pinned"]["symbols_sha256"],tag+"symbols hash")
        need(r["candidate_sha256"]==res["pinned"]["candidate_sha256"],tag+"candidate hash")
        need(r["candidate_bytes"]==n,tag+"candidate size != meaningful prefix")
        need(r["stack_diagnostics"]==[],tag+"stack diagnostics")
        need(set(r["fresh_local_crate_compilations"].values())=={1},tag+"local crates not freshly compiled once")
        need(r["sdk_tools"]==tools,tag+"SDK tool hashes differ from builder TOOLS")
        need(r["objcopy_sha256"]==res["tools"]["objcopy_sha256"],tag+"objcopy")
        need(r["controller_script_sha256"]==sha((repo/res["builder"]).read_bytes()),tag+"builder script differs from repo")
        need(r["environment"].get("CARGO_NET_OFFLINE")=="true",tag+"not offline")
        need(r["inventory_digests"]==runs[0]["inventory_digests"],tag+"inputs differ between runs")
        for key,digest in current.items():
            need(r["inventory_digests"].get(key)==digest,tag+key+" differs from current canonical source")
    for f,k in ((candidate,"candidate_sha256"),(symbols,"symbols_sha256")):
        if f is not None: need(sha(Path(f).read_bytes())==res["pinned"][k],"supplied %s does not match pin"%k)
    return "OK: 2 cold Linux builds == pinned symbols %s / candidate %s; capture prefix (%d B) equal, %d B zero suffix"%(
        res["pinned"]["symbols_sha256"][:12],res["pinned"]["candidate_sha256"][:12],n,cap["zero_suffix_bytes"])
def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--repo",type=Path,default=HERE.parents[1]); a.add_argument("--packet",type=Path,default=HERE)
    a.add_argument("--candidate"); a.add_argument("--symbols")
    x=a.parse_args()
    try: print(check(x.repo.resolve(),x.packet.resolve(),x.candidate,x.symbols))
    except (Fail,KeyError,ValueError,OSError,AttributeError) as e: print("FAIL:",e,file=sys.stderr); sys.exit(1)
if __name__=="__main__": main()
