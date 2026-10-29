"""CLI portability/protocol checks; loopback fixture is not a Next/SDK proof."""
import http.server
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

APP = pathlib.Path(__file__).resolve().parents[1]
CHECKER = APP / "scripts/amm-wallet-record/check-http.py"
SOURCES = (
    "app/packages/frontend/src/app/amm-wallet-record/handler.ts",
    "app/packages/frontend/src/app/amm-wallet-record/server.ts",
    "app/packages/frontend/src/app/api/portfolio/amm-record/route.ts",
)


class PortableHttpCheck(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="amm-public-http-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name) / "checkout in a different location"
        self.root.mkdir()
        for name in SOURCES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(APP.parent / name, path)
        self.git("init", "-q")
        self.git("add", "app")
        self.git("-c", "user.name=Local fixture", "-c", "user.email=fixture@example.invalid", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "Exact public-source input fixture")
        self.requests = []
        self.bad_headers = False
        owner = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.reply()

            def do_HEAD(self):
                self.reply()

            def reply(self):
                owner.requests.append((self.command, self.path))
                self.send_response(400 if "unknown=1" in self.path else 503)
                self.send_header("Content-Type", "application/json")
                if not owner.bad_headers:
                    self.send_header("Cache-Control", "no-store")
                self.end_headers()
                if self.command == "GET":
                    self.wfile.write(b'{"error":{"code":"RPC_CONFIGURATION_INVALID"}}')

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.origin = "http://127.0.0.1:" + str(self.server.server_port)
        self.output = pathlib.Path(self.temp.name) / "new receipt.json"

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.DEVNULL)

    def run_check(self, *extra):
        return subprocess.run([sys.executable, "-B", str(CHECKER), "--repository", str(self.root),
                               "--origin", self.origin, "--output", str(self.output), *extra],
                              cwd=self.temp.name, capture_output=True, text=True, timeout=15)

    def test_explicit_paths_and_protocol(self):
        run = self.run_check()
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        receipt = json.loads(self.output.read_text())
        self.assertEqual(receipt["head"], self.git("rev-parse", "HEAD").decode().strip())
        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(len(receipt["source_sha256"]), 3)
        self.assertEqual([row["status"] for row in receipt["cases"]], [503, 503, 400])
        self.assertEqual([row["body_bytes"] for row in receipt["cases"]][1:], [0, 0])
        self.assertEqual([method for method, _ in self.requests], ["GET", "HEAD", "HEAD"])

    def test_missing_metadata_is_a_recorded_failure(self):
        self.bad_headers = True
        run = self.run_check()
        self.assertEqual(run.returncode, 1)
        self.assertEqual(json.loads(self.output.read_text())["result"], "FAIL")
        self.assertEqual(len(self.requests), 1)

    def test_dirty_source_fails_before_http(self):
        with (self.root / SOURCES[0]).open("a") as source:
            source.write("\n// changed after checkout\n")
        self.assertEqual(self.run_check().returncode, 1)
        self.assertIn("differs from HEAD", self.output.read_text())
        self.assertEqual(self.requests, [])

    def test_existing_receipt_is_never_replaced(self):
        self.output.write_bytes(b"retained earlier observation")
        self.assertEqual(self.run_check().returncode, 1)
        self.assertEqual(self.output.read_bytes(), b"retained earlier observation")
        self.assertEqual(self.requests, [])

    def test_nonlocal_origin_is_rejected_before_http(self):
        self.assertEqual(self.run_check("--origin", "http://example.invalid").returncode, 2)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
