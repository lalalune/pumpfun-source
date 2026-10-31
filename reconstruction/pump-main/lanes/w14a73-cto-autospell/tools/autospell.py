#!/usr/bin/env python3
"""autospell.py <admin_cto.rs> <outdir> [--from-line 283] [--rules a,b,...]

Mechanical, semantics-preserving single-site spelling lattice for programs/pump/src/creator/admin_cto.rs.
Emits one EDITS file per variant (<outdir>/<name>.py, the format tools/capvar.sh and rx.py consume: a list of
exact (old,new) pairs, each old unique in the file) plus <outdir>/manifest.json.  Every edit keeps the file's
newline count, so every require!/error! site keeps its line!() immediate.

Rules (name: what it rewrites):
  andand   L&&R            -> (L)&(R)            pure bool operands only (no ?, return, calls with effects)
  oror     L||R            -> (L)|(R)            closures `||f()` are skipped
  bitand   a&b (idents)    -> a&&b
  not      !X              -> (X==false), (X!=true)
  eqfalse  X==false        -> !X ;  X!=true -> !X
  cmpswap  L==R / L!=R / L>R -> R==L / R!=L / R<L
  cmpneg   L==R -> !(L!=R) ;  L!=R -> !(L==R)
  keyspell X.key() -> *X.key ;  *X.key -> X.key()
  iflet    if let Some(p)=e{B}   -> match e{Some(p)=>{B}None=>{}}  and None-first
           if let Some(p)=e{B}else{C} -> match (both arm orders)
  match    match e{Some(p)=>{B}None=>{}} -> if let / None-first
  letelse  let t=if let Some(t)=e{t}else{R}; -> let Some(t)=e else{R}; / match forms
  unwrapor if let Some(f)=e{x=f;} -> x=e.unwrap_or(x);
  andthen  A?;B -> A.and_then(|()|B)  (B a call, optional trailing ?) ;  A.and_then(|()|B) -> A?;B
  require  require!(C,E); -> if !(C){return Err(error!(E));} and the negated-comparison form
  ifreq    if C{return Err(error!(E));} -> require!(!(C),E); (and simplified negations)
  issome   X.is_some() -> matches!(X,Some(_)) / X!=None / !X.is_none() ; X.is_none() likewise
           X==Some(true) -> matches!(X,Some(true)) / X.unwrap_or(false) / X.is_some_and(|v|v) / Some(true)==X
  inline   let N=E; with exactly one later use of N in its block -> use site (E), binding removed
  ifq      if C{f()?;} -> if C{f()}else{Ok(())}?; / C.then(||f()).transpose()?;
  thenopt  (c).then(||f).transpose()?.unwrap_or(d) -> if/match/Ok-wrapped/flipped/then_some forms
  letswap  let A=E1;let B=E2; -> let B=E2;let A=E1;  (independent, pure)
  fieldswap adjacent field-init swaps in CtoState / associated_token::Create literals
  reread   one use of a multi-use pure binding -> its expression
  reuse    a later recomputation of a bound pure expression -> the binding
  opswap   L&&R -> R&&L, L||R -> R||L, a&b -> b&a (pure operands)
Variants that do not compile are dropped by the build; behaviour is checked by the 363-case differential at landing.
"""
import sys, os, re, json

def code_mask(s):
    """True for characters that are code (not inside string literals or // comments)."""
    m = [True] * len(s); i = 0; n = len(s)
    while i < n:
        c = s[i]
        if c == '/' and i + 1 < n and s[i + 1] == '/':
            j = s.find('\n', i); j = n if j < 0 else j
            for k in range(i, j): m[k] = False
            i = j; continue
        if c == '"':
            j = i + 1
            while j < n and s[j] != '"':
                j += 2 if s[j] == '\\' else 1
            for k in range(i, j + 1): m[k] = False
            i = j + 1; continue
        if c == "'" and i + 2 < n and s[i + 2] == "'":  # char literal 'x'
            for k in range(i, i + 3): m[k] = False
            i += 3; continue
        i += 1
    return m

OPEN = '([{'; CLOSE = ')]}'
KW = ('if', 'return', 'else', 'let', 'match', 'in', 'while')

