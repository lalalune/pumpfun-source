def edit(f):
    d='%_185 = icmp ne i8 %683, 0'; assert f.count(d)==1
    return f.replace(d,'%_185 = icmp ne i8 %571, 0')
