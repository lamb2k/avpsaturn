"""Prove the live VDP1 frontend objects at every -FrontendShotTest hold.

Object counts are not evidence.  This check decodes the live VDP1 command
table captured by `tools/capture_frontend_cram.py` and compares every held
frame against ROM-derived oracles - the converter manifest
`data/avsp_frontend_assets.json` and the MAME-measured interaction evidence
`data/frontend_interaction.json` - reporting four independent results:

* geometry - each object's four vertices are the inclusive fitted source
  rectangle.  The runtime places objects with explicit four-point quads
  because `jo_sprite_draw3D()` routed unequal scales through SGL's
  `slDispSpriteHV()` workaround and rotated every quad by a fraction of a
  degree, which read back two scanlines too tall and one pixel sheared.  The
  correction passes only if the live inclusive bounds match exactly.
* colour - each object's CMDCOLR is the colour-bank address Jo derives from
  the palette id and the object's sub-bank, `256 * id + 16 * subbank`.
* order - the draw order matches the source schedule.  VDP1 draws the list in
  address order while the runtime emits increasing depth, so the frontend's
  objects appear reversed with respect to the schedule; that reversal is part
  of the expected result, not a tolerance.
* timing - the hold's encounter state and in-state frame are the ones the
  schedule is defined at, the live encounter timer agrees with the in-state
  frame count, and the cursor's six-frame border cycle is proved by texture
  address rather than by picture.

Covered holds and their oracles:

* the twelve title objects, from `title_draw_order`;
* the Start-transition mask rows at the first, two intermediate and the last
  drawn frame, from the measured `start_transition_mask` table - the live
  quads must cover exactly the measured `[0, top_mask_end]` and
  `[bottom_mask_start, 223]` rows, so the reveal is proved against MAME's
  per-frame measurement rather than against the runtime's own formula;
* all three cursor-intro frames, from `start_transition_intro`;
* both live marker objects at Warrior, Schaefer, Hunter and Linn, from the
  per-position `marker_objects` rectangles MAME measured;
* the confirmation blink, whose visible and blank frames follow the measured
  `input_to_first_blink_frames` latency and four-frame period, anchored to
  the confirm input edge (the confirm clock leads frames-since-input by one).

Every hold also has its frame preamble checked: the system clip, user clip and
local coordinate must describe a 352x224 field centred at (176, 112), so a
crop, bar, or shifted origin fails here rather than being read off a picture.

Four negative controls run against a hold that has just passed exactly: one
perturbed vertex, one perturbed colour bank, one transposed command order, and
one perturbed timing anchor.  All four must fail.

One condition is reported as a declared GAP rather than normalised into a
pass: the confirmation shutter is a VDP2 bitmap row blackout and therefore
emits no VDP1 objects, so this instrument cannot prove it.  The Round 1
title holds now compare the two ROM-derived text-line objects (and their
measured retirement) over the native street scene.

Skips cleanly when the private capture or converter payloads are absent.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "build" / "frontend_cram_readback.json"
MANIFEST = ROOT / "data" / "avsp_frontend_assets.json"
INTERACTION = ROOT / "data" / "frontend_interaction.json"
REPORT = ROOT / "data" / "avsp_frontend_object_readback.json"

WIDTH = 352
HEIGHT = 224
SOURCE_WIDTH = 384
CENTRE_X = WIDTH // 2
CENTRE_Y = HEIGHT // 2

# VDP1 command values.
CMD_DISTORTED = 3
CMD_USER_CLIP = 8
CMD_SYSTEM_CLIP = 9
CMD_LOCAL_COORD = 10

# Encounter states, matching CapEncounterState.
MAIN_MENU = 0
START_TRANSITION = 1
CHARACTER_SELECT = 2
CHARACTER_CONFIRM = 3
ROUND_TITLE = 4

# avsp_shot_holds[] in main.c: (encounter state, in-state frame).
HOLDS = (
    (MAIN_MENU, 60),
    (START_TRANSITION, 1), (START_TRANSITION, 10), (START_TRANSITION, 20),
    (START_TRANSITION, 25), (START_TRANSITION, 27), (START_TRANSITION, 28),
    (START_TRANSITION, 29),
    (CHARACTER_SELECT, 1), (CHARACTER_SELECT, 2), (CHARACTER_SELECT, 3),
    (CHARACTER_SELECT, 30), (CHARACTER_SELECT, 60), (CHARACTER_SELECT, 100),
    (CHARACTER_SELECT, 140),
    (CHARACTER_CONFIRM, 1), (CHARACTER_CONFIRM, 10), (CHARACTER_CONFIRM, 20),
    (ROUND_TITLE, 20), (ROUND_TITLE, 60), (ROUND_TITLE, 100),
)
# Palette slots: frontend_palettes[0] is the title scene, [1] the select scene.
TITLE_SCENE = 0
SELECT_SCENE = 1
# generated/avsp_frontend.h: mask cels use sub-bank 14, cursor and intro 15,
# and the title's two source banks map onto 14 and 15 in sorted order.
MASK_SUBBANK = 14
CURSOR_SUBBANK = 15
R1TEXT_SUBBANK = 13
CURSOR_PERIOD = 6
START_MASK_FRAMES = 27
R1TEXT_CLEAR_FRAME = 90


def fit_source_x(source_x: int) -> int:
    """The runtime's horizontal fit, fit_source_x() in avsp_frontend.c."""
    return (source_x * WIDTH) // SOURCE_WIDTH


