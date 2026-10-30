#!/usr/bin/env python3
"""Positive check plus negative controls / mutations for verify.py. Stdlib unittest; valid under python -O.
Each mutation is applied to a temporary copy of only the files the verifier reads."""
import hashlib,json,shutil,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parents[1]
sys.path.insert(0,str(HERE)); import verify
READS=["programs/pump-fees/build_exact.py","reconstruction/harness/make_hybrid144.sh","scripts/core_linux_v144_inputs.json",
       "evidence/original/pump_fees/deployed.so","reconstruction/pump-main/checkpoints/completion-20261030/other-programs.json"]
def resum(pk):
    lines=[l.split(None,1) for l in (pk/"SHA256SUMS").read_text().splitlines()]
    (pk/"SHA256SUMS").write_text("".join("%s  %s\n"%(hashlib.sha256((pk/n.lstrip("*")).read_bytes()).hexdigest(),n.lstrip("*")) for _,n in lines))
class T(unittest.TestCase):
    def setUp(self):
        self.t=Path(tempfile.mkdtemp(prefix="fees rebuild "))
        self.repo=self.t/"repo"; self.pk=self.repo/"research/pk"
        for r in READS: (self.repo/r).parent.mkdir(parents=True,exist_ok=True); shutil.copy2(REPO/r,self.repo/r)
        shutil.copytree(REPO/"programs/pump-fees",self.repo/"programs/pump-fees",dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__","target"))
        shutil.copytree(HERE,self.pk,ignore=shutil.ignore_patterns("__pycache__"))
    def tearDown(self): shutil.rmtree(self.t)
    def run_ok(self,**kw): return verify.check(self.repo,self.pk,**kw)
    def bad(self,msg,**kw):
        with self.assertRaises(verify.Fail) as c: self.run_ok(**kw)
        self.assertIn(msg,str(c.exception))
    def edit_result(self,f):
        r=json.loads((self.pk/"RESULT.json").read_text()); f(r); (self.pk/"RESULT.json").write_text(json.dumps(r,indent=2)+"\n"); resum(self.pk)
    def flip(self,path,off):
        b=bytearray(path.read_bytes()); b[off]^=1; path.write_bytes(bytes(b))
    def test_positive(self): self.assertTrue(self.run_ok().startswith("OK"))
    def test_positive_real_repo(self): self.assertTrue(verify.check(REPO,HERE).startswith("OK"))
    def test_unsummed_result_edit(self):
        r=self.pk/"RESULT.json"; r.write_text(r.read_text().replace('"returncode": 0','"returncode": 1',1)); self.bad("SHA256SUMS mismatch")
    def test_run_candidate_hash_mutated(self): self.edit_result(lambda r:r["runs"][1].__setitem__("candidate_sha256","0"*64)); self.bad("run2: candidate hash")
    def test_run_not_cold(self): self.edit_result(lambda r:r["runs"][0].__setitem__("target_initially_empty",False)); self.bad("not a cold build")
    def test_single_run(self): self.edit_result(lambda r:r["runs"].pop()); self.bad("two independent runs")
    def test_runs_inputs_differ(self): self.edit_result(lambda r:r["runs"][1]["inventory_digests"].__setitem__("registry_inputs","1"*64)); self.bad("inputs differ")
    def test_pinned_value_mutated(self): self.edit_result(lambda r:r["pinned"].__setitem__("candidate_sha256","f"*64)); self.bad("candidate pin differs")
    def test_builder_pin_mutated(self):
        b=self.repo/"programs/pump-fees/build_exact.py"; b.write_text(b.read_text().replace("5b6ceda5","5b6ceda6",1)); self.bad("candidate pin differs")
    def test_builder_script_changed(self):
        b=self.repo/"programs/pump-fees/build_exact.py"; b.write_text(b.read_text()+"\n# x\n"); self.bad("builder script differs")
    def test_capture_prefix_byte_flipped(self):
        c=self.repo/"evidence/original/pump_fees/deployed.so"; self.flip(c,1000)
        self.edit_result(lambda r:r["capture"].__setitem__("sha256",hashlib.sha256(c.read_bytes()).hexdigest())); self.bad("prefix != pinned")
    def test_capture_suffix_nonzero(self):
        c=self.repo/"evidence/original/pump_fees/deployed.so"; self.flip(c,900000)
        self.edit_result(lambda r:r["capture"].__setitem__("sha256",hashlib.sha256(c.read_bytes()).hexdigest())); self.bad("not all zero")
    def test_objcopy_pin_mismatch(self): self.edit_result(lambda r:r["tools"].__setitem__("objcopy_sha256","a"*64)); self.bad("objcopy pin")
    def test_shim_tampered(self):
        s=self.pk/"podman-bwrap-shim.py"; s.write_text(s.read_text()+"#\n"); resum(self.pk); self.bad("shim hash")
    def test_checkpoint_record_changed(self):
        o=self.repo/"reconstruction/pump-main/checkpoints/completion-20261030/other-programs.json"
        o.write_text(o.read_text().replace('"meaningful_elf_bytes": 873256','"meaningful_elf_bytes": 873257')); self.bad("checkpoint record")
    def test_supplied_candidate_mutated(self):
        f=self.t/"cand.so"; d=(self.repo/"evidence/original/pump_fees/deployed.so").read_bytes()[:873256]; f.write_bytes(d)
        self.assertTrue(self.run_ok(candidate=str(f)).startswith("OK"))
        self.flip(f,4096); self.bad("candidate_sha256",candidate=str(f))
    def test_current_source_changed(self):
        source=self.repo/"programs/pump-fees/src/buyback.rs"
        source.write_text(source.read_text()+"\n// mutated canonical source\n")
        self.bad("canonical source validation failed")
    def test_matching_run_digests_do_not_replace_current_source(self):
        self.edit_result(lambda r:[run["inventory_digests"].__setitem__("source_inputs","0"*64) for run in r["runs"]])
        self.bad("source_inputs differs from current canonical source")
    def test_matching_macro_digests_do_not_replace_current_macros(self):
        self.edit_result(lambda r:[run["inventory_digests"].__setitem__("macro_inputs","0"*64) for run in r["runs"]])
        self.bad("macro_inputs differs from current canonical source")
if __name__=="__main__": unittest.main()
