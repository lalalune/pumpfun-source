# w14a115-cto-devol338st: line-338 `read_volatile` placeholder replaced by ordinary source

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base: main ebe5387e1 (0.67316, 3,123 slots).
Continues w14a110-cto-devol338 (#3485, IR kind table) and w14a99-cto-feeexitstore (b0).
Ledger: approach `devol338st`, keys `0x22a10-w14-ebe5387-devol338st-*`.

## Result

| | ratio | slots | bytes | normalized/raw | differential |
| --- | ---: | ---: | ---: | --- | --- |
| main ebe5387 | 0.67316 | 3,123 | 27,400 | 1034/1034 | - |
| this PR (measure.sh, unstripped sha bf84626c0473cc06) | 0.67316 | 3,123 | 27,400 | 1034/1034, no losses | 363 cases, 0 mismatches |

Source change in `validate` (no new intrinsic, volatile, black_box or asm):
- `validate` takes `st:&mut CtoState` (call site `validate(&mut st,..)`, `let mut st`).
- the fee-Some arm ends with `st.fee_configurable=false;` in place of the `read_volatile(holder_key)`.
- `let hr=st.holder_reward;` at line 289, reused at line 298 (`holder&&!hr&&...`).

The candidate window differs from main's in exactly one instruction: main's `ldxb r1,[r10-0x6a0]` (placeholder)
becomes `stb [r10-0xb],0` (the store into `st`+45). Every other instruction is byte-identical.

Caveat for the owner's rule review: the store writes a local copy that is not read again, so it is semantically
dead; it survives opt only because `st` escapes into the later `memcmp(st.creator, ..)` (stores to `st`+32..45 are
already kept on main). It is ordinary Rust, but it is still a store whose job is to keep the fee-Some exit edge
non-empty (the original keeps a fee-tag constant `mov r7,1` there; that faithful data flow costs 276 M, see #3485).

## Mechanism

1. The fee-Some exit block only needs one surviving value-free instruction (w14a110). A constant store into the
   escaped `st` alloca survives DSE because `st` is passed to `memcmp` later.
2. Writing to `st` needs `&mut CtoState`. That alone costs 0.0039 (v_mut0 0.66247 vs b0 0.66637): with a shared
   `&CtoState` (Freeze, readonly) MIR GVN reuses the line-289 `st.holder_reward` load at line 298; through `&mut`
   it reloads, which adds a MIR block and swaps the 289/298 error-block order. A reborrow `let st=&*stm;` does not
   restore it (w_rb_* = v_* exactly).
3. Binding `let hr=st.holder_reward;` restores the reuse explicitly. With it, every constant-store spelling ties main.

## Priced table (raw-IR capture + opt/llc oracle, ebe5387)

| key | spelling | ratio | bytes | slots |
| --- | --- | ---: | ---: | ---: |
| m0 | main recapture (eq_main true) | 0.67316 | 27,400 | 3,123 |
| b0 | placeholder removed | 0.66637 | 27,392 | - |
| v_mut0 | `&mut CtoState`, no store | 0.66247 | 27,392 | - |
| v_mf1 / v_mayT / v_mayF / v_fcF / v_qlT | `&mut` + `st.max_fee=1` / `mayhem=true` / `mayhem=false` / `fee_configurable=false` / `quote_locked=true` | 0.66896 | 27,400 | 3,121 |
| v_mff | `&mut` + `st.max_fee=f` | 0.66856 | 27,408 | - |
| w_rb_* | `stm:&mut` + `let st=&*stm;` (same as v_*) | 0.66247 / 0.66896 / 0.66856 | | |
| x_hr_b0 / x_hr_0 | `hr` local without / with `&mut`, no store | 0.66637 | 27,392 | - |
| **x_hr_mf1 / x_hr_mayF / x_hr_fcF** | `&mut` + `hr` + constant store | **0.67316** | 27,400 | 3,123 |
| x_hr_mff | `&mut` + `hr` + `st.max_fee=f` | 0.67246 | 27,408 | - |
| x_hr_334 | `&mut` + `hr` + `st.mayhem=false` in place of the **334** volatile (338 kept) | 0.67316 | 27,400 | 3,123 |
| x_hr_both | both placeholders replaced (334: `st.mayhem=false`, 338: `st.max_fee=1`) | 0.67316 | 27,400 | 3,123 |

Line 334 (owned by w14a95-cto-devol334, not touched here): the same store kind also ties there, and with both
replaced the window still ties main (two instructions differ from main, both the former placeholder loads).

Tools: `tools/capvar.sh` (copy crate, apply EDITS, capture pre-opt IR), `tools/rx.py` (opt -O3 + llc + score),
`tools/batch.sh` (two captures at a time), `tools/gen*.py` (the EDITS above).
