#!/usr/bin/env python3

"""Generate reference fixtures with Astronomy Engine (independent of skyengine).

Usage (from the repository root, inside the test venv):

    python tests/tools/gen_fixtures.py

Writes tests/fixtures/reference_positions.jsonl (full set for the CPython
suite) and tests/fixtures/reference_device.jsonl (small subset for the
MicroPython runner). Each line is one JSON object:

    {"id": "...", "utc": [y, m, d, h, mi, s], "lat": .., "lon": ..,
     "pos": [[az, alt] x 9],      # topocentric, equinox of date, no refraction
     "moon_geo": [az, alt]}       # geocentric Moon, for the parallax test

The first line is a {"meta": ...} record describing the generator.
Body order matches skyengine: Sun, Moon, Mercury, Venus, Mars, Jupiter,
Saturn, Uranus, Neptune.
"""
import json
import os
import sys

import astronomy as ae

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), "fixtures")

BODIES = [ae.Body.Sun, ae.Body.Moon, ae.Body.Mercury, ae.Body.Venus, ae.Body.Mars,
          ae.Body.Jupiter, ae.Body.Saturn, ae.Body.Uranus, ae.Body.Neptune]

# name, latitude (N+), longitude (E+)
LOCATIONS = [
    ("warsaw", 52.23, 21.01),
    ("reykjavik", 64.13, -21.90),
    ("quito", -0.18, -78.47),
    ("singapore", 1.35, 103.82),
    ("sydney", -33.87, 151.21),
    ("ushuaia", -54.80, -68.30),
    ("longyearbyen", 78.22, 15.63),
    ("honolulu", 21.31, -157.86),
    ("null_island", 0.0, 0.0),
    ("mcmurdo", -77.85, 166.67),
]
GRID_LOCATIONS = LOCATIONS[:5]

GRID_YEARS = list(range(2020, 2051, 3))
GRID_DATES = [(1, 15), (4, 20), (7, 25), (10, 30)]
GRID_HOURS = [0, 6, 12, 18]

SPECIAL_INSTANTS = [
    ("equinox_mar_2024", (2024, 3, 20, 3, 6, 0)),
    ("solstice_jun_2024", (2024, 6, 20, 20, 51, 0)),
    ("equinox_sep_2024", (2024, 9, 22, 12, 44, 0)),
    ("solstice_dec_2024", (2024, 12, 21, 9, 20, 0)),
    ("equinox_mar_2040", (2040, 3, 20, 11, 11, 0)),
    ("solstice_dec_2040", (2040, 12, 21, 12, 20, 0)),
    ("leap_day_2024", (2024, 2, 29, 23, 59, 59)),
    ("leap_day_2028", (2028, 2, 29, 12, 0, 0)),
    ("after_leap_2028", (2028, 3, 1, 0, 0, 0)),
    ("year_end_2029", (2029, 12, 31, 23, 59, 59)),
    ("year_start_2030", (2030, 1, 1, 0, 0, 0)),
    ("year_start_2030_1s", (2030, 1, 1, 0, 0, 1)),
    ("month_end_2031", (2031, 4, 30, 23, 59, 30)),
    ("month_start_2031", (2031, 5, 1, 0, 0, 30)),
    ("midnight_2045", (2045, 8, 10, 0, 0, 0)),
    ("range_start", (2020, 1, 1, 0, 0, 0)),
    ("range_end", (2050, 12, 31, 23, 59, 59)),
]

# Instants at which a near-zenith observer location is derived for a body.
ZENITH_INSTANTS = [
    ("sun", ae.Body.Sun, (2024, 3, 20, 12, 7, 0)),
    ("sun", ae.Body.Sun, (2033, 6, 21, 4, 0, 0)),
    ("moon", ae.Body.Moon, (2027, 2, 2, 20, 0, 0)),
    ("moon", ae.Body.Moon, (2041, 9, 9, 9, 0, 0)),
    ("jupiter", ae.Body.Jupiter, (2029, 11, 11, 11, 0, 0)),
    ("venus", ae.Body.Venus, (2036, 5, 5, 5, 0, 0)),
]


