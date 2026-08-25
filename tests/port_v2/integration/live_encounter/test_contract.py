#!/usr/bin/env python3
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent

def require(value, message):
    if not value:
        raise AssertionError(message)

contract = json.loads((HERE / "contract.json").read_text())
source = (ROOT / "src/port_v2/integration/live_encounter/live_encounter.c").read_text()
header = (ROOT / "src/port_v2/integration/live_encounter/live_encounter.h").read_text()
main = (ROOT / "main.c").read_text()

def presentation_boundary_ok(text):
    return (
        "avsp_pw_render_facing(live_encounter_frame.player.facing)" in text and
        "live_encounter_frame.player.facing ? -1 : 1" not in text and
        "avsp_pw_source_presentation_ready(" in text and
        re.search(
            r"live_encounter_frame\.player\.state == AVSP_PW_STATE_ATTACK &&\s*"
            r"!scene->player_presentation_active\)\s*\{.*?"
            r"scene->player_action = AVSP_PORT_V2_SLICE_ACTION_IDLE;",
            text, re.S) is not None
    )

require(contract["real_input_authority"] is True and
        contract["fixed_frame_authority"] is False and
        contract["presentation_owned_outcome"] is False and
        contract["fallback_present"] is False, "authority contract drifted")
require("target_ko != 0u && target_inactive != 0u" in source,
        "clear lost target KO plus inactivity authority")
require("avsp_collision_overlap" in source and
        "avsp_pw_step" in source and "avsp_alien_ai_step" in source and
        "avsp_port_v2_hit_ko_begin" in source,
        "promoted gameplay authorities are not integrated")
require("AVSP_LIVE_ENCOUNTER_SPEC01_SHA256" in header and
        "avsp_live_encounter_project_screen_y" in source and
        "avsp_pw_resolve_navigation" in source,
        "SPEC-01 identity, projection, or navigation authority is absent")
require(not re.search(r"runtime->frame\s*[>=]=?\s*\d+.*(?:clear|contact|damage)",
                      source, re.I), "fixed-frame gameplay authority introduced")
require("AVSP_LIVE_ENCOUNTER_AUTOTEST" in main and
        "jo_is_pad1_key_pressed" in main and "jo_is_pad1_key_down" in main,
        "exact live profile lacks real controller input boundary")
require(presentation_boundary_ok(main),
        "live player facing or source-presentation boundary drifted")
require(not presentation_boundary_ok(main.replace(
            "avsp_pw_render_facing(live_encounter_frame.player.facing)",
            "live_encounter_frame.player.facing ? -1 : 1", 1)),
        "facing-sign mutation control failed")
require(not presentation_boundary_ok(main.replace(
            "!scene->player_presentation_active)\n"
            "    {\n"
            "        /* The measured source remains in its control pose for the first two\n"
            "           attack ticks. Do not flash the unrelated legacy attack clip before\n"
            "           the selector-owned source presentation becomes active. */\n"
            "        scene->player_action = AVSP_PORT_V2_SLICE_ACTION_IDLE;",
            "!scene->player_presentation_active)\n"
            "    {\n"
            "        /* MUTATED: restore the unrelated legacy attack clip. */\n"
            "        scene->player_action = AVSP_PORT_V2_SLICE_ACTION_ATTACK;", 1)),
        "legacy attack-flash mutation control failed")
require("PHYSICAL SATURN" not in source.upper(),
        "production core introduced a physical claim")
translated = subprocess.run(["wsl.exe", "wslpath", "-a", str(ROOT).replace("\\", "/")], check=True, capture_output=True, text=True).stdout.strip()
command = (f"cd '{translated}' && mkdir -p build/port_v2/live_encounter && "
           "gcc -std=c90 -pedantic -Wall -Wextra -Werror -O2 "
           "src/port_v2/gameplay/player_action/player_action.c "
           "src/port_v2/gameplay/street_alien_ai/street_alien_ai.c "
           "src/port_v2/combat/hit_ko/hit_ko.c "
           "src/port_v2/integration/combat/combat.c "
           "src/port_v2/integration/player_enemy/player_enemy.c "
           "src/port_v2/player/player.c src/port_v2/enemy/enemy.c "
           "src/port_v2/audio/pcm/pcm.c "
           "src/port_v2/integration/live_encounter/live_encounter.c "
           "avsp_actor.c avsp_collision.c "
           "tests/port_v2/integration/live_encounter/live_encounter_test.c "
           "-o build/port_v2/live_encounter/live_encounter_test && "
           "./build/port_v2/live_encounter/live_encounter_test")
subprocess.run(["wsl.exe", "bash", "-lc", command], check=True)
print("INTEGRATE-04A production contract and deterministic negative controls: PASS")
