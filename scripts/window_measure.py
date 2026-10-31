"""Window measurement used by verify.py (stdlib only). Same rule as the AMM lanes' measure.py:
an original .text window is matched when some candidate function has the same size, the same normalized
bytes (call immediates and relocated immediates zeroed) and the same relocation pattern; raw = exact bytes."""
import collections, json, types
from pathlib import Path
HERE = Path(__file__).resolve().parent
def _elf_class():
    m = types.ModuleType('window_elf_reader'); p = HERE / 'window_elf_reader.py'; m.__file__ = str(p)
    exec(compile(p.read_bytes(), str(p), 'exec'), m.__dict__); return m.Elf
def measure(original_path, candidate_path):
    Elf = _elf_class(); o = Elf(Path(original_path)); c = Elf(Path(candidate_path))
    ix = collections.defaultdict(list)
    for f in c.funcs:
        key = (f['size'], c.normalized[f['start']:f['start'] + f['size']], json.dumps(c.pattern(f['start'], f['size']), sort_keys=True))
        ix[key].append(f)
    rows = []
    for a, z in zip(o.entries, o.entries[1:] + [o.hi]):
        key = (z - a, o.normalized[a:z], json.dumps(o.pattern(a, z - a), sort_keys=True))
        ms = ix.get(key, [])
        # Name the raw-equal function when one exists, not merely the first normalized match.
        exact = next((f for f in ms if o.b[a:z] == c.b[f['start']:f['start'] + z - a]), None)
        best = exact or (ms[0] if ms else None)
        rows.append({'original': hex(a), 'bytes': z - a, 'match': best['name'] if best else None, 'raw': exact is not None})
    return rows
