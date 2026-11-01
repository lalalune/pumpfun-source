"""fnspan must slice execute's defining `define`, wherever its first call site sits.

mvscan.py and volscan.py enumerate execute's block labels from fnspan(t) and
mvend inserts moved blocks at fnspan's end. fnspan searched for the first
`@...execute...(` occurrence and took the define before it, so on a module
where an earlier function calls execute it returned that caller's span: the
scans enumerated and moved the caller's blocks and scored them as execute's.
Anchor the search on execute's defining define line and fail clearly when it
is never defined.
"""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import mv  # noqa: E402

EXEC = '@_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E('
CALLER = '\n'.join([
    'define internal fastcc void @dispatcher(ptr %0) #0 {',
    'entry:',
    f'  call internal fastcc void {EXEC}ptr %0)',
    '  ret void',
    '}',
    '',
])
EXECUTE = '\n'.join([
    f'define internal fastcc void {EXEC}ptr %0) #0 {{',
    'exec_entry:',
    '  br label %exec_mid',
    '',
    'exec_mid:',
    '  %moved = add i32 1, 2',
    '  br label %exec_tail',
    '',
    'exec_tail:',
    '  ret void',
    '}',
    '',
])
HEADER = '; captured module header\n'


def labels(t):
    a, b = mv.fnspan(t)
    return re.findall(r'\n([\w.$"-]+):', t[a:b])


class FnSpanTests(unittest.TestCase):
    def test_caller_first_module_spans_execute_not_the_caller(self):
        t = HEADER + CALLER + EXECUTE
        a, b = mv.fnspan(t)
        self.assertTrue(t[a:b].startswith('define internal fastcc void ' + EXEC))
        self.assertEqual(['exec_entry', 'exec_mid', 'exec_tail'], labels(t))

    def test_define_first_module_span_is_unchanged(self):
        t = HEADER + EXECUTE + CALLER
        a, b = mv.fnspan(t)
        self.assertTrue(t[a:b].startswith('define internal fastcc void ' + EXEC))
        self.assertEqual(['exec_entry', 'exec_mid', 'exec_tail'], labels(t))

    def test_declare_only_module_fails_loudly(self):
        t = HEADER + f'declare internal fastcc void {EXEC}ptr) #0\n\n' + CALLER
        with self.assertRaisesRegex(ValueError, 'no definition of admin_cto::execute'):
            mv.fnspan(t)

    def test_mvend_moves_the_block_inside_execute_on_a_caller_first_module(self):
        t = HEADER + CALLER + EXECUTE
        out = mv.mvend(t, 'exec_mid')
        dispatcher = out.split('define internal fastcc void ' + EXEC)[0]
        self.assertNotIn('%moved = add i32 1, 2', dispatcher)
        a, b = mv.fnspan(out)
        self.assertLess(out.index('%moved = add i32 1, 2', a),
                        out.index('\n}\n', a))
        self.assertLess(out.index('exec_tail:'), out.index('%moved = add i32 1, 2'))


    def test_repeated_labels_are_scoped_to_execute(self):
        t = HEADER + CALLER.replace('entry:', 'exec_mid:') + EXECUTE
        a, b = mv.fnspan(t)
        start, end = mv.span(t, 'exec_mid')
        self.assertLessEqual(a, start)
        self.assertLess(end, b)
        out = mv.mvend(t, 'exec_mid')
        self.assertEqual(t[:a], out[:a])
        self.assertLess(out.index('exec_tail:', a), out.index('%moved =', a))

    def test_move_after_stays_within_execute_with_repeated_labels(self):
        caller = CALLER.replace('entry:', 'exec_mid:')
        t = HEADER + caller + EXECUTE
        a, _ = mv.fnspan(t)
        out = mv.mvafter(t, 'exec_tail', 'exec_entry')
        self.assertEqual(t[:a], out[:a])
        self.assertLess(out.index('exec_tail:', a), out.index('exec_mid:', a))
        self.assertIn('\n}\n', out[a:])

    def test_last_block_is_bounded_and_move_to_end_is_unchanged(self):
        t = HEADER + CALLER + EXECUTE + CALLER.replace('@dispatcher', '@later')
        _, b = mv.fnspan(t)
        _, end = mv.span(t, 'exec_tail')
        self.assertEqual(b, end)
        self.assertEqual(t, mv.mvend(t, 'exec_tail'))


if __name__ == '__main__':
    unittest.main()
