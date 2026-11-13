# Yellowjacket mouse-test cases

The case work for branch `test/pmw3610-right` lives in [mouse/](mouse/README.md).
It includes the right sensor case, matching left pressure-fit case, fit coupons,
lens-cover insert, STL/STEP exports, FreeCAD documents and validation reports.

The directory is self-contained. `mouse/board.json` pins the mechanical PCB
geometry used for these prototypes, including its original source SHA-256.

The shared files `generate.py`, `extract_board.py`, `generate_enclosures.py`
and `parameters.json` were copied from `bugs/cases/yellowjacket` to support
the mouse-case generators. Their legacy standalone entry points are not
part of this package: use the commands in `mouse/README.md`.

Regenerate from the repository root:

```sh
python cases/yellowjacket/mouse/generate_mouse.py
python cases/yellowjacket/mouse/generate_mouse.py --left-only
python cases/yellowjacket/mouse/generate_insert.py
python cases/yellowjacket/mouse/preview_mouse.py
```
