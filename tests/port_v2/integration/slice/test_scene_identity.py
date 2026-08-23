#!/usr/bin/env python3
"""Source-bound actor identity contract for INTEGRATE-03 correction 2."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    capture = json.loads(
        (ROOT / "data/enemy_action_capture.json").read_text(encoding="utf-8")
    )
    states = json.loads(
        (ROOT / "data/avsp_table_set_states_verification.json").read_text(
            encoding="utf-8"
        )
    )
    clips = {clip["name"]: clip for clip in capture["clips"]}
    require(capture["actor"]["actor_address"] == "0xffa000" and
            capture["actor"]["actor_id"] == 31,
            "HIT/KO visual capture is not the intended actor slot/class")
    require(states["anchor"]["actor_address"] == "0xffa000" and
            states["anchor"]["hit_clip"]["class"] == "0x1F" and
            states["anchor"]["ko_clip"]["class"] == "0x1F" and
            set(states["anchor"]["hit_clip"]["field_histograms"]
                ["table_set"]) == {"0x00130AC8"} and
            set(states["anchor"]["ko_clip"]["field_histograms"]
                ["table_set"]) == {"0x00130AC8"},
            "HIT/KO semantic records are not bound to class 0x1F")
    palettes = {
        name: {sample["cps2_palette"] for sample in clips[name]["timeline"]
               if sample["cps2_palette"] is not None}
        for name in ("walk", "hit", "ko")
    }
    require(palettes == {"walk": {17}, "hit": {19}, "ko": {16, 18}},
            f"street-alien source palette transitions drifted: {palettes}")
    ko_palette_18 = [sample for sample in clips["ko"]["timeline"]
                     if sample["cps2_palette"] == 18]
    require(ko_palette_18 and
            all(sample["pose"] in (5, 6) for sample in ko_palette_18) and
            all(sample["object_offsets"] for sample in ko_palette_18),
            "KO auxiliary palette 0x12 is not confined to its measured effect poses")
    for name in ("hit", "ko"):
        visible = [sample for sample in clips[name]["timeline"]
                   if sample["source_visible"]]
        require(visible and all(sample["object_offsets"] for sample in visible),
                f"{name} has no source-bound emitted object identities")
    header = (ROOT / "src/port_v2/integration/slice/slice.h").read_text()
    source = (ROOT / "src/port_v2/integration/slice/slice.c").read_text()
    main_source = (ROOT / "main.c").read_text()
    draw_start = main_source.index("static void playable_slice_draw_actors")
    draw_end = main_source.index("static void playable_slice_frame_callback")
    draw = main_source[draw_start:draw_end]
    require("AVSP_PORT_V2_SLICE_ARCHETYPE_STREET_ALIEN" in header and
            "AVSP_PORT_V2_SLICE_ASSET_STREET_ALIEN_ROM" in header and
            "enemy->kind = CAP_ACTOR_ALIEN" in draw and
            "CAP_ACTOR_STALKER" not in draw,
            "slice renderer permits a Stalker identity substitution")
    require("scene->enemy_identity.palette_bank = 19" in source and
            "scene->enemy_identity.palette_bank = 16" in source and
            "playable_slice_frame.scene.enemy_identity.palette_bank" in
            main_source,
            "runtime palette binding is not sourced from the identity contract")
    print("INTEGRATE-03 source actor identity contract: PASS")


if __name__ == "__main__":
    main()
