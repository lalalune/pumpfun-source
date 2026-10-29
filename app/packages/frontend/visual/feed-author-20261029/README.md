# Local feed author navigation

Chromium local screenshots at 1280 x 800 and 375 x 812 CSS pixels. The focused
`home-feed.spec.ts` case opened Alice's profile by keyboard, opened the group
profile by pointer, returned with browser Back, and focused the group's author
name at each viewport before capture. Both images are full-page screenshots.

The same synthetic local feed and disclosure remain visible. The author name
now uses the shared focus outline and a profile link; the avatar remains a
decorative initial. No external image or production request was made.

The retained original root HTML is a different, dated callout state; there is
no equivalent captured screenshot for these synthetic users. These are local
behavior/layout checks, not pixel parity or original whole-card qualification.
The baseline missing-link failure, screenshot and trace are retained outside
the repository in the contribution review's `feed-author-before-artifacts`.
