# Local component consumer screenshots

These images render the complete original row and actual JSX invocation with
synthetic, schema-admitted entries and local translation/Avatar/Link ports.
The row DOM/classes, original crown and verified SVGs use maintained product
CSS/fonts. Heading, buttons and placeholder avatars belong to the host.

Desktop1280x900 and mobile375x812 screenshots are retained for both squad
contexts with the first explicit image context. All three image contexts were
exercised in the same browser test; they normalize the supplied image value
before the host Avatar port. No remote image is requested.

There is no authenticated original screenshot or whole-page visual comparison.
The maintained competition page remains unchanged. These images establish only
the bounded local rendering result, including mobile truncation rather than
horizontal overflow. The update/reject/clear states are asserted in the run.

Regenerate using the existing pinned dependencies:

    ENTRY_SCREENSHOTS_DIR=reconstruction/competition-entry/visual \
      node --test tests/original_competition_entry_browser.test.mjs
