#!/usr/bin/env python3
"""Finite retained-evidence verifier. No compiler, producer, VM, or network execution.
Requires Python 3 and solders (qualified runtime version 0.27.1).
Consistency and signed-wire checks are not independent execution attestation.
"""
if not __debug__:
    raise SystemExit("Run without -O")
import argparse,difflib,gzip,hashlib,importlib.util,json,stat,sys,tarfile
from pathlib import Path,PurePosixPath
sys.dont_write_bytecode=True
ORIGINAL_SHA="7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"
SOURCE_PATH="programs/pump/src/multi_hop_curve_swap.rs"
LABELS=("parent","candidate")
def require(ok,message):
    if not ok:raise AssertionError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":")).encode()
def read(path):
    raw=path.read_bytes();return gzip.decompress(raw)if path.suffix==".gz"else raw
def doc(path):return json.loads(read(path))
def relative(name):
    p=PurePosixPath(name)
    require(p.parts and not p.is_absolute()and ".."not in p.parts and "\\"not in name,"unsafe relative path")
    return p.as_posix()
def manifest(packet):
    require(not packet.is_symlink(),"packet root symlink")
    actual={}
    for p in packet.rglob("*"):
        mode=p.lstat().st_mode
        require(stat.S_ISDIR(mode)or stat.S_ISREG(mode),"non-regular packet entry")
        if p.is_file()and p.relative_to(packet).as_posix()!="MANIFEST.json":actual[p.relative_to(packet).as_posix()]=sha(p.read_bytes())
    saved=doc(packet/"MANIFEST.json")
    require(isinstance(saved,dict)and saved==actual,"MANIFEST hash/membership differs")
    for name in saved:relative(name)
    return len(actual)
def archive(path):
    files={}
    with tarfile.open(path,"r:gz")as tf:
        for member in tf:
            name=relative(member.name)
            if member.isdir():continue
            require(member.isfile()and name not in files,"archive nonregular/duplicate member")
            files[name]=tf.extractfile(member).read()
    return files

def sources(packet):
    files={label:archive(packet/("source-"+label+".tar.gz"))for label in LABELS}
    maps={label:{k:sha(v)for k,v in rows.items()}for label,rows in files.items()}
    require(len(maps["parent"])==len(maps["candidate"])==66 and maps["parent"].keys()==maps["candidate"].keys(),"66-source membership")
    require(sha(canonical(maps["parent"]))=="6303113ac18a90ad2ff3536a722b500f6ae6a0d9e165ffcc3e0a6899bacf60ed","selected current1110 control source")
    for label in LABELS:require(maps[label]==doc(packet/("source-"+label+".json")),"source map/archive join")
    require([k for k in files["parent"]if files["parent"][k]!=files["candidate"][k]]==[SOURCE_PATH],"only multi-hop source changed")
    a,b=[files[label][SOURCE_PATH].splitlines(keepends=True)for label in LABELS]
    require(len(a)==len(b)==931,"931 physical source lines")
    require([i+1 for i,(x,y)in enumerate(zip(a,b))if x!=y]==[581,582,589],"only physical source lines 581/582/589")
    expected={581:(b"require!(q != 0,PumpError::Overflow);",b""),582:(b"let effective = q - 1;",b""),589:(b"let base = u64::try_from(div(effective as u128 * c.virtual_token_reserves as u128, c.virtual_quote_reserves as u128 + effective as u128)?).map_err(|_| error!(PumpError::Truncation))?;",b"let base = u64::try_from(crate::constant_product::tokens_for_quote(c,q)?).map_err(|_| error!(PumpError::Truncation))?;")}
    for line,pair in expected.items():require((a[line-1].strip(),b[line-1].strip())==pair,"exact helper source change")
    patch="".join(difflib.unified_diff([x.decode()for x in a],[x.decode()for x in b],fromfile="a/"+SOURCE_PATH,tofile="b/"+SOURCE_PATH))
    require((packet/"source.patch").read_bytes()==patch.encode(),"exact source patch")
    d037=archive(packet/"provenance/d037-source-parent.tar.gz")
    dm={k:sha(v)for k,v in d037.items()}
    require(sha(canonical(dm))=="ffec01de903f07b258b2f62263a0785ed3cd03bf329386d5a782ec0d58b9f8aa","selected D037 66-input origin")
    require(dm==doc(packet/"provenance/d037-source-parent.json"),"D037 origin map")
    changed=sorted(k for k in dm if dm[k]!=maps["parent"][k])
    require(changed==["programs/pump/src/buy.rs","programs/pump/src/creator/admin_cto.rs",SOURCE_PATH,"programs/pump/src/sweep_fees.rs"],"four maintained control Rust changes")
    current=doc(packet/"provenance/current-input-map.json")
    current_rows={row["path"]:row for row in current["changed"]}
    for k in changed:require(current_rows[k]["main_sha256"]==maps["parent"][k],"current main control input")
    require(maps["parent"]["programs/pump/src/util/constant_product.rs"]=="3269785c24ef5a343c6b7f2095ba1541b042b9944596bad9cab1e026dbca8616","reviewed selected constant-product helper")
    return maps

