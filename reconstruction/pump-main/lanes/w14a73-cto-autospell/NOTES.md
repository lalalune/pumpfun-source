# w14a73-cto-autospell: mechanical single-site spelling lattice for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 39eb377 (0.66477, M 2,219), then 0d04cf4 (#3393, 0.66507 / 3,228 slots, M 2,220).
Ledger approach `autospell`, keys `0x22a10-w14-<main7>-autospell-<rule>-L<line>-<k><tag>-v1`
(rows written before 02:28Z under `0d04cf4` keys were measured on 39eb377; see `...-autospell-labelfix-v1`).

## Tool: `tools/autospell.py` (reusable after every landing)

```bash
python3 tools/autospell.py $WT/programs/pump/src/creator/admin_cto.rs $OUT/v [--rules a,b] [--from-line 283]
# -> $OUT/v/<rule>-L<line>-<k><tag>.py (EDITS=[(old,new)], old unique, newline count kept) + manifest.json
bash tools/runlist.sh <namelist> $OUT/v $OUT/res.jsonl <slot>    # capvar.sh per name (2 workers = 2 slots)
SHA=<main7> python3 tools/rec.py $OUT/res.jsonl $OUT/v/manifest.json   # M per row + one ledger row per variant
```

- Token/regex level, no new deps. A string/comment mask and a bracket-depth operand scanner give operand extents for
  `&&`, `||`, `==`, `!=`, `>` and unary `!`; every edit is one site, keeps the line count (so every `line!()` immediate),
  and is skipped when it would reorder a side effect (`?`, `return`, `token_frozen`, or an assignment to a root of the
  moved expression between binding and use).
- Rules (24): `andand` `oror` `bitand` `not` (`==false` / `!=true`) `eqfalse` `cmpswap` `cmpneg` `keyspell`
  (`x.key()` <-> `*x.key`) `iflet` / `match` (both arm orders, `is_some()+unwrap`) `letelse` `unwrapor` `andthen`
  (both directions) `require` (`!(c)`, negated comparison, `err!`) `ifreq` (if-return -> `require!`) `issome`
  (`matches!`, `!=None`, `!is_none()`, `unwrap_or(false)`, `is_some_and`) `inline` (single-use let) `ifq`
  (`if c{f()?;}` -> `if c{f()}else{Ok(())}?;` / `then().transpose()?`) `thenopt` (the sweep `(!skip).then(..)` in 5
  forms) `letswap` (adjacent independent lets) `fieldswap` (CtoState / Create init order) `reread` (one use of a
  multi-use pure binding re-read) `reuse` (a recomputation replaced by its binding).
- `tools/capraw2.py` is `capraw.py` with `--emit=llvm-ir` only (no link): 13.9 s instead of ~27 s per capture,
  byte-identical raw IR (checked against the linked capture of main). `capvar.sh` here uses it.
- Oracle reproduces main on both bases (`eq_main: true`, 0.66477 and 0.66507 at 27,400).

## Result: the single-site lattice is flat on 0d04cf4 (no variant exceeds main's M at any size)

~250 singles on 0d04cf4 (plus 193 on 39eb377) and 22 composites. Main M = 2,220.

| rule | built | compile-fail | identical to main | best M (bytes) |
| --- | ---: | ---: | ---: | --- |
| not / eqfalse | 34 | 0 | most | 2,220 (eqfalse-L556 at 27,392; not-L561 at 27,408) |
| cmpswap / cmpneg | 41 | 0 | 22 | 2,220 (identical); swaps of key compares cost 1-3 M |
| require / ifreq | 26 | 0 | 26 | identical: `require!` and if-return lower to the same MIR |
| issome | 21 | 0 | 5 | 2,220 (identical); `hopt==Some(true)` respellings collapse to 0.42-0.57 |
| iflet / match / letelse / unwrapor | 16 | 0 | 5 | 2,220; match-L746 if-let 27,392 / 2,218 |
| andand / oror / bitand | 13 | 0 | 1 | 2,220 (bitand-L578 = `&&` back, identical M); all `&` forms lose 40-430 M |
| inline / reread / reuse / letswap | 63 | 9 | 13 | 2,220 (inline-L339-6, identical M); inline-L649 27,384 / 2,219 |
| ifq / thenopt | 11 | 0 | 1 | 2,220 (ifq-L561 if/else 27,408; thenopt match form 27,400) |
| fieldswap | 17 | 0 | 6 | 2,220 (identical); Create field orders +56..+80 B |
| keyspell / andthen | 13 | 3 | 6 | `*x.key` at L339/L648: -80 B for -9 M (largest cheap size lever) |

Free size knobs on 0d04cf4 (M unchanged): `eqfalse-L556-0` (wallet `!is_writable`, -8 B, ratio 0.66517 at 27,392),
`ifq-L561-0e` / `not-L561-*` (+8 B). Near-free: `inline-L649-0` (-16 B, M -1), `ifq-L556-*` (-8 B, M -1),
`match-L746-*` (-8 B, M -2), `andthen-L664-0` (-24 B, M -4 on 39eb377).

Pairs at 27,400 (eqfalse/ifq/match -8 x L561 +8, and zero-size identical-M triples): all M 2,218-2,220, none above main;
the -8/+8 pairs raise slots 3,228 -> 3,265-3,270. `shift.py` on eqfalse-L556-0 bounds a pure +8 repay at +2 M
(cand 0x2468-0x24e8, the sweep coin-vault token_frozen block), and main's own pure pair bound is +3.

On 39eb377 the lattice found the two edits #3393 landed (`iflet-L746` sharing match, `not-L556` is_writable==false) as
size-neutral M-equal knobs; that pair plus the pump_fees owner re-read drop is exactly w14a72's landing.
