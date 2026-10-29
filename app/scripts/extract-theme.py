#!/usr/bin/env python3
"""Derive the frontend Tailwind theme from the captured compiled utility stylesheet.

The captured site ships Tailwind v3 output. Every color, radius and font utility it
uses is present as a compiled rule, so the theme that produced them can be read
back mechanically instead of being re-typed by hand:

* colors: each ``.{bg,text,border,ring,...}-<name>`` rule (including variant
  forms such as ``hover:bg-<name>``) yields ``<name> -> value``. A name must
  resolve to one value across every prefix and variant, or extraction fails.
* borderRadius / fontFamily: the compiled ``rounded*`` and ``font-*`` rules.
* rootVariables: the stylesheet's ``:root`` custom properties, emitted verbatim
  as CSS so arbitrary values such as ``var(--color-bg-secondary)`` resolve.

The capture is read through ``evidence/web/manifest.json`` and its SHA-256 is
checked first. Outputs are deterministic; ``--check`` fails if they are stale.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_URL = 'https://pump.fun/_next/static/immutable/chunks/219hatf4piwx4.css'
THEME_JSON = ROOT / 'packages/frontend/src/theme/captured-theme.json'
ROOT_CSS = ROOT / 'packages/frontend/src/app/captured-root.css'
SHELL_CSS = ROOT / 'packages/frontend/src/app/captured-shell.css'
# Non-utility rules the shell markup depends on. Each selector list is copied verbatim.
SHELL_SELECTOR = re.compile(r'\.(?:pump-main-shell|pump-page-container|pump-main-row|custom-scrollbar|scrollbar-hide)\b'
                            r'|\[data-pf-auth')
# Site base rules layered after Tailwind's preflight: `html{scrollbar-gutter:stable}`,
# `body{isolation:isolate;...}` and the universal `*{border-color:...}` default.
BASE_SELECTORS = {'html', 'body', '*'}

COLOR_PREFIXES = ('bg', 'text', 'border', 'ring', 'outline', 'fill', 'stroke', 'from', 'via', 'to',
                  'divide', 'placeholder', 'caret', 'accent', 'decoration', 'ring-offset', 'shadow')
COLOR_PROPERTIES = ('background-color', 'color', 'border-color', 'border-top-color', 'border-bottom-color',
                    'border-left-color', 'border-right-color', '--tw-ring-color', 'outline-color', 'fill',
                    'stroke', '--tw-gradient-from', '--tw-gradient-to', 'caret-color', 'accent-color',
                    'text-decoration-color', '--tw-ring-offset-color', '--tw-shadow-color')
RULE = re.compile(r'([^{}]+)\{([^{}]*)\}')
# A utility token is the last unescaped segment of a class: `.hover\:bg-x:hover` -> `bg-x`.
CLASS = re.compile(r'\.((?:[a-zA-Z0-9_-]|\\.)+)')
RGB_ALPHA = re.compile(r'^rgb\((\d+) (\d+) (\d+)/var\(--tw-[a-z-]+-opacity,1\)\)$')
# Tailwind substitutes each prefix's own opacity variable (bg, text, border, ring...) for
# `<alpha-value>`, so the same theme color compiles differently per prefix.
OPACITY_PLACEHOLDER = re.compile(r'var\(--tw-[a-z-]+-opacity,\s*1\)')


def fail(message):
    raise SystemExit(f'extract-theme: {message}')


def load_source():
    manifest = json.loads((ROOT / 'evidence/web/manifest.json').read_text(encoding='utf-8'))
    record = next((r for r in manifest['records'] if r['url'] == SOURCE_URL), None)
    if record is None:
        fail(f'{SOURCE_URL} is not in the capture manifest')
    data = (ROOT / record['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != record['sha256']:
        fail(f'{record["path"]} does not match its manifest SHA-256')
    return record, data.decode('utf-8')


def utility_of(class_token):
    """Strip variant prefixes (`md\\:`, `group-hover\\/menu-item\\:`) from an escaped class token."""
    parts = re.split(r'(?<!\\)\\:', class_token)
    return parts[-1].replace('\\', '')


def canonical_hex(value):
    """The minifier writes `#000` for `#000000` and `#0000` for `#00000000`; compare expanded forms."""
    digits = value[1:].lower()
    if len(digits) in (3, 4):
        digits = ''.join(ch * 2 for ch in digits)
    return '#' + digits


def normalize_color(value):
    value = re.sub(r'\s*!important\s*$', '', value.strip(), flags=re.I).strip()
    match = RGB_ALPHA.match(value)
    if match:
        return '#%02x%02x%02x' % tuple(int(x) for x in match.groups())
    if re.fullmatch(r'#[0-9a-fA-F]{3,8}', value):
        return canonical_hex(value)
    keyword = value.lower()
    if keyword == 'transparent':
        return '#00000000'
    if keyword in ('currentcolor', 'inherit'):
        return keyword
    value = OPACITY_PLACEHOLDER.sub('<alpha-value>', value)
    # For properties with no opacity variable (fill, stroke, outline) Tailwind writes `/ 1`.
    return re.sub(r'^((?:rgb|hsl)a?\(.+?)\s*/\s*1\)$', r'\1 / <alpha-value>)', value)


def declarations(body):
    result = {}
    for declaration in body.split(';'):
        name, _, value = declaration.partition(':')
        if value:
            result[name.strip()] = value.strip()
    return result


def gradient_color(value):
    """`--tw-gradient-from:#hex var(--tw-gradient-from-position)` -> `#hex`."""
    return value.split(' var(--tw-gradient-')[0]


# Which compiled property carries the theme color for each utility prefix.
# `via-*` declares the transparent end stop first; its color is the middle gradient stop.
PREFIX_COLOR = {
    'from': lambda d: gradient_color(d['--tw-gradient-from']) if '--tw-gradient-from' in d else None,
    'to': lambda d: gradient_color(d['--tw-gradient-to']) if '--tw-gradient-to' in d else None,
    'via': lambda d: (re.match(r'var\(--tw-gradient-from\),\s*(.+?) var\(--tw-gradient-via-position\)',
                               d.get('--tw-gradient-stops', '')) or [None, None])[1],
}


def color_value(prefix, body):
    found = declarations(body)
    if prefix in PREFIX_COLOR:
        value = PREFIX_COLOR[prefix](found)
    else:
        value = next((found[p] for p in COLOR_PROPERTIES if p in found), None)
    return normalize_color(value) if value else None


def extract_colors(css):
    colors, origins = {}, {}
    prefixes = sorted(COLOR_PREFIXES, key=len, reverse=True)
    for selector, body in RULE.findall(css):
        for token in CLASS.findall(selector):
            utility = utility_of(token)
            if '/' in utility or '[' in utility:
                continue  # opacity modifiers and arbitrary values are derived, not theme keys
            prefix = next((p for p in prefixes if utility.startswith(p + '-')), None)
            if prefix is None:
                continue
            value = color_value(prefix, body)
            if value is None:
                continue  # e.g. `border-x` widths, `text-sm` sizes
            name = utility[len(prefix) + 1:]
            previous = colors.get(name)
            if previous is not None and previous != value:
                fail(f'color {name!r} is {previous} in {origins[name]} but {value} in .{utility}')
            colors.setdefault(name, value)
            origins.setdefault(name, '.' + utility)
    return dict(sorted(colors.items()))


def extract_scale(css, pattern, prop):
    """Read `.utility-key{prop:value}` rules; the minifier merges equal rules into selector lists."""
    scale = {}
    for selectors, body in RULE.findall(css):
        value = declarations(body).get(prop)
        if value is None:
            continue
        for selector in selectors.split(','):
            match = re.fullmatch(pattern, selector.strip())
            if match:
                key = match.group(1) or 'DEFAULT'
                if scale.get(key, value) != value:
                    fail(f'{selector.strip()} is {value}, already {scale[key]}')
                scale[key] = value
    return dict(sorted(scale.items()))


def root_block(css):
    blocks = re.findall(r'(?<![\w-]):root\{([^}]*)\}', css)
    if len(blocks) != 1:
        fail(f'expected one :root block, found {len(blocks)}')
    return blocks[0]


def style_rules(css):
    """Yield (at_rule, selectors, body) for every style rule; at_rule is the enclosing block or ''."""
    stack, start = [], 0
    for index, char in enumerate(css):
        if char == '{':
            stack.append((css[start:index].strip(), index))
            start = index + 1
        elif char == '}':
            selectors, brace = stack.pop()
            start = index + 1
            if not selectors.startswith('@') and len(stack) <= 1:
                outer = stack[0][0] if stack else ''
                if outer and not outer.startswith('@'):
                    continue
                yield outer, selectors, css[brace + 1:index]


# Tailwind's own preflight `body` rule; our build regenerates it.
PREFLIGHT_BODY = 'line-height:inherit;margin:0'


def shell_rules(css):
    rules = []
    for at_rule, selectors, body in style_rules(css):
        parts = {s.strip() for s in selectors.split(',')}
        site_base = not at_rule and parts <= BASE_SELECTORS and 'tab-size' not in body and body != PREFLIGHT_BODY
        if SHELL_SELECTOR.search(selectors) or site_base:
            rule = f'{selectors}{{{body}}}'
            rules.append(f'{at_rule}{{{rule}}}' if at_rule else rule)
    if not any('.pump-main-shell' in r for r in rules):
        fail('no .pump-main-shell rules found')
    return rules


def generate():
    record, css = load_source()
    theme = {
        'source': {'url': record['url'], 'path': record['path'], 'sha256': record['sha256'],
                   'generator': 'app/scripts/extract-theme.py'},
        'colors': extract_colors(css),
        'borderRadius': extract_scale(css, r'\.rounded(?:-([a-z0-9]+))?', 'border-radius'),
        'fontFamily': extract_scale(css, r'\.font-(sans|serif|mono)', 'font-family'),
    }
    if not theme['colors'] or 'bg-primary' not in theme['colors']:
        fail('no semantic colors extracted')
    theme_text = json.dumps(theme, indent=2) + '\n'
    banner = (f'/* Generated by app/scripts/extract-theme.py from {record["path"]}\n'
              f'   ({record["url"]}, sha256 {record["sha256"]}). Do not edit. */\n')
    root_text = banner + f':root{{{root_block(css)}}}\n'
    shell_text = banner + '\n'.join(shell_rules(css)) + '\n'
    return {THEME_JSON: theme_text, ROOT_CSS: root_text, SHELL_CSS: shell_text}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='fail if generated files are missing or stale')
    args = parser.parse_args()
    outputs = generate()
    stale = [path for path, text in outputs.items() if not path.is_file() or path.read_text(encoding='utf-8') != text]
    if args.check:
        if stale:
            print('stale theme outputs: ' + ', '.join(str(p.relative_to(ROOT)) for p in stale), file=sys.stderr)
            return 1
        print('captured theme outputs are current')
        return 0
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    theme = json.loads(outputs[THEME_JSON])
    print(f"wrote {len(theme['colors'])} colors, {len(theme['borderRadius'])} radii, "
          f"{len(theme['fontFamily'])} font families and the :root block")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
