# astro: RP2040 Sky Observatory, astronomical calculation engine

`skyengine` computes the azimuth and altitude of the Sun, Moon and the seven
other planets for an observer at a given latitude, longitude and UTC time.
It runs offline on MicroPython (RP2040, 32-bit floats) using only the `math`
module.

```python
import skyengine

az, alt = skyengine.position(skyengine.MARS, (2030, 7, 1, 21, 30, 0), 52.23, 21.01)
all_nine = skyengine.positions((2030, 7, 1, 21, 30, 0), 52.23, 21.01)
```

Repository layout:

| Path                              | Content                                                        |
|-----------------------------------|----------------------------------------------------------------|
| `src/skyengine/`                  | production package, copy as-is to the device                   |
| `tests/`                          | CPython pytest suite and Astronomy Engine reference fixtures   |
| `tests/tools/`                    | fixture generator and optional Skyfield cross-check            |
| `tests_micropython/`              | pytest-free runner for the RP2040 or the MicroPython Unix port |
| `doc/skyengine/requirements.md`   | specification                                                  |
| `doc/skyengine/implementation.md` | implementation notes, accuracy, limitations, how to test       |

Run the PC tests:

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[test]'
pytest
```
