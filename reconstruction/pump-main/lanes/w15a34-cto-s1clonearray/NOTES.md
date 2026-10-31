# w15a34-cto-s1clonearray: s1 clone-at-store source forms (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: w15a18-cto-s1greedy (#3742) next idea 1. s1 (all seven `AdminCtoSharingConfig` fields as plain
`to_account_info()`) passes main with 6 greedy decisions (M 2,255 @27,352), but those decisions need the E2/E3/E5/E6 clone
pieces to carry 3x or more spill-weight density than their evictors. This lane asked whether an ordinary source form that
makes each clone's pieces short-lived (array/tuple binding, per-clone blocks, Vec push, account_infos next to the metas)
changes those densities. No codegen-forcing construct was used (BRIEF RULE).

Base: main 9120883a9 (admin_cto 0.67376, 3,124 slots @27,400, M 2,249 free). Branch merged to origin/main 1cc487926
(programs/pump/src unchanged). Ledger: approach `s1clonearray`, keys `0x22a10-w15-9120883-s1clonearray-*`.

**Result: notes only, no source change. The s1 clone-at-store family is closed.**
- Every stack form that keeps the anchor `admin_cto_sharing_config` call (array literal, tuple, 8-element array with the
  CpiContext program, whole-array binding, per-field blocks, per-element blocks) compiles to the s1 clone run token for
  token. SROA scalarises the bound clones, so each piece is still loaded at its clone and stored into the CpiContext at the
  call. 56 of 64 role-matched pieces keep the exact s1 initial spill weight, and the other 8 move by at most 0.6%.
- These forms only lose things. Each one drops the 5 B CpiContext.program padding copy that s1 and the original both have
  (orig 0x4a08-0x4a20), which costs 32 B and 3-10 M.
- The only measured form whose pieces really are short-lived is a `Vec` push. It stores each piece at its def into the heap
  element. That is not what the original does (the original spills at def and reloads at the call), and it costs 205 M and
  9 extra calls.
- Manual `invoke_signed` forms (account_infos built next to the metas) are excluded by construction. They remove the only
  caller of three windows that are byte-matched today.
- Evaluation order is the only lever that moves the densities by integer factors. Moving the CpiContext program clone last
  makes its own pieces x3.0-4.1 denser and shrinks every struct clone uniformly (0.62-0.91). That is the literal-order
  family w15a18 already screened (best 0.654), and its own greedy ceiling (M 2,199) is below s1's.
- New RA target for s1 (no source lever found): two weight decisions give M 2,256 @27,384 (0.67606), against main's free
  2,249 @27,400. They are weight x3 on the CpiContext program clone's key and on the global clone's data Rc pointer. This
  is cheaper than w15a18's 6-decision cell and only 16 B short. The binding forms reach only 2,245 with the same two
  decisions.
- The `sharing_update` arm's branch probability is not a lever either. main is at its optimum at the 50/50 that `match`
  gives, and s1 gains at most +20 M with the arm made likely (IR probe only).

## 1. Forms and measurements (raw-IR capture + opt + llc on 9120883; `tools/gen.py`, `tools/runq.sh`)

`prog` is the CpiContext program clone, `a.pump_fees.to_account_info()`. Free cell = SDK-equivalent llc as built.
Role weights compare each form's 64 clone pieces (8 clones x 8 AccountInfo fields) with s1 (`tools/rolew.py`).

| form | source of the sharing CPI | fn.bin class | ratio | bytes | M free | role weights vs s1 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| s1 | `new_with_signer(prog, S{f: a.x.to_account_info(), ..})` | = w15a18 s1x | 0.64319 | 27,376 | 2,146 | ref |
| a7p | `let prog=..; let [pa,..,pr]=[..7 clones..]; .. S{pa,..}` | A | 0.64268 | 27,344 | 2,143 | 56/64 identical, max 0.6% |
| t7p | same with a 7-tuple | A | 0.64268 | 27,344 | 2,143 | same |
| a8 | `let [prog,pa,..,pr]=[..8 clones..]` | A | 0.64268 | 27,344 | 2,143 | same |
| t8 | 8-tuple | A | 0.64268 | 27,344 | 2,143 | same |
| a7w | `let accs:[AccountInfo;7]=[..]; let [..]=accs;` | A | 0.64268 | 27,344 | 2,143 | same |
| a7b | array elements as `{let x=a.f.to_account_info();x}` | A | 0.64268 | 27,344 | 2,143 | same |
| blk | struct fields as `{let x=..;x}`, prog still a direct temp | A + 4 val-store insns | 0.64268 | 27,344 | 2,143 | same |
| a7 | `let [..]=[..7..];` then `new_with_signer(a.pump_fees.to_account_info(), ..)` | = w15a18 ctxafter + 4 insns | 0.64387 | 27,344 | 2,147 | prog x3.0-4.1, struct clones 0.62-0.91 |
| vec7p | `Vec::with_capacity(7)` + 7 `push` in field order, `try_into::<[AccountInfo;7]>().unwrap()` | own | 0.58192 | 27,416 | 1,941 | pieces stored at def into the heap |
| manual invoke | `Instruction{accounts: metas, ..}` + `invoke_signed(&ix, &[infos..], seeds)` | not built | - | - | - | removes the only caller of 3 matched windows |

