"""Outline the six v2/v3 handlers as the #[program] fns (line-neutral). usage: handlers.py <src>"""
import sys,re
from pathlib import Path
S=Path(sys.argv[1])
def sub(p,old,new,count=1):
    t=(S/p).read_text(); assert t.count(old)==count,(p,old,t.count(old)); (S/p).write_text(t.replace(old,new))
for f in ('buy_v2','buy_exact_quote_in_v2','sell_v2'):
    sub('lib.rs','    pub fn '+f+'<' if f in ('buy_v2','buy_exact_quote_in_v2') else '    pub fn '+f+'(', '    #[inline(never)]pub fn '+f+('<' if f in ('buy_v2','buy_exact_quote_in_v2') else '('))
sub('buy_v2.rs','#[inline(never)]\nfn buy_handler<','#[inline(always)]\nfn buy_handler<')
sub('buy_v2.rs','#[inline(never)]\nfn buy_exact_quote_in_handler<','#[inline(always)]\nfn buy_exact_quote_in_handler<')
sub('sell_v2.rs','\npub fn execute(ctx:Context<SellV2>','\n#[inline(always)]pub fn execute(ctx:Context<SellV2>')
t=(S/'sell_v2.rs').read_text()
print('ok')
