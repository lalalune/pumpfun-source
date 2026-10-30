"""A failed dependency-cache check must not publish a successful build report."""

import tempfile
import unittest
from pathlib import Path

from pump_build_verified import finish_report
from pump_dependency_cache import DependencyCache


class AcceptedCache:
    record = {"status": "hit"}

    def finish(self, target, log, report):
        self.report_seen = report.exists()


class BuildReportCleanupTests(unittest.TestCase):
    def test_cache_rejection_removes_preliminary_success_report(self):
        with tempfile.TemporaryDirectory(prefix="pump-build-report-") as temporary:
            output = Path(temporary)
            report = output / "build-comparison.json"
            receipt = output / "build-attempt.json"
            external = output / "external"
            external.mkdir()
            (external / "source.rs").write_text("pub fn current() {}\n")
            cache = DependencyCache.__new__(DependencyCache)
            cache.record = {"status": "miss"}
            cache.sources = {
                str(external): {"source.rs": "stale sha256"},
            }

            # Normal Python stops at the source-integrity assertion. Under -O,
            # the same deliberately incomplete cache reaches the missing log.
            with self.assertRaises((AssertionError, FileNotFoundError)):
                finish_report(
                    {"returncode": 0},
                    report,
                    receipt,
                    cache,
                    output / "target",
                    output / "build.log",
                    data_order=False,
                )

            self.assertFalse(report.exists())

    def test_accepted_cache_keeps_the_completed_report(self):
        with tempfile.TemporaryDirectory(prefix="pump-build-report-") as temporary:
            output = Path(temporary)
            report = output / "build-comparison.json"
            cache = AcceptedCache()

            finish_report(
                {"returncode": 0},
                report,
                output / "build-attempt.json",
                cache,
                output / "target",
                output / "build.log",
                data_order=False,
            )

            self.assertTrue(cache.report_seen)
            self.assertTrue(report.exists())


if __name__ == "__main__":
    unittest.main()
