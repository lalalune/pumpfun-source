# coordlib: how to integrate (tested)

Recipe (tools/pipeline.sh does exactly this; arg 2 = any crate dir, e.g. another lane's delivered src):
  1. python3 tools/restructure.py <crate>      # genuine lib.rs item moves (asserts i1/i1c text)
  2. python3 tools/changes2.py <crate>         # validate_buyback_fee_recipient + call sites (any count), SharingConfig macro,
                                               # boost_enabled via pump_amm GlobalConfig, pump_amm IDL GlobalConfig layout
  3. python3 tools/changes3.py <crate>         # add/remove_quote_mint for-loop form
  4. fastbuild -> layout.py apply --src <crate> --cand <unstripped.so> -> fastbuild + score
coordlib's layout.py only pads src/lib.rs (anchors = lib.rs-origin sites); coordfiles' layout pads the other files, so
the two compose. Run coordfiles' layout AFTER coordlib's restructure (restructure removes the LegacyBuy struct from
buy.rs = 26 lines, and empties create.rs/set_params.rs execute bodies).

Tested 12:4x: coordfiles-04 src -> coordlib pipeline = 833 normalized (= i1c 778 + coordfiles 35 + coordlib 20),
no losses, runtime_valid, unstripped sha256 2c573611b4fe7fa3114a3cb814ee1c5038b1d759572d4b726f7a7334f39fe6a7
(lanes/coordlib/work/bx1-b, source lanes/coordlib/work/x1-src).
