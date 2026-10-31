# w14a108-cto-crlrepay: crl_L repay and extra-code ledger for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 13fe453 (#3480, 0.67256, M 2,245, 3,123 slots). Ledger approach `crlrepay`, keys
`0x22a10-w14-<main7>-crlrepay-<variant>-v1`.

## Result: original memcmp operand order through a key local (0.67256 -> 0.67316)

```rust
// before
let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();
// after
let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();
```

| | main 13fe453 | this lane |
| --- | ---: | ---: |
| ratio | 0.67256 | **0.67316** |
| M (matched masked tokens) | 2,245 | 2,247 |
| slots_diff | 3,123 | 3,123 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, no gains, no losses |
| differential | | 363 cases, 0 mismatches |

The original entry (orig 0x140-0x1c8) copies the sharing-config key into a stack temporary and calls
`memcmp(&curve.creator, &key_copy)`: the creator is the first operand and is compared in place. Main called
`memcmp(&key_copy, &curve.creator)`. The plain operand swap (`a.bonding_curve.creator==a.sharing_config.key()`, and
`.eq(&..)` / `&..==&..`) is token-identical among itself and costs 6 M (2,239). Binding the key first in a block,
then comparing `creator==sk`, keeps the same skeleton (`vs.py`: no skeleton difference) and gains 2 M through
register/frame naming. Hoisting the `sk` out of the `&&` operand and reusing it for `validate` collapses (M 1,819 at
27,056 B), as the w14a80 crh probes found for the creator copy.

## crl_L is not a faithful construct

crl_L (`{let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}`, w14a80) adds 9 instructions at cand 0x80: a
4-word copy of `curve.creator` to the stack before the sharing-key copy. **The original has no creator copy**: its two
4-word runs at orig 0x100-0x198 are the `hk.0` -> holder_key copy and the sharing-key copy. crl_L's +3 M is incidental
RA/frame naming. A "faithful -72 B repay" for it does not exist in the sense the angle assumed. On 13fe453 it is still
+3 M at +72 B (2,248 @ 27,472).

Repay screen on 13fe453 (raw-IR oracle, M at bytes):

| variant | bytes | M |
| --- | ---: | ---: |
| dv334 (drop the 334 `read_volatile` placeholder) | 27,392 | 2,244 |
| dv338 (drop the 338 placeholder) | 27,392 | 2,222 |
| dv334+dv338 | 27,384 | 2,222 |
| crl_L + dv334+dv338 | 27,456 | 2,225 |
| t1 (w14a87; on 13fe453 it is +8 B) | 27,408 | 2,239 |
| crl_L + t1 / + t1+dv334+dv338 / + t1+dv338 | 27,480 / 27,464 / 27,472 | 2,242 / 2,221 / 2,222 |

## Extra-code ledger (tools/xled.py, tools/xtab.py; tables xtab_13fe453.txt)

Skeleton-masked alignment (registers, frame offsets, jump offsets, lea immediates and call immediates masked) of a
candidate against the original, then the unmatched tokens of each side are cross-aligned against the other side's
unmatched pool (runs >= 3) to separate moved code from code that exists on one side only.

On main 13fe453: skM 2,810; ours-only 336 tokens, orig-only 338 tokens; moved ~190 each side. Most ours-only runs are
Rc-clone / AccountInfo-literal scheduling in the sharing CPI (cand 0x4070-0x4160, 0x4200-0x4308) and the post-validate
join (cand 0x1830-0x1920): order differences, not source constructs. The one real ours-only source construct is:

**to_string inlined at 307 and 312.** Each `error!` site calls `PumpError::name` and `<T as ToString>::to_string`.
The original calls the outlined `to_string` (0xa938) at 307 and 312 (and at 326/330/334/338/660/719, as ours does) and
inlines the formatter at 284/289/296/298/306. Ours inlines it at 307 and 312 too. IR oracle with a call-site
`noinline` on just those calls: 312 alone -216 B (M 2,191 on 963d1ee, fM unchanged: frame-only loss), 307 alone -192 B
(M 2,003), both -408 B (M 1,950).

**Mechanism (tools/bfi.py, seconds, needs only a raw-IR capture):** `to_string` costs 130; it is inlined at
threshold 325 and refused at the cold-call-site threshold 45. A call site is cold when its block frequency is below 2 % of
the caller's entry frequency. In `validate` on main (bfi_13fe453.txt):

