"""Combine the deadline calendars of the STEMEd+ sites into one page and one calendar.

    python -m stemed_deadlines --out output --previous https://<owner>.github.io/<repo>

Output (all static, served by GitHub Pages):
    index.html              every upcoming deadline, "next 60 days" first
    embed.html              a compact view with subscribe buttons, for embedding in another website
    deadlines.json          everything listed (also what the next run falls back on if a site is down)
    feeds/all.ics           one calendar with every deadline
    feeds/<source>.ics      one calendar per site, as a convenience
"""
import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional
from urllib.request import Request, urlopen

from . import ics

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "STEMEd+ Deadlines (https://github.com/JLib271/stemed-deadlines)"
ASSETS = ("stemedplus-commons-logo.png", "stemedplus-commons-logo-white.png", "stemedplus-theme.css", "manrope.woff")


def load_config() -> dict:
    return json.loads((ROOT / "config" / "sources.json").read_text(encoding="utf-8"))


def fetch(url: str) -> str:
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as resp:
        return resp.read().decode("utf-8")


def load_previous(previous: Optional[str], get: Callable[[str], str] = fetch) -> List[dict]:
    if not previous:
        return []
    try:
        if previous.startswith(("http://", "https://")):
            data = json.loads(get(previous.rstrip("/") + "/deadlines.json"))
        else:
            data = json.loads(Path(previous).read_text(encoding="utf-8"))
        return data.get("deadlines", [])
    except Exception as exc:  # noqa: BLE001 - any failure means "start fresh"
        print(f"Note: no previous deadlines loaded from {previous} ({exc}).")
        return []


def run(out: Path, previous: Optional[str], today: dt.date, get: Callable[[str], str] = fetch,
        now: Optional[dt.datetime] = None) -> dict:
    now = now or dt.datetime.combine(today, dt.time(12), tzinfo=dt.timezone.utc)
    cfg = load_config()
    today_s = today.isoformat()
    earlier: Dict[str, List[dict]] = {}
    for d in load_previous(previous, get):
        earlier.setdefault(d["source"], []).append(d)

    deadlines, status = [], []
    for s in cfg["sources"]:
        try:
            events = ics.parse(get(s["ics"]))
            got = [{"uid": e.get("uid") or f"{s['id']}-{e['date']}-" + hashlib.sha1(e["summary"].encode("utf-8")).hexdigest()[:12],
                    "date": e["date"], "summary": e["summary"], "description": e.get("description", ""),
                    "url": e.get("url", ""), "location": e.get("location", ""),
                    "source": s["id"]} for e in events]
            status.append({"source": s["name"], "ok": True, "count": len(got)})
        except Exception as exc:  # noqa: BLE001 - keep yesterday's deadlines for a site that is down
            got = earlier.get(s["id"], [])
            status.append({"source": s["name"], "ok": False, "error": str(exc)[:200], "kept": len(got)})
            print(f"WARNING: {s['name']}: {exc}; kept {len(got)} earlier deadline(s).")
        for d in got:
            if d["date"] >= today_s:
                deadlines.append(dict(d, source_name=s["name"], source_label=s["label"], source_url=s["url"]))

    seen, unique = set(), []
    for d in sorted(deadlines, key=lambda d: (d["date"], d["summary"].lower())):
        if d["uid"] not in seen:
            seen.add(d["uid"])
            unique.append(d)

    payload = {
        "generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "today": today_s,
        "site": {k: cfg[k] for k in ("title", "tagline", "repo_url", "site_url", "commons_home")},
        "sources": [{k: s[k] for k in ("id", "name", "label", "url", "about")} for s in cfg["sources"]],
        "status": status,
        "deadlines": unique,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "deadlines.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
                                        encoding="utf-8")
    shutil.copyfile(ROOT / "site" / "index.html", out / "index.html")
    shutil.copyfile(ROOT / "site" / "embed.html", out / "embed.html")
    for name in ASSETS:
        shutil.copyfile(ROOT / "site" / name, out / name)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    feeds = out / "feeds"
    feeds.mkdir(parents=True, exist_ok=True)
    (feeds / "all.ics").write_bytes(ics.calendar(
        cfg["title"], "Every deadline from STEMEd+ Funding, Conferences, Professional Learning, and Faculty Development. "
                      "Always confirm on the sponsor's page.", unique, stamp))
    for s in cfg["sources"]:
        (feeds / f"{s['id']}.ics").write_bytes(ics.calendar(
            f"{cfg['title']}: {s['label']}", f"Deadlines from {s['name']}. Always confirm on the sponsor's page.",
            [d for d in unique if d["source"] == s["id"]], stamp))
    failed = [x for x in status if not x["ok"]]
    print(f"Wrote {len(unique)} upcoming deadline(s) from {len(cfg['sources'])} site(s); {len(failed)} site(s) unreachable.")
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--previous", help="URL of the published site (or a local deadlines.json)")
    args = ap.parse_args(argv)
    run(args.out, args.previous, dt.date.today())
    return 0


if __name__ == "__main__":
    sys.exit(main())
