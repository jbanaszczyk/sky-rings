"""Continuity, monotonic motion and determinism over time."""
import datetime

import pytest

import skyengine
from skyengine import timecalc, sun, moon
import helpers

WARSAW = (52.23, 21.01)


def minute_series(start, minutes, lat, lon):
    out = []
    t = start
    for _ in range(minutes):
        out.append(skyengine.positions(t.timetuple()[:6], lat, lon))
        t += datetime.timedelta(minutes=1)
    return out


def test_no_jumps_minute_to_minute_over_a_day():
    series = minute_series(datetime.datetime(2030, 3, 10, 0, 0, 0), 24 * 60 + 5, *WARSAW)
    for prev, cur in zip(series, series[1:]):
        for body in helpers.BODIES:
            step = helpers.angular_separation(*(prev[body] + cur[body]))
            assert step < 0.30, skyengine.NAMES[body]   # diurnal motion <= 0.25 deg/min


def test_no_jumps_across_year_boundary():
    series = minute_series(datetime.datetime(2029, 12, 31, 23, 50, 0), 20, *WARSAW)
    for prev, cur in zip(series, series[1:]):
        for body in helpers.BODIES:
            assert helpers.angular_separation(*(prev[body] + cur[body])) < 0.30


def test_no_jumps_across_leap_day():
    series = minute_series(datetime.datetime(2028, 2, 29, 23, 50, 0), 20, -33.87, 151.21)
    for prev, cur in zip(series, series[1:]):
        for body in helpers.BODIES:
            assert helpers.angular_separation(*(prev[body] + cur[body])) < 0.30


def test_one_second_step_is_tiny():
    a = skyengine.positions((2040, 10, 10, 10, 10, 10), *WARSAW)
    b = skyengine.positions((2040, 10, 10, 10, 10, 11), *WARSAW)
    for body in helpers.BODIES:
        assert helpers.angular_separation(*(a[body] + b[body])) < 0.006


def test_sun_azimuth_increases_clockwise_at_mid_latitude():
    # At latitude 52 N the Sun's azimuth increases monotonically all day.
    series = minute_series(datetime.datetime(2030, 6, 1, 0, 0, 0), 24 * 60, *WARSAW)
    for prev, cur in zip(series, series[1:]):
        daz = helpers.wrap180(cur[skyengine.SUN][0] - prev[skyengine.SUN][0])
        assert daz > 0.0


def test_sun_culminates_near_local_noon():
    # Warsaw, 21 E: local mean noon is 10:36 UTC; equation of time shifts it by < 17 min.
    series = minute_series(datetime.datetime(2030, 3, 10, 8, 0, 0), 5 * 60, *WARSAW)
    alts = [p[skyengine.SUN][1] for p in series]
    peak = alts.index(max(alts))
    peak_time = datetime.datetime(2030, 3, 10, 8, 0, 0) + datetime.timedelta(minutes=peak)
    assert datetime.datetime(2030, 3, 10, 10, 15) < peak_time < datetime.datetime(2030, 3, 10, 11, 0)
    # altitude rises before the peak and falls after it
    assert all(a < b for a, b in zip(alts[:peak], alts[1:peak + 1]))
    assert all(a > b for a, b in zip(alts[peak:], alts[peak + 1:]))


def test_moon_moves_eastward_about_13_degrees_per_day():
    for d in (7305, 9000, 12000, 15500, 18600):
        lons = []
        for dd in (d, d + 1):
            _, _, Ms, ws = sun.geocentric(dd, 0.0)
            lon, _, _ = moon.geocentric(dd, 0.0, Ms, timecalc.rev(Ms + ws))
            lons.append(lon)
        assert 11.0 < helpers.wrap180(lons[1] - lons[0]) < 16.0


def test_sun_moves_eastward_about_one_degree_per_day():
    for d in (7305, 9000, 12000, 15500, 18600):
        a = sun.geocentric(d, 0.0)[0]
        b = sun.geocentric(d + 1, 0.0)[0]
        assert 0.95 < helpers.wrap180(b - a) < 1.03


def test_deterministic():
    args = ((2033, 3, 3, 3, 3, 3), -12.5, 130.25)
    assert skyengine.positions(*args) == skyengine.positions(*args)
    assert skyengine.positions(*args) == skyengine.positions(*args)


def test_direction_vectors_continuous_through_zenith_passage():
    """Azimuth may swing by ~180 deg when the Sun passes near the zenith; the
    physical direction must not jump."""
    # Sun near the zenith at the equator around the equinox, 12:07 UTC at 0 E
    start = datetime.datetime(2030, 3, 20, 11, 50, 0)
    series = minute_series(start, 40, 0.0, 0.0)
    for prev, cur in zip(series, series[1:]):
        assert helpers.angular_separation(*(prev[skyengine.SUN] + cur[skyengine.SUN])) < 0.30
    assert max(p[skyengine.SUN][1] for p in series) > 89.0
