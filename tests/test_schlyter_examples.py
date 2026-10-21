"""Intermediate results checked against Paul Schlyter's worked example
(https://stjarnhimlen.se/comp/tutorial.html), 1990-04-19 00:00 UT,
observer at 60 N, 15 E. Values in the tutorial are rounded to 4 decimals,
so most tolerances are a few 1e-4 degrees.
"""
import pytest

import skyengine
from skyengine import timecalc, orbit, sun, moon, planets
import helpers

D = -3543
DF = 0.0
LAT = 60.0
LON = 15.0
UTC = (1990, 4, 19, 0, 0, 0)


def test_sun_elements_and_longitude():
    lon, r, M, w = sun.geocentric(D, DF)
    assert M == pytest.approx(104.0653, abs=1e-4)
    assert w == pytest.approx(282.7735, abs=1e-4)
    assert timecalc.rev(M + w) == pytest.approx(26.8388, abs=1e-4)
    assert lon == pytest.approx(28.6869, abs=2e-4)
    assert r == pytest.approx(1.004323, abs=1e-6)


def test_sun_equatorial_and_horizontal():
    lon, r, M, w = sun.geocentric(D, DF)
    ecl = timecalc.obliquity(D)
    x, y = r * orbit.cosd(lon), r * orbit.sind(lon)
    assert (x, y) == pytest.approx((0.881048, 0.482098), abs=2e-6)
    xe, ye, ze = orbit.ecliptic_to_equatorial(x, y, 0.0, ecl)
    assert (xe, ye, ze) == pytest.approx((0.881048, 0.442312, 0.191778), abs=2e-6)
    ra, dec = helpers.radec(xe, ye, ze)
    assert ra == pytest.approx(26.6580, abs=2e-4)
    assert dec == pytest.approx(11.0084, abs=2e-4)

    lst = timecalc.local_sidereal_time(timecalc.rev(M + w), 0.0, LON)
    assert lst == pytest.approx(14.78925 * 15.0, abs=1e-3)
    az, alt = orbit.horizontal(xe, ye, ze, lst, LAT)
    assert az == pytest.approx(15.6767, abs=1e-3)
    assert alt == pytest.approx(-17.9570, abs=1e-3)

    az, alt = skyengine.position(skyengine.SUN, UTC, LAT, LON)
    assert az == pytest.approx(15.6767, abs=1e-3)
    assert alt == pytest.approx(-17.9570, abs=1e-3)


def test_moon_elements():
    N = timecalc.rev(orbit.element(125.1228, -0.0529538083, D, DF))
    w = timecalc.rev(orbit.element(318.0634, 0.1643573223, D, DF))
    M = timecalc.rev(orbit.element(115.3654, 13.0649929509, D, DF))
    assert N == pytest.approx(312.7381, abs=1e-4)
    assert w == pytest.approx(95.7454, abs=1e-4)
    assert M == pytest.approx(266.0954, abs=1e-4)
    E = orbit.eccentric_anomaly(M, 0.054900)
    assert E == pytest.approx(262.9735, abs=1e-4)
    r, v = orbit.orbit_plane_position(60.2666, 0.054900, M)
    assert r == pytest.approx(60.67134, abs=1e-4)
    assert v == pytest.approx(259.8605 - 360.0, abs=1e-4)


def test_moon_geocentric_with_perturbations():
    _, _, Ms, ws = sun.geocentric(D, DF)
    Ls = timecalc.rev(Ms + ws)
    lon, lat, r = moon.geocentric(D, DF, Ms, Ls)
    assert lon == pytest.approx(306.9484, abs=2e-4)
    assert lat == pytest.approx(-0.5856, abs=2e-4)
    assert r == pytest.approx(60.6779, abs=2e-3)

    ecl = timecalc.obliquity(D)
    x, y, z = orbit.rect(lon, lat, 1.0)
    xe, ye, ze = orbit.ecliptic_to_equatorial(x, y, z, ecl)
    ra, dec = helpers.radec(xe, ye, ze)
    assert ra == pytest.approx(309.5011, abs=3e-4)
    assert dec == pytest.approx(-19.1032, abs=3e-4)


def test_moon_topocentric():
    """Our vector parallax correction vs Schlyter's RA/Dec formulas.

    Schlyter's topRA/topDecl formulas are first-order approximations; the
    exact vector subtraction used by the engine differs from them by a few
    thousandths of a degree, hence the 0.01 deg tolerance.
    """
    _, _, Ms, ws = sun.geocentric(D, DF)
    Ls = timecalc.rev(Ms + ws)
    lst = timecalc.local_sidereal_time(Ls, 0.0, LON)
    lon, lat, r = moon.geocentric(D, DF, Ms, Ls)
    ecl = timecalc.obliquity(D)
    x, y, z = orbit.rect(lon, lat, r)
    xe, ye, ze = orbit.ecliptic_to_equatorial(x, y, z, ecl)
    ox, oy, oz = moon.observer_vector(LAT, lst)
    ra, dec = helpers.radec(xe - ox, ye - oy, ze - oz)
    assert ra == pytest.approx(310.0017, abs=1e-2)
    assert dec == pytest.approx(-19.8790, abs=1e-2)


