"""Read and write the small part of iCalendar the STEMEd+ sites use: all-day events with
UID, SUMMARY, DESCRIPTION, URL, and LOCATION."""
import datetime as dt
from typing import Dict, List


def unfold(text: str) -> List[str]:
    """Lines that continue on the next line start with a space or tab."""
    lines: List[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        elif raw:
            lines.append(raw)
    return lines


def unescape(value: str) -> str:
    out, i = [], 0
    while i < len(value):
        c = value[i]
        if c == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            out.append("\n" if nxt in "nN" else nxt)
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _date(value: str) -> str:
    digits = value[:8]
    try:
        return dt.date(int(digits[:4]), int(digits[4:6]), int(digits[6:8])).isoformat()
    except ValueError:
        return ""


def parse(text: str) -> List[Dict[str, str]]:
    """Events as dicts: uid, date (YYYY-MM-DD), summary, description, url, location."""
    events, current = [], None
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current is not None and current.get("date") and current.get("summary"):
                events.append(current)
            current = None
            continue
        if current is None or ":" not in line:
            continue
        head, value = line.split(":", 1)
        name = head.split(";", 1)[0].upper()
        if name == "DTSTART":
            current["date"] = _date(value)
        elif name in ("UID", "SUMMARY", "DESCRIPTION", "URL", "LOCATION"):
            current[name.lower()] = unescape(value)
    return events


def escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line: str) -> List[str]:
    """iCalendar lines are at most 75 octets; longer ones continue with a leading space."""
    out, data = [], line.encode("utf-8")
    while len(data) > 75:
        cut = 75 if not out else 74
        while cut and (data[cut] & 0xC0) == 0x80:   # do not split a UTF-8 character
            cut -= 1
        out.append(data[:cut].decode("utf-8"))
        data = data[cut:]
    out.append(data.decode("utf-8"))
    return [out[0]] + [" " + s for s in out[1:]]


def calendar(name: str, about: str, events: List[dict], stamp: str) -> bytes:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//STEMEd+//Deadlines//EN", "CALSCALE:GREGORIAN"]
    lines += fold("X-WR-CALNAME:" + escape(name)) + fold("X-WR-CALDESC:" + escape(about))
    for e in events:
        end = (dt.date.fromisoformat(e["date"]) + dt.timedelta(days=1)).strftime("%Y%m%d")
        body = ["BEGIN:VEVENT", f"UID:{e['uid']}", f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{e['date'].replace('-', '')}", f"DTEND;VALUE=DATE:{end}",
                "SUMMARY:" + escape(f"[{e['source_label']}] {e['summary']}")]
        if e.get("location"):
            body.append("LOCATION:" + escape(e["location"]))
        description = (e.get("description") or "").strip()
        body.append("DESCRIPTION:" + escape((description + "\n\n" if description else "") + f"From {e['source_name']}: {e['source_url']}"))
        if e.get("url"):
            body.append("URL:" + e["url"])
        body.append("END:VEVENT")
        lines += [part for line in body for part in fold(line)]
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")
