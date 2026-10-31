#!/usr/bin/env python3
"""drive.py <res.jsonl> name... : run capvar.sh for e/<name>.py on 2 work slots, append rx + evreg results."""
import sys, subprocess, json, threading, queue, os
OUT = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a44-cto-evprov')
T = os.path.dirname(os.path.abspath(__file__))
res, names = sys.argv[1], sys.argv[2:]
q = queue.Queue(); [q.put(n) for n in names]; lock = threading.Lock()
def work(slot):
    while True:
        try: n = q.get_nowait()
        except queue.Empty: return
        r = subprocess.run(['bash', f'{OUT}/tools/capvar.sh', n, f'{OUT}/e/{n}.py', str(slot)], capture_output=True, text=True)
        line = r.stdout.strip().split('\n')[-1] if r.stdout.strip() else ''
        try: d = json.loads(line)
        except Exception: d = {'name': n, 'error': (r.stdout + r.stderr)[-400:]}
        if 'ratio' in d:
            for k, rng in (('ev', []), ('wl', ['0x5c38', '0x6b08'])):
                e = subprocess.run(['python3', f'{T}/evreg.py', f'{OUT}/rx/{n}/fn.bin', *rng], capture_output=True, text=True).stdout
                try: d[k] = {x: y for x, y in json.loads(e).items() if x.startswith('L') or x == 'error'}
                except Exception: d[k] = e[-200:]
            if os.path.exists(f'{OUT}/ir/{n}.ll'): os.remove(f'{OUT}/ir/{n}.ll')
        with lock:
            open(res, 'a').write(json.dumps(d) + '\n'); print(json.dumps(d), flush=True)
th = [threading.Thread(target=work, args=(s,)) for s in (0, 1)]
[t.start() for t in th]; [t.join() for t in th]
