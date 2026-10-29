import sys,os
D=os.path.dirname(os.path.abspath(__file__))
P='/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm/baselines/pristine-ws/programs/pump-amm/src/instructions/swap/sell.rs'
def setl(lines,n,text): lines[n-1]=text
V={}
def v(name):
    def deco(f): V[name]=f; return f
    return deco
@v('wr_eqfalse')
def _(L): setl(L,467,'    if ata.is_writable == false { return err!(PumpAmmError::InvalidCashbackAccumulatorAta); }')
@v('create_elseok')
def _(L):
    assert L[479-1].strip()=='))?;' and L[480-1].strip()=='}'
    setl(L,479,'        ))'); setl(L,480,'    } else { Ok(()) }?;')
@v('create_match')
def _(L):
    V['create_elseok'](L)
    setl(L,468,'    match ata.data_is_empty() { true =>')
    setl(L,480,'    , false => Ok(()) }?;')
@v('create_notfirst')
def _(L):
    V['create_elseok'](L)
    setl(L,468,'    if !ata.data_is_empty() { Ok(()) } else {')
    setl(L,480,'    }?;')
@v('create_letres')
def _(L):
    V['create_elseok'](L)
    setl(L,468,'    let created = if ata.data_is_empty() {')
    setl(L,480,'    } else { Ok(()) }; created?;')
@v('tfu_match')
def _(L):
    assert 'try_from_unchecked(ata)?;' in L[481-1]
    setl(L,481,'    let ata = match InterfaceAccount::<TokenAccount>::try_from_unchecked(ata) { Ok(ata) => ata, Err(e) => return Err(e) };')
@v('owner_ne')
def _(L):
    assert 'require!(*user_volume_accumulator.owner' in L[444-1]
    setl(L,444,'        if *user_volume_accumulator.owner != crate::ID { return err!(PumpAmmError::InvalidCashbackAccumulator); }')
@v('owner_eqfalse')
def _(L):
    setl(L,444,'        if (*user_volume_accumulator.owner == crate::ID) == false { return err!(PumpAmmError::InvalidCashbackAccumulator); }')

E='PumpAmmError::InvalidCashbackAccumulatorAta'
@v('ata_ne')
def _(L):
    assert 'require!(ata.key() == expected_ata' in L[464-1]
    setl(L,464,'    if ata.key() != expected_ata { return err!(%s); }'%E)
@v('wr_not')
def _(L):
    assert 'require!(ata.is_writable' in L[467-1]
    setl(L,467,'    if !ata.is_writable { return err!(%s); }'%E)
@v('wr_elseif')
def _(L):
    assert L[468-1].strip()=='if ata.data_is_empty() {'
    setl(L,467,'    if !ata.is_writable { return err!(%s); } else if ata.data_is_empty() {'%E)
    setl(L,468,'')
@v('create_semi_else')
def _(L):
    assert L[480-1].strip()=='}'
    setl(L,480,'    } else {}')
@v('tfu_twostep')
def _(L):
    setl(L,481,'    let ata_res = InterfaceAccount::<TokenAccount>::try_from_unchecked(ata); let ata = ata_res?;')
@v('tfu_block')
def _(L):
    setl(L,481,'    let ata = { InterfaceAccount::<TokenAccount>::try_from_unchecked(ata)? };')
@v('key_ne')
def _(L):
    assert 'if user_volume_accumulator.key() != expected_accumulator {' in L[391-1]

@v('ok_after_q')
def _(L):
    setl(L,479,'        ))?; Ok(())')
@v('ok_wrap')
def _(L):
    assert L[469-1].strip().startswith('anchor_spl::associated_token::create(')
    setl(L,469,'        Ok(anchor_spl::associated_token::create(CpiContext::new(')
    setl(L,479,'        ))?)')
@v('elseif_notfirst')
def _(L):
    setl(L,467,'    if !ata.is_writable { return err!(%s); } else if !ata.data_is_empty() { Ok(()) } else {'%E)
    setl(L,468,'')
    setl(L,480,'    }?;')

@v('ok_annot')
def _(L):
    assert L[480-1].strip()=='} else { Ok(()) }?;'
    setl(L,480,'    } else { Ok::<(), Error>(()) }?;')

@v('ok_unit_else')
def _(L):
    assert L[480-1].strip()=='} else { Ok(()) }?;'
    setl(L,480,'    } else { Result::<()>::Ok(()) }?;')
@v('elseif_wr_eqfalse')
def _(L):
    setl(L,467,'    if ata.is_writable == false { return err!(%s); } else if ata.data_is_empty() {'%E)
    setl(L,468,'')

name=sys.argv[1]
L=open(P).read().split('\n')
for part in name.split('+'):
    V[part](L)
out=os.path.join(D,name.replace('+','__')+'.rs'); open(out,'w').write('\n'.join(L)); print(out)
