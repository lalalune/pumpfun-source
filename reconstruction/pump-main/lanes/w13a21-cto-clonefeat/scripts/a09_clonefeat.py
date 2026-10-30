#!/usr/bin/env python3
"""clonefeat.py <unstripped.so>...: how admin_cto::execute addresses the CPI AccountInfo clones.

Counts the `ldxdw rB,[rA+off]` loads of the AdminCto account fields that only the CPI clone runs read
(off 0x68 pool_authority, 0x90 sharing_config, 0x98 pump_fees, 0xa0 pump_fees_event_authority) and splits
them by how rA was produced:
  spill = rA was loaded from the frame by the instruction right before (accounts pointer reloaded from
          its spill slot per use, as the original does at 0x26798..0x26f10);
  reg   = rA is a register that already held the accounts pointer (ours: r6 for the whole clone run).
The original window scores spill/reg = 6/2; main (3912c47 .. b78bf19) scores 2/6.
Uses the w12a02-cto-iroracle ctoracle token reader (same tokens as target_metric)."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'w12a02-cto-iroracle/scripts'))
import ctoracle  # noqa: E402

OFFS = (0x68, 0x90, 0x98, 0xa0)


def feats(toks):
    spill = reg = 0
    prev = None
    for t in toks:
        op, regs = t[0], t[1]
        src = regs >> 4
        off = struct.unpack('<h', t[2:4])[0]
        if op == 0x79 and off in OFFS:
            if prev is not None and prev[0] == 0x79 and (prev[1] >> 4) == 10 and (prev[1] & 15) == src:
                spill += 1
            else:
                reg += 1
        prev = t
    return spill, reg


def main():
    otok, _ = ctoracle.orig_tokens()
    print('original spill/reg = %d/%d' % feats(otok))
    for f in sys.argv[1:]:
        toks = ctoracle.so_tokens(f)[0]
        s, r = feats(toks)
        print(f'{f} spill/reg = {s}/{r} insns={len(toks)}')


if __name__ == '__main__':
    main()
