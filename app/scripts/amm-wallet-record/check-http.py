"""Inspect an explicitly selected local, unconfigured AMM product route.

This is an HTTP protocol checker. Its output does not establish the server's
implementation, SDK execution, configured RPC success or historical test results.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SOURCES = (
    "app/packages/frontend/src/app/amm-wallet-record/handler.ts",
    "app/packages/frontend/src/app/amm-wallet-record/server.ts",
    "app/packages/frontend/src/app/api/portfolio/amm-record/route.ts",
)
QUERY = "/api/portfolio/amm-record?address=So11111111111111111111111111111111111111112"


def loopback_origin(value):
    url = urllib.parse.urlsplit(value)
    if (url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost", "::1")
            or url.username or url.password or url.path or url.query or url.fragment):
        raise argparse.ArgumentTypeError("Expected an explicit HTTP loopback origin without a path")
    try:
        url.port
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=pathlib.Path)
    parser.add_argument("--origin", required=True, type=loopback_origin)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    receipt = {"origin": args.origin, "cases": [], "source_sha256": {},
               "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "mode": "HTTP protocol observation; server implementation and configuration supplied by operator"}
    # Refuse replacement of a retained receipt, including on a failed request.
    with args.output.open("x", encoding="utf-8") as output:
        try:
            root = args.repository.resolve(strict=True)
            git = lambda *items: subprocess.check_output(["git", *items], cwd=root)
            if pathlib.Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() != root:
                raise ValueError("--repository must name the Git checkout root")
            receipt["head"] = git("rev-parse", "HEAD").decode().strip()
            for relative in SOURCES:
                body = (root / relative).read_bytes()
                if body != git("show", "HEAD:" + relative):
                    raise ValueError("Working source differs from HEAD: " + relative)
                receipt["source_sha256"][relative] = hashlib.sha256(body).hexdigest()
            # Disable ambient proxies and redirects: this check stays on its
            # explicit local server and never follows a response to another host.
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
            for method, suffix, status in (("GET", "", 503), ("HEAD", "", 503), ("HEAD", "&unknown=1", 400)):
                started = time.monotonic()
                request = urllib.request.Request(args.origin + QUERY + suffix, method=method,
                                                headers={"Origin": args.origin, "Accept": "application/json"})
                try:
                    response = opener.open(request, timeout=10)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    body = response.read()
                    headers = {key.lower(): value for key, value in response.headers.items()}
                    row = {"method": method, "path": QUERY + suffix, "status": response.status,
                           "headers": headers, "body_utf8": body.decode("utf-8"), "body_bytes": len(body),
                           "elapsed_ms": round((time.monotonic() - started) * 1000, 3)}
                receipt["cases"].append(row)
                if row["status"] != status or headers.get("cache-control") != "no-store" or not headers.get("content-type", "").startswith("application/json"):
                    raise ValueError("Unexpected status or response metadata")
                if method == "HEAD":
                    if body:
                        raise ValueError("HEAD response contained a body")
                elif json.loads(body).get("error", {}).get("code") != "RPC_CONFIGURATION_INVALID":
                    raise ValueError("GET did not report the unconfigured RPC guard")
            receipt["result"] = "PASS"
        except Exception as error:
            receipt.update(result="FAIL", failure=repr(error))
        finally:
            json.dump(receipt, output, indent=2)
            output.write("\n")
    print(json.dumps({"result": receipt["result"], "cases": len(receipt["cases"]), "output": str(args.output)}))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
