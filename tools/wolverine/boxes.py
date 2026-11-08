#!/usr/bin/env python
"""Wolverine's MSHvSF hit and hurt boxes per move step, for saturn/guests/wolverine (build input, ROM-derived, never in git).
Reads boxes.txt of a WV_BOXES=1 MAME run over the same schedule as the pose capture (tools/wolverine/run_mame.sh full.txt), the windows of
assets.py and the move steps of remap.json. A step's frames are the window's frames in order, step by step by its frame count.
Each box is put in his own frame: x forward of the player origin, y up from the feet (MSHvSF's origin, +0c/+10). Per step:
  hit  = union over the step of the first attack box (+70, else +72; throw-range ids with bit 15 left out) and the number of frames one is out;
  hurt = union of the hurt boxes (+74..+7a).
MSHvSF and AvP draw at the same pixel scale here (his poses are drawn 1:1), so the boxes go over as they are; the depth stays AvP's.
usage: boxes.py BOXES.txt ASSETS_DIR   (writes ASSETS_DIR/boxes.json)"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from assets import WINDOWS


# His origin (+0c/+10 against the screen base) sits on the pose anchor in x and FEET px above its bottom row (boxcap obj.txt against
# boxes.txt, idle and lp frames: anchor - origin = 64, 29 in object space, object space = screen + 64, + 16).
FEET = 13


def rect(s):
    if s == "-":
        return None
    i, v = s.split(":")
    x, xr, y, yr = (int(t) for t in v.split(","))
    return int(i, 16), (-x - xr, -x + xr, -y - yr + FEET, -y + yr + FEET)   # forward, up from the feet


def union(a, b):
    if a is None:
        return b
    return (min(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), max(a[3], b[3]))


def main():
    src, adir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    A = json.loads((adir / "remap.json").read_text())
    moves = A.get("moves_one", A["moves"])
    fr = {}
    for line in src.read_text().splitlines():
        t = line.split()
        if t[0] != "b":
            continue
        boxes = [rect(s) for s in t[8:14]]
        hit = [b[1] for b in boxes[:2] if b and not b[0] & 0x8000]
        fr[int(t[1])] = dict(hit=hit[:1], hurt=[b[1] for b in boxes[2:] if b])   # the first attack box only: the second (+72) runs past the art (hp: 148 px)
    out = {}
    for name, seq in moves.items():
        steps = []
        if name in WINDOWS and WINDOWS[name][0] < 100000:
            f = WINDOWS[name][0]
            for _pose, n, _anc in seq:
                hit = hurt = None
                act = 0
                for g in range(f, f + n):
                    b = fr.get(g)
                    if not b:
                        continue
                    for r in b["hit"]:
                        hit = union(hit, r)
                    if b["hit"]:
                        act += 1
                    for r in b["hurt"]:
                        hurt = union(hurt, r)
                f += n
                steps.append(dict(hit=hit, active=act, hurt=hurt, frames=n))
            print(name, "frames", f - WINDOWS[name][0], "of window", WINDOWS[name][1] - WINDOWS[name][0] + 1, "active", sum(s["active"] for s in steps))
        else:   # runs without a box capture (dash, crouch): no hit box; the hurt box comes from idle at runtime
            steps = [dict(hit=None, active=0, hurt=None, frames=n) for _p, n, _a in seq]
            print(name, "no box capture")
        out[name] = steps
    # The capture's Berserker Barrage window caught him in hitstun (+06 = 12 from 2402 to 2432), so no attack box was out. Until a clean
    # capture exists, its two slash poses (steps 1 and 2) take the standing heavy slash's box: same arm reach, flagged in boxes.json.
    b = out.get("berserker")
    if b and not any(s["active"] for s in b) and out.get("hp"):
        hb = next(s["hit"] for s in out["hp"] if s["hit"])
        for s in b[1:3]:
            s["hit"], s["active"], s["stand_in"] = hb, s["frames"], "hp"
        print("berserker: stand-in box from hp", hb)
    (adir / "boxes.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
