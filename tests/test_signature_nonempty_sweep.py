"""No tracked Python may treat a transaction with no signatures as signed.

``solders`` returns an empty result list for a transaction whose signature is
absent, and ``all([])`` is true, so ``all(tx.verify_with_results())`` accepted a
stripped transaction. The guard is the signature vector itself: ``tx.signatures
and all(...)``, or, where the results are held in a variable, ``results and
all(results)``.

Every tracked Python file under ``scripts``, ``reconstruction``, ``tests`` and
``research`` is parsed, including the source of ``-c`` drivers held as string
constants. A guard may sit in the same condition (``tx.signatures and
all(...)``, ``not checks or not all(checks)``, ``len(results) > 0 and
all(results)``), in an earlier statement of the same block
(``self.assertTrue(results)``), or in a branch that calls a module-level helper
which can only leave by raising (``fail(msg)``). Docstrings are prose, not code,
and are not parsed.

This is a bounded conservative lint of explicit local verification bindings and
pure boolean/length predicates, not a proof of arbitrary Python control flow,
aliases or called functions. The one called-function proof it does make stays
inside the file: a module-level helper counts only when every path through its
body raises. Unknown effects and overwritten bindings cannot supply a proof.
Runtime signature verification and exact header counts remain separate
admission checks.
"""
import ast
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKED_ROOTS = ('scripts', 'reconstruction', 'tests', 'research')
# These files assert that all() of an empty or partial vector is true, then
# assert that the strong guard rejects the same transaction: the demonstration
# is the counter-example, not a signature check.
DEMONSTRATIONS = {
    'reconstruction/pump-main/lanes/v3-sell-payment-layout/test_external_inputs.py',
    'research/runtime-mayhem-typed-receipts-20261101/probe.py',
    'tests/test_signature_nonempty_sweep.py',
}
# Verbatim copies of a checkout's scripts kept for provenance under a
# ``runtime/inputs/upstream`` directory. Nothing in this repository imports or
# runs them; they record what the producer shipped, so they stay as they are.
UPSTREAM_ARCHIVES = {
    'research/pump-multihop-sell-fees-20261029/runtime/inputs/upstream/tools/focused.py',
    'research/pump-multihop-token-quote-20261029/runtime/inputs/upstream/tools/focused.py',
}

CALL_NAMES = {'exec', 'eval', 'compile', 'run', 'check_output', 'check_call', 'Popen', 'call'}


def tracked_python():
    """Every tracked ``.py`` under the scanned roots, listed by git."""
    listed = subprocess.run(['git', 'ls-files', '--', *TRACKED_ROOTS], cwd=ROOT,
                            text=True, capture_output=True, check=True).stdout.split()
    return [ROOT / path for path in listed if path.endswith('.py')]


def results_source(node):
    """The receiver of a ``verify_with_results()`` call, or None.

    ``tx.verify_with_results()`` and ``list(tx.verify_with_results())`` both
    yield ``tx``.
    """
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Attribute) and node.func.attr == 'verify_with_results':
        return ast.unparse(node.func.value)
    if (isinstance(node.func, ast.Name) and node.func.id == 'list'
            and len(node.args) == 1 and isinstance(node.args[0], ast.Call)
            and isinstance(node.args[0].func, ast.Attribute)
            and node.args[0].func.attr == 'verify_with_results'):
        return ast.unparse(node.args[0].func.value)
    return None


def own_nodes(scope):
    """Traverse one lexical scope; another function's names prove nothing here."""
    yield scope
    for child in ast.iter_child_nodes(scope):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        yield from own_nodes(child)


def bound_vectors(scope):
    """Retain signature taint even if a name is later overwritten."""
    bound = {}
    for node in own_nodes(scope):
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
            targets, value = (node.target,), node.value
        else:
            continue
        source = results_source(value)
        if source is not None:
            for target in targets:
                if isinstance(target, ast.Name):
                    bound.setdefault(target.id, set()).add(source)
    return bound


_UNKNOWN = object()
_EMPTY = ()


