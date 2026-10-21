"""Orbital mechanics and coordinate transformations shared by all bodies.

All angles are in degrees unless stated otherwise. Rectangular coordinate
triples are plain tuples (x, y, z).
"""
from math import sin, cos, atan2, sqrt, radians, degrees, pi

from .timecalc import rev

RAD2DEG = 180.0 / pi


def sind(x):
    return sin(radians(x))


def cosd(x):
    return cos(radians(x))


def element(a0, a1, d, df):
    """Evaluate a linear orbital element a0 + a1 * (d + df).

    d is the integer day number and df the fraction of the day. The two
    products are formed separately so single-precision rounding of the
    large integer-day product does not swallow the time-of-day contribution.
    """
    return a0 + a1 * d + a1 * df


def eccentric_anomaly(M, e):
    """Solve Kepler's equation for the eccentric anomaly E (degrees)."""
    E = M + RAD2DEG * e * sind(M) * (1.0 + e * cosd(M))
    for _ in range(10):
        dE = (E - RAD2DEG * e * sind(E) - M) / (1.0 - e * cosd(E))
        E -= dE
        if abs(dE) < 1e-4:
            break
    return E


def orbit_plane_position(a, e, M):
    """Return (r, v): distance and true anomaly for mean anomaly M."""
    E = eccentric_anomaly(M, e)
    x = a * (cosd(E) - e)
    y = a * sqrt(1.0 - e * e) * sind(E)
    return sqrt(x * x + y * y), degrees(atan2(y, x))


def ecliptic_rect(N, i, w, r, v):
    """Rectangular ecliptic coordinates from orbital orientation and (r, v).

    N: longitude of the ascending node, i: inclination,
    w: argument of perihelion, r: distance, v: true anomaly.
    """
    u = v + w
    cu = cosd(u)
    su = sind(u)
    cN = cosd(N)
    sN = sind(N)
    ci = cosd(i)
    return (r * (cN * cu - sN * su * ci),
            r * (sN * cu + cN * su * ci),
            r * su * sind(i))


def spherical(x, y, z):
    """Return (lon, lat, r) in degrees from rectangular coordinates."""
    rxy = sqrt(x * x + y * y)
    return (rev(degrees(atan2(y, x))),
            degrees(atan2(z, rxy)),
            sqrt(rxy * rxy + z * z))


def rect(lon, lat, r):
    """Rectangular coordinates from spherical (lon, lat, r)."""
    cl = cosd(lat)
    return r * cosd(lon) * cl, r * sind(lon) * cl, r * sind(lat)


def ecliptic_to_equatorial(x, y, z, ecl):
    """Rotate rectangular ecliptic coordinates to equatorial (obliquity ecl)."""
    ce = cosd(ecl)
    se = sind(ecl)
    return x, y * ce - z * se, y * se + z * ce


def radec(x, y, z):
    """Right ascension and declination in degrees from an equatorial vector."""
    return rev(degrees(atan2(y, x))), degrees(atan2(z, sqrt(x * x + y * y)))


def horizontal(x, y, z, lst, lat):
    """Shared transform: equatorial rectangular vector -> (azimuth, altitude).

    lst: local sidereal time in degrees, lat: observer latitude in degrees.
    The vector length is irrelevant; only its direction is used.
    Azimuth is 0 at north, 90 at east, normalised to [0, 360).
    Altitude is +90 at the zenith, negative below the mathematical horizon.
    """
    cl = cosd(lst)
    sl = sind(lst)
    # rotate about the celestial pole into the hour-angle frame
    xh = x * cl + y * sl
    yh = x * sl - y * cl
    # tilt the pole up to the zenith
    cphi = cosd(lat)
    sphi = sind(lat)
    xhor = xh * sphi - z * cphi
    zhor = xh * cphi + z * sphi
    az = rev(degrees(atan2(yh, xhor)) + 180.0)
    alt = degrees(atan2(zhor, sqrt(xhor * xhor + yh * yh)))
    return az, alt


def radec_to_horizontal(ra, dec, lst, lat):
    """Convenience wrapper: (RA, Dec) in degrees -> (azimuth, altitude)."""
    x, y, z = rect(ra, dec, 1.0)
    return horizontal(x, y, z, lst, lat)
