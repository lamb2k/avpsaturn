#!/usr/bin/env python3
"""Mutation controls for the target-visible Round 1 entry wiring."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MAIN = (ROOT / "main.c").read_text()
SPEC_SHA256 = hashlib.sha256(
    (ROOT / "data/spec02_round1_executable_contract.json").read_bytes()
).hexdigest()

REQUIRED = (
    '#include "src/port_v2/gameplay/round1/round1.h"',
    "#define AVSP_TILE_REGION_BYTES 0x96000",
    "#define AVSP_TILE_FRAME_UNIQUE_LIMIT 8192",
    "#define AVSP_ROUND1_RUNTIME_REGION_BYTES 0x19000",
    "#define AVSP_ROUND1_RUNTIME_MEASURED_BYTES 0x173dc",
    "(actor->type == 24u && actor->actor_class == 0x43)",
    "(unsigned short)actor->y <= (unsigned short)actor->z",
    "#define AVSP_LIVE_DIAG_REGION_BYTES 0x1A000",
    "#define AVSP_LIVE_DIAG_RECORD_BYTES 156",
    "#define round1_runtime (*AVSP_ROUND1_RUNTIME_BASE)",
    "sizeof(AvspRound1Runtime) <= AVSP_ROUND1_RUNTIME_REGION_BYTES ? 1 : -1",
    "sizeof(AvspRound1Runtime) == AVSP_ROUND1_RUNTIME_MEASURED_BYTES ? 1 : -1",
    "sizeof(LiveEncounterDiagSample) * AVSP_LIVE_DIAG_SAMPLES <=",
    "sizeof(LiveEncounterDiagSample) == AVSP_LIVE_DIAG_RECORD_BYTES ? 1 : -1",
    "AVSP_LIVE_DIAG_REGION_BYTES <=\n        AVSP_CART_DRAM1_BYTES",
    "volatile LiveEncounterDiagSample *avsp_diag_live_samples =",
    "AVSP_ROUND1_RUNTIME_REGION_BYTES +\n                               AVSP_LIVE_DIAG_REGION_BYTES",
    "AVSP_STRIPS_REGION_BYTES -\n                               AVSP_ROUND1_RUNTIME_REGION_BYTES",
    "AVSP_ROUND1_RUNTIME_REGION_BYTES -\n                               AVSP_LIVE_DIAG_REGION_BYTES",
    "static unsigned long round1_native_capture_frame;",
    "#define AVSP_LIVE_DIAG_SAMPLES 575",
    "avsp_round1_init(&round1_runtime);",
    "round1_native_capture_frame = 0UL;",
    "!avsp_round1_begin_first_entry(&round1_runtime)",
    "avsp_round1_step_first_entry(&round1_runtime)",
    "avsp_round1_step_player(&round1_runtime, round1_player_mask, 0)",
    "avsp_round1_step_scheduler_pre_player_source_differential(",
    "avsp_round1_step_scheduler_post_player_source_differential(",
    "avsp_diag_round1_entry_valid = avsp_round1_entry_valid(&round1_runtime);",
    "strcmp(AVSP_ROUND1_SPEC02_SHA256,",
    f'"{SPEC_SHA256}") ==',
    "avsp_diag_round1_route_state = round1_runtime.route_state;",
    "avsp_diag_round1_rng_seed = round1_runtime.rng_seed;",
    "avsp_diag_round1_canaries_ok = avsp_round1_canaries_ok(&round1_runtime);",
    "avsp_diag_round1_entry_spawn_count = round1_runtime.entry.spawn_count;",
    "avsp_diag_round1_control_enabled =",
    "avsp_diag_round1_player_controller_updates =",
    "avsp_diag_round1_scheduler_order_hash =",
    "((AVSP_ROUND1_DIAGNOSTIC_SOURCE_BASE_FRAME +",
    "round1_runtime.frame + 1UL) & 0x0000ffffUL) << 16",
    "avsp_diag_round1_presentation_bindings =",
    "avsp_diag_round1_state_context_bindings =",
    "avsp_diag_round1_navigation_applications =",
    "avsp_diag_round1_navigation_obstacle_responses =",
    "avsp_diag_round1_navigation_terrain_responses =",
    "avsp_diag_round1_camera_x_position =",
    "avsp_diag_round1_camera_scroll2_x =",
    "avsp_diag_round1_player_stop_entries =",
    "avsp_diag_round1_player_melee_entries =",
    "avsp_diag_round1_player_melee_presentation_mask =",
    "round1_build_native_first_encounter_frame(round1_player_mask);",
    "live_encounter_frame.frame = round1_native_capture_frame++;",
    "if (!round1_runtime.first_encounter.initialized)",
    "live_encounter_publish();",
    "avsp_round1_first_encounter_view(&round1_runtime, &encounter);",
    "round1_runtime.first_encounter.reaction.elapsed :",
    "(int)round1_runtime.first_encounter.player_contacts;",
    "(int)round1_runtime.fallback_count;",
    "round1_runtime.first_encounter.hit_events;",
    "round1_runtime.first_encounter.ko_events;",
    "if (jo_is_pad1_key_down(JO_KEY_A)) mask |= AVSP_ROUND1_INPUT_BUTTON1;",
    "if (jo_is_pad1_key_down(JO_KEY_C)) mask |= AVSP_ROUND1_INPUT_BUTTON3;",
    "input.player_mask = avsp_round1_coffee_shop_source_input(",
    "(unsigned short)source_frame);",
    "for (source_tick = 0u; source_tick < source_updates; ++source_tick)",
    "if (round1_player_authority_enabled_at_tick_start &&\n"
    "            !avsp_round1_step_player",
    "avsp_diag_round1_player_weapon_entries =",
    "avsp_diag_round1_player_weapon_completions =",
    "avsp_diag_round1_player_weapon_attempts =",
    "avsp_diag_round1_player_weapon_allocations =",
    "avsp_diag_round1_player_weapon_resource_debits =",
    "avsp_diag_round1_player_weapon_presentation_bindings =",
    "avsp_diag_round1_player_weapon_empty_allocations =",
    "avsp_diag_round1_player_weapon_empty_allocation_failures =",
    "avsp_diag_round1_player_weapon_empty_releases =",
    "avsp_diag_round1_player_weapon_empty_presentation_bindings =",
    "avsp_diag_round1_player_resource = round1_runtime.player_resource;",
    "avsp_diag_round1_player_weapon_projectile_free =",
    "sample->round1_player_weapon_state0 =",
    "sample->round1_player_weapon_state1 =",
    "round1_runtime.camera_guard_countdown &",
    "round1_runtime.navigation_obstacle_responses &",
    "sample->round1_player_jump_state =",
    "sample->round1_player_identity_state =",
    "4u, projectile->actor_class, projectile->animation_record,",
    "avsp_round1_is_weapon_parent_projectile(projectile)",
    "avsp_round1_is_weapon_child_projectile(projectile)",
    "avsp_diag_round1_native_weapon_forbidden_identity",
    "round1_runtime.player_jump_motion_updates & 0x3fu",
    "avsp_diag_round1_native_player_render_commands > 0",
    "avsp_round1_player_native_presentation_active(&round1_runtime)",
    "draw_round1_empty_effects() > 0",
    "avsp_diag_round1_native_empty_effect_render_frames",
    "round1_runtime.player_action.height) +",
    "world_z, projection_height) +",
    "round1_runtime.player_action.height,",
    "draw_round1_source_actor(",
    "static unsigned char tile_pool_frame_pinned[AVSP_TILE_SPRITE_POOL];",
    "tile_pool_frame_pinned[index] = 1u;",
    "++avsp_diag_round1_native_tile_pin_exhaustions;",
    "avsp_diag_round1_native_tile_unique_peak",
    "entry_right <= -JO_TV_WIDTH / 2",
    "if (victim < 0)\n    {",
    "tile_pool_begin_frame();",
    "#define AVSP_ROUND1_STARTUP_TRACE_SAMPLES 16",
    "#define AVSP_ROUND1_DIAGNOSTIC_SOURCE_BASE_FRAME 2040",
    "#define AVSP_ROUND1_NATIVE_ENTRY_STEP_FRAME 32",
    "round1_runtime.frame >= AVSP_FRONTEND_R1HUD_FRAME",
    "round1_runtime.frame >= AVSP_FRONTEND_R1SCENE_POP_FRAME",
    "if (!round1_runtime.entry.started &&\n        round1_runtime.frame == AVSP_ROUND1_NATIVE_ENTRY_STEP_FRAME &&",
    "if (round1_runtime.entry.started &&\n            round1_runtime.route_state != 4 &&",
    "hud_input.players[AVSP_PORT_V2_HUD_P2].visible = 0;",
    "if (round1_runtime.route_state == 4 &&\n        round1_runtime.first_encounter.initialized)",
    "int retained_stepped = 0;",
    "pcm_input.cue_event = 0;",
    "source_frame ==\n            AVSP_PORT_V2_CDDA_SOURCE_FRAME_STAGE1",
    "round1_record_startup_chronology(retained_stepped);",
    "round1_runtime.camera_scroll2_x :",
    "street_scroll3_for_scroll2(camera_scroll2)",
    "avsp_diag_round1_startup_retained_before_handoff",
    "avsp_diag_round1_startup_p2_visible_frames",
    "avsp_diag_round1_startup_hidden_contacts",
    "avsp_diag_round1_startup_hidden_damage",
    "avsp_diag_round1_startup_orphan_pcm",
    "avsp_diag_round1_startup_duplicate_cdda",
    "avsp_frontend_load_round1_text(&frontend_runtime);",
)

def accepts(body):
    return all(token in body for token in REQUIRED)

assert accepts(MAIN)
for token in REQUIRED[1:]:
    assert not accepts(MAIN.replace(token, "/* suppressed Round 1 binding */"))
assert "avsp_frontend_draw_round1_text(&frontend_runtime);" in MAIN
assert "round1_runtime.frame < AVSP_FRONTEND_R1TEXT_CLEAR_FRAME" in MAIN
assert "hud_input.players[AVSP_PORT_V2_HUD_P2].visible = 1;" not in MAIN[MAIN.index("static void live_encounter_build_slice_frame"):MAIN.index("static int round1_startup_player_visible")]
assert "pcm_input.cue_event = live_encounter_frame.player_contact" not in MAIN
assert "live_encounter_frame.frame == 0UL" not in MAIN
assert "5u, 0x05u, projectile->animation_record," not in MAIN
encounter_builder = MAIN[MAIN.index("static void live_encounter_build_slice_frame"):MAIN.index("static int round1_startup_player_visible")]
live_callback = MAIN[MAIN.index("static void live_encounter_frame_callback"):MAIN.index("static void playable_slice_frame_callback")]
assert "avsp_live_encounter_step" not in live_callback
assert "live_encounter_runtime.player.hit_timer" not in encounter_builder
assert "live_encounter_runtime.reaction_elapsed" not in encounter_builder
assert "live_encounter_runtime.player_contacts" not in encounter_builder
assert "live_encounter_runtime.fallback_count" not in encounter_builder
print(f"REIMPLEMENT-13 target entry/player/scheduler/class1f/global-bounds/neutral-stop/melee/Button1/startup-authority/first-encounter wiring: PASS ({len(REQUIRED) - 2} suppressions rejected)")
