"""Moon-specific checks: geocentric model, topocentric parallax correction."""
import math

import pytest

import skyengine
import helpers

MOON = skyengine.MOON


def test_geocentric_model_against_reference(reference_cases):
    errors = []
    for c in reference_cases:
        az, alt = helpers.moon_geocentric_horizontal(tuple(c["utc"]), c["lat"], c["lon"])
        errors.append(helpers.angular_separation(az, alt, *c["moon_geo"]))
    helpers.record_errors("Moon/geo", errors, 0.25)
    assert max(errors) < 0.25


def test_parallax_correction_matches_reference(reference_cases):
    """The shift we apply equals the shift between the two reference frames."""
    for c in reference_cases:
        utc = tuple(c["utc"])
        geo = helpers.moon_geocentric_horizontal(utc, c["lat"], c["lon"])
        topo = skyengine.position(MOON, utc, c["lat"], c["lon"])
        ours = helpers.angular_separation(*(geo + topo))
        ref = helpers.angular_separation(*(tuple(c["moon_geo"]) + tuple(c["pos"][MOON])))
        assert ours == pytest.approx(ref, abs=0.03), c["id"]


def test_parallax_magnitude(reference_cases):
    """Shift ~ horizontal parallax (0.9-1.0 deg) times cos(altitude)."""
    for c in reference_cases:
        utc = tuple(c["utc"])
        geo = helpers.moon_geocentric_horizontal(utc, c["lat"], c["lon"])
        topo = skyengine.position(MOON, utc, c["lat"], c["lon"])
        shift = helpers.angular_separation(*(geo + topo))
        expected = 0.95 * math.cos(math.radians(geo[1]))
        assert abs(shift - expected) < 0.08, c["id"]
        assert topo[1] <= geo[1] + 1e-9   # parallax always lowers the Moon


def test_topocentric_is_closer_than_geocentric(reference_cases):
    n = 0
    for c in reference_cases:
        utc = tuple(c["utc"])
        ref = tuple(c["pos"][MOON])
        if ref[1] > 70.0:
            continue  # near the zenith the shift is too small to rank
        geo = helpers.moon_geocentric_horizontal(utc, c["lat"], c["lon"])
        topo = skyengine.position(MOON, utc, c["lat"], c["lon"])
        assert helpers.angular_separation(*(topo + ref)) < helpers.angular_separation(*(geo + ref))
        n += 1
    assert n > 100


def test_moon_near_horizon_cases(reference_cases):
    near = [c for c in reference_cases if abs(c["pos"][MOON][1]) < 5.0]
    assert len(near) >= 20
    for c in near:
        az, alt = skyengine.position(MOON, tuple(c["utc"]), c["lat"], c["lon"])
        assert helpers.angular_separation(az, alt, *c["pos"][MOON]) < helpers.TOLERANCE[MOON]


def test_moon_orbital_configurations(reference_cases):
    """Fixtures span the lunar month: elongation from the Sun covers all quadrants."""
    quadrants = set()
    for c in reference_cases:
        sun_az, sun_alt = c["pos"][skyengine.SUN]
        moon_az, moon_alt = c["pos"][MOON]
        sep = helpers.angular_separation(sun_az, sun_alt, moon_az, moon_alt)
        quadrants.add(int(sep // 45))
    assert quadrants >= {0, 1, 2, 3}
