import runpy
g=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a21-shim-sweepdup/v/s4.py')
L663,L664,NATQ,TOKH,L720=g['L663'],g['L664'],g['NATQ'],g['TOKH'],g['L720']
H663='  if native{let min='
def form(head,mid,tail):
    return [(L663,L663.replace('  if native{',head)),(L664,'   '+NATQ+mid+TOKH+'\n'),(L720,'   Ok(amount)'+tail+'\n')]
V={
 'g_ne':form('  if native!=false{','}else{','}'),
 'g_eqt':form('  if native==true{','}else{','}'),
 'g_mt':form('  match native{true=>{','}false=>{','}}'),
 'g_mu8':form('  match native as u8{1=>{','}_=>{','}}'),
}
