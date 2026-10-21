"""Coordinate conventions of the shared RA/Dec -> azimuth/altitude transform
and of the public API output."""
import pytest

import skyengine
from skyengine import orbit
import helpers

LST = 123.4  # arbitrary local sidereal time (degrees)


def test_object_on_meridian_at_zenith():
    az, alt = orbit.radec_to_horizontal(LST, 50.0, LST, 50.0)
    assert alt == pytest.approx(90.0, abs=1e-9)


def test_transit_south_of_zenith():
    az, alt = orbit.radec_to_horizontal(LST, 20.0, LST, 50.0)
    assert az == pytest.approx(180.0)
    assert alt == pytest.approx(60.0)


def test_transit_north_of_zenith_northern_observer():
    az, alt = orbit.radec_to_horizontal(LST, 80.0, LST, 50.0)
    assert az == pytest.approx(0.0) or az == pytest.approx(360.0)
    assert alt == pytest.approx(60.0)


def test_transit_north_of_zenith_southern_observer():
    az, alt = orbit.radec_to_horizontal(LST, -10.0, LST, -40.0)
    assert az == pytest.approx(0.0) or az == pytest.approx(360.0)
    assert alt == pytest.approx(60.0)


def test_south_transit_southern_observer():
    az, alt = orbit.radec_to_horizontal(LST, -70.0, LST, -40.0)
    assert az == pytest.approx(180.0)
    assert alt == pytest.approx(60.0)


@pytest.mark.parametrize("lat", [-60.0, -10.0, 0.0, 35.0, 70.0])
def test_equatorial_object_rising_east_setting_west(lat):
    # hour angle -90: rising point of the celestial equator, due east
    az, alt = orbit.radec_to_horizontal(LST + 90.0, 0.0, LST, lat)
    assert az == pytest.approx(90.0)
    assert alt == pytest.approx(0.0, abs=1e-9)
    # hour angle +90: due west
    az, alt = orbit.radec_to_horizontal(LST - 90.0, 0.0, LST, lat)
    assert az == pytest.approx(270.0)
    assert alt == pytest.approx(0.0, abs=1e-9)


def test_celestial_pole():
    az, alt = orbit.radec_to_horizontal(0.0, 90.0, LST, 50.0)
    assert alt == pytest.approx(50.0)
    assert az == pytest.approx(0.0, abs=1e-6) or az == pytest.approx(360.0, abs=1e-6)
    az, alt = orbit.radec_to_horizontal(0.0, 90.0, LST, 0.0)   # pole on the horizon at the equator
    assert alt == pytest.approx(0.0, abs=1e-9)
    az, alt = orbit.radec_to_horizontal(0.0, -90.0, LST, -30.0)
    assert alt == pytest.approx(30.0)
    assert az == pytest.approx(180.0)


def test_north_pole_observer_altitude_equals_declination():
    for ra in (0.0, 90.0, 200.0, 359.0):
        for dec in (-45.0, 0.0, 33.0):
            _, alt = orbit.radec_to_horizontal(ra, dec, LST, 90.0)
            assert alt == pytest.approx(dec)


def test_below_horizon():
    az, alt = orbit.radec_to_horizontal(LST, -60.0, LST, 50.0)
    assert alt == pytest.approx(-20.0)
    az, alt = orbit.radec_to_horizontal(LST + 180.0, 0.0, LST, 50.0)  # lower culmination
    assert alt == pytest.approx(-40.0)
    assert az == pytest.approx(0.0) or az == pytest.approx(360.0)


def test_azimuth_normalised_over_full_sweep():
    for ha10 in range(-1800, 1800):
        ha = ha10 / 10.0
        for dec in (-80.0, -20.0, 0.0, 55.0, 89.0):
            az, alt = orbit.radec_to_horizontal(LST - ha, dec, LST, 50.0)
            assert 0.0 <= az < 360.0
            assert -90.0 <= alt <= 90.0


def test_azimuth_wrap_around_north():
    # object just east / just west of the meridian, north of the zenith
    az_e, _ = orbit.radec_to_horizontal(LST + 0.5, 80.0, LST, 50.0)
    az_w, _ = orbit.radec_to_horizontal(LST - 0.5, 80.0, LST, 50.0)
    assert az_e < 90.0           # a few degrees east of north
    assert az_w > 270.0          # a few degrees west of north
    assert abs(helpers.wrap180(az_e - az_w)) < 10.0


def test_horizontal_ignores_vector_length():
    a = orbit.horizontal(1.0, 2.0, 3.0, LST, 40.0)
    b = orbit.horizontal(1000.0, 2000.0, 3000.0, LST, 40.0)
    assert a == pytest.approx(b)


def test_radec_roundtrip():
    for ra in (0.0, 45.0, 179.9, 180.1, 300.0):
        for dec in (-89.0, -20.0, 0.0, 66.0):
            x, y, z = orbit.rect(ra, dec, 1.0)
            r, d = orbit.radec(x, y, z)
            assert r == pytest.approx(ra, abs=1e-9)
            assert d == pytest.approx(dec, abs=1e-9)


def test_api_shape_and_ranges():
    res = skyengine.positions((2030, 7, 1, 12, 0, 0), 45.0, 10.0)
    assert isinstance(res, tuple) and len(res) == 9
    assert len(skyengine.NAMES) == 9
    for az, alt in res:
        assert 0.0 <= az < 360.0
        assert -90.0 <= alt <= 90.0
    assert skyengine.position(skyengine.MARS, (2030, 7, 1, 12, 0, 0), 45.0, 10.0) == res[skyengine.MARS]
    assert (skyengine.SUN, skyengine.MOON, skyengine.NEPTUNE) == (0, 1, 8)


def test_longitude_sign_moves_sun_through_the_day():
    # Equinox, 12:00 UTC, latitude 50 N: the Sun is near due south at 0 E,
    # in the west for an eastern observer and in the east for a western one.
    utc = (2030, 3, 20, 12, 0, 0)
    az0, alt0 = skyengine.position(skyengine.SUN, utc, 50.0, 0.0)
    az_e, alt_e = skyengine.position(skyengine.SUN, utc, 50.0, 90.0)
    az_w, alt_w = skyengine.position(skyengine.SUN, utc, 50.0, -90.0)
    assert abs(az0 - 180.0) < 5.0 and alt0 > 35.0
    assert 260.0 < az_e < 280.0 and abs(alt_e) < 5.0
    assert 80.0 < az_w < 100.0 and abs(alt_w) < 5.0


def test_southern_hemisphere_sun_culminates_north():
    utc = (2030, 3, 20, 12, 10, 0)
    az, alt = skyengine.position(skyengine.SUN, utc, -40.0, 0.0)
    assert abs(az) < 5.0 or abs(az - 360.0) < 5.0
    assert alt > 45.0


def test_equator_observer_equinox_sun_near_zenith():
    utc = (2030, 3, 20, 12, 10, 0)
    _, alt = skyengine.position(skyengine.SUN, utc, 0.0, 0.0)
    assert alt > 89.0


def test_high_latitude_midnight_sun():
    # Longyearbyen, June solstice: the Sun stays above the horizon all day.
    for hour in range(24):
        _, alt = skyengine.position(skyengine.SUN, (2030, 6, 21, hour, 0, 0), 78.22, 15.63)
        assert alt > 10.0
    # ...and stays below it in December.
    for hour in range(24):
        _, alt = skyengine.position(skyengine.SUN, (2030, 12, 21, hour, 0, 0), 78.22, 15.63)
        assert alt < -10.0
