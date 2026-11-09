#!/usr/bin/env python
"""Choose a gameplay pose set from an existing private assets.py capture.

usage: reselect.py IN_DIR OUT_DIR FULL_MOVES [BUDGET]
FULL_MOVES is comma-separated: walk,hp,hk preserves every pose of those moves;
walk/2 keeps alternate walk poses. 'all' preserves every move's poses. A missing
BUDGET (or 0) keeps only the required/full set, without filling spare room.

Only tiles referenced by emitted moves are resident in gameplay. Portraits and
their graphics remain in the asset source for future HUD/select work. This does
not prove Saturn fit: run fit.py on the result, then regenerate boxes.py's data.
HIT8=0 omits optional long-held hitstun poses, as before.
"""
import json
import os
import pathlib
import shutil
import sys


def select(asset, full_specs, budget=0, hit8=True):
    poses, moves, keys = asset["poses"], asset["moves"], asset["keys"]
    if not moves or any(not seq for seq in moves.values()):
        raise ValueError("every move must contain at least one pose")
    if budget < 0:
        raise ValueError("BUDGET must be nonnegative")
    seen, fresh, hold = set(), {}, {}
    for name, seq in moves.items():
        order = list(dict.fromkeys(step[0] for step in seq))
        fresh[name] = [pose for pose in order if pose not in seen]
        seen.update(order)
        for pose, frames, _ in seq:
            if not 0 <= pose < len(poses) or frames <= 0:
                raise ValueError("invalid pose or duration in " + name)
            hold[pose] = max(hold.get(pose, 0), frames)

    # trim always emits the first pose of every move, even if it was previously
    # seen in another move. Account for it before budgeting, not after packing.
    need = {seq[0][0] for seq in moves.values()}
    stance = asset.get("stance_pose", 17)
    if not 0 <= stance < len(poses):
        raise ValueError("stance_pose is absent from this capture")
    if stance in seen:
        need.add(stance)
    for name, own in fresh.items():
        if own:
            need.update((own[0], max(own, key=hold.get), own[-1]))
            if name == "hit_etc" and hit8:
                need.update(pose for pose in own if hold[pose] >= 8)
    for spec in full_specs:
        name, _, every = spec.partition("/")
        if name not in moves:
            raise ValueError("unknown move: " + name)
        stride = int(every) if every else 1
        if stride < 1:
            raise ValueError("pose stride must be positive: " + spec)
        order = list(dict.fromkeys(pose for pose, _, _ in moves[name]))
        need.update(pose for index, pose in enumerate(order)
                    if index % stride == 0 or index == len(order) - 1)

    def cost(pose_ids):
        return len({tile[2] for pose in pose_ids for tile in poses[pose]})

    floor = cost(need)
    if budget and floor > budget:
        raise ValueError("required/full poses need %d tiles, exceeding BUDGET %d" % (floor, budget))
    if budget:
        order = (["walk"] if "walk" in fresh else []) + [name for name in fresh if name != "walk"]
        progress = True
        while progress:
            progress = False
            for name in order:
                own = fresh[name]
                candidates = [index for index, pose in enumerate(own) if pose not in need]
                if not candidates:
                    continue
                kept = [index for index, pose in enumerate(own) if pose in need]
                index = max(candidates, key=lambda j: min(abs(j - k) for k in kept) if kept else 0)
                if cost(need | {own[index]}) <= budget:
                    need.add(own[index])
                    progress = True

    trimmed = {}
    for name, seq in moves.items():
        steps = []
        for pose, frames, anchor in seq:
            if pose in need or not steps:
                steps.append([pose, frames, anchor])
            else:
                steps[-1][1] += frames
        trimmed[name] = steps
    emitted = {step[0] for seq in trimmed.values() for step in seq}
    have = {tile[2] for pose in emitted for tile in poses[pose]}
    portrait_tiles = {tile[2] for group in asset.get("portraits", {}).values() for tile in group}
    result = dict(asset)
    result["moves_one"] = trimmed
    result["stance_pose"] = stance
    result["boxes_pending"] = True
    result["one_set"] = dict(budget=budget, floor=floor, full=list(full_specs),
                             tiles=len(have), poses=len(emitted), residency="emitted_moves",
                             portrait_only_tiles_omitted=len(portrait_tiles - have))
    result["stage_keys"] = {"%02x" % stage: sorted(keys[tile] for tile in have)
                            for stage in range(2, 0x28, 2)}
    return result


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not 3 <= len(argv) <= 4:
        print("usage: reselect.py IN_DIR OUT_DIR FULL_MOVES [BUDGET]", file=sys.stderr)
        return 2
    try:
        src, out = pathlib.Path(argv[0]), pathlib.Path(argv[1])
        asset = json.loads((src / "remap.json").read_text())
        full = list(asset["moves"]) if argv[2] == "all" else [name for name in argv[2].split(",") if name]
        selected = select(asset, full, int(argv[3]) if len(argv) == 4 else 0,
                          hit8=os.environ.get("HIT8", "1") == "1")
        # Reject missing source bytes before publishing a new remap beside old
        # graphics. Always refresh a different output's graphics from its source.
        graphics = src / "gfx_wolverine.bin"
        if not graphics.is_file():
            raise ValueError("missing source gfx_wolverine.bin")
        out.mkdir(parents=True, exist_ok=True)
        if src.resolve() != out.resolve():
            shutil.copyfile(graphics, out / "gfx_wolverine.bin")
        (out / "remap.json").write_text(json.dumps(selected))
        print("one set", selected["one_set"])
        print("Regenerate boxes.json for these move steps, then run fit.py.")
        # Keep existing evidence intact. gen_c refuses step-indexed boxes until
        # boxes.py clears boxes_pending for this new selection.
        return 0
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        print("NO-GO:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
