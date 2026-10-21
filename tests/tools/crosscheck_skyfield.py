#!/usr/bin/env python3

"""Optional: cross-check the Astronomy Engine fixtures against Skyfield.

This guards against trusting a single reference implementation. It is not
part of the regular test suite because Skyfield needs the de421.bsp
ephemeris (about 17 MB, downloaded on first use).

    pip install skyfield
    python tests/tools/crosscheck_skyfield.py [max_cases]

Prints the maximum disagreement per body between the two references and
exits with status 1 if any exceeds 0.05 degrees.
"""
import json
import math
import os
import sys

from skyfield.api import load, wgs84

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(os.path.dirname(HERE), "fixtures", "reference_positions.jsonl")
NAMES = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
TARGETS = ["sun", "moon", "mercury", "venus", "mars barycenter", "jupiter barycenter",
           "saturn barycenter", "uranus barycenter", "neptune barycenter"]
LIMIT = 0.05


def separation(az1, alt1, az2, alt2):
    a1, h1, a2, h2 = (math.radians(v) for v in (az1, alt1, az2, alt2))
    c = math.sin(h1) * math.sin(h2) + math.cos(h1) * math.cos(h2) * math.cos(a1 - a2)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def main(max_cases=None):
    ts = load.timescale()
    eph = load("de421.bsp")
    earth = eph["earth"]
    worst = [0.0] * 9
    n = 0
    with open(FIXTURE) as f:
        for line in f:
            rec = json.loads(line)
            if "meta" in rec:
                continue
            if max_cases and n >= max_cases:
                break
            y, m, d, hh, mm, ss = rec["utc"]
            t = ts.ut1(y, m, d, hh, mm, ss)
            site = earth + wgs84.latlon(rec["lat"], rec["lon"])
            for i, target in enumerate(TARGETS):
                # geometric (light-time corrected, no aberration) position, equinox of date
                app = site.at(t).observe(eph[target])
                alt, az, _ = app.apparent().altaz()
                err = separation(az.degrees, alt.degrees, *rec["pos"][i])
                worst[i] = max(worst[i], err)
            n += 1
    print("cross-checked %d cases against Skyfield/de421" % n)
    bad = False
    for name, w in zip(NAMES, worst):
        flag = "" if w <= LIMIT else "  <-- exceeds %.2f" % LIMIT
        bad = bad or w > LIMIT
        print("%-8s max disagreement %.4f deg%s" % (name, w, flag))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else None))
