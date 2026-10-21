"""Day number, time of day, angle normalisation and sidereal time."""
import datetime

import astronomy as ae
import pytest

from skyengine import timecalc
import helpers

EPOCH = datetime.date(1999, 12, 31)  # d = 0


def test_epoch_convention():
    assert timecalc.day_number((1999, 12, 31, 0, 0, 0)) == (0, 0.0)
    assert timecalc.day_number((2000, 1, 1, 0, 0, 0)) == (1, 0.0)
    assert timecalc.day_number((1990, 4, 19, 0, 0, 0)) == (-3543, 0.0)  # Schlyter's test date


@pytest.mark.parametrize("ymd", [
    (2020, 2, 28), (2020, 2, 29), (2020, 3, 1),       # leap year
    (2021, 2, 28), (2021, 3, 1),                      # common year
    (2024, 2, 29), (2048, 2, 29),
    (2029, 12, 31), (2030, 1, 1),                     # year boundary
    (2031, 4, 30), (2031, 5, 1),                      # month boundary
    (1900, 3, 1), (2100, 2, 28),                      # formula validity limits
])
def test_day_number_matches_calendar(ymd):
    d, _ = timecalc.day_number(ymd + (0, 0, 0))
    assert d == datetime.date(*ymd).toordinal() - EPOCH.toordinal()


def test_day_number_every_day_2019_to_2051():
    day = datetime.date(2019, 1, 1)
    end = datetime.date(2051, 12, 31)
    while day <= end:
        d, _ = timecalc.day_number((day.year, day.month, day.day, 0, 0, 0))
        assert d == day.toordinal() - EPOCH.toordinal(), day
        day += datetime.timedelta(days=1)


def test_time_of_day():
    _, ut = timecalc.day_number((2030, 6, 1, 12, 30, 0))
    assert ut == pytest.approx(12.5)
    _, ut = timecalc.day_number((2030, 6, 1, 23, 59, 59))
    assert ut == pytest.approx(23.0 + 59 / 60.0 + 59 / 3600.0)
    _, ut = timecalc.day_number((2030, 6, 1, 0, 0, 0.5))
    assert ut == pytest.approx(0.5 / 3600.0)


@pytest.mark.parametrize("x,expected", [
    (0.0, 0.0), (359.9, 359.9), (360.0, 0.0), (725.0, 5.0),
    (-10.0, 350.0), (-360.0, 0.0), (-725.0, 355.0), (1e6, 1e6 % 360.0),
])
def test_rev(x, expected):
    assert timecalc.rev(x) == pytest.approx(expected)


def test_rev_range_near_zero():
    for x in (-1e-12, -1e-9, 1e-12, 359.9999999999):
        r = timecalc.rev(x)
        assert 0.0 <= r < 360.0


@pytest.mark.parametrize("utc", [
    (2020, 1, 1, 0, 0, 0), (2024, 3, 20, 12, 0, 0), (2033, 9, 1, 23, 59, 59),
    (2041, 12, 31, 6, 15, 30), (2050, 7, 4, 18, 0, 0),
])
def test_gmst_against_astronomy_engine(utc):
    gmst = helpers.lst(utc, 0.0)
    ref = ae.SiderealTime(ae.Time.Make(*utc)) * 15.0  # apparent GST in degrees
    assert abs(helpers.wrap180(gmst - ref)) < 0.05


def test_sidereal_progression_per_hour():
    base = datetime.datetime(2030, 3, 10, 20, 0, 0)
    prev = helpers.lst(base.timetuple()[:6], 0.0)
    for h in range(1, 30):  # crosses midnight and a date rollover
        t = base + datetime.timedelta(hours=h)
        cur = helpers.lst(t.timetuple()[:6], 0.0)
        step = helpers.wrap180(cur - prev)
        assert step == pytest.approx(15.04107, abs=0.002)
        prev = cur


def test_sidereal_progression_across_year_boundary():
    a = helpers.lst((2029, 12, 31, 23, 59, 0), 0.0)
    b = helpers.lst((2030, 1, 1, 0, 0, 0), 0.0)
    c = helpers.lst((2030, 1, 1, 0, 1, 0), 0.0)
    assert helpers.wrap180(b - a) == pytest.approx(15.04107 / 60.0, abs=1e-4)
    assert helpers.wrap180(c - b) == pytest.approx(15.04107 / 60.0, abs=1e-4)


def test_longitude_sign_in_sidereal_time():
    utc = (2030, 5, 5, 5, 5, 5)
    at0 = helpers.lst(utc, 0.0)
    assert helpers.wrap180(helpers.lst(utc, 15.0) - at0) == pytest.approx(15.0)
    assert helpers.wrap180(helpers.lst(utc, -75.0) - at0) == pytest.approx(-75.0)
    assert 0.0 <= helpers.lst(utc, 179.9) < 360.0
    assert 0.0 <= helpers.lst(utc, -179.9) < 360.0


def test_obliquity():
    assert timecalc.obliquity(-3543) == pytest.approx(23.4406, abs=5e-5)
    assert timecalc.obliquity(0) == pytest.approx(23.4393)
