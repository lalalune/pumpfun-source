"""Shared append framing for the AMM ledger; callers hold .attempts.lock."""
import json
import os


def append_entry(path, entry):
    encoded = (json.dumps(entry, sort_keys=True) + '\n').encode('utf-8')
    with path.open('a+b') as log:
        if log.tell():
            log.seek(-1, os.SEEK_END)
            if log.read(1) != b'\n':
                # Keep a torn row as evidence, but do not join the new row to it.
                log.write(b'\n')
        log.write(encoded)
