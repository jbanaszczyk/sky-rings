"""Geocentric position of the Sun from Earth's orbital elements."""
from .timecalc import rev
from .orbit import element, orbit_plane_position


def geocentric(d, df):
    """Return (lon, r, M, w) for day number d and day fraction df.

    lon: geocentric ecliptic longitude of the Sun (degrees), latitude is 0.
    r:   distance in astronomical units.
    M:   mean anomaly (degrees), w: argument of perihelion (degrees).
    M + w is the Sun's mean longitude, needed for sidereal time and for the
    lunar perturbations.
    """
    w = element(282.9404, 4.70935e-5, d, df)
    e = element(0.016709, -1.151e-9, d, df)
    M = rev(element(356.0470, 0.9856002585, d, df))
    r, v = orbit_plane_position(1.0, e, M)
    return rev(v + w), r, M, w
