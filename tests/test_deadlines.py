import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from stemed_deadlines import build, ics

TODAY = dt.date(2026, 11, 12)


def cal(*events: str) -> str:
    return "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", *events, "END:VCALENDAR"]) + "\r\n"


def event(uid: str, day: str, summary: str, url: str = "https://example.org/x", description: str = "") -> str:
    lines = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTART;VALUE=DATE:{day}", "SUMMARY:" + ics.escape(summary)]
    if description:
        lines.append("DESCRIPTION:" + ics.escape(description))
    lines += [f"URL:{url}", "END:VEVENT"]
    return "\r\n".join(part for line in lines for part in ics.fold(line))


FEEDS = {
    "https://jlib271.github.io/stemed-funding/feeds/deadlines.ics": cal(
        event("f1@stemed-funding", "20261201", "Deadline: Example Grant (NSF)", description="A long description, with commas; and semicolons " * 3),
        event("f0@stemed-funding", "20261001", "Deadline: Past Grant (NSF)")),
    "https://jlib271.github.io/stemed-conferences/feeds/deadlines.ics": cal(
        event("c1@stemed-conferences", "20261120", "Proposals due: NARST 2027")),
    "https://jlib271.github.io/stemed-professional-learning/feeds/deadlines.ics": cal(
        event("p1@stemed-professional-learning", "20261130", "Applications due: NOAA Teacher at Sea (2027 field season)")),
    "https://jlib271.github.io/stemed-faculty-development/feeds/deadlines.ics": cal(
        event("d1@stemed-faculty-development", "20270115", "Requests due: NAGT Traveling Workshops")),
}


def fake_get(url: str) -> str:
    if url in FEEDS:
        return FEEDS[url]
    raise OSError(f"unreachable: {url}")


class IcsTests(unittest.TestCase):
    def test_round_trip_unfolds_and_unescapes(self):
        text = cal(event("u1", "20261201", "Due: A, B; C\\D", description="Line one\nLine two, with a comma " * 4))
        [e] = ics.parse(text)
        self.assertEqual(e["date"], "2026-12-01")
        self.assertEqual(e["summary"], "Due: A, B; C\\D")
        self.assertIn("Line one\nLine two, with a comma", e["description"])

    def test_events_without_a_date_are_skipped(self):
        self.assertEqual(ics.parse(cal("BEGIN:VEVENT\r\nUID:x\r\nSUMMARY:No date\r\nEND:VEVENT")), [])


class BuildTests(unittest.TestCase):
    def test_combines_all_sites_and_drops_past_deadlines(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            payload = build.run(out, None, TODAY, get=fake_get)
            self.assertEqual([d["uid"] for d in payload["deadlines"]],
                             ["c1@stemed-conferences", "p1@stemed-professional-learning", "f1@stemed-funding",
                              "d1@stemed-faculty-development"])
            self.assertTrue(all(s["ok"] for s in payload["status"]))
            for name in ("index.html", "embed.html", "deadlines.json", "feeds/all.ics", "feeds/funding.ics",
                         "feeds/faculty-development.ics", "stemedplus-theme.css"):
                self.assertTrue((out / name).exists(), name)
            text = (out / "feeds" / "all.ics").read_bytes().decode("utf-8")
            self.assertTrue(all(len(line.encode()) <= 75 for line in text.split("\r\n")))
            events = ics.parse(text)
            self.assertEqual(len(events), 4)
            self.assertTrue(any(e["summary"] == "[Conferences] Proposals due: NARST 2027" for e in events))
            self.assertTrue(all("From STEMEd+" in e["description"] for e in events))
            only_funding = ics.parse((out / "feeds" / "funding.ics").read_bytes().decode("utf-8"))
            self.assertEqual([e["uid"] for e in only_funding], ["f1@stemed-funding"])

    def test_upcoming_rss_is_soonest_first_with_dates_in_titles(self):
        import xml.etree.ElementTree as ET
        with tempfile.TemporaryDirectory() as tmp:
            build.run(Path(tmp), None, TODAY, get=fake_get)
            root = ET.parse(Path(tmp) / "feeds" / "upcoming.xml").getroot()
            titles = [i.findtext("title") for i in root.findall("./channel/item")]
            self.assertEqual(titles[0], "Nov. 20: Proposals due: NARST 2027")
            self.assertEqual(len(titles), 3)                      # the January deadline is beyond 60 days
            self.assertIsNone(root.find("./channel/item/pubDate"))
            one = ET.parse(Path(tmp) / "feeds" / "upcoming-funding.xml").getroot()
            self.assertEqual([i.findtext("title") for i in one.findall("./channel/item")],
                             ["Dec. 1: Deadline: Example Grant (NSF)"])

    def test_a_site_that_is_down_keeps_its_earlier_deadlines(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = build.run(Path(tmp) / "a", None, TODAY, get=fake_get)
            prev = Path(tmp) / "previous.json"
            prev.write_text(json.dumps(first))

            def conferences_down(url):
                if "stemed-conferences" in url:
                    raise OSError("503")
                return fake_get(url)

            payload = build.run(Path(tmp) / "b", str(prev), TODAY, get=conferences_down)
            self.assertIn("c1@stemed-conferences", [d["uid"] for d in payload["deadlines"]])
            down = [s for s in payload["status"] if not s["ok"]]
            self.assertEqual([s["source"] for s in down], ["STEMEd+ Conferences"])
            self.assertEqual(down[0]["kept"], 1)

    def test_page_offers_one_calendar(self):
        html = (build.ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("One calendar for everything", html)
        self.assertIn('aria-current="page"', html)


if __name__ == "__main__":
    unittest.main()
