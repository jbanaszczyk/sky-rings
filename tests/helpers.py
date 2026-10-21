"""Shared helpers for the CPython test suite."""
import json
import math
import os

import skyengine
from skyengine import timecalc, orbit, sun, moon

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

# Acceptance tolerance in degrees per body index (Sun, Moon, planets...).
TOLERANCE = (1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)

# Filled by test_reference / test_moon, printed by conftest at the end.
ERROR_SUMMARY = {}


def angular_separation(az1, alt1, az2, alt2):
    """Great-circle angle in degrees between two (azimuth, altitude) directions."""
    a1, h1, a2, h2 = (math.radians(v) for v in (az1, alt1, az2, alt2))
    c = math.sin(h1) * math.sin(h2) + math.cos(h1) * math.cos(h2) * math.cos(a1 - a2)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def load_cases(name):
    cases = []
    with open(os.path.join(FIXTURE_DIR, name)) as f:
        for line in f:
            rec = json.loads(line)
            if "meta" in rec:
                continue
            cases.append(rec)
    assert cases, "no fixture cases in %s (run tests/tools/gen_fixtures.py)" % name
    return cases


def record_errors(name, errors, tol):
    ERROR_SUMMARY[name] = {"n": len(errors), "max": max(errors),
                           "mean": sum(errors) / len(errors), "tol": tol}


def moon_geocentric_horizontal(utc, lat, lon):
    """Moon azimuth/altitude without the parallax correction (test helper)."""
    d, ut = timecalc.day_number(utc)
    df = ut / 24.0
    ecl = timecalc.obliquity(d + df)
    _, _, Ms, ws = sun.geocentric(d, df)
    Ls = timecalc.rev(Ms + ws)
    lst = timecalc.local_sidereal_time(Ls, ut, lon)
    mlon, mlat, mr = moon.geocentric(d, df, Ms, Ls)
    x, y, z = orbit.rect(mlon, mlat, mr)
    xe, ye, ze = orbit.ecliptic_to_equatorial(x, y, z, ecl)
    return orbit.horizontal(xe, ye, ze, lst, lat)


def sun_mean_longitude(utc):
    d, ut = timecalc.day_number(utc)
    _, _, Ms, ws = sun.geocentric(d, ut / 24.0)
    return timecalc.rev(Ms + ws), ut


def lst(utc, lon):
    Ls, ut = sun_mean_longitude(utc)
    return timecalc.local_sidereal_time(Ls, ut, lon)


def wrap180(x):
    """Wrap an angle difference to (-180, 180]."""
    return (x + 180.0) % 360.0 - 180.0


BODIES = list(range(len(skyengine.NAMES)))


def radec(x, y, z):
    """Right ascension and declination in degrees from an equatorial vector."""
    return (timecalc.rev(math.degrees(math.atan2(y, x))),
            math.degrees(math.atan2(z, math.sqrt(x * x + y * y))))


def radec_to_horizontal(ra, dec, lst, lat):
    """(RA, Dec) in degrees -> (azimuth, altitude)."""
    x, y, z = orbit.rect(ra, dec, 1.0)
    return orbit.horizontal(x, y, z, lst, lat)