def builds(packet,inputs):
    commands={"parent":"4605743bb631b076e32d08252c4fed2a8a2606ddca72a979eef8b7581f0b6a18","candidate":"0b6f3f7b3cb06a8b7486f578d967fea9c9d5927eff28e47a5ffbefce96842e29"}
    tools={"rustc":"c8807b7ebede8578ac5a257ea333780f9d89bd356064fd8184af7e996cb71a97","cargo":"d28444578306fe5a4f40524331411340123004e9e6556322fcabdbe351fe265d","objcopy":"f078d5b1f9df4190e67938a13e81e1dda1057e16228ff1a6f2f5d5540c9e6aaf"}
    images={}
    for label in LABELS:
        folder=packet/"build"/label;launch=doc(folder/"launch.json");result=doc(folder/"result.json")
        require(launch["inputs"]==inputs[label],"build source hash join")
        require(result["returncode"]==0 and result["inputs_unchanged"]is True and result["actual_root_compilations"]==1,"successful actual build record")
        require(sha(canonical(launch["command"]))==commands[label],"reviewed literal Cargo command")
        require(launch["tools"]==tools,"qualified v1.44 tool hashes")
        require(launch["controller_sha256"]==sha((packet/"controllers/local_build.py").read_bytes())=="771d9295ee6e8997546b2f0cde677213f23d9d31528a6df33293b9a284911eea","actual build controller")
        log=read(folder/"build.log.gz").decode()
        require(sum(x.strip().startswith("Running ")and "--crate-name pump_recovered "in x for x in log.splitlines())==1,"one actual root compilation")
        images[label]={kind:read(folder/(kind+".so.gz"))for kind in ["symbols","candidate"]}
        for kind,raw in images[label].items():require(sha(raw)==result[kind+"_sha256"],"build ELF hash join")
    return images

def binary(packet,repo,images):
    pins={'census.py': '804b88102b69c7bf41f7a3f751454bf9d4d1c89cc36fb7e7f52bdc89f28b9d5c', 'pump_compare_function_bytes.py': '43fa359dce1e398f820df445d534e0912ac5f181f1ea15e13a5267b53105b075', 'pump_quote_control_function_match.py': '28ad656012f8fbcd41ed1726e9345ee76f6249992bf28c91c4b9202479d3e94e'}
    for name,digest in pins.items():require(sha((packet/"tools"/name).read_bytes())==digest,"qualified census/normalizer helper")
    # Recompute whole-window membership using the retained census implementation.
    import tempfile
    require(sha((repo/"repro/reconstruction-status-2026-10-26/functions.tsv").read_bytes())=="fb2c0a47514567d65eb45c1e268dacd5291e4659bb7dceb575a767dc20bcaff8","qualified function-window inventory")
    sys.path.insert(0,str(packet/"tools"));import census
    census.ROOT=repo
    original=(repo/"evidence/original/pump/deployed.so").read_bytes()
    require(sha(original)==ORIGINAL_SHA,"original ELF identity")
    os_=census.sections(original);on,_=census.normalize(census.body(original,os_,0x5b3b0,18584),0x5b3b0,os_)
    counts={"total":1035,"normalized":1019,"raw":183,"unmatched":16,"matched_text_bytes":1611088}
    memberships=[];report={}
    with tempfile.TemporaryDirectory(prefix="pump-multihop-verify-")as tmp:
        for label,size,expected in [("parent",18056,3423),("candidate",17704,3372)]:
            blob=images[label]["symbols"];path=Path(tmp)/(label+".so");path.write_bytes(blob);sections=census.sections(blob)
            matches=[f for f in census.functions(blob)if f[2]=="_ZN14pump_recovered15multi_hop_curve8swap_hop17ha6abe54e52afef15E"]
            require(len(matches)==1 and matches[0][1]==size,"unique target size")
            addr,_,_=matches[0];norm,_=census.normalize(census.body(blob,sections,addr,size),addr,sections)
            slots=lambda b:[b[i:i+8]for i in range(0,len(b),8)]
            aligned=sum(max(j-i,l-k)for op,i,j,k,l in difflib.SequenceMatcher(None,slots(on),slots(norm),autojunk=False).get_opcodes()if op!="equal")
            require(aligned==expected and norm!=on,"partial alignment diagnostic")
            full=census.census(path);require(full==doc(packet/"build"/label/"census.json.gz")and full["counts"]==counts,"recomputed full census")
            membership={w["start"]:(bool(w["normalized_matches"]),w["raw_match"])for w in full["windows"]};require(membership[0x5b3b0]==(False,False),"target remains unmatched");memberships.append(membership)
            stripped=images[label]["candidate"];ss=census.sections(stripped)
            for name in [".text",".rodata",".data.rel.ro"]:
                a,b=sections[name],ss[name];require(a["addr"]==b["addr"]and blob[a["offset"]:a["offset"]+a["size"]]==stripped[b["offset"]:b["offset"]+b["size"]],"strip section identity")
            report[label]={"bytes":size,"aligned_differing_8byte_slots":aligned}
    require(memberships[0]==memberships[1],"no whole-window gain or loss")
    return dict(original_bytes=18584,counts=counts,whole_target_equal=False,**report)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--repo-root",type=Path,required=True);args=parser.parse_args()
    packet=Path(__file__).resolve().parent;repo=args.repo_root.resolve();files=manifest(packet);inputs=sources(packet);images=builds(packet,inputs)
    require((repo/SOURCE_PATH).read_bytes()==archive(packet/"source-candidate.tar.gz")[SOURCE_PATH],"maintained repository source equals compiled candidate")
    spec=importlib.util.spec_from_file_location("multihop_correspondence",packet/"correspondence.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    runtime=module.verify(packet,repo,images,read,doc)
    binary_report=binary(packet,repo,images)
    print(json.dumps(dict(verified=True,scope="Retained consistency and signatures, not execution attestation; no compiler or VM replay.",manifest_files=files,source_files=66,changed_source_lines=[581,582,589],build_records=2,repeat_build_claim=False,binary=binary_report,runtime=runtime),indent=2))
if __name__=="__main__":main()
