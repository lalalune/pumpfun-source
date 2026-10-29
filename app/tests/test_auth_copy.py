import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("auth_copy", ROOT / "scripts/extract-auth-copy.py")
AUTH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUTH)


def synthetic_html(resources=None, locale="en", duplicate=False):
    # Synthetic labels test parsing only. They are never used by the product UI.
    if resources is None:
        resources = {}
        for key in AUTH.KEYS:
            cursor = resources
            parts = key.split(".")
            for part in parts[:-1]:
                cursor = cursor.setdefault(part, {})
            cursor[parts[-1]] = f"synthetic {key}"
    row = "c6:" + json.dumps({"locale": locale, "resources": resources}) + "\n"
    if duplicate:
        row += row
    return '<script>self.__next_f.push(' + json.dumps([1, row]) + ')</script>'


class AuthCopyTests(unittest.TestCase):
    def test_real_capture_cli_uses_utf8_manifest_and_lf_output(self):
        # The selected capture remains byte-identical; an unrelated manifest note
        # must not make admitted JSON depend on the host's default text codec.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evidence/web/objects").mkdir(parents=True)
            manifest = json.loads((ROOT / "evidence/web/manifest.json").read_text(encoding="utf-8"))
            manifest["note"] = "\u6355\u83b7 \u20ac"
            (root / "evidence/web/manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            (root / AUTH.SOURCE["path"]).write_bytes((ROOT / AUTH.SOURCE["path"]).read_bytes())
            destination = root / AUTH.OUTPUT
            destination.parent.mkdir(parents=True)
            env = {**os.environ, "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "LC_ALL": "C"}
            command = [sys.executable, "-X", "utf8=0", str(ROOT / "scripts/extract-auth-copy.py"), "--root", str(root)]
            generated = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(generated.returncode, 0, generated.stderr.decode("ascii", errors="backslashreplace"))
            expected = AUTH.generate(ROOT).encode("utf-8")
            self.assertEqual(destination.read_bytes(), expected)
            checked = subprocess.run([*command, "--check"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(checked.returncode, 0, checked.stderr.decode("ascii", errors="backslashreplace"))
            self.assertIn(b"Verified 23 auth labels", checked.stdout)

    def test_checked_in_copy_matches_hash_bound_capture(self):
        self.assertEqual((ROOT / AUTH.OUTPUT).read_text(), AUTH.generate(ROOT))

    def test_json_only_script_parsing(self):
        values = AUTH.extract(synthetic_html())
        self.assertEqual(len(values), len(AUTH.KEYS))
        self.assertEqual(values["common.close"], "synthetic common.close")
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            AUTH.extract('<script>self.__next_f.push(doNotExecute())</script>')

    def test_wrong_locale_duplicate_missing_or_non_string_labels_fail(self):
        for source in [synthetic_html(locale="fr"), synthetic_html(duplicate=True), synthetic_html(resources={}), "<html></html>"]:
            with self.assertRaises(ValueError):
                AUTH.extract(source)
        source = synthetic_html().replace("synthetic common.close", "")
        with self.assertRaises(ValueError):
            AUTH.extract(source)

    def test_tampered_bytes_and_changed_manifest_fail_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evidence/web/objects").mkdir(parents=True)
            record = dict(AUTH.SOURCE)
            manifest = {"captured_at": AUTH.CAPTURED_AT, "records": [record]}
            destination = root / "evidence/web/manifest.json"
            destination.write_text(json.dumps(manifest))
            (root / AUTH.SOURCE["path"]).write_text("not the retained HTML")
            with self.assertRaisesRegex(ValueError, "bytes"):
                AUTH.generate(root)
            record["sha256"] = "0" * 64
            destination.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "identity"):
                AUTH.generate(root)


if __name__ == "__main__":
    unittest.main()
