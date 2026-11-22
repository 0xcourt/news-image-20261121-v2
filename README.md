# news-image-20261121-v2

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/0xcourt/news-image-20261121-v2/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/0xcourt/news-image-20261121-v2/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

One 1024x1024 broadsheet PNG summing up the world news of Saturday 21 November 2026: 35 verified stories across 9 regions — Iran's strikes on US bases in Bahrain as the single dominant lead, COP31 in overtime in Antalya, the M6.7 Peru quake, Mexico's capture of Chapo Isidro, the Shenzhen trilateral summit, and 30 more. A from-scratch redesign for legibility: one big lead story instead of a crammed grid, larger type, generous whitespace, a UTC timeline strip, date-check marks, and a pin map. Drawn from scratch in pure Python 3 stdlib (own 5x7 bitmap font, own world map, own PNG encoder). No network at runtime; deterministic — every run writes identical bytes.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=e57xstcn&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>

## What it is

`main.py` (Python 3.13, standard library only) draws the broadsheet and writes
`entry.png` (1024x1024, ~54 KB) to `$MAKEFUN_OUTPUT_DIR`. Layout: a masthead
with the date and verification mark, one dominant lead story with a stylised
Persian Gulf diagram, a UTC timeline of the day's six beats, 34 more stories
in three regional columns in large type, a 12-pin world map, and a sources
footer. All 35 stories were verified against reporting from 21 November 2026
(AFP, AP, Reuters, BBC, Al Jazeera, Euronews, USGS, Yonhap, DW) — see
`../VERIFIED-STORIES.md` in the workdir (kept out of the repo) for the
story-by-story sources.
