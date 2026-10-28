#!/usr/bin/env python3
"""Run a command while holding one of N shared build slots (fcntl locks).

Usage: python3 sbf_lock.py [--slots N] [--name NAME] -- <command...>
"""
import fcntl, os, subprocess, sys, time
LOCKDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locks")
args = sys.argv[1:]
slots = 3; name = "slot"
while args[:1] in (["--slots"], ["--name"]):
    if args[0] == "--slots": slots = int(args[1])
    else: name = args[1]
    args = args[2:]
if args[:1] == ["--"]:
    args = args[1:]
if not args:
    sys.exit("usage: sbf_lock.py [--slots N] -- command ...")
os.makedirs(LOCKDIR, exist_ok=True)
start = time.time(); fh = None
while fh is None:
    for i in range(slots):
        f = open(os.path.join(LOCKDIR, f"{name}{i}.lock"), "w")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fh = f; break
        except BlockingIOError:
            f.close()
    if fh is None:
        time.sleep(5)
print(f"[sbf_lock] acquired slot after {time.time()-start:.0f}s", file=sys.stderr, flush=True)
sys.exit(subprocess.call(args))
