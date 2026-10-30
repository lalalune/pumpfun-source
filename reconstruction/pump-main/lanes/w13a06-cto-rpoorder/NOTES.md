# w13a06-cto-rpoorder: admin_cto sret-slot RPO order and the per-site holder test

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main `3912c47ac` (0.48772 / 3,273 slots), then main `8370e2f8a` (#2885 + w13a11-cto-stitch-2: 0.49071 / 3,313 slots).
Angle: make the 33 sret-demotion (`{i64, ptr}` call result) slots follow the original's ISel RPO
`284 289 298 296 330 338 334 326 | prepare 410 ... 719 | 312 307 307wp 306`.

`slots.py` (this directory) prints the `From<AnchorError>` result slot of each error line, sorted by slot:

```
python3 reconstruction/pump-main/lanes/w13a06-cto-rpoorder/slots.py orig <unstripped.so> ...
orig  284:6d0 289:6e0 298:6f0 296:700 330:710 338:720 334:730 326:740 410:760 556:7b0 648:7c0 660:7e0 719:800 312:8a0 307:8b0 306:8d0
main  284:6b0 289:6c0 330:6d0 312:6e0 307:6f0 306:710 298:720 338:730 334:740 326:750 410:770 556:7c0 648:7d0 660:7f0 719:810 296:8b0
```

## Result: a source form that gives the original's exact slot order (and its to_string outlining)

Mechanism. On main, `holder` is one `i1` (`(h & -3) != 0`) computed in execute, passed to validate and used by
every holder branch. A multi-use `i1` branch keeps the true successor first, so ISel's DFS enters the holder arm
before the non-holder arm, and the non-holder errors 306/307/312 get early slots while 296 is visited first and
gets the last slot. The original tests `h & 1` at each site (`and64 r8,1; jeq/jne r8,0`).

Give validate the raw `Option<bool>` and spell each holder test as `matches!(hopt,Some(true))`. Each site is
lowered on its own (discriminant switch + payload), and InstCombine/SimplifyCFG turn every site into a one-use
`icmp eq (and h,1),0` with the **false (non-holder) successor first** before GVN merges the compares. ISel's RPO
then becomes the original's, slot for slot (every offset is the original's minus 0x20):

| trial (edits on top of main) | bytes | ratio | slot order | to_string calls / lddw |
| --- | ---: | ---: | --- | --- |
| main 3912c47 | 27,400 | 0.48772 | `284 289 330 312 307 306 298 338 334 326 \| .. \| 296` | 5 / 88 |
| hm: target split `if matches!(hopt,Some(true))` | 27,120 | 0.43842 | `284 289 298 330 338 334 326 \| .. \| 312 307 306 296` | |
| a4: hm + 296 test + per-arm cashback use `matches!` | 27,152 | 0.41793 | **original** | |
| a2: hm + 289 + 296 use `matches!` | 26,848 | 0.42366 | **original** | |
| a1: hm + 289 + 296 + cashback use `matches!` | 26,832 | 0.42652 | **original** | |
| main 8370e2f | 27,400 | 0.49071 | main order | 5 / 88 |
| a1 on 8370e2f | 26,832 | 0.41834 | **original** | **7 / 86 = original** |
| a4 on 8370e2f | 27,024 | 0.43764 | **original** | **7 / 86 = original** (calls 154+4) |

So the original's RPO, its 7 outlined `to_string` calls (307/312 no longer inlined) and its lddw multiset
(86, i.e. no extra `.rel.dyn` entries) all come from the same change: per-site and-1 holder tests. The cost is
size: -248 to -568 B, so the function then lacks the original's other data flow (entry copy of `new`, sharing
payload pieces, 8/24 target, phi flags). This form is a structural target for the size lanes, not landable alone.

Edits (newline count unchanged; every error line kept):

```
fn validate(st:&CtoState,holder:bool,hopt:Option<bool>,fee:..)   // extra param, validate is inlined
let hopt=holder;let holder=hopt==Some(true);.. validate(&st,holder,hopt,fee,..)
289: if st.holder_reward&&!matches!(hopt,Some(true)){..}
296: if matches!(hopt,Some(true))&&!st.holder_reward&&!st.holder_enabled{..}
     let target=if matches!(hopt,Some(true)){if new.is_some(){..298..}*holder_key}else{..306..307..312..};
     let cashback=if matches!(hopt,Some(true)){false}else{st.cashback};
```

Not enough on their own: the same with `hopt==Some(true)` or `hopt!=Some(true)` at 289/296 (EarlyCSE merges them
with execute's compare: RPO unchanged), `holder.unwrap_or(false)` in execute (one shared and-1 `i1`: RPO unchanged,
27,064 B, 0.42659), the nested hr tree (27,016 B, RPO unchanged).

