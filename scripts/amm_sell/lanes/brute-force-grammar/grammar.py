#!/usr/bin/env python3
"""Micro-spelling grammar over fn cashback in pristine sell.rs.

Each SITE has a list of alternatives; alternative 0 is the pristine spelling.
An alternative is a dict {line_number: full replacement line} (1-based), and
every alternative of a site touches the same set of lines, so line numbers of
all error macros stay fixed. render(choice) -> text; check() validates that
error macros appear exactly on MACRO_LINES.
"""
import re
from pathlib import Path

SWARM = Path(__file__).resolve().parents[2]
PRISTINE = SWARM / 'baselines/pristine-ws/programs/pump-amm/src/instructions/swap/sell.rs'
LINES = PRISTINE.read_text().split('\n')
MACRO_RE = re.compile(r'\b(error!|err!|require!|require_[a-z_]+!)')
MACRO_LINES_CASHBACK = {378, 383, 392, 395, 444, 448, 464, 467, 502}
E_ACC = 'PumpAmmError::InvalidCashbackAccumulator'
E_ATA = 'PumpAmmError::InvalidCashbackAccumulatorAta'
E_MISS = 'PumpAmmError::MissingCashbackAccounts'
DISC = 'UserVolumeAccumulator::DISCRIMINATOR'
I4, I8, I12 = ' ' * 4, ' ' * 8, ' ' * 12
ERR = 'anchor_lang::error::Error'
PE = 'anchor_lang::solana_program::program_error::ProgramError'


def L(n):
    return LINES[n - 1]


def alt(**kw):
    return {int(k[1:]): v for k, v in kw.items()}


SITES = {}


def site(name, lines, *alts):
    base = {n: L(n) for n in lines}
    out = [base]
    for a in alts:
        assert set(a) <= set(lines), (name, a)
        d = dict(base)
        d.update(a)
        out.append(d)
    SITES[name] = out


# ---- near the borrow test (priority) ----
site('owner', [444],
     alt(l444=f'{I8}require!(user_volume_accumulator.owner == &crate::ID, {E_ACC});'),
     alt(l444=f'{I8}if *user_volume_accumulator.owner != crate::ID {{ return err!({E_ACC}); }}'),
     alt(l444=f'{I8}if user_volume_accumulator.owner != &crate::ID {{ return err!({E_ACC}); }}'),
     alt(l444=f'{I8}require!(user_volume_accumulator.owner.eq(&crate::ID), {E_ACC});'),
     alt(l444=f'{I8}require!(crate::ID == *user_volume_accumulator.owner, {E_ACC});'),
     alt(l444=f'{I8}if !(*user_volume_accumulator.owner == crate::ID) {{ return Err(error!({E_ACC})); }}'),
     alt(l444=f'{I8}require!(user_volume_accumulator.owner.eq(&ID), {E_ACC});'),
     alt(l444=f'{I8}require!(*user_volume_accumulator.owner == ID, {E_ACC});'),
     alt(l444=f'{I8}if crate::ID != *user_volume_accumulator.owner {{ return err!({E_ACC}); }}'),
     alt(l444=f'{I8}if user_volume_accumulator.owner.ne(&crate::ID) {{ return err!({E_ACC}); }}'),
     alt(l444=f'{I8}require!(!(*user_volume_accumulator.owner != crate::ID), {E_ACC});'),
     alt(l444=f'{I8}if *user_volume_accumulator.owner != crate::ID {{ return Err(error!({E_ACC})); }}'),
     alt(l444=f'{I8}if *user_volume_accumulator.owner != ID {{ return err!({E_ACC}); }}'),
     )
