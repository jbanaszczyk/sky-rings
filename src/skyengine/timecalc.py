"""Time calculations: day number, time of day, angle normalisation, sidereal time.

All angles are in degrees. The day number convention follows Paul Schlyter
(https://stjarnhimlen.se/comp/ppcomp.html): d = 0 at 1999-12-31 00:00 UT,
so d = 1 on 2000-01-01 00:00 UT.

Numerical note for 32-bit floats: the integer day number and the time of day
are kept apart. The day number is an int, the time of day is a float in hours.
A combined floating-point day count (or a full Julian Date) would lose
minutes of time-of-day resolution in single precision.
"""


def rev(x):
    """Reduce an angle in degrees to the range [0, 360)."""
    x = x % 360.0
    if x >= 360.0:  # guard against rounding to exactly 360.0
        x = 0.0
    return x


def day_number(utc):
    """Convert a UTC tuple to (d, ut).

    utc: (year, month, day, hour, minute, second); second may be fractional.
    Returns the integer day number d (Schlyter convention, see module doc)
    and the time of day ut in hours as a float.

    The calendar formula is valid from 1900-03-01 to 2100-02-28. Outside the
    2020-2050 target range the orbital elements degrade silently.
    """
    y = utc[0]
    m = utc[1]
    d = 367 * y - 7 * (y + (m + 9) // 12) // 4 + 275 * m // 9 + utc[2] - 730530
    ut = utc[3] + utc[4] / 60.0 + utc[5] / 3600.0
    return d, ut


def obliquity(d):
    """Obliquity of the ecliptic in degrees for day number d (may be fractional)."""
    return 23.4393 - 3.563e-7 * d


def local_sidereal_time(sun_mean_lon, ut, lon):
    """Local sidereal time in degrees.

    sun_mean_lon: the Sun's mean longitude Ls = Ms + ws (degrees).
    ut: time of day in hours.
    lon: observer longitude in degrees, east positive.

    GMST0 = Ls + 180 deg is the Greenwich sidereal time at 0h UT; the time of
    day is added separately so its full precision is preserved.
    """
    return rev(sun_mean_lon + 180.0 + ut * 15.0 + lon)
