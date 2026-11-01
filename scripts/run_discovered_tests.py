"""Run one unittest discovery pattern and require the case count it ships.

`python -m unittest discover -s <dir> -p <pattern>` exits 0 as long as the cases
it did find pass, so a module renamed, moved or made empty leaves the step green
with fewer cases than the patterns were written for. Callers state the count
their pattern must keep discovering.
"""
import argparse
import sys
import unittest
from pathlib import Path


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('start', type=Path, help='Directory discovery starts in')
    parser.add_argument('pattern', help='Module file pattern, e.g. test_triage*.py')
    parser.add_argument('--expect', type=int, required=True,
                        help='Case count the pattern must discover')
    options = parser.parse_args(argv)
    if options.expect <= 0:
        parser.error('--expect must be positive')
    suite = unittest.defaultTestLoader.discover(
        str(options.start), pattern=options.pattern, top_level_dir=str(options.start))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f'Expected {options.expect} cases; ran {result.testsRun}; '
          f'skipped {len(result.skipped)}', file=sys.stderr)
    passed = result.wasSuccessful() and result.testsRun == options.expect and not result.skipped
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