def expected_quad(source_x: int, source_y: int, width: int,
                  height: int) -> list[int]:
    """Inclusive fitted rectangle in VDP1 local coordinates."""
    left = fit_source_x(source_x) - CENTRE_X
    right = fit_source_x(source_x + width) - 1 - CENTRE_X
    top = source_y - CENTRE_Y
    bottom = source_y + height - 1 - CENTRE_Y
    return [left, top, right, top, right, bottom, left, bottom]


def objects_of(commands):
    """The frontend's own object commands, without Jo's frame scaffolding."""
    return [command for command in commands
            if command["command"] == CMD_DISTORTED and not command["end"]]


def preamble_failures(hold: int, commands):
    failures = []
    found = {}
    for command in commands:
        if command["command"] in (CMD_SYSTEM_CLIP, CMD_USER_CLIP,
                                  CMD_LOCAL_COORD):
            found.setdefault(command["command"], command)
    for name, code, expect in (
            ("system clip", CMD_SYSTEM_CLIP, [WIDTH - 1, HEIGHT - 1]),
            ("user clip", CMD_USER_CLIP, [WIDTH - 1, HEIGHT - 1]),
            ("local coordinate", CMD_LOCAL_COORD, [CENTRE_X, CENTRE_Y])):
        command = found.get(code)
        if command is None:
            failures.append(f"hold {hold}: no {name} command")
            continue
        actual = (command["vertices"][4:6] if code != CMD_LOCAL_COORD
                  else command["vertices"][0:2])
        if actual != expect:
            failures.append(
                f"hold {hold}: {name} is {actual}, expected {expect}")
    return failures


def title_schedule(manifest):
    """The twelve title objects with their converter-assigned sub-banks."""
    order = manifest["object_schedules"]["title_draw_order"]
    banks = sorted({entry["palette_bank"] for entry in order})
    subbanks = {bank: MASK_SUBBANK + index
                for index, bank in enumerate(banks)}
    return [{"source_x": entry["source_x"], "source_y": entry["source_y"],
             "source_width": entry["source_width"],
             "source_height": entry["source_height"],
             "palette_subbank": subbanks[entry["palette_bank"]],
             "scene": TITLE_SCENE}
            for entry in order]


def mask_schedule(manifest, frame: int):
    """Mask bars for one transition frame, from the measured mask table.

    The measured table gives the revealed window as `top_mask_end` and
    `bottom_mask_start`; the covered rows are everything outside it.  The
    runtime emits the top bar first, so the command table holds it last.
    """
    entry = manifest["object_schedules"]["start_transition_mask"][frame]
    top_end = int(entry["top_mask_end"])
    bottom_start = int(entry["bottom_mask_start"])
    bars = []
    if top_end >= 0:
        bars.append((0, top_end + 1))
    if bottom_start <= HEIGHT - 1:
        bars.append((bottom_start, HEIGHT - bottom_start))
    return [{"source_x": 0, "source_y": row, "source_width": SOURCE_WIDTH,
             "source_height": rows, "palette_subbank": MASK_SUBBANK,
             "scene": SELECT_SCENE}
            for row, rows in bars]


def intro_schedule(manifest, index: int):
    entry = manifest["object_schedules"]["start_transition_intro"][index]
    return [{"source_x": entry["source_x"], "source_y": entry["source_y"],
             "source_width": entry["source_width"],
             "source_height": entry["source_height"],
             "palette_subbank": CURSOR_SUBBANK, "scene": SELECT_SCENE}]


