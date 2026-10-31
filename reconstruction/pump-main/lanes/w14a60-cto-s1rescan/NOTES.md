# w14a60-cto-s1rescan: gated re-screen of the faithful sharing-CPI clone form (s1) on 6330811 and c3e5b51

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`, sharing CPI line 749), pinned at 27,400 B.
Continuation of w14a47-cto-sharestruct (#3351) and w14a05-cto-sibclone (#3217). Ledger approach `s1rescan`, keys
`0x22a10-w14-6330811-s1rescan-*-v1`, `0x22a10-w14-c3e5b51-s1rescan-*-v1` and the verdict row `0x22a10-w14-6330811-s1rescan-gate-v1`.

**No source change is proposed. The gate (step 1 of the angle) holds, so the hybrid screen was not run.**

## Gate result

s1 = all 7 sharing `AccountInfo`s as plain `to_account_info()` (the original's uniform derived-clone run; `edits/s1.py`,
regenerated per main by `edits/gen.py`). Raw-IR capture + rx.py oracle; `m0` reproduces main (`eq_main: true`) on both bases.

| base | main | s1 | s1 loss | cls seg 0x3c38-0x4a78 main (miss/fm/rm/jm/sk) | s1 |
| --- | ---: | ---: | ---: | --- | --- |
| 28ab23a (#3351) | 0.65488 | 0.61741 @27,376 | -0.03747 | 231/61/0/0/170 | 356/152/123/15/66 |
| 6330811 (#3358) | 0.65698 / 3193 | 0.61891 @27,376 | -0.03807 | 231/61/0/0/170 | 356/152/123/15/66 |
| c3e5b51 (#3369) | 0.65698 / 3182 | 0.62020 @27,368 | -0.03678 | 231/61/0/0/170 (447 cand insns) | 356/152/123/15/66 |

The classified miss counts are identical on all three bases: #3340-#3358 (TCF clones, sweep token arm) and #3369
(`if let` sharing arm, pool_authority `rent_epoch` re-read) did not move the sharing region's structure/register split.
The single-literal reversion row is also unchanged to within 0.0006 of #3351 (on c3e5b51: program 0.65608, authority
0.65428, pool_authority 0.65228 @27,392, global 0.64278 @27,360, mint 0.63901, event_authority 0.63298 @27,352). The
all-literal form is still the lattice optimum.

## Sweep-join occupancy (tools/csrmap.py on the debug-llc greedy log, `csrmap-c3e5b51.txt`)

The asm at the join is byte-for-byte the #3351 description on both bases:

```
ours  ldxdw r3,[r10-0x828] ... jne r7,2 ; stxdw [r10-0x968],r3      ; swept spilled at once
      ldxdw r1,[r10-0x8e8] ; stxdw [r10-0x8e8],r1 ; ... ldxdw r1,[r10-0x8e8]   ; tag reloaded twice
orig  ldxdw r9,[r10-0x828] ; ldxdw r6,[r10-0x8f8] ; jne r7,2        ; swept in r9, tag in r6
```

New fact from the occupancy map: **on c3e5b51 r7, r8 and r9 are free at the bb36 sweep join in main, and r6 is free until
the first clone load** (slot 56448). On 6330811, r9 held a 0/1 bool (`%1633 = MOV_ri 1/0`, 4 uses, the last a byte store after
the CPI) over the whole sharing arm, and r6 held the accounts pointer `%0`. #3369's `match` -> `if let`
removed both. Swept and the tag still spill. So callee-saved occupancy is **not** what keeps swept out of r9 or the tag
out of r6. The likely cause is their own live ranges and spill weights (swept is defined at the join and used again only
after the CPI; the tag is re-read from its slot for the `and 0xff; jne 2` test), but this lane did not price that. The occupancy re-screen trigger in #3351 is therefore too weak. A landing has to
change those two values' live ranges (defs or uses), not just free registers.

In s1 the accounts pointer `%0` sits in r7 for 4,032 slots of the clone run (the original reloads it from
`[r10-0x8d8]` before every clone). In main the clone run's callee-saved registers hold per-clone Rc pointers instead.
That is the rm 123 register-naming loss, unchanged from #3351.

## Tools (tools/, experiment only)

- w14a47's `capvar.sh` / `batch.sh` / `rx.py` / `cls.py` / `segdiff.py` / `rec.py`, repointed to this lane.
- `blk.py <ra.log> lo hi`: pre-RA MIR block headers and calls with slot indexes, used to pick csrmap ranges.
- `fdis.py <objdump.txt>`: execute listing from `llvm-objdump -d` of the rx/debug-llc object, at byte offsets
  (comparable to `win.py orig` minus 0x22a10).
- Debug-greedy log: `~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc` with rx.py's llc flags plus
  `-debug-only=regalloc` on `rx/<name>/m.ll`. It reproduces rx's `fn.bin` exactly (checked for m0 and s1).
- w14a46's `csrmap.py` and `lineage.py`, unchanged.

## Next ideas

- Re-screen s1 only after a landing that changes **swept's or the tag's live range**: for example swept consumed
  before the sharing arm, or the tag test folded into the `if let`. Freed registers alone no longer count.
- If a lane gets swept into r9 at the join (w14a06's coalescing route), run `bash tools/batch.sh res.jsonl m0 s1` plus
  `cls.py rx/s1/fn.bin 0x3c38 0x4a78` first. It takes about 30 s.