def empty_values(node, vectors, known=None):
    """Conservatively evaluate a predicate with this signature vector empty.

    Unknown values have both truth values. Only explicit booleans, numeric
    comparisons and the documented pure builtins establish a proof. In
    particular an unknown required length may be zero.
    """
    known = {} if known is None else known
    if isinstance(node, ast.Name) and node.id in known:
        return {known[node.id]}
    text = ast.unparse(node)
    if text in vectors:
        return {_EMPTY}
    if isinstance(node, ast.Constant):
        return {node.value} if isinstance(node.value, (type(None), bool, int, float, str, bytes)) else {_UNKNOWN}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return {not value for value in empty_truth(node.operand, vectors, known)}
    if isinstance(node, ast.BoolOp):
        possible = {True} if isinstance(node.op, ast.And) else {False}
        for child in node.values:
            values = empty_truth(child, vectors, known)
            possible = ({False} if False in possible else set()) | values if isinstance(node.op, ast.And) else ({True} if True in possible else set()) | values
            # Do not evaluate later siblings on a definitely short-circuited path.
            if possible == ({False} if isinstance(node.op, ast.And) else {True}):
                break
        return possible
    if isinstance(node, ast.Compare):
        values, outcomes = empty_values(node.left, vectors, known), {True}
        for operator, right in zip(node.ops, node.comparators):
            others = empty_values(right, vectors, known)
            pair = set()
            for left in values:
                for value in others:
                    if left is _UNKNOWN or value is _UNKNOWN:
                        pair.update((False, True))
                        continue
                    try:
                        if isinstance(operator, ast.Eq): answer = left == value
                        elif isinstance(operator, ast.NotEq): answer = left != value
                        elif isinstance(operator, ast.Gt): answer = left > value
                        elif isinstance(operator, ast.GtE): answer = left >= value
                        elif isinstance(operator, ast.Lt): answer = left < value
                        elif isinstance(operator, ast.LtE): answer = left <= value
                        elif isinstance(operator, ast.Is): answer = left is value
                        elif isinstance(operator, ast.IsNot): answer = left is not value
                        else: pair.update((False, True)); continue
                        pair.add(answer)
                    except TypeError:
                        pair.update((False, True))
            outcomes = {a and b for a in outcomes for b in pair}
            values = others
        return outcomes
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and len(node.args) == 1 and not node.keywords:
        name, arg = node.func.id, node.args[0]
        if name == 'bool': return empty_truth(arg, vectors, known)
        if name == 'len':
            return {0} if empty_values(arg, vectors, known) == {_EMPTY} else {_UNKNOWN}
        if name == 'list' and empty_values(arg, vectors, known) == {_EMPTY}: return {_EMPTY}
        if name == 'all' and (ast.unparse(arg) in vectors or empty_values(arg, vectors, known) == {_EMPTY}): return {True}
    return {_UNKNOWN}


def empty_truth(node, vectors, known=None):
    values = empty_values(node, vectors, known)
    return {b for value in values for b in ((False, True) if value is _UNKNOWN else (bool(value),))}


def predicate_truth(expression, vectors):
    """A conjunction's equalities can pin an otherwise unknown required count.

    If len(results)==required must hold and results is empty, required must
    be zero. An accompanying required>0 then rejects that empty case. No
    assumptions are imported across OR branches or executable side effects.
    """
    def conjuncts(node):
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            return [part for child in node.values for part in conjuncts(child)]
        return [node]
    parts = conjuncts(expression)
    known = {}
    for _ in parts:
        changed = False
        for part in parts:
            if not isinstance(part, ast.Compare) or not all(isinstance(op, ast.Eq) for op in part.ops):
                continue
            operands = [part.left, *part.comparators]
            values = [empty_values(value, vectors, known) for value in operands]
            constants = [next(iter(value)) for value in values if len(value) == 1 and _UNKNOWN not in value]
            constants = [value for value in constants if isinstance(value, (int, float))]
            if not constants:
                continue
            for operand in operands:
                if isinstance(operand, ast.Name) and operand.id not in known and operand.id not in vectors:
                    known[operand.id] = constants[0]
                    changed = True
        if not changed: break
    return empty_truth(expression, vectors, known)


