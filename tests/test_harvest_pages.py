"""Tests for keeping CDX pages across failed passes.

No network: ``fetch`` (the page count) and ``cdx_rows`` (one page) are
replaced by fakes, and ``time.sleep`` by a no-op.

    python3 -m unittest discover -s tests
"""

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import harvest  # noqa: E402

HOST = "example.house.gov"


def row(url):
    return {"url": url, "timestamp": "20200101000000",
            "mimetype": "application/pdf", "length": "1", "digest": "X"}


class FakeCDX:
    """Five pages, two rows each; ``bad`` pages raise; every call is logged."""

    def __init__(self, pages=5, bad=()):
        self.pages = pages
        self.bad = set(bad)
        self.asked: list[int] = []

    def fetch(self, url, timeout=None):
        return str(self.pages)

    def cdx_rows(self, host, page=None, page_size=None, **_):
        self.asked.append(page)
        if page in self.bad:
            raise ConnectionResetError("reset by peer")
        return [row(f"{host}/p{page}-a-letter.pdf"),
                row(f"{host}/p{page}-b-letter.pdf")]


class PagedWalkTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.partial = harvest.partial_path_for(self.dir, HOST)
        patcher = mock.patch.object(harvest.time, "sleep", lambda s: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def walk(self, cdx):
        with mock.patch.object(harvest, "fetch", cdx.fetch), \
             mock.patch.object(harvest, "cdx_rows", cdx.cdx_rows):
            return harvest.cdx_rows_paged(HOST, pause=0,
                                          partial_path=self.partial)

    def test_a_retry_asks_only_for_the_page_that_failed(self):
        first = FakeCDX(bad={3})
        with self.assertRaises(RuntimeError) as caught:
            self.walk(first)
        self.assertIn("page 3 of 5", str(caught.exception))
        self.assertIn("4 of 5 pages kept", str(caught.exception))

        second = FakeCDX()
        rows = self.walk(second)
        self.assertEqual(second.asked, [3])
        self.assertEqual(len(rows), 10)

    def test_the_result_matches_an_uninterrupted_walk(self):
        clean = Path(tempfile.mkdtemp())
        with mock.patch.object(harvest, "fetch", FakeCDX().fetch), \
             mock.patch.object(harvest, "cdx_rows", FakeCDX().cdx_rows):
            whole = harvest.cdx_rows_paged(
                HOST, pause=0, partial_path=harvest.partial_path_for(clean, HOST))
        with self.assertRaises(RuntimeError):
            self.walk(FakeCDX(bad={0}))
        resumed = self.walk(FakeCDX())
        self.assertEqual(resumed, whole)

    def test_a_host_with_a_missing_page_still_fails(self):
        # The page cache changes what a retry asks for, never what counts as
        # finished: four pages of five is not a result.
        with self.assertRaises(RuntimeError):
            self.walk(FakeCDX(bad={4}))

    def test_two_failures_in_a_row_stop_the_walk(self):
        cdx = FakeCDX(bad={1, 2})
        with self.assertRaises(RuntimeError):
            self.walk(cdx)
        # Each failed page is tried 3 times; nothing after page 2 is asked.
        self.assertEqual(cdx.asked, [0, 1, 1, 1, 2, 2, 2])

    def test_one_failure_carries_on_to_later_pages(self):
        cdx = FakeCDX(bad={1})
        with self.assertRaises(RuntimeError):
            self.walk(cdx)
        self.assertEqual(sorted(set(cdx.asked)), [0, 1, 2, 3, 4])

    def test_a_changed_page_count_starts_over(self):
        with self.assertRaises(RuntimeError):
            self.walk(FakeCDX(bad={4}))
        grown = FakeCDX(pages=6)
        self.walk(grown)
        self.assertEqual(grown.asked, [0, 1, 2, 3, 4, 5])

    def test_old_saved_pages_are_not_trusted(self):
        with self.assertRaises(RuntimeError):
            self.walk(FakeCDX(bad={4}))
        saved = json.loads(self.partial.read_text())
        saved["started"] = time.time() - harvest.PARTIAL_MAX_AGE - 60
        self.partial.write_text(json.dumps(saved))
        cdx = FakeCDX()
        self.walk(cdx)
        self.assertEqual(cdx.asked, [0, 1, 2, 3, 4])

    def test_another_hosts_pages_are_not_used(self):
        with self.assertRaises(RuntimeError):
            self.walk(FakeCDX(bad={4}))
        saved = json.loads(self.partial.read_text())
        saved["host"] = "someone-else.house.gov"
        self.partial.write_text(json.dumps(saved))
        cdx = FakeCDX()
        self.walk(cdx)
        self.assertEqual(cdx.asked, [0, 1, 2, 3, 4])


class HarvestHostTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        patcher = mock.patch.object(harvest.time, "sleep", lambda s: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_host(self, cdx):
        with mock.patch.object(harvest, "fetch", cdx.fetch), \
             mock.patch.object(harvest, "cdx_rows", cdx.cdx_rows):
            return harvest.harvest_host({"host": HOST, "bioguide": "X000001"},
                                        self.dir)

    def test_failure_is_cached_as_an_error_and_pages_are_kept(self):
        result = self.run_host(FakeCDX(bad={2}))
        self.assertIn("error", result)
        entry = harvest.read_cache(self.dir / f"{HOST}.json")
        self.assertIn("error", entry)
        self.assertTrue(harvest.partial_path_for(self.dir, HOST).exists())

    def test_success_writes_the_entry_and_removes_the_pages(self):
        self.run_host(FakeCDX(bad={2}))
        result = self.run_host(FakeCDX())
        self.assertEqual(result["method"], harvest.CACHE_METHOD)
        self.assertEqual(len(result["rows"]), 10)
        self.assertFalse(harvest.partial_path_for(self.dir, HOST).exists())

    def test_the_saved_pages_file_is_not_the_hosts_entry(self):
        # Anything that looks up <host>.json must never find the partial.
        partial = harvest.partial_path_for(self.dir, HOST)
        self.assertNotEqual(partial.name, f"{HOST}.json")
        self.assertNotEqual(partial.with_suffix(".tmp1").name,
                            (self.dir / f"{HOST}.json").with_suffix(".tmp1").name)


if __name__ == "__main__":
    unittest.main()
