# Native web competition row display

The maintained web row showed rank 0 as `0`, colored zero PnL as a gain and omitted
positive-value prefixes. The complete captured `590407.X` uses a dash when rank
is not positive, neutral text when PnL equals zero, gain/loss text for its sign,
and `+` only when the supplied value is positive. This bounded native-page
correction adapts those three display decisions and gives the defensive dash
the native English accessible label “Not ranked”. It does not assign a rank,
calculate PnL, infer eligibility or remove/reorder rows.

The original `139209` DTO describes rank 0 as not ranked. It also explicitly says
struck entries are excluded from ranked arrays and remain available in own-entry
and detail contexts. Therefore rank 0 fixtures here prove a currently admitted
**local defensive display boundary**, not that the documented ranked API returns
unranked/struck users. Zero/positive/negative PnL rendering uses separately supplied
positive ranks. No server contract or private backend compatibility is inferred.

The existing native Intl formatter, realized/unrealized facts, API/types,
projection, ranks, row identity and supplied values remain unchanged. Negative
zero retains the existing Intl `-$0.00` text but receives neutral tone because
it equals zero in the original comparison. A tiny positive value still has a
positive prefix even if the existing formatter rounds its amount to zero.
The theme uses existing native positive/negative classes and inherited primary
text; this is not a pixel-identity claim about original theme/provider internals.

The source gate authenticates the complete original row context and its used
rank/tone/prefix expressions, prefix-value ownership, the original rank/struck
DTO descriptions, every selected physical factory origin and original byte/
UTF-16 ranges. It checks the actual native expressions, unchanged Intl initializer
and existing row key/fact bindings. The baseline excerpt is the complete actual
native function at the recorded base/range. Captured factories remain inert.
No dependency on the unaccepted participant/viewer/coordinator port stack is
introduced; those source discoveries receive attribution and no new recovery
count. The display gate permits independent additive UI such as the separately
qualified prize badge rather than freezing an unrelated whole-file layout.

Run from `app`:

    node scripts/verify-competition-entry-presentation.mjs --check
    node --test tests/competition-entry-presentation.test.mjs tests/original_source.test.mjs
    pnpm -r typecheck
    python3 scripts/verify-evidence.py

The source negatives restore rank-zero, zero-gain and prefix-boundary errors and
are rejected. Real React SSR compares the exact base excerpt to the actual
maintained module with only its existing private row exposed for the test;
product row bodies are not replaced. It covers positive ranks with zero/gain/
loss, defensive rank 0, negative zero, sub-cent rounding, amount precision policy,
identity, facts and order. Existing client admission preserves finite supplied
values and rejects nonfinite values. Source and browser transport fixtures are
explicitly synthetic; no profile, session, key, signing or remote service is used.

The two finite actual Next cases use the full maintained `/leaderboard` page at
390/1280px, synthetic local read envelopes and foreign/mutating request blocking.
The final causal baseline fails at valid rank 1 zero PnL still having the positive
class, before any defensive rank0 assertion. The same final method passes both
fixed cases in 16.1s, including valid rank 2 positive/rank 3 negative amounts and
no horizontal overflow. Exact source/tree bindings, raw final logs and four
actual before/after PNGs are retained in `qualification/`. Earlier three-row
and defensive-first methods remain private setup evidence, not final proof.
An initial admission test used a nonstandard source label and was corrected to
the existing required label without product changes; its raw failure is retained.
The final source/SSR 15 tests, all three workspace typechecks and 698 capture/npm/SDK
integrity checks pass.
No full production build, full app/browser suite or original provider parity is
claimed by these finite cases.