| code | line | freq | decision |
| --- | --- | ---: | --- |
| 88 | 284 | 0.625 | inline |
| 83 | 289 | 0.117 | inline |
| 84 | 296 | 0.0264 | inline (original: inline) |
| 90 | 298 | 0.0403 | inline |
| 89 | 306 | 0.0754 | inline |
| 30 | 307 | **0.0283** | inline (original: **outlined**) |
| 19 | 312 | **0.0287** | inline (original: **outlined**) |
| 91/77/78/80 | 326/330/334/338 | < 0.02 | outlined (original: outlined) |

The original's pattern needs 307 and 312 below 0.02 while 296 stays above it. Holder spellings in validate reach
exactly that pattern: `hopt.unwrap_or(false)`, `matches!(hopt,Some(true))`, `hopt.unwrap_or_default()` and
`hopt.is_some_and(|h|h)` all give 307 0.0176 / 312 0.0179 cold, 296 0.0703 hot. But each collapses the function
(M 1,397 at 27,416 B, rfjM 2,137 against main 2,810): it is the old and-1 / outline basin. `!holder` at 289 alone
(v_289h) moves 307/312 to 0.0220/0.0223 at M 2,230 (-15), still hot. The outline basin needs its ~400 B repaid by the
original's orig-only constructs (orig 0x10f0 23 tok, 0xd90 15, 0x14b0 16, see xtab), which no single lane has found.

## Tools (experiment only)

- `tools/cv.sh <name> <genes> <slot>`: copy the worktree crate, apply genes (`mine.py`, w14a80 `genes.py`), capture the
  pre-opt IR (`capraw.py`) and run the opt/llc oracle (`rx.py`). `tools/batch.sh <spec>` runs a spec two at a time.
- `tools/mm.py`: bytes, M, skM, ours-only/orig-only token counts. `tools/fr.py`: M with frame (fM), registers (rM), both
  (rfM) and jumps (rfjM) masked. `tools/vs.py a b`: skeleton diff between two candidates.
- `tools/xled.py` / `tools/xtab.py`: the extra-code ledger above. `tools/bfi.py <raw.ll>`: to_string call-site
  frequencies and cold/hot prediction for validate (pass another fn regex as argv[2]).

## After landing (#3495, main ebe5387, 0.67316, M 2,247)

All 14 memcmp call sites now use the original operand order: same r1/r2 kinds at every site (stack copy versus in-place
field versus rodata constant). Screens on ebe5387 (raw-IR oracle; every row is in `screen_rows.md` and in the ledger):

- **Key-local / operand-order family (20 spellings):** sweep dest, wallet/sweep native, owner tests, 307/312
  operands, `*x.key` derefs and event keys. Every key-local spelling folds to main's tokens (eq_main true). The operand
  swaps `dest!=hv`, `ID==qm` (wallet, sweep) and `Pubkey::default()==q` lose 2-3 M. The skeleton holds at the other sites.
- **Curve-pointer-first entry (cb1-cb8):** the original loads `a.bonding_curve` before the sharing key. cb1/cb6/cb7/cb8
  fold to main. Binding `&a.bonding_curve.creator` or `&*a.bonding_curve` first (cb2-cb4) loses 8 M. `sk==creator`
  (cb5) loses 2 M.
- **PDA-first with the key local (pdaf, pdaf2, pdaf3):** skM rises to 2,823-2,828 (main 2,810), but M collapses to 1,953-1,955.
- **312 as two `if`s on one line (i312a/b):** the source form that would make 312's `to_string` cold collapses (M 1,880-1,887).
- **crl_L on ebe5387:** only +1 M at +72 B now (2,248 @ 27,472); with dv334, 2,247 @ 27,464.
- **dv334 (drop the 334 `read_volatile` placeholder) is -8 B / -1 M.** No +8 B partner repays it: rP_back gives 2,245,
  cu_unwrapcur / wl_writ_eq 2,244, p_colnat 2,243, wl_ts_clockvar / g_w_clock_local 2,243 @ 27,408, su_to_st 2,244 @ 27,384.
- **Lead (not landable):** `ev_cb_local` (event `is_cashback_coin:cashback`) gives **rfjM 2,872** (main 2,810, +62).
  The gain is in skeleton order in the sharing-CPI clone region (cand 0x3da8-0x4fb8), but M is 2,222 at 27,392 B: the jump
  distances and colouring do not follow. If a lane can repair the intervening block sizes, it may be worth a look.
