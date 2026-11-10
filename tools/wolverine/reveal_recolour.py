#!/usr/bin/env python
"""Wolverine reveal art: recolour the classic blue costume to the red he wears in play; the yellow costume stays as the artist drew it (owner, 11-09: "keeps his current in-play colour").
usage: reveal_recolour.py SRC_DIR OUT_DIR   (SRC_DIR holds frame1_closed.png, frame2_opening.png, frame3_burst.png; the originals are never written)

His in-play reds (his sprite, rounded to the 12-bit grid) take the costume's blues the way hud_art.py maps its blue ramp, light to light, dark to dark:
    ramp step   in-play red   costume entries (palette index, colour)
    light       #ee3300       53 #5566aa  54 #667799  55 #7788aa  57 #8899bb  58 #aabbdd
    mid         #cc0000       50 #445599  51 #556677  52 #556688  49 #555577
    dark        #880000       47 #445577  46 #445566  45 #444466
    darkest     #550000       43 #333344  42 #222233
Palette entries 50 and 53 are costume only (every pixel of them lies in the six costume patches), so they change colour in place. The others are SHARED with
the pipes, walls, aliens' shading and floor of all three frames: only the costume's pixels of them are recoloured, and they move to entry 53 or 50 (light, mid) or to two
new entries appended to the shared palette (dark, darkest). A pixel is a costume pixel when a chain of blue-ramp pixels of at most 4 pixels joins it to 50 or 53.
Everything else keeps its entry and colour: the yellows, skin, belt, aliens (teal, steel purple) and scenery; frames 1 and 2 are copied as they are.
Every 16 x 16 tile still holds at most 15 opaque colours (checked; a tile pushed over loses its least used scenery colour of a recoloured entry to the nearest colour in the tile, reported).
(The 80s red-brown and gold variant of revision 3 of the artist's palette was tried on 11-09 and dropped: RB and GOLD below, RECOLOUR_YELLOW.)"""
import json
import pathlib
import sys
from collections import deque
from PIL import Image
import numpy as np

FRAMES = ("frame1_closed.png", "frame2_opening.png", "frame3_burst.png")
RB = ((0xee, 0x33, 0x00), (0xcc, 0x00, 0x00), (0x88, 0x00, 0x00), (0x55, 0x00, 0x00))     # his sprite's reds, light to dark (80s variant: bb7755 995533 662211 331111)
GOLD = ((0xff, 0xee, 0xbb), (0xdd, 0xbb, 0x66), (0xbb, 0x88, 0x33), (0x77, 0x55, 0x22))   # gold, light to dark
IN_PLACE = {53: RB[0], 50: RB[1]}   # costume-only entries
BLUE = {53: 0, 54: 0, 55: 0, 57: 0, 58: 0, 50: 1, 51: 1, 52: 1, 49: 1, 47: 2, 46: 2, 45: 2, 43: 3, 42: 3}   # entry -> red-brown step
RECOLOUR_YELLOW = False                      # the 80s variant recoloured the costume's yellows to GOLD
YELLOW = {35: 0, 27: 1, 26: 2, 25: 3} if RECOLOUR_YELLOW else {}       # entry -> gold step
YELLOW_SHADE = {24: 3} if RECOLOUR_YELLOW else {}                       # one pixel from the gold only
REACH = 4
FIGURE = (150, 85, 230, 160)                 # x0 y0 x1 y1 of the figure's yellow in frame 3
MIN_PATCH = 80


