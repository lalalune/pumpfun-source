# Lane w6r3-layout-rodata (wave 6, round 3): rodata / data layout for raw

Base: origin/main 6484b2837 (1027/293), rebased onto fb25fce02 (1030/295).
Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w6r3-layout-rodata/`. Lane tools are in `tools/`:

| tool | what it does |
| --- | --- |
| `t.sh NAME [src]` | fastbuild + score + admin_cto target_metric |
| `secs.py so` | per-section size/identity against the original |
| `elfmap.py so refined.json` | whole-ELF non-`.text` identity modulo placement. It maps candidate addresses to original ones (`.text` through the refined window pairing, data by section base) and compares `.rel.dyn` (multiset and per-window counts), `.dynsym` and `.dynamic` |
| `dridn.py so refined.json` | each `.data.rel.ro` text pointer: does it point at the paired function (plus the same in-function offset)? |
| `errsites2.py orig.txt cand.txt` | for every anchor `error!` site in a disassembly: is `ToString::to_string` inlined (`D`, the String fmt::Write vtable lddw) or called (`NT`)? |
| `bag.py so 0xwin sym` | bag-of-instructions and n-gram overlap (an alignment-insensitive diagnostic that sits alongside win.py's ratio) |
| `capture.py` | experiment-only capture with extra rustc flags (`-Cremark=inline`, `-Cllvm-args=-print-bfi ...`). Never used for proposals |

`refine.py`, `shiftraw.py`, `drr.py` and `dataoff.py` are the layout-order-census and w6r2-layout-rodata tools.

## Census: the data side is done except for 2 relocations (attempt `b9032d07`)

On main 6484b28 (and on fb25fce02, same picture):

- `.rodata` is byte-identical to the original (w6r2-layout-rodata's result holds).
- `.data.rel.ro`: 158 slots differ. All of them are text pointers, and all 158 point at the paired function at the same in-function offset (`dridn.py`). They differ only because of placement.
- `.dynsym` is equal after mapping. `.dynamic` differs in the section addresses, which are equal after mapping, and in `DT_RELSZ`/`DT_RELCOUNT` (2 entries).
- `.rel.dyn`: 6147 entries in the original, 6149 in ours. The 590 non-`.text` relocations are equal. Every window's `.text` relocation count is equal except `admin_cto::execute` (87 in the original, 89 in ours).
- `.text` is +552 B on 6484b28 (+472 on fb25fce02): the 512-B `ensure_rent_exempt` wrapper (PR #2168 removes it) plus the unmatched-window deltas. It shifts every data lddw. `shiftraw.py` gives raw 439 (6484b28) and 456 (fb25fce02) if only the data bases moved.

## The 2 extra relocations: inlined `ToString::to_string` at two cold call sites

The 2 extra relocations are lddw's of the `String as fmt::Write` vtable (`.data.rel.ro`+0x128). They come from the inlined
`<T as ToString>::to_string` in anchor's `error!` (`error_msg: e.to_string()`). Where the call stays outlined (to the
296-B `to_string` at 0xa938), there is no vtable lddw.

Per-site census (`errsites2.py`):

| line | 284 | 289 | 296 | 298 | 306 | **307** | **312** | 326 | 330 | 334 | 338 | 410 | 556 | 648 | 660 | 719 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original | inl | inl | inl | inl | inl | **call** | **call** | inl | call | call | call | inl | inl | inl | call | call |
| main | inl | inl | inl | inl | inl | **inl** | **inl** | inl | call | call | call | inl | inl | inl | call | call |

Inliner oracle (attempt `4aed3843`, experiment-only `-Cremark=inline -Cdebuginfo=line-tables-only` and `-print-bfi`
on `validate`): `to_string` costs 130. The normal threshold is 325. At a cold call site (block frequency < 2% of
the caller's entry, no profile) the threshold is 45, so the call stays outlined. Before inlining, `validate`'s BFI puts the 307 error
block at 0.0220 and the 312 block at 0.0223, just above 2%. The cause is the line-296 check
`if holder&&!st.holder_reward&&!st.holder_enabled{..}` followed by a separate `let target=if holder{..}else{..}`.
BPI cannot see that the block after the 296 check has `holder == true`, so it sends 50% of that flow (+0.047) into
the `else` arm, which holds 306/307/312.

## Change (attempt `f5a10147`)

The 296 check moves inside the `if holder` arm, which keeps the same checks, the same order and the same Source lines:

```rust
 let target=if holder{if !st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}

  if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}holder_key}else{
```

| metric | main fb25fce | this lane |
| --- | ---: | ---: |
| official normalized / raw | 1030 / 295 | 1030 / 295 (0 losses, 0 raw losses) |
| `to_string` inline/call set in admin_cto | 10 / 5 (original 8 / 7) | **8 / 7 = original, site for site** |
| String-vtable lddw in admin_cto | 11 (original 9) | **9** |
| `.rel.dyn` entries | 6149 (original 6147) | **6147** |
| windows whose relocation count differs | 1 (admin_cto) | **0** |
| `.dynamic` | RELSZ, RELCOUNT differ | **equal after address mapping** |
| `.rodata` | identical | identical |
| `.text` vs original | +472 | +56 |
| admin_cto bytes (original 27400) | 27344 | 26928 |
| admin_cto win.py ratio | 0.37637 | 0.32392 |
| admin_cto bag / 3-gram / 6-gram (`bag.py`, on 6484b28) | 0.6235 / 0.2997 / 0.1548 | 0.6274 / 0.3006 / 0.1533 |
| unstripped sha256 | 585b84b8... | b139972f... |

Every non-`.text` byte of the ELF now matches the original after address mapping: the relocation multiset per window,
`.dynsym`, `.dynamic`, `.rodata` and `.data.rel.ro` targets. What is left is placement and `.text` size.

The win.py ratio drops because the two inlined bodies (~208 B each) are gone and the function is now 472 B short
of the original. That makes the sequence alignment worse. The alignment-insensitive overlap stays flat (bag slightly up).
admin_cto lanes: the original is 472 B larger *without* those two inlined `to_string` bodies, so the missing code is
elsewhere. Keep the 296 check inside the holder arm, or any other form that leaves 307/312 below 2% BFI, or the vtable
relocations come back.

## Composition with PR #2168 (attempt `32ba9da6`)

| build | normalized / raw | `.text` vs original | raw if only data bases moved | sha256 |
| --- | ---: | ---: | ---: | --- |
| main fb25fce + #2168 | 1030 / 336 | -40 | 553 | 3acec89a... |
| main fb25fce + #2168 + this | 1030 / 336 (0 losses, 0 raw losses vs the row above) | -456 | 553 | b9ad5637... |

admin_cto against the original after this change: the multiset of data lddw targets is equal (84 = 84, it was 86 before), and so is
the direct-call count (157 = 157). The 472 B the original has on top are therefore plain instructions (no call, no
data reference): register, stack and branch structure. Official raw from data rebasing (553 with #2168) needs the
unmatched windows' total size delta at 0. Today that is create_v2 +8, admin_cto -472, swap_hop -40, sweep +48 (cand - orig).

## Attempts

| id | trial | result |
| --- | --- | --- |
| `b9032d07` | whole-ELF non-text census (elfmap/dridn) | data identity complete except admin_cto's 2 relocations |
| `4aed3843` | inline-remark + BFI oracle on validate | 307/312 at 2.2% BFI (cold threshold 2%), infeasible holder edge |
| `f5a10147`, `4e7f17e3` | t01/t02: 296 check inside the holder arm (6484b28, fb25fce) | **kept**: to_string set = original, `.rel.dyn` 6147 = 6147, 0 losses |
| `32ba9da6` | merged with #2168 | 0 losses, raw 336 = 336 |

## Merge review (2026-10-30, main 5b54ad5)

Merged with origin/main, the admin_cto reorder scores 1032 / 347 (13 gains vs baseline), the same as main, with
0 normalized and 0 raw losses. admin_cto 0x22a10 (original 27400 B) goes from 27344 B / ratio 0.37637 on main
to 26928 B / 0.32392, which is further from the original size. #2412 had already restored admin_cto to 27344 B.
The source change is not merged; main's programs/pump is kept, and this lane's notes and tools are kept as a record.