- All stack forms keep 157 calls (as the original and s1). vec7p has 166.
- True LCS against s1, unmasked (`lcschunk.py`): class A is -9 (-8 in the 0x4800 chunk, where the padding copy sits, and
  -1 at 0x800). The clone-run chunks 0x3800 and 0x4000 are identical to s1. vec7p is -258 (0x3800 -33, 0x4000 -68,
  0x4800 -38, 0x5000 -60, 0x5800 -52).
- Excluded windows (baseline `score.json`, all normalized and raw matched): `pump_fees::cpi::admin_cto_sharing_config`
  0x116718 (4,040 B), `AdminCtoSharingConfig as ToAccountMetas` 0x118360 (1,472 B) and `.. as ToAccountInfos` 0xca628
  (1,944 B). The original's execute passes the CpiContext by pointer to the first one (orig 0x4a48-0x4a78:
  r2 = r10-0x2d0, r3 = r10-0x651, `call`), so any form that bypasses the anchor cpi function loses three windows and shifts
  every later function.

## 2. Why the stack forms cannot change the pieces

Post-opt IR (s1 vs a7p, `diff` of the slim modules):
- Each clone is a chain of field loads and Rc `inc_strong` blocks that leave SSA scalars. The CpiContext argument memory
  (`%_120`, 424 B) gets all of its field stores at the call (IR ascending, emitted descending by the scheduler). Rust evaluates
  all aggregate operands before it builds the aggregate, and SROA removes every intermediate binding (array, tuple, block
  local). So no binding form can put a store next to a clone.
- The only IR differences are a `[5 x i8]` SROA slice (`%_121.sroa.11`) with its 5 B memcpy into `%_120+67`, and where
  `lifetime.start(424)` of the argument memory sits. The slice is the CpiContext.program padding, copied when the
  `new_with_signer` result moves into the call argument.
  - s1 keeps it: `ldxw r1,[r10-0x450]; stxw [r10-0x28d],r1; ldxb r1,[r10-0x44c]; stxb [r10-0x289],r1`. These are the
    original's exact instructions and slots at 0x4a08-0x4a20; main has them too, at 0x49b8.
  - Every binding or block form drops it, even blk, where the program is still a direct temp. Changing the MIR shape
    around the CpiContext temp is enough.
  - So the plain temp form is the faithful one. Other lanes should not bind the CpiContext program or the account
    struct for this CPI.
- Initial greedy weights (RAPRIO_LOG `Q` lines, `tools/rolew.py`): for class A, 56/64 pieces are identical and the other 8
  are within 0.6% (the CpiContext program pieces, whose interval grows by the 32 B no longer copied). w15a18's decisions
  needed x3 on specific pieces.

## 3. RA ceilings (private RAPRIO llc from w15a18; `tools/ceil.sh`)

Pool: the vregs defined in the sharing arm (`tools/famvregs.py`, 108-110 per form) x {top, bottom, cascade, weight x3,
weight x0.3}, 540-550 singles. Forward climb on free M with the top 40 singles, up to 6 rounds.

| form | free M @ bytes | decisions | ceiling M @ bytes (ratio) |
| --- | --- | --- | --- |
| s1, this pool | 2,146 @27,376 | weight x3 on %290 (CpiContext program clone key, `LDD %289,0`), weight x3 on %319 (global data Rc ptr, `LDD %316,16`); the climb then stops | **2,256 @27,384 (0.67606)** |
| s1, w15a18's 6 decisions replayed | 2,146 @27,376 | casc 309, 348; top 321, 334; bottom 354, 339 | 2,256 @27,352 (0.67646) |
| a7p class (all stack binding forms), this pool | 2,143 @27,344 | weight x3 %290, cascade %319 (same two values) | 2,245 @27,352 (0.67316) |
| a7p class, s1's 2 decisions replayed | 2,143 @27,344 | same vreg numbers and roles | 2,245 @27,352 |
| a7p class, w15a18's 6 decisions replayed | 2,143 @27,344 | | 2,246 @27,320 (0.67387) |
| a7 (CpiContext program clone last), this pool | 2,147 @27,344 | bottom 1244, top 1218, bottom 1636 (stops) | 2,199 @27,368 (0.65917) |

Main for comparison: M 2,249 free @27,400. w15a18 measured 2,251 after a two-step climb with its own pool, and the brief
gives 2,260 @27,384 for 5 decisions.

- New for s1: two weight decisions are enough for M 2,256, at 27,384 B (16 B short, where w15a18's 6-decision cell is 48 B
  short). True LCS against main for that cell: unmasked +5 (chunk 0x4000 +12) and rfj +32 (s1 alone is already rfj +22:
  its clone-run skeleton is closer to the original than main's literals).
- The two decisions change nothing in the register budget. The accounts pointer is still in r5 and r9 still carries pieces,
  so this is a greedy coincidence, not the original's allocation. Both values have one def and one use (plus the Rc pair
  for %319), so no ordinary source gives them 3x weight. The only density lever, evaluation order, is a7: it moves the
  wrong pieces and caps at 2,199.
