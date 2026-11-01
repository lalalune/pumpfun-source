"""Private source-only local imports for fresh composition qualification."""
import builtins
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import types
import uuid

MODULES = (
    'fresh_control', 'verify_fresh_control', 'build_score_pair', 'fastbuild',
    'score', 'original_input', 'compare_scores', 'link_order', 'build_process',
    'elf_symbols', 'instruction_stream', 'llvm_tools', 'score_admission', 'source_inputs',
)


class SourceContext:
    def __init__(self):
        self.root = Path(__file__).resolve().parent
        self.raw = {name: (self.root / (name + '.py')).read_bytes() for name in MODULES}
        self.raw['fresh_control_inputs'] = globals().get('_ADMITTED_SOURCE_BYTES',
                                                       Path(__file__).read_bytes())
        self.modules = {}
        self.prefix = '_pump_fresh_' + uuid.uuid4().hex + '_'
        self.hashes = {name + '.py': hashlib.sha256(raw).hexdigest()
                       for name, raw in self.raw.items()}

    def recheck(self):
        for name, digest in self.hashes.items():
            if hashlib.sha256((self.root / name).read_bytes()).hexdigest() != digest:
                raise ValueError('executed source input changed: ' + name)

    def load(self, name):
        if name in self.modules:
            return self.modules[name]
        module = types.ModuleType(self.prefix + name)
        module.__file__ = str(self.root / (name + '.py'))
        module.__dict__['_SOURCE_CONTEXT'] = self
        module.__dict__['_ADMITTED_SOURCE_BYTES'] = self.raw[name]
        imports = dict(vars(builtins))
        def source_import(target, globals=None, locals=None, fromlist=(), level=0):
            if level == 0 and target in self.raw and target != 'fresh_control_inputs':
                return self.load(target)
            return builtins.__import__(target, globals, locals, fromlist, level)
        imports['__import__'] = source_import
        module.__dict__['__builtins__'] = imports
        self.modules[name] = module
        sys.modules[module.__name__] = module
        try:
            exec(compile(self.raw[name], module.__file__, 'exec', dont_inherit=True),
                 module.__dict__)
        except BaseException:
            self.modules.pop(name, None)
            sys.modules.pop(module.__name__, None)
            raise
        return module

    @contextmanager
    def hook_cache(self):
        # Child compiler/linker Python hooks ignore sibling caches as well.
        keys = ('PYTHONPYCACHEPREFIX', 'PYTHONDONTWRITEBYTECODE')
        saved = {key: os.environ.get(key) for key in keys}
        with tempfile.TemporaryDirectory(prefix='pump-fresh-hook-cache-') as temporary:
            os.environ.update(PYTHONPYCACHEPREFIX=temporary, PYTHONDONTWRITEBYTECODE='1')
            try:
                yield
                if any(Path(temporary).rglob('*')):
                    raise ValueError('external hook bytecode cache changed during build')
            finally:
                for key, value in saved.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value


def load_context():
    context = SourceContext()
    context.recheck()
    return context
