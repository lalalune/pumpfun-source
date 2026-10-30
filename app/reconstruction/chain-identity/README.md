# Captured application chain identity algorithms

This restores the complete retained factory **646908** as an editable, callable
source adaptation. It was absent as a complete module on base
`094a06f18df738d41e77070c1a009e135671ac1a`. The maintained implementation preserves
all 24 exports and the complete declaration AST. Captured JavaScript, factory
wrappers and original runtime imports are never executed.

The source is the captured Pump.fun script
`evidence/web/objects/1e479323ffe53c14.js`, factory hash
`719f637fc436bde35bcaa1da5eac3057212d49b84331e27068450218041eb6c0`, UTF-16
`[1996,3677)` / UTF-8 `[1996,3679)`. These are source/provenance claims, not a
claim about legal ownership or the original TypeScript filename. Existing
repository and third-party attribution continue to apply.

`contract.json` authenticates the whole capture, exact physical registration,
complete indexed variant set, retained declaration and every export. It also
records actual imports and calls from ordinary **Explore 228998** (`e`, `X`,
`a`) and all four retained ordinary **Search 379705** variants (`a`). Those
consumers require these namespace/coin predicates. Static references establish
use, not an active registration winner or complete original runtime behavior.

This contribution adds no backend chain support, product UI, network request,
watchlist/account write, token-detail feature or deferred-perps implementation.
The larger Explore/Search owners, authentication, providers, remote state and
their unrelated dependencies remain external. Existing namespace and NEAR
pattern fragments in `positions-by-mint` and `notification-navigation` are
credited unchanged and are not newly recovered behaviors.

```js
import { createChainIdentity } from "./client.mjs";

// One instance corresponds to one initialized original module namespace.
const identity = createChainIdentity();
identity.Y(" 0xAB "); // padded lowercase Starknet-shaped identifier
identity.U("eip155:8453"); // "base"
identity.a({ chain_id: "near:mainnet" }); // true
```

The original export keys are retained instead of inventing original names:

| Exports | Preserved behavior |
| --- | --- |
| `H`, `c`, `l` | EVM namespace map, ordinary chain names, expanded names |
| `J`, `W`, `d`, `z`, `h`, `Q` | TON/Starknet/NEAR namespaces and names |
| `Y`, `V`, `M` | Trim/pad/lowercase Starknet normalization, canonical shape, distinction from a 40-digit EVM address |
| `U` | Trimmed EVM namespace/numeric-ID reverse lookup |
| `C`, `L`, `_`, `B` | Exact supported non-EVM namespace predicates |
| `e`, `X`, `a` | Exact `coin.chain_id` predicates |
| `n`, `R`, `u` | Broad NEAR account regex, stricter typed NEAR-input classification, TON EQ shape |
| `f` | Unchanged six/four UTF-16-code-unit abbreviated label |

Important original quirks remain: `U("toString")` returns the inherited
function, `U("constructor")` returns `Object`, and `U("__proto__")` returns
`Object.prototype`. The reverse map is an ordinary object. The exported map and
arrays are mutable; editing the EVM map later does not rebuild its reverse map,
and editing the ordinary-chain list does not alter the expanded list. New
instances initialize independent values. No null-prototype conversion or
additional validation is introduced.

The normalization ceiling is the captured first-two-hex-digit heuristic, not
field-prime validation. TON recognition checks only the EQ-shaped string, not
checksum or account existence. `n` uses JavaScript regex coercion while `R`
requires a string; their length and `0x` rules differ. Coin predicates read
`chain_id` directly and throw for null. These behaviors are preserved and
tested, not strengthened into an address-validation or financial guarantee.

From `app/`:

```sh
node reconstruction/chain-identity/recover.mjs --check
node --test tests/chain-identity.test.mjs
```

`--write` regenerates only `client.mjs` and `contract.json` after source review.
The seven finite tests exercise the maintained algorithms directly, including all
24 exports, every mapped EVM chain, 256 high-byte normalization boundaries,
NEAR/TON distinctions, object/coercion quirks, per-instance lifecycle and a
synthetic ordinary-coin identity projection. They also regenerate and compare
the complete source and five physical consumer bindings, and reject an actual
maintained-adapter ceiling mutation through the source-check CLI. No mock decoder,
production request, browser UI, remote service or original-runtime oracle is
used or claimed.
