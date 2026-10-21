"""Geocentric position of the Moon with perturbations, plus the observer
vector used for the topocentric (parallax) correction.
"""
from .timecalc import rev
from .orbit import element, orbit_plane_position, ecliptic_rect, spherical, sind, cosd


def geocentric(d, df, Ms, Ls):
    """Geocentric ecliptic (lon, lat, r) of the Moon, r in Earth radii.

    Ms: the Sun's mean anomaly, Ls: the Sun's mean longitude (degrees).
    Includes the 12 longitude, 5 latitude and 2 distance perturbation terms
    with amplitudes above 0.01 deg / 0.1 Earth radii (Schlyter).
    """
    N = rev(element(125.1228, -0.0529538083, d, df))
    i = 5.1454
    w = rev(element(318.0634, 0.1643573223, d, df))
    a = 60.2666
    e = 0.054900
    M = rev(element(115.3654, 13.0649929509, d, df))
    r, v = orbit_plane_position(a, e, M)
    x, y, z = ecliptic_rect(N, i, w, r, v)
    lon, lat, r = spherical(x, y, z)

    Lm = rev(N + w + M)   # mean longitude
    D = Lm - Ls           # mean elongation
    F = Lm - N            # argument of latitude

    lon += (-1.274 * sind(M - 2 * D)          # evection
            + 0.658 * sind(2 * D)             # variation
            - 0.186 * sind(Ms)                # yearly equation
            - 0.059 * sind(2 * M - 2 * D)
            - 0.057 * sind(M - 2 * D + Ms)
            + 0.053 * sind(M + 2 * D)
            + 0.046 * sind(2 * D - Ms)
            + 0.041 * sind(M - Ms)
            - 0.035 * sind(D)                 # parallactic equation
            - 0.031 * sind(M + Ms)
            - 0.015 * sind(2 * F - 2 * D)
            + 0.011 * sind(M - 4 * D))
    lat += (-0.173 * sind(F - 2 * D)
            - 0.055 * sind(M - F - 2 * D)
            - 0.046 * sind(M + F - 2 * D)
            + 0.033 * sind(F + 2 * D)
            + 0.017 * sind(2 * M + F))
    r += -0.58 * cosd(M - 2 * D) - 0.46 * cosd(2 * D)
    return rev(lon), lat, r


def observer_vector(lat, lst):
    """Observer position from the Earth's centre in equatorial rectangular
    coordinates, in Earth equatorial radii.

    Accounts for the Earth's flattening (geocentric latitude and radius).
    Subtracting this vector from the Moon's geocentric equatorial vector
    (also in Earth radii) gives the topocentric direction; this is the full
    parallax correction in both azimuth and altitude and has no singular
    cases.
    """
    gclat = lat - 0.1924 * sind(2 * lat)
    rho = 0.99833 + 0.00167 * cosd(2 * lat)
    c = rho * cosd(gclat)
    return c * cosd(lst), c * sind(lst), rho * sind(gclat)