site('borrow', [445],
     alt(l445=f'{I8}let data = user_volume_accumulator.try_borrow_data().map_err(Into::<{ERR}>::into)?;'),
     alt(l445=f'{I8}let data = user_volume_accumulator.data.try_borrow().map_err(|_| {PE}::AccountBorrowFailed)?;'),
     alt(l445=f'{I8}let Ok(data) = user_volume_accumulator.try_borrow_data() else {{ return Err({PE}::AccountBorrowFailed.into()); }};'),
     alt(l445=f'{I8}let data = match user_volume_accumulator.try_borrow_data() {{ Ok(data) => data, Err(e) => return Err(e.into()) }};'),
     alt(l445=f'{I8}let data = match user_volume_accumulator.try_borrow_data() {{ Err(e) => return Err(e.into()), Ok(data) => data }};'),
     alt(l445=f'{I8}let data = user_volume_accumulator.try_borrow_data().map_err({ERR}::from)?;'),
     alt(l445=f'{I8}let data: core::cell::Ref<&mut [u8]> = user_volume_accumulator.try_borrow_data()?;'),
     alt(l445=f'{I8}let data = user_volume_accumulator.data.try_borrow().map_err(|_| {ERR}::from({PE}::AccountBorrowFailed))?;'),
     alt(l445=f'{I8}let data = &user_volume_accumulator.try_borrow_data()?[..];'),
     alt(l445=f'{I8}let data = {{ user_volume_accumulator.try_borrow_data()? }};'),
     alt(l445=f'{I8}let data = user_volume_accumulator.try_borrow_data(); let data = data?;'),
     alt(l445=f'{I8}let data = user_volume_accumulator.try_borrow_data().map_err(|e| e)?;'),
     alt(l445=f'{I8}let data = user_volume_accumulator.try_borrow_data().or_else(|e| Err(e))?;'),
     alt(l445=f'{I8}let data = user_volume_accumulator.try_borrow_data().map_err(|e| {ERR}::from(e))?;'),
     alt(l445=f'{I8}let data = if let Ok(data) = user_volume_accumulator.try_borrow_data() {{ data }} else {{ return Err({PE}::AccountBorrowFailed.into()); }};'),
     )
site('check', [446, 447, 448, 449],
     alt(l447=f'{I8}if data.len() < 8 || &data[..8] != {DISC} {{'),
     alt(l447=f'{I8}if !data.starts_with({DISC}) {{'),
     alt(l447=f'{I8}if data.get(..8) != Some({DISC}) {{'),
     alt(l447='', l448=f'{I8}require!(data.len() >= 8 && data[..8] == *{DISC}, {E_ACC});', l449=''),
     alt(l447=f'{I8}if data.len() < 8 || data[0..8] != {DISC}[..] {{'),
     alt(l447=f'{I8}if data.len() < 8 {{',
         l448=f'{I12}return err!({E_ACC}); }} else if data[..8] != *{DISC} {{ return err!({E_ACC});'),
     alt(l448=f'{I12}return Err(error!({E_ACC}));'),
     alt(l447='', l448=f'{I8}require!(data.starts_with({DISC}), {E_ACC});', l449=''),
     alt(l447=f'{I8}if data.len() < 8 || data[..8] != {DISC}[..] {{'),
     alt(l447=f'{I8}if data.len() < 8 || !data[..8].eq({DISC}) {{'),
     alt(l447=f'{I8}if data.len() < {DISC}.len() || data[..8] != *{DISC} {{'),
     alt(l447=f'{I8}if !(data.len() >= 8 && data[..8] == *{DISC}) {{'),
     alt(l446=f'{I8}let data: &[u8] = &data;'),
     alt(l446=f'{I8}let disc = {DISC};', l447=f'{I8}if data.len() < 8 || data[..8] != *disc {{'),
     alt(l446=f'{I8}let valid = |d: &[u8]| d.len() >= 8 && d[..8] == *{DISC};', l447=f'{I8}if !valid(&data) {{'),
     alt(l447=f'{I8}if !matches!(data.get(..8), Some(d) if d == {DISC}) {{'),
     alt(l447=f'{I8}if data.len() < 8 || {DISC} != &data[..8] {{'),
     alt(l447=f'{I8}if data.len() < 8 || *{DISC} != data[..8] {{'),
     alt(l447=f'{I8}if data.len() < 8 || data[..8] != {DISC}[..8] {{'),
     alt(l447=f'{I8}if data.len() < 8 || data[..8].ne({DISC}) {{'),
     )
site('drop', [449, 450],
     alt(l449=f'{I8}}} drop(data);'),
     alt(l450=f'{I4}}};'),
     alt(l449=f'{I8}}} core::mem::drop(data);'),
     alt(l449=f'{I8}}} else {{ drop(data); }}'),
     )
site('else', [443],
     alt(l443=f'{I4}}} else {{ {{'),  # needs drop site closure; handled via combo constraint
     )
site('empty', [396],
     alt(l396=f'{I4}if user_volume_accumulator.data_len() == 0 {{'),
     alt(l396=f'{I4}if user_volume_accumulator.data.borrow().is_empty() {{'),
     alt(l396=f'{I4}if user_volume_accumulator.data_is_empty() == true {{'),
     )
