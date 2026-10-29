# Local composition-host output

`board-desktop.png` (1280x900) and `board-mobile.png` (375x812) show the actual
captured person-board invocation after recovered list/detail queryFns complete
local GETs. Original row/viewer/prize/heading/payline components render supplied
synthetic data. The dashed hero and labelled highlights explicitly mark local
ports; motion/dialog/media/translation/router parity is not inferred.

Both images were inspected. Tests also hold the detail request, exercise
failure/retry and pending/empty/final output, switch to the actual group caller,
and unmount with balanced foreground/query cleanup. They assert no overflow or
external requests. These are not original-reference or maintained-page images.

Reproduce with `BOARD_SCREENSHOTS_DIR=/absolute/output node --test tests/original_competition_board_browser.test.mjs`.
