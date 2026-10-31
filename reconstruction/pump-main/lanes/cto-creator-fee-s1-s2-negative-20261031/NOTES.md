# S1–S3 fee-boundary counterexamples

The achieved local phases did not guarantee byte progress. S1/S2 moved the
intended creator-value phases before fees but retained a common shared gate
and outlined sweep. S3 restored a private fee-success gate, three fee tests
and inline settings/sweep layout. Native no-loss passed, while normalized CTO
matches fell from 2245 to 1279. Every candidate remains rejected as source
progress; the last CTO window remains unmatched.

These are historical pairs with different controls, not a common-base
one-factor sequence. S1 and S2 are separate children of ECEA; S3 is a child of
13fe. Research patches are retained comparisons, never proposed latest-main
program edits.

| Measurement | Frozen control → candidate | Admitted native phase | Native no-loss | Source decision |
|---|---|---|---|---|
| S1 | ECEA `ecea7021` → `66caa3e2` | creator projection before direct fees; common shared gate; 9,096 B sweep outline | FAIL: 1034 norm/347 raw, 687 raw losses | REJECTED |
| S2 | ECEA `ecea7021` → `5cfe37b1` | pre-fee selected K/C/N reaches consumers; common shared gate; 9,096 B sweep outline | FAIL: 1034 norm/347 raw, 687 raw losses | REJECTED |
| S3 | 13fe `13fe4536` → `65f0162a` | three fee tests/private Some gate; no scoped outline witness | SUCCESS: 1034 norm/raw, all 1035 rows unchanged | REJECTED: target metric |

Both retained controls have 27,400-byte execute bodies and 1034 normalized/raw
membership matches. Original's private fee-Some shared gate is a separate
original-byte observation; it is not a control-table measurement or proof of
an original Rust helper/Result type.

Full cohort identities, 141 source files/142 staged files/236 CORE inputs provenance and exact native
ZIPs are pinned by `inputs.json` plus `s3-inputs.json`. S1/S2 retain their
untouched FAILURE receipts. S3 retains its actual RESULT success; no native
failure receipt is invented. Unchanged membership in an already-unmatched
window does not measure similarity inside that body. S3 VM was held before
launch: 0 runs and no 363-case/runtime claim.

## Completed native observations

Offsets are relative to execute VA 0x22a10 for the named historical ELF;
LDDW occupies 16 bytes. S1's 7/9 fragment projection completes before fee read/
test +ad0/+ad8. Valid Some +1268 and None still join +1270's three-instruction
shared head. S2 selects its K/C/N target before +b28/+b30, preserves it through
packing +1518..1560 and reaches curve/pool consumers. Its valid Some +1328 and
None likewise join +1330's common three-instruction head. Neither achieves the
predicted private gate; both outline the 9,096-byte sweep and lose 687 raw rows.

S3's incoming fee tag is spilled at +8. Its three validation reads/tests are
+9f8/+a00,+1480/+1488,+14d8/+14e0 before prepare +1a98. Selected 32 store arms
finish before those tests. All Some entries can reach private head +17c0;
None entries cannot in the bounded direct CFG. That head's four rows store a
flag, perform the retained byte read, reload shared and branch. No scoped
nonzero validate/sweep symbol, corresponding direct outline call or CALLX is
observed. This does not identify an inliner threshold, original helper type
or surviving full-settings Result niche.

S3's source retains creator/error ordering, both private-reference volatile
reads 334/338 and 772 lines. It returns the six settings together, selects C
only after N validation, and uses original `Some(new)` for sharing. The
selected target32 and sharing Option33 occupy distinct outgoing buffers and
reach the recorded curve/pool/Fees argument/serializer points. The compact
checker verifies selected raw points, target direct-store census and outgoing
argument bridges; it does not replay a complete bytewise provenance/alias
engine. Normally returning calls, ABI register preservation and private owned
buffers remain explicit conditions, not Rust-lifetime theorems.

## Native success, target-metric rejection

The 13fe/S3 bodies each contain 3337 logical instructions, versus 3339 in the
original. The exact maintained method is archived CORE score.normalize,
win.insns/Cand.tokens and SequenceMatcher(None,original,candidate,
autojunk=False). It masks encoded internal-call immediates and section-address
LDDW words, while retaining registers, FP offsets and jumps.

| Original → candidate | 13fe | S3 |difference|
|---|---:|---:|---:|
| normalized matching logical instructions M |2245|1279|−966|
| normalized ratio 2M/6676 |0.6725584182144997|0.38316357100059917|−0.2893948472139005|

This within-CTO metric is separate from official matched-window membership.
The preserved target-metric receipt supports rejection of S3, not a claim
that its native no-loss guard failed or that the private gate caused the
whole-function regression. No compensating source form follows.

## Original value families and prior credit

