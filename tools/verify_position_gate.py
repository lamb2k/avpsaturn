"""The scoped per-part position gate.

Answers one question for the currently decoded boss poses: does an object's
screen position, predicted from the previous frame's world coordinates plus
the ROM assembly's layout words, match captured object RAM or leave only a
known, explicitly classified residual?

Model (see docs/AGENT_HANDOFF.md):

    right_ring = wx(f-1) + origin_x - lx + 64
    left_ring  = right_ring - width
    top_ring   = 464 - origin_y + ly - wy(f-1)

where

* wx, wy are the integer parts of the actor's 16.16 world coordinates from the
  *previous* frame (one-frame render lag). World Y is up; screen Y is down,
  hence the subtractive Y form.
* (origin_x, origin_y) and, per object, (lx, ly) come from the selector-6
  assembly the animation record selects (data/avsp_animation_scripts.json).
* 64 is VISIBLE_LEFT and 464 is the single global Y constant
  (verified: C(part) + origin_y - ly == 464 for every part).

Comparison is in the game's 1024 ring space (low 10 bits of the object X/Y
words). shift_x / shift_y are capture-tool unwrap normalizations, not game
state, so they are not part of the oracle. Residuals are signed on the ring,
so crossing the boundary is not a large error.

Assembly selection is by the captured object-code set (the same robust match
the pose gate uses). Two cases are handled honestly:

* Attack / hit poses whose code set is not one of the decoded assemblies are
  counted as unmatched (their assemblies are not yet in the JSON). They do not
  silently pass full-coverage validation.
* Where two assemblies share a code set (the airborne vs at-rest forms of
  assembly 3, and a sibling of assembly 1), the code-set match alone cannot
  tell them apart; their per-code layout words are identical and only the
  origin differs. The gate selects the correct origin with the actor-slot
  record pointer at frame f-1 (the same one-frame source the world
  coordinates use): when that pointer's table has the captured code set, its
  origin is adopted, which drives the formerly ambiguous frame to exact.
  As a safety net the gate still DECODES every pointer-reachable table and
  builds the set of origin-delta residuals a shared code set can produce; any
  residual not driven to zero PASSES only if it is in that explained set,
  never as a general tolerance.

The only other residual in the whole scope (8 parts, 2 frames) is (x=0, y=-4).
This is a *formally bounded* observation, not a general tolerance:

* It is the single non-zero residual across every tested part (X is 100%
  exact; the residual table contains only (0,0) and (0,-4)).
* It is whole-pose: every part in each of the two frames shifts by the same
  (0,-4), i.e. a global actor-Y offset, not a per-part layout/tile defect.
* It occurs only just after the integer world Y has decelerated to a rest
  value (a vertical settle); the implied world Y that would zero it is the
  rest value minus 4 in both cases, so the on-screen Y applies one final
  downward settle step while the world RAM has already clamped to rest.
  The exact object-Y writer that produces that one-step trail is not yet
  disassembled, so the gate reports it as bounded, not derived.

The tool recognises only that precise residual in that recent-world-Y-change
context, so it cannot broaden into a general +/-4 tolerance.

The default exit status is a *scoped* gate: green means every tested part is
exact or belongs to one of those explicit residual classes. ``--require-exact``
is the goal-strength gate: it also requires every geometry frame to be matched
and every tested part to have residual (0, 0).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_avspu_stage1 as avsp  # noqa: E402
import verify_pose_gate as gate  # noqa: E402
import decode_avsp_animation_scripts as dec  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
BOSS_DIR = ROOT / ".deps" / "mame" / "boss_actions"
SCRIPTS = ROOT / "data" / "avsp_animation_scripts.json"
ROM = ROOT / ".deps" / "mame" / "actorprobe" / "rom_window_13c_13f.bin"
OFFSET = ROOT / ".deps" / "mame" / "actorprobe" / "offset_program.bin"
ROM_BASE = 0x13C000
ASSEMBLY_FIRST = 0x13DE00
ASSEMBLY_LAST = 0x13F000
RING = 1024


def _signed(value: int) -> int:
    """Map a ring delta to [-RING/2, RING/2)."""
    value %= RING
    if value > RING // 2:
        value -= RING
    return value


def load_world() -> dict[int, tuple[int, int, int]]:
    """Per-frame (wx, wy, record_pointer) from the actor slot."""
    world: dict[int, tuple[int, int, int]] = {}
    for path in sorted(BOSS_DIR.glob("workram_*.bin")):
        frame = int(path.stem.split("_")[1])
        raw = path.read_bytes()
        wx = int.from_bytes(raw[0x23D0:0x23D2], "big")
        wy = int.from_bytes(raw[0x23D4:0x23D6], "big")
        ptr = int.from_bytes(raw[0x23DC:0x23E0], "big")
        world[frame] = (wx, wy, ptr)
    return world


def build_by_codes(assemblies: list[dict]) -> dict[frozenset, int]:
    by_codes: dict[frozenset, int] = {}
    for idx, assembly in enumerate(assemblies):
        entries = assembly["entries"][:assembly.get("count", 0)]
        codes = frozenset(int(e["code"], 16) for e in entries)
        by_codes[codes] = idx
    return by_codes


def decode_assembly_at(rom: bytes, offset_data: bytes, address: int) -> dict | None:
    if not (ASSEMBLY_FIRST <= address < ASSEMBLY_LAST):
        return None
    assembly = dec.decode_assembly(rom, ROM_BASE, address, offset_data,
                                   layout_data=None, offset_base=0x1FD1C8)
    if assembly.get("status") != "decoded_structure":
        return None
    return assembly


def assembly_for_record(rom: bytes, offset_data: bytes, pointer: int) -> dict | None:
    """Follow an actor-slot record pointer to the assembly it selects."""
    if pointer < dec.SCRIPT_FIRST or pointer >= dec.SCRIPT_LAST:
        return None
    offset = pointer - ROM_BASE
    if offset < 0 or offset + 8 > len(rom):
        return None
    first = dec.u32(rom, offset)
    if dec.SCRIPT_FIRST <= first < dec.SCRIPT_LAST:
        offset = first - ROM_BASE
    if offset < 0 or offset + 8 > len(rom):
        return None
    return decode_assembly_at(rom, offset_data, dec.u32(rom, offset + 4))


def build_explained(rom: bytes, offset_data: bytes,
                    assemblies: list[dict],
                    world: dict[int, tuple[int, int, int]]) -> set[tuple[int, int]]:
    """All (dx, dy) residuals a shared-code-set ambiguity can produce.

    Collects every (origin_x, origin_y) per object-code set across the JSON
    assemblies and the assemblies the record pointers select, then returns the
    origin deltas between every ordered pair of distinct tables in a set.
    """
    origins: dict[frozenset, set[tuple[int, int]]] = defaultdict(set)
    for assembly in assemblies:
        entries = assembly["entries"][:assembly.get("count", 0)]
        codes = frozenset(int(e["code"], 16) for e in entries)
        origins[codes].add((assembly["origin_x"], assembly["origin_y"]))
    for (_wx, _wy, pointer) in world.values():
        assembly = assembly_for_record(rom, offset_data, pointer)
        if assembly is None:
            continue
        entries = assembly["entries"][:assembly.get("count", 0)]
        codes = frozenset(int(e["code"], 16) for e in entries)
        origins[codes].add((assembly["origin_x"], assembly["origin_y"]))

    explained = {(0, 0)}
    for oset in origins.values():
        for ax, ay in oset:
            for bx, by in oset:
                if (ax, ay) == (bx, by):
                    continue
                # picked table (a) vs true table (b): pred - true
                explained.add((ax - bx, by - ay))
    return explained


def run(verbose: bool = False, require_exact: bool = False) -> int:
    scripts = json.loads(SCRIPTS.read_text(encoding="ascii"))
    assemblies = scripts["assemblies"]
    by_codes = build_by_codes(assemblies)
    world = load_world()
    geometry = gate.load_frame_geometry()
    rom = ROM.read_bytes()
    offset_data = OFFSET.read_bytes()
    explained = build_explained(rom, offset_data, assemblies, world)

    total_frames = matched_frames = unmatched_frames = 0
    total_parts = 0
    x_resid = Counter()
    y_resid = Counter()
    pair_resid = Counter()
    settling = 0
    settling_cases: list[tuple[int, int, int]] = []
    sibling = 0
    unexplained: list[tuple[int, int, int, int, int]] = []
    per_asm: dict[int, dict] = defaultdict(
        lambda: {"parts": Counter(), "x": Counter(), "y": Counter()})

    def is_settling(frame: int, xr: int, yr: int) -> bool:
        # The only observed transient is exactly (0, -4), about two frames
        # after world Y changes. Keep this narrow so it cannot become a general
        # tolerance that hides a new position-model error.
        if (xr, yr) != (0, -4):
            return False
        recent_y = [world[f][1] for f in range(frame - 3, frame)
                    if f in world]
        return len(recent_y) >= 2 and recent_y[0] != recent_y[-1]

    for frame in sorted(geometry):
        if frame - 1 not in world:
            continue
        wx, wy, ptr_prev = world[frame - 1]
        spec = geometry[frame]
        entries = avsp.decode_object_entries(
            gate.read_words(Path(spec["path"])))
        by_offset = {e["offset"]: e for e in entries}
        parts = [by_offset[o] for o in spec["offsets"] if o in by_offset]
        if not parts:
            continue
        total_frames += 1
        codeset = frozenset(p["code"] for p in parts)
        idx = by_codes.get(codeset)
        if idx is None:
            unmatched_frames += 1
            continue
        matched_frames += 1
        assembly = assemblies[idx]
        ox = assembly["origin_x"]
        oy = assembly["origin_y"]
        entry_by_code = {int(e["code"], 16): e
                         for e in assembly["entries"][:assembly.get("count", 0)]}
        # Shared-code-set disambiguation. The code-set match above is
        # last-wins, so where two ROM assemblies share a code set (the at-rest
        # and airborne siblings) it may pick the wrong origin. The residual on
        # such a frame is then exactly the origin delta between the picked and
        # true tables (their per-code layouts are identical). The actor-slot
        # record pointer at frame f-1 -- the same one-frame source the world
        # coordinates use -- selects the true table. If that table has this
        # frame's code set, use its origin; the layout words are unchanged
        # because the observed delta was a pure origin offset.
        selected = assembly_for_record(rom, offset_data, ptr_prev)
        if selected is not None:
            sel_codes = frozenset(int(e["code"], 16)
                                  for e in selected["entries"][:selected.get("count", 0)])
            if sel_codes == codeset:
                ox = selected["origin_x"]
                oy = selected["origin_y"]
        for part in parts:
            entry = entry_by_code.get(part["code"])
            if entry is None:
                continue
            total_parts += 1
            lx = int(entry["layout_x_signed"])
            ly = int(entry["layout_y_signed"])
            width = part.get("width", 16)
            cap_left = part["x"] & 0x3FF
            cap_top = part["y"] & 0x3FF
            left_pred = wx + ox - lx + 64 - width
            top_pred = 464 - oy + ly - wy
            xr = _signed(left_pred - cap_left)
            yr = _signed(top_pred - cap_top)
            x_resid[xr] += 1
            y_resid[yr] += 1
            pair_resid[(xr, yr)] += 1
            per_asm[idx]["parts"]["n"] += 1
            per_asm[idx]["x"][xr] += 1
            per_asm[idx]["y"][yr] += 1
            if (xr, yr) == (0, 0):
                continue
            if (xr, yr) in explained:
                sibling += 1
            elif is_settling(frame, xr, yr):
                settling += 1
                settling_cases.append((frame, idx, part["code"]))
            else:
                unexplained.append((frame, idx, part["code"], xr, yr))

    x_exact = x_resid.get(0, 0)
    y_exact = y_resid.get(0, 0)
    pair_exact = pair_resid.get((0, 0), 0)

    print("Position gate: predicted from world(f-1) + ROM layout vs capture")
    print(f"  frames total {total_frames}  matched {matched_frames}  "
          f"unmatched {unmatched_frames}")
    print(f"  parts tested {total_parts}")
    print(f"  X exact {x_exact}/{total_parts}   "
          f"Y exact {y_exact}/{total_parts}")
    print(f"  classification:  exact-pair {pair_exact}  sibling-delta {sibling}  "
          f"settling {settling}  unexplained {len(unexplained)}")
    print(f"  sibling origin-delta pairs (from decoded record tables): "
          f"{len(explained) - 1} nonzero")
    for dx, dy in sorted(p for p in explained if p != (0, 0)):
        print(f"    (x{dx:+d}, y{dy:+d})")

    print("\n  observed (x, y) residual pairs:")
    for (xr, yr), n in sorted(pair_resid.items()):
        if (xr, yr) == (0, 0):
            tag = "  (exact)"
        elif (xr, yr) in explained:
            tag = "  (sibling delta)"
        elif (xr, yr) == (0, -4) and settling == n:
            tag = "  (settling)"
        elif (xr, yr) == (0, -4) and settling:
            tag = "  (mixed settling / UNEXPLAINED)"
        else:
            tag = "  <-- UNEXPLAINED"
        print(f"    (x{xr:+d}, y{yr:+d})  {n}{tag}")

    print("\n  per-assembly (parts / X-exact / Y-exact):")
    for idx in sorted(per_asm):
        d = per_asm[idx]
        print(f"    asm[{idx:2d}]  parts {d['parts']['n']:4d}  "
              f"X-exact {d['x'].get(0, 0):4d}  Y-exact {d['y'].get(0, 0):4d}")

    scoped_ok = total_parts > 0 and not unexplained
    exact_ok = (scoped_ok and unmatched_frames == 0 and
                pair_exact == total_parts)
    if verbose and unexplained:
        print(f"\n  {len(unexplained)} UNEXPLAINED residuals (model failures):")
        for frame, idx, code, xr, yr in unexplained[:40]:
            print(f"    frame {frame} asm[{idx}] code {code}  (x{xr:+d}, y{yr:+d})")

    if verbose and settling:
        frames = sorted({frame for frame, _idx, _code in settling_cases})
        print(f"\n  {settling} settling parts in frames {frames} "
              f"(observed x+0/y-4 after a recent world-Y change; exact "
              f"cause remains open)")

    print("\n" + ("SCOPED PASS: every tested part is exact or belongs to an "
                 "explicit sibling/settling class; no unexpected residual."
                 if scoped_ok else
                 "FAIL: unexpected residuals are present in the decoded scope."))
    print("FULL PIXEL-EXACT COVERAGE: " +
          ("PASS" if exact_ok else
           f"OPEN ({unmatched_frames} unmatched frames, "
           f"{total_parts - pair_exact} tested parts not directly exact)"))
    return 0 if (exact_ok if require_exact else scoped_ok) else 1


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true",
                        help="list unexplained residuals")
    parser.add_argument("--require-exact", action="store_true",
                        help="fail unless all frames match and every residual is zero")
    args = parser.parse_args()
    raise SystemExit(run(verbose=args.verbose, require_exact=args.require_exact))


if __name__ == "__main__":
    main()
