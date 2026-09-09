#!/usr/bin/env python3
"""Fetch Heavens-Above "brighter satellite" pass predictions for Valley View.

Pulls the AllSats.aspx daily-predictions table for the Orient Land Trust
site and prints it as a Markdown table (the format used in the
``vvYYYYMMDD/satellites.md`` files).

Heavens-Above is a server-rendered ASP.NET page: we GET it once for the
hidden __VIEWSTATE, then POST the date / AM-PM / magnitude-limit form back
and parse the results table out of the HTML. No login needed; the public
daily-predictions page is the same whether or not you're signed in.

Usage
-----
    python3 bin/ha_passes.py 2026-09-09                 # evening, mag<=3.0
    python3 bin/ha_passes.py 2026-09-10 --morning
    python3 bin/ha_passes.py 2026-09-10 --mag 3.5 --keep-starlink
    python3 bin/ha_passes.py 2026-09-10 -o vv20260910/satellites.md

Validated 2026-09-09: reproduces the hand-pasted Sept 9 evening table
(21 passes, mag<=3.0, Starlink excluded) exactly.
"""
from __future__ import annotations

import argparse
import datetime as dt
import http.cookiejar
import re
import sys
import urllib.parse
import urllib.request

BASE = "https://www.heavens-above.com/AllSats.aspx"
SITE = dict(lat="38.191", lng="-105.816", loc="Valley View Hot Springs",
            alt="2600", tz="MST")
UTC_OFFSET_MS = "-21600000"                 # MST, UTC-7? no: site uses MST=-7?  -6h here
UA = "Mozilla/5.0 (X11; Linux x86_64)"

# comboMonth <option> values are Heavens-Above internal ids, not month
# numbers. June 2026 = 24317, so month M of year 2026 = 24317 + (M - 6).
_MONTH_BASE = 24317 - 6


def _month_id(year: int, month: int) -> str:
    if year != 2026:
        raise SystemExit("month-id table only calibrated for 2026; re-check "
                         "the comboMonth <option> values for other years")
    return str(_MONTH_BASE + month)


def _opener():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", UA)]
    return op


def _hidden(html: str, name: str) -> str:
    m = re.search(r'name="' + re.escape(name) + r'"[^>]*value="([^"]*)"', html)
    return m.group(1) if m else ""


def _parse_rows(html: str):
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 10:
            continue
        c = [re.sub(r"<[^>]+>", "", x).replace("&#176;", "°").strip()
             for x in tds]
        if re.match(r"^\d\d:\d\d:\d\d$", c[2]) and re.match(r"^\d\d:\d\d:\d\d$", c[8]):
            # name, mag, (time alt az) x3  ->  disappearance az is c[10]
            rows.append(c[:11] if len(c) >= 11 else c[:10] + [""])
    return rows


def fetch(date: dt.date, evening: bool, mag: str, exclude_starlink: bool):
    op = _opener()
    qs = "?" + urllib.parse.urlencode(SITE)
    html = op.open(BASE + qs).read().decode("utf-8", "replace")
    form = {
        "__EVENTTARGET": "", "__EVENTARGUMENT": "", "__LASTFOCUS": "",
        "__VIEWSTATE": _hidden(html, "__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": _hidden(html, "__VIEWSTATEGENERATOR"),
        "utcOffset": UTC_OFFSET_MS,
        "ctl00$ddlCulture": "en",
        "ctl00$cph1$TimeSelectionControl1$comboMonth": _month_id(date.year, date.month),
        "ctl00$cph1$TimeSelectionControl1$comboDay": str(date.day),
        "ctl00$cph1$TimeSelectionControl1$radioAMPM": "PM" if evening else "AM",
        "ctl00$cph1$TimeSelectionControl1$btnSubmit": "Update",
        "ctl00$cph1$radioButtonsMag": mag,
    }
    if exclude_starlink:
        form["ctl00$cph1$chkExcludeStarlink"] = "on"
    data = urllib.parse.urlencode(form).encode()
    html2 = op.open(urllib.request.Request(BASE + qs, data=data)).read().decode("utf-8", "replace")
    return _parse_rows(html2)


def to_markdown(rows, date: dt.date, evening: bool, mag: str) -> str:
    when = "evening" if evening else "morning"
    ha_link = ("https://www.heavens-above.com/AllSats.aspx"
               f"?lat={SITE['lat']}&lng={SITE['lng']}&alt={SITE['alt']}&tz={SITE['tz']}")
    out = [
        f"# Satellite passes — {date:%A, %B %-d, %Y} ({when})",
        "",
        "*Valley View Hot Springs / Orient Land Trust — "
        f"{SITE['lat']}°N, {abs(float(SITE['lng']))}°W*",
        "",
        f"Every satellite pass brighter than magnitude {mag}, from "
        f"[Heavens-Above]({ha_link}). Starlink excluded. Times MDT (UTC−6).",
        "",
        "| Satellite | Mag | Appears | Highest point | Disappears |",
        "|---|---:|---|---|---|",
    ]
    for name, m, t1, a1, z1, t2, a2, z2, t3, a3, z3 in rows:
        out.append(f"| {name} | {m} | {t1} · {a1} {z1} | {t2} · {a2} {z2} | "
                   f"{t3} · {a3} {z3} |")
    out += [
        "",
        "<small>Each cell is *time · altitude · compass direction*; brightness "
        "in magnitudes (lower = brighter). \"Appears\" and \"disappears\" mark "
        "10° altitude or entry/exit from Earth's shadow. The ISS and its "
        "Zvezda module are listed as separate rows for the same pass. "
        f"Generated with [`bin/ha_passes.py`](../bin/ha_passes.py).</small>",
        "",
        "← [Valley View astronomy](../index.md)",
        "",
    ]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("date", help="YYYY-MM-DD")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--evening", action="store_true", default=True)
    g.add_argument("--morning", dest="evening", action="store_false")
    ap.add_argument("--mag", default="3.0", choices=["3.0", "3.5", "4.0", "4.5", "5.0"])
    ap.add_argument("--keep-starlink", dest="exclude_starlink",
                    action="store_false", default=True)
    ap.add_argument("-o", "--out", help="write Markdown here instead of stdout")
    args = ap.parse_args()

    date = dt.date.fromisoformat(args.date)
    rows = fetch(date, args.evening, args.mag, args.exclude_starlink)
    if not rows:
        sys.exit("no rows parsed - Heavens-Above markup may have changed")
    md = to_markdown(rows, date, args.evening, args.mag)
    if args.out:
        open(args.out, "w").write(md)
        print(f"wrote {len(rows)} passes -> {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