def make_time(utc):
    return ae.Time.Make(utc[0], utc[1], utc[2], utc[3], utc[4], utc[5])


def horizon(time, observer, body):
    eq = ae.Equator(body, time, observer, True, False)  # of date, no aberration
    h = ae.Horizon(time, observer, eq.ra, eq.dec, ae.Refraction.Airless)
    return [round(h.azimuth, 5), round(h.altitude, 5)]


def moon_geocentric_horizon(time, observer):
    vec = ae.GeoMoon(time)                       # J2000 equatorial, geocentric
    vec = ae.RotateVector(ae.Rotation_EQJ_EQD(time), vec)
    eq = ae.EquatorFromVector(vec)
    h = ae.Horizon(time, observer, eq.ra, eq.dec, ae.Refraction.Airless)
    return [round(h.azimuth, 5), round(h.altitude, 5)]


def sub_point(body, time):
    """Latitude/longitude where body is at the geocentric zenith."""
    eq = ae.Equator(body, time, ae.Observer(0.0, 0.0, 0.0), True, False)
    lon = eq.ra * 15.0 - ae.SiderealTime(time) * 15.0
    lon = (lon + 180.0) % 360.0 - 180.0
    return round(eq.dec, 4), round(lon, 4)


def case(case_id, utc, lat, lon):
    time = make_time(utc)
    observer = ae.Observer(lat, lon, 0.0)
    return {
        "id": case_id,
        "utc": list(utc),
        "lat": lat,
        "lon": lon,
        "pos": [horizon(time, observer, b) for b in BODIES],
        "moon_geo": moon_geocentric_horizon(time, observer),
    }


def build_cases():
    full = []
    device = []
    n = 0
    for year in GRID_YEARS:
        for month, day in GRID_DATES:
            for hour in GRID_HOURS:
                utc = (year, month, day, hour, 0, 0)
                for name, lat, lon in GRID_LOCATIONS:
                    c = case("grid_%d%02d%02d_%02dh_%s" % (year, month, day, hour, name),
                             utc, lat, lon)
                    full.append(c)
                    if n % 23 == 0:
                        device.append(c)
                    n += 1
    for tag, utc in SPECIAL_INSTANTS:
        for name, lat, lon in LOCATIONS:
            c = case("%s_%s" % (tag, name), utc, lat, lon)
            full.append(c)
            if name in ("warsaw", "quito", "mcmurdo"):
                device.append(c)
    for tag, body, utc in ZENITH_INSTANTS:
        time = make_time(utc)
        lat, lon = sub_point(body, time)
        for dlat, dlon, suffix in ((0.0, 0.0, "zenith"), (0.3, -0.2, "near_zenith")):
            c = case("%s_%s_%d" % (tag, suffix, utc[0]), utc, lat + dlat, lon + dlon)
            full.append(c)
            device.append(c)
    return full, device


def generator_version():
    try:
        from importlib.metadata import version
        return version("astronomy-engine")
    except Exception:  # Python < 3.8 or package metadata missing
        return "unknown"


def write(path, cases):
    meta = {"meta": {
        "generator": "astronomy-engine",
        "version": generator_version(),
        "frame": "topocentric, equinox of date, no aberration, no refraction",
        "bodies": ["Sun", "Moon", "Mercury", "Venus", "Mars",
                   "Jupiter", "Saturn", "Uranus", "Neptune"],
        "cases": len(cases),
    }}
    with open(path, "w") as f:
        f.write(json.dumps(meta) + "\n")
        for c in cases:
            f.write(json.dumps(c, separators=(",", ":")) + "\n")
    print("wrote %d cases to %s" % (len(cases), path))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    full, device = build_cases()
    write(os.path.join(OUT_DIR, "reference_positions.jsonl"), full)
    write(os.path.join(OUT_DIR, "reference_device.jsonl"), device)


if __name__ == "__main__":
    sys.exit(main())