site('mutdrop', [441, 442],
     alt(l441=f'{I8}drop(data);'),
     alt(l442=f'{I8}Ok::<(), {ERR}>(())?;'),
     )
site('mutborrow', [425],
     alt(l425=f'{I8}let mut data = user_volume_accumulator.try_borrow_mut_data().map_err(Into::<{ERR}>::into)?;'),
     alt(l425=f'{I8}let mut data = user_volume_accumulator.data.try_borrow_mut().map_err(|_| {PE}::AccountBorrowFailed)?;'),
     )
# ---- ATA block ----
site('acc_from', [451],
     alt(l451=f'{I4}let mut accumulator: Account<UserVolumeAccumulator> = Account::try_from(user_volume_accumulator)?;'),
     alt(l451=f'{I4}let mut accumulator = match Account::<UserVolumeAccumulator>::try_from(user_volume_accumulator) {{ Ok(a) => a, Err(e) => return Err(e) }};'),
     alt(l451=f'{I4}let mut accumulator = Account::<\'info, UserVolumeAccumulator>::try_from(user_volume_accumulator)?;'),
     )
site('ata_key', [464],
     alt(l464=f'{I4}require!(*ata.key == expected_ata, {E_ATA});'),
     alt(l464=f'{I4}require!(ata.key == &expected_ata, {E_ATA});'),
     alt(l464=f'{I4}if ata.key() != expected_ata {{ return err!({E_ATA}); }}'),
     alt(l464=f'{I4}require!(expected_ata == ata.key(), {E_ATA});'),
     alt(l464=f'{I4}if *ata.key != expected_ata {{ return err!({E_ATA}); }}'),
     alt(l464=f'{I4}require!(ata.key().eq(&expected_ata), {E_ATA});'),
     alt(l464=f'{I4}if ata.key != &expected_ata {{ return err!({E_ATA}); }}'),
     alt(l464=f'{I4}if ata.key().ne(&expected_ata) {{ return err!({E_ATA}); }}'),
     alt(l464=f'{I4}if expected_ata != ata.key() {{ return err!({E_ATA}); }}'),
     alt(l464=f'{I4}require!(!(ata.key() != expected_ata), {E_ATA});'),
     )
site('ata_w', [467],
     alt(l467=f'{I4}if !ata.is_writable {{ return err!({E_ATA}); }}'),
     alt(l467=f'{I4}require!(ata.is_writable == true, {E_ATA});'),
     alt(l467=f'{I4}if ata.is_writable != true {{ return err!({E_ATA}); }}'),
     alt(l467=f'{I4}if ata.is_writable == false {{ return err!({E_ATA}); }}'),
     )
site('ata_empty', [468],
     alt(l468=f'{I4}if ata.data_len() == 0 {{'),
     alt(l468=f'{I4}if ata.data.borrow().is_empty() {{'),
     alt(l468=f'{I4}if ata.data_is_empty() == true {{'),
     alt(l468=f'{I4}if let true = ata.data_is_empty() {{'),
     alt(l468=f'{I4}if ata.data_len() < 1 {{'),
     alt(l468=f'{I4}if ata.data_is_empty() != false {{'),
     )
site('ata_cpi', [469, 479],
     alt(l479=f'{I8})).map_err(Into::<{ERR}>::into)?;'),
     alt(l469=f'{I8}if let Err(e) = anchor_spl::associated_token::create(CpiContext::new(',
         l479=f'{I8})) {{ return Err(e); }}'),
     alt(l469=f'{I8}let res = anchor_spl::associated_token::create(CpiContext::new(',
         l479=f'{I8})); res?;'),
     )
site('ata_close', [480],
     alt(l480=f'{I4}}};'),
     )
site('ata_from', [481],
     alt(l481=f'{I4}let ata: InterfaceAccount<TokenAccount> = InterfaceAccount::try_from_unchecked(ata)?;'),
     alt(l481=f'{I4}let ata = match InterfaceAccount::<TokenAccount>::try_from_unchecked(ata) {{ Ok(a) => a, Err(e) => return Err(e) }};'),
     )
