# w14a30-cto-shareauthport: port of #3277 (sharing CPI authority AccountInfo literal) onto main f100a59

Target `0x22a10` `admin_cto::execute`. Base: origin/main `f100a59c1` (ratio 0.6423, 3173 slots).

Port of the external PR #3277 (w14a24-cto-shareauth, by kutluhaneth46), which showed 0.6414 -> 0.6426 on 7e6aa9c.

## Result

| | main f100a59 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.6423 | **0.6435** |
| slots_diff | 3,173 | 3,173 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `9c745887ccab74089ffe1e12af01486c483965013348b93ee65516619319e42c` |

## Change

In the `admin_cto_sharing_config` CPI, `authority:a.admin_set_creator_authority.to_account_info()` becomes an
eight-field `AccountInfo` literal that binds the lamports/data Rc clones to locals first, then stores the fields in the
order rent_epoch, owner, lamports, key, is_writable, is_signer, executable, data.

Ledger key: `0x22a10-w14-f100a59-shareauthport-port3277-v1`.
