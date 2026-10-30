"""Resealed finite negative controls; no compiler, producer or VM execution."""
if not __debug__:
    raise SystemExit("Run without -O")
import argparse,base64,copy,gzip,hashlib,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.dont_write_bytecode=True

def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(path):
    raw=path.read_bytes();return json.loads(gzip.decompress(raw)if path.suffix==".gz"else raw)
def save(path,value):
    raw=(json.dumps(value,indent=2)+"\n").encode();path.write_bytes(gzip.compress(raw,mtime=0)if path.suffix==".gz"else raw)
def seal(packet):save(packet/"MANIFEST.json",{p.relative_to(packet).as_posix():sha(p.read_bytes())for p in packet.rglob("*")if p.is_file()and p.relative_to(packet).as_posix()!="MANIFEST.json"})
def repin(packet):
    for family in ["standard","upstream-gate"]:
        file=packet/"runtime"/family/"execution.json";value=load(file)
        for name in value["output_files"]:
            raw=(file.parent/name).read_bytes();value["output_files"][name]=dict(sha256=sha(raw),bytes=len(raw))
        save(file,value)
    seal(packet)
def run(packet,repo=None):return subprocess.run([sys.executable,"-I","-B",str(packet/"verify.py"),"--repo-root",str(ROOT if repo is None else repo)],capture_output=True,text=True)
def report(packet,mutate):
    path=packet/"runtime/standard/arithmetic-two.json.gz";v=load(path);mutate(v);save(path,v)
def duplicate(packet):report(packet,lambda v:v["cases"].__setitem__(1,copy.deepcopy(v["cases"][0])))
def signed_wrong_amount(packet):
    def change(v):
        for label in ["original","parent","proposal"]:
            old,new=v["cases"][1],v["cases"][0];wire=old["runs"][label]["transaction_base64"]
            new["runs"][label]["transaction_base64"]=new["observations"][label]["transaction_base64"]=wire
            new["runs"][label]["transaction_sha256"]=sha(base64.b64decode(wire))
            new["observations"][label]["metadata"]["signature"]=old["observations"][label]["metadata"]["signature"]
    report(packet,change)
def invalid_signature(packet):
    def change(v):
        for label in ["original","parent","proposal"]:
            row=v["cases"][0];wire=bytearray(base64.b64decode(row["runs"][label]["transaction_base64"]));wire[1]^=1
            row["runs"][label]["transaction_base64"]=row["observations"][label]["transaction_base64"]=base64.b64encode(wire).decode()
    report(packet,change)
def prestate(packet):
    def change(v):
        for label in ["original","parent","proposal"]:
            row=v["cases"][0];key=next(k for k,s in row["runs"][label]["before"].items()if s is not None and s["data_hex"])
            row["runs"][label]["before"][key]["lamports"]+=1
            next(s for s in row["observations"][label]["before"]if s["key"]==key)["lamports"]+=1
    report(packet,change)
def loader(packet):
    def change(v):
        for label in ["original","parent","proposal"]:v["cases"][0]["observations"][label]["loads"][0]["zero_allocation_tail"]=False
    report(packet,change)
def loaded_program(packet):
    def change(v):
        for label in ["original","parent","proposal"]:
            row=v["cases"][0];row["observations"][label]["program_loads"][0]["sha256"]="0"*64;pid=row["observations"][label]["program_loads"][0]["program"];row["runs"][label]["program_sha256"][pid]="0"*64
    report(packet,change)
def metadata(packet):
    report(packet,lambda v:v["cases"][0]["observations"]["proposal"]["metadata"]["logs"].append("invented raw log"))
def build_command(packet):
    p=packet/"build/candidate/launch.json";v=load(p);v["command"].append("--unreviewed");save(p,v)
def build_tools(packet):
    for label in ["candidate"]:
        p=packet/"build"/label/"launch.json";v=load(p);v["tools"]["rustc"]="0"*64;save(p,v)
def receipt(packet,mutate):
    p=packet/"runtime/standard/execution.json";v=load(p);mutate(v);save(p,v)
def result_name(packet):receipt(packet,lambda v:v["results"][0].__setitem__("name","wrong"))
def missing_result(packet):receipt(packet,lambda v:v["results"].pop())
def missing_output(packet):receipt(packet,lambda v:v["output_files"].pop("arithmetic.stderr.log"))
def extra_output(packet):
    (packet/"runtime/standard/extra.log").write_bytes(b"extra")
    receipt(packet,lambda v:v["output_files"].__setitem__("extra.log",{}))
def stream(packet):
    p=packet/"runtime/standard/arithmetic.stdout.log";p.write_bytes(p.read_bytes()+b"changed stream\n")
def source_map(packet):
    p=packet/"source-parent.json";v=load(p);v["programs/pump/src/buy.rs"]="0"*64;save(p,v)