# ---- elsewhere in cashback ----
site('get0', [377], alt(l377=f'{I8}.first()'))
site('ok378', [378], alt(l378=f'{I8}.ok_or(error!({E_MISS}))?;'))
site('ok383', [383], alt(l383=f'{I8}.ok_or(error!({E_MISS}))?;'))
site('key391', [391, 392, 393],
     alt(l391='', l392=f'{I4}require!(user_volume_accumulator.key() == expected_accumulator, {E_ACC});', l393=''),
     alt(l391=f'{I4}if *user_volume_accumulator.key != expected_accumulator {{'),
     alt(l391=f'{I4}if user_volume_accumulator.key != &expected_accumulator {{'),
     )
site('w395', [395],
     alt(l395=f'{I4}if !user_volume_accumulator.is_writable {{ return err!({E_ACC}); }}'),
     )
site('rent', [397, 398],
     alt(l397=f'{I8}let rent = Rent::get()?.minimum_balance(137);', l398=''),
     )
site('ok502', [502], alt(l502=f'{I8}.ok_or_else(|| error!(PumpAmmError::Overflow))?;'))

TIF = 'InterfaceAccount::<TokenAccount>::try_from_unchecked(ata)?'
site('ata_if', [468, 469, 479, 480, 481],
     alt(l468=f'{I4}match ata.data_is_empty() {{ true => {{', l479=f'{I8}))?; }}', l480=f'{I4}false => {{}} }}'),
     alt(l468=f'{I4}match ata.data_is_empty() {{ false => {{}} true => {{', l480=f'{I4}}} }}'),
     alt(l479=f'{I8}))?'),
     alt(l468=f'{I4}let created = if ata.data_is_empty() {{', l479=f'{I8})) }} else {{ Ok(()) }};', l480=f'{I4}created?;'),
     alt(l480=f'{I4}}} else {{}}'),
     alt(l468=f'{I4}ata.data_is_empty().then(|| {{', l479=f'{I8}))', l480=f'{I4}}}).transpose()?;'),
     alt(l479=f'{I8})).map(|_| ())?;'),
     alt(l468=f'{I4}let ata = if ata.data_is_empty() {{', l479=f'{I8}))?; ata }} else {{ ata }};', l480=''),
     alt(l468=f'{I4}let ata = if ata.data_is_empty() {{', l479=f'{I8}))?; {TIF} }} else {{ {TIF} }};', l480='', l481=''),
     alt(l468=f'{I4}let created = if ata.data_is_empty() {{', l479=f'{I8})) }} else {{ Ok(()) }};', l480=f'{I4}if let Err(e) = created {{ return Err(e); }}'),
     alt(l468=f'{I4}if ata.data_is_empty() {{ let _: () =', l479=f'{I8}))?; }}', l480=''),
     alt(l468=f'{I4}let ata = match ata.data_is_empty() {{ true => {{', l479=f'{I8}))?; ata }} false => ata }};', l480=''),
     )

# ---- else-if chain family around reorder lane's e0dfd60d (467/468/479/480) ----
_EA = f'return err!({E_ATA});'
_HEADS = [
    (f'{I4}if !ata.is_writable {{ {_EA} }} else if ata.data_is_empty() {{', '', ''),
    (f'{I4}if ata.is_writable == false {{ {_EA} }} else if ata.data_is_empty() {{', '', ''),
    (f'{I4}if !ata.is_writable {{ {_EA} }} else if !ata.data_is_empty() {{ Ok(()) }} else {{', '', ''),
    (f'{I4}if !ata.is_writable {{ {_EA} }}', f'{I4}if ata.data_is_empty() {{', ''),
    (f'{I4}require!(ata.is_writable, {E_ATA});', f'{I4}if ata.data_is_empty() {{', ''),
    (f'{I4}let r = if !ata.is_writable {{ {_EA} }} else if ata.data_is_empty() {{', '', 'r'),
    (f'{I4}match if !ata.is_writable {{ {_EA} }} else if ata.data_is_empty() {{', '', 'm'),
    (f'{I4}if ata.is_writable == false {{ {_EA} }}', f'{I4}if ata.data_is_empty() {{', ''),
    (f'{I4}if !ata.is_writable {{ {_EA} }} else {{ if ata.data_is_empty() {{', '', 'b'),
]
_TAILS = [
    (f'{I8}))', f'{I4}}} else {{ Ok(()) }}?;'),
    (f'{I8}))?;', f'{I4}}}'),
    (f'{I8}))?; Ok::<(), {ERR}>(())', f'{I4}}} else {{ Ok(()) }}?;'),
    (f'{I8})).map(|()| ())', f'{I4}}} else {{ Ok(()) }}?;'),
    (f'{I8}))', f'{I4}}} else {{ Result::<()>::Ok(()) }}?;'),
    (f'{I8}))', f'{I4}}} else {{ Ok(()) }}.map_err(|e| e)?;'),
    (f'{I8}))', f'{I4}}} else {{ return_ok() }}?;'),
]
_chain = []
for hi, (h, h2, kind) in enumerate(_HEADS):
    for ti, (t1, t2) in enumerate(_TAILS):
        if ti == 6:
            continue
        if kind == 'r':
            t2b = t2[:-2] + '; r?;' if t2.endswith('?;') else None
            if t2b is None or not t2.endswith('}?;'):
                continue
            t2b = t2[:-2] + '; r?;'
            t2b = t2b.replace('?; r?;', '; r?;') if False else t2[:-2] + '; r?;'
        elif kind == 'm':
            if not t2.endswith('}?;'):
                continue
            t2b = t2[:-2] + ' { Ok(()) => {}, Err(e) => return Err(e) }'
        elif kind == 'b':
            t2b = t2 + ' }'
        else:
            t2b = t2
        if kind == '' and h.endswith('Ok(()) } else {') and not t2.endswith('}?;'):
            continue
        a = {467: h, 468: h2, 479: t1, 480: t2b}
        if h2 == '' and kind == '':
            pass
        _chain.append(a)