def tile_colours(a):
    return max(len(set(a[ty * 16:ty * 16 + 16, tx * 16:tx * 16 + 16].flatten().tolist()) - {0}) for ty in range(a.shape[0] // 16) for tx in range(a.shape[1] // 16))


def blue_mask(a):
    ramp = np.isin(a, list(BLUE))
    dist = np.full(a.shape, 99, dtype=int)
    q = deque()
    for y, x in zip(*np.nonzero((a == 50) | (a == 53))):
        dist[y, x] = 0
        q.append((y, x))
    while q:
        y, x = q.popleft()
        if dist[y, x] >= REACH:
            continue
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] and ramp[yy, xx] and dist[yy, xx] > dist[y, x] + 1:
                    dist[yy, xx] = dist[y, x] + 1
                    q.append((yy, xx))
    return dist <= REACH


def gold_mask(a):
    """8-connected patches of the yellow entries inside the figure's box with at least MIN_PATCH pixels, and the shade entry one pixel from them"""
    y_all = np.isin(a, list(YELLOW))
    if not YELLOW:
        return np.zeros(a.shape, dtype=bool), np.zeros(a.shape, dtype=bool)
    lab = np.zeros(a.shape, dtype=bool)
    seen = np.zeros(a.shape, dtype=bool)
    for y0, x0 in zip(*np.nonzero(y_all)):
        if seen[y0, x0]:
            continue
        stack, px = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            px.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] and y_all[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True
                        stack.append((yy, xx))
        xs = [p[1] for p in px]
        ys = [p[0] for p in px]
        if len(px) >= MIN_PATCH and min(xs) >= FIGURE[0] and min(ys) >= FIGURE[1] and max(xs) <= FIGURE[2] and max(ys) <= FIGURE[3]:
            for p in px:
                lab[p] = True
    p = np.pad(lab, 1)
    near = np.zeros_like(lab)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near |= p[1 + dy:1 + dy + lab.shape[0], 1 + dx:1 + dx + lab.shape[1]]
    return lab, near & np.isin(a, list(YELLOW_SHADE)) & ~lab


def recolour(src, out):
    src, out = pathlib.Path(src), pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ims = [Image.open(src / f) for f in FRAMES]
    arrs = [np.array(im) for im in ims]
    npal = max(int(a.max()) for a in arrs) + 1
    pal = list(ims[0].getpalette())[:npal * 3]
    assert all(list(im.getpalette())[:npal * 3] == pal for im in ims), "the frames do not share a palette"
    for i in IN_PLACE:
        assert all(int((a == i).sum()) == 0 for a in arrs[:2]), "entry %d is not costume only" % i
    f3 = arrs[2]
    bmask = blue_mask(f3)
    for i in IN_PLACE:
        assert not ((f3 == i) & ~bmask).any()
    gmask, smask = gold_mask(f3)
    new_pal = list(pal)
    for i, rgb in IN_PLACE.items():
        new_pal[i * 3:i * 3 + 3] = list(rgb)
    idx = {}
    for name, ramp, steps in (("rb", RB, (2, 3)),) + ((("gold", GOLD, (0, 1, 2, 3)),) if RECOLOUR_YELLOW else ()):
        for s in steps:
            idx[(name, s)] = len(new_pal) // 3
            new_pal += list(ramp[s])
    rb_to = {0: 53, 1: 50, 2: idx[("rb", 2)], 3: idx[("rb", 3)]}
    new = [a.copy() for a in arrs]
    report = {"palette_entries_before": npal, "blue": [], "yellow": [], "costume_pixels_blue": int(bmask.sum()), "costume_pixels_yellow": int(gmask.sum() + smask.sum())}
    hexc = lambda p, i: "#%02x%02x%02x" % tuple(p[i * 3:i * 3 + 3])
    for old, step in sorted(BLUE.items()):
        if old >= npal:
            continue
        to = rb_to[step]
        total = [int((a == old).sum()) for a in arrs]
        m = (f3 == old) & bmask
        new[2][m] = to
        report["blue"].append({"old_index": old, "old": hexc(pal, old), "to_index": to, "to": hexc(new_pal, to), "pixels_recoloured_frame3": int(m.sum()),
                               "pixels_of_entry_frames_1_2_3": total, "shared_with_scenery": bool(total[0] or total[1] or total[2] - int(m.sum()))})
    for old, step in sorted({**YELLOW, **YELLOW_SHADE}.items()):
        if old >= npal:
            continue
        to = idx[("gold", step)]
        m = ((f3 == old) & gmask) if old in YELLOW else ((f3 == old) & smask)
        total = [int((a == old).sum()) for a in arrs]
        new[2][m] = to
        report["yellow"].append({"old_index": old, "old": hexc(pal, old), "to_index": to, "to": hexc(new_pal, to), "pixels_recoloured_frame3": int(m.sum()),
                                 "pixels_of_entry_frames_1_2_3": total, "shared_with_scenery": bool(total[0] or total[1] or total[2] - int(m.sum()))})
    merged = []
    watch = set(BLUE) | set(YELLOW) | set(YELLOW_SHADE)
    for ty in range(new[2].shape[0] // 16):
        for tx in range(new[2].shape[1] // 16):
            t = new[2][ty * 16:ty * 16 + 16, tx * 16:tx * 16 + 16]
            while len(set(t.flatten().tolist()) - {0}) > 15:
                cand = [(int((t == e).sum()), e) for e in sorted(set(t.flatten().tolist()) - {0}) if e in watch and e not in IN_PLACE and e < npal]
                if not cand:
                    raise SystemExit("NO-GO: tile %d,%d over 15 colours" % (tx, ty))
                n, e = min(cand)
                others = [c for c in set(t.flatten().tolist()) - {0, e}]
                to = min(others, key=lambda c: sum((new_pal[c * 3 + k] - new_pal[e * 3 + k]) ** 2 for k in range(3)))
                t[t == e] = to
                merged.append({"tile": [tx, ty], "from_index": e, "to_index": to, "pixels": n})
    report["merged"] = merged
    for a, f in zip(new, FRAMES):
        if tile_colours(a) > 15:
            raise SystemExit("NO-GO: %s over 15 colours in a tile" % f)
    report["max_opaque_colours_per_tile"] = max(tile_colours(a) for a in new)
    report["palette_entries_after"] = len(new_pal) // 3
    for a, f in zip(new, FRAMES):
        o = Image.fromarray(a, "P")
        o.putpalette(new_pal + [0] * (768 - len(new_pal)))
        o.save(out / f.replace(".png", "_red.png"))
    keep = [i for i in range(npal) if i not in IN_PLACE]
    assert all(new_pal[i * 3:i * 3 + 3] == pal[i * 3:i * 3 + 3] for i in keep)
    old_rgb = np.array(pal).reshape(-1, 3)[arrs[2]]
    new_rgb = np.array(new_pal).reshape(-1, 3)[new[2]]
    d = (old_rgb != new_rgb).any(axis=2)
    ys, xs = np.nonzero(d)
    report["changed_pixels_frame3"] = int(d.sum())
    report["changed_bbox_frame3"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    report["changed_pixels_frames_1_2"] = [int((a != b).sum()) for a, b in zip(new[:2], arrs[:2])]
    (out / "recolour.json").write_text(json.dumps(report, indent=1))
    return report


if __name__ == "__main__":
    print(json.dumps(recolour(sys.argv[1], sys.argv[2]), indent=1))
