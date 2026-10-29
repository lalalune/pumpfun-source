"""Real capture CLI over loopback-only TLS; no live host, mocks or captured JS."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socketserver
import ssl
import subprocess
import sys
import threading

APP = Path(__file__).resolve().parents[1]


class Proxy(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(10)
        method, authority, _ = self.rfile.readline(4096).decode('ascii').strip().split(' ')
        if method != 'CONNECT' or authority not in ('pump.fun:443', 'docs.pump.fun:443'):
            raise ValueError('loopback fixture refuses any other target')
        while self.rfile.readline(4096) not in (b'\r\n', b'\n', b''):
            pass
        self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
        self.wfile.flush()
        with self.server.context.wrap_socket(self.connection, server_side=True) as tls:
            with tls.makefile('rb') as stream:
                request = stream.readline(4096).decode('ascii').strip()
                if request.split(' ', 1)[0] != 'GET':
                    raise ValueError('loopback fixture permits only GET')
                while stream.readline(4096) not in (b'\r\n', b'\n', b''):
                    pass
                body = f'<html><title>synthetic v{self.server.version}</title></html>'.encode()
                self.server.events.append((authority, request, self.server.version))
                tls.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\nContent-Length: ' + str(len(body)).encode() + b'\r\n\r\n' + body)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class CaptureCli:
    def __init__(self, folder):
        self.root = folder / 'app'
        self.web = self.root / 'evidence/web'
        scripts = self.root / 'scripts'
        scripts.mkdir(parents=True)
        for name in ('capture.py', 'verify-evidence.py'):
            shutil.copyfile(APP / 'scripts' / name, scripts / name)
        self.script = scripts / 'capture.py'
        assert self.script.read_bytes() == (APP / 'scripts/capture.py').read_bytes()
        certificate, key = folder / 'fixture.crt', folder / 'fixture.key'
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
            '-keyout', str(key), '-out', str(certificate), '-subj', '/CN=pump.fun',
            '-addext', 'subjectAltName=DNS:pump.fun,DNS:docs.pump.fun', '-days', '1',
        ], check=True, capture_output=True)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certificate, key)
        self.server = Server(('127.0.0.1', 0), Proxy)
        self.server.context = context
        self.server.version = 1
        self.server.events = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        proxy = f'http://127.0.0.1:{self.server.server_address[1]}'
        self.environment = {
            'PATH': os.environ.get('PATH', ''), 'HTTPS_PROXY': proxy,
            'HTTP_PROXY': proxy, 'NO_PROXY': '', 'SSL_CERT_FILE': str(certificate),
        }
        # The exact copied application verifier still checks npm integrity and all
        # original SDK source bytes. These local copies are inputs, never edited.
        sdk = self.root / 'evidence/sdk'
        sdk.mkdir(parents=True)
        for name in ('registry.json', 'pump-sdk-4.3.1.tgz'):
            shutil.copyfile(APP / 'evidence/sdk' / name, sdk / name)
        shutil.copytree(APP / 'packages/sdk/src', self.root / 'packages/sdk/src')
        shutil.copyfile(APP / 'packages/sdk/package.json', self.root / 'packages/sdk/package.json')
        for name in ('api-probes.json', 'source-map-probes.json'):
            (self.root / 'evidence' / name).write_text('[]', encoding='utf-8')

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def run(self, version, *args):
        self.server.version = version
        return subprocess.run([sys.executable, '-B', str(self.script), *args],
                              cwd=self.root, env=self.environment,
                              capture_output=True, timeout=30)

    def verify(self):
        return subprocess.run([sys.executable, '-B', str(self.root / 'scripts/verify-evidence.py')],
                              cwd=self.root, capture_output=True, timeout=20)

    def manifest(self):
        return (self.web / 'manifest.json').read_bytes()

    def archive(self, raw):
        return self.web / 'manifests' / (hashlib.sha256(raw).hexdigest() + '.json')

    def objects(self, manifest):
        return {row['path']: (self.root / row['path']).read_bytes()
                for row in json.loads(manifest)['records']}
