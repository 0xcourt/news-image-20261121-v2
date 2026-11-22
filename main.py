#!/usr/bin/env python3
"""The World in One Picture -- 35 Stories, Saturday 21 November 2026.

Draws a 1024x1024 newspaper front page summing up the world news of
Saturday 21 November 2026 and writes it to $MAKEFUN_OUTPUT_DIR/entry.png.

Pure Python 3 standard library. No network, no fonts on disk, no image
libraries: the glyphs, the map shapes and the PNG encoder are all defined
in this file. The output is fully deterministic: same bytes every run.

Design (a deliberate redesign for legibility): one dominant lead story,
a broadsheet masthead, a UTC timeline strip, three airy story columns in
large type, a pin map, and a sources footer. 35 stories, 9 regions.
"""

import binascii
import hashlib
import os
import struct
import sys
import zlib

# ---------------------------------------------------------------------------
# 5x7 bitmap typeface, drawn by hand for this entry.
# Each glyph is 7 rows of 5 bits, '#' = ink. Lowercase letters sit on the
# same baseline with descenders where needed. Stored as one compact string
# per glyph so the table stays readable and editable.
# ---------------------------------------------------------------------------

_FONT_RAW = """
A 01110 10001 10001 11111 10001 10001 10001
B 11110 10001 10001 11110 10001 10001 11110
C 01110 10001 10000 10000 10000 10001 01110
D 11110 10001 10001 10001 10001 10001 11110
E 11111 10000 10000 11110 10000 10000 11111
F 11111 10000 10000 11110 10000 10000 10000
G 01110 10001 10000 10111 10001 10001 01111
H 10001 10001 10001 11111 10001 10001 10001
I 01110 00100 00100 00100 00100 00100 01110
J 00111 00010 00010 00010 00010 10010 01100
K 10001 10010 10100 11000 10100 10010 10001
L 10000 10000 10000 10000 10000 10000 11111
M 10001 11011 10101 10101 10001 10001 10001
N 10001 11001 10101 10011 10001 10001 10001
O 01110 10001 10001 10001 10001 10001 01110
P 11110 10001 10001 11110 10000 10000 10000
Q 01110 10001 10001 10001 10101 10010 01101
R 11110 10001 10001 11110 10100 10010 10001
S 01111 10000 10000 01110 00001 00001 11110
T 11111 00100 00100 00100 00100 00100 00100
U 10001 10001 10001 10001 10001 10001 01110
V 10001 10001 10001 10001 10001 01010 00100
W 10001 10001 10001 10101 10101 11011 10001
X 10001 10001 01010 00100 01010 10001 10001
Y 10001 10001 01010 00100 00100 00100 00100
Z 11111 00001 00010 00100 01000 10000 11111
a 00000 00000 01110 00001 01111 10001 01111
b 10000 10000 11110 10001 10001 10001 11110
c 00000 00000 01110 10000 10000 10001 01110
d 00001 00001 01111 10001 10001 10001 01111
e 00000 00000 01110 10001 11111 10000 01110
f 00110 01001 01000 11110 01000 01000 01000
g 00000 01111 10001 10001 01111 00001 01110
h 10000 10000 11110 10001 10001 10001 10001
i 00100 00000 01100 00100 00100 00100 01110
j 00010 00000 00110 00010 00010 10010 01100
k 10000 10000 10010 10100 11000 10100 10010
l 01100 00100 00100 00100 00100 00100 01110
m 00000 00000 11010 10101 10101 10101 10101
n 00000 00000 11110 10001 10001 10001 10001
o 00000 00000 01110 10001 10001 10001 01110
p 00000 00000 11110 10001 10001 11110 10000
q 00000 00000 01111 10001 10001 01111 00001
r 00000 00000 10110 11001 10000 10000 10000
s 00000 00000 01111 10000 01110 00001 11110
t 01000 01000 11100 01000 01000 01000 00110
u 00000 00000 10001 10001 10001 10011 01101
v 00000 00000 10001 10001 10001 01010 00100
w 00000 00000 10001 10101 10101 10101 01010
x 00000 00000 10001 01010 00100 01010 10001
y 00000 00000 10001 10001 01111 00001 01110
z 00000 00000 11111 00010 00100 01000 11111
0 01110 10001 10011 10101 11001 10001 01110
1 00100 01100 00100 00100 00100 00100 01110
2 01110 10001 00001 00110 01000 10000 11111
3 11111 00010 00100 00010 00001 10001 01110
4 00010 00110 01010 10010 11111 00010 00010
5 11111 10000 11110 00001 00001 10001 01110
6 00110 01000 10000 11110 10001 10001 01110
7 11111 00001 00010 00100 01000 01000 01000
8 01110 10001 10001 01110 10001 10001 01110
9 01110 10001 10001 01111 00001 00010 01100
SP 00000 00000 00000 00000 00000 00000 00000
. 00000 00000 00000 00000 00000 01100 01100
, 00000 00000 00000 00000 01100 00100 01000
: 00000 01100 01100 00000 01100 01100 00000
; 00000 01100 01100 00000 01100 00100 01000
' 00100 00100 01000 00000 00000 00000 00000
" 01010 01010 00000 00000 00000 00000 00000
! 00100 00100 00100 00100 00100 00000 00100
? 01110 10001 00001 00110 00100 00000 00100
- 00000 00000 00000 01110 00000 00000 00000
_ 00000 00000 00000 00000 00000 00000 11111
( 00010 00100 01000 01000 01000 00100 00010
) 01000 00100 00010 00010 00010 00100 01000
/ 00001 00010 00010 00100 01000 01000 10000
% 11001 11010 00010 00100 01000 01011 10011
$ 00100 01111 10100 01110 00101 11110 00100
& 01100 10010 10100 01000 10101 10010 01101
+ 00000 00100 00100 11111 00100 00100 00000
= 00000 00000 11111 00000 11111 00000 00000
* 00000 00100 10101 01110 10101 00100 00000
# 01010 01010 11111 01010 11111 01010 01010
@ 01110 10001 10111 10101 10110 10000 01110
~ 00000 00000 01001 10110 00000 00000 00000
"""


