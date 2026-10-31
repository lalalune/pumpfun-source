"""Heredoc boundary and env option-cluster tests for check_workflow_inputs.py."""

import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
import check_workflow_inputs as check  # noqa: E402


class CheckWorkflowInputsParsingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        check.git(self.root, "init", "-q")
        self.write("scripts/ok.py", "print('ok')\n")
        self.workflow("python -B scripts/ok.py")
        check.git(self.root, "add", ".")
        check.git(
            self.root,
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "baseline",
        )

    def write(self, name: str, text: str):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def workflow(self, commands: str):
        indented = "\n".join("          " + line for line in commands.splitlines())
        self.write(
            ".github/workflows/test.yml",
            "name: test\non: [push]\njobs:\n  audit:\n    steps:\n      - run: |\n"
            + indented
            + "\n",
        )

    def run_check(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            status = check.main(["--repo", str(self.root), *args])
        return status, json.loads(out.getvalue())

    def test_non_heredoc_double_lt_does_not_skip_workflow_step(self):
        non_heredocs = {
            "comment_bitshift": "# Verify 1 << 32 bound\npython -B scripts/missing.py",
            "double_quoted_bitshift": 'python -c "assert (1 << 8) == 256"\npython -B scripts/missing.py',
            "single_quoted_bitshift": "python -c 'assert (1 << 8) == 256'\npython -B scripts/missing.py",
            "bash_here_string": "cat <<< 'inline-token'\npython -B scripts/missing.py",
            "escaped_lt": "echo \\<<EOF\npython -B scripts/missing.py",
        }
        for label, step_body in non_heredocs.items():
            with self.subTest(case=label):
                self.workflow(step_body)
                status, report = self.run_check("--all")
                self.assertEqual(status, 1, label)
                self.assertEqual(
                    [row[2] for row in report["new_missing"]],
                    ["scripts/missing.py"],
                    label,
                )
                self.assertEqual(report["uninspected"], [], label)

    def test_genuine_heredocs_still_report_uninspected(self):
        heredocs = (
            "cat <<EOF\npython scripts/not-run.py\nEOF",
            "cat <<-EOF\n\tpython scripts/not-run.py\nEOF",
            "cat <<'EOF'\npython scripts/not-run.py\nEOF",
            'cat <<"EOF"\npython scripts/not-run.py\nEOF',
            "cat <\\\n<EOF\npython scripts/not-run.py\nEOF",
        )
        for step_body in heredocs:
            with self.subTest(command=step_body):
                self.workflow(step_body)
                status, report = self.run_check("--all")
                self.assertEqual(status, 0)
                self.assertEqual(report["checked_references"], 0)
                self.assertIn(
                    [".github/workflows/test.yml", "audit", "heredoc body requires shell parsing"],
                    report["uninspected"],
                )

    def test_clustered_env_flags_and_post_dashdash_assignments(self):
        missing_cases = {
            "clustered_iu_separate": ("env -iu PYTHONPATH python -B scripts/missing.py", "scripts/missing.py"),
            "clustered_iC_separate": ("env -iC scripts python -B missing.py", "scripts/missing.py"),
            "clustered_iC_attached": ("env -iCscripts python -B missing.py", "scripts/missing.py"),
            "clustered_iC_double_prefix": (
                "env -iCscripts python -B scripts/ok.py",
                "scripts/scripts/ok.py",
            ),
            "post_dashdash_assignment": (
                "env -- FOO=bar python -B scripts/missing.py",
                "scripts/missing.py",
            ),
        }
        for label, (command, expected_missing) in missing_cases.items():
            with self.subTest(case=label):
                self.workflow(command)
                status, report = self.run_check("--all")
                self.assertEqual(status, 1, label)
                self.assertEqual(
                    [row[2] for row in report["new_missing"]],
                    [expected_missing],
                    label,
                )

        valid_cases = (
            (["-iu", "DROP", "FOO=1", sys.executable, "-B", "scripts/ok.py"], "env -iu DROP FOO=1 python -B scripts/ok.py"),
            (["-iC", "scripts", sys.executable, "-B", "ok.py"], "env -iC scripts python -B ok.py"),
            (["-iCscripts", sys.executable, "-B", "ok.py"], "env -iCscripts python -B ok.py"),
            (["--", "FOO=1", sys.executable, "-B", "scripts/ok.py"], "env -- FOO=1 python -B scripts/ok.py"),
        )
        env_bin = shutil.which("env")
        for native_args, workflow_cmd in valid_cases:
            with self.subTest(valid=workflow_cmd):
                if sys.platform != "win32" and env_bin is not None:
                    completed = subprocess.run(
                        [env_bin, *native_args],
                        cwd=self.root,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertEqual(completed.stdout.strip(), "ok")
                self.workflow(workflow_cmd)
                status, report = self.run_check("--all")
                self.assertEqual(status, 0, workflow_cmd)
                self.assertEqual(report["checked_references"], 1)
                self.assertEqual(report["uninspected"], [])

    def test_truncated_env_value_options_fail_closed(self):
        for bad_cmd in ("env -u", "env --unset", "env -iu", "env -iC"):
            with self.subTest(command=bad_cmd):
                self.workflow(bad_cmd)
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as err:
                    self.run_check("--all")
                self.assertEqual(err.exception.code, 2, bad_cmd)

    def test_env_split_string_is_reported_as_uninspected(self):
        for split_cmd in (
            'env -S "FOO=1 python3 -B scripts/missing.py"',
            'env -iS "python3 -B scripts/missing.py"',
            'env --split-string "python3 -B scripts/missing.py"',
            'env --split-string="python3 -B scripts/missing.py"',
        ):
            with self.subTest(command=split_cmd):
                self.workflow(split_cmd)
                status, report = self.run_check("--all")
                self.assertEqual(status, 0)
                self.assertEqual(report["checked_references"], 0)
                self.assertIn(
                    [".github/workflows/test.yml", "audit", "env split-string requires shell parsing"],
                    report["uninspected"],
                )


if __name__ == "__main__":
    unittest.main()