def mentions_vector(node, vectors):
    return any(ast.unparse(child) in vectors for child in ast.walk(node))


def impure(node):
    if isinstance(node, (ast.NamedExpr, ast.Await, ast.Yield, ast.YieldFrom)):
        return True
    if not isinstance(node, ast.Call):
        return False
    if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {'Transaction', 'VersionedTransaction'} and node.func.attr == 'from_bytes'):
        return False
    if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
            and node.func.value.id == 'self' and node.func.attr in {'assertTrue', 'assertFalse'}):
        return False
    return not ((isinstance(node.func, ast.Name) and node.func.id in {'all', 'bool', 'len', 'list', 'bytes'})
                or (isinstance(node.func, ast.Attribute) and node.func.attr == 'verify_with_results'))


def effects_before(expression, target):
    """Call effects occur after their arguments; an enclosing call is later."""
    effects = []
    def visit(node):
        if node is target:
            return True
        for child in ast.iter_child_nodes(node):
            if visit(child): return True
        if impure(node): effects.append(node)
        return False
    visit(expression)
    return effects


def rejects_branch(statements, helpers=frozenset()):
    """Prove a raise on every path; trailing unreachable raise is not proof."""
    for statement in statements:
        if isinstance(statement, ast.Raise):
            return True
        if isinstance(statement, ast.Expr) and raises_through(statement.value, helpers):
            return True
        if isinstance(statement, (ast.Return, ast.Break, ast.Continue)):
            return False
        if isinstance(statement, ast.If):
            if rejects_branch(statement.body, helpers) and rejects_branch(statement.orelse, helpers):
                return True
            if any(isinstance(child, (ast.Return, ast.Break, ast.Continue, ast.Yield, ast.YieldFrom))
                   for child in ast.walk(statement)):
                return False
        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Match)):
            return False
    return False


def raises_through(node, helpers):
    """Only a statically bound local raising helper supplies a call proof."""
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id in helpers
    return ('sys.exit' in helpers and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'exit' and isinstance(node.func.value, ast.Name)
            and node.func.value.id == 'sys')


def raising_helpers(tree):
    """Module-level names whose bodies can only leave by raising.

    ``fail(msg)`` wrappers hide the ``raise`` from the branch walk, so the
    branch looks like it falls through and the guard is reported as missing.
    Resolving the local definition keeps the proof inside the file: a helper
    that can return normally is still not a proof, and a name imported from
    elsewhere is never assumed to raise.
    """
    definitions = [node for node in ast.walk(tree)
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    rebound = {node.id for node in ast.walk(tree)
               if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))}
    rebound.update(node.arg for node in ast.walk(tree) if isinstance(node, ast.arg))
    rebound.update(alias.asname or alias.name.split('.')[0]
                   for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                   for alias in node.names)
    functions = {node.name: node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and not node.decorator_list
                 and node.name not in rebound
                 and sum(d.name == node.name for d in definitions) == 1
                 and not any(isinstance(child, (ast.Yield, ast.YieldFrom))
                             for child in ast.walk(node))}
    # A sys.exit call is usable only with an ordinary stable import. Explicit
    # rebinding, parameter shadowing and exit replacement invalidate the proof.
    sys_imports = [n for n in tree.body if isinstance(n, ast.Import)
                   and any(a.name == 'sys' and a.asname is None for a in n.names)]
    unstable_sys = any(
        (isinstance(n, ast.Name) and n.id == 'sys' and isinstance(n.ctx, (ast.Store, ast.Del)))
        or (isinstance(n, ast.arg) and n.arg == 'sys')
        or (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
            and n.value.id == 'sys' and n.attr == 'exit'
            and isinstance(n.ctx, (ast.Store, ast.Del)))
        or (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == 'sys')
        or (isinstance(n, (ast.Import, ast.ImportFrom))
            and any((a.asname or a.name.split('.')[0]) == 'sys'
                    and not (isinstance(n, ast.Import) and a.name == 'sys' and a.asname is None)
                    for a in n.names))
        for n in ast.walk(tree))
    raising = {'sys.exit'} if sys_imports and not unstable_sys else set()
    changed = True
    while changed:                      # helpers that call other helpers
        changed = False
        for name, node in functions.items():
            if name not in raising and rejects_branch(node.body, raising):
                raising.add(name)
                changed = True
    return frozenset(raising)