def census_helper(packet):
    p=packet/"tools/pump_compare_function_bytes.py";p.write_bytes(p.read_bytes()+b"\n# unreviewed helper\n")
CONTROLS=[("duplicate case",duplicate,"exact source-owned arithmetic definitions"),("valid signed wrong amount",signed_wrong_amount,"fixture signed operation/amount/limit"),("invalid signature",invalid_signature,"verified canonical signed wire"),("coherent wrong prestate",prestate,"source-owned complete prestate"),("allocation tail drift",loader,"captured loader actual image/allocation/zero-tail join"),("coherent loaded program drift",loaded_program,"all actual loaded program hashes"),("raw metadata drift",metadata,"raw metadata/result join"),("literal Cargo command",build_command,"reviewed literal Cargo command"),("coherent tool fingerprints",build_tools,"qualified v1.44 tool hashes"),("runtime result name",result_name,"exact runtime result names/success"),("runtime missing result",missing_result,"exact runtime result names/success"),("runtime missing output",missing_output,"exact runtime output membership"),("runtime extra output",extra_output,"exact runtime output membership"),("resealed stream",stream,"runtime result stream receipt join"),("source map drift",source_map,"published parent member identity"),("normalizer drift",census_helper,"qualified census/normalizer helper")]

class EvidenceTests(unittest.TestCase):
    def test_optimized_guards(self):
        for name in ["verify.py","correspondence.py","test_verify.py","audit_refs.py"]:
            with self.subTest(entrypoint=name):
                result=subprocess.run([sys.executable,"-I","-B","-O",str(HERE/name),"--repo-root","/nonexistent"],capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0);self.assertIn("Run without -O",result.stdout+result.stderr);self.assertNotIn("Traceback",result.stderr)
    def test_resealed_correspondence_controls(self):
        for name,mutate,reason in CONTROLS:
            with self.subTest(control=name),tempfile.TemporaryDirectory()as tmp:
                packet=Path(tmp)/"packet";shutil.copytree(HERE,packet);mutate(packet);repin(packet);result=run(packet)
                self.assertNotEqual(result.returncode,0);self.assertIn(reason,result.stderr)
    def test_wrong_output_hash(self):
        with tempfile.TemporaryDirectory()as tmp:
            packet=Path(tmp)/"packet";shutil.copytree(HERE,packet);receipt(packet,lambda v:v["output_files"]["arithmetic.stdout.log"].__setitem__("sha256","0"*64));seal(packet);result=run(packet)
            self.assertNotEqual(result.returncode,0);self.assertIn("actual runtime output receipt join",result.stderr)
    def test_repository_source_binding(self):
        with tempfile.TemporaryDirectory()as tmp:
            repo=Path(tmp);p=repo/"programs/pump/src/multi_hop_curve_swap.rs";p.parent.mkdir(parents=True);p.write_bytes(b"wrong maintained source")
            result=run(HERE,repo);self.assertNotEqual(result.returncode,0);self.assertIn("maintained repository sources equal compiled candidate",result.stderr)
    def test_repository_fixture_binding(self):
        # Read-only links to dependencies; mutation stays in this isolated temp dir.
        with tempfile.TemporaryDirectory()as tmp:
            repo=Path(tmp);(repo/"evidence").symlink_to(ROOT/"evidence",target_is_directory=True)
            for name in ["multi_hop_curve_swap.rs","trade_v3.rs"]:
                p=repo/"programs/pump/src"/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/p.relative_to(repo)).read_bytes())
            prior="research/pump-multihop-token-quote-20261029";shutil.copytree(ROOT/prior,repo/prior)
            p=repo/"research/pump-multi-hop-quote-admission/runtime/inputs/base-fixture.json";p.parent.mkdir(parents=True);p.write_bytes((ROOT/p.relative_to(repo)).read_bytes()+b"\n")
            result=run(HERE,repo);self.assertNotEqual(result.returncode,0);self.assertIn("repository fixture agrees",result.stderr)
    def test_resealed_frozen_parent_manifest(self):
        with tempfile.TemporaryDirectory()as tmp:
            repo=Path(tmp)
            for name in ["multi_hop_curve_swap.rs","trade_v3.rs"]:
                p=repo/"programs/pump/src"/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/p.relative_to(repo)).read_bytes())
            prior="research/pump-multihop-token-quote-20261029";shutil.copytree(ROOT/prior,repo/prior)
            p=repo/prior/"source-candidate.json";p.write_bytes(p.read_bytes()+b"\n");seal(repo/prior)
            result=run(HERE,repo);self.assertNotEqual(result.returncode,0);self.assertIn("frozen published parent manifest",result.stderr)
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--repo-root",type=Path,default=ROOT);args,remaining=parser.parse_known_args();ROOT=args.repo_root.resolve();unittest.main(argv=[sys.argv[0],*remaining])
