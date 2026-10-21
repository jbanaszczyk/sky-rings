"""Target-side test runner for skyengine.

Runs under MicroPython (RP2040 or the Unix port) and also under CPython.
It needs no pytest and no third-party modules: it checks Schlyter's worked
example and compares the engine with the Astronomy Engine reference fixture
``reference_device.jsonl`` (generated on the PC) using angular separation.

Usage:
    micropython run_tests.py [fixture_path]
    python3    run_tests.py [fixture_path]   (with src/ on sys.path)

Exit status is 1 if any check fails. Prints the maximum error per body so
the single-precision behaviour of the target can be documented.
"""
import sys
import math

try:
    import json
except ImportError:  # MicroPython without json would be unusual
    import ujson as json

import skyengine

TOLERANCE = (1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
DEFAULT_FIXTURES = ("reference_device.jsonl",
                    "tests/fixtures/reference_device.jsonl",
                    "../tests/fixtures/reference_device.jsonl")

failures = []


def check(name, ok, detail=""):
    if not ok:
        failures.append(name + (": " + detail if detail else ""))
        print("FAIL", name, detail)


def separation(az1, alt1, az2, alt2):
    a1 = math.radians(az1)
    h1 = math.radians(alt1)
    a2 = math.radians(az2)
    h2 = math.radians(alt2)
    c = math.sin(h1) * math.sin(h2) + math.cos(h1) * math.cos(h2) * math.cos(a1 - a2)
    if c > 1.0:
        c = 1.0
    if c < -1.0:
        c = -1.0
    return math.degrees(math.acos(c))


def float_info():
    # 32-bit floats cannot distinguish 1 + 1e-8 from 1; report which build runs.
    bits = 64 if (1.0 + 1e-10) != 1.0 else 32
    print("platform:", sys.platform, "implementation:", sys.implementation.name,
          "float bits:", bits)
    return bits


def test_schlyter_example():
    az, alt = skyengine.position(skyengine.SUN, (1990, 4, 19, 0, 0, 0), 60.0, 15.0)
    err = separation(az, alt, 15.6767, -17.9570)
    print("Schlyter Sun example: az %.4f alt %.4f (err %.5f deg)" % (az, alt, err))
    check("schlyter_sun_example", err < 0.01, "%.5f" % err)
    d, ut = skyengine.timecalc.day_number((1990, 4, 19, 0, 0, 0))
    check("schlyter_day_number", d == -3543 and ut == 0.0, "d=%d ut=%r" % (d, ut))


def test_conventions():
    res = skyengine.positions((2030, 7, 1, 12, 0, 0), 45.0, 10.0)
    check("nine_bodies", len(res) == 9)
    for i, (az, alt) in enumerate(res):
        check("azimuth_range_" + skyengine.NAMES[i], 0.0 <= az < 360.0, "%r" % az)
        check("altitude_range_" + skyengine.NAMES[i], -90.0 <= alt <= 90.0, "%r" % alt)
    a = skyengine.positions((2040, 10, 10, 10, 10, 10), 52.23, 21.01)
    b = skyengine.positions((2040, 10, 10, 10, 10, 11), 52.23, 21.01)
    for i in range(9):
        s = separation(a[i][0], a[i][1], b[i][0], b[i][1])
        check("one_second_step_" + skyengine.NAMES[i], s < 0.01, "%.4f" % s)
    check("deterministic", skyengine.positions((2033, 3, 3, 3, 3, 3), -12.5, 130.25)
          == skyengine.positions((2033, 3, 3, 3, 3, 3), -12.5, 130.25))


def open_fixture(path):
    if path:
        return open(path)
    for p in DEFAULT_FIXTURES:
        try:
            return open(p)
        except OSError:
            pass
    return None


def test_reference(path):
    f = open_fixture(path)
    if f is None:
        print("fixture reference_device.jsonl not found; skipping reference comparison")
        failures.append("fixture_missing")
        return
    worst = [0.0] * 9
    n = 0
    for line in f:
        line = line.strip()
        if not line:
            continue
        case = json.loads(line)
        if "meta" in case:
            print("fixture:", case["meta"].get("generator"), case["meta"].get("version"),
                  "cases:", case["meta"].get("cases"))
            continue
        pos = skyengine.positions(tuple(case["utc"]), case["lat"], case["lon"])
        for i in range(9):
            err = separation(pos[i][0], pos[i][1], case["pos"][i][0], case["pos"][i][1])
            if err > worst[i]:
                worst[i] = err
            if err > TOLERANCE[i]:
                check("reference_" + case["id"] + "_" + skyengine.NAMES[i], False,
                      "%.3f deg" % err)
        n += 1
        case = None
        pos = None
    f.close()
    print("reference cases:", n)
    print("%-8s %8s %5s" % ("body", "max_err", "tol"))
    for i in range(9):
        print("%-8s %8.4f %5.1f" % (skyengine.NAMES[i], worst[i], TOLERANCE[i]))
    check("reference_cases_present", n > 0)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    float_info()
    test_schlyter_example()
    test_conventions()
    test_reference(path)
    if failures:
        print("FAILED: %d check(s)" % len(failures))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