def explicit_vector_test(expression, vectors):
    """The vector occurs outside all(); negating all() alone is not a guard."""
    def visit(node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'all':
            return False
        if ast.unparse(node) in vectors:
            return True
        return any(visit(child) for child in ast.iter_child_nodes(node))
    return visit(expression)


def condition_guard(node, child, vectors, parents, helpers=frozenset()):
    target = child
    current = child
    while parents.get(id(current)) is not None and not isinstance(parents[id(current)], ast.stmt):
        current = parents[id(current)]
    statement = parents.get(id(current))
    if isinstance(statement, ast.Assert):
        expression = statement.test
    elif isinstance(statement, ast.If) and current is statement.test:
        expression = statement.test
    else:
        # The nearest enclosing boolean expression is the local predicate.
        expression = child
        for parent in iter_parents(child, parents):
            if isinstance(parent, ast.stmt): break
            if isinstance(parent, ast.BoolOp): expression = parent
    if not explicit_vector_test(expression, vectors) or effects_before(expression, target):
        return False
    result = predicate_truth(expression, vectors)
    if isinstance(statement, ast.If) and expression is statement.test:
        if rejects_branch(statement.body, helpers):
            return result == {True}
        if rejects_branch(statement.orelse, helpers):
            return result == {False}
    return result == {False}


def iter_parents(node, parents):
    while id(node) in parents:
        node = parents[id(node)]
        yield node


def writes(node, names):
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)) and child.id in names:
            return True
        if isinstance(child, (ast.Attribute, ast.Subscript)) and isinstance(child.ctx, (ast.Store, ast.Del)):
            if any(isinstance(part, ast.Name) and part.id in names for part in ast.walk(child.value)):
                return True
    return False


def most_recent_binding(node, name, parents, blocks):
    """Return the current direct verification binding and stable receiver proof."""
    current, intervening = node, []
    while current is not None:
        if id(current) in blocks:
            block, index = blocks[id(current)]
            for earlier in reversed(block[:index]):
                if not writes(earlier, {name}):
                    intervening.append(earlier)
                    continue
                if isinstance(earlier, (ast.Assign, ast.AnnAssign)):
                    source = results_source(earlier.value)
                    if source is None:
                        return None, False
                    receiver = ast.parse(source, mode='eval').body
                    names = {part.id for part in ast.walk(receiver) if isinstance(part, ast.Name)}
                    receiver_stable = isinstance(receiver, (ast.Name, ast.Attribute)) and not any(
                        writes(stmt, names) or any(impure(part) for part in ast.walk(stmt))
                        for stmt in intervening)
                    # Do not certify a vector which a call or write could have
                    # changed since verification, even if it is tested again.
                    if any(writes(stmt, {name}) or any(impure(part) for part in ast.walk(stmt)) for stmt in intervening):
                        return None, False
                    return source, receiver_stable
                return None, False
        current = parents.get(id(current))
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            break
    return None, False


def statement_guard(node, vectors, parents, blocks, helpers=frozenset()):
    while node is not None and not isinstance(node, ast.stmt):
        node = parents.get(id(node))
    if node is None or id(node) not in blocks:
        return False
    block, index = blocks[id(node)]
    names = {child.id for text in vectors for child in ast.walk(ast.parse(text, mode='eval')) if isinstance(child, ast.Name)}
    for earlier in reversed(block[:index]):
        expression, polarity = None, False
        if isinstance(earlier, ast.Assert):
            expression = earlier.test
        elif isinstance(earlier, ast.Expr) and isinstance(earlier.value, ast.Call):
            call = earlier.value
            name = call.func.attr if isinstance(call.func, ast.Attribute) else None
            if name in {'assertTrue', 'assertFalse'} and call.args:
                expression, polarity = call.args[0], name == 'assertFalse'
        elif isinstance(earlier, ast.If) and rejects_branch(earlier.body, helpers):
            expression, polarity = earlier.test, True
        if expression is not None and explicit_vector_test(expression, vectors):
            if not any(impure(n) for n in ast.walk(expression)) and predicate_truth(expression, vectors) == {polarity}:
                return True
        if writes(earlier, names) or any(impure(n) for n in ast.walk(earlier)):
            break
    return False


