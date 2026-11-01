# w17a31-shim-mv58src: source form of the original's sweep-exit block order (MV58)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 shim track.
Base: main 8bee07558 / e89d79aa8 (same `programs/`): admin_cto 0.68754, M 2,295, 3,096 slots, 27,400 B, Pump Main 1034/1034.
Continues w17a21-shim-sweepdup (#4047) NOTES sections 3-4 and next ideas 1-3.
Ledger: approach `mv58src`, keys `0x22a10-w17-8bee075-mv58src-<item>-v1`.

`M` = scorer matched tokens from the slim pre-opt oracle (w17a06 `capraw` + `preslim` + `fx`; it reproduces main exactly:
2,295 @27,400). `m1`/`m2`/`m3` = w17a21 `skel.py` mask levels.

## 1. Result: an ordinary-Rust source form whose build equals the MV58 oracle

`b_two` (line count kept; `b_two.diff`):

```rust
// lines 663-664 (token arm head on 664, lines 719-720 unchanged)
  let min=if native{let rent=Rent::get()?;rent.minimum_balance(0)}else{0};let amount;if native{amount=a.creator_vault.lamports().saturating_sub(min);
   if amount>0{ensure_rent_exempt(..)?;transfer_native(..,amount,&vsigner)?;}Ok(amount)}else{let frozen=token_frozen(..)?;amount=token_raw_amount(..)?;
```

Its capture is **byte-identical to w17a21's s_nat1 + post-opt MV58 module**: 2,121 @27,384, m1 2,293, m2 2,480, m3 2,858,
raw sha1 `b3da2668d99d` (same bytes as `lx/s_nat1.mv`). No steering construct is involved. So the original's sweep-exit
skeleton (sweep.exit preds {648, 660, vsigner-scope Err join}, Ok returns and AMM `?` Errs threaded, per-exit `jne r7,2`
copies, the Rent-Err call falling into the shared test, rest of the native arm at the original's offset) is now reachable
from source, and every MV58-based IR lead (h_n1, h_evdn, e79v, c1a, the RA climbs) can be built as source on top of it.

## 2. Mechanism

- rustc codegens MIR in reverse postorder and creates each LLVM block at its first reference (appended at the end).
  Postorder takes successors with `next_back`, so for `switchInt(native) -> [0: token, otherwise: native]` the whole token
  region is codegenned before the native region (and vice versa for a flipped switch).
- The vsigner-scope Err join J (return drop-tree node of the vsigner scope) is reached from both arms. Whichever region is
  codegenned first references J from its last block (its own Err drop node), so J lands between the two arms. Every switch
  spelling (bool, `!`, `==false`, opaque `pt1`, 3-way `match`) only chooses WHICH arm comes first; none can put J after both.
- J is created after both arms only if the first region's Err node is itself reachable from the second region (then RPO
  codegens it late). A drop node shared by both arms but not by the Rent::get Err needs a local that is live in both arms and
  declared after Rent::get: hoist Rent::get into its own `if native` and declare `let amount;` between the tests.
  `amount`'s StorageDead node (empty after SROA) is then the token/native-rest Err join, codegenned after the native rest,
  and J (`min`'s node + the vsigner chain) is created there. Rent Err goes to J directly, as in the original.
- MIR jump threading merges the two `native` tests, so the final CFG has one test; the pre-opt order becomes
  `..R T m r . T .. C . V .. O .. E . N .. J` (R = Rent::get, J last) and the post-opt order equals MV58's.

## 3. Form table (screened by pre/post-opt block order with `tools/preord.py`, then M)

| form | what | M @ bytes | order |
| --- | --- | --- | --- |
| main | | 2,295 @27,400 | |
| s_nat1 | w17a21 native tail | 1,302 @27,424 | J before native rest (collapse) |
| s_nat1 + MV58 (IR) | | 2,121 @27,384 | oracle |
| **b_two** | Rent::get hoisted + deferred `let amount;` | **2,121 @27,384** | = oracle, byte-identical |
| a_pt1same | `if unsafe{pt1(31,native)}` | 1,302 @27,424 | byte-identical to s_nat1 |
| a_pt1flip | `if unsafe{pt1(31,!native)}{token}else{native}` | 1,300 @27,456 | native, J, token |
| c_tokia | token arm as `#[inline(always)]` nested fn (value arm) | 1,700 @27,416 | J late but Rent::get after the token rest; two-join shape |
| c_tokpl | token arm as plain nested fn | 963 @30,088 | not inlined (invalid) |

## Tools

- `tools/preord.py <name> [--post]`: compact block-order signature of the sweep region (pre-opt sweep fn or post-opt
  execute) from a capture's `fx/<name>/{in,m}.ll`.
- `variants/f1.py`: the forms above (w17a21 `capvar.sh`/`batch.sh` format; `variants/s4.py` holds the anchors).
