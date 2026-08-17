"""Validate and decode one stable CPS2 alien actor across exact action states.

The object list is rebuilt and palette-sorted every frame, so palette number and
object offset are not actor identities.  This analysis uses the native actor slot
at FF A000, its health/state fields, and CPS scroll registers to select the
corresponding rendered commands.  It emits metadata and previews only; the ROM
and private captures remain local and are never copied into the repository.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_avspu_stage1 as avsp  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = PROJECT_ROOT / ".deps" / "mame" / "enemy_actions"
ROUTE_ROOT = PROJECT_ROOT / ".deps" / "mame" / "captures"
OUTPUT_PATH = PROJECT_ROOT / "data" / "enemy_action_capture.json"
PREVIEW_ROOT = CAPTURE_ROOT / "analysis"
FIRST_FRAME = 4080
LAST_FRAME = 6200
ACTOR_ADDRESS = 0xFFA000
WORKRAM_START = 0xFF8000
ACTOR_OFFSET = ACTOR_ADDRESS - WORKRAM_START
# The largest verified attack extends 133 pixels left of the logical pivot.
# A 288-pixel VDP1 cel preserves it with margin and remains 8-pixel aligned.
CANVAS_SIZE = (288, 192)

CLIPS = (
    ("walk", 4214, 4252, "palette17_actor"),
    ("attack", 4253, 4372, "palette17_actor"),
    ("hit", 5191, 5226, "nearest_actor"),
    ("ko", 5330, 5469, "nearest_actor"),
)


def read_words(path: Path) -> list[int]:
    return [
        int(line.split("\t")[1], 16)
        for line in path.read_text(encoding="utf-8").splitlines()[1:]
        if line
    ]


def signed_word(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def actor_state(frame: int) -> dict[str, int]:
    data = (CAPTURE_ROOT / f"workram_{frame:05d}.bin").read_bytes()
    if len(data) != 0x8000:
        raise ValueError(f"frame {frame}: expected a 32 KiB work-RAM capture")
    slot = data[ACTOR_OFFSET:ACTOR_OFFSET + 0x80]

    def word(offset: int) -> int:
        return int.from_bytes(slot[offset:offset + 2], "big")

    registers = read_words(CAPTURE_ROOT / f"cps_a_regs_{frame:05d}.tsv")
    world_x = word(0x10)
    world_y = word(0x14)
    world_z = word(0x18)
    return {
        "active": slot[0],
        "actor_id": slot[2],
        "action": word(0x06),
        "state": word(0x0C),
        "substate": word(0x0E),
        "world_x": world_x,
        "world_y": world_y,
        "world_z": world_z,
        "screen_x": world_x - registers[8],
        "screen_bottom": 186 - (world_y - world_z),
        "animation": word(0x1E),
        "animation_timer": word(0x2A),
        "health": signed_word(word(0x40)),
        "latched_health": signed_word(word(0x42)),
        "maximum_health": word(0x44),
        "scroll_x": registers[8],
        "scroll_y": registers[9],
    }


def sample_bank(frame: int) -> int:
    line = (CAPTURE_ROOT / "samples.tsv").read_text(
        encoding="utf-8").splitlines()[frame - FIRST_FRAME + 1]
    recorded_frame, bank, _, _ = line.split("\t")
    if int(recorded_frame) != frame or int(bank) not in (1, 2):
        raise ValueError(f"frame {frame}: invalid active-bank metadata")
    return int(bank)


def frame_entries(frame: int) -> list[dict[str, int]]:
    words = read_words(CAPTURE_ROOT / f"objram_active_{frame:05d}.tsv")
    return avsp.decode_object_entries(words)


def alien_run_candidates(frame: int) -> list[list[dict[str, int]]]:
    candidates = []
    for colour in range(16, 20):
        for run in avsp.contiguous_palette_runs(frame_entries(frame), colour):
            bounds = avsp.command_bounds(run)
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            has_alien_art = any(
                17000 <= command["tile_code"] <= 22000 or
                59000 <= command["tile_code"] <= 65000
                for command in run)
            if (has_alien_art and 64 <= width <= CANVAS_SIZE[0] and
                    16 <= height <= 176 and bounds[0] < 544 and
                    bounds[2] > -160 and bounds[1] < 288 and bounds[3] > -64):
                candidates.append(run)
    return candidates


def select_palette17_actor(frame: int, state: dict[str, int]) -> list[dict[str, int]]:
    """Select the actor by its logical X before nearby same-palette commands."""
    screen_x = state["screen_x"]
    palette_commands = [
        command for command in frame_entries(frame)
        if command["colour"] == 17 and
        command["tile_code"] != 18944 and command["tile_code"] < 59000 and
        command["screen_y"] + command["height"] <= 191
    ]
    commands = [
        command for command in palette_commands
        if abs(command["screen_x"] + command["width"] // 2 - screen_x) <= 90
    ]
    if not commands:
        raise ValueError(f"frame {frame}: actor-guided palette 17 selection is empty")
    bounds = avsp.command_bounds(commands)
    if bounds[2] - bounds[0] > CANVAS_SIZE[0]:
        raise ValueError(f"frame {frame}: palette 17 actor exceeds the exact canvas")
    return sorted(commands, key=lambda command: command["offset"])


def select_nearest_actor(frame: int, state: dict[str, int]) -> list[dict[str, int]]:
    expected_centre = state["screen_x"] + 20
    expected_bottom = state["screen_bottom"]
    candidates = alien_run_candidates(frame)
    if not candidates:
        raise ValueError(f"frame {frame}: no alien object-run candidates")

    def score(run: list[dict[str, int]]) -> tuple[int, int, int]:
        left, top, right, bottom = avsp.command_bounds(run)
        centre = (left + right) // 2
        return (
            abs(centre - expected_centre) + 4 * abs(bottom - expected_bottom),
            abs(centre - expected_centre),
            min(command["offset"] for command in run),
        )

    selected = min(candidates, key=score)
    # In the most crowded KO hold the CPS2 list deliberately omits this actor
    # on alternating frames.  Treat an implausible match as an empty source
    # frame instead of silently splicing in a nearby alien.
    return selected if score(selected)[0] <= 50 else []


def render_actor(frame: int, state: dict[str, int],
                 commands: list[dict[str, int]]) -> tuple[Image.Image, bytes, int]:
    if not commands:
        return (Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0)),
                bytes(CANVAS_SIZE[0] * CANVAS_SIZE[1] // 2), -1)
    colour = commands[0]["colour"]
    if any(command["colour"] != colour for command in commands):
        raise ValueError(f"frame {frame}: one alien actor unexpectedly spans palettes")
    palette = avsp.load_palette_path(CAPTURE_ROOT / f"palette_{frame:05d}.tsv")
    source_name = f"../enemy_actions/objram_active_{frame:05d}.tsv"
    layers, palettes = avsp.exact_object_layers(
        GFX, palette, frame, sample_bank(frame),
        [command["offset"] for command in commands],
        pivot=(state["screen_x"], state["screen_bottom"]),
        source_filename=source_name, canvas_size=CANVAS_SIZE)
    layer = layers[colour]
    packed = avsp.pack_4bpp(layer)
    rgb = [(0, 0, 0)] + palettes[colour]
    layer.putpalette([component for value in rgb for component in value] +
                     [0] * ((256 - len(rgb)) * 3))
    layer.info["transparency"] = 0
    preview = layer.convert("RGBA")
    bbox = preview.getbbox()
    if bbox is None:
        raise ValueError(f"frame {frame}: selected actor rendered empty")
    if bbox[0] == 0 or bbox[2] == CANVAS_SIZE[0] or bbox[1] == 0 or bbox[3] == CANVAS_SIZE[1]:
        raise ValueError(f"frame {frame}: selected actor touches the canvas edge")
    return preview, packed, colour


def make_contact_sheet(name: str, samples: list[tuple[int, Image.Image]]) -> None:
    tile_width, tile_height = 168, 120
    columns = 5
    rows = (len(samples) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    for index, (frame, image) in enumerate(samples):
        x = (index % columns) * tile_width
        y = (index // columns) * tile_height
        thumb = image.copy()
        thumb.thumbnail((160, 96), Image.Resampling.NEAREST)
        sheet.paste(thumb, (x + (160 - thumb.width) // 2, y + 16), thumb)
        draw.text((x + 4, y + 2), f"{name} {frame}", fill=(240, 240, 240))
    sheet.save(PREVIEW_ROOT / f"{name}_contact.png")


def verify_route_prefix() -> list[dict[str, object]]:
    checks = []
    for frame in (4080, 4164, 4200):
        for kind, old_name, new_name in (
                ("object_ram", f"objram_active_{frame}.tsv",
                 f"objram_active_{frame:05d}.tsv"),
                ("palette", f"palette_{frame}.tsv", f"palette_{frame:05d}.tsv")):
            old_data = (ROUTE_ROOT / old_name).read_bytes()
            new_data = (CAPTURE_ROOT / new_name).read_bytes()
            if old_data != new_data:
                raise ValueError(f"frame {frame}: enemy probe diverged from verified {kind}")
            checks.append({
                "frame": frame,
                "kind": kind,
                "sha256": hashlib.sha256(new_data).hexdigest(),
            })
    return checks


def analyze_clip(name: str, first: int, last: int,
                 selector_name: str) -> dict[str, object]:
    timeline = []
    pose_indexes: dict[str, int] = {}
    previews = []
    preview_stride = max(1, (last - first + 1) // 14)
    for frame in range(first, last + 1):
        state = actor_state(frame)
        commands = (select_palette17_actor(frame, state)
                    if selector_name == "palette17_actor"
                    else select_nearest_actor(frame, state))
        preview, packed, colour = render_actor(frame, state, commands)
        digest = hashlib.sha256(packed).hexdigest()
        pose_index = pose_indexes.setdefault(digest, len(pose_indexes))
        bounds = avsp.command_bounds(commands) if commands else None
        timeline.append({
            "frame": frame,
            "pose": pose_index,
            "cps2_palette": colour if colour >= 0 else None,
            "object_offsets": [command["offset"] for command in commands],
            "source_bounds": list(bounds) if bounds else None,
            "source_visible": bool(commands),
            "actor_screen_x": state["screen_x"],
            "actor_screen_bottom": state["screen_bottom"],
            "action": state["action"],
            "animation": state["animation"],
            "health": state["health"],
        })
        if ((frame - first) % preview_stride == 0 or frame == last):
            previews.append((frame, preview))
    make_contact_sheet(name, previews)
    return {
        "name": name,
        "start_frame": first,
        "end_frame": last,
        "frame_count": last - first + 1,
        "unique_poses": len(pose_indexes),
        "source_omitted_frames": sum(
            not frame["source_visible"] for frame in timeline),
        "canvas": list(CANVAS_SIZE),
        "selector": selector_name,
        "timeline": timeline,
    }


def verify_actor_transitions() -> dict[str, object]:
    health_events = []
    prior = actor_state(FIRST_FRAME)["health"]
    for frame in range(FIRST_FRAME + 1, LAST_FRAME + 1):
        current = actor_state(frame)["health"]
        if current != prior:
            health_events.append({"frame": frame, "from": prior, "to": current})
            prior = current
    expected = [
        {"frame": 5190, "from": 87, "to": 63},
        {"frame": 5236, "from": 63, "to": 39},
        {"frame": 5283, "from": 39, "to": 8},
        {"frame": 5329, "from": 8, "to": -1},
        {"frame": 5471, "from": -1, "to": 87},
        {"frame": 6153, "from": 87, "to": 0},
    ]
    if health_events != expected:
        raise ValueError(f"unexpected actor health events: {health_events}")
    if actor_state(5330)["active"] != 2 or actor_state(5469)["active"] != 2:
        raise ValueError("confirmed KO visibility interval is not active")
    if actor_state(5470)["active"] != 0:
        raise ValueError("confirmed KO actor did not disappear at frame 5470")
    return {
        "actor_address": f"0x{ACTOR_ADDRESS:06x}",
        "actor_id": actor_state(4200)["actor_id"],
        "health_word_offset": "0x40",
        "latched_health_word_offset": "0x42",
        "maximum_health_word_offset": "0x44",
        "health_events": health_events,
        "confirmed_ko_visible_start": 5330,
        "confirmed_ko_visible_end": 5469,
        "confirmed_ko_frame_count": 140,
        "disappears_at_frame": 5470,
    }


def main() -> None:
    if not CAPTURE_ROOT.is_dir():
        raise FileNotFoundError("run capture_enemy_actions.ps1 first")
    sample_lines = (CAPTURE_ROOT / "samples.tsv").read_text(
        encoding="utf-8").splitlines()
    if len(sample_lines) != LAST_FRAME - FIRST_FRAME + 2:
        raise ValueError("enemy capture does not contain the complete dense frame range")
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": 1,
        "source": "user-supplied avspu ROM set captured with MAME 0.289",
        "capture_scope": [FIRST_FRAME, LAST_FRAME],
        "probe": {
            "enemy_state_modified": False,
            "player_health_only_frozen": True,
            "player_health_address": "0xff83c1",
            "note": "The P1 health freeze prevents Continue transitions; all enemy state remains native.",
        },
        "route_prefix_checks": verify_route_prefix(),
        "actor": verify_actor_transitions(),
        "clips": [analyze_clip(*clip) for clip in CLIPS],
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "Validated actor FF A000: " +
        ", ".join(f"{clip['name']}={clip['frame_count']}f/{clip['unique_poses']}p"
                  for clip in report["clips"]))


GFX = avsp.load_gfx_region()


if __name__ == "__main__":
    main()
