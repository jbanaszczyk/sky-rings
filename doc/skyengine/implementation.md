# skyengine: implementation notes

Phase 1 deliverable for the RP2040 Sky Observatory (see `phase_1.md`).
`skyengine` returns the azimuth and altitude of the Sun, Moon, Mercury,
Venus, Mars, Jupiter, Saturn, Uranus and Neptune for an observer at a given
latitude, longitude and UTC instant. It runs offline, on MicroPython, with
the `math` module as its only dependency.

## API

```python
import skyengine

utc = (2030, 7, 1, 21, 30, 0)  # year, month, day, hour, minute, second (UTC)
lat, lon = 52.23, 21.01  # degrees, north and east positive

pairs = skyengine.positions(utc, lat, lon)
az, alt = pairs[skyengine.MARS]

az, alt = skyengine.position(skyengine.MOON, utc, lat, lon)
```

`positions()` returns a tuple of nine `(azimuth, altitude)` pairs in degrees,
in the fixed order `SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS,
NEPTUNE` (index constants 0 to 8, names in `skyengine.NAMES`). Azimuth is 0 at
north, 90 at east, in `[0, 360)`. Altitude is +90 at the zenith and negative
below the mathematical horizon. Seconds may be fractional. No input
validation is performed.

## Modules

| Module        | Responsibility                                                                                                                        |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `timecalc.py` | day number, time of day, `rev()` angle normalisation, obliquity, local sidereal time                                                  |
| `orbit.py`    | element evaluation, Kepler's equation, orbit-plane to ecliptic, ecliptic to equatorial, the shared equatorial-to-horizontal transform |
| `sun.py`      | Sun's geocentric ecliptic longitude and distance, mean anomaly and perihelion (reused by the Moon and sidereal time)                  |
| `planets.py`  | orbital element table, heliocentric positions, perturbations of Jupiter, Saturn and Uranus                                            |
| `moon.py`     | lunar elements, 12 + 5 + 2 perturbation terms, observer vector for the parallax correction                                            |
| `__init__.py` | `positions()`, `position()`, body constants                                                                                           |

All inputs and outputs of the internal functions are degrees, AU (planets,
Sun) or Earth equatorial radii (Moon). Rectangular coordinates are plain
tuples.

## Algorithm

Paul Schlyter's method (https://stjarnhimlen.se/comp/ppcomp.html) is
implemented directly:

1. Day number `d` (integer, 0 at 1999-12-31 00:00 UT) and time of day `ut` in hours.
2. Linear orbital elements `a0 + a1 * d`, mean anomaly reduced to `[0, 360)`.
3. Kepler's equation: the mean anomaly is first reduced to `[-180, 180)` (keeps
   `E` small in single precision), then a first approximation is followed by
   Newton iteration until the step is below 0.001 degrees (at most 10
   iterations). The result is shifted back to the caller's 360-degree turn.
4. Orbit-plane position, rotation by `w`, `i`, `N` into ecliptic rectangular
   coordinates.
5. Sun: geocentric directly. Planets: heliocentric spherical coordinates,
   Schlyter's perturbation terms added to longitude (Jupiter, Saturn,
   Uranus) and latitude (Saturn), then the Sun's geocentric vector is added.
   Moon: geocentric spherical coordinates with 12 longitude, 5 latitude and
   2 distance perturbation terms.
6. Rotation by the obliquity into equatorial coordinates (equinox of date).
7. Moon only: the observer's geocentric position vector (Earth flattening
   included, Schlyter's `gclat` and `rho`) is subtracted from the Moon's
   equatorial vector in Earth radii. This is the full topocentric parallax
   correction in both azimuth and altitude and has no singular cases, unlike
   the first-order RA/Dec formulas.
8. Shared transform `orbit.horizontal()`: rotate the equatorial vector by the
   local sidereal time into the hour-angle frame, tilt by the latitude,
   `atan2` to azimuth and altitude.

Local sidereal time is `Ls + 180 + 15 * ut + lon` where `Ls` is the Sun's
mean longitude. The time of day enters this expression separately from the
day-number term, which is what preserves time-of-day precision in single
precision.

### Simplifications and their effect

| Simplification                                                 | Effect on direction                                                                                     |
|----------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| UTC treated as UT1 (and as the dynamical time of the elements) | below 0.001 deg for all bodies through 2050                                                             |
| no nutation                                                    | up to 0.005 deg                                                                                         |
| no aberration, no light-time correction                        | up to 0.006 deg                                                                                         |
| no atmospheric refraction                                      | up to 0.6 deg at the horizon, zero above about 10 deg altitude; intentionally omitted per specification |
| no topocentric correction for Sun and planets                  | below 0.01 deg (Venus at inferior conjunction worst)                                                    |
| Keplerian orbits with Schlyter's major perturbations only      | a few hundredths of a degree for planets, about 0.1 deg for the Moon                                    |

## Measured accuracy

Angular separation between `skyengine` and Astronomy Engine 2.1.19 (topocentric, equinox of date, no refraction) over
1062 cases: 11 years from
2020 to 2050, four dates per year, four times of day, ten observer sites from
78 N to 78 S including the equator, plus equinoxes, solstices, leap days,
year and month boundaries, and constructed near-zenith cases. Measured under
CPython (64-bit floats):

