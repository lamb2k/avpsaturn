#!/usr/bin/env python3
"""Independent source-event identity checks for INTEGRATE-03."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    contract = json.loads(
        (ROOT / "data/avsp_source_combat_presentation_contract.json").read_text(
            encoding="utf-8"))
    require(contract["classification"] == "MEASURED MAME source contract" and
            contract["source"]["byte_identical_reruns"] is True and
            contract["event_pipeline"].startswith(
                "one event binds selector, player record"),
            "source-event provenance or one-event binding drifted")
    events = contract["events"]
    require([event["contact_frame"] for event in events] ==
            [5190, 5236, 5283, 5329] and
            [event["attack_selector"] for event in events] == [1, 2, 3, 4],
            "source contact/selector sequence drifted")
    require(len({event["player"]["animation_record"]
                 for event in events}) == 4,
            "four selectors no longer bind four source player records")
    require(all(event["enemy_contact"]["class_id"] == 31 and
                event["enemy_contact"]["role"] == "street_alien" and
                event["enemy_contact"]["palette"] == 19 and
                event["enemy_reaction"]["palette"] == 19
                for event in events),
            "a source event permits a non-street-alien identity or palette")
    header = (ROOT / "src/port_v2/integration/slice/slice.h").read_text()
    source = (ROOT / "src/port_v2/integration/slice/slice.c").read_text()
    main_source = (ROOT / "main.c").read_text()
    draw_start = main_source.index("static void playable_slice_draw_actors")
    draw_end = main_source.index("static void playable_slice_frame_callback")
    draw = main_source[draw_start:draw_end]
    require("AVSP_PORT_V2_SLICE_INTERFACE_VERSION 3" in header and
            "AVSP_PORT_V2_SLICE_SOURCE_FIRST_CONTACT" in source and
            "avsp_port_v2_combat_source_player_frame" in source and
            "avsp_port_v2_combat_source_enemy_sample" in source,
            "slice does not consume the accepted source presentation ports")
    require("enemy->kind = CAP_ACTOR_ALIEN" in draw and
            "CAP_ACTOR_STALKER" not in draw and
            "playable_slice_frame.scene.enemy_identity.palette_bank" in
            main_source,
            "slice renderer permits a Stalker or authored palette substitution")
    require("frame >= 2300 ? 13" not in main_source and
            "player_source_height" in main_source,
            "timeline-wide fourth-attack height override was restored")
    print("INTEGRATE-03 independent source-event identity contract: PASS")


if __name__ == "__main__":
    main()
