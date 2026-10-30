"""A failed attribution publish must leave no partial packet behind.

The generator refuses an existing output directory, so writing its
packet directly into the destination was doubly bad: a write failure
(for example a file-size limit) left a truncated details file with no
manifest, and a retry at the same destination then failed with
"output already exists". The generator now stages beside the
destination and publishes by rename; failures remove only the private
stage.
"""

import hashlib
import importlib.util
import inspect
import shutil
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    import resource
except ImportError:  # pragma: no cover - non-POSIX hosts
    resource = None

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "reconstruction/diagnostics/roadmap-stable-attribution/generate.py"


def limit_file_size():
    resource.setrlimit(resource.RLIMIT_FSIZE, (64, 64))


class StableAttributionPublicationTests(unittest.TestCase):
    def run_generator(self, output, limit=False):
        kwargs = {}
        if limit:
            kwargs["preexec_fn"] = limit_file_size
        return subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(GENERATOR),
             "--repo", str(ROOT), "--output", str(output)],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
            timeout=900, **kwargs)

    def check_complete(self, output):
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("manifest.json", manifest)
        self.assertIn("attribution-inputs.json", manifest)
        self.assertIn("pump-details.json", manifest)
        for name, digest in manifest.items():
            self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)

    def staging_leftovers(self, parent, output):
        return [p.name for p in parent.iterdir()
                if p.name.startswith("." + output.name + ".staging-")]

    def test_successful_run_publishes_complete_directory(self):
        with tempfile.TemporaryDirectory(prefix="pump-stable-attribution-publication-") as temporary:
            parent = Path(temporary).resolve()
            output = parent / "attributed"
            completed = self.run_generator(output)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.check_complete(output)
            self.assertEqual(self.staging_leftovers(parent, output), [])

    @unittest.skipUnless(resource is not None and hasattr(resource, "RLIMIT_FSIZE")
                         and os.name != "nt", "file-size limits are POSIX-only")
    def test_write_failure_leaves_no_output_and_allows_retry(self):
        with tempfile.TemporaryDirectory(prefix="pump-stable-attribution-publication-") as temporary:
            parent = Path(temporary).resolve()
            output = parent / "attributed"
            failed = self.run_generator(output, limit=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(self.staging_leftovers(parent, output), [])
            retried = self.run_generator(output)
            self.assertEqual(retried.returncode, 0, retried.stdout + retried.stderr)
            self.check_complete(output)

    def load_generator(self):
        spec=importlib.util.spec_from_file_location('attribution_generator_test',GENERATOR)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def layout(self, root):
        for relative in ['scripts/reconstruction_roadmap.py','scripts/window_elf_reader.py',
                         *['evidence/original/'+name+'/deployed.so' for name in ['pump','pump_amm','mayhem']]]:
            target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,target)

    def test_late_empty_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();output=root/'late';generator=self.load_generator()
            lines,first=inspect.getsourcelines(generator.generate)
            line=next(first+i for i,text in enumerate(lines) if 'rename' in text and 'stage' in text and 'output' in text)
            seen=[]
            def trace(frame,event,arg):
                if frame.f_code is generator.generate.__code__ and event=='line' and frame.f_lineno==line:
                    sys.settrace(None);output.mkdir();seen.append(True)
                return trace
            sys.settrace(trace)
            try:
                with self.assertRaises(FileExistsError):generator.generate(ROOT,output)
            finally:sys.settrace(None)
            self.assertEqual(seen,[True]);self.assertEqual(list(output.iterdir()),[])
            self.assertEqual(self.staging_leftovers(root,output),[])

    def test_dangling_output_link_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();output=root/'link';target=root/'target'
            output.symlink_to(target,target_is_directory=True)
            result=self.run_generator(output)
            self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue(output.is_symlink());self.assertFalse(target.exists())

    def test_changed_capture_is_not_relabelled_in_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();self.layout(root);output=root/'rejected'
            generator=self.load_generator();changed=[]
            def trace(frame,event,arg):
                if event=='return' and frame.f_code.co_name=='generate_roadmap' and frame.f_code.co_filename==str(root/'scripts/reconstruction_roadmap.py'):
                    sys.setprofile(None);path=root/'evidence/original/pump/deployed.so';path.write_bytes(path.read_bytes()+b'changed');changed.append(True)
            sys.setprofile(trace)
            try:
                with self.assertRaisesRegex(ValueError,'input changed'):generator.generate(root,output)
            finally:sys.setprofile(None)
            self.assertEqual(changed,[True]);self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
