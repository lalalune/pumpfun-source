import unittest

from win import demangle


class MalformedDemangleTests(unittest.TestCase):
    def test_malformed_names_preserve_symbol_identity(self):
        for name in ('_ZNE', '_ZN0fooE', '_ZN4fooE', '_ZN3fooextraE',
                     '_ZN3foo0barE', '_ZN\u00b2fooE', '_ZN\u0663fooE',
                     '_ZN' + '9' * 5000 + 'fooE'):
            with self.subTest(name=name[:80]):
                self.assertEqual(demangle(name), name)

    def test_valid_paths_and_compiler_hashes_still_decode(self):
        for name, expected in (
                ('_ZN3foo3barE', 'foo::bar'),
                ('_ZN3foo17h0123456789abcdefE', 'foo'),
                ('_ZN17h0123456789abcdefE', ''),
                ('ordinary_symbol', 'ordinary_symbol')):
            with self.subTest(name=name):
                self.assertEqual(demangle(name), expected)


if __name__ == '__main__':
    unittest.main()