- Spill-slot relabel bound (w15a08 `relab.py` bestperm, spill set from the binary, `tools/mperm.py`; M -> Mperm): main
  2,249 -> 2,292; s1 2,146 -> 2,202; a7p class 2,143 -> 2,192; a7 2,147 -> 2,203; vec7p 1,941 -> 1,990; s1 + 2 decisions
  2,256 -> **2,293**; a7p + 2 decisions 2,245 -> 2,287. Even s1's best greedy cell only ties main once slot colours are
  free.
- True LCS against main in 0x200 chunks over 0x3e00-0x4800 (unmasked, `lcschunk.py --sz 0x200`). Main per chunk:
  33, 30, 31, 10, 37. Deltas:
  - s1 and the a7p class (identical): -3 -2 -15 +2 -16;
  - a7: -21 0 -23 +3 -15;
  - s1 + 2 decisions: +2 -1 +4 +17 -8.
- Arm branch probability (IR probe only, `tools/bwprobe.py`, `!prof` on `br i1 %578, label %bb35, label %bb37`, the
  `sharing_update != None` test). s1 gains at most +20 (arm 2:1 to 100:1: M 2,166; 5:3: 2,162) and loses when the arm is
  unlikely (1:2: 2,108; 1:8: 2,036). Main is at its optimum at 50/50 (2:1: 2,199; 5:3: 2,191; 1:2: 2,205; 3:5: 2,242).
  50/50 is also the only probability an ordinary `match`/`if let` gives this test. Closed.

## 4. What the s1 gap is, in the original's own terms

In the original, from the sweep call to the event (orig 0x3c38-0x5030):
- `swept` stays in r9 (`ldxdw r9,[r10-0x828]` at 0x3c40, next use `stxdw [r10-0x218],r9` at 0x5030). It crosses the
  whole sharing arm and the pool CPI, and the clone run never touches r9.
- The accounts pointer is reloaded from its spill slot before every clone (`ldxdw rX,[r10-0x8d8]` at 0x3d88, 0x3e30,
  0x3f38, 0x4050, 0x4178, 0x42a0, 0x43c8, 0x44f8).

s1 and main do the opposite. The accounts pointer holds a register through the run (s1 r7, main r5), r9 carries clone
pieces, and `swept` is spilled at def (main `stxdw [r10-0x968],r3`). The clone run itself already has the original's
skeleton in s1: each clone's owner, rent and flags load in the next clone's first block.

So the s1 RA gap is a one-register budget question (accounts pointer vs swept). It is not a question of the pieces'
relative densities, and no clone-run source form can answer it. w14a85-cto-s1reload (#3420) priced the accounts-pointer half
as an IR probe (s1 +0.018, still below main).

## 5. Tools (`tools/`)

- `gen.py`: writes the EDITS files for every form above from the current sharing-CPI line.
- `runq.sh`: capture queue (copy of w15a18 `capvar.sh` + `rx.py` paths), one build slot per worker.
- `rolew.py <ref> <var>..`: role-matched initial greedy spill weights of the 64 clone pieces. Roles are (account, occurrence,
  field) from the pre-greedy MIR. Use it to show without a build whether a source form changes RA inputs.
- `wcmp.py`: the same by vreg number (valid when the arm's IR order is unchanged).
- `famvregs.py <pregreedy.mir>`: vregs defined in the sharing arm (the climb pool).
- `cellf.sh`: free cell only (about half the cost of w15a18 `cell.sh`; identical free numbers).
- `ceil.sh <name>`: family singles + forward climb.
- `mperm.py name=fn.bin ..`: w15a08 relabel bound on function blobs (spill set from the binary).
- `bwprobe.py <m.ll> '<br line>' a:b ..`: attach `branch_weights` to one branch of a slim module and print free cells
  (IR probe only).

The private llc is `~/.cache/pumpfun-reconstruction/lanes/w15a18-cto-s1greedy/llvmb/bin/llc` (w15a18 `build.sh`).
Slim post-opt modules kept for reuse: `~/.cache/pumpfun-reconstruction/lanes/w15a34-cto-s1clonearray/rx/{m0,s1,a7p,a7}/m.ll`
(captured on 9120883; `admin_cto.rs` is unchanged on 9bd38c7d5, which only touched buy_v2/sell_v2/v2_native_payments). m0
reproduces main exactly (`eq_main`). `fn.bin` is kept for every form.

## 6. Next ideas (not this lane's angle)

- The s1 gap is the register budget in section 4. A source lever would have to make `swept` (phi of 0 and the sweep
  result) worth a callee-saved register across both CPIs, or make the accounts pointer's arm piece lose. Either changes the
  whole region, so price candidates with `rolew.py`-style weight dumps of those two vregs before spending builds.
- s1 is 24 B short (27,376). Its best greedy cell (2 decisions, M 2,256) is 16 B short. Any s1 lead still needs a
  faithful 16-24 B repay (`$SWARM/w11/sizeknobs-cto.json`), and the two weight decisions still need a source mechanism.
