"""Validate and decode the two native CPS2 Stage 1 Stalker actor slots.

The Chrysalis room uses a 64-pixel object-space origin that is not present in
the street capture.  Actor identity therefore comes from work RAM first, then
palette-17 object commands are assigned to the nearest corrected actor pivot.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_avspu_stage1 as avsp  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "stalker_actions"
OUTPUT_PATH = ROOT / "data" / "stalker_action_capture.json"
PREVIEW_ROOT = CAPTURE_ROOT / "analysis"
FIRST_FRAME = 5520
LAST_FRAME = 7800
WORKRAM_START = 0xFF8000
STALKER_A = 0xFFA240
STALKER_B = 0xFFA300
CPS2_OBJECT_ORIGIN_X = 64
CANVAS_SIZE = (288, 192)
CLIPS = (
    ("walk", STALKER_B, 6007, 6063),
    ("attack", STALKER_A, 6888, 6904),
    # No nonlethal Stalker damage occurred in the natural route.  These two
    # exact frames are the visible onset of its captured KO response and are
    # kept explicit rather than substituting street-alien artwork.
    ("hit", STALKER_A, 7512, 7513),
    ("ko", STALKER_A, 7512, 7668),
)


def read_words(path: Path) -> list[int]:
    return [
        int(line.split("\t")[1], 16)
        for line in path.read_text(encoding="utf-8").splitlines()[1:]
        if line
    ]


def signed_word(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def actor_state(frame: int, address: int) -> dict[str, int]:
    data = (CAPTURE_ROOT / f"workram_{frame:05d}.bin").read_bytes()
    if len(data) != 0x8000:
        raise ValueError(f"frame {frame}: expected a 32 KiB work-RAM capture")
    offset = address - WORKRAM_START
    slot = data[offset:offset + 0x80]

    def word(field: int) -> int:
        return int.from_bytes(slot[field:field + 2], "big")

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
        "screen_x": world_x - registers[8] - CPS2_OBJECT_ORIGIN_X,
        "screen_bottom": 186 - (world_y - world_z),
        "animation": word(0x1E),
        "animation_timer": word(0x2A),
        "health": signed_word(word(0x40)),
        "maximum_health": word(0x44),
        "scroll_x": registers[8],
    }


def sample_banks() -> dict[int, int]:
    result = {}
    lines = (CAPTURE_ROOT / "samples.tsv").read_text(
        encoding="utf-8").splitlines()
    if len(lines) != LAST_FRAME - FIRST_FRAME + 2:
        raise ValueError("Stalker capture does not contain the dense frame range")
    for expected, line in zip(range(FIRST_FRAME, LAST_FRAME + 1), lines[1:]):
        frame_text, bank_text, _, _ = line.split("\t")
        frame = int(frame_text)
        bank = int(bank_text)
        if frame != expected or bank not in (1, 2):
            raise ValueError(f"frame {expected}: invalid active-bank metadata")
        result[frame] = bank
    return result


def frame_entries(frame: int) -> list[dict[str, int]]:
    return avsp.decode_object_entries(read_words(
        CAPTURE_ROOT / f"objram_active_{frame:05d}.tsv"))


def select_actor(frame: int, address: int) -> list[dict[str, int]]:
    target = actor_state(frame, address)["screen_x"]
    rival_address = STALKER_B if address == STALKER_A else STALKER_A
    rival = actor_state(frame, rival_address)["screen_x"]
    selected = []
    for command in frame_entries(frame):
        if (command["colour"] != 17 or
                not 16000 <= command["tile_code"] < 18000):
            continue
        centre = command["screen_x"] + command["width"] // 2
        target_distance = abs(centre - target)
        if (target_distance <= abs(centre - rival) and target_distance <= 180):
            selected.append(command)
    return sorted(selected, key=lambda command: command["offset"])


def render_actor(frame: int, state: dict[str, int],
                 commands: list[dict[str, int]], bank: int
                 ) -> tuple[Image.Image, bytes]:
    if not commands:
        blank = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        return blank, bytes(CANVAS_SIZE[0] * CANVAS_SIZE[1] // 2)
    bounds = avsp.command_bounds(commands)
    if bounds[2] - bounds[0] > CANVAS_SIZE[0] or bounds[3] - bounds[1] > CANVAS_SIZE[1]:
        raise ValueError(f"frame {frame}: Stalker exceeds the exact canvas")
    palette = avsp.load_palette_path(CAPTURE_ROOT / f"palette_{frame:05d}.tsv")
    layers, palettes = avsp.exact_object_layers(
        GFX, palette, frame, bank,
        [command["offset"] for command in commands],
        pivot=(state["screen_x"], state["screen_bottom"]),
        source_filename=f"../stalker_actions/objram_active_{frame:05d}.tsv",
        canvas_size=CANVAS_SIZE)
    if 17 not in layers:
        raise ValueError(f"frame {frame}: selected Stalker has no palette-17 layer")
    layer = layers[17]
    packed = avsp.pack_4bpp(layer)
    rgb = [(0, 0, 0)] + palettes[17]
    layer.putpalette([component for value in rgb for component in value] +
                     [0] * ((256 - len(rgb)) * 3))
    layer.info["transparency"] = 0
    return layer.convert("RGBA"), packed


def make_contact_sheet(name: str, samples: list[tuple[int, Image.Image]]) -> None:
    width, height, columns = 168, 120, 5
    rows = (len(samples) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * width, rows * height), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    for index, (frame, actor) in enumerate(samples):
        x = index % columns * width
        y = index // columns * height
        thumb = actor.copy()
        thumb.thumbnail((160, 96), Image.Resampling.NEAREST)
        sheet.paste(thumb, (x + (160 - thumb.width) // 2, y + 16), thumb)
        draw.text((x + 4, y + 2), f"{name} {frame}", fill=(240, 240, 240))
    sheet.save(PREVIEW_ROOT / f"{name}_contact.png")


def analyze_clip(name: str, address: int, first: int, last: int,
                 banks: dict[int, int]) -> dict[str, object]:
    timeline = []
    poses: dict[str, int] = {}
    previews = []
    stride = max(1, (last - first + 1) // 14)
    for frame in range(first, last + 1):
        state = actor_state(frame, address)
        commands = select_actor(frame, address)
        preview, packed = render_actor(frame, state, commands, banks[frame])
        digest = hashlib.sha256(packed).hexdigest()
        pose = poses.setdefault(digest, len(poses))
        bounds = avsp.command_bounds(commands) if commands else None
        timeline.append({
            "frame": frame,
            "pose": pose,
            "cps2_palette": 17 if commands else None,
            "object_offsets": [command["offset"] for command in commands],
            "source_bounds": list(bounds) if bounds else None,
            "source_visible": bool(commands),
            "actor_screen_x": state["screen_x"],
            "actor_screen_bottom": state["screen_bottom"],
            "action": state["action"],
            "animation": state["animation"],
            "health": state["health"],
            "active_object_bank": banks[frame],
        })
        if (frame - first) % stride == 0 or frame == last:
            previews.append((frame, preview))
    make_contact_sheet(name, previews)
    return {
        "name": name,
        "actor_address": f"0x{address:06x}",
        "start_frame": first,
        "end_frame": last,
        "frame_count": last - first + 1,
        "unique_poses": len(poses),
        "source_omitted_frames": sum(not item["source_visible"] for item in timeline),
        "canvas": list(CANVAS_SIZE),
        "timeline": timeline,
    }


def validate_contract() -> dict[str, object]:
    for address in (STALKER_A, STALKER_B):
        initial = actor_state(FIRST_FRAME, address)
        if (initial["active"], initial["actor_id"], initial["health"]) != (1, 0, 24):
            raise ValueError(f"{address:#x}: initial Stalker identity changed")
    if any(actor_state(frame, STALKER_B)["action"] != 1024
           for frame in range(6007, 6064)):
        raise ValueError("clean Stalker walk interval changed")
    if any(actor_state(frame, STALKER_A)["action"] != 5632
           for frame in range(6888, 6905)):
        raise ValueError("clean Stalker attack interval changed")
    health_lines = (CAPTURE_ROOT / "samples.tsv").read_text(
        encoding="utf-8").splitlines()
    contact_health = int(health_lines[6530 - FIRST_FRAME + 1].split("\t")[3])
    if actor_state(6530, STALKER_A)["action"] != 5632 or contact_health != 89:
        raise ValueError("natural Stalker attack-contact evidence changed")
    before = actor_state(7511, STALKER_A)["health"]
    after = actor_state(7512, STALKER_A)["health"]
    if (before, after) != (24, 0):
        raise ValueError("captured Stalker KO transition changed")
    return {
        "actor_addresses": [f"0x{STALKER_A:06x}", f"0x{STALKER_B:06x}"],
        "actor_id": 0,
        "cps2_palette": 17,
        "initial_health": 24,
        "walk_action": 1024,
        "walk_frames": 57,
        "attack_action": 5632,
        "attack_frames": 17,
        "attack_contact_evidence": {
            "frame": 6530,
            "action_offset": 0,
            "player_health_from": 101,
            "player_health_to": 89,
            "damage": 12,
        },
        "ko_health_event": {"frame": 7512, "from": 24, "to": 0},
        "hit_note": "The hit clip is the exact two-frame visible KO onset; a natural nonlethal Stalker hit remains uncaptured.",
    }


def main() -> None:
    if not CAPTURE_ROOT.is_dir():
        raise FileNotFoundError("run capture_stalker_actions.ps1 first")
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    banks = sample_banks()
    report = {
        "schema": 1,
        "source": "user-supplied avspu ROM set captured with MAME 0.289",
        "capture_scope": [FIRST_FRAME, LAST_FRAME],
        "probe": {
            "neutral_scope": [5520, 7000],
            "ordinary_input_damage_scope": [7001, 7800],
            "enemy_state_modified": False,
            "player_health_only_frozen": True,
        },
        "actor": validate_contract(),
        "clips": [analyze_clip(*clip, banks) for clip in CLIPS],
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Validated native Stalkers: " + ", ".join(
        f"{clip['name']}={clip['frame_count']}f/{clip['unique_poses']}p"
        for clip in report["clips"]))


GFX = avsp.load_gfx_region()


if __name__ == "__main__":
    main()
