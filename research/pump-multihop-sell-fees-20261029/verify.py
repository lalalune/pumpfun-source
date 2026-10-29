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
SOURCE_PATHS=(SOURCE_PATH,"programs/pump/src/trade_v3.rs")
PRIOR_PACKET="research/pump-multihop-token-quote-20261029"
PRIOR_MANIFEST="54639f0c28720c6231e70dd330998f5c001caafa8e65dfcc559b5fba3b38e603"
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

def sources(packet,repo):
    prior=repo/PRIOR_PACKET
    require(sha((prior/"MANIFEST.json").read_bytes())==PRIOR_MANIFEST,"frozen published parent manifest")
    require(manifest(prior)==68,"all 68 frozen parent members")
    expected={"source-parent.json":"source-candidate.json","source-parent.tar.gz":"source-candidate.tar.gz",**{"build/parent/"+n:"build/candidate/"+n for n in ["symbols.so.gz","candidate.so.gz","build.log.gz","launch.json","result.json","census.json.gz"]}}
    lineage=doc(packet/"provenance/parent-lineage.json")
    require(lineage["prior_pr"]==1164 and lineage["prior_head"]=="9d7b5652ce8b20692bea817a9f0660b6a126cf36"and lineage["prior_packet"]==PRIOR_PACKET and lineage["prior_manifest_sha256"]==PRIOR_MANIFEST,"published parent lineage declaration")
    require(set(lineage["byte_equal_parent_members"])==set(expected),"eight parent lineage members")
    for current,old in expected.items():
        raw=(packet/current).read_bytes();require(raw==(prior/old).read_bytes(),"published parent member identity")
        require(lineage["byte_equal_parent_members"][current]==dict(prior_member=old,sha256=sha(raw)),"parent member lineage receipt")
    files={label:archive(packet/("source-"+label+".tar.gz"))for label in LABELS}
    maps={label:{k:sha(v)for k,v in rows.items()}for label,rows in files.items()}
    require(len(maps["parent"])==len(maps["candidate"])==66 and maps["parent"].keys()==maps["candidate"].keys(),"66-source membership")
    require(sha(canonical(maps["parent"]))=="d7ba04fe95d627509dffd5fc35d18143cdbd31780220c9987d78f2c541878fb3","published1164 compiled source parent")
    for label in LABELS:require(maps[label]==doc(packet/("source-"+label+".json")),"source map/archive join")
    require(sorted(k for k in files["parent"]if files["parent"][k]!=files["candidate"][k])==list(SOURCE_PATHS),"only two reviewed source files changed")
    patch=""
    for name,line,total,old,new in [(SOURCE_PATH,679,931,b"let net = sub(sub(gross_sell,pf)?,cf)?;",b"let net = crate::trade::sub3(gross_sell,pf,cf)?;"),(SOURCE_PATHS[1],294,1295,b"fn sub3(a:u64,b:u64,c:u64)->Result<u64>{a.checked_sub(b).and_then(|x|x.checked_sub(c)).ok_or_else(||error!(PumpError::Overflow))}",b"pub(crate) fn sub3(a:u64,b:u64,c:u64)->Result<u64>{a.checked_sub(b).and_then(|x|x.checked_sub(c)).ok_or_else(||error!(PumpError::Overflow))}")]:
        a,b=[files[label][name].splitlines(keepends=True)for label in LABELS]
        require(len(a)==len(b)==total,"preserved physical source line counts")
        require([i+1 for i,(x,y)in enumerate(zip(a,b))if x!=y]==[line],"one reviewed physical line per source")
        require((a[line-1].strip(),b[line-1].strip())==(old,new),"exact sub3 source change")
        patch+="".join(difflib.unified_diff([x.decode()for x in a],[x.decode()for x in b],fromfile="a/"+name,tofile="b/"+name))
    require((packet/"source.patch").read_bytes()==patch.encode(),"exact source patch")
    return maps

def builds(packet,inputs):
    commands={"parent":"0b6f3f7b3cb06a8b7486f578d967fea9c9d5927eff28e47a5ffbefce96842e29","candidate":"0b071b9760df92fce2ca3e03cbdb3752b2dfae5090ff02ed82977143c0281fd2"}
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
        for label,size,expected in [("parent",17704,3372),("candidate",17608,3336)]:
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
    packet=Path(__file__).resolve().parent;repo=args.repo_root.resolve();files=manifest(packet)
    candidate_sources=archive(packet/"source-candidate.tar.gz")
    require(all((repo/name).read_bytes()==candidate_sources[name]for name in SOURCE_PATHS),"maintained repository sources equal compiled candidate")
    inputs=sources(packet,repo);images=builds(packet,inputs)
    spec=importlib.util.spec_from_file_location("multihop_correspondence",packet/"correspondence.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    runtime=module.verify(packet,repo,images,read,doc)
    binary_report=binary(packet,repo,images)
    print(json.dumps(dict(verified=True,scope="Retained consistency and signatures, not execution attestation; no compiler or VM replay.",manifest_files=files,source_files=66,changed_source_lines={SOURCE_PATH:[679],SOURCE_PATHS[1]:[294]},build_records=2,new_normal_compilations=1,reused_published_parent_compilations=1,repeat_build_claim=False,binary=binary_report,runtime=runtime),indent=2))
if __name__=="__main__":main()
