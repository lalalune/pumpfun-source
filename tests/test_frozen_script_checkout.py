"""Exercise Git's actual Windows-style checkout of hash-pinned root tools."""
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source_blobs():
    listing = subprocess.check_output(['git', 'ls-tree', '-r', '-z', 'HEAD', 'scripts'], cwd=ROOT)
    names = []
    for entry in listing.split(b'\0'):
        if not entry:
            continue
        metadata, name = entry.split(b'\t', 1)
        path = name.decode('utf-8')
        if path.count('/') == 1 and path.endswith('.py'):
            if metadata.split()[0] not in (b'100644', b'100755'):
                raise AssertionError('root script must be a regular blob: ' + path)
            names.append(path)
    request = ''.join('HEAD:' + name + '\n' for name in names).encode()
    result = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT, input=request,
                            capture_output=True, check=True)
    stream = io.BytesIO(result.stdout)
    blobs = {}
    for name in names:
        _, kind, size = stream.readline().split()
        if kind != b'blob':
            raise AssertionError(name)
        blobs[name] = stream.read(int(size))
        if stream.read(1) != b'\n':
            raise AssertionError('invalid batch framing')
    return blobs


class FrozenScriptCheckoutTests(unittest.TestCase):
    def test_autocrlf_checkout_preserves_every_root_script_blob(self):
        blobs = source_blobs()
        self.assertGreater(len(blobs), 100, 'exercise the frozen tool set')
        environment = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull,
                           GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            def git(*arguments):
                return subprocess.check_output(
                    ['git', '-c', 'gc.auto=0', '-c', 'commit.gpgsign=false',
                     '-c', 'core.hooksPath=' + str(stage/'empty-hooks'), *arguments],
                    cwd=stage, env=environment, stderr=subprocess.PIPE)
            git('init', '--quiet')
            git('config', 'core.autocrlf', 'false')
            git('config', 'user.name', 'Checkout regression')
            git('config', 'user.email', 'checkout-test@example.invalid')
            (stage/'.gitattributes').write_bytes((ROOT/'.gitattributes').read_bytes())
            for name, content in blobs.items():
                path = stage/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            git('add', '--', '.gitattributes', 'scripts')
            git('commit', '--quiet', '-m', 'Canonical tool bytes')
            for name in blobs:
                (stage/name).unlink()
            git('-c', 'core.autocrlf=true', 'checkout', '--', 'scripts')
            changed = [name for name, content in blobs.items()
                       if (stage/name).read_bytes() != content]
            self.assertEqual(git('-c', 'core.autocrlf=true', 'status', '--porcelain'), b'')
            self.assertEqual(changed, [], 'clean checkout changed frozen tool bytes')


if __name__ == '__main__':
    unittest.main()
