#!/usr/bin/env python3
"""Publish a checked round-display bundle without overwriting older releases."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Release directory name, e.g. v4")
    parser.add_argument("--round-build", type=Path, required=True)
    parser.add_argument("--left", type=Path, required=True, help="Compatible left-half UF2")
    parser.add_argument("--right", type=Path, required=True, help="Compatible right-half UF2")
    parser.add_argument("--build-log", type=Path, required=True)
    parser.add_argument("--test-log", type=Path, required=True)
    parser.add_argument("--zmk-app", type=Path, required=True)
    parser.add_argument("--notes", type=Path, help="Release notes (defaults to docs/releases/pinchwing-VERSION.md)")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.version):
        parser.error("version must be a simple directory name")
    base = ROOT / "build/firmware/pinchwing-dongle"
    release = base / "releases" / args.version
    stage = base / "releases" / (args.version + ".staging")
    if release.exists() or stage.exists():
        parser.error("release/staging directory already exists; choose a new version")
    sources = {
        "pinchwing_dongle_round": args.round_build / "zephyr/zmk.uf2",
        "pinchwing_dongle_left": args.left,
        "pinchwing_dongle_right": args.right,
    }
    notes = args.notes or ROOT / "docs/releases" / f"pinchwing-{args.version}.md"
    checks = subprocess.check_output(
        ["python3", str(ROOT / "scripts/check-pinchwing-uf2.py"), *map(str, sources.values())],
        text=True,
    )
    for path in [notes, args.build_log, args.test_log, args.round_build / "zephyr/.config",
                 args.round_build / "zephyr/zephyr.dts"]:
        if not path.is_file():
            parser.error(f"missing metadata: {path}")
    if "PASS: all layers" not in args.test_log.read_text():
        parser.error("display test log does not contain a passing result")
    # Freeze checked-out commits, rather than the manifest's moving branch names.
    projects = subprocess.check_output(
        ["west", "list", "-f", "{name}|{abspath}"], cwd=args.zmk_app, text=True
    )
    revisions = {}
    for entry in projects.splitlines():
        name, path = entry.split("|", 1)
        # A west manifest directory may be a plain generated directory, not a
        # project checkout. The repo's manifest is included in source.tar.gz.
        if name == "manifest":
            continue
        if Path(path).is_dir():
            revisions[name] = subprocess.check_output(
                ["git", "-C", path, "rev-parse", "HEAD"], text=True).strip()
    metadata = stage / "metadata"
    metadata.mkdir(parents=True)
    for name, source in sources.items():
        shutil.copy2(source, stage / (name + ".uf2"))
    for source, name in [
        (args.round_build / "zephyr/.config", "round.config"),
        (args.round_build / "zephyr/zephyr.dts", "round.dts"),
        (args.build_log, "build.log"), (args.test_log, "display-test.log"),
    ]:
        shutil.copy2(source, metadata / name)
    (metadata / "uf2-checks.txt").write_text(checks)
    (metadata / "dependencies.json").write_text(json.dumps(revisions, indent=2) + "\n")
    provenance = {
        "version": args.version,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "working_tree_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "images": {name: {"source": str(path.resolve()), "sha256": digest(path)}
                   for name, path in sources.items()},
        "note": "Half images are compatible existing builds. Source snapshot describes the new receiver.",
    }
    (metadata / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    # Include uncommitted source as well, so this local build can be reproduced.
    files = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT
    ).decode().split("\0")
    with tarfile.open(metadata / "source.tar.gz", "w:gz") as archive:
        for name in sorted(set(files)):
            if name and (ROOT / name).is_file():
                archive.add(ROOT / name, arcname=name)
    shutil.copy2(notes, stage / "README.md")
    (stage / "SHA256SUMS").write_text("".join(
        f"{digest(path)}  {path.relative_to(stage)}\n"
        for path in sorted(stage.rglob("*")) if path.is_file()
    ))
    stage.rename(release)
    current = base / "current"
    if current.is_symlink():
        current.unlink()
    elif current.exists():
        parser.error(f"{current} is not a symlink; release saved but pointer not changed")
    current.symlink_to(Path("releases") / args.version, target_is_directory=True)
    print(checks, end="")
    print(f"Published {release}\nCurrent: {current}")


if __name__ == "__main__":
    main()
