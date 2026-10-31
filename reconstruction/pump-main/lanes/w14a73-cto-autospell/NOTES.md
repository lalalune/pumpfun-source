# w14a73-cto-autospell: mechanical single-site spelling lattice for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 39eb377 (0.66477, M 2,219), 0d04cf4 (#3393, 0.66507 / 3,228, M 2,220), 95a64ba (#3409, 0.66986 / 3,204,
M 2,236) and 963d1ee (#3437, 0.67226 / 3,123, M 2,244). The lattice was regenerated and re-screened on each.
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
  multi-use pure binding re-read) `reuse` (a recomputation replaced by its binding) `opswap` (`L&&R` -> `R&&L`,
  `L||R` -> `R||L`, `a&b` -> `b&a`).
- `tools/capraw2.py` is `capraw.py` with `--emit=llvm-ir` only (no link): 13.9 s instead of ~27 s per capture,
  byte-identical raw IR (checked against the linked capture of main). `capvar.sh` here uses it.
- Oracle reproduces main on both bases (`eq_main: true`, 0.66477 and 0.66507 at 27,400).

## Results by base

### 39eb377 and 0d04cf4: the lattice found the next landings, then went flat

- On 39eb377 the lattice flagged `iflet-L746` (sharing `if let` -> `match`) and `not-L556` (wallet `!is_writable` ->
  `==false`) as M-neutral size knobs. That pair, plus the pump_fees owner re-read drop, is exactly #3393 (w14a72).
- On 0d04cf4: about 250 singles, 44 applicable `sizeknobs-cto.json` knobs, 22 pairs and 4 bundles (up to 17 edits). Nothing
  beats main's M 2,220 at any size. The table below has per-rule counts.
- Size knobs at unchanged M: `eqfalse-L556-0` (`==false` -> `!`, -8 B) and `ifq-L561-0e` / `not-L561-*` (+8 B). Their
  pairs reach M 2,220 at 27,400 but raise slots from 3,228 to 3,265-3,270. `shift.py` bounds a pure +8 repay at +2 M.

### 95a64ba (#3409): two -8 B leads, both landed by other lanes before this lane could repay them

| variant | bytes | M | ratio |
| --- | ---: | ---: | ---: |
| main 95a64ba | 27,400 | 2,236 | 0.66986 |
| `eqfalse-L556-0` (wallet `!a.current_creator.is_writable`) | 27,392 | **2,238** | 0.67056 |
| `match-L746-0i` / `-2u` (sharing `match` -> `if let`) | 27,392 | **2,237** | 0.67026 |
| `iflet-L757-*` (curve fee match) | 27,392 | 2,236 | 0.66996 |
| best pair at 27,400: `eqfalse-L556-0` + `unwrapor-L757-0u` | 27,400 | 2,236 | 0.66986 (slots 3,215 > 3,204) |
| eqfalse/match -8 x L561 +8 pairs | 27,400 | 2,234-2,235 | |
| -16 / +16 triples (with `inline-L339-6`, `k-wl_ts_clockvar`) | 27,400 | 2,230-2,234 | |

The wallet +8 knobs at L561 sit in the same block as L556, so they cancel its jump-distance gain. `shift.py` on
`eqfalse-L556-0` found a pure +8 worth +1 M only at the entry `data_is_empty` call (cand 0x180) or in validate
(0x6d8-0xca8), and no source knob of the lattice puts +8 there. #3430 (w14a88) landed the same `!is_writable` revert,
repaid with a validate volatile placeholder at 334, and #3437 (w14a86) landed the sharing `if let`. The lattice had found
both leads.

### 963d1ee (#3437): partial screen (time box)

Main M 2,244. 41 singles were screened, with the size-moving families first. None reaches M 2,244 off-size or beats it
at 27,400. The closest: `ifq-L556-1t` at 27,392 / 2,239, `iflet-L757-1n` at 27,392 / 2,238, `not-L561-*` at 27,408 /
2,241, `iflet-L746-1n` (sharing `if let` -> None-first `match`) at 27,408 / 2,241, `inline-L339-6` at 27,416 / 2,243 and
`bitand-L578` at 27,400 / 2,243. With #3430 and #3437 in, the -8 B wallet and sharing levers are spent. About 220 of the
264 generated variants were not screened on 963d1ee, including the remaining `not`, `cmpswap`, `issome` and `reread`
sites.

## Per-rule table on 0d04cf4 (main M 2,220)

| rule | built | compile-fail | token-identical | best M (bytes) |
| --- | ---: | ---: | ---: | --- |
| andand | 7 | 0 | 1 | 2,220 (27,400) |
| oror | 5 | 0 | 0 | 2,208 (27,416) |
| bitand | 1 | 0 | 0 | 2,220 (27,400) |
| not / eqfalse | 16 (+17 identical on 39eb377) | 0 | 5 | 2,220 (27,392 eqfalse-L556) |
| cmpswap / cmpneg | 40 | 0 | 22 | 2,220 |
| keyspell | 11 | 3 | 6 | 2,220; `*x.key` at L339/L648 is -80 B for -9 M |
| iflet / match / letelse / unwrapor | 16 | 0 | 5 | 2,220 |
| andthen | 2 | 0 | 0 | 2,215 (27,376) |
| require / ifreq | 26 | 0 | 26 | identical (same MIR) |
| issome | 21 | 0 | 5 | 2,220; `hopt==Some(true)` respellings collapse (0.42-0.57) |
| inline / reread / reuse / letswap | 56 | 9 | 12 | 2,220 |
| ifq / thenopt | 11 | 0 | 1 | 2,220 |
| fieldswap | 17 | 0 | 6 | 2,220; Create field orders +56..+80 B |
| opswap (`L&&R` -> `R&&L` etc.) | 14 | 0 | 0 | 2,220 (L296-0, L338, L578); others -7..-631 |
| catalog (`sizeknobs-cto.json`, 44 that apply) | 44 | 0 | 0 | 2,220 (13 knobs, all M-equal) |

Families that are always token-identical (`require`/`ifreq`, most `cmpneg`, `!x` <-> `x!=true` vs `x==false`) can be skipped
on later mains. The live families are the size-moving ones: wallet / sharing / curve-store `if let` / `match`, `==false`,
`inline`, `ifq`.
