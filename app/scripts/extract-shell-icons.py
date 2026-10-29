#!/usr/bin/env python3
"""Generate the shell icon components and logomark from captured server-rendered pages.

The shell's icons are inline SVG in the streamed `S:2` segment of every captured
page. The segment is fixed evidence, so icons are addressed by their position in
document order and each position is checked against the control that owns it
(link href, aria-label or test id). Any capture drift fails extraction instead of
silently mislabeling an icon. Active-state variants are read from the page whose
route is active. Output is deterministic; `--check` fails when it is stale.
"""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_TSX = ROOT / 'packages/frontend/src/components/shell/captured-icons.tsx'
OUT_LOGO = ROOT / 'packages/frontend/public/pump-logomark.svg'
HOME = 'https://pump.fun/'
LOGO_URL = 'https://pump.fun/pump-logomark.svg'

# (position in the home page's S:2 segment, export name, expected owning control).
# Owners: "href:<path>", "label:<aria-label>", "testid:<data-testid>",
# "role:search" for the search landmark, or None when the
# icon's owner is a plain wrapper. Excluded app-promotion icons are listed so
# positions stay checked, but are not exported.
HOME_ICONS = [
    (0, 'SidebarToggleIcon', 'label:Toggle Sidebar'),
    (1, 'NavHomeIcon', 'href:/'),
    (2, 'NavExploreIcon', 'href:/explore'),
    (3, 'NavPerpsIcon', 'href:/perps'),
    (4, 'NavLeaderboardIcon', 'href:/leaderboard'),
    (5, 'NavLiveIcon', 'href:/live'),
    (6, 'NavGoIcon', 'href:/go'),
    (7, 'NavMayhemIcon', 'href:/mayhem'),
    (8, 'NavHolderRewardsIcon', 'href:/holder-rewards'),
    (9, 'NavPumpTokenIcon', 'href:/pump-token'),
    (10, 'CreateIcon', 'testid:create-button-sidebar'),
    (11, 'SupportIcon', 'testid:help-support-button-sidebar'),
    (12, 'TerminalIcon', 'href:https://trade.padre.gg/?utm_source=pumpweb'),
    (13, 'ExternalLinkIcon', 'href:https://trade.padre.gg/?utm_source=pumpweb'),
    (14, None, 'testid:try-app-button-sidebar'),  # app promotion: excluded surface
    (15, 'MobileHomeIcon', 'href:/'),
    (16, 'MobileExploreIcon', 'href:/explore'),
    (17, 'MobileCreateIcon', 'testid:create-button-mobile-nav'),
    (18, 'MobileGoIcon', 'href:/go'),
    (19, 'MobileMenuIcon', None),
    (20, None, None),  # app banner arrow: excluded surface
    (21, None, 'label:Close'),  # app banner close: excluded surface
    (22, 'BackIcon', 'label:Go back'),
    (23, 'SearchIcon', 'role:search'),  # search landmark; the back button is closed
    (24, 'ForwardIcon', None),
    (27, 'SearchMobileIcon', 'label:Search for coins and users'),
    (28, 'TopbarCreateIcon', 'testid:topbar-create-button'),
    (29, 'InfoBarSettingsIcon', 'label:Info bar settings'),
    (30, 'InfoBarWatchlistIcon', 'label:Watchlist'),
    (31, 'InfoBarPositionsIcon', 'label:Positions'),
    (32, 'InfoBarFollowingIcon', 'label:Following'),
    (33, 'InfoBarRecentIcon', 'label:Recently viewed'),
    (34, 'XIcon', 'label:X'),
    (35, 'TikTokIcon', 'label:TikTok'),
    (36, 'YouTubeIcon', 'label:YouTube'),
    (37, 'ChevronDownIcon', None),
]
# Positions whose bytes must equal another listed position (repeated controls).
DUPLICATES = {25: 22, 26: 24, 38: 37, 39: 34, 40: 35, 41: 36}
# Active nav icons: (page URL, href, export name).
ACTIVE_ICONS = [
    ('https://pump.fun/explore', '/explore', 'NavExploreActiveIcon'),
    ('https://pump.fun/perps', '/perps', 'NavPerpsActiveIcon'),
    ('https://pump.fun/leaderboard', '/leaderboard', 'NavLeaderboardActiveIcon'),
    ('https://pump.fun/live', '/live', 'NavLiveActiveIcon'),
    ('https://pump.fun/go', '/go', 'NavGoActiveIcon'),
    ('https://pump.fun/mayhem', '/mayhem', 'NavMayhemActiveIcon'),
    ('https://pump.fun/holder-rewards', '/holder-rewards', 'NavHolderRewardsActiveIcon'),
]
SVG = re.compile(r'<svg\b.*?</svg>', re.S)
TAG = re.compile(r'<(/?)([a-zA-Z]+)((?:\s+[a-zA-Z:-]+(?:="[^"]*")?)*)\s*(/?)>')
ATTR = re.compile(r'([a-zA-Z:-]+)(?:="([^"]*)")?')
JSX_ATTR = {'class': 'className', 'stroke-width': 'strokeWidth', 'stroke-linecap': 'strokeLinecap',
            'stroke-linejoin': 'strokeLinejoin', 'fill-rule': 'fillRule', 'clip-rule': 'clipRule',
            'fill-opacity': 'fillOpacity', 'stroke-dasharray': 'strokeDasharray',
            'stroke-opacity': 'strokeOpacity', 'stop-color': 'stopColor'}
ALLOWED_TAGS = {'svg', 'path', 'circle', 'rect', 'g', 'line', 'polyline', 'polygon'}