Original has an early 7/9 validation reconstruction and a distinct late 7/9
entry-new/sharing transport. Its selected K/C/N target instead follows an
8+24 path and later target32/curve packing. Absent reset payload is excluded.
Neither these widths nor S3's 45 B co-transport identifies an original Result/
Try type, tuple size, helper boundary or lifetime. S1's candidate Result
projection attribution comes from its exact source; it is not a width-based
identification of the original late sharing-payload chain.

Exact retained [#3384](https://github.com/lalalune/pumpfun-source/pull/3384)
f1/f2 already project creator Result in execute before a private fee helper;
f3 uses an and_then closure. Their older 2e1379d notes report 9,080 B and sweep
outlining, without the current volatile reads. Exact placement is known;
the historical trial was not rerun. [#3197](https://github.com/lalalune/pumpfun-source/pull/3197),
old OV and related full-settings negatives remain relevant. No novelty,
original-type uniqueness or permission for another helper combination is
claimed. C1's Option-carrier negative stays separate in [#3436](https://github.com/lalalune/pumpfun-source/pull/3436).

## Replay and external diagnostic evidence

The existing 5.61 MB `captures.tar.xz` is byte-unchanged. `S3-captures.tar.xz`
adds only the two normal 13fe43/S345 ZIPs and small native/metric/held records;
it contains no diagnostic trace. Identical 236 CORE inputs reuse the existing
208 archived text/symlink leaves and 28 pinned repository binaries. Both old
raw failures and the empty/unqualified ABI records remain intact.

Run `PYTHONDONTWRITEBYTECODE=1 python3 -B verify.py --repo /path/to/repo`. This stdlib checker reads archived inputs,
source patches, saved score arithmetic, selected raw/CFG joins and the exact
maintained target tokens. It never invokes the compiler, full scorer, IR tools,
objdump or a VM. A packet PASS would authenticate the preserved counterexamples,
not accept any candidate source.

**Extended replay passed once on input commit `649a241324a66768875229682e7487da7c5a4918`**
(tree `60e317153e3233573ab73dae75b64a6128337f09`). Actual stdout is retained
byte-for-byte as `verification-s3.json`; `replay-s3-receipt.json` records the
3.5404 s replay, 9 verified captures and 228 passing tooling tests, with
unchanged 314 local and 5 external inputs for each check. Existing
`verification.json` remains the immutable earlier S1/S2-only replay. Later
receipt/docs packaging changes no executable input and is not the executed
Git SHA. This PASS authenticates the counterexamples; S3 remains source
REJECTED and its standalone VM count remains 0.

Separate diagnostic run 41173731317 uses the same frozen S3 source, with code
identity to normal S3 admitted by 50 checks. Its three files are retained in
the operational own-fork at immutable commit
[`3b6d3a92`](https://github.com/shawkkkkk/pumpfun-source/commit/3b6d3a92da95d6722af3ae3782d3d30d856b6c15):

| External file | SHA256 |
|---|---|
| [raw diagnostic ZIP](https://github.com/shawkkkkk/pumpfun-source/blob/3b6d3a92da95d6722af3ae3782d3d30d856b6c15/reconstruction/pump-main/lanes/source-s1-native-retained-20261031/s3-diagnostic-raw-artifact.zip) | `10485e815b0df43c8a2124c60ad02757b91acb7742ef9a57308fce9da9a96d09` |
| [admission records](https://github.com/shawkkkkk/pumpfun-source/blob/3b6d3a92da95d6722af3ae3782d3d30d856b6c15/reconstruction/pump-main/lanes/source-s1-native-retained-20261031/s3-diagnostic-admission.tar.xz) | `de57acdf0b2b71bab8cb274215c830b75ba195ad6368686d99962c20ee2c7d16` |
| [bounded causal records](https://github.com/shawkkkkk/pumpfun-source/blob/3b6d3a92da95d6722af3ae3782d3d30d856b6c15/reconstruction/pump-main/lanes/source-s1-native-retained-20261031/s3-diagnostic-causal.tar.xz) | `5e8d92f32906fd874f66f84ffa7567db4390ace2702cb3668faf228ba89db736` |

Those external records place selected-target32 and separate incoming-N
sharing-suffix13 in a 45-byte object before the earliest retained
JumpThreading snapshot. Two 45-byte copies through an intermediate persist
across both captured pairs; only the unsampled last-JT-to-optimized interval
bounds removal of that intermediate. The surviving copy already exists
before register allocation, and 30 final machine operations join the normal
native witness around +19f0. These observations do not identify the responsible
unsampled pass, an original Result/type or lifetime, or a cause of the global
966-match decrease. They justify no new source variant.

The external trace is neither included nor replayed by this portable packet.
Its diagnostic fields/marker remain the frozen pre-retention omission
declaration; they do not authenticate these external diagnostic findings.

No latest-main executable qualification, runtime equivalence, source gain,
compiler-lifetime explanation, size repayment or next source correction is
established. The extension remains research on the same already registered PR3483.
