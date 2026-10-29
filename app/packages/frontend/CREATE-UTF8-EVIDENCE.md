# Create name/ticker byte limits

The captured Create client validates the name and ticker in **UTF-8 bytes**.
The local draft instead counted JavaScript UTF-16 code units, accepting 11 CJK
characters (33 bytes) as a name and three astral emoji (12 bytes) as a ticker.
Those strings fit the retained native input caps but exceed the actual used
Create validation boundaries.

`node scripts/original-create-utf8.mjs --check` authenticates the captured
registration/ranges and selected physical common chunk from actual Create HTML.
It writes a [proof](../../reconstruction/create-utf8/contract.json) containing:

- Selected `807757` SHA `7094dc3c2113698f06bc9cef420cd9c153d355911226020d467f49a0ad85bf68`, in `6a1606765ef3e83e.js`, exports `W` as `e => new Blob([e]).size`.
- `734638` imports that helper as `eY`. Its `tn` validator uses `eY.W(name)>32` and `eY.W(ticker)>10`, with limits from the selected `586090` factory. Both actual Create handlers call `tn` with current name/ticker state.
- The name/ticker input callbacks separately cap JavaScript `.length` at 32/10. Description admission remains `.length>2000`, rather than the byte helper.

No captured JavaScript executes. This is used frontend validation evidence,
not a claim about every SDK, API schema or on-chain string capacity.

The local helper uses the same native `Blob.size` semantics in both field guards
and user-visible counters. Errors identify UTF-8 bytes so multibyte input is not
mislabelled as too many characters. Inclusive 32/10-byte boundaries remain valid;
no Unicode normalization, transliteration or character-set restriction is added.
The native maxlengths, description's 2000-code-unit count, whitespace-only rejection,
URL policy and all media behavior stay intact. Local whitespace policy remains a
documented narrowing compared with the captured nonempty-string guard.

Combining marks, BOM and surrogate replacement count as their native Blob UTF-8
representation. This draft does not become an encoding/launch eligibility check:
PR #1259's separate exact-SDK unpaired-surrogate rejection is unchanged and not
copied. No SDK source, upload, metadata URI, wallet, signing or chain call changes.

Focused tests exercise exact byte edges, Unicode preservation, existing guards
and the complete draft validator. Browser cases verify the actual form/counters,
error focus, valid boundary JSON, retained native caps and recovery. Same-method
base/candidate evidence and executed gate results are recorded in the PR. Local
screenshots are not production references or full visual-compatibility evidence.