def fail(message):
    raise SystemExit(f'extract-shell-icons: {message}')


def manifest():
    return json.loads((ROOT / 'evidence/web/manifest.json').read_text(encoding='utf-8'))


def captured(records, url):
    record = next((r for r in records if r['url'] == url), None)
    if record is None:
        fail(f'{url} is not captured')
    data = (ROOT / record['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != record['sha256']:
        fail(f'{record["path"]} does not match its manifest SHA-256')
    return record, data


def shell_segment(text):
    """The streamed segment holding the app shell; its id differs per page (S:2, or S:1 on /live)."""
    element = text.find('data-app-shell=""')
    start = text.rfind('<div hidden id="S:', 0, element)
    if element < 0 or start < 0:
        fail('streamed app shell segment not found')
    return text[start:text.find('<script', element)]


def owner(segment, position):
    """Keys of the nearest open control or explicit search landmark ancestor."""
    class Ancestors(HTMLParser):
        void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                'link', 'meta', 'param', 'source', 'track', 'wbr'}

        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []

        def handle_starttag(self, tag, attrs):
            if tag not in self.void:
                self.stack.append((tag, dict(attrs)))

        def handle_startendtag(self, tag, attrs):
            pass

        def handle_endtag(self, tag):
            for index in range(len(self.stack) - 1, -1, -1):
                if self.stack[index][0] == tag:
                    del self.stack[index:]
                    break

    parser = Ancestors()
    parser.feed(segment[:position])
    for tag, attrs in reversed(parser.stack):
        if tag in {'a', 'button'} or attrs.get('role') == 'search':
            return {f'{prefix}:{attrs[name]}' for name, prefix in
                    (('href', 'href'), ('aria-label', 'label'),
                     ('data-testid', 'testid'), ('role', 'role'))
                    if attrs.get(name) is not None}
    return set()


def to_jsx(svg):
    """Convert one captured SVG to JSX, accepting only static presentational markup."""
    out = []
    for close, name, attrs, self_closing in TAG.findall(svg):
        if name not in ALLOWED_TAGS:
            fail(f'unexpected <{name}> in captured icon')
        if close:
            out.append(f'</{name}>')
            continue
        parts = []
        for attr, value in ATTR.findall(attrs):
            if attr.startswith('on') or attr in ('style', 'href', 'xlink:href'):
                fail(f'unexpected attribute {attr} in captured icon')
            parts.append(f'{JSX_ATTR.get(attr, attr)}={json.dumps(html.unescape(value))}')
        tail = ' /' if self_closing else ''
        out.append(f'<{name} {" ".join(parts)}{tail}>' if parts else f'<{name}{tail}>')
    return ''.join(out)


def component(name, svg, source):
    jsx = to_jsx(svg)
    end = jsx.index('>')  # end of the <svg> start tag: captured attributes are defaults, props override
    jsx = jsx[:end] + ' {...props}' + jsx[end:]
    return (f'/** {source} */\n'
            f'export function {name}(props: IconProps) {{\n  return {jsx};\n}}\n')


def generate():
    records = manifest()['records']
    home_record, home_bytes = captured(records, HOME)
    segment = shell_segment(home_bytes.decode('utf-8'))
    found = list(SVG.finditer(segment))
    if len(found) != 42:
        fail(f'expected 42 icons in the home shell segment, found {len(found)}')
    for position, name, expected in HOME_ICONS:
        if expected is not None and expected not in owner(segment, found[position].start()):
            fail(f'icon {position} ({name}) is not owned by {expected}')
    for position, same_as in DUPLICATES.items():
        if found[position].group(0) != found[same_as].group(0):
            fail(f'icon {position} no longer duplicates icon {same_as}')
    blocks, exported = [], {}
    for position, name, _ in HOME_ICONS:
        if name is None:
            continue
        source = f'{home_record["path"]} ({HOME}) shell icon #{position}'
        blocks.append(component(name, found[position].group(0), source))
        exported[name] = hashlib.sha256(found[position].group(0).encode()).hexdigest()
    for url, href, name in ACTIVE_ICONS:
        record, data = captured(records, url)
        page = shell_segment(data.decode('utf-8'))
        link = re.search(rf'<a [^>]*data-active="true"[^>]*href="{re.escape(href)}"[^>]*>.*?</a>', page, re.S)
        if link is None:
            fail(f'{url} has no active link for {href}')
        icons = SVG.findall(link.group(0))
        if len(icons) != 1:
            fail(f'{url} active link {href} has {len(icons)} icons')
        blocks.append(component(name, icons[0], f'{record["path"]} ({url}) active {href} icon'))
    header = ('// Generated by app/scripts/extract-shell-icons.py from captured server-rendered pages.\n'
              '// Do not edit. Path data and attributes are the captured bytes, converted to JSX.\n'
              "import type { SVGProps } from 'react';\n\n"
              'export type IconProps = SVGProps<SVGSVGElement>;\n\n')
    logo_record, logo_bytes = captured(records, LOGO_URL)
    return {OUT_TSX: (header + '\n'.join(blocks)).encode('utf-8'), OUT_LOGO: logo_bytes}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='fail if generated files are missing or stale')
    args = parser.parse_args()
    outputs = generate()
    stale = [p for p, data in outputs.items() if not p.is_file() or p.read_bytes() != data]
    if args.check:
        if stale:
            print('stale icon outputs: ' + ', '.join(str(p.relative_to(ROOT)) for p in stale), file=sys.stderr)
            return 1
        print('captured shell icons are current')
        return 0
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    count = outputs[OUT_TSX].count(b'export function ')
    print(f'wrote {count} icon components and the logomark')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
