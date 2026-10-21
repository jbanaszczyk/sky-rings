RP2040 Sky Observatory — Astronomy Calculation Engine

1. Project Overview

Build a small astronomical visualization device using an RP2040 microcontroller running MicroPython.

The physical device consists of five concentric rings of individually addressable LEDs, approximately 30 cm in diameter.
The rings represent the visible hemisphere of the sky, with the observer positioned at the center.

The device knows:

- Its fixed geographical location (latitude and longitude).
- Current UTC time, initially synchronized using NTP.
- The orientation of the physical display.

After time synchronization, all astronomical calculations must run locally and offline, without external services, APIs,
or downloaded ephemeris data.

Current development scope

Implement only the astronomical calculation engine and its tests.

LED mapping, rendering, colors, brightness, animation, and all hardware control are explicitly out of scope.

The engine should calculate the positions of the Sun, Moon, and planets as seen by an observer at a specified location
and UTC time.

---

2. Target Platform and Constraints

Production environment

- Hardware: Raspberry Pi RP2040.
- Runtime: MicroPython.
- Language: Python compatible with MicroPython.
- Dependencies: standard MicroPython modules only.
- Mathematical library: "math".
- No NumPy, SciPy, Astropy, Skyfield, or other external astronomy libraries in production code.
- No network access required during astronomical calculations.
- No reliance on CPython-specific modules such as "datetime", "dataclasses", or "zoneinfo".

The production implementation should be relatively compact, understandable, and easy to maintain.

Floating-point precision

The target MicroPython firmware may use 32-bit floating-point arithmetic.

This is an important implementation constraint.

In particular:

- Avoid calculations that require high precision from large absolute floating-point values.
- Do not represent full Julian Dates as single-precision floats when performing time-sensitive calculations.
- Prefer integer calendar/day calculations and separate fractional-day or time-of-day values.
- Normalize angles periodically to avoid unnecessarily large intermediate values.
- Ensure that sidereal-time calculations preserve sufficient time-of-day precision.
- Do not assume that satisfactory results under CPython's "float64" guarantee satisfactory results on RP2040.

A custom MicroPython firmware with "float64" must not be a prerequisite.

PC development and testing

Tests execute under regular CPython.

Testing code may use NumPy, pytest, and external astronomy packages, including Astropy, Skyfield, or Astronomy Engine.

These dependencies must remain completely isolated from the production implementation.

---

3. Astronomical Objects

Calculate positions for nine celestial bodies:

1. Sun
2. Moon
3. Mercury
4. Venus
5. Mars
6. Jupiter
7. Saturn
8. Uranus
9. Neptune

Earth is the observer's planet and is not represented as a separate sky object.

Pluto, stars, satellites, comets, and asteroids are not required.

---

4. Required Input and Output

Input

The calculation engine receives:

- UTC date and time.
- Observer latitude in degrees.
- Observer longitude in degrees.

Use the following conventions:

- Latitude: positive north, negative south.
- Longitude: positive east, negative west.
- UTC: no local timezone or daylight-saving conversions.

Prefer a simple representation of UTC, such as:

"(year, month, day, hour, minute, second)"

This avoids dependence on platform-specific timestamp epochs and CPython date/time classes.

The astronomical module must not perform NTP synchronization or access the hardware RTC itself.

Output

For each celestial body, return:

Azimuth, in degrees:

- 0° — North
- 90° — East
- 180° — South
- 270° — West
- Normalized to "[0, 360)".

Altitude, in degrees:

- +90° — Zenith
- 0° — Mathematical horizon
- −90° — Nadir

Negative altitudes must be returned normally. Visibility filtering belongs to a future visualization layer.

API

The primary call computes all nine bodies at once, reusing the common intermediate results (day number, Sun position,
sidereal time, obliquity):

"positions (utc, latitude, longitude) -> tuple of nine (azimuth, altitude) pairs"

The tuple has a fixed order: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune. The module exposes
index constants with these names and a matching "NAMES" tuple. A fixed-order tuple avoids dictionary allocations on
the device and gives the display layer a stable contract.

A convenience wrapper returns a single body:

"position (body, utc, latitude, longitude) -> (azimuth, altitude)"

Input validation is not required. Dates outside the supported range are accepted and degrade silently (see section 6).

The API must remain small, predictable, and independent of device hardware.

---