| Body    | max error (deg) | mean error (deg) | tolerance (deg) |
|---------|-----------------|------------------|-----------------|
| Sun     | 0.012           | 0.005            | 1.0             |
| Moon    | 0.105           | 0.033            | 2.0             |
| Mercury | 0.021           | 0.006            | 1.0             |
| Venus   | 0.023           | 0.005            | 1.0             |
| Mars    | 0.029           | 0.007            | 1.0             |
| Jupiter | 0.026           | 0.008            | 1.0             |
| Saturn  | 0.052           | 0.016            | 1.0             |
| Uranus  | 0.021           | 0.012            | 1.0             |
| Neptune | 0.014           | 0.007            | 1.0             |

The Moon's geocentric model alone agrees with the reference to 0.10 deg; the
remaining Moon error is the model itself, not the parallax correction. The
display resolution is about 6 deg per LED, so the engine's error is far
below one LED step.

The 32-bit-float result on the RP2040 has not been measured yet; this is the
one open acceptance item (phase_1.md, section 9.5). See "Testing on the
device" below. Expected additional error from single
precision is about 0.01 deg for the Moon (rate × day-number products of
roughly 240 000 degrees have a float32 resolution of 0.016 deg) and less for
other bodies.

## Supported time range

- Orbital elements: designed for 2020 to 2050; Schlyter's linear elements
  stay within about 0.1 deg for the planets over 1900 to 2100 (Uranus and
  Neptune worst). Outside this the error grows gradually. Nothing is
  validated or raised.
- Calendar formula: exact from 1900-03-01 to 2100-02-28. Outside that range
  the day number is wrong by whole days.
- Moon: the 2-arcminute Schlyter model is valid for centuries; the day-number
  product dominates the float32 error far outside 2000.

## Numerical notes for MicroPython (32-bit floats)

- The day number is an `int`; the time of day is a separate float in hours.
  A combined float day count would have a resolution of about 3 minutes at
  d = 18 000, which is 0.7 deg of Earth rotation.
- `orbit.element()` evaluates `a0 + a1 * d + a1 * df` as separate products so
  the day-fraction term is not rounded away.
- Angles are reduced with `rev()` immediately after evaluation.
- Float literals in the element table lose digits beyond 7 significant
  figures in float32; the resulting rate error is below 0.01 deg by 2050.
- `rev()` uses the float `%` operator, which MicroPython implements for
  floats, and guards against a result of exactly 360.0.
- No `datetime`, `dataclasses`, f-strings, type hints or other features
  beyond MicroPython's Python 3.4-level core are used in the package.

## Running the PC tests

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'          # pytest and astronomy-engine
pytest                            # about 1 second
```

`pytest` prints a per-body error table at the end of the run. Test files:

| File                              | Covers                                                                                                                                                            |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `tests/helpers.py`                | shared tolerances and error summary; test-only `radec()` and `radec_to_horizontal()` helpers                                                                         |
| `tests/test_time.py`              | day number against `datetime` for every day 2019-2051, leap years, rollover, `rev()`, GMST against Astronomy Engine, sidereal progression, longitude sign         |
| `tests/test_coords.py`            | horizontal transform conventions (zenith, meridian, east/west, poles, below horizon), azimuth normalisation, API shape, hemisphere and midnight-sun behaviour     |
| `tests/test_schlyter_examples.py` | intermediate values from Schlyter's 1990-04-19 worked example for the Sun, Moon, all planet elements and heliocentric positions                                   |
| `tests/test_reference.py`         | all nine bodies against the fixtures within tolerance; fixture coverage; device subset consistency                                                                |
| `tests/test_moon.py`              | geocentric model, parallax magnitude and direction, topocentric vs geocentric reference, near-horizon cases, lunar phases covered                                 |
| `tests/test_continuity.py`        | minute-step continuity over a day and across year/leap boundaries, monotonic Sun azimuth, culmination time, eastward Moon/Sun motion, determinism, zenith passage |

Regenerate the fixtures after changing the case list in
`tests/tools/gen_fixtures.py`:

```sh
python tests/tools/gen_fixtures.py
```

Optional one-off cross-check of the fixtures against a second, unrelated
reference (downloads the 17 MB `de421.bsp` ephemeris into the current
directory):

```sh
pip install skyfield
python tests/tools/crosscheck_skyfield.py
```

This was run once on 2026-10-20 with Skyfield 1.55 and de421: the two
references agree to within 0.01 deg on every body over all 1062 cases, so
the stored fixtures do not depend on a single library being correct.

## Testing on the device

`tests_micropython/run_tests.py` needs only `skyengine`, `json` and `math`.
It checks Schlyter's example, output conventions and the 102-case device
fixture, prints the interpreter's float width and the maximum error per body,
and exits with status 1 on failure. Instructions for the RP2040 via
`mpremote` and for a 32-bit-float build of the MicroPython Unix port are in
`tests_micropython/README.md`. The same runner also executes under CPython:

```sh
PYTHONPATH=src python tests_micropython/run_tests.py tests/fixtures/reference_device.jsonl
```

## Deploying

Copy `src/skyengine/` to the device file system (for example
`mpremote cp -r src/skyengine :`) and `import skyengine`. The package is
about 15 KB of source; freezing it into the firmware or compiling to `.mpy`
with `mpy-cross` reduces RAM use but is not required.
