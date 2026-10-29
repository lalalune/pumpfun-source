# Saved-capture verification mode

This is the maintained entry for the frozen `scripts/verify_evidence.py` gate.
It does not change the frozen Python script set or any saved evidence.

## Reproduced failure

At base `b34e28a37ea3ed0326e120ff064c49ff213096bd`, a disposable copy of the
real nine-capture snapshot had one Pump payload byte at offset 0x1000 (inside
`.text`) flipped. The normal verifier refused it. With `python -O`, the same verifier
exited zero and printed `9 captures verified; no source rebuild claimed.`
Python had removed its assertion checks. `-OO` and `PYTHONOPTIMIZE=1` or `2`
have the same effect.

The entry refuses those modes before loading the frozen verifier. In normal
mode it executes the existing verifier unchanged, including its loader, hash,
slot, allocation, ELF and exact-capture-set assertions. The refusal tells the
caller how to rerun. This is narrower than replacing frozen checks or changing
interpreter settings and re-executing the process.

## Run

From the repository root, with Python 3.12 and the saved capture files present:

```sh
python -B repro/capture-verification-mode/verify.py
python -B repro/capture-verification-mode/test_verify.py
python -O -B repro/capture-verification-mode/test_verify.py
```

The regression uses copies of real saved evidence, with synthetic corruption
only in the copied payload. Original captures are never changed. It checks
the normal successful path and refusal of corrupted evidence under default,
`-O`, `-OO` and both environment-selected optimization levels.

The direct historical script retains its original optimization limitation;
use this entry for current verification. This change proves saved-evidence
gate behavior only. It adds no source reconstruction, program equivalence,
fresh compilation, transaction replay, live capture or security acceptance.
