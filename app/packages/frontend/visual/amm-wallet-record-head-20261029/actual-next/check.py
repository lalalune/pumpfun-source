import datetime
import hashlib
import json
import pathlib
import subprocess
import time
import urllib.error
import urllib.request

root = pathlib.Path(__file__).resolve().parents[3]
out = pathlib.Path(__file__).resolve().parent
origin = "http://127.0.0.1:3027"
path = "/api/portfolio/amm-record?address=So11111111111111111111111111111111111111112"
receipt = {
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
    "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "origin": origin,
    "mode": "actual next dev unconfigured product route; SOLANA_RPC_URL explicitly empty; no fixture",
    "source_sha256": {},
    "cases": [],
}
for rel in [
    "app/packages/frontend/src/app/amm-wallet-record/handler.ts",
    "app/packages/frontend/src/app/amm-wallet-record/server.ts",
    "app/packages/frontend/src/app/api/portfolio/amm-record/route.ts",
]:
    receipt["source_sha256"][rel] = hashlib.sha256((root / rel).read_bytes()).hexdigest()
try:
    for method, suffix, expected in [("GET", "", 503), ("HEAD", "", 503), ("HEAD", "&unknown=1", 400)]:
        started = time.monotonic()
        req = urllib.request.Request(origin + path + suffix, method=method, headers={"Origin": origin, "Accept": "application/json"})
        try:
            resp = urllib.request.urlopen(req, timeout=10)
        except urllib.error.HTTPError as error:
            resp = error
        with resp:
            body = resp.read()
            row = {
                "method": method,
                "path": path + suffix,
                "status": resp.status,
                "headers": dict(resp.headers),
                "body_utf8": body.decode(),
                "body_bytes": len(body),
                "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
            }
        receipt["cases"].append(row)
        print(json.dumps(row), flush=True)
        headers = {key.lower(): value for key, value in row["headers"].items()}
        assert row["status"] == expected, row
        assert headers.get("cache-control") == "no-store", row
        assert headers.get("content-type", "").startswith("application/json"), row
        if method == "HEAD":
            assert body == b"", row
        else:
            assert json.loads(body)["error"]["code"] == "RPC_CONFIGURATION_INVALID", row
    receipt["result"] = "PASS"
except Exception as error:
    receipt["result"] = "FAIL"
    receipt["failure"] = repr(error)
    raise
finally:
    (out / "HTTP.json").write_text(json.dumps(receipt, indent=2) + "\n")
