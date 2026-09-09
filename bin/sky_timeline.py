#!/usr/bin/env python3
"""Evening/morning observing timeline for Valley View Hot Springs, CO.

Purpose
-------
Generate the "when is it dark / what's up" numbers that go into a nightly
``vvYYYYMMDD/highlights.md`` file and into the "Nightly plan / targets"
section of the Valley View telescopes doc:

  * sunset, civil / nautical / astronomical dusk (evening)
  * astronomical / nautical / civil dawn, sunrise (next morning)
  * Moon phase, moonrise / moonset
  * rise / set / transit for the naked-eye planets and a few favourite
    deep-sky objects, plus their altitude at a chosen "tour time"

Site defaults to the 20" PlaneWave pier: 38.193071 N, 105.817073 W, ~2600 m.

Usage
-----
    python3 bin/sky_timeline.py 2026-09-09
    python3 bin/sky_timeline.py 2026-09-09 --tour-time 21:00
    python3 bin/sky_timeline.py 2026-09-09 --tz America/Denver

Needs: skyfield (pip install skyfield). Ephemeris de421.bsp is cached next
to this script on first run.

This is deliberately a small standalone script; if a second night needs
something it can't do, extend it here rather than pasting a one-off snippet.
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

from skyfield import almanac
from skyfield.api import Loader, wgs84, Star

HERE = Path(__file__).resolve().parent
LOAD = Loader(HERE)  # cache de421.bsp beside this script (git-ignored)

SITE_LAT = 38.193071
SITE_LON = -105.817073
SITE_ELEV_M = 2600
DEFAULT_TZ = "America/Denver"

# A few favourites from astro-evening-vv.md / the VV telescopes doc.
# (name, RA hours, Dec degrees, J2000)
DSOS = {
    "M13 (Hercules globular)": (16 + 41.7 / 60, 36 + 28 / 60),
    "M57 (Ring Nebula)": (18 + 53.6 / 60, 33 + 2 / 60),
    "Albireo (Cygnus double)": (19 + 30.7 / 60, 27 + 58 / 60),
    "M31 (Andromeda Galaxy)": (0 + 42.7 / 60, 41 + 16 / 60),
    "M8 (Lagoon Nebula)": (18 + 3.8 / 60, -(24 + 23 / 60)),
    "Mizar/Alcor (Big Dipper)": (13 + 23.9 / 60, 54 + 55 / 60),
    "Double Cluster (Perseus)": (2 + 20.0 / 60, 57 + 8 / 60),
}

PLANETS = {
    "Mercury": "mercury",
    "Venus": "venus",
    "Mars": "mars",
    "Jupiter": "jupiter barycenter",
    "Saturn": "saturn barycenter",
    "Uranus": "uranus barycenter",
    "Neptune": "neptune barycenter",
}


def fmt(t, tz):
    return t.astimezone(tz).strftime("%H:%M")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("date", help="evening date, YYYY-MM-DD (local)")
    ap.add_argument("--tz", default=DEFAULT_TZ)
    ap.add_argument("--tour-time", default="21:00",
                    help="local HH:MM to report object altitudes for")
    ap.add_argument("--lat", type=float, default=SITE_LAT)
    ap.add_argument("--lon", type=float, default=SITE_LON)
    ap.add_argument("--elev", type=float, default=SITE_ELEV_M)
    args = ap.parse_args()

    tz = ZoneInfo(args.tz)
    y, m, d = (int(x) for x in args.date.split("-"))
    eve = dt.datetime(y, m, d, 12, tzinfo=tz)          # local noon, evening date
    nextnoon = eve + dt.timedelta(days=1)

    ts = LOAD.timescale()
    eph = LOAD("de421.bsp")
    sun, moon, earth = eph["sun"], eph["moon"], eph["earth"]
    site = earth + wgs84.latlon(args.lat, args.lon, elevation_m=args.elev)
    obs = wgs84.latlon(args.lat, args.lon, elevation_m=args.elev)

    t0 = ts.from_datetime(eve)
    t1 = ts.from_datetime(nextnoon)

    print(f"Valley View Hot Springs  ({args.lat:.4f}, {args.lon:.4f}, {args.elev:.0f} m)")
    print(f"Evening of {args.date}  ({args.tz})\n")

    # --- Twilight -------------------------------------------------------
    f = almanac.dark_twilight_day(eph, obs)
    times, events = almanac.find_discrete(t0, t1, f)
    labels = {
        0: "astronomical dark begins/ends",
        1: "astronomical twilight",
        2: "nautical twilight",
        3: "civil twilight",
        4: "sunrise/sunset",
    }
    # skyfield dark_twilight_day states: 0 night, 1 astro twil, 2 nautical,
    # 3 civil, 4 day.  `e` is the state *entered* at time `t`.
    prev = f(t0).item()
    print("Twilight timeline:")
    dusk = {3: "Sunset", 2: "Civil dusk", 1: "Nautical dusk",
            0: "Astronomical dusk (full dark)"}
    dawn = {1: "Astronomical dawn (dark ends)", 2: "Nautical dawn",
            3: "Civil dawn", 4: "Sunrise"}
    for t, e in zip(times, events):
        e = int(e)
        edge = (dusk if e < prev else dawn).get(e, labels.get(e, str(e)))
        print(f"  {fmt(t.utc_datetime(), tz):>6}  {edge}")
        prev = e
    print()

    # --- Moon ----------------------------------------------------------
    phase = almanac.moon_phase(eph, ts.from_datetime(eve.replace(hour=21)))
    illum = 0.5 * (1 - __import__("math").cos(phase.radians))
    print(f"Moon: phase angle {phase.degrees:.0f} deg, ~{illum*100:.0f}% illuminated")
    fr = almanac.risings_and_settings(eph, moon, obs)
    mt, me = almanac.find_discrete(t0, t1, fr)
    for t, e in zip(mt, me):
        print(f"  Moon{'rise' if e else 'set'}: {fmt(t.utc_datetime(), tz)}")
    print()

    # --- Tour-time altitudes ----------------------------------------
    hh, mm = (int(x) for x in args.tour_time.split(":"))
    tour_dt = eve.replace(hour=hh, minute=mm)
    if hh < 12:
        tour_dt += dt.timedelta(days=1)
    tt = ts.from_datetime(tour_dt)
    print(f"At {args.tour_time} local ({tour_dt.date()}):")

    def rise_set_transit(body, label):
        fr = almanac.risings_and_settings(eph, body, obs)
        rt, re = almanac.find_discrete(t0, t1, fr)
        rr = {("rise" if e else "set"): fmt(t.utc_datetime(), tz)
              for t, e in zip(rt, re)}
        alt = site.at(tt).observe(body).apparent().altaz()[0].degrees
        extra = f"  rise {rr.get('rise','--')}  set {rr.get('set','--')}"
        print(f"  {label:<28} alt {alt:+5.1f} deg{extra}")

    for name, key in PLANETS.items():
        rise_set_transit(eph[key], name)
    print()
    for name, (ra_h, dec_d) in DSOS.items():
        star = Star(ra_hours=ra_h, dec_degrees=dec_d)
        alt = site.at(tt).observe(star).apparent().altaz()[0].degrees
        fr = almanac.risings_and_settings(eph, star, obs)
        rt, re = almanac.find_discrete(t0, t1, fr)
        rr = {("rise" if e else "set"): fmt(t.utc_datetime(), tz)
              for t, e in zip(rt, re)}
        print(f"  {name:<28} alt {alt:+5.1f} deg  rise {rr.get('rise','--')}  set {rr.get('set','--')}")


if __name__ == "__main__":
    main()
