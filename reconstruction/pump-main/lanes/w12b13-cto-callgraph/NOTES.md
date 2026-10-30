# w12b13-cto-callgraph: admin_cto::execute call-sequence alignment

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `20a1ae9c0` (landed baseline `8cd7695c…`): 0.43919, 3,352 slots, 27,400 B, 1033/1033.

## Tool

`callseq.py` (this directory) lists every call in layout order for the original window and a
candidate function, names internal callees with a same-layout unstripped build (every other window
is byte-identical at the same address, so an original callee address names the same function;
`--orig-names` defaults to the landed baseline, so candidates of another size still resolve),
names syscalls through `.rel.dyn`, and labels error sites:

- `vNNNN`: the PumpError variant whose rodata constant is in r1/r2 at a `name`/`fmt`/`to_string` call;
- `ENNNN Lnnn`: the error code and `line!()` immediates stored before a `From<AnchorError>` call.

```bash
python3 callseq.py                      # summary of differing runs (callee names)
python3 callseq.py --table --by-site    # full table aligned on callee + error-site identity
python3 callseq.py --cand <unstripped.so> --json out.json
```

`TABLE-main-20a1ae9.txt` and `TABLE-k4.txt` are the `--table --by-site` outputs for main and for
the best unlanded composite (w9r2-admincto-harvest k4).

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
3. **The wallet_flags gene (#2518, `do_collect`/`do_coin` short-circuit flags) makes the whole tail
   o47..o157 (110 calls) identical to the original** (harvest j3 and k4). Its cost is size: j3 is
   27,312 B (-88), k4 27,384 B (-16).
4. Per-interval size map (candidate offset minus original offset at each aligned call):
   - entry: -8 at o1, -56 at o4, -128 at o7 (the original's `new` pieces copy at 0x4d8..0x538 and
     the holder_key copy at 0x598..0x5d0 have no counterpart in ours);
   - in j3/k4 the wallet region (o108..o157) is within ±40 B of the original, so the j3 deficit of
     88 B is not in the wallet: main's wallet form is ~88 B larger than the original's and
     compensates the entry/validate deficit by accident.
   So a landable wallet_flags needs compensation in the entry/validate region (where the original
   really has more code), not in the wallet.

## Ledger keys

See SUMMARY.json at the end of the lane.
