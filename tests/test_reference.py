"""Numerical accuracy against independent reference positions (Astronomy
Engine fixtures). Error metric: angular separation on the celestial sphere."""
import pytest

import skyengine
import helpers


@pytest.fixture(scope="module")
def computed(reference_cases):
    return [skyengine.positions(tuple(c["utc"]), c["lat"], c["lon"]) for c in reference_cases]


@pytest.mark.parametrize("body", helpers.BODIES, ids=skyengine.NAMES)
def test_body_within_tolerance(body, reference_cases, computed):
    tol = helpers.TOLERANCE[body]
    errors = []
    failures = []
    for case, pos in zip(reference_cases, computed):
        ref_az, ref_alt = case["pos"][body]
        az, alt = pos[body]
        err = helpers.angular_separation(az, alt, ref_az, ref_alt)
        errors.append(err)
        if err > tol:
            failures.append("%s: %.3f deg (ours %.3f/%.3f ref %.3f/%.3f)" % (
                case["id"], err, az, alt, ref_az, ref_alt))
    helpers.record_errors(skyengine.NAMES[body], errors, tol)
    assert not failures, "\n".join(failures[:20])


def test_fixture_coverage(reference_cases):
    """The fixture set exercises the situations the specification lists."""
    lats = [c["lat"] for c in reference_cases]
    lons = [c["lon"] for c in reference_cases]
    years = {c["utc"][0] for c in reference_cases}
    assert min(lats) < -50 and max(lats) > 70
    assert any(abs(lat) < 2 for lat in lats)
    assert min(lons) < -150 and max(lons) > 150
    assert min(years) <= 2020 and max(years) >= 2050
    assert len(years) >= 10
    hours = {c["utc"][3] for c in reference_cases}
    assert len(hours) >= 4

    alts = [alt for c in reference_cases for _, alt in c["pos"]]
    assert any(alt < -30 for alt in alts) and any(alt > 85 for alt in alts)
    assert sum(1 for alt in alts if abs(alt) < 3) >= 10    # near the horizon
    assert sum(1 for alt in alts if alt > 88) >= 3          # near the zenith


def test_device_subset_is_subset(reference_cases):
    full = {c["id"]: c for c in reference_cases}
    device = helpers.load_cases("reference_device.jsonl")
    assert 20 <= len(device) <= 120
    for c in device:
        assert full[c["id"]]["pos"] == c["pos"]
