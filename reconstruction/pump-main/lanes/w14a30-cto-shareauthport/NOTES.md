# w14a30-cto-shareauthport: port of #3277 (sharing CPI authority AccountInfo literal) onto main f100a59

Target `0x22a10` `admin_cto::execute`. Base: origin/main `f100a59c1` (ratio 0.6423, 3173 slots).

Port of the external PR #3277 (w14a24-cto-shareauth, by kutluhaneth46), which showed 0.6414 -> 0.6426 on 7e6aa9c.

## Result

| | main f100a59 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.6423 | **0.6435** |
| slots_diff | 3,173 | 3,173 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `9c745887ccab74089ffe1e12af01486c483965013348b93ee65516619319e42c` |

## Change

In the `admin_cto_sharing_config` CPI, `authority:a.admin_set_creator_authority.to_account_info()` becomes an
eight-field `AccountInfo` literal that binds the lamports/data Rc clones to locals first, then stores the fields in the
order rent_epoch, owner, lamports, key, is_writable, is_signer, executable, data.

Ledger key: `0x22a10-w14-f100a59-shareauthport-port3277-v1`.

## Part 2 (branch -2, main b2e90aa, 0.6444): sharing CPI literal read-order screen

Tools (experiment only, in `$OUT/tools`): w14a17's raw-IR capture + `rx.py` oracle, and `pscan.py`, an extension of
w14a17's `fscan.py`. fscan places the six scalar reads (key, owner, rent_epoch, is_signer, is_writable, executable) of one
inlined AccountInfo clone at P0 (before the lamports Rc clone), P1 (between the Rc clones) or P2 (after both), but always in
canonical order inside a position. That loses the literal's own order: the authority literal in canonical P2 order scores
0.6393, not main's 0.6444. pscan adds `MODE=perm` (all 720 read orders, every read at one position) and `MODE=place`
(729 placements that keep the clone's current relative order).

| clone (sharing CPI) | perm (all P2) best at 27,400 | place best at 27,400 | result |
| --- | ---: | ---: | --- |
| authority (`%x18`) | **0.6447** (8 orders, e.g. K,R,W,S,O,E) | 0.6444 (main) | +1 M, source-confirmed |
| pool_authority (`%x`) | 0.62642 (most change size) | 0.6444 (main) | at optimum |
| global (`%x19`) | 0.63811 | **0.6447** (exec read before lamports: S,W,R,E,L,D,O,K) | +1 M, source-confirmed |
| mint (`%x20`) | no order keeps 27,400 | 0.6444 (main) | at optimum |
| sharing_config (`%_452`, to_account_info) | 0.63601 | 0.6444 (main, key first) | at optimum |

Composite authority K,R,W,S,O,E + global exec-early: **0.6450**, 3,172 slots, 27,400 B, 0 losses, differential 363/0,
unstripped sha256 `45414ecf9c83379f6ab13d6b627becda98cf9b8574643c89f0573d252a21034a`.

Struct-literal evaluation order of `AdminCtoSharingConfig` (authority at each position, global/mint swap, pool_authority
late, event_authority before sharing_config, full reverse): all 10 lose, 9 change size. Ledger
`0x22a10-w14-b2e90aa-shareauthport-sharing-struct-field-order-v1`.

## Part 3 (branch -3, main 5ee681d, 0.6450): sharing CPI program literal

pscan on the sharing CPI's last field `program:a.pump_fees.to_account_info()` (`%_461` on b2e90aa): placing the key read
between the two Rc clones gives 0.6447 on b2e90aa. As source, `program:{let x:&AccountInfo=a.pump_fees.as_ref();
AccountInfo{lamports,key,data,owner,rent_epoch,is_signer,is_writable,executable}}` on 5ee681d: **0.6450 -> 0.6453**, 3,172
slots, 27,400 B, 0 losses, differential 363/0, unstripped sha256 `72de66ff8867c2c7c00c3c7d14c01f6180ed7443a67340d23a3cfd4cd588b635`.
Ledger `0x22a10-w14-5ee681d-shareauthport-program-lit-keymid-v1`.

The CpiContext program (`%_418`) and sharing_config (`%_452`) to_account_info clones are at their placement optimum
(the current key-first order); every all-P2 permutation of them loses (best 0.62133 / 0.63601).

## Part 4 (branch -4, main 65df90f, 0.6453): in-position permutations (pscan `MODE=pp`)

`MODE=pp` keeps a clone's placement and permutes the read order inside each position. The `|` in an order marks the
lamports and data Rc clones.

| variant on 65df90f | literal read order | ratio | slots |
| --- | --- | ---: | ---: |
| main | | 0.6453 | 3,172 |
| g2 global | W,E,S,R \| L,D \| O,K | 0.6462 | 3,172 |
| a3 authority | K,R,W,E \| L,D \| S,O (inline Rc; the let-bound form a3b is the same) | 0.6456 | 3,170 |
| pa2 pool_authority | E \| L,D \| K,W,S,R,O | 0.6456 | 3,172 |
| **g2+a3** | | **0.64649** | 3,170 |
| g2+pa2 | | 0.64649 | 3,172 |
| g2+a3+pa2 / a3+pa2 | | 0.63751 / 0.63661 | 3,168 |

g2+a3 at 27,400 B has 0 losses and differential 363/0. Unstripped sha256 `927c4de8ae17595d136b623c023b021e9d3c8d112a4bd1fec5ed27040dca413f`.
Also tried on 65df90f: sharing_config and the CpiContext program written as literals. The to_account_info clone order
(K,L,D,O,R,S,W,E) equals main. The #3260 forms a and b and the #3277 form all lose, mostly through size changes.
