# Original Settings query and results component

This is the complete captured `124884.eb` search/results component, together
with its full `ef` normalizer and keyed `eg → ed` field forwarder. It filters
registry definitions by supplied visible sections and hidden-ID membership,
excludes hidden control kinds, builds the original translated metadata/identifier
search document, applies token-AND matching and renders the original empty or
section-ordered result structure. Fields receive their original descriptor
objects and keys; no preference value or control implementation is fabricated.

The actual `SettingsModal` caller supplies `et.trim()` and its visible section
list. Source witnesses trace the memoized trimmed value, length-positive alias
and conditional results branch. The caller's outer availability/provider,
blank-query section view, routing/input and whole modal remain external. This
module supplies the complete selected results component, not that modal.

The generator authenticates the single explicit physical factory context and
checks all three complete retained AST regions exactly once inside the actual
used constructor. Eight additional caller/import/visibility/field context
witnesses retain raw ranges and hashes. Captured code is never evaluated or
imported. Original materials retain their authorship.

## Explicit module-lifetime capabilities

`createSettingsSearchResults` accepts JSX/React compiler, translation, hidden-ID
hook, registry, section catalog and `Field`/`Section` ports. Create it once for
that intended module lifetime. The original compiler memo tracks query,
translation/visibility and visible-section reference identities; the registry
and catalog arrays are not newly subscribed stores. No stronger metadata
reactivity, visibility acquisition or private provider behavior is inferred.

Original case-before-NFKD normalization, accent stripping, identifier-period
replacement in the **document**, token matching, group/catalog order, registry
order within each group, early-return empty status and keyed field forwarding
are preserved. Literal dotted query strings do not gain special normalization.
The captured normalizer's uppercase compatibility-character quirk also remains.
A matching definition missing from the supplied section catalog can produce an
empty results region rather than the no-matches status; no extra fallback is
invented for that synthetic capability boundary.

## Attribution and qualification

#1885 separately corrects the native Settings identifier operand. #1872 recovers
field/choice rendering and #1839 the setting framework. Existing #675/#683 retain
settings metadata/translation mapping. This unit copies/imports none of those
unmerged runtime modules, retallies no helper and supplies no new product page.

Run from `app/` using the existing pinned dependencies:

```sh
node scripts/original-settings-search-results.mjs
node --test tests/original_settings_search_results.test.mjs tests/original_source.test.mjs
PUMP_SETTINGS_RESULTS_OUTPUT=/your/isolated/output node --test tests/original_settings_search_results_browser.test.mjs
```

The Node tests use actual React SSR and safe synthetic metadata to cover the
full component, filters/ordering/normalization/empty paths, source descriptor
identity and explicit translation failure. The standalone browser method uses
real React with an authored input/visibility host and read-only Field/Section
ports. It does not run the product Settings page or private registry/framework.
The host's empty-query placeholder is labeled as external to the original
selected results branch, rather than inventing the original other section view.

No account/trading controls, user storage/cookies/sessions/credentials, tenant
request, backend or preference mutation is acquired or implemented. The
original provider/whole modal/global mount, native/API/pixel equivalence,
completion and security acceptance remain unqualified. No Next build is needed
or claimed for this unmounted source module.
