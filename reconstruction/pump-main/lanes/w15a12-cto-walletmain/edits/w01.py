import runpy,os
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__) or '.','c.py')).read())
HYP="do_coin bound before do_collect (frozen(coin) evaluated before the quote-vault checks)"
EDITS=[(DCOL+"\n  "+DC, DC+"\n  "+DCOL)]