PLANET_ELEMENTS = {
    # planet: (N, i, w, a, e, M)
    planets.MERCURY: (48.2163, 7.0045, 29.0882, 0.387098, 0.205633, 69.5153),
    planets.VENUS: (76.5925, 3.3945, 54.8420, 0.723330, 0.006778, 131.6578),
    planets.MARS: (49.4826, 1.8498, 286.3978, 1.523688, 0.093396, 321.9965),
    planets.JUPITER: (100.3561, 1.3036, 273.8194, 5.20256, 0.048482, 85.5238),
    planets.SATURN: (113.5787, 2.4890, 339.2884, 9.55475, 0.055580, 198.4741),
    planets.URANUS: (73.9510, 0.7732, 96.5529, 19.18176, 0.047292, 101.0460),
    planets.NEPTUNE: (131.6737, 1.7709, 272.8675, 30.05814, 0.008598, 239.0063),
}


@pytest.mark.parametrize("planet,expected", sorted(PLANET_ELEMENTS.items()))
def test_planet_elements(planet, expected):
    el = planets.ELEMENTS[planet]
    got = (timecalc.rev(orbit.element(el[0], el[1], D, DF)),
           orbit.element(el[2], el[3], D, DF),
           timecalc.rev(orbit.element(el[4], el[5], D, DF)),
           orbit.element(el[6], el[7], D, DF),
           orbit.element(el[8], el[9], D, DF),
           planets.mean_anomaly(planet, D, DF))
    for g, e, tol in zip(got, expected, (1e-4, 1e-4, 1e-4, 1e-5, 1e-6, 1e-4)):
        assert g == pytest.approx(e, abs=tol)


HELIOCENTRIC = {
    # planet: (lon, lat, r) with Schlyter's perturbations applied
    planets.MERCURY: (170.5709, 5.9255, 0.374862),
    planets.VENUS: (263.6570, -0.4180, 0.726607),
    planets.MARS: (290.6297, -1.6203, 1.417194),
    planets.JUPITER: (105.2423, 0.1113, 5.19508),
    planets.SATURN: (289.3824, 0.1845, 10.06118),
    planets.URANUS: (276.7672, -0.3003, 19.39628),
    planets.NEPTUNE: (282.7192, 0.8575, 30.19284),
}


@pytest.mark.parametrize("planet,expected", sorted(HELIOCENTRIC.items()))
def test_planet_heliocentric(planet, expected):
    Mj = planets.mean_anomaly(planets.JUPITER, D, DF)
    Ms = planets.mean_anomaly(planets.SATURN, D, DF)
    Mu = planets.mean_anomaly(planets.URANUS, D, DF)
    lon, lat, r = planets.heliocentric(planet, D, DF, Mj, Ms, Mu)
    assert lon == pytest.approx(expected[0], abs=3e-4)
    assert lat == pytest.approx(expected[1], abs=3e-4)
    assert r == pytest.approx(expected[2], rel=2e-5)


def test_mercury_kepler_iteration():
    assert orbit.eccentric_anomaly(69.5153, 0.205633) == pytest.approx(81.1572, abs=1e-4)


def test_mercury_geocentric():
    slon, rs, Ms, ws = sun.geocentric(D, DF)
    xs, ys = rs * orbit.cosd(slon), rs * orbit.sind(slon)
    Mj = planets.mean_anomaly(planets.JUPITER, D, DF)
    Msat = planets.mean_anomaly(planets.SATURN, D, DF)
    Mu = planets.mean_anomaly(planets.URANUS, D, DF)
    lon, lat, r = planets.heliocentric(planets.MERCURY, D, DF, Mj, Msat, Mu)
    x, y, z = orbit.rect(lon, lat, r)
    assert (x, y, z) == pytest.approx((-0.367821, 0.061084, 0.038699), abs=3e-6)
    xg, yg, zg = x + xs, y + ys, z
    assert (xg, yg, zg) == pytest.approx((0.513227, 0.543182, 0.038699), abs=3e-6)
    xe, ye, ze = orbit.ecliptic_to_equatorial(xg, yg, zg, timecalc.obliquity(D))
    assert (xe, ye, ze) == pytest.approx((0.513227, 0.482961, 0.251582), abs=3e-6)
    ra, dec = helpers.radec(xe, ye, ze)
    assert ra == pytest.approx(43.2598, abs=3e-4)
    assert dec == pytest.approx(19.6460, abs=3e-4)
