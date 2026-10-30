"""Verify bindings, packet inventory and fresh terminal-branch observations."""
import hashlib
import json
import proof


def main():
    expected = json.loads((proof.P / 'manifest.json').read_text(encoding='utf-8'))
    actual = {str(path.relative_to(proof.P)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(proof.P.rglob('*')) if path.is_file()
              and path.name != 'manifest.json' and '__pycache__' not in path.parts
              and path.suffix != '.pyc'}
    if actual != expected:
        raise ValueError('packet inventory or content changed')
    saved = json.loads((proof.P / 'observations.json').read_text(encoding='utf-8'))
    if proof.check() != saved:
        raise ValueError('fresh observations differ from saved evidence')
    print('Terminal branch packet: bindings, manifest and observations passed')


if __name__ == '__main__':
    main()
