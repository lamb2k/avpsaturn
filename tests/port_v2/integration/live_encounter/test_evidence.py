#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).resolve().parent
inventory=json.loads((HERE/"inventory.json").read_text()); base=inventory["build_root"]
def load(path): return json.loads((ROOT/path).read_text())
builds=[load(f"{base}/run-{n}/build.json") for n in (1,2)]
normals=[load(f"{base}/run-{n}/iso-normalization.json") for n in (1,2)]
reads=[load(f"{base}/run-{n}/readback.json") for n in (1,2)]
assert builds[0]["source_commit"] == builds[1]["source_commit"]
assert builds[0]["source_tree"] == builds[1]["source_tree"]
assert normals[0]["normalized_iso_sha256"] == normals[1]["normalized_iso_sha256"]
assert reads[0]["samples"] == reads[1]["samples"]
assert reads[0]["state"] == reads[1]["state"]
assert reads[0]["vdp1_texture_integrity"] == reads[1]["vdp1_texture_integrity"]
assert len(reads[0]["samples"]) == 467 and reads[0]["state"]["frame"] == 466
for build,normal,report in zip(builds,normals,reads):
    assert build["result"] == report["result"] == "PASS"
    assert normal["production_payload_changed"] is False
    assert build["artifacts"]["game_iso"]["sha256"] == normal["normalized_iso_sha256"] == report["iso_sha256"]
    assert report["source_commit"] == build["source_commit"] and report["physical_saturn"] == "UNRUN"
    assert report["task_id"] == "REIMPLEMENT-12-SOURCE-CLOSED-LIVE-ENCOUNTER"
    assert report["state"]["interface_version"] == 2
    assert report["state"]["contract_flags"] == 127
    assert report["state"]["failures"] == report["state"]["fallback_count"] == 0
    assert report["state"]["round1_spec_bound"] == 1
    assert report["state"]["round1_entry_valid"] == 1
    assert report["state"]["round1_canaries_ok"] == 1
    assert report["state"]["round1_route_state"] == 4
    assert report["state"]["round1_rng_seed"] == 0x3318
    assert report["state"]["round1_player_health"] == 101
    assert [report["state"][f"round1_pool{kind}_free"]
            for kind in (12,16,20,24)] == [10,20,13,2]
    assert report["state"]["round1_fallback_count"] == 0
    assert report["state"]["round1_failure_count"] == 0
    assert report["state"]["round1_entry_spawn_count"] == 10
    assert report["state"]["round1_entry_step"] == 8
    assert report["state"]["round1_entry_timer_decrements"] == 164
    assert report["state"]["round1_entry_gate8236"] == 0
    assert report["state"]["round1_entry_gate81af"] == 1
    assert report["state"]["round1_control_enabled"] == 1
    assert report["state"]["round1_player_x"] == 1025
    assert report["state"]["round1_player_z"] == 320
    assert report["state"]["round1_player_facing"] == 1
    assert report["state"]["round1_player_source_action"] == 514
    assert report["state"]["round1_player_controller_updates"] == 468
    assert report["state"]["round1_scheduler_frames"] == 638
    assert report["state"]["round1_scheduler_dispatches"] == 9126
    assert report["state"]["round1_scheduler_trace_count"] == 14
    assert report["state"]["round1_scheduler_order_hash"] == -203734367
    assert report["state"]["round1_actor_handler_dispatches"] == 6380
    assert report["state"]["round1_presentation_bindings"] == 6380
    assert report["state"]["round1_state_context_bindings"] == 6380
    assert report["state"]["round1_navigation_bound_x"] == 801
    assert report["state"]["round1_navigation_bound_z"] == 256
    assert report["state"]["round1_navigation_applications"] == 468
    assert report["state"]["round1_navigation_clamps"] == 0
    assert report["state"]["round1_navigation_obstacle_responses"] == 0
    assert report["state"]["round1_navigation_terrain_responses"] == 0
    assert report["state"]["round1_navigation_terrain_retries"] == 0
    assert report["state"]["round1_camera_x_position"] == 801
    assert report["state"]["round1_camera_x_target"] == 801
    assert report["state"]["round1_camera_x_lower"] == 640
    assert report["state"]["round1_camera_x_upper"] == 832
    assert report["state"]["round1_camera_scroll2_x"] == 737
    assert report["state"]["round1_camera_phase"] == 0
    assert report["state"]["round1_camera_countdown"] == 1200
    assert report["state"]["round1_camera_locks"] == 0
    assert report["state"]["round1_camera_unlocks"] == 0
    assert report["state"]["round1_player_stop_ticks"] == 0
    assert report["state"]["round1_player_stop_entries"] == 4
    assert report["state"]["round1_player_stop_completions"] == 3
    assert report["state"]["round1_player_stop_motion_suppressions"] == 19
    assert report["state"]["round1_player_melee_entries"] == 4
    assert report["state"]["round1_player_melee_completions"] == 4
    assert report["state"]["round1_player_melee_selector_mask"] == 15
    assert report["state"]["round1_player_melee_presentation_mask"] == 15
    assert report["state"]["round1_player_melee_interruptions"] == 0
    assert report["state"]["round1_player_weapon_entries"] == 2
    assert report["state"]["round1_player_weapon_completions"] == 2
    assert report["state"]["round1_player_weapon_attempts"] == 12
    assert report["state"]["round1_player_weapon_allocations"] == 12
    assert report["state"]["round1_player_weapon_allocation_failures"] == 0
    assert report["state"]["round1_player_weapon_resource_debits"] == 12
    assert report["state"]["round1_player_weapon_presentation_bindings"] == 70
    assert report["state"]["round1_player_weapon_empty_requests"] == 1
    assert report["state"]["round1_player_weapon_empty_allocations"] == 1
    assert report["state"]["round1_player_weapon_empty_allocation_failures"] == 0
    assert report["state"]["round1_player_weapon_empty_releases"] == 1
    assert report["state"]["round1_player_weapon_empty_presentation_bindings"] == 10
    assert report["state"]["round1_player_weapon_interruptions"] == 0
    assert report["state"]["round1_player_resource"] == 32
    assert report["state"]["round1_player_resource_recharge"] == 6
    assert report["state"]["round1_player_weapon_projectile_free"] == 24
    assert report["state"]["round1_native_initial_actor_render_commands"] > 0
    assert report["state"]["round1_class1f_initializations"] == 10
    assert report["state"]["round1_class1f_initial_rng_calls"] == 10
    assert report["state"]["round1_class1f_transition_completions"] == 10
    assert report["state"]["round1_class1f_effect_allocations"] == 2
    assert report["state"]["round1_class1f_effect_allocation_failures"] == 2
    assert report["state"]["round1_class1f_audio_events"] == 2
    assert report["state"]["round1_class1f_audio_command"] == 0x4d
    assert report["state"]["round1_class09_rng_calls"] == 158
    assert report["state"]["round1_class4e_initializations"] == 2
    assert report["state"]["round1_class4e_releases"] == 2
    assert report["state"]["round1_class44_guard_clears"] == 1
    assert report["state"]["round1_scheduler_failure_code"] == 0
    assert report["state"]["round1_native_projectile_render_frames"] > 0
    assert report["state"]["round1_native_impact_render_frames"] > 0
    assert report["state"]["round1_native_projectile_render_commands_peak"] > 0
    assert report["state"]["round1_native_impact_render_commands_peak"] > 0
    assert report["state"]["round1_native_presentation_decode_failures"] == 0
    assert report["state"]["round1_native_projectile_collision_writes"] > 0
    assert report["state"]["round1_native_projectile_damage_writes"] > 0
    assert report["state"]["round1_presentation_ready"] == 1
    assert report["state"]["round1_presentation_seen"] == 1
    assert report["state"]["round1_presentation_commands_peak"] == 2
    assert report["chronology"] == {
        "alien_contacts":1, "misses":0, "player_contacts":0,
        "player_damage_events":1, "unlock_frame":None}
    assert report["visual_scanout"] == "UNAVAILABLE_WINDOWS_ACCELERATED_SURFACE"
    assert report["vdp1_texture_integrity"]["checked_textures"] == 208
    assert report["vdp1_texture_integrity"]["mismatches"] == 0
    assert report["vdp1_texture_integrity"]["sprite_array_distance"] >= 255 * 8
    assert report["vdp1_texture_integrity"]["sprite_high_water"] < 255
print("REIMPLEMENT-13 paired source-closed emulator evidence: PASS")
