# Target-device tests

`run_tests.py` checks the engine without pytest or third-party modules. It
compares against `tests/fixtures/reference_device.jsonl`, a small subset of
the Astronomy Engine reference positions (regenerate both files with
`python tests/tools/gen_fixtures.py` on the PC). The same tolerances apply as
in the CPython suite: 1 degree for the Sun and planets, 2 degrees for the
Moon. The runner prints the floating-point width of the interpreter and the
maximum error per body.

## RP2040 (mpremote)

```sh
pip install mpremote
mpremote cp -r src/skyengine :
mpremote cp tests/fixtures/reference_device.jsonl :
mpremote cp tests_micropython/run_tests.py :
mpremote run tests_micropython/run_tests.py
```

Alternatively mount the repository without copying:

```sh
mpremote mount . exec "import sys; sys.path.insert(0, 'src'); exec(open('tests_micropython/run_tests.py').read())"
```

## MicroPython Unix port with 32-bit floats

The stock Unix port uses 64-bit floats. To reproduce the RP2040 behaviour on
a PC, build it with single precision:

```sh
cd micropython/ports/unix
make submodules
make CFLAGS_EXTRA='-DMICROPY_FLOAT_IMPL=MICROPY_FLOAT_IMPL_FLOAT'
```

then, from this repository root:

```sh
MICROPYPATH=src path/to/micropython tests_micropython/run_tests.py tests/fixtures/reference_device.jsonl
```

## CPython sanity run

```sh
PYTHONPATH=src python3 tests_micropython/run_tests.py tests/fixtures/reference_device.jsonl
```
