# Tools

Run commands from the repository root.

| Tool | Purpose |
| --- | --- |
| `build-pinchwing-dongle.sh` | Build all dongle/half/display/reset targets in an initialized west workspace |
| `check-pinchwing-uf2.py` | Check UF2 block integrity and conservative legacy bootloader size |
| `convert-bongo-cat.py` | Regenerate original body and paw sprite C data |
| `convert-cat-overlays.py` | Export demo props into compact firmware tiles |
| `publish-pinchwing-release.py` | Validate and publish a versioned round-display bundle with compatible halves, logs, checksums, and source/dependency provenance |

Local rebuilds go to `build/firmware/pinchwing-dongle/development/`.
Published bundles use `releases/<version>/`, with `current` pointing at the
recommended bundle. Historical experiments live under `archive/`.
Build trees are disposable; release bundles include flashing files, checksums,
and metadata. See [display development](../docs/development/display.md).