site('ata_chain', [467, 468, 479, 480], *_chain)

_more = []
for h, h2, kind in [_HEADS[0], _HEADS[1], _HEADS[3], _HEADS[7]]:
    for t1, t2 in [(f'{I8}))?', f'{I4}}}'), (f'{I8}))?', f'{I4}}} else {{}}'), (f'{I8}))?;', f'{I4}}} else {{}}'),
                   (f'{I8})).map_err(|e| e)', f'{I4}}} else {{ Ok(()) }}?;'),
                   (f'{I8}))', f'{I4}}} else {{ Ok::<(), {ERR}>(()) }}?;')]:
        _more.append({467: h, 468: h2, 479: t1, 480: t2})
for h in [_HEADS[2][0], f'{I4}if ata.is_writable == false {{ {_EA} }} else if !ata.data_is_empty() {{ Ok(()) }} else {{']:
    for t1, t2 in [(f'{I8}))', f'{I4}}}?;'), (f'{I8}))?; Ok(())', f'{I4}}}?;')]:
        _more.append({467: h, 468: '', 479: t1, 480: t2})
SITES['ata_chain'].extend(_more)

# 'else' alt 1 opens an extra brace; it must be combined with an extra closing brace
CONSTRAINTS = [
    # (site, alt) requires (site2, alt2)
]


def render(choice):
    """choice: dict site->alt index (missing = 0)."""
    lines = list(LINES)
    used = {}
    for name, idx in choice.items():
        if idx:
            for n in SITES[name][idx]:
                if SITES[name][idx][n] != LINES[n - 1] and n in used:
                    raise ValueError('site overlap %s/%s at %d' % (name, used[n], n))
                if SITES[name][idx][n] != LINES[n - 1]:
                    used[n] = name
    for name, idx in choice.items():
        if idx:
            for n, text in SITES[name][idx].items():
                if text != LINES[n - 1]:
                    lines[n - 1] = text
    # extra-scope hack: else alt 1 needs a closing brace on line 450
    if choice.get('else') == 1:
        lines[450 - 1] = lines[450 - 1] + ' }'
    return '\n'.join(lines)


def check(text):
    ls = text.split('\n')
    if len(ls) != len(LINES):
        return 'line count changed'
    for n in range(364, 507):
        has = bool(MACRO_RE.search(ls[n - 1]))
        if has != (n in MACRO_LINES_CASHBACK):
            return f'macro presence mismatch at line {n}'
    for n in list(range(1, 364)) + list(range(507, len(LINES) + 1)):
        if ls[n - 1] != LINES[n - 1]:
            return f'outside cashback changed at {n}'
    return None


def key_of(choice):
    return ','.join(f'{k}={v}' for k, v in sorted(choice.items()) if v)


if __name__ == '__main__':
    tot = 1
    for k, v in SITES.items():
        print(k, len(v))
        tot *= len(v)
    print('space', tot)
    for k, v in SITES.items():
        for i in range(len(v)):
            e = check(render({k: i}))
            assert e is None, (k, i, e)
    print('all single alts pass check')
