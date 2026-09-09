# Valley View astronomy

Observing notes for star parties at **Valley View Hot Springs**, Colorado
(38.193&nbsp;N, 105.817&nbsp;W, ~2600&nbsp;m, [Bortle 2](https://en.wikipedia.org/wiki/Bortle_scale)),
using the 20" PlaneWave CDK20 and two Celestron 8" telescopes.

Published at **https://nealmcb.github.io/valleyview-astro/**

## Contents

- **[astro-evening-vv.md](astro-evening-vv.md)** — the full "evening tour": a
  tour of the universe from the dark sky and the 20" scope, from the Moon out
  to the cosmic microwave background.
- **[vv20260909/highlights.md](vv20260909/highlights.md)** — short highlights
  for the nights of Sept 9–10, 2026.

## Tools

- **[bin/sky_timeline.py](bin/sky_timeline.py)** — twilight timeline, Moon, and
  planet / deep-sky rise-set-altitude for a given night at the site. Needs
  `skyfield`.
  ```
  python3 bin/sky_timeline.py 2026-09-09 --tour-time 21:00
  ```
- **[bin/build_site.sh](bin/build_site.sh)** — regenerate the `.html` pages
  from the `.md` sources with pandoc.