def statement_blocks(tree):
    blocks = {}
    for node in ast.walk(tree):
        for attribute in ('body', 'orelse', 'finalbody'):
            block = getattr(node, attribute, None)
            if not isinstance(block, list) or not block or not isinstance(block[0], ast.stmt):
                continue
            for index, statement in enumerate(block):
                blocks[id(statement)] = (block, index)
    return blocks


def unsigned_gates(tree, location):
    """Every ``all(...)`` over signature results with no non-empty test."""
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
    blocks = statement_blocks(tree)
    helpers = raising_helpers(tree)
    scopes = {}
    for node in ast.walk(tree):
        if (not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name)
                or node.func.id != 'all' or len(node.args) != 1):
            continue
        scope = next((p for p in iter_parents(node, parents) if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.Module))), tree)
        if id(scope) not in scopes:
            scopes[id(scope)] = bound_vectors(scope)
        bound = scopes[id(scope)]
        argument = node.args[0]
        source = results_source(argument)
        if source is not None:
            vectors = {ast.unparse(argument), source + '.signatures'}
        elif isinstance(argument, ast.Name) and argument.id in bound:
            source, stable = most_recent_binding(node, argument.id, parents, blocks)
            if source is None:
                yield f'{location}{node.lineno}'
                continue
            vectors = {argument.id}
            if stable:
                vectors.add(source + '.signatures')
        else:
            continue
        if condition_guard(parents.get(id(node)), node, vectors, parents, helpers):
            continue
        if statement_guard(node, vectors, parents, blocks, helpers):
            continue
        yield f'{location}{node.lineno}'


def string_constants(tree):
    names = {}
    for node in ast.walk(tree):
        value = getattr(node, 'value', None)
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) else [])
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            for target in targets:
                if isinstance(target, ast.Name):
                    names[target.id] = value
    return names