## IR oracle facts (llc on main's post-opt IR, target_metric tokens)

| IR edit on main 3912c47 | bytes | ratio | RPO |
| --- | ---: | ---: | --- |
| none | 27,400 | 0.48772 | main |
| swap `bb11.i` (hr==0 holder test: non-holder first) | 27,400 | 0.48023 | original |
| 306 tag test as `(tag&1)==0` | 27,408 | 0.47956 | main |
| 306 and-1 + swap `bb11.i` | 27,400 | 0.48742 | original |
| holder as `trunc i8 %h to i1` (shared) | 27,080 | 0.42435 | main |
| holder trunc + swap `bb11.i` | 27,080 | 0.44605 | original |
| best single flip: 410 `require!` error first (`bb74`) | 27,400 | 0.49311 | 410 slot last; abs_ratio 0.679 -> 0.633 |

The exact RPO alone is worth about nothing at main's structure; with the holder `trunc` it is worth +0.022.
The 410 flip's gain is a frame/alignment artefact (abs_ratio drops); `if creator_fee>0{return Err(..)}` and
`require!(!(creator_fee>0),..)` are byte-identical to main.

## Later bases (main 8370e2f 0.49071, main 10b4ddf 0.50929)

| build (main 10b4ddf unless noted) | bytes | ratio | abs_ratio | note |
| --- | ---: | ---: | ---: | --- |
| main 10b4ddf | 27,400 | 0.50929 | 0.68993 | slot order still main's (+0x28: 284 at 6d8, orig 6d0) |
| IR: swap `bb11.i` (original RPO) | 27,400 | 0.50180 | 0.69023 | |
| IR: 306 tag `(tag&1)==0` | 27,416 | 0.50045 | 0.67775 | |
| IR: 306 and-1 + swap `bb11.i` | 27,416 | 0.50794 | 0.69422 | original RPO |
| IR: holder `trunc` + 306 and-1 + swap `bb11.i` | 27,088 | 0.49932 | **0.69128** | the three faithful features together: code closer than main, 312 B short |
| a4 (source) | 26,744 | 0.43693 | | original RPO |
| a1 (source) | 26,840 | 0.43099 | | original RPO |

So the original RPO is worth something only together with the original's and-1 holder/tag tests, and even then
the function is ~300 B short. The source forms that give the RPO (per-site compares) also move the `to_string`
inlining set (BFI of a 3-way `Option<bool>` switch), which costs 250-800 B and most of the ratio.

### Other levers measured (all zero normalized losses, none a gain)

- 289 spellings on g8 (= w13a03 `let args=&(new,)` entry copy, 27,416 B / 0.49296 on 8370e2f):
  `!holder&&hr` 27,232/0.46544; `hr>holder` 27,168/0.49007; `require!(!hr||holder)` = g8; `(hr,holder)==(true,false)`
  27,216/0.48512; `match (hr,holder){(true,false)=>..}` = g8; nested `if hr{if !holder}` 27,088/0.3124; `hr&!holder`
  27,176/0.31704; `hr as u8>holder as u8` 27,048; hr as a separate validate `bool` param at 289 only 27,248/0.47492, at
  289 and 296 = g8; `#[inline(always)] validate` 27,256/0.44992; CtoState `holder_reward:..==true` = g8;
  collect_old `!hr&(creator!=default)` 27,400/0.41582.
  Reason: on g8's IR the best flip at 27,400 is the hr test `bb5.i` (hr-true first: 0.49670), but InstCombine inverts the
  hr compare as long as every user is a branch/select/not (it does so even with two branch users), and the original
  itself tests `jeq hr,0` with the same canonical successor order. That flip is a coincidental gain, not the original's form.
- 306 as `if let Some(t)=new{t}else{..}` / `match new{Some(t)=>t,None=>..}`: same bytes, 0.49011 on 8370e2f (-0.0006);
  the range-tagged compare canonicalizes back to None-first.
- non-holder target arm as a nested `fn pick(..)->Result<Pubkey>` (+216 B, 0.4586) or an immediately-called closure
  (+48 B, 0.48997 on 8370e2f; on g8 +48 B, 0.49222): RPO unchanged. Usable as positive size knobs (+48/+216 B).
- per-site `hopt.unwrap_or(false)` / `is_some_and(|h|h)` at all four sites: original RPO, 27,144 B, 0.43552.

Ledger keys: `0x22a10-w13-3912c47-rpoorder-*-v1` (all trials of this lane, including the later bases).
