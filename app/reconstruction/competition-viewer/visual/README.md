# Local React component-host output

The actual captured viewer-card invocation renders supplied synthetic props with
real React and the maintained Tailwind/token/font inputs. Avatar, translations,
Link and price are explicit local capabilities. These are not authenticated
original-reference images, original media-provider output or maintained-page
integration proof.

- `viewer-desktop-collapsed.png` / `viewer-desktop-expanded.png`: 1280x900.
- `viewer-mobile-collapsed.png` / `viewer-mobile-expanded.png`: 375x812.

Both states were inspected. The expanded state follows a real click and a
supplied-price update; the workflow checks keyboard collapse, cleanup, prop
updates and no horizontal overflow. Reproduce with
`VIEWER_SCREENSHOTS_DIR=/absolute/output node --test tests/original_competition_viewer_browser.test.mjs`.
