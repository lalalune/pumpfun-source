"""Replay Write/Edit tool calls on fees100/shared/tools/* from all workflow transcripts, in timestamp order."""
import json, glob, sys
from pathlib import Path
D = '/Users/shawwalters/.claude/projects/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/e9a70435-0695-431c-bd3e-ac553674cc64/subagents/workflows'
OUT = Path('/Users/shawwalters/fees100-run/recovery/tools')
events = []
for f in glob.glob(D + '/*/agent-*.jsonl'):
    agent = f.split('/')[-1]
    for line in open(f):
        try: e = json.loads(line)
        except Exception: continue
        msg = e.get('message') or {}
        content = msg.get('content')
        if not isinstance(content, list): continue
        for c in content:
            if c.get('type') != 'tool_use': continue
            inp = c.get('input', {}); fp = inp.get('file_path', '') or ''
            if '/shared/tools/' in fp and c.get('name') in ('Write', 'Edit', 'MultiEdit'):
                events.append((str(len(events)).zfill(6) + ' ' + e.get('timestamp', ''), agent, c.get('name'), fp.split('/shared/tools/')[1], inp))
# keep transcript order (all tool edits come from the speed lane's single transcript)
files = {}; log = []
for ts, agent, name, rel, inp in events:
    if name == 'Write':
        files[rel] = inp['content']; log.append((ts, agent, 'W', rel))
    elif name == 'Edit':
        if rel not in files: log.append((ts, agent, 'E-noFILE', rel)); continue
        old, new = inp['old_string'], inp['new_string']
        if old not in files[rel]: log.append((ts, agent, 'E-MISS', rel)); continue
        files[rel] = files[rel].replace(old, new) if inp.get('replace_all') else files[rel].replace(old, new, 1)
        log.append((ts, agent, 'E', rel))
    elif name == 'MultiEdit':
        for ed in inp.get('edits', []):
            if ed['old_string'] in files.get(rel, ''):
                files[rel] = files[rel].replace(ed['old_string'], ed['new_string'], 0 if not ed.get('replace_all') else -1) if False else (files[rel].replace(ed['old_string'], ed['new_string']) if ed.get('replace_all') else files[rel].replace(ed['old_string'], ed['new_string'], 1))
        log.append((ts, agent, 'ME', rel))
OUT.mkdir(parents=True, exist_ok=True)
for rel, text in files.items():
    p = OUT / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
for l in log: print(*l)
print('files:', sorted(files))