class Src:
    def __init__(self, s, from_line):
        self.s = s; self.m = code_mask(s)
        self.lo = 0
        for _ in range(from_line - 1): self.lo = s.index('\n', self.lo) + 1
    def code(self, i): return 0 <= i < len(self.s) and self.m[i]
    def line(self, i): return self.s.count('\n', 0, i) + 1

    def left(self, p, level):
        """Start index of the left operand ending just before p. level: 'cmp' or 'logic'."""
        s = self.s; i = p - 1; depth = 0
        while i >= 0:
            c = s[i]
            if not self.m[i]: i -= 1; continue
            if c in CLOSE: depth += 1
            elif c in OPEN:
                if depth == 0: break
                depth -= 1
            elif depth == 0:
                if c in ',;' or c.isspace(): break
                if c == '=' and s[i - 1] not in '=!<>' and s[i + 1] != '=' and s[i + 1] != '>': break
                if c == '>' and s[i - 1] == '=': break  # =>
                if c in '&|' and s[i - 1] == c and level in ('cmp', 'logic', 'unary'):
                    # `&&` / `||` at depth 0 bounds the operand (a closure `||` is preceded by ( or ,)
                    break
                if level == 'cmp' and c in '&|^': break
            i -= 1
        j = i + 1
        while s[j].isspace(): j += 1
        if level == 'logic' and s[j] in '&|' and s[j + 1] == s[j]: j += 2
        # strip a leading keyword like `if ` (handled by whitespace stop) -- nothing else to do
        return j

    def right(self, p, level):
        """End index (exclusive) of the right operand starting at p."""
        s = self.s; i = p; n = len(s); depth = 0
        while i < n and s[i].isspace(): i += 1
        start = i
        while i < n:
            c = s[i]
            if not self.m[i]: i += 1; continue
            if c in OPEN:
                if c == '{' and depth == 0 and i > start: break
                depth += 1
            elif c in CLOSE:
                if depth == 0: break
                depth -= 1
            elif depth == 0:
                if c in ',;' or c.isspace(): break
                if c in '&|' and i + 1 < n and s[i + 1] == c: break
                if level == 'cmp' and c in '&|^' and i > start: break
                if c == '=' and s[i + 1] != '=' and s[i - 1] not in '=!<>': break
                if level == 'cmp' and c in '=!<>' and i > start and s[i + 1] == '=': break
            i += 1
        return i

    def postfix(self, p):
        """End of a postfix expression (path, .field, .method(..), [..], ?) starting at p."""
        s = self.s; i = p; n = len(s)
        if s[i] == '(':
            i = self.match_close(i) + 1
        elif s[i] == '*':
            return self.postfix(i + 1)
        else:
            mm = re.compile(r'[\w:]+').match(s, i)
            if not mm: return None
            i = mm.end()
        while i < n:
            if s[i] in '([':
                i = self.match_close(i) + 1
            elif s[i] == '.' and re.match(r'\.\w', s[i:i + 2]):
                i = re.compile(r'\.\w+').match(s, i).end()
            elif s[i] == '?':
                i += 1
            else: break
        return i

    def match_close(self, i):
        s = self.s; depth = 0; j = i
        while j < len(s):
            if self.m[j]:
                if s[j] in OPEN: depth += 1
                elif s[j] in CLOSE:
                    depth -= 1
                    if depth == 0: return j
            j += 1
        raise ValueError('unbalanced')

def pure(x):
    return '?' not in x and 'return' not in x and 'token_frozen' not in x and 'token_raw_amount' not in x

