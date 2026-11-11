"""Tests for the per-request timing log. No network: urlopen is faked.

    python3 -m unittest discover -s tests
"""

import io
import json
import socket
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import harvest  # noqa: E402
import timing_report  # noqa: E402

PAGE_URL = ("http://web.archive.org/cdx/search/cdx?url=jolly.house.gov"
            "&page=3&pageSize=100")
COUNT_URL = ("http://web.archive.org/cdx/search/cdx?url=jolly.house.gov"
             "&showNumPages=true")


class Answer(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def answers(*results):
    """A fake urlopen that answers, or raises, each result in turn."""
    queue = list(results)

    def urlopen(request, timeout=None):
        result = queue.pop(0)
        if isinstance(result, Exception):
            raise result
        return Answer(result.encode())
    return urlopen


class TimingLogTest(unittest.TestCase):
    def setUp(self):
        self.log = Path(tempfile.mkdtemp()) / "requests.jsonl"
        for patcher in (mock.patch.object(harvest, "TIMING_LOG", self.log),
                        mock.patch.object(harvest.time, "sleep", lambda s: None)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def lines(self):
        return [json.loads(x) for x in self.log.read_text().splitlines()]

    def test_every_try_is_one_line_with_how_it_ended(self):
        http503 = urllib.error.HTTPError(PAGE_URL, 503, "busy", {}, None)
        timeout = urllib.error.URLError(socket.timeout("timed out"))
        with mock.patch.object(harvest.urllib.request, "urlopen",
                               answers(http503, timeout, "a b c d e\n")):
            harvest.fetch(PAGE_URL)
        got = self.lines()
        self.assertEqual([r["result"] for r in got], ["http503", "timeout", "ok"])
        self.assertEqual([r["try"] for r in got], [1, 2, 3])
        self.assertEqual({r["kind"] for r in got}, {"page 3"})
        self.assertEqual({r["host"] for r in got}, {"jolly.house.gov"})
        self.assertEqual(got[-1]["bytes"], len("a b c d e\n"))

    def test_the_offline_page_is_logged_as_html(self):
        with mock.patch.object(harvest.urllib.request, "urlopen",
                               answers("<html>offline", "<html>", "<html>")):
            with self.assertRaises(RuntimeError):
                harvest.fetch(COUNT_URL)
        self.assertEqual({(r["kind"], r["result"]) for r in self.lines()},
                         {("count", "html")})

    def test_no_log_when_turned_off(self):
        with mock.patch.object(harvest, "TIMING_LOG", None), \
             mock.patch.object(harvest.urllib.request, "urlopen",
                               answers("a b c d e\n")):
            harvest.fetch(PAGE_URL)
        self.assertFalse(self.log.exists())

    def test_an_unwritable_log_never_fails_the_request(self):
        with mock.patch.object(harvest, "TIMING_LOG",
                               Path("/nonexistent/dir/requests.jsonl")), \
             mock.patch.object(harvest.urllib.request, "urlopen",
                               answers("a b c d e\n")):
            self.assertEqual(harvest.fetch(PAGE_URL), "a b c d e\n")


class ReportTest(unittest.TestCase):
    def test_time_is_attributed_to_how_requests_ended(self):
        rows = [{"t": 1000, "s": 10, "pid": 1, "host": "a", "kind": "page 0",
                 "try": 1, "result": "ok", "bytes": 5},
                {"t": 1010, "s": 300, "pid": 1, "host": "a", "kind": "page 1",
                 "try": 1, "result": "timeout", "bytes": 0},
                {"t": 1400, "s": 5, "pid": 2, "host": "b", "kind": "count",
                 "try": 1, "result": "http503", "bytes": 0}]
        text = timing_report.report(rows)
        self.assertIn("3 requests", text)
        self.assertIn("2 harvest process(es)", text)
        first_result = text.splitlines()[3]
        self.assertTrue(first_result.startswith("timeout"))  # most time first
        self.assertIn("count requests: 1, failed 1 (100%)", text)

    def test_empty(self):
        self.assertIn("No requests", timing_report.report([]))


if __name__ == "__main__":
    unittest.main()
