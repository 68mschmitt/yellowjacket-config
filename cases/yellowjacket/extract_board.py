#!/usr/bin/env python3
"""Extract mechanical data from the original board without touching the PCB files."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
BOARD_PATH = "pcbs/yellowjacket/yellowjacket.kicad_pcb"
BOARD_COMMIT = "c33fb44ca9b7976cfc861d12f74ec4a424eb21dc"


def parse_sexpr(text):
    stack = []
    root = None
    for match in re.finditer(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text):
        token = match.group()
        if token == "(":
            node = []
            if stack:
                stack[-1].append(node)
            else:
                if root is not None:
                    raise ValueError("Multiple root expressions")
                root = node
            stack.append(node)
        elif token == ")":
            stack.pop()
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    if stack:
        raise ValueError("Unclosed expression")
    return root


def children(node, name):
    return [item for item in node if isinstance(item, list) and item and item[0] == name]


def child(node, name, default=None):
    matches = children(node, name)
    return matches[0] if matches else default


def xy(node):
    return [float(node[1]), float(node[2])]


def rotate(point, degrees):
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    return [c * point[0] - s * point[1], s * point[0] + c * point[1]]


def reference(footprint):
    for prop in children(footprint, "property"):
        if prop[1] == "Reference":
            return prop[2]
    for text in children(footprint, "fp_text"):
        if text[1] == "reference":
            return text[2]
    return ""


def extract(ref=BOARD_COMMIT):
    commit = subprocess.check_output(
        ["git", "rev-parse", f"{ref}^{{commit}}"], cwd=ROOT, text=True
    ).strip()
    raw = subprocess.check_output(["git", "show", f"{commit}:{BOARD_PATH}"], cwd=ROOT)
    board = parse_sexpr(raw.decode())
    edges = []
    for item in board:
        if not isinstance(item, list) or item[0] not in ("gr_line", "gr_arc"):
            continue
        if child(item, "layer")[1] != "Edge.Cuts":
            continue
        if item[0] == "gr_line":
            edges.append({"type": "line", "start": xy(child(item, "start")),
                          "end": xy(child(item, "end"))})
        elif child(item, "mid"):
            edges.append({"type": "arc", **{
                key: xy(child(item, key)) for key in ("start", "mid", "end")
            }})
        else:
            # Legacy KiCad arcs store the centre in 'start' and the initial
            # point in 'end'. In KiCad's downward Y axis, rotate by 'angle'.
            centre = xy(child(item, "start"))
            start = xy(child(item, "end"))
            delta = [start[i] - centre[i] for i in (0, 1)]
            sweep = float(child(item, "angle")[1])
            points = [rotate(delta, sweep * fraction) for fraction in (0.5, 1)]
            edges.append({"type": "arc", "start": start,
                          "mid": [centre[i] + points[0][i] for i in (0, 1)],
                          "end": [centre[i] + points[1][i] for i in (0, 1)]})

    footprints = []
    for item in children(board, "footprint"):
        at = child(item, "at")
        origin = xy(at)
        angle = float(at[3]) if len(at) > 3 else 0
        pads = []
        for pad in children(item, "pad"):
            local = xy(child(pad, "at"))
            # Footprint rotation is counterclockwise viewed from above.
            offset = rotate(local, -angle)
            drill = child(pad, "drill", [])
            pads.append({
                "number": pad[1], "type": pad[2], "shape": pad[3],
                "at": [origin[i] + offset[i] for i in (0, 1)],
                "size": xy(child(pad, "size")),
                "drill": [float(value) for value in drill[1:] if value != "oval"],
            })
        footprints.append({"name": item[1], "reference": reference(item),
                           "at": origin, "rotation": angle, "pads": pads})

    result = {
        "schema": 1,
        "source": {"repository": "https://github.com/jimmerricks/bugs",
                   "commit": commit, "path": BOARD_PATH,
                   "sha256": hashlib.sha256(raw).hexdigest()},
        "revision": child(child(board, "title_block"), "rev")[1],
        "thickness": float(child(child(board, "general"), "thickness")[1]),
        "edges": edges, "footprints": footprints,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default=BOARD_COMMIT, help="Explicit Git revision of the PCB")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("board.json"))
    args = parser.parse_args()
    board = extract(args.ref)
    args.output.write_text(json.dumps(board, indent=2) + "\n")
    switches = [fp for fp in board["footprints"] if fp["reference"].startswith("SW")]
    mounts = [fp for fp in board["footprints"] if "thread_m2" in fp["name"]]
    print(f"Yellowjacket {board['revision']}: {len(board['edges'])} outline segments, "
          f"{len(switches)} switches, PCB {board['thickness']} mm")
    print(f"Switch footprints: {sorted({fp['name'] for fp in switches})}")
    print(f"Mounting-reference footprints: {len(mounts)}, "
          f"actual pads in those footprints: {sum(len(fp['pads']) for fp in mounts)}")
    for fp in board["footprints"]:
        if fp["reference"] in ("U1", "PSW1", "BT1") or fp in mounts:
            print(f"  {fp['reference']} {fp['name']}: {fp['at']}")
    print(f"Source: {board['source']['commit']}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
