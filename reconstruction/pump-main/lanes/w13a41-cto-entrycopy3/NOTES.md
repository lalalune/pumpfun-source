# w13a41-cto-entrycopy3: entry copy of `new` + by-value validate keys (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 16c10e631 (0.62043) and 52c0b087c (0.62103, current baseline).
Continues w13a28-cto-entrycopy2 (#3103) and w13a33-cto-keyslots (#3087).
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w13a41-cto-entrycopy3/` (not in git).
Ledger keys: `0x22a10-w13-{16c10e6,52c0b08}-entrycopy3-*-v1`.

**Result: no zero-loss gain, no source change.** Every entry-copy composite stays 0.05 to 0.06 below main. This
notes PR records which source form is the original's, and why it still loses. Every number below comes from the
raw-IR capture + rx `opt`/`llc` oracle. Its tokens equal a `measure.sh` build (`eq_main` is true on both mains).
Trial edit lists are in `e/` (`capvar.sh` EDITS format, `e/common.py` holds the shared strings).

## 1. The original's form: validate takes `new`, `holder_key` and the sharing key by value

At orig 0x22ee8..0x22fe0, after the CtoState stores, the original makes three copies in this order:
- `new` in 1/7/8/8/9 pieces;
- the sharing key, 32 B to T 0x470;
- holder_key, 32 B to T 0x518.

Then the mayhem test starts. These are the by-value argument temps of the inlined `validate` call.

**t8**, on 16c10e6: 0.56111 at exactly 27,400 B. The form is:
- `let args=&(new,)` placed right after the `CtoState` literal;
- `validate(&st,hopt,fee,args.0,holder_key,sk)`, with `holder_key:Pubkey,sharing:Pubkey` taken by value and `let sk` kept;
- the plain `let (holder_key,_)=find_program_address(..)`.

What t8 reproduces:

- The entry copy sits after the CtoState stores, with the original's instruction pattern: tag spill, `ldxw [+4]/[+1]` 7 B,
  `ldxdw [+8]`, `ldxdw [+16]`, `ldxb [+0x20]`/`ldxdw [+0x18]` 9 B. Then come the sk copy and the holder_key copy, the
  original's order.
- Validate's non-holder `t` is built exactly like orig 0x23618: `mov r2,r8; add r2,0x18; add r8,1; ldxw [r8+3];
  ldxw [r8+0]; ..; ldxdw [r2+0]; ldxb [r2+8]`, with `[8]`/`[16]` taken from the entry-copy SSA values.
  **So validate does read the copy in the original as well.** w13a28's next idea, a copy that validate does not
  read, is moot. The 7/9 B ends come from the `%new` argument only because GVN forwards the readonly argument.
- Why the cut is 7/8/8/9: `Result<Pubkey>` is laid out like `Option<Pubkey>` (tag at 0, Pubkey at [1,33)) with `Error` at
  [8,24). Validate's `Ok(t)` overlay therefore cuts the copied Pubkey at 8, 16 and 24.
- Frame matches with the original: holder_key 0x6a0, mint 0x6c0, val6 0x651, P2 (`sharing_update12.sroa.3`) cut 7/9 at
  0x550/0x560, E32 (`target11`) 0x580.
- Skeleton ratio (registers and frame offsets masked): t8 0.8538 against main 0.8517 (16c10e6), and on 52c0b08
  t8n 0.8568 against main 0.8544. **t8 is closer to the original in structure than main.**
- What it loses: plain 0.5797 against 0.6321; register-masked 0.689 against 0.7582; frame-masked 0.6884 against 0.7121.
  The code shape is right; frame offsets and register assignment are wrong.

## 2. The composites (16c10e6 unless marked)

| trial | form | ratio | bytes |
| --- | --- | ---: | ---: |
| main 16c10e6 / 52c0b08 | | 0.62043 / 0.62103 | 27,400 |
| t1 | b1: validate reads `args.0` (args at main's spot, before CtoState) + plain PDA | 0.56515 | 27,472 |
| t2 | v1 alone (holder_key by value) | 0.55764 | 27,360 |
| **t3** | b1 + v1 (sk -0x470, hk copy -0x518, pieces 0x65d/0x660/0x900/0x668/0x670) | **0.57271** | 27,408 |
| t4 / t5 | t3 with args after CtoState (t5 without plain PDA) | 0.43684 / 0.42876 | 27,504 |
| t6 | args after CtoState + validate reads args.0 + plain PDA, no v1 | 0.53021 | 27,344 |
| **t8** = t14 | args after CtoState + validate reads args.0 + holder_key and sk both by value + plain PDA | 0.56111 | **27,400** |
| t8n (52c0b08) | t8 | 0.56081 | 27,400 |
| t7 / t9 / t12 | sk passed as an inline `a.sharing_config.key()` argument (orig copy order new, sk, hk) | 0.437-0.438 | 27,504 |
| t10 / t17 / t16 | by-value keys without the copy / t8 without the copy | 0.517 / 0.555 / 0.539 | 27,360-27,416 |
| t11 / t13 | t8 without plain PDA / t8 with args at main's spot | 0.53235 / 0.52778 | 27,400 / 27,408 |
| **t22** (52c0b08) | t8 + `quote_locked:global_quote(..)` inline in the CtoState literal (creator, max_fee first) | **0.57305** | 27,544 |
| t26 (52c0b08) | t22 with bools in the original's load order (cashback, holder_reward, mayhem) | 0.57275 | 27,544 |
| t20 / t21 / t23 (52c0b08) | bools or quote_locked before `creator` in the literal | 0.527-0.534 | 27,744-27,792 |
| t24 / t25 / t27 (52c0b08) | inline quote_locked on main / t22 with v1 only / t1 with inline quote_locked | 0.559 / 0.544 / 0.542 | |

| t28 (52c0b08) | t8 + `let (cb0,hr0,my0)=(..)` (curve bools read before `global_quote`, the original's entry order) | 0.53401 | 27,744 |
| t29 (52c0b08) | t22 + the bool locals | 0.57284 | 27,536 |
| t30 / t31 / t32 (52c0b08) | t28 / t8 / main + w13a17 IN296. It no longer outlines `to_string` (157 calls) | 0.526 / 0.458 / 0.523 | |

- **t28 is the pressure lead.** Reading the bools before `global_quote` and copying `creator` after the call is the
  original's entry order. t20, t21, t23 and t28 all give the same tokens. Results:
  - 311 spill reloads, the closest to the original's 330 (main 304);
  - the mayhem flag stays in a register (`mov r2,r6; jne r2,0`, like orig 0x22fe8);
  - the original's dead reload pair after the hk copy appears.

  It costs +344 B. That is +43 instructions of spill code spread over the function, and it makes a 108-instruction
  `to_string` error chunk move (orig 0x27e10-0x28010, skeleton 64 -> 0). That fits the w12 residual "outlined to_string
  must be repaid by faithful data flow". A form that outlines 307/312 on current main would be the counterpart; w13a17's
  IN296 no longer does that (t32).
- The 0.43 collapse (t4, t5, t7, t9, t12) is a block-layout change: a 749-instruction chunk at 0x24c8 moves, and orig regions
  0x25210-0x26210 match nothing. It appears with v1 or an inline key when args comes after CtoState, but not with V2
  (holder_key and sk both by value, `let sk` kept).
- t22 keeps t8's frame and improves the entry. Its creator loads are ascending (`ldxdw [r0+0..0x18]`, like the original's
  `[r9+0..0x18]`), and its frame-masked ratio is **0.7183, above main's 0.7121**. It is still 144 B larger and 0.048 lower.

## 3. Why it loses: register allocation, not the frame, and the copy is not a pressure source

- Frame ceiling: a single-edit frame scan (`mv`/`nolt`, 234 items each, `iredit.py scan`) on each composite:

  | composite | base | best single edit |
  | --- | ---: | ---: |
  | t3 | 0.57271 | 0.57421 |
  | t8n | 0.56081 | 0.56171 |
  | t22 | 0.57305 | 0.57395 |

  A 24 B stand-in before holder_key on t3 (`padins.py`) gives the original's val6..mint frame exactly: 7 B 0x658,
  9 B 0x668, x24 0x680, holder_key 0x6a0, mint 0x6c0. It scores 0.54238 (worse).
- Spill reloads (`ldxdw rX,[r10-0x8xx..0xcxx]`):

  | | orig | main2 | t3 | t8n | t22 |
  | --- | ---: | ---: | ---: | ---: | ---: |
  | reloads | 330 | 304 | 289 | 292 | 300 |

  The entry copy **lowers** pressure, like v1 does. Its long-lived pieces are not where the original's extra pressure
  comes from. Reloads per 0x800 region: the original has 12/14 in 0x0000-0x1000 against t8n's 4/4, and 11/9 in
  0x1800-0x2800 against 5/3. The first gap comes from the CtoState bools, which the original loads before the
  sharing-key memcmp and spills (0x8e0/0x8e8, reloaded at 0x210/0x258/0x440). Moving the bools earlier in source
  (t20/t21/t23) costs +344 B.
- `fdelta.py`: t8n's spill slots are shifted -24 (t22: -8) across orig 0x2800-0x4800. Main's are shifted 0. The
  skeleton losses are in the AccountInfo clone runs (orig 0x25a10-0x25c10, -36 skeleton tokens for t3), which are
  spill-heavy, so register-allocation driven.

**Remaining source blocker:** the original's greedy-RA state, with more reloads in validate and the clone runs and with
`[16]` of `new` kept in r9 instead of spilled. None of these forms reproduces it. The entry copy, v1/V2 and inline
quote_locked are faithful in structure (skeleton above main) but leave fewer values live. The unmatched pressure source is
upstream of the entry copy: the CtoState bools loaded before `global_quote` and the PDA as the first call. t28 shows
the first one: 311 reloads and an original-like entry. It is paid for with +344 B and a moved `to_string` error chunk, so
it only pays off together with outlining 307/312. The second is w13a32's angle. Combine t22/t28 with that when it lands.

## Tools (tools/)

- `capvar.sh`, `runq.sh`, `rec.py`: w13a28's capture + rx oracle, repointed to this lane (BASE env sets the main).
- `an.sh name..`: reload count + per-0x800 matched tokens of an rx trial.
- `skcov.py a.dis b.dis [regs]`: skeleton (frame, and optionally registers, masked) matched tokens per orig 0x200
  bucket, between two candidates.
- Also used: w13a33 `skel.py`/`drift2.py`, w13a20 `frame2.py`/`fdelta.py`, w13a16 `padins.py`, w12 `iredit.py`.
