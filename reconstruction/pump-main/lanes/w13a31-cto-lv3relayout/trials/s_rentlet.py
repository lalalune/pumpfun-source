exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a31-cto-lv3relayout/e/lv3.py').read())
EDITS=EDITS+[('let min=Rent::get()?.minimum_balance(0);', 'let rent=Rent::get()?;let min=rent.minimum_balance(0);')]