def _build_font():
    font = {}
    for line in _FONT_RAW.strip().splitlines():
        parts = line.split()
        if not parts:
            continue
        ch = parts[0]
        if ch == "SP":
            ch = " "
        rows = parts[1:]
        if len(rows) != 7 or any(len(r) != 5 for r in rows):
            raise ValueError("bad glyph for %r" % ch)
        font[ch] = tuple(tuple(c == "#" or c == "1" for c in r) for r in rows)
    # Special marks defined directly (no ASCII key fits them).
    font["\u2713"] = (  # check mark
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 1),
        (0, 0, 0, 1, 1),
        (1, 0, 1, 1, 0),
        (0, 1, 1, 0, 0),
        (0, 0, 1, 0, 0),
        (0, 0, 0, 0, 0),
    )
    font["\u2605"] = (  # star
        (0, 0, 1, 0, 0),
        (0, 0, 1, 0, 0),
        (1, 1, 1, 1, 1),
        (0, 1, 1, 1, 0),
        (0, 1, 0, 1, 0),
        (1, 0, 0, 0, 1),
        (0, 0, 0, 0, 0),
    )
    font["\u2014"] = (  # em dash
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (1, 1, 1, 1, 1),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
    )
    font["\u2013"] = font["-"]  # en dash = hyphen here
    font["\u00b7"] = (  # middle dot
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 1, 1, 0, 0),
        (0, 1, 1, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
    )
    font["\u00d7"] = (  # multiplication x
        (0, 0, 0, 0, 0),
        (1, 0, 0, 0, 1),
        (0, 1, 0, 1, 0),
        (0, 0, 1, 0, 0),
        (0, 1, 0, 1, 0),
        (1, 0, 0, 0, 1),
        (0, 0, 0, 0, 0),
    )
    font["\u2192"] = (  # right arrow
        (0, 0, 0, 0, 0),
        (0, 0, 1, 0, 0),
        (0, 0, 0, 1, 0),
        (1, 1, 1, 1, 1),
        (0, 0, 0, 1, 0),
        (0, 0, 1, 0, 0),
        (0, 0, 0, 0, 0),
    )
    return font


FONT = _build_font()
FONT_W, FONT_H = 5, 7


