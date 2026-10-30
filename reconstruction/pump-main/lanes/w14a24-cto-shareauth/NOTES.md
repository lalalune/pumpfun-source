# w14a24-cto-shareauth: sharing CPI authority AccountInfo clone (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute`. Base: origin/main `7e6aa9c` (ratio 0.6414).

## Result

| | main 7e6aa9c | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.6414 | **0.6426** |
| slots_diff | 3,174 | 3,174 |
| bytes | 27,400 | 27,400 |
| normalized / raw vs baseline | | 0 losses |
| differential | | 363 cases, 0 mismatches |

## Change

In `admin_cto_sharing_config` CPI, replace
`authority:a.admin_set_creator_authority.to_account_info()`
with an explicit eight-field `AccountInfo` clone that binds lamports/data Rc
locals once each, then stores rent_epoch/owner/lamports/key/... in that order.

Other sharing clones (pool_authority, global, mint, event_authority) and the
transfer vault ATA clone already on main are unchanged.

## Evidence

- Fresh-main unstripped: `e8059a708baf122c743347e8b67589ccf164056b4b6af69d9ab74395fdde7b60`
- Candidate unstripped (two builds): `7591ad00d51398f1996a42f54704081451a6c5cc593adceccd4a7151992a7c4b`
- Candidate runtime: `0ce3f042859d9fab62f8363eed24347c6f36dbe8340f43f114799e2dd1ee1d41`

Partial similarity gain only. Not a complete-window match or whole-ELF identity.
