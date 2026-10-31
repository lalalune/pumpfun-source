import runpy,os
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__) or '.','c.py')).read())
HYP="ATA gate re-uses do_coin: if !collection_native||coin_present||do_coin (do_coin used in the ATA gate)"
EDITS=[(ATA,"if !collection_native||do_coin||coin_present{")]
