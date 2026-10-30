"""Compact the two full builder receipts (~890 KB each) into RESULT.json. Run once by the producer."""
import hashlib,json,sys
from pathlib import Path
def cj(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
F=Path(sys.argv[1]); out={}
KEEP=("returncode","seconds","source_unchanged","macro_unchanged","sdk_libraries_unchanged","registry_unchanged","target_initially_empty",
      "original_executable_is_build_input","clean_returncode","symbols_sha256","candidate_sha256","exact_symbols_equal","exact_candidate_equal",
      "candidate_bytes","stack_diagnostics","fresh_local_crate_compilations","controller_script_sha256","sdk_tools","objcopy_sha256","environment")
runs=[]
for name in sys.argv[2:]:
    r=json.loads((F/name/"result.json").read_text())
    d={k:r[k] for k in KEEP}
    d["run"]=name
    d["inventory_digests"]={k:cj(r[k]) for k in ("source_inputs","qualified_source_inputs","target_libraries","macro_inputs","registry_inputs","input_mapping")}
    d["registry_packages"]=len(r["registry_inputs"]); d["source_input_files"]=len(r["source_inputs"])
    d["build_log_compiling_lines"]=sum(l.lstrip().startswith("Compiling ") for l in (F/name/"build.log").read_text().splitlines())
    d["result_json_sha256"]=hashlib.sha256((F/name/"result.json").read_bytes()).hexdigest()
    runs.append(d)
print(json.dumps({"schema":1,"runs":runs},indent=2))
