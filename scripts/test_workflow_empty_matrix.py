import unittest
import check_workflow_inputs as check


class EmptyWorkflowMatrixTests(unittest.TestCase):
    def test_fully_excluded_matrix_has_no_script_references(self):
        source = """jobs:
  audit:
    strategy:
      matrix:
        os: [ubuntu-latest]
        exclude:
          - os: ubuntu-latest
    steps:
      - run: python scripts/not-run.py
"""
        self.assertEqual(check.references('test.yml', source), (set(), set()))

    def test_include_can_reintroduce_a_configuration(self):
        matrix = {'os': ['linux'], 'exclude': [{'os': 'linux'}], 'include': [{'os': 'linux', 'script': 'check.py'}]}
        self.assertEqual(check.matrix_rows({'strategy': {'matrix': matrix}}), [{'os': 'linux', 'script': 'check.py'}])

    def test_non_matrix_job_retains_one_configuration(self):
        self.assertEqual(check.matrix_rows({}), [{}])


if __name__ == '__main__': unittest.main()
