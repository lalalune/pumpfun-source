import os
# DEL="2766 2928" : delete body-relative line numbers of buy_exact_quote_body
def edit(t):
    L=t.split('\n')
    s=next(i for i,l in enumerate(L) if l.startswith('define') and 'buy_exact_quote_body17h' in l)
    for k in sorted(map(int,os.environ['DEL'].split()),reverse=True): del L[s+k]
    return '\n'.join(L)
