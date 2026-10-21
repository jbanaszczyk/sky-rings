"""Heliocentric positions of Mercury through Neptune with major perturbations."""
from .timecalc import rev
from .orbit import element, orbit_plane_position, ecliptic_rect, spherical, sind, cosd

MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE = range(7)

# Orbital elements (Schlyter): value at d = 0 and rate per day for
# N (ascending node), i (inclination), w (argument of perihelion),
# a (semi-major axis, AU), e (eccentricity), M (mean anomaly).
ELEMENTS = (
    (48.3313, 3.24587e-5, 7.0047, 5.00e-8, 29.1241, 1.01444e-5,
     0.387098, 0.0, 0.205635, 5.59e-10, 168.6562, 4.0923344368),
    (76.6799, 2.46590e-5, 3.3946, 2.75e-8, 54.8910, 1.38374e-5,
     0.723330, 0.0, 0.006773, -1.302e-9, 48.0052, 1.6021302244),
    (49.5574, 2.11081e-5, 1.8497, -1.78e-8, 286.5016, 2.92961e-5,
     1.523688, 0.0, 0.093405, 2.516e-9, 18.6021, 0.5240207766),
    (100.4542, 2.76854e-5, 1.3030, -1.557e-7, 273.8777, 1.64505e-5,
     5.20256, 0.0, 0.048498, 4.469e-9, 19.8950, 0.0830853001),
    (113.6634, 2.38980e-5, 2.4886, -1.081e-7, 339.3939, 2.97661e-5,
     9.55475, 0.0, 0.055546, -9.499e-9, 316.9670, 0.0334442282),
    (74.0005, 1.3978e-5, 0.7733, 1.9e-8, 96.6612, 3.0565e-5,
     19.18171, -1.55e-8, 0.047318, 7.45e-9, 142.5905, 0.011725806),
    (131.7806, 3.0173e-5, 1.7700, -2.55e-7, 272.8461, -6.027e-6,
     30.05826, 3.313e-8, 0.008606, 2.15e-9, 260.2471, 0.005995147),
)


def mean_anomaly(planet, d, df):
    """Mean anomaly (degrees) of the given planet."""
    el = ELEMENTS[planet]
    return rev(element(el[10], el[11], d, df))


def heliocentric(planet, d, df, Mj, Msat, Mu):
    """Heliocentric ecliptic (lon, lat, r) of a planet, perturbations included.

    Mj, Msat, Mu: mean anomalies of Jupiter, Saturn and Uranus (degrees),
    computed once per timestamp by the caller and shared between planets.
    r is in astronomical units.
    """
    el = ELEMENTS[planet]
    N = element(el[0], el[1], d, df)
    i = element(el[2], el[3], d, df)
    w = element(el[4], el[5], d, df)
    a = element(el[6], el[7], d, df)
    e = element(el[8], el[9], d, df)
    M = rev(element(el[10], el[11], d, df))
    r, v = orbit_plane_position(a, e, M)
    x, y, z = ecliptic_rect(N, i, w, r, v)
    lon, lat, r = spherical(x, y, z)

    if planet == JUPITER:
        lon += (-0.332 * sind(2 * Mj - 5 * Msat - 67.6)
                - 0.056 * sind(2 * Mj - 2 * Msat + 21.0)
                + 0.042 * sind(3 * Mj - 5 * Msat + 21.0)
                - 0.036 * sind(Mj - 2 * Msat)
                + 0.022 * cosd(Mj - Msat)
                + 0.023 * sind(2 * Mj - 3 * Msat + 52.0)
                - 0.016 * sind(Mj - 5 * Msat - 69.0))
    elif planet == SATURN:
        lon += (0.812 * sind(2 * Mj - 5 * Msat - 67.6)
                - 0.229 * cosd(2 * Mj - 4 * Msat - 2.0)
                + 0.119 * sind(Mj - 2 * Msat - 3.0)
                + 0.046 * sind(2 * Mj - 6 * Msat - 69.0)
                + 0.014 * sind(Mj - 3 * Msat + 32.0))
        lat += (-0.020 * cosd(2 * Mj - 4 * Msat - 2.0)
                + 0.018 * sind(2 * Mj - 6 * Msat - 49.0))
    elif planet == URANUS:
        lon += (0.040 * sind(Msat - 2 * Mu + 6.0)
                + 0.035 * sind(Msat - 3 * Mu + 33.0)
                - 0.015 * sind(Mj - Mu + 20.0))

    return rev(lon), lat, r
