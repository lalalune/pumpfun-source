import runpy
g=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a31-shim-mv58src/v/s4.py')
L663,L664,NATQ,NATM,TOKH,L720=g['L663'],g['L664'],g['NATQ'],g['NATM'],g['TOKH'],g['L720']
T719a=',amount,&vsigner))?;return Ok(amount);}'
T719b=',amount,vsigner))?;return Ok(amount);}'
S1=[(L664,'   '+NATQ+'}else{'+TOKH+'\n')]          # s_nat1
def tokfn(attr,call='tok(a,&vsigner)'):
    return [(L663,'  '+attr+'fn tok(a:&AdminCto,vsigner:&[&[&[u8]];1])->Result<u64>{'+TOKH+'\n'),(L664,'\n'),(T719a,T719b),
            (L720+'\n','   Ok(amount)}\n  if native{'+NATM+NATQ+'}else{'+call+'}\n')]
V={
 's_nat1':S1,
 # opaque condition, token arm first in source (switch [0: native, otherwise: token])
 'a_pt1flip':[(L663,'  if unsafe{pt1(31,!native)}/*shim: opaque arm order*/{'+TOKH+'\n'),(L664,'\n'),(L720,'   Ok(amount)}else{'+NATM+NATQ+'}\n')],
 # opaque condition, same arm order as s_nat1
 'a_pt1same':[(L663,L663.replace('  if native{','  if unsafe{pt1(31,native)}/*shim: opaque native test*/{'))]+S1,
 # Rent::get hoisted into its own native test, amount declared between (shared drop node for both arms)
 'b_two':[(L663,'  let min=if native{let rent=Rent::get()?;rent.minimum_balance(0)}else{0};let amount;if native{amount=a.creator_vault.lamports().saturating_sub(min);\n'),
          (L664,'   '+NATQ+'}else{'+TOKH.replace('let amount=token_raw_amount','amount=token_raw_amount')+'\n')],
 # token arm as a nested fn (value arm, no ? at the call site)
 'c_tokia':tokfn('#[inline(always)]'),
 'c_tokpl':tokfn(''),
}
