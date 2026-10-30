def transform(s):
    L=s.split('\n')
    assert L[282].startswith('pub fn execute(')
    L[282]=L[282]+"let target:Result<Pubkey>='v:{"
    for k in range(283,338):
        L[k]=L[k].replace('return Err(',"break 'v Err(")
    assert L[337].rstrip().endswith('None=>{}}'),L[337][-40:]
    L[337]=L[337]+"Ok(target)};let target=target?;"
    return '\n'.join(L)