5. Astronomical Algorithm

Primary reference

Use Paul Schlyter's astronomical algorithms as the initial implementation reference:

"How to compute planetary positions — Paul Schlyter" (https://stjarnhimlen.se/comp/ppcomp.html)

These algorithms are suitable for low-resource environments and provide substantially better theoretical accuracy than
this project requires.

Implement the mathematics directly in MicroPython-compatible Python.

The implementation should be derived from documented formulas rather than relying on an external runtime library.

5.1 Time calculations

Convert UTC date/time into the astronomical time representation required by the orbital algorithms.

Implement:

- Gregorian calendar calculations.
- Days elapsed from the algorithm's reference epoch.
- Fractional time of day.
- Angle normalization.
- Local sidereal time (LST).

UTC may be treated as UT1 for this project.

Pay particular attention to numeric precision in sidereal-time calculations because Earth rotation directly affects the
computed azimuth and altitude of every object.

5.2 Sun

Calculate the Sun's approximate geocentric position using Earth's orbital elements.

Required stages:

1. Determine orbital elements for the requested date.
2. Calculate mean anomaly.
3. Solve the simplified Kepler equation.
4. Determine true anomaly and orbital position.
5. Calculate geocentric ecliptic coordinates.
6. Convert to equatorial coordinates (right ascension and declination).
7. Convert to the observer's horizontal coordinate system.

High-precision solar ephemerides are unnecessary.

5.3 Planets

For Mercury through Neptune:

1. Calculate the orbital elements at the requested UTC date.
2. Determine heliocentric coordinates.
3. Calculate Earth's heliocentric position.
4. Convert planetary positions from heliocentric to geocentric coordinates.
5. Convert ecliptic coordinates to right ascension and declination.
6. Apply local sidereal time and observer latitude.
7. Return azimuth and altitude.

The calculation must correctly handle both inner and outer planets.

Use the orbital-element equations from the reference algorithm.

Include the significant planetary perturbation corrections documented by Schlyter where appropriate, particularly for
Jupiter, Saturn, and Uranus.

5.4 Moon

The Moon requires a separate calculation model.

Implement:

1. Approximate lunar orbital elements.
2. Orbital position and geocentric ecliptic coordinates.
3. Significant lunar perturbation corrections.
4. Conversion into equatorial coordinates.
5. Conversion into horizontal coordinates.
6. Topocentric parallax correction.

The topocentric correction matters because the Moon's apparent position from the Earth's surface can differ from its
geocentric position by approximately one degree.

A simplified topocentric correction is sufficient.

Lunar phases, illuminated fraction, apparent size, and brightness are not required at this stage.

5.5 Horizontal coordinate conversion

Implement a shared transformation from:

"(right_ascension, declination, UTC, observer_location)"

to:

"(azimuth, altitude)"

The transformation must correctly account for:

- Observer latitude.
- Observer longitude.
- Earth rotation and local sidereal time.
- Hour angle.
- The conventional north-zero, east-positive azimuth system.

Prefer sharing this code between all celestial objects instead of duplicating coordinate transformations.

5.6 Simplifications

The following are acceptable:

- Approximate Keplerian orbits.
- Simplified planetary perturbations.
- Ignoring atmospheric refraction.
- Ignoring nutation and aberration.
- Ignoring relativistic corrections.
- Ignoring small topocentric corrections for the Sun and planets.
- Treating UTC as UT1.

Document any significant simplification that may affect accuracy.

No need to implement astronomical-grade ephemerides.

---

6. Accuracy Requirements

This is a decorative astronomical visualization, not a precision astronomical instrument.

The physical display has very low spatial resolution:

- Five concentric LED rings.
- Approximately 12 LEDs on the innermost ring.
- Approximately 60 LEDs on the outermost ring.
- Outer-ring angular spacing: approximately 6°.
- Inner-ring angular spacing: substantially larger.

The device therefore cannot show positions better than about 6°. The targets below are deliberately tighter than the
display resolution so that calculation error never contributes a visible LED step.

The device will not be used for telescope alignment, astrophotography calibration, navigation, or scientific
measurements.

Accuracy targets

Use these practical targets:

Object| Target angular error
Sun| ≤ 1°
Moon| ≤ 2°
Planets| ≤ 1°

These are engineering acceptance targets, not a requirement for arcminute-level accuracy.

Evaluate accuracy as angular separation between the calculated and reference directions on the celestial sphere, rather
than using only independent azimuth and altitude differences.

This avoids misleading results near the zenith, where azimuth becomes poorly defined.

A more accurate implementation is welcome if it does not introduce substantial complexity.

Do not implement sophisticated corrections solely to improve results from, for example, 0.1° to 0.01°.

The important property is that the positions and their motion correspond approximately to the real sky.

Time range

Prioritize correctness for dates from 2020 through 2050.

A wider supported period is welcome, but not required.

Outside the supported range the engine degrades silently: it must not raise or validate the date, and the accuracy
targets no longer apply.

Any limitations of the chosen orbital-element model must be documented.

---

7. Architecture

Keep the implementation independent of hardware and display code.

Suggested logical components:

Component| Responsibility
Time calculations| Astronomical day count, UTC conversion, sidereal time
Orbital calculations| Kepler equation, orbital elements, coordinate transformations
Solar calculations| Sun's geocentric position
Planetary calculations| Heliocentric and geocentric planet positions
Lunar calculations| Moon orbit, perturbations, topocentric correction
Horizontal coordinates| RA/Dec to azimuth/altitude
Public API| Unified interface for all supported bodies

Multiple Python files are preferred over one large module; they are simpler to maintain. One module per logical
component is a reasonable split.

Directory layout

Use a standard Python layout and keep the three kinds of code apart:

- "src/skyengine/" — production code, MicroPython-compatible, copied to the device as-is.
- "tests/" — CPython test suite (pytest), reference fixtures and the fixture generator.
- "tests_micropython/" — a pytest-free runner executed on the target device or the MicroPython Unix port.
- "doc/" — specification and implementation notes.

Avoid unnecessary allocations and repeated calculations when processing all celestial bodies for the same timestamp.

The calculation engine does not need asynchronous processing, background threads, or event-loop integration.

---

8. Performance

Positions of all objects are returned in one API call; the caller retrieves them in a loop.

Calculations will be executed (approx.) each minute, time required for calculations is not critical.

Avoid defining many large data structures in Python. Code size is limited (RP2040 + MicroPython) and the engine is
part of a larger program. Of course some structures have to be defined.

---

9. Testing Strategy

Tests are an important part of this task.

The implementation must be verified against independent astronomical reference calculations rather than relying
exclusively on internal consistency.

9.1 Reference calculations

Use an established astronomy library under CPython to generate reference positions.

Primary reference: "Astronomy Engine" (https://github.com/cosinekitty/astronomy). It is pure Python, needs no
ephemeris download, and uses an algorithm independent of Schlyter's.

Secondary cross-check: "Skyfield" (https://rhodesmill.org/skyfield/) with a JPL ephemeris, run once by hand to confirm
the stored fixtures. This step is optional and not part of the regular test suite because it downloads ephemeris data.

Testing tools may use NumPy internally.

Reference computations should use:

- The same geographical coordinates.
- The same UTC timestamps.
- Topocentric positions, equinox of date.
- Atmospheric refraction disabled.

Differences between geometric and apparent positions (aberration, light time, nutation) are at most a few hundredths of
a degree and are irrelevant at the tolerances above. Either definition is acceptable; the choice must be recorded in the
fixture metadata.

Use an independent algorithm to avoid reproducing the same implementation mistakes in both the production and reference
calculations.

Reference values are generated ahead of time and stored as fixtures, allowing the regular test suite to operate offline
without downloading ephemeris files. Fixtures use a plain line-oriented JSON format so that both the CPython suite and
the MicroPython runner can read them.

9.2 Numerical reference tests

Provide representative reference cases for all nine celestial objects.

Cover:

- Multiple UTC dates.
- Different times of day.
- Different observer locations.
- Positive and negative latitudes.
- Eastern and western longitudes.
- Objects above and below the horizon.
- Different planetary orbital configurations.

Include cases where objects appear near the horizon and near the zenith.

The reference tests must verify numerical accuracy against the stated tolerances.

9.3 Time and coordinate tests

Test at least:

- UTC midnight and date rollover.
- Month and year boundaries.
- Leap years.
- Equinoxes and solstices.
- Correct handling of longitude signs.
- Azimuth normalization around 0°/360°.
- Altitudes below the horizon.
- Observer locations near the equator.
- High-latitude observers.
- Correct sidereal-time progression as UTC advances.

Include deterministic tests for basic coordinate conventions and transformations.

9.4 Moon-specific tests

Verify lunar results for:

- Several dates spanning different lunar orbital configurations.
- Different geographical observer locations.
- Positions near the horizon.
- The influence of topocentric parallax.

Compare the corrected lunar position against a topocentric reference, not only a geocentric reference.

9.5 Numerical stability

The requirement is that "float32" results stay within tolerance, not that the difference between "float64" and
"float32" is measured.

Verify this by running the real engine, unchanged, under a 32-bit-float MicroPython against the same reference
fixtures:

- On the RP2040 itself, when hardware is available.
- On the MicroPython Unix port built with "MICROPY_FLOAT_IMPL_FLOAT", which reproduces the RP2040 float behavior on a
  PC without hardware.

The target-side runner must not depend on pytest or third-party modules. It reports the maximum angular error per body
so the single-precision behavior can be documented.

Do not simulate "float32" with NumPy in the CPython suite: it would require writing the engine generically over a
number type and still would not prove MicroPython behavior.

The engine should be robust to single precision by construction. Particular attention should be given to:

- Julian day / epoch calculations: keep the integer day number and the time of day as separate values.
- Sidereal-time calculations: add the time of day to the sidereal angle separately from the day-number term.
- Large accumulated orbital angles: evaluate rate × integer-day and rate × day-fraction as separate products, then
  normalize.
- Trigonometric function inputs and angle normalization.
- Date-dependent loss of precision.

Results must remain within the specified angular accuracy targets on the target platform.

9.6 Continuity and regression tests

Test positions at multiple timestamps within a single day and across consecutive days.

Verify that:

- Positions change in the expected direction over time.
- Ordinary time progression does not introduce artificial jumps.
- Angle wrapping does not cause discontinuities in the physical direction.
- Results remain deterministic.
- Small changes in input time do not produce implausibly large changes in celestial positions.

Remember that azimuth wrapping and zenith singularities can produce large numerical coordinate changes without
corresponding physical discontinuities.

Use direction vectors or spherical angular separation where appropriate.

9.7 Reference algorithm examples

Also use the numerical worked examples provided by Paul Schlyter:

"Computing planetary positions — reference and worked examples" (https://stjarnhimlen.se/comp/ppcomp.html)

These are useful for validating intermediate results such as orbital elements, ecliptic coordinates, and equatorial
coordinates.

They supplement, but do not replace, independent reference tests.

---

10. Explicitly Out of Scope

Do not implement any of the following in this phase:

- LED ring mapping.
- Altitude-to-ring conversion.
- Azimuth-to-LED conversion.
- Physical display orientation or calibration.
- LED drivers or animation.
- Color configurations.
- Object priorities or overlap resolution.
- Visibility filtering based on the horizon.
- Moon phase or brightness visualization.
- Sky illumination or background colors.
- NTP client.
- Wi-Fi management.
- RTC management.
- Persistent configuration.
- Power management.
- Physical hardware integration.

The display projection has not yet been decided.

Do not make assumptions about how altitude will be mapped onto physical rings.

The astronomical engine should return continuous angular coordinates, leaving all quantization and rendering decisions
to a future layer.

---

11. Expected Deliverables

1. MicroPython-compatible astronomical calculation package implementing the nine supported celestial objects.
2. Stable public API accepting UTC and observer coordinates and returning azimuth/altitude.
3. Automated PC test suite with independent astronomical reference data.
4. Numerical accuracy verification against the specified tolerances.
5. Target-side test runner that verifies the same tolerances under 32-bit-float MicroPython.
6. Short documentation describing the implementation, supported time range, dependencies, numerical limitations, and how
   to execute the tests.

Acceptance Criteria

The task is complete when:

- All nine celestial objects are supported.
- Calculations work offline using only UTC and geographical coordinates.
- Production code runs under standard RP2040 MicroPython without external numerical libraries.
- Output coordinates follow the specified conventions.
- Accuracy targets are verified against independent reference results.
- The test suite runs under CPython.
- No rendering or hardware dependencies have been introduced.

Primary engineering priority: a correct, compact, portable astronomical calculation engine that provides sufficiently
accurate sky positions for a coarse LED-based visual representation, without unnecessary precision or computational
complexity.