def round1_text_schedule(manifest):
    """Both measured Round 1 title text lines, from the converter manifest.

    The runtime draws the first line at the lower depth, so the live command
    table holds the second line first; the shared reversal in
    compare_schedule expresses that.
    """
    return [{"source_x": entry["source_x"], "source_y": entry["source_y"],
             "source_width": entry["source_width"],
             "source_height": entry["source_height"],
             "palette_subbank": R1TEXT_SUBBANK, "scene": SELECT_SCENE}
            for entry in manifest["object_schedules"]["round1_title_text"]]


def cursor_schedule(interaction, cursor: int):
    """Both marker objects at one cursor position, as MAME measured them.

    The runtime emits the border cel before the label cel, so the command
    table holds the label first.  The border cel is the larger rectangle.
    """
    positions = {int(position["index"]): position
                 for position in interaction["cursor_positions"]}
    markers = sorted(positions[cursor]["marker_objects"],
                     key=lambda marker: -int(marker["width"]))
    return [{"source_x": int(marker["x"]), "source_y": int(marker["y"]),
             "source_width": int(marker["width"]),
             "source_height": int(marker["height"]),
             "palette_subbank": CURSOR_SUBBANK, "scene": SELECT_SCENE}
            for marker in markers]


def confirm_cursor_visible(interaction, frames_since_input: int) -> bool:
    """The measured confirmation blink: latency, then a four-frame period.

    MAME measured the markers first vanishing `input_to_first_blink_frames`
    frames after the confirm input, then alternating every four frames, and
    its +1-frame edge mutation control failed as required, so the phase is
    anchored to the input edge rather than to a state counter.
    """
    latency = int(interaction["confirmation"]["input_to_first_blink_frames"])
    if frames_since_input < latency:
        return True
    return (((frames_since_input - latency) // 4) % 2) == 1


def compare_schedule(hold: int, objects, schedule, palette_ids, label: str,
                     vertex_shift: int = 0, colour_shift: int = 0,
                     reverse: bool = True):
    """Geometry, colour and order as three independent results."""
    expected = list(reversed(schedule)) if reverse else list(schedule)
    result = {"label": label, "expected": len(expected),
              "observed": len(objects), "geometry": 0, "colour": 0,
              "order_exact": False, "failures": []}
    if len(objects) != len(expected):
        result["failures"].append(
            f"hold {hold} ({label}): {len(objects)} live objects, schedule "
            f"has {len(expected)}")
        return result
    order_ok = True
    for index, (command, entry) in enumerate(zip(objects, expected)):
        want = expected_quad(entry["source_x"], entry["source_y"],
                             entry["source_width"], entry["source_height"])
        if vertex_shift and index == 0:
            want = list(want)
            want[1] += vertex_shift
        if command["vertices"] == want:
            result["geometry"] += 1
        else:
            order_ok = False
            if len(result["failures"]) < 4:
                result["failures"].append(
                    f"hold {hold} ({label}) object {index}: live quad "
                    f"{command['vertices']} != fitted source rectangle {want}")
        want_colour = (palette_ids[entry["scene"]] * 256
                       + 16 * entry["palette_subbank"])
        if colour_shift and index == 0:
            want_colour += colour_shift
        if command["colour"] == want_colour:
            result["colour"] += 1
        else:
            order_ok = False
            if len(result["failures"]) < 6:
                result["failures"].append(
                    f"hold {hold} ({label}) object {index}: colour bank "
                    f"0x{command['colour']:04X} != expected "
                    f"0x{want_colour:04X}")
    result["order_exact"] = order_ok
    return result


def schedule_for(state: int, timer: int, cursor: int, manifest, interaction):
    """The ROM-derived schedule a hold must reproduce, or a declared gap."""
    if state == MAIN_MENU:
        return "title", title_schedule(manifest)
    if state == START_TRANSITION:
        if timer < START_MASK_FRAMES:
            return f"start mask frame {timer}", mask_schedule(manifest, timer)
        index = timer - START_MASK_FRAMES
        return f"cursor intro cel {index}", intro_schedule(manifest, index)
    if state == CHARACTER_SELECT:
        return (f"select cursor {cursor} frame {timer}",
                cursor_schedule(interaction, cursor))
    if state == CHARACTER_CONFIRM:
        # cap_confirm_character() zeroes the timer on the confirm step and
        # cap_update_encounter() increments it in that same step, so the
        # rendered timer leads frames-since-input by one.
        frames_since_input = timer - 1
        if confirm_cursor_visible(interaction, frames_since_input):
            return (f"confirm blink visible frame {frames_since_input}",
                    cursor_schedule(interaction, cursor))
        return f"confirm blink blank frame {frames_since_input}", []
    if state == ROUND_TITLE:
        # The measured text lines stay up until the instant tilemap clear at
        # frame 90; the street scene behind them is the native renderer, not
        # a frontend object schedule.
        if timer < R1TEXT_CLEAR_FRAME:
            return (f"round 1 title text frame {timer}",
                    round1_text_schedule(manifest))
        return f"round 1 title cleared frame {timer}", []
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, default=CAPTURE)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--interaction", type=Path, default=INTERACTION)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()

    if not args.capture.is_file() or not args.manifest.is_file():
        print("frontend VDP1 objects: SKIPPED - live capture absent")
        return 0
    capture = json.loads(args.capture.read_text(encoding="ascii"))
    sample = next(iter(capture["holds"].values()))
    if "vdp1" not in sample:
        print("frontend VDP1 objects: SKIPPED - capture predates VDP1 "
              "recording")
        return 0
    if "encounter_timer" not in sample["diagnostics"]:
        print("frontend VDP1 objects: SKIPPED - capture predates the live "
              "encounter-timer diagnostic")
        return 0
    manifest = json.loads(args.manifest.read_text(encoding="ascii"))
    interaction = json.loads(args.interaction.read_text(encoding="ascii"))

    failures = []
    gaps = []
    report_holds = []
    border_addresses = {}
    for key in sorted(capture["holds"], key=int):
        hold = int(key)
        record = capture["holds"][key]
        commands = record["vdp1"]
        diagnostics = record["diagnostics"]
        objects = objects_of(commands)
        state = diagnostics["encounter_state"]
        if state == ROUND_TITLE:
            # Once the native street scene pops in, the gameplay renderer
            # shares the frame: its unequal-scale sprites also draw as
            # distorted commands, but in their own palette blocks. The
            # frontend's text objects are the ones in the select block.
            select_id = diagnostics[f"frontend_palette_{SELECT_SCENE}_id"]
            objects = [command for command in objects
                       if select_id * 256 <= command["colour"]
                       < (select_id + 1) * 256]
        timer = diagnostics["encounter_timer"]
        cursor = diagnostics["selection_cursor"]
        palette_ids = {
            TITLE_SCENE: diagnostics[f"frontend_palette_{TITLE_SCENE}_id"],
            SELECT_SCENE: diagnostics[f"frontend_palette_{SELECT_SCENE}_id"],
        }
        entry = {
            "hold": hold,
            "encounter_state": state,
            "hold_timer": diagnostics["hold_timer"],
            "encounter_timer": timer,
            "selection_cursor": cursor,
            "commands_total": len(commands),
            "objects": len(objects),
            "runtime_command_counter": diagnostics["frontend_commands"],
        }
        failures.extend(preamble_failures(hold, commands))

        # Timing: the schedule is defined at an exact (state, in-state frame),
        # and the model's own encounter timer must agree with the frame the
        # route counted, or every frame-indexed schedule above is misaligned.
        # The agreement is state-specific: the title never starts the clock,
        # the transition, select and round-title states count in-state frames
        # exactly, and the confirm clock leads by one because the confirm
        # step both zeroes and increments it.
        want_state, want_timer = HOLDS[hold]
        want_clock = (0 if want_state == MAIN_MENU
                      else want_timer + 1 if want_state == CHARACTER_CONFIRM
                      else want_timer)
        entry["timing_exact"] = (state == want_state
                                 and diagnostics["hold_timer"] == want_timer
                                 and timer == want_clock)
        if not entry["timing_exact"]:
            failures.append(
                f"hold {hold}: held at state {state} in-state frame "
                f"{diagnostics['hold_timer']} encounter timer {timer}, "
                f"schedule expects state {want_state} frame {want_timer} "
                f"clock {want_clock}")
        if len(objects) != diagnostics["frontend_commands"]:
            failures.append(
                f"hold {hold}: {len(objects)} live object commands but the "
                f"runtime counted {diagnostics['frontend_commands']}")

        label, schedule = schedule_for(state, timer, cursor, manifest,
                                       interaction)
        if schedule is None:
            failures.append(f"hold {hold}: no schedule for state {state}")
        else:
            result = compare_schedule(hold, objects, schedule, palette_ids,
                                      label)
            entry["comparison"] = result
            failures.extend(result["failures"])
        if state == CHARACTER_CONFIRM:
            gaps.append(
                f"hold {hold}: the confirmation shutter is a VDP2 bitmap row "
                "blackout, so this VDP1 instrument proves only the marker "
                "blink at this hold, not the shutter band")
        # The border cel cycles with period six; equal phases must reuse the
        # same texture and different phases must not.
        if state == CHARACTER_SELECT and len(objects) == 2:
            border_addresses.setdefault(timer % CURSOR_PERIOD, []).append(
                (hold, objects[1]["character_address"]))
        report_holds.append(entry)

    for phase, seen in sorted(border_addresses.items()):
        if len({address for _, address in seen}) != 1:
            failures.append(
                f"cursor cycle phase {phase} used {len(seen)} different "
                "border textures")
    distinct = {phase: seen[0][1] for phase, seen in border_addresses.items()}
    if len(set(distinct.values())) != len(distinct):
        failures.append(
            "different cursor cycle phases shared a border texture")

    # Negative controls against hold 0, which has just passed exactly.
    record = capture["holds"]["0"]
    objects = objects_of(record["vdp1"])
    schedule = title_schedule(manifest)
    palette_ids = {
        TITLE_SCENE:
            record["diagnostics"][f"frontend_palette_{TITLE_SCENE}_id"],
        SELECT_SCENE:
            record["diagnostics"][f"frontend_palette_{SELECT_SCENE}_id"],
    }
    controls = {
        "perturbed_vertex": compare_schedule(
            0, objects, schedule, palette_ids, "control", vertex_shift=1),
        "perturbed_colour_bank": compare_schedule(
            0, objects, schedule, palette_ids, "control", colour_shift=16),
        "transposed_order": compare_schedule(
            0, objects, schedule, palette_ids, "control", reverse=False),
        "perturbed_timing": HOLDS[0][1] + 1
        != record["diagnostics"]["hold_timer"],
    }
    if controls["perturbed_vertex"]["geometry"] == len(schedule):
        failures.append("negative control: a perturbed vertex still matched")
    if controls["perturbed_colour_bank"]["colour"] == len(schedule):
        failures.append("negative control: a perturbed colour bank still "
                        "matched")
    if controls["transposed_order"]["order_exact"]:
        failures.append("negative control: the transposed draw order still "
                        "matched")
    if not controls["perturbed_timing"]:
        failures.append("negative control: a perturbed timing anchor still "
                        "matched")

    if failures:
        for line in failures:
            print(f"frontend VDP1 objects: FAIL - {line}")
        return 1

    proven = [entry for entry in report_holds if "comparison" in entry]
    objects_proven = sum(entry["comparison"]["expected"] for entry in proven)
    args.report.write_text(json.dumps({
        "schema": 2,
        "classification": "Live Saturn VDP1 command-table evidence for the "
                          "frontend objects; command words, counts and "
                          "verdicts only, no ROM-derived graphics payload",
        "instrument": "pinned Yaba Sanshiro MCP debug server, "
                      "-FrontendShotTest holds",
        "oracles": ["data/avsp_frontend_assets.json",
                    "data/frontend_interaction.json"],
        "geometry_rule": "each object is an inclusive four-point quad over the "
                         "fitted source rectangle, left = (x * 352) / 384",
        "colour_rule": "CMDCOLR is Jo's colour-table index, "
                       "256 * palette_id + 16 * subbank",
        "order_rule": "VDP1 draws in address order while the runtime emits "
                      "increasing depth, so frontend objects appear reversed "
                      "with respect to the schedule",
        "timing_rule": "the live encounter timer, the route's in-state frame "
                       "count and the schedule frame must be the same number, "
                       "and the six-frame cursor border cycle is proved by "
                       "texture address",
        "verdict": "PASS WITH DECLARED GAPS" if gaps else "PASS",
        "proven_holds": len(proven),
        "proven_objects": objects_proven,
        "proven_schedules": [entry["comparison"]["label"] for entry in proven],
        "cursor_cycle_phases_proved": sorted(border_addresses),
        "declared_gaps": gaps,
        "negative_controls": {
            "perturbed_vertex_geometry_matches":
                controls["perturbed_vertex"]["geometry"],
            "perturbed_colour_bank_colour_matches":
                controls["perturbed_colour_bank"]["colour"],
            "transposed_order_exact":
                controls["transposed_order"]["order_exact"],
            "perturbed_timing_rejected": controls["perturbed_timing"],
            "required": "each control must fail",
        },
        "holds": report_holds,
    }, indent=1, sort_keys=True) + "\n", encoding="ascii")
    print(f"frontend VDP1 objects: PASS - {len(report_holds)} holds, "
          f"352x224 clip and (176,112) origin exact, "
          f"{len(proven)} schedule(s) / {objects_proven} objects exact in "
          "geometry, colour and order, 4 negative controls failed as required")
    for line in gaps:
        print(f"frontend VDP1 objects: GAP - {line}")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
