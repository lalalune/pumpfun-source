# Restore the captured reference-list markers

The archived Privacy and Terms documents contain eight unordered lists:
43 items in Privacy and 14 in Terms. Every captured list explicitly has the
`list-disc` class. Both HTML documents link the authenticated stylesheet whose
exact rule is `.list-disc{list-style-type:disc}`. The typed local renderer
preserves the list/items and text but intentionally drops captured classes.
Its reference stylesheet set layout/padding without restoring the markers
after Tailwind's `list-style:none` reset.

The source correction adds only this scoped rule:

```css
.reference-document ul {
  list-style-type: disc;
}
```

This restores an observed source declaration. It changes no document wording,
generated blocks, links, heading IDs, tables, global styles, table of contents
or anchor policy. The existing mobile-anchor work in #1462 stays separate.

## Actual healthy before and after

The finite inspection ran unchanged at 1280px and 375px for Fees, Privacy and
Terms: **six healthy pages per stage**. Both runs exited 0 intentionally.
They validate 200 responses, document titles, heading/table/list/item counts,
no page overflow and no console/page errors or forbidden requests, then record
actual computed styles and screenshots. There is no new maintained test suite
or CSS-rule assertion. The defect is the measured absence of the declared
markers in an otherwise healthy page, not an assertion failure.

| Revision | Marker observations |
| --- | --- |
| Unchanged main `094a06f18df738d41e77070c1a009e135671ac1a` | All eight document ULs and first LIs compute `none` at both widths. |
| Fixed source `4a76228f44c5f44fa8aa7957985978cd2912330d` | All eight compute `disc` at both widths; screenshots show the bullets. |

The paired records preserve first-item text, counts, padding, display, marker
position and recorded document widths. Fees remains a healthy seven-table
control with no document lists. Full before/fixed observations, source hashes,
controller/measurement hashes and raw compressed logs are retained here.
The measurement/controller bytes are identical across the two runs; only the
source rule, output destination and stage label differ.

Published screenshots show Privacy at 375px and Terms at 1280px, before and
after. The other four screenshots remain privately retained with their hashes
in `VALIDATION.json`; the JSON covers both documents at both widths. These are
local settled rendering observations, not original pixel parity, exhaustive
viewports, other browser engines, screen-reader results or accessibility
certification.

## Exact captured witness

`SOURCE-WITNESS.json` pins whole HTML/CSS objects, their manifest identity,
stylesheet links, and raw UTF-8 byte ranges/hashes for all eight list opening
tags and the disc rule. The existing authenticated extraction is credited as
prior work; this PR does not claim to newly recover those documents.

- Privacy object: `evidence/web/objects/ecde4a73aafb477e`, SHA-256
  `babc5695f31c07f667f321e2c4456ae37e478bc77eac77ca2b724878daf13cc7`.
- Terms object: `evidence/web/objects/1e06d459af096a65`, SHA-256
  `f6ffed345dfb40e8f8fc4fec31b522e10663d19783508849ba75642b16dd4be2`.
- Linked CSS: `evidence/web/objects/4a341ff6a9551721.css`, SHA-256
  `8bda96ca39398a46befb900a2d43a4e695ff9975ce6c4bb83c1f45bb47eced93`.

The witness procedure reuses the maintained extractor's manifest/object
authentication and selects the unique document main by its direct title,
excluding captured application chrome. It reads original HTML/CSS as data and
never evaluates captured JavaScript or contacts the live site. Existing
heading/inline/link/table extraction and generated content stay byte-identical.

## Repeat the finite inspection

Use the repository's pinned installed dependencies. Port 3027 must be free;
the controller starts only its own ordinary Next development process and
stops that process group afterward. Copy `run.py` and `measure.mjs` outside
the checkout before changing between the base and fixed revisions, so the
same procedure is available for both. Use fresh output directories:

```sh
python3 /path/to/run.py --repo /path/to/checkout --output /tmp/reference-before --stage baseline
python3 /path/to/run.py --repo /path/to/fixed-checkout --output /tmp/reference-after --stage fixed
```

The base and fixed checkout must each be clean. Expected: both processes
exit 0, all six document-health checks pass, and actual marker observations
change from `none` to `disc`. No route/body fulfillment, injected styles,
original capture execution, wallet interaction or mutation is used. Script
hashes bind the actual measurements; paths/output labels are explicit in the
retained result files.

Regenerate the captured witness:

```sh
python3 source-witness.py /path/to/checkout > /tmp/reference-source-witness.json
```

Existing checks passed before and after:

```sh
cd app
corepack pnpm test:references
cd ..
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

Reference checks comprise deterministic extraction freshness, 6 Python tests
and 9 existing Node tests. Required repository checks pass 9 captures and 10
tooling tests. This CSS-only change adds no test registration/configuration,
dependency, SDK or backend change. `MANIFEST.json` binds every packet byte and
both raw/compressed log hashes; later packet commits preserve measured CSS.

Historical capture status remains explicit on the pages. Current legal
authority, interpretation, fee calculations, production build, live services,
full visual parity and compatibility/feature milestones remain unqualified.