def driver_sources(tree):
    """String constants executed as Python: ``exec``/``eval``/``compile``/``-c``."""
    names = string_constants(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        name = (function.attr if isinstance(function, ast.Attribute)
                else function.id if isinstance(function, ast.Name) else None)
        if name not in CALL_NAMES:
            continue
        candidates = []
        if name in ('exec', 'eval', 'compile') and node.args:
            candidates.append(node.args[0])
        for argument in node.args:
            if not isinstance(argument, (ast.List, ast.Tuple)):
                continue
            for index, item in enumerate(argument.elts[:-1]):
                if isinstance(item, ast.Constant) and item.value == '-c':
                    candidates.append(argument.elts[index + 1])
        for candidate in candidates:
            if isinstance(candidate, ast.Constant) and isinstance(candidate.value, str):
                yield candidate.value, candidate.lineno
            elif isinstance(candidate, ast.Name) and candidate.id in names:
                yield names[candidate.id].value, names[candidate.id].lineno


def unsigned_gates_in(path):
    text = path.read_text(encoding='utf-8')
    if 'verify_with_results' not in text:
        return
    tree = ast.parse(text, filename=str(path))
    yield from unsigned_gates(tree, '')
    for source, line in driver_sources(tree):
        try:
            driver = ast.parse(source)
        except SyntaxError:
            continue
        yield from unsigned_gates(driver, f'driver@{line}:')


class SignatureGuardTests(unittest.TestCase):
    def test_every_signature_check_rejects_an_unsigned_transaction(self):
        offenders = []
        for path in tracked_python():
            relative = str(path.relative_to(ROOT))
            if relative in DEMONSTRATIONS or relative in UPSTREAM_ARCHIVES:
                continue
            offenders.extend(f'{relative}:{where}' for where in unsigned_gates_in(path))
        self.assertEqual(offenders, [], 'test the signature vector before all() of its results')

    def test_accepts_a_branch_that_calls_a_raising_helper(self):
        def gates(source):
            return list(unsigned_gates(ast.parse(source), ''))
        self.assertEqual(gates('def fail(msg):\n'
                               '    raise SystemExit(msg)\n'
                               'results = tx.verify_with_results()\n'
                               'if not results or not all(results):\n'
                               '    fail("unsigned")\n'), [])
        # A helper may call another one, in any definition order.
        self.assertEqual(gates('def stop(msg):\n'
                               '    fail(msg)\n'
                               'def fail(msg):\n'
                               '    raise SystemExit(msg)\n'
                               'results = tx.verify_with_results()\n'
                               'if not results or not all(results):\n'
                               '    stop("unsigned")\n'), [])
        # A helper that can return normally proves nothing.
        self.assertEqual(gates('def note(msg):\n'
                               '    print(msg)\n'
                               'if not all(tx.verify_with_results()):\n'
                               '    note("unsigned")\n'), ['3'])
        # Neither does a name imported from somewhere else.
        self.assertEqual(gates('from helpers import fail\n'
                               'if not all(tx.verify_with_results()):\n'
                               '    fail("unsigned")\n'), ['2'])

    def test_unstable_or_lazy_helpers_supply_no_rejection_proof(self):
        base = ('results=tx.verify_with_results()\n'
                'if not results or not all(results):\n fail("unsigned")\n')
        prefixes = (
            'def fail(msg):\n yield 1\n raise SystemExit(msg)\n',
            '@lambda f: (lambda *a: None)\ndef fail(msg):\n raise SystemExit(msg)\n',
            'def fail(msg):\n raise SystemExit(msg)\nfail=lambda *a: None\n',
            'def fail(msg):\n raise SystemExit(msg)\ndef fail(msg):\n return None\n',
            'def fail(msg):\n sys.exit(msg)\n',
        )
        for prefix in prefixes:
            self.assertTrue(list(unsigned_gates(ast.parse(prefix + base), '')))
        shadowed = ('def fail(msg):\n raise SystemExit(msg)\n'
                    'def check(tx, fail):\n results=tx.verify_with_results()\n'
                    ' if not results or not all(results):\n  fail("unsigned")\n')
        self.assertTrue(list(unsigned_gates(ast.parse(shadowed), '')))
        stable = 'import sys\ndef fail(msg):\n sys.exit(msg)\n'
        self.assertEqual(list(unsigned_gates(ast.parse(stable + base), '')), [])
        for rebind in ('sys=object()\n', 'sys.exit=lambda *a: None\n'):
            self.assertTrue(list(unsigned_gates(ast.parse(stable + rebind + base), '')))

    def test_the_sweep_accepts_only_a_non_empty_test(self):
        def gates(source):
            return list(unsigned_gates(ast.parse(source), ''))
        self.assertEqual(gates('assert all(tx.verify_with_results())\n'), ['1'])
        self.assertEqual(gates('assert tx.signatures and all(tx.verify_with_results())\n'), [])
        self.assertEqual(gates('if not tx.signatures or not all(tx.verify_with_results()):\n'
                               '    raise ValueError\n'), [])
        self.assertEqual(gates('if tx.signatures or all(tx.verify_with_results()):\n'
                               '    pass\n'), ['1'])
        self.assertEqual(gates('checks = tx.verify_with_results()\n'
                               'assert not checks\n'
                               'assert all(checks)\n'), ['3'])

    def test_rejects_resealed_polarity_length_and_reset_false_proofs(self):
        unsafe = [
            'assert not tx.signatures or all(tx.verify_with_results())',
            'checks=tx.verify_with_results()\nassert len(checks)==0 and all(checks)',
            'checks=tx.verify_with_results()\nassert checks\nchecks=[]\nassert all(checks)',
            'checks=tx.verify_with_results()\nassert len(checks)>=0 and all(checks)',
            'checks=tx.verify_with_results()\nassert len(checks)==required and all(checks)',
            'checks=tx.verify_with_results()\nassert checks\nchecks.clear()\nassert all(checks)',
            'assert tx.signatures\ntx.signatures=[]\nassert all(tx.verify_with_results())',
            'if not all(tx.verify_with_results()):\n    raise ValueError',
        ]
        for source in unsafe:
            with self.subTest(source=source):
                self.assertTrue(list(unsigned_gates(ast.parse(source), '')))

    def test_accepts_only_actual_positive_local_guards(self):
        safe = [
            'verified=bool(tx.signatures) and all(tx.verify_with_results())',
            'checks=tx.verify_with_results()\nassert checks and all(checks)',
            'checks=tx.verify_with_results()\nassert len(checks)>0 and all(checks)',
            'checks=tx.verify_with_results()\nassert len(checks)==2 and all(checks)',
            'checks=tx.verify_with_results()\nassert required>0 and len(checks)==required and all(checks)',
            'checks=tx.verify_with_results()\nself.assertTrue(checks)\nassert all(checks)',
            'checks=tx.verify_with_results()\nassert checks\nassert all(checks)',
            'checks=tx.verify_with_results()\ndecoded=VersionedTransaction.from_bytes(raw)\nassert checks and all(checks)',
        ]
        for source in safe:
            with self.subTest(source=source):
                self.assertEqual(list(unsigned_gates(ast.parse(source), '')), [])
        # Another function's local name must not taint an ordinary all().
        source = ('def signed(tx):\n    checks=tx.verify_with_results()\n    assert checks and all(checks)\n'
                  'def ordinary():\n    checks=[True]\n    return all(checks)')
        self.assertEqual(list(unsigned_gates(ast.parse(source), '')), [])

    def test_unreachable_raise_is_not_a_rejecting_branch(self):
        for early in ('return True', 'continue', 'break'):
            source = ('def gate(tx):\n    for _ in (1,):\n'
                      '        if not tx.signatures or not all(tx.verify_with_results()):\n'
                      f'            {early}\n            raise ValueError')
            with self.subTest(exit=early):
                self.assertTrue(list(unsigned_gates(ast.parse(source), '')))
        source = ('if not tx.signatures or not all(tx.verify_with_results()):\n'
                  '    if other:\n        return True\n    raise ValueError')
        self.assertTrue(list(unsigned_gates(ast.parse(source), '')))

    def test_literal_python_drivers_are_checked_without_execution(self):
        source = "checks=tx.verify_with_results()\nassert len(checks)==0 and all(checks)"
        wrapper = ast.parse('driver=' + repr(source) + '\nexec(driver)')
        drivers = list(driver_sources(wrapper))
        self.assertEqual(len(drivers), 1)
        self.assertTrue(list(unsigned_gates(ast.parse(drivers[0][0]), 'driver:')))

    def test_real_signed_and_stripped_vectors(self):
        from solders.compute_budget import set_compute_unit_limit
        from solders.hash import Hash
        from solders.keypair import Keypair
        from solders.transaction import Transaction
        payer = Keypair.from_seed(bytes([29]) * 32)
        signed = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000)], payer.pubkey(), [payer], Hash.default())
        stripped = Transaction.populate(signed.message, [])
        self.assertTrue(signed.signatures and all(signed.verify_with_results()))
        self.assertEqual(list(stripped.verify_with_results()), [])
        self.assertTrue(all(stripped.verify_with_results()))
        self.assertFalse(stripped.signatures and all(stripped.verify_with_results()))

    def test_the_guard_is_what_makes_an_empty_vector_false(self):
        class Stripped:
            signatures = []
            def verify_with_results(self): return []
        stripped = Stripped()
        self.assertTrue(all(stripped.verify_with_results()))
        self.assertFalse(stripped.signatures and all(stripped.verify_with_results()))
        held = stripped.verify_with_results()
        self.assertTrue(all(held))
        self.assertFalse(held and all(held))


if __name__ == '__main__':
    unittest.main()
