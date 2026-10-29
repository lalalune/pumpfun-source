# Finite same-data Rules schedule geometry

Baseline `aaac6d9dcbcc14caa413260eda30350ba876a60b` is a clean main `094a06f1`
branch with probe/source-reference evidence. The 390px case has one causal
failure: both schedule labels split into two text-range lines. The 1280px case
is an already-passing control. Candidate `9dc2b26ab4a1ebc619974ce3fecaad6d9785ad84`
changes only the schedule `dl` class and its scoped `dd` allocation, `flex:1`.
The exact same method then passes 2/2 in 10.3s. Both labels use one line, with no
horizontal overflow and identical API data, date strings, prize text and measured
prize row heights. Full prize/shell/pixel geometry is not claimed.

The standalone source verifier at `5bde170bdc55dda71807d80d84c946d4bdb89ce0`
authenticates the original helper/callers/CSS/HTML and native scoped binding:

```sh
node reconstruction/competition-rules-schedule/verify-source.mjs
python3 reconstruction/competition-rules-schedule/qualification/verify.py
python3 -O reconstruction/competition-rules-schedule/qualification/verify.py
```

All runtime/probe inputs are identical to measured `9dc2b26a`; only README and
that source verifier were added afterward. No runtime result is transferred to
changed code. Frontend typecheck, Prettier and 698 capture/npm/SDK checks pass.

Four public #1751 fixture tools are referenced by hashes, not duplicated or
included as feature ancestry. Preparation checks them before temporary use;
cleanup verifies/removes only the four untracked copies. The current branch's
real Next/native Fastify handler and default synthetic seed are used. The native
key gate is active with a public synthetic child key. No browser JSON fulfillment,
credential inheritance, fake layout property/clock, real account or network
mutation is used. No maintained suite was added for this CSS property.

Raw DOM ranges/data/handler ledgers, PNGs and compressed process/check logs are
retained. Both Next processes exit 0 and their stopped cache was removed.
Verification binds every input to its actual phase and works with optimized
Python. Reference Git blobs must be available as documented in the parent README.
Independent production outputs may be appended with an unchanged-runtime map;
original production API/provider, financial, pixel and milestone parity remain
unqualified.
