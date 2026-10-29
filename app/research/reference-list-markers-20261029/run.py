"""Finite localhost inspection; never changes reference source or captured data."""
from pathlib import Path
import argparse, hashlib, json, os, signal, socket, subprocess, time, urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--stage', choices=['baseline', 'fixed'], required=True)
args = parser.parse_args()
root = args.repo.resolve()
output = args.output.resolve()
assert not output.exists(), 'Preserve earlier measurements; choose a fresh output path'
output.mkdir(parents=True)
frontend = root / 'app/packages/frontend'
measurement = Path(__file__).with_name('measure.mjs')
assert measurement.is_file()
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip()
with socket.socket() as probe:
    assert probe.connect_ex(('127.0.0.1', 3027)) != 0, 'Port3027 already occupied'
paths = ['app/packages/frontend/src/app/docs/reference-page.tsx', 'app/packages/frontend/src/app/docs/reference-data.ts', 'app/packages/frontend/src/app/docs/reference-loader.ts', 'app/packages/frontend/src/app/docs/reference-pages.css', 'app/packages/frontend/src/app/docs/reference-pages.generated.json', 'app/scripts/extract-reference-pages.py']
before = {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths}
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
command = ['corepack', 'pnpm', 'exec', 'next', 'dev', '--turbopack', '--hostname', '127.0.0.1', '--port', '3027']
inspect_command = ['node', '--experimental-strip-types', str(measurement), str(root), str(output), args.stage]
support = frontend / 'next-env.d.ts'
original = support.read_bytes()
result = None
server = None
try:
    with (output / 'next.log').open('wb') as next_log:
        server = subprocess.Popen(command, cwd=frontend, env={**os.environ, 'PUMPFUN_DEVELOPER_API_KEY': ''}, stdout=next_log, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + 120
        while True:
            assert server.poll() is None, 'Owned Next exited before readiness'
            try:
                with urllib.request.urlopen('http://127.0.0.1:3027/docs/fees', timeout=2) as response:
                    if response.status == 200:
                        break
            except (OSError, TimeoutError):
                pass
            assert time.monotonic() < deadline, 'Local readiness deadline exceeded'
            time.sleep(0.25)
        with (output / 'browser.log').open('wb') as browser_log:
            result = subprocess.run(inspect_command, cwd=frontend, stdout=browser_log, stderr=subprocess.STDOUT)
finally:
    if server is not None and server.poll() is None:
        os.killpg(server.pid, signal.SIGINT)
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(server.pid, signal.SIGTERM)
            server.wait(timeout=10)
    support.write_bytes(original)
    after = {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths}
    assert before == after, 'Inspection must not change document source'
    record = {'head': head, 'stage': args.stage, 'serverCommand': command, 'browserCommand': inspect_command, 'exitCode': result.returncode if result is not None else None, 'sourceHashes': before, 'measurementSha256': hashlib.sha256(measurement.read_bytes()).hexdigest(), 'controllerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'nextLogSha256': hashlib.sha256((output / 'next.log').read_bytes()).hexdigest(), 'browserLogSha256': hashlib.sha256((output / 'browser.log').read_bytes()).hexdigest() if (output / 'browser.log').exists() else None}
    (output / 'RESULT.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record), flush=True)
assert result is not None
raise SystemExit(result.returncode)
