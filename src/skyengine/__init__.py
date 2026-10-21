"""skyengine: offline azimuth/altitude of the Sun, Moon and planets.

MicroPython-compatible (standard "math" module only). Based on Paul
Schlyter's algorithms, https://stjarnhimlen.se/comp/ppcomp.html.

Public API
----------
positions(utc, lat, lon) -> tuple of nine (azimuth, altitude) pairs in degrees,
    in the order SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE.
position(body, utc, lat, lon) -> (azimuth, altitude) for a single body index.

utc: (year, month, day, hour, minute, second) in UTC.
lat: observer latitude in degrees, north positive.
lon: observer longitude in degrees, east positive.
Azimuth: 0 north, 90 east, in [0, 360). Altitude: +90 zenith, negative below
the mathematical horizon. No refraction is applied.
"""
from .timecalc import rev, day_number, obliquity, local_sidereal_time
from .orbit import sind, cosd, rect, ecliptic_to_equatorial, horizontal
from . import sun, moon, planets

SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE = range(9)

NAMES = ("Sun", "Moon", "Mercury", "Venus", "Mars",
         "Jupiter", "Saturn", "Uranus", "Neptune")


def positions(utc, lat, lon):
    """Azimuth and altitude of all nine bodies for one UTC instant."""
    d, ut = day_number(utc)
    df = ut / 24.0
    ecl = obliquity(d + df)

    slon, rs, Ms, ws = sun.geocentric(d, df)
    Ls = rev(Ms + ws)
    lst = local_sidereal_time(Ls, ut, lon)
    xs = rs * cosd(slon)
    ys = rs * sind(slon)

    out = []

    # Sun
    xe, ye, ze = ecliptic_to_equatorial(xs, ys, 0.0, ecl)
    out.append(horizontal(xe, ye, ze, lst, lat))

    # Moon: geocentric vector in Earth radii minus observer vector
    mlon, mlat, mr = moon.geocentric(d, df, Ms, Ls)
    x, y, z = rect(mlon, mlat, mr)
    xe, ye, ze = ecliptic_to_equatorial(x, y, z, ecl)
    ox, oy, oz = moon.observer_vector(lat, lst)
    out.append(horizontal(xe - ox, ye - oy, ze - oz, lst, lat))

    # Planets: heliocentric + Sun's geocentric position = geocentric
    Mj = planets.mean_anomaly(planets.JUPITER, d, df)
    Msat = planets.mean_anomaly(planets.SATURN, d, df)
    Mu = planets.mean_anomaly(planets.URANUS, d, df)
    for p in range(7):
        plon, plat, pr = planets.heliocentric(p, d, df, Mj, Msat, Mu)
        x, y, z = rect(plon, plat, pr)
        xe, ye, ze = ecliptic_to_equatorial(x + xs, y + ys, z, ecl)
        out.append(horizontal(xe, ye, ze, lst, lat))

    return tuple(out)


def position(body, utc, lat, lon):
    """Azimuth and altitude of a single body (index constant, e.g. MARS)."""
    return positions(utc, lat, lon)[body]