class Gen:
    def __init__(self, s, from_line=283):
        self.S = Src(s, from_line); self.s = s; self.out = []; self.seen = set()
    def add(self, rule, i, j, new, tag=''):
        """Replace s[i:j] with new."""
        s = self.s
        if s[i:j] == new: return
        a, b = i, j
        while True:
            old = s[a:b]
            if s.count(old) == 1 and b - a >= 12: break
            a = max(0, a - 4); b = min(len(s), b + 4)
        newfull = s[a:i] + new + s[j:b]
        assert old.count('\n') == newfull.count('\n'), (rule, old)
        if (old, newfull) in self.seen: return
        self.seen.add((old, newfull))
        ln = self.S.line(i)
        k = sum(1 for v in self.out if v['rule'] == rule and v['line'] == ln)
        name = f"{rule}-L{ln}-{k}{tag}"
        self.out.append({'name': name, 'rule': rule, 'line': ln, 'edits': [(old, newfull)],
                         'from': s[i:j][:160], 'to': new[:160]})

    def sites(self, pat):
        S = self.S
        for mm in re.finditer(pat, self.s):
            if mm.start() >= S.lo and S.code(mm.start()): yield mm

    def r_andand(self):
        s, S = self.s, self.S
        for mm in self.sites(r'&&'):
            p = mm.start()
            if s[p - 1] == '&' or s[p + 2] == '&': continue
            L = S.left(p, 'logic'); R = S.right(p + 2, 'logic')
            l, r = s[L:p].strip(), s[p + 2:R].strip()
            if not (pure(l) and pure(r)) or not l or not r: continue
            self.add('andand', L, R, f'({l})&({r})')
    def r_oror(self):
        s, S = self.s, self.S
        for mm in self.sites(r'\|\|'):
            p = mm.start()
            prev = s[:p].rstrip()[-1:]
            if prev in '(,=' or s[:p].rstrip().endswith('move'): continue
            L = S.left(p, 'logic'); R = S.right(p + 2, 'logic')
            l, r = s[L:p].strip(), s[p + 2:R].strip()
            if not (pure(l) and pure(r)) or not l or not r: continue
            self.add('oror', L, R, f'({l})|({r})')
    def r_bitand(self):
        s = self.s
        for mm in self.sites(r'(?<=[\w)])&(?=[\w(])'):
            p = mm.start()
            if s[p - 1] == '&' or s[p + 1] == '&': continue
            a = re.search(r'\w+$', s[:p]); b = re.match(r'\w+', s[p + 1:])
            if not a or not b: continue
            self.add('bitand', p - len(a.group()), p + 1 + len(b.group()), f'{a.group()}&&{b.group()}')
    def r_not(self):
        s, S = self.s, self.S
        for mm in self.sites(r'!'):
            p = mm.start()
            if s[p + 1] == '=' or re.match(r'\w', s[p - 1]): continue
            e = S.postfix(p + 1)
            if e is None: continue
            x = s[p + 1:e]
            if not x: continue
            for k, form in enumerate((f'({x}==false)', f'({x}!=true)')):
                self.add('not', p, e, form, tag=f'f{k}')
    def r_eqfalse(self):
        s, S = self.s, self.S
        for mm in self.sites(r'(==false|!=true)\b'):
            p = mm.start(); L = S.left(p, 'cmp'); x = s[L:p]
            self.add('eqfalse', L, mm.end(), f'!{x}' if re.fullmatch(r'[\w.:]+(\(\))?', x) else f'!({x})')
    def cmp_sites(self):
        s, S = self.s, self.S
        for mm in self.sites(r'==|!=|(?<=[\w)])>(?=[\w])'):
            p = mm.start(); op = mm.group()
            if op == '>' and (s[p - 1] in '-=' or s[p + 1] in '=>'): continue
            if op in ('==', '!=') and (s[p - 1] in '=!<>' or s[p + 2] == '='): continue
            L = S.left(p, 'cmp'); R = S.right(p + len(op), 'cmp')
            l, r = s[L:p], s[p + len(op):R]
            if not l or not r or l in ('false', 'true') or r in ('false', 'true'): continue
            if not pure(l) or not pure(r): continue
            yield L, R, l, op, r
    def r_cmpswap(self):
        for L, R, l, op, r in self.cmp_sites():
            nop = {'==': '==', '!=': '!=', '>': '<'}[op]
            self.add('cmpswap', L, R, f'{r}{nop}{l}')
    def r_cmpneg(self):
        for L, R, l, op, r in self.cmp_sites():
            if op == '>': continue
            nop = '!=' if op == '==' else '=='
            self.add('cmpneg', L, R, f'!({l}{nop}{r})')
    def r_keyspell(self):
        for mm in self.sites(r'(?<![\w.*])(a\.\w+)\.key\(\)'):
            self.add('keyspell', mm.start(), mm.end(), f'*{mm.group(1)}.key', tag='d')
        for mm in self.sites(r'\*(a\.\w+)\.key\b(?!\()'):
            self.add('keyspell', mm.start(), mm.end(), f'{mm.group(1)}.key()', tag='m')
    def block(self, i):
        """s[i]=='{' -> (i, j) with s[j]=='}'"""
        return i, self.S.match_close(i)
    def r_iflet(self):
        s, S = self.s, self.S
        for mm in self.sites(r'if let Some\(([^=]*?)\)=([\w.]+)\{'):
            if s[mm.start() - 1] == '=':  # let t=if let ... handled by letelse
                continue
            b0, b1 = self.block(mm.end() - 1)
            body = s[b0 + 1:b1]; p, e = mm.group(1), mm.group(2)
            rest = s[b1 + 1:]
            if rest.startswith('else{'):
                c0, c1 = self.block(b1 + 5); other = s[c0 + 1:c1]
                self.add('iflet', mm.start(), c1 + 1, f'match {e}{{Some({p})=>{{{body}}}None=>{{{other}}}}}', tag='s')
                self.add('iflet', mm.start(), c1 + 1, f'match {e}{{None=>{{{other}}}Some({p})=>{{{body}}}}}', tag='n')
            elif rest.startswith('else'):
                continue
            else:
                self.add('iflet', mm.start(), b1 + 1, f'match {e}{{Some({p})=>{{{body}}}None=>{{}}}}', tag='s')
                self.add('iflet', mm.start(), b1 + 1, f'match {e}{{None=>{{}}Some({p})=>{{{body}}}}}', tag='n')
                if '?' in e: pass
        # if let with a call scrutinee (collect(...)?)
        for mm in self.sites(r'if let Some\((\([^)]*\)|\w+)\)='):
            st = mm.end()
            if re.match(r'[\w.]+\{', s[st:]): continue
            e_end = S.postfix(st)
            if e_end is None or s[e_end] != '{': continue
            b0, b1 = self.block(e_end)
            if s[b1 + 1:].startswith('else'): continue
            body = s[b0 + 1:b1]; p = mm.group(1); e = s[st:e_end]
            self.add('iflet', mm.start(), b1 + 1, f'match {e}{{Some({p})=>{{{body}}}None=>{{}}}}', tag='cs')
            self.add('iflet', mm.start(), b1 + 1, f'match {e}{{None=>{{}}Some({p})=>{{{body}}}}}', tag='cn')
    def r_match(self):
        s = self.s
        for mm in self.sites(r'match ([\w.]+)\{Some\((\w+)\)=>\{'):
            b0, b1 = self.block(mm.end() - 1)
            body = s[b0 + 1:b1]; rest = s[b1 + 1:]
            m2 = re.match(r'None=>\{\}\}', rest)
            if not m2: continue
            end = b1 + 1 + m2.end(); e, p = mm.group(1), mm.group(2)
            self.add('match', mm.start(), end, f'if let Some({p})={e}{{{body}}}', tag='i')
            self.add('match', mm.start(), end, f'match {e}{{None=>{{}}Some({p})=>{{{body}}}}}', tag='n')
            self.add('match', mm.start(), end, f'if {e}.is_some(){{let {p}={e}.unwrap();{body}}}', tag='u')
    def r_letelse(self):
        s = self.s
        for mm in self.sites(r'let (\w+)=if let Some\((\w+)\)=([\w.]+)\{\2\}else\{'):
            c0, c1 = self.block(mm.end() - 1)
            if s[c1 + 1] != ';': continue
            t, p, e = mm.groups(); R = s[c0 + 1:c1]
            if t != p: continue
            self.add('letelse', mm.start(), c1 + 2, f'let Some({t})={e} else{{{R}}};', tag='le')
            self.add('letelse', mm.start(), c1 + 2, f'let {t}=match {e}{{Some({t})=>{t},None=>{{{R}}}}};', tag='ms')
            self.add('letelse', mm.start(), c1 + 2, f'let {t}=match {e}{{None=>{{{R}}}Some({t})=>{t}}};', tag='mn')
            self.add('letelse', mm.start(), c1 + 2, f'if {e}.is_none(){{{R}}}let {t}={e}.unwrap();', tag='un')
        for mm in self.sites(r'let Some\((\w+)\)=([\w.]+) else\{'):
            c0, c1 = self.block(mm.end() - 1)
            t, e = mm.groups(); R = s[c0 + 1:c1]
            self.add('letelse', mm.start(), c1 + 2, f'let {t}=if let Some({t})={e}{{{t}}}else{{{R}}};', tag='il')
    def r_unwrapor(self):
        for mm in self.sites(r'if let Some\((\w+)\)=([\w.]+)\{([\w.]+)=\1;\}'):
            f, e, x = mm.groups()
            self.add('unwrapor', mm.start(), mm.end(), f'{x}={e}.unwrap_or({x});', tag='u')
            self.add('unwrapor', mm.start(), mm.end(), f'if {e}.is_some(){{{x}={e}.unwrap();}}', tag='s')
        for mm in self.sites(r'([\w.]+)=([\w.]+)\.unwrap_or\(\1\);'):
            x, e = mm.groups()
            self.add('unwrapor', mm.start(), mm.end(), f'if let Some(v)={e}{{{x}=v;}}', tag='r')
    def r_andthen(self):
        s, S = self.s, self.S
        for mm in self.sites(r'\)\?;'):
            p = mm.start() + 1  # at '?'
            # find start of the call expression: walk back over the call chain
            L = S.left(p, 'logic')
            a = s[L:p]
            if not re.match(r'[\w:]', a) or a.startswith(('let', 'if')): continue
            st = p + 2
            if not re.match(r'(crate::|anchor_spl::)[\w:]+\(', s[st:]): continue
            e = S.postfix(st)
            b = s[st:e]; tail = ''
            if b.endswith('?'): b = b[:-1]; tail = '?'
            self.add('andthen', L, e, f'{a}.and_then(|()|{b}){tail}')
        for mm in self.sites(r'\.and_then\(\|\(\)\|'):
            c = S.match_close(mm.start() + len('.and_then'))
            inner = s[mm.end():c]
            self.add('andthen', mm.start(), c + 1, f'?;{inner}', tag='r')
    def r_require(self):
        s, S = self.s, self.S
        for mm in self.sites(r'require!\('):
            c = S.match_close(mm.end() - 1)
            body = s[mm.end():c]
            k = body.rfind(',PumpError::')
            if k < 0 or s[c + 1] != ';': continue
            cond, err = body[:k], body[k + 1:]
            self.add('require', mm.start(), c + 2, f'if !({cond}){{return Err(error!({err}));}}', tag='n')
            m2 = re.fullmatch(r'(.+?)(==|!=)(.+)', cond)
            if m2:
                nop = '!=' if m2.group(2) == '==' else '=='
                self.add('require', mm.start(), c + 2, f'if {m2.group(1)}{nop}{m2.group(3)}{{return Err(error!({err}));}}', tag='c')
                self.add('require', mm.start(), c + 2, f'if {m2.group(1)}{nop}{m2.group(3)}{{return err!({err});}}', tag='e')
    def r_ifreq(self):
        s, S = self.s, self.S
        for mm in self.sites(r'if (.+?)\{return Err\(error!\((PumpError::\w+)\)\);\}'):
            cond, err = mm.group(1), mm.group(2)
            if '{' in cond or '}' in cond or ';' in cond: continue
            self.add('ifreq', mm.start(), mm.end(), f'require!(!({cond}),{err});', tag='n')
            if cond.startswith('!') and S.postfix(mm.start() + 4) == mm.start() + 3 + len(cond):
                self.add('ifreq', mm.start(), mm.end(), f'require!({cond[1:]},{err});', tag='s')
            self.add('ifreq', mm.start(), mm.end(), f'if {cond}{{return err!({err});}}', tag='e')
    def r_issome(self):
        s, S = self.s, self.S
        for mm in self.sites(r'(?<![\w.])([\w.]+)\.is_(some|none)\(\)'):
            x, k = mm.groups()
            if k == 'some':
                forms = [f'matches!({x},Some(_))', f'({x}!=None)', f'!{x}.is_none()']
            else:
                forms = [f'matches!({x},None)', f'({x}==None)', f'!{x}.is_some()']
            for t, f in enumerate(forms): self.add('issome', mm.start(), mm.end(), f, tag=f'f{t}')
        for mm in self.sites(r'(?<![\w.])(\w+)==Some\(true\)'):
            x = mm.group(1)
            for t, f in enumerate([f'matches!({x},Some(true))', f'{x}.unwrap_or(false)', f'{x}.is_some_and(|v|v)', f'(Some(true)=={x})', f'({x}.unwrap_or_default())']):
                self.add('issome', mm.start(), mm.end(), f, tag=f'b{t}')
    def r_inline(self):
        s, S = self.s, self.S
        for mm in self.sites(r'let (\w+)=(?!=)'):
            n = mm.group(1)
            if n in ('mut', 'e', 'a'): continue
            st = mm.end(); i = st; depth = 0
            while i < len(s):
                c = s[i]
                if S.code(i):
                    if c in OPEN: depth += 1
                    elif c in CLOSE:
                        if depth == 0: break
                        depth -= 1
                    elif c == ';' and depth == 0: break
                i += 1
            if s[i] != ';': continue
            e = s[st:i]
            if '?' in e or 'return' in e or '\n' in e: continue
            # scope: to the end of the enclosing block
            j = i + 1; depth = 0
            while j < len(s):
                if S.code(j):
                    if s[j] in OPEN: depth += 1
                    elif s[j] in CLOSE:
                        if depth == 0: break
                        depth -= 1
                j += 1
            scope = s[i + 1:j]
            uses = [u for u in re.finditer(rf'(?<![\w.]){n}\b', scope) if S.code(i + 1 + u.start())]
            if len(uses) != 1: continue
            u = uses[0]; up = i + 1 + u.start()
            between = s[i + 1:up]
            roots = set(re.findall(r'(?<![\w.:])([a-z_]\w*)(?=\.)', e)) | set(re.findall(r'(?<![\w.:])([a-z_]\w*)\b', e))
            if any(re.search(rf'(?<![\w.]){r}(\.\w+)*\s*=(?![=>])', between) for r in roots): continue
            if re.match(rf'{n}\s*[:,}}]', s[up:]) and s[up - 1] in '{,':  # struct shorthand
                rep = f'{n}:{e}'
            elif re.match(rf'{n}\s*=[^=]', s[up:]) or re.search(rf'let\s+(mut\s+)?{n}\b', scope):
                continue
            else:
                rep = e if re.fullmatch(r'[\w.:]+(\(\))?|\*?[\w.]+', e) else f'({e})'
            if '\n' in s[mm.start():up + len(n)]:
                # cross-line: two edits must stay separate; express as one span replacement keeping newlines
                pass
            seg = s[mm.start():up + len(n)]
            newseg = s[i + 1:up] + rep
            # remove `let n=e;` keeping newline count (it contains no newline)
            self.add('inline', mm.start(), up + len(n), newseg)

    def r_ifq(self):
        s, S = self.s, self.S
        # if C{CALL?;}  ->  if C{CALL}else{Ok(())}?;
        for mm in self.sites(r'(?<![\w])(else )?if '):
            st = mm.end(); i = st; depth = 0
            while i < len(s):
                if S.code(i):
                    if s[i] in OPEN:
                        if s[i] == '{' and depth == 0: break
                        depth += 1
                    elif s[i] in CLOSE: depth -= 1
                i += 1
            if i >= len(s) or s[i] != '{': continue
            b0, b1 = self.block(i)
            body = s[b0 + 1:b1]
            if s[b1 + 1:].startswith('else') or mm.group(1): continue
            m2 = re.fullmatch(r'(\s*)((?:crate|anchor_spl|wallet)[\w:]*\(.*\))\?;(\s*)', body, re.S)
            if not m2: continue
            call = m2.group(2)
            if S.postfix(b0 + 1 + len(m2.group(1))) != b0 + 1 + len(m2.group(1)) + len(call) + 1: continue
            cond = s[st:i]
            self.add('ifq', mm.start(), b1 + 1, f'if {cond}{{{m2.group(1)}{call}{m2.group(3)}}}else{{Ok(())}}?;', tag='e')
            self.add('ifq', mm.start(), b1 + 1, f'{cond}.then(||{m2.group(1)}{call}{m2.group(3)}).transpose()?;' if re.fullmatch(r'[\w.]+', cond) else f'({cond}).then(||{m2.group(1)}{call}{m2.group(3)}).transpose()?;', tag='t')
    def r_thenopt(self):
        s, S = self.s, self.S
        for mm in self.sites(r'\(([!\w.]+)\)\.then\(\|\|'):
            c = S.match_close(mm.end() - 3)
            f = s[mm.end():c]
            m2 = re.match(r'\.transpose\(\)\?\.unwrap_or\((\w+)\)', s[c + 1:])
            if not m2: continue
            cond = mm.group(1); d = m2.group(1); end = c + 1 + m2.end()
            self.add('thenopt', mm.start(), end, f'if {cond}{{{f}?}}else{{{d}}}', tag='i')
            self.add('thenopt', mm.start(), end, f'match {cond}{{true=>{f}?,false=>{d}}}', tag='m')
            self.add('thenopt', mm.start(), end, f'(if {cond}{{{f}}}else{{Ok({d})}})?', tag='o')
            if cond.startswith('!'):
                self.add('thenopt', mm.start(), end, f'if {cond[1:]}{{{d}}}else{{{f}?}}', tag='f')
                self.add('thenopt', mm.start(), end, f'{cond[1:]}.then_some({d}).map_or_else(||{f},Ok)?', tag='s')

    def stmt_end(self, st):
        s, S = self.s, self.S; i = st; depth = 0
        while i < len(s):
            if S.code(i):
                c = s[i]
                if c in OPEN: depth += 1
                elif c in CLOSE:
                    if depth == 0: return None
                    depth -= 1
                elif c == ';' and depth == 0: return i
            i += 1
        return None
    def r_letswap(self):
        """let A=E1;let B=E2; -> let B=E2;let A=E1; (independent, no ?, same line)"""
        s, S = self.s, self.S
        for mm in self.sites(r'let (mut )?(\w+)(:[^=]+)?=(?!=)'):
            e1 = self.stmt_end(mm.end())
            if e1 is None: continue
            m2 = re.compile(r'(\s*)let (mut )?(\w+)(:[^=]+)?=(?!=)').match(s, e1 + 1)
            if not m2: continue
            e2 = self.stmt_end(m2.end())
            if e2 is None: continue
            A, B = mm.group(2), m2.group(3)
            st1, st2 = s[mm.start():e1 + 1], s[m2.start() + len(m2.group(1)):e2 + 1]
            if '\n' in st1 + st2 + m2.group(1) or '?' in st1 + st2 or 'return' in st1 + st2: continue
            if re.search(rf'(?<![\w.]){A}\b', st2) or re.search(rf'(?<![\w.]){B}\b', st1): continue
            self.add('letswap', mm.start(), e2 + 1, st2 + m2.group(1) + st1)
    def r_fieldswap(self):
        """adjacent field-init swaps in selected struct literals (evaluation order)"""
        s, S = self.s, self.S
        for mm in self.sites(r'(CtoState|AdminCtoEvent|CollectCreatorFeeEvent|associated_token::Create)\{'):
            b0, b1 = self.block(mm.end() - 1)
            body = s[b0 + 1:b1]
            # split top-level commas
            parts = []; depth = 0; last = 0
            for k, c in enumerate(body):
                if not S.code(b0 + 1 + k): continue
                if c in OPEN: depth += 1
                elif c in CLOSE: depth -= 1
                elif c == ',' and depth == 0: parts.append(body[last:k]); last = k + 1
            parts.append(body[last:])
            if any('?' in p for p in parts): continue
            for k in range(len(parts) - 1):
                q = parts[:]; q[k], q[k + 1] = q[k + 1], q[k]
                self.add('fieldswap', b0 + 1, b1, ','.join(q), tag=mm.group(1)[:3].lower())

    def _lets(self):
        """yield (name, expr, let_start, let_end(;), scope_end) for pure single-line lets"""
        s, S = self.s, self.S
        for mm in self.sites(r'let (\w+)=(?!=)'):
            n = mm.group(1)
            if n in ('mut', 'e', 'a'): continue
            e1 = self.stmt_end(mm.end())
            if e1 is None: continue
            e = s[mm.end():e1]
            if '?' in e or 'return' in e or '\n' in e or 'find_program_address' in e: continue
            j = e1 + 1; depth = 0
            while j < len(s):
                if S.code(j):
                    if s[j] in OPEN: depth += 1
                    elif s[j] in CLOSE:
                        if depth == 0: break
                        depth -= 1
                j += 1
            yield n, e, mm.start(), e1, j
    def r_reread(self):
        """multi-use pure binding: replace one later use of N with its expression (re-read)"""
        s, S = self.s, self.S
        for n, e, st, e1, j in self._lets():
            scope = s[e1 + 1:j]
            uses = [e1 + 1 + u.start() for u in re.finditer(rf'(?<![\w.]){n}\b(?!\s*:)', scope) if S.code(e1 + 1 + u.start())]
            if len(uses) < 2: continue
            roots = set(re.findall(r'(?<![\w.:])([a-z_]\w*)\b', e))
            for k, up in enumerate(uses):
                between = s[e1 + 1:up]
                if any(re.search(rf'(?<![\w.]){r}(\.\w+)*\s*=(?![=>])', between) for r in roots): continue
                if s[up - 1] in '{,' and re.match(rf'{n}\s*[,}}]', s[up:]): continue
                rep = e if re.fullmatch(r'[\w.:]+(\(\))?', e) else f'({e})'
                self.add('reread', up, up + len(n), rep, tag=f'{n[:6]}')
    def r_reuse(self):
        """later recomputation of a bound pure expression -> the binding"""
        s, S = self.s, self.S
        for n, e, st, e1, j in self._lets():
            if len(e) < 10: continue
            core = e[1:] if e.startswith('!') else e
            for mm in re.finditer(re.escape(core), s[e1 + 1:j]):
                p = e1 + 1 + mm.start()
                if not S.code(p): continue
                if re.match(r'\s*=(?![=>])', s[p + len(core):]) or re.match(r'[\w(]', s[p + len(core):p + len(core) + 1]): continue
                roots = set(re.findall(r'(?<![\w.:])([a-z_]\w*)\b', e))
                if any(re.search(rf'(?<![\w.]){r}(\.\w+)*\s*=(?![=>])', s[e1 + 1:p]) for r in roots): continue
                if e.startswith('!'):
                    if s[p - 1] == '!': self.add('reuse', p - 1, p + len(core), n, tag=n[:6])
                    else: self.add('reuse', p, p + len(core), f'(!{n})', tag=n[:6])
                else:
                    self.add('reuse', p, p + len(core), n, tag=n[:6])

    def r_opswap(self):
        """L&&R -> R&&L, L||R -> R||L, a&b -> b&a for pure operands (short-circuit block order)"""
        s, S = self.s, self.S
        for mm in self.sites(r'&&|\|\||(?<=[\w)])&(?=[\w(])'):
            p = mm.start(); op = mm.group()
            if op == '&' and (s[p - 1] == '&' or s[p + 1] == '&'): continue
            if op == '&&' and (s[p - 1] == '&' or s[p + 2] == '&'): continue
            if op == '||':
                prev = s[:p].rstrip()[-1:]
                if prev in '(,=' or s[:p].rstrip().endswith('move'): continue
            L = S.left(p, 'logic'); R = S.right(p + len(op), 'logic')
            l, r = s[L:p].strip(), s[p + len(op):R].strip()
            if not (pure(l) and pure(r)) or not l or not r: continue
            if op == '&': 
                a = re.search(r'\w+$', s[:p]).group(); b = re.match(r'\w+', s[p + 1:]).group()
                self.add('opswap', p - len(a), p + 1 + len(b), f'{b}&{a}'); continue
            sp = s[p - 1] == ' '
            self.add('opswap', L, R, f'{r} {op} {l}' if sp else f'{r}{op}{l}')

    def run(self, rules):
        for r in rules: getattr(self, 'r_' + r)()
        return self.out

RULES = ['andand', 'oror', 'bitand', 'not', 'eqfalse', 'cmpswap', 'cmpneg', 'keyspell', 'iflet', 'match', 'letelse',
         'unwrapor', 'andthen', 'require', 'ifreq', 'issome', 'inline', 'ifq', 'thenopt', 'letswap', 'fieldswap', 'reread', 'reuse', 'opswap']

if __name__ == '__main__':
    a = sys.argv[1:]; src, out = a[0], a[1]; fl = 283; rules = RULES
    if '--from-line' in a: fl = int(a[a.index('--from-line') + 1])
    if '--rules' in a: rules = a[a.index('--rules') + 1].split(',')
    s = open(src).read(); g = Gen(s, fl); vs = g.run(rules)
    os.makedirs(out, exist_ok=True)
    for v in vs:
        open(f"{out}/{v['name']}.py", 'w').write('EDITS=' + repr(v['edits']) + '\n')
    json.dump([{k: v[k] for k in ('name', 'rule', 'line', 'from', 'to')} for v in vs], open(f'{out}/manifest.json', 'w'), indent=0)
    from collections import Counter
    print(len(vs), dict(Counter(v['rule'] for v in vs)))
