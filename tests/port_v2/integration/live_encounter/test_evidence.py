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
assert len(reads[0]["samples"]) == 471 and reads[0]["state"]["frame"] == 470
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
    assert report["state"]["round1_rng_seed"] == 0x8DEF
    assert report["state"]["round1_player_health"] == 101
    assert [report["state"][f"round1_pool{kind}_free"]
            for kind in (12,16,20,24)] == [10,20,16,32]
    assert report["state"]["round1_fallback_count"] == 0
    assert report["state"]["round1_failure_count"] == 0
    assert report["state"]["round1_entry_spawn_count"] == 10
    assert report["state"]["round1_entry_step"] == 8
    assert report["state"]["round1_entry_timer_decrements"] == 164
    assert report["state"]["round1_entry_gate8236"] == 0
    assert report["state"]["round1_entry_gate81af"] == 1
    assert report["state"]["round1_control_enabled"] == 1
    assert report["state"]["round1_player_x"] == 1049
    assert report["state"]["round1_player_z"] == 320
    assert report["state"]["round1_player_facing"] == 1
    assert report["state"]["round1_player_source_action"] == 514
    assert report["state"]["round1_player_controller_updates"] == 301
    assert report["state"]["round1_scheduler_frames"] == 301
    assert report["state"]["round1_scheduler_dispatches"] == 3010
    assert report["state"]["round1_scheduler_trace_count"] == 10
    assert report["state"]["round1_scheduler_order_hash"] == -2089937380
    assert report["state"]["round1_actor_handler_dispatches"] == 3010
    assert report["state"]["round1_presentation_bindings"] == 3010
    assert report["state"]["round1_state_context_bindings"] == 3010
    assert report["state"]["round1_navigation_bound_x"] == 720
    assert report["state"]["round1_navigation_bound_z"] == 256
    assert report["state"]["round1_navigation_applications"] == 301
    assert report["state"]["round1_navigation_clamps"] == 0
    assert report["state"]["round1_player_stop_ticks"] == 0
    assert report["state"]["round1_player_stop_entries"] == 2
    assert report["state"]["round1_player_stop_completions"] == 1
    assert report["state"]["round1_player_stop_motion_suppressions"] == 10
    assert report["state"]["round1_player_melee_entries"] == 4
    assert report["state"]["round1_player_melee_completions"] == 4
    assert report["state"]["round1_player_melee_selector_mask"] == 15
    assert report["state"]["round1_player_melee_presentation_mask"] == 15
    assert report["state"]["round1_player_melee_interruptions"] == 0
    assert report["state"]["round1_player_weapon_entries"] == 1
    assert report["state"]["round1_player_weapon_completions"] == 1
    assert report["state"]["round1_player_weapon_attempts"] == 12
    assert report["state"]["round1_player_weapon_allocations"] == 12
    assert report["state"]["round1_player_weapon_allocation_failures"] == 0
    assert report["state"]["round1_player_weapon_resource_debits"] == 12
    assert report["state"]["round1_player_weapon_presentation_bindings"] == 51
    assert report["state"]["round1_player_weapon_empty_requests"] == 0
    assert report["state"]["round1_player_weapon_interruptions"] == 0
    assert report["state"]["round1_player_resource"] == 46
    assert report["state"]["round1_player_resource_recharge"] == 1
    assert report["state"]["round1_player_weapon_projectile_free"] == 12
    assert report["state"]["round1_presentation_ready"] == 1
    assert report["state"]["round1_presentation_seen"] == 1
    assert report["state"]["round1_presentation_commands_peak"] == 2
    assert report["chronology"] == {
        "alien_contacts":1, "misses":1, "player_contacts":4,
        "player_damage_events":1, "unlock_frame":450}
    assert report["visual_scanout"] == "UNAVAILABLE_WINDOWS_ACCELERATED_SURFACE"
print("REIMPLEMENT-12 paired source-closed emulator evidence: PASS")