# ---------------------------------------------------------------------------
# Canvas: a plain RGB bytearray with the drawing primitives this page needs.
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, width, height, background):
        self.w = width
        self.h = height
        self.px = bytearray(background * (width * height))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = color

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, color, thick=1):
        self.fill_rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill_rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line, with square caps of the requested thickness."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0 - thick // 2, y0 - thick // 2, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else -1
            if dx >= 0:
                self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r - thick, cy + r + thick + 1):
            for xx in range(cx - r - thick, cx + r + thick + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - thick / 2 <= d <= r + thick / 2:
                    self.set(xx, yy, color)

    def polygon(self, points, color):
        """Scanline fill of a simple polygon (even-odd)."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[j]), y, max(1, int(xs[j + 1]) - int(xs[j])), 1, color)

    def polyline(self, points, color, thick=1, closed=False):
        pts = list(points) + ([points[0]] if closed else [])
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], color, thick)

    # -- text ---------------------------------------------------------------
    def text_width(self, text, scale):
        return len(text) * 6 * scale - scale

    def draw_text(self, x, y, text, scale, color, bold=False):
        """Draw text; y is the top of the 7-row cell. Returns width used."""
        cx = x
        for ch in text:
            glyph = FONT.get(ch)
            if glyph is None:
                glyph = FONT["?"]
            for row in range(FONT_H):
                for col in range(FONT_W):
                    if glyph[row][col]:
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
                        if bold:
                            self.fill_rect(cx + col * scale + 1, y + row * scale,
                                           scale, scale, color)
            cx += 6 * scale
        return cx - x - scale

    def text_centered(self, cx, y, text, scale, color, bold=False):
        w = self.text_width(text, scale)
        return self.draw_text(cx - w // 2, y, text, scale, color, bold)

    def wrap(self, text, scale, max_width):
        """Greedy word wrap; returns a list of lines that fit max_width."""
        words = text.split()
        lines = []
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_width(trial, scale) <= max_width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# ---------------------------------------------------------------------------
# PNG encoder (stdlib zlib; filter 0 on every scanline -- deterministic).
# ---------------------------------------------------------------------------

def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas):
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    return png


# ---------------------------------------------------------------------------
# The news: 35 stories, all verified as having happened or first been
# reported on Saturday 21 November 2026 (any time zone). Sources per story
# were checked against AFP, AP, Reuters, BBC, Al Jazeera, Euronews, USGS,
# Yonhap, DW and national outlets. Two dated-care notes:
#  - the Peru quake struck 19:09 local Friday in Peru = 00:09 UTC Saturday;
#  - the market rout was Friday's close, reported across Saturday.
# ---------------------------------------------------------------------------

LEAD = {
    "kicker": "\u2605 LEAD STORY \u00b7 MIDDLE EAST \u00b7 EVENING, 21 NOV",
    "headline": ["IRAN STRIKES US BASES", "IN BAHRAIN"],
    "deck": ("IRGC missiles and drones hit two US positions at al-Riffa "
             "and Awali. A civilian industrial site burned; Bahrain "
             "intercepted other attacks and reported no injuries. Iran "
             "says it downed a US drone near Qeshm; the US denies an "
             "F-16 was hit."),
    "source": "Sources: AFP \u00b7 Al Jazeera \u00b7 Euronews \u00b7 Reuters",
}

# Timeline: (time label, line 1, line 2) -- one beat per part of the day.
TIMELINE = [
    ("00:09", "PERU QUAKE", "M6.7"),
    ("MORNING", "COP31 IN", "OVERTIME"),
    ("MIDDAY", "KRYVYI RIH", "MISSILE"),
    ("AFTERNOON", "SHENZHEN", "SUMMIT"),
    ("EVENING", "IRAN STRIKES", "BAHRAIN"),
    ("FRI CLOSE", "MARKETS IN", "AI ROUT"),
]

# Column stories: (region, headline, one-line summary). Each headline is
# written to fit one line at scale 2 in a 300 px column; the summary is
# one short line. Order inside a column is by weight, heaviest first.
COL_A = [  # Middle East + Europe
    ("MIDDLE EAST", "COP31 IN OVERTIME", "No deal; fuels cut"),
    ("EUROPE", "KRYVYI RIH HIT KILLS 2", "Boy, 7, dead; ~60 hurt"),
    ("EUROPE", "SPARTA II ABLAZE AT SEA", "Ship drifts to Finland"),
    ("EUROPE", "UK AND EU SIGN 3 DEALS", "Food, emissions, youth"),
    ("EUROPE", "EU-INDONESIA TRADE DEAL", "98.5% of tariffs to go"),
    ("EUROPE", "DENMARK EXPELS RUSSIAN", "Attache out; 'kill plot'"),
    ("EUROPE", "FRANCE PROTESTS, 6TH WEEK", "144 arrests in Paris"),
    ("MIDDLE EAST", "TANKERS HIT AT HORMUZ", "Oil flows down about 15%"),
    ("MIDDLE EAST", "HOUTHIS FIRE ON RIYADH", "4 missiles intercepted"),
    ("MIDDLE EAST", "GAZA FOOD-TRUCK STRIKE", "3 Palestinians killed"),
    ("MIDDLE EAST", "BASRA POWER FIRE KILLS 4", "35 hurt; grid strained"),
    ("EUROPE", "CERN'S ULTRA-RARE DECAY", "First evidence of decay"),
]

COL_B = [  # The Americas + Asia
    ("N. AMERICA", "MEXICO NABS CHAPO ISIDRO", "FBI most-wanted man held"),
    ("N. AMERICA", "MARKETS IN AI ROUT", "S&P -3.7%; Nasdaq wiped"),
    ("ASIA", "TRUMP, XI AND PUTIN MEET", "Nuclear-risk talks agreed"),
    ("N. AMERICA", "FBI CRIME DATABASE HACKED", "2nd breach in 2 months"),
    ("N. AMERICA", "NVIDIA CHIEF HUANG OUSTED", "Trump talked to Xi on it"),
    ("N. AMERICA", "TRUMP THREATENS DATA TAX", "AI centres built abroad"),
    ("S. AMERICA", "BOLSONARO IN INTENSIVE", "Bowel blockage; stable"),
    ("S. AMERICA", "WOLBACHIA CUTS DENGUE 69%", "Trial: far fewer cases"),
    ("EAST ASIA", "SEOUL MOVES TO IMPEACH", "Chief justice targeted"),
    ("SOUTH ASIA", "NEPAL PM HEADS TO INDIA", "Trade tops agenda"),
    ("SE ASIA", "M6.8 QUAKE OFF TIMOR", "NE of Dili; coast watches"),
    ("CARIBBEAN", "HAITI: TROOPS FIGHT GANGS", "3 prisons agreed"),
]

COL_C = [  # Africa + space, culture and sport
    ("S. AMERICA", "PERU QUAKE M6.7", "1 dead, 16 hurt in Lima"),
    ("AFRICA", "NIGERIA BOAT SINKS", "24 dead; funeral boat"),
    ("AFRICA", "UGANDA EBOLA CURBS", "DR Congo outbreak grows"),
    ("AFRICA", "ETHIOPIA: 700,000 FLEE", "Troops mass on border"),
    ("AFRICA", "MLAMBO-NGCUKA DIES, 71", "Ex-UN Women chief, 71"),
    ("SPACE", "BEPICOLOMBO AT MERCURY", "8-year trip ends in orbit"),
    ("CULTURE", "GTA VI: $3.8BN IN ONE DAY", "Biggest launch in history"),
    ("SPORT", "ALCARAZ TO FACE ZVEREV", "ATP final Sunday, Turin"),
    ("SPORT", "ENGLAND 37-12 ALL BLACKS", "Record win at Twickenham"),
    ("SPORT", "WALLABIES 29, WALES 26", "Streak ends in Cardiff"),
]

# Stylised world map: coarse continent outlines in (lon, lat). Drawn from
# a rough atlas sketch for this entry -- deliberately simplified, and the
# image says so. Pins are (number, lon, lat, label).
WORLD = {
    "N. America": [(-168, 66), (-140, 70), (-125, 72), (-110, 68), (-95, 69),
                   (-85, 66), (-80, 73), (-65, 60), (-55, 52), (-60, 47),
                   (-70, 42), (-75, 35), (-80, 32), (-81, 26), (-90, 21),
                   (-95, 19), (-105, 20), (-115, 28), (-125, 40),
                   (-125, 49), (-135, 58), (-155, 60)],
    "Greenland": [(-58, 64), (-45, 60), (-40, 65), (-30, 68), (-22, 70),
                  (-30, 76), (-55, 76), (-58, 70)],
    "S. America": [(-80, 9), (-75, 11), (-62, 10), (-52, 5), (-50, 0),
                   (-44, -3), (-35, -8), (-40, -20), (-48, -28), (-58, -38),
                   (-65, -45), (-70, -52), (-73, -50), (-73, -37),
                   (-70, -20), (-77, -12), (-80, -3)],
    "Africa": [(-17, 15), (-10, 31), (-5, 35), (10, 37), (20, 32), (32, 31),
               (35, 28), (43, 12), (51, 11), (48, 0), (40, -10), (35, -18),
               (32, -26), (28, -33), (20, -35), (15, -27), (12, -18),
               (9, 4), (-8, 5)],
    "Eurasia": [(-10, 36), (-9, 43), (-2, 48), (2, 51), (7, 54), (10, 57),
                (18, 56), (21, 55), (24, 59), (28, 61), (32, 64), (45, 68),
                (60, 69), (75, 72), (95, 76), (115, 73), (135, 71),
                (155, 70), (170, 67), (178, 66), (170, 60), (160, 55),
                (155, 50), (142, 48), (140, 42), (135, 35), (130, 33),
                (127, 35), (122, 31), (120, 28), (113, 22), (108, 18),
                (105, 10), (100, 7), (98, 10), (94, 17), (91, 22), (88, 22),
                (86, 20), (80, 13), (77, 8), (76, 10), (73, 20), (70, 21),
                (66, 25), (61, 25), (57, 27), (54, 26), (51, 28), (49, 30),
                (48, 29), (44, 29), (42, 15), (43, 12), (45, 13), (50, 16),
                (55, 17), (59, 22), (57, 24), (52, 26), (50, 29), (48, 30),
                (44, 29), (39, 21), (38, 24), (35, 29), (34, 31), (36, 36),
                (30, 36), (27, 37), (23, 36), (19, 40), (15, 44), (12, 44),
                (8, 44), (3, 43), (0, 40), (-2, 37), (-6, 36)],
    "Australia": [(113, -22), (114, -30), (115, -35), (124, -33), (129, -32),
                  (132, -32), (137, -35), (140, -38), (145, -38), (150, -37),
                  (153, -32), (153, -27), (146, -19), (142, -11), (137, -12),
                  (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
                  (118, -20)],
    "Britain": [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
                (1, 51)],
    "Japan": [(130, 31), (132, 33), (135, 34), (137, 35), (139, 37),
              (141, 39), (142, 42), (144, 44), (141, 45), (140, 40),
              (139, 38), (137, 36), (135, 34), (133, 34), (131, 33)],
}

PINS = [
    (1, 50.6, 26.2, "Bahrain"),
    (2, 30.7, 36.9, "Antalya"),
    (3, -75.2, -11.2, "Junin, Peru"),
    (4, -107.9, 25.6, "Guasave"),
    (5, 33.4, 47.9, "Kryvyi Rih"),
    (6, 114.1, 22.5, "Shenzhen"),
    (7, 25.0, 59.5, "Gulf of Finland"),
    (8, -47.9, -15.8, "Brasilia"),
    (9, 6.3, 4.9, "Bayelsa"),
    (10, 125.6, -8.6, "Dili"),
    (11, 7.7, 45.1, "Turin"),
    (12, -115.1, 36.2, "Las Vegas"),
]

FOOTER_SOURCES = ("Sources: AFP, AP, Reuters, BBC, Al Jazeera, Euronews, "
                  "USGS, Yonhap, DW")
FOOTER_CHECK = ("Every story happened or was first reported Sat 21 Nov 2026. "
                "\u2713 DATE-CHECKED")


# ---------------------------------------------------------------------------
# Palette and layout.
# ---------------------------------------------------------------------------

W, H = 1024, 1024
MARGIN = 26
PAPER = (246, 241, 229)   # newsprint cream
INK = (25, 23, 19)
RED = (158, 27, 27)
NAVY = (23, 58, 94)
SEA = (207, 224, 232)
SAND = (233, 221, 192)
LAND = (216, 203, 168)
GREY = (96, 90, 80)
GOLD = (150, 108, 0)
WHITE = (255, 255, 255)

COL_X = [MARGIN, 362, 698]
COL_W = 300


def draw_masthead(cv):
    cv.text_centered(W // 2, 18, "THE WORLD IN ONE PICTURE", 5, INK, bold=True)
    cv.text_centered(
        W // 2, 60,
        "SATURDAY 21 NOVEMBER 2026 \u00b7 35 STORIES \u00b7 9 REGIONS "
        "\u00b7 ALL VERIFIED \u2713",
        2, INK)
    cv.hline(MARGIN, 84, W - 2 * MARGIN, INK, 3)
    cv.hline(MARGIN, 90, W - 2 * MARGIN, INK, 1)


def draw_lead(cv):
    # Kicker, two-line headline, deck, sources -- left two-thirds.
    cv.draw_text(MARGIN, 104, LEAD["kicker"], 2, RED, bold=True)
    y = 124
    for line in LEAD["headline"]:
        cv.draw_text(MARGIN, y, line, 4, INK, bold=True)
        y += 30
    deck_lines = cv.wrap(LEAD["deck"], 2, 636)
    y = 190
    for line in deck_lines:
        cv.draw_text(MARGIN, y, line, 2, INK)
        y += 15
    cv.draw_text(MARGIN, y + 3, LEAD["source"], 2, GREY)
    draw_gulf(cv)


def draw_gulf(cv):
    """Stylised Persian Gulf diagram in the lead panel's right third."""
    x0, y0, w, h = 688, 104, 310, 176
    cv.fill_rect(x0, y0, w, h, SEA)
    cv.polyline([(x0, y0), (x0 + w - 1, y0), (x0 + w - 1, y0 + h - 1),
                 (x0, y0 + h - 1)], INK, 2, closed=True)
    arabia = [(x0, y0 + h), (x0, y0 + 108), (x0 + 70, y0 + 78),
              (x0 + 130, y0 + 92), (x0 + 160, y0 + 128), (x0 + 176, y0 + h)]
    iran = [(x0 + w, y0), (x0 + w, y0 + h), (x0 + 250, y0 + h),
            (x0 + 224, y0 + 140), (x0 + 234, y0 + 88), (x0 + 260, y0 + 44),
            (x0 + 290, y0 + 14)]
    cv.polygon(arabia, SAND)
    cv.polygon(iran, SAND)
    cv.polyline(arabia, INK, 1)
    cv.polyline(iran, INK, 1)
    cv.draw_text(x0 + 118, y0 + 52, "PERSIAN GULF", 1, NAVY, bold=True)
    cv.draw_text(x0 + 262, y0 + 66, "IRAN", 2, INK, bold=True)
    cv.draw_text(x0 + 30, y0 + 138, "ARABIA", 2, INK, bold=True)
    # Missile path from Iran toward Bahrain, then the strike star.
    cv.line(x0 + 248, y0 + 90, x0 + 192, y0 + 112, RED, 2)
    cv.line(x0 + 192, y0 + 112, x0 + 204, y0 + 108, RED, 2)
    cv.line(x0 + 192, y0 + 112, x0 + 196, y0 + 122, RED, 2)
    bx, by = x0 + 185, y0 + 115
    cv.disc(bx, by, 7, RED)
    cv.draw_text(x0 + 144, y0 + 130, "BAHRAIN", 2, RED, bold=True)
    cv.draw_text(x0 + 150, y0 + 146, "US bases hit", 1, RED)
    qx, qy = x0 + 235, y0 + 158
    cv.disc(qx, qy, 4, INK)
    cv.draw_text(qx + 7, qy - 3, "QESHM IS.", 1, INK)
    cv.draw_text(x0 + 180, y0 + 166, "STRAIT OF HORMUZ", 1, NAVY)


def draw_timeline(cv):
    cv.draw_text(MARGIN, 286, "THE DAY IN UTC \u2014 21 NOVEMBER 2026", 2,
                 NAVY, bold=True)
    cv.draw_text(W - MARGIN - cv.text_width("ALL TIMES UTC \u2713", 2), 286,
                 "ALL TIMES UTC \u2713", 2, GREY)
    seg = (W - 2 * MARGIN) / len(TIMELINE)
    y_rule = 322
    cv.hline(MARGIN, y_rule, W - 2 * MARGIN, INK, 2)
    for i, (when, l1, l2) in enumerate(TIMELINE):
        cx = int(MARGIN + seg * i + seg / 2)
        cv.draw_text(cx - cv.text_width(when, 2) // 2, 304, when, 2, RED,
                     bold=True)
        cv.disc(cx, y_rule + 1, 5, RED)
        cv.text_centered(cx, y_rule + 10, l1, 2, INK, bold=True)
        cv.text_centered(cx, y_rule + 25, l2, 2, INK, bold=True)


def draw_columns(cv):
    headers = ["MIDDLE EAST & EUROPE", "THE AMERICAS & ASIA",
               "AFRICA, SPACE & SPORT"]
    cv.draw_text(MARGIN, 366, "THE REST OF THE DAY \u2014 34 MORE STORIES",
                 2, INK, bold=True)
    y = 388
    for x, head in zip(COL_X, headers):
        cv.draw_text(x, y, head, 2, NAVY, bold=True)
        cv.hline(x, y + 17, COL_W, NAVY, 2)
    y = 414
    for col, x in zip((COL_A, COL_B, COL_C), COL_X):
        # Spread each column evenly down to y=848 so no column ends ragged.
        gap = (848 - y - 30 * len(col)) // max(1, len(col) - 1)
        cy = y
        for si, (region, head, sub) in enumerate(col):
            lines = cv.wrap(head, 2, COL_W)
            for ln in lines:
                cv.draw_text(x, cy, ln, 2, INK, bold=True)
                cy += 15
            cv.draw_text(x, cy, sub, 2, GREY)
            cy += 15
            if si < len(col) - 1:
                cy += gap  # breathing room between stories
        if cy > 852:
            print("WARNING: column at x=%d overflows to y=%d" % (x, cy),
                  file=sys.stderr)


def project(x0, y0, w, h, lon, lat):
    """Equirectangular projection into the map box (lat 75..-60)."""
    px = x0 + (lon + 180.0) / 360.0 * w
    py = y0 + (75.0 - lat) / 135.0 * h
    return int(px), int(py)


def draw_map(cv):
    cv.draw_text(MARGIN, 860, "WHERE IT HAPPENED \u2014 12 PLACES IN THE NEWS",
                 2, NAVY, bold=True)
    cv.draw_text(W - MARGIN - cv.text_width("STYLISED MAP \u2014 NOT TO SCALE", 1),
                 864, "STYLISED MAP \u2014 NOT TO SCALE", 1, GREY)
    x0, y0, w, h = MARGIN, 878, 634, 82
    cv.fill_rect(x0, y0, w, h, SEA)
    cv.polyline([(x0, y0), (x0 + w - 1, y0), (x0 + w - 1, y0 + h - 1),
                 (x0, y0 + h - 1)], INK, 1, closed=True)
    for name, pts in WORLD.items():
        poly = [project(x0, y0, w, h, lon, lat) for lon, lat in pts]
        cv.polygon(poly, LAND)
        cv.polyline(poly, INK, 1, closed=True)
    for num, lon, lat, _label in PINS:
        px, py = project(x0, y0, w, h, lon, lat)
        cv.disc(px, py, 5, RED)
        cv.ring(px, py, 5, WHITE, 1)
        # Number beside the dot, not inside it: dots in Europe sit a few
        # pixels apart, so in-disc numbers would collide.
        cv.draw_text(px + 7, py - 9, str(num), 1, RED, bold=True)
    # Key, two columns to the right of the map.
    kx = [684, 842]
    for i, (num, _lon, _lat, label) in enumerate(PINS):
        col = i // 6
        row = i % 6
        cv.draw_text(kx[col], 882 + row * 13, "%d %s" % (num, label), 1, INK)


def draw_footer(cv):
    cv.hline(MARGIN, 970, W - 2 * MARGIN, INK, 1)
    cv.text_centered(W // 2, 978, FOOTER_SOURCES, 2, GREY)
    cv.text_centered(W // 2, 996, FOOTER_CHECK, 2, INK, bold=True)


def render():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_lead(cv)
    draw_timeline(cv)
    draw_columns(cv)
    draw_map(cv)
    draw_footer(cv)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    png = write_png(render())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote %s %d bytes sha256=%s"
          % (path, len(png), hashlib.sha256(png).hexdigest()))


if __name__ == "__main__":
    main()
