#!/usr/bin/env python3
"""List file-mutating tool calls from a subagent transcript: tx_edits.py <agent.jsonl> [path-substring ...]"""
import json, sys
path = sys.argv[1]; pats = sys.argv[2:]
for n, line in enumerate(open(path)):
    try:
        m = json.loads(line)
    except Exception:
        continue
    msg = m.get('message') or {}
    if msg.get('role') != 'assistant':
        continue
    for b in msg.get('content') or []:
        if not isinstance(b, dict) or b.get('type') != 'tool_use':
            continue
        nm, inp = b.get('name'), b.get('input') or {}
        text = json.dumps(inp)
        if pats and not any(p in text for p in pats):
            continue
        if nm in ('Edit', 'Write', 'MultiEdit', 'Bash'):
            print(f"#### line {n} {nm} {inp.get('file_path', '')}")
            if nm == 'Edit':
                print('--- OLD:\n' + inp.get('old_string', '') + '\n--- NEW:\n' + inp.get('new_string', ''))
            elif nm == 'Write':
                print(inp.get('content', '')[:3000])
            else:
                print(inp.get('command', '')[:3000])
