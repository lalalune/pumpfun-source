# w12b13-cto-callgraph: admin_cto::execute call-sequence alignment

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `20a1ae9c0` (landed baseline `8cd7695c…`): 0.43919, 3,352 slots, 27,400 B, 1033/1033.

## Tool

`callseq.py` (this directory) lists every call in layout order for the original window and a
candidate function, names internal callees with a same-layout unstripped build (address-based
labels are an analysis aid, not proof of original source identity;
`--orig-names` defaults to the landed baseline, so candidates of another size still resolve),
names syscalls through `.rel.dyn`, and labels error sites:

- `vNNNN`: the PumpError variant whose rodata constant is in r1/r2 at a `name`/`fmt`/`to_string` call;
- `ENNNN Lnnn`: the error code and `line!()` immediates stored before a `From<AnchorError>` call.

```bash
python3 callseq.py                      # summary of differing runs (callee names)
python3 callseq.py --table --by-site    # full table aligned on callee + error-site identity
python3 callseq.py --cand <unstripped.so> --json out.json
```

`TABLE-main-20a1ae9.txt` is the `--table --by-site` output for the pinned
main `20a1ae9c0` build. It reproduces byte-for-byte from the retained pass-7
unstripped ELF (`8cd7695c3fc638fc8ccfaba49a55b7615421e6f1c4c02f623124d9cc67a8ebf2`).
Unretained intermediate k4 and j3 tables are omitted.

## Findings (main 20a1ae9)

1. 157 calls each (154 internal + 3 syscalls). The callee multisets are equal except the known
   ToString split: original 7 `to_string` / 8 inlined `PumpError::fmt`, ours 5 / 10 (307 and 312
   inlined in ours).
2. Callee-name sequence ratio 0.8726 (site-aware 0.8662). Only three regions differ:
   - **validate** (o7..o47): error-site layout order. Original (first block of each site):
     `289 306 [F289] 298 326 [3 memcmp] [F306] 296 [F326] 312ts 307ts 330ts 338ts 334ts | prep 410 memcmp sol_log`.
     Ours: `289 296 298 [F289] 330ts [3 memcmp] 312 [F296] 326 306 [F312] 307 338ts | prep 410 memcmp 334ts sol_log`.
     (`ts` = outlined `to_string`; `[Fnnn]` = the site's From call placed apart from its name/fmt.)
   - **334 placement**: the CreatorFeeNotConfigurable block has the same code and the same single
     predecessor (`jeq fee_configurable,0`) in both, but the original places it right after the 338
     block; ours places it after the wallet "Creator is a program" msg block (between its
     `ja` and the second msg literal). This is a pure block-placement difference (no size change).
   - **wallet / sweep tail** (o109..o157): original order is
     `[wallet flags] [wallet ATA create] [sweep ATA create] transfer_vault_tokens collect Clock::get From<PE> token_frozen(coin) [event] [collect_coin_creator_fee] From<PE>`;
     main has `[wallet flags] [sweep ATA create] transfer_vault_tokens token_frozen(coin) [wallet ATA create] collect …` and one extra trailing From<PE>.
## Follow-up on main b5975fa (after #2749)

`callseq.py --obj <m.o>` reads a relocatable object from an `llc -function-sections` oracle run:
callees are named through `.rel` entries and lddw constants are resolved through their relocation, so
the same site-aware table works for IR experiments (3 s per llc run, no build slot).

On main b5975fa (0.45147 / 3,308 slots / 27,400 B) the tail o47..o157 (110 calls) is identical to the
original; every remaining call-sequence difference is inside validate (o7..o47): the error-site order,
the 307/312 `to_string` inline split, and the 334 block placed after the 410 code.

Wallet hybrids on 20a1ae9 (ledger `...-callgraph-wallet-docollect-only-v1`, `...-docoin-only-v1`):
only both halves of #2518 together align the wallet/sweep tail. The source half alone carries all of
the -88 B (27,312 B, 0.44801) but keeps main's tail order; the coin half alone is +24 B (0.44378).

334 placement (`llc -debug-only=block-placement`, debug llc): when the 338 chain ends, the 334 block
(freq .0039) loses to `bb40.i`, the non-holder `target = t` copy (.0080). In the original `bb40.i` is
already placed because the fee checks are duplicated per arm (the holder arm tests fee tag and
quote_locked itself and jumps straight to the fee_configurable test, skipping 330), so the
fee_configurable block is not ready early. Branch weights on the 334 test alone never move it
(1:1, 3:1, 1:8 all keep the call order; ledger `...-callgraph-334-branch-weight-oracle-v1`).

`to_string` boundary (307/312): nesting the holder-reward checks as in the original's post-opt tree
(`if st.holder_reward{if !holder{289}} else if holder&&!st.holder_enabled{296}`, lines kept) makes the
callee multiset equal to the original (7 `to_string`, 8 inlined fmt) and raises the callee-sequence
ratio to 0.8854, but the function shrinks to 27,016 B (-384) and the ratio drops to 0.41569
(ledger `...-callgraph-nest-289-296-hr-first-v1`). Masking frame offsets and registers, main and this
variant are equally close to the original (0.803 vs 0.804), so the to_string fix needs ~380 B of
compensating structure (the original's per-arm fee checks and phi-of-constants exit) to be landable.

## Scope

These are instruction and call-layout observations for the named baseline.
They do not establish equivalent source scopes or whole-program identity.
Use the same-layout `--orig-names` input when examining a differently laid-out
candidate. Reports require a fresh output path and never replace an existing file.
