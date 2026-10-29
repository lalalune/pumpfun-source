# Theme extraction

Install the pinned CSS parser before running the theme generator:

```
python -m pip install -r app/requirements-capture.txt
cd app
python scripts/extract-theme.py --check
python -m unittest tests/test_theme_css_structure.py
```

The root requirements include the same parser pins. These are identical to the
capture-tool dependencies introduced in #1378; either contribution can be used
independently. Python 3.10 or later is required by the parser.

Structural shell rules and the root custom-property block are read as CSS syntax
using tinycss2. Braces inside strings, comments and URL values are token data,
rather than rule boundaries. Generated rules serialize those tokens, preserving
their CSS meaning; future captures need not preserve their original quote or
escape spelling in generated CSS. Original capture bytes remain unchanged.

The generator keeps its existing scope of top-level style rules and style rules
inside one enclosing at-rule. It does not evaluate media conditions, CSS custom
properties or layout. Utility color/scale extraction is unchanged. Existing
retained input still produces exactly the bound generated file hashes.
