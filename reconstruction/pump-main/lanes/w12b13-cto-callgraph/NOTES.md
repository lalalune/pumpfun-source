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
## Scope

These are instruction and call-layout observations for the named baseline.
They do not establish equivalent source scopes or whole-program identity.
Use the same-layout `--orig-names` input when examining a differently laid-out
candidate. Reports require a fresh output path and never replace an existing file.
