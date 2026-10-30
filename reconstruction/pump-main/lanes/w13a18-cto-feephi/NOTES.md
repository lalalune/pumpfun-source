# w13a18-cto-feephi: per-arm fee-None threading with validate kept as a separate fn

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 74b31714a (admin_cto 0.51348, 3,334 slots). This lane continues w13a05-cto-feethread (#2926).
Every number below comes from the raw-IR opt oracle (w13a01 `rx.py`). On this main its tokens equal the
baseline build (`eq_main: true`). Nothing here is landable yet.

## Result: the source shape that threads fee-None per arm (validate stays an LLVM-inlined fn)

**Mechanism.** In main, every fee-None edge and the fee-OK path join one block (`bb68`). That block memcpys
validate's returned target pieces (`target.i.sroa.0` 7 B, `target.i.sroa.9` 9 B) into execute's `target`.
So the block is too big for JumpThreading (n=4..12 against the 6-instruction cut), and LVI cannot resolve
`shared` on its incoming edges. Once validate writes the target through an **out-param** instead of returning it:

- the join holds only the `br shared`;
- JumpThreading duplicates the join for the holder fee-None edge, which tests `shared` and then jumps straight
  to the holder&shared tree block (holder is known through LVI). This is orig 0x10e8;
- with `shared` passed in and the override in the arm (`if shared{st.creator}else{t}`), the non-holder fee test
  is duplicated per shared sub-arm (`maybeThreadThroughTwoBasicBlocks`, LVI-known `shared`). Its None edges go
  straight to the shared/!holder block (orig 0x1850) and to the `creator!=default` memcmp (orig 0x18f8);
- wallet and sweep stay inlined (157 = 154+3 calls), unlike validation written inline (w13a05 f02b, 86 calls).

`tools/feetests.py rx/<name>` (post-opt IR) for `vb8`:
```
TEST bb45.i         None-> bb68.thread   -> br label %bb17   (shared, !holder)
TEST bb45.i.thread  None-> bb18.thread   -> br label %bb19   (!shared: collect_old memcmp)
TEST bb44.i         None-> bb68.thread287-> br i1 %shared, label %bb22 (holder&shared), label %bb18
```

Minimal source edits (`trials/vb8.py`):
```
fn validate(st,holder,shared:bool,fee,new,holder_key,sharing,out:&mut Pubkey)->Result<()>
  *out=if holder{..*holder_key}else{..;if shared{st.creator}else{t}};   .. Ok(())
execute: let (holder_key,_)=find_program_address(..);let shared=..;   (shared after the PDA, as orig 0x140)
  let mut target=holder_key;validate(&st,holder,shared,fee,new,&holder_key,&sharing,&mut target)?;
  tree: shared&&!holder arm no longer assigns target
```

**Returning `Result<()>` costs the error layout.** `Result<(),Error>` is niche-encoded: Ok is tag 2 of the
`From<AnchorError>` result. Validate's error edges then reach a `tag==2` test that JumpThreading cannot
resolve, and the 284 block moves before 410. Returning `Result<Pubkey>` and ignoring the payload
(`Ok(*holder_key)`, `trials/vb12.py`) brings back a constant tag. **errseq from 330 on then equals the
original:** `.. 330 338 334 410 719 648 660 284 556`. Main has `.. 330 338 410 334 ..`.

## Measurements (raw-IR oracle, main 74b31714a)

fm = frame-masked difflib ratio (`tools/absratio.py`). Main's fm is 0.69772 (skeleton 0.86669).

| trial | change | bytes | ratio | fm | fee tests | errseq |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| main | | 27,400 | 0.51348 | 0.698 | 2 | 298 289 296 326 306 312 307 330 338 410 334 719 648 660 284 556 |
| g1 | w13a05 let-else `return Ok(target)` | 27,440 | 0.47508 | | 2 | = main |
| e1 | f01 re-run: override in validate | 27,288 | 0.28580 | | 2 | = main |
| vc | e1 + `(Pubkey,u8)` arm tag, tree matches on it | 27,456 | 0.38755 | 0.682 | 2 | = main |
| va | out-param only (holder threads) | 27,064 | 0.14591 | | 2 | .. 338 334 284 410 .. |
| vb | out-param + arm override | 27,176 | 0.14651 | 0.599 | **3** | .. 338 334 284 410 .. |
| vb7 | vb + shared after the PDA | 27,304 | 0.14496 | 0.642 | 3 | |
| vb8 | vb7 with `target=holder_key` init | 27,304 | 0.15666 | 0.643 | 3 | |
| vb9 | `target=st.creator` init, shared arm writes nothing | 27,088 | 0.14977 | 0.598 | 3 | |
| va8 | va + shared move + holder_key init | 27,152 | 0.14959 | 0.597 | 2 | |
| vb11 | vb8 returning `Result<Pubkey>` = `Ok(*out)` | 27,648 | 0.13329 | 0.531 | 3 | **tail = orig** |
| vb12 | vb8 returning `Ok(*holder_key)` | 27,512 | 0.18774 | 0.525 | 3 | **tail = orig** |
| vb12a1 / a4 | + w13a06 per-site `matches!(hopt,Some(true))` | 26,784 / 26,752 | 0.24511 / 0.21586 | 0.388 / 0.554 | 2 | 289 298 296 306 312 307 330 326 338 410 334 .. |
| vb8a1 / a4 | same on vb8 | 26,752 / 26,864 | 0.15280 / 0.18031 | 0.591 / 0.633 | 2 | 289 298 296 306 312 307 330 326 338 334 284 410 .. |

Why the ratio drops: execute's frame grows 24-40 B (r4 spill at -0x938/-0x948; orig -0x928, main -0x910).
New 32 B allocas (`target`, the creator copy, the `new` payload copy) replace main's 7/9 B pieces.
The changed BFI also moves large chunks. vb12 lays the sweep tail (orig 0x2548/0x3e38) elsewhere, a 747-insn
hunk, and `tools/regcov.py` shows its regions 0x3800-0x4800 drop to 0. On vb8 the losses sit in regions
0x1800, 0x3000 and 0x5000-0x6000, mostly register and lea differences.

## Tools (`tools/`; experiment only)

- `feetests.py <rxdir>`: fee-tag tests in post-opt execute, with their preds and None/Some successors.
- `splitmerge.py in.ll out.ll <block> <pred:suffix>..`: duplicates a block per predecessor, for JT mechanism tests
  with `opt -passes=jump-threading`. On e1, splitting `bb68` is not enough: the copy is still n=11, so JT will not
  duplicate the fee test.
- `errseq.py <so|orig|fn.bin>`: error sites in code-layout order. `slotsbin.py`: w13a06's sret slot order on `fn.bin`.
- `absratio.py`, `regcov.py`: frame-masked/skeleton ratio, and per-0x800-region orig coverage.
- `runq.sh <list>`: two-worker capture+oracle queue (w13a01 `capvar.sh`/`rx.py` with this lane's paths).

Ledger keys: `0x22a10-w13-74b3171-feephi-*`.
