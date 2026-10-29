import re
def split(t):
    m=re.search(r'^define[^\n]*create_token_account_v217h[^\n]*\n.*?^\}\n',t,re.M|re.S)
    return t[:m.start()],m.group(0),t[m.end():]
