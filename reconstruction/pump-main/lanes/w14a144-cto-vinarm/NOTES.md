# w14a144-cto-vinarm: per-arm sharing_update local, and the vin/payload-local family priced on main, O and O312

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base main ebe5387
(0.67316, 3,123 slots). Continues w14a123-cto-origfill (#3593) next ideas 3 and 4. Ledger approach `vinarm`, keys
`0x22a10-w14-ebe5387-vinarm-*`.

## Landable change (pl2)

The execute-level sharing tree assigns `sharing_update` per arm instead of returning it in the tuple:

```rust
let mut sharing_update:Option<Option<Pubkey>>=None;
let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}
  else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}
  else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};
```

Same semantics (holder arm `Some(None)`, shared non-holder `Some(new)`, not shared `None`). Line count unchanged.

| build | admin_cto ratio | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main ebe5387 | 0.67316 | 3,123 | 27,400 | 1034 / 1034 | |
| pl2 (measure.sh, unstripped sha e9df54086dcfc8ca) | **0.67346** | 3,124 | 27,400 | 1034 / 1034 | none |

Runtime differential: 363 cases, 0 mismatches. The change is local: the fee/flag init block at 0x17d0 is rescheduled
(the `[r10-2272]` store moves up) and the 0x19c0 sharing-payload copy runs in the other piece order.
