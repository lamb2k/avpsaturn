#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("enemy_tools", ROOT / "tests/port_v2/enemy_bench/collect_readback.py")
tools = importlib.util.module_from_spec(spec); spec.loader.exec_module(tools)
FIELDS = ("frame","input_mask","player_x","player_lane","player_health","player_state",
          "player_selector","player_attack_active","player_facing",
          "player_animation_record","player_assembly","player_screen_y",
          "alien_x","alien_lane","alien_health","alien_state","alien_inner",
          "alien_action","alien_facing","alien_animation_record","alien_assembly",
          "alien_screen_y","alien_rng","player_contact","alien_contact","player_damage",
          "alien_damage","attack_miss","encounter_state","route_unlocked",
          "continued_after_unlock","camera_world_x","failures")
FIELDS = FIELDS + ("round1_player_x","round1_player_z","round1_player_facing",
                   "round1_player_source_action","round1_player_controller_updates")
FIELDS = FIELDS + ("round1_scheduler_frames","round1_scheduler_dispatches",
                   "round1_scheduler_trace_count","round1_scheduler_order_hash")
FIELDS = FIELDS + ("round1_actor_handler_dispatches",
                   "round1_presentation_bindings",
                   "round1_state_context_bindings")
FIELDS = FIELDS + ("round1_navigation_applications",)
FIELDS = FIELDS + ("round1_player_stop_state",
                   "round1_player_weapon_state0",
                   "round1_player_weapon_state1",
                   "round1_native_presentation_state",
                   "round1_class1f_state",
                   "round1_auxiliary_state",
                   "round1_native_initial_state",
                   "round1_player_jump_state",
                   "round1_player_identity_state")
U16_FIELDS = {"input_mask", "alien_rng", "round1_player_source_action"}
S16_FIELDS = {
    "player_x", "player_lane", "player_health", "player_state",
    "player_selector", "player_attack_active", "player_facing",
    "player_screen_y", "alien_x", "alien_lane", "alien_health",
    "alien_state", "alien_inner", "alien_action", "alien_facing",
    "alien_screen_y", "player_contact", "alien_contact", "player_damage",
    "alien_damage", "attack_miss", "encounter_state", "route_unlocked",
    "continued_after_unlock", "camera_world_x", "failures",
    "round1_player_x", "round1_player_z", "round1_player_facing",
}
EVIDENCE_LAST_FRAME = 574
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def signed(mcp, address): return tools.signed32(mcp.u32(address))
def read_samples(mcp, base, count):
    offsets = {}
    cursor = 0
    for name in FIELDS:
        size = 2 if name in U16_FIELDS or name in S16_FIELDS else 4
        if cursor % size:
            cursor += size - cursor % size
        offsets[name] = (cursor, size)
        cursor += size
    record_bytes = (cursor + 3) & ~3
    max_records = 65536 // record_bytes
    payload = bytearray()
    for first in range(0, count, max_records):
        records = min(max_records, count - first)
        payload.extend(mcp.read(base + first * record_bytes,
                                records * record_bytes))
    result = []
    for index in range(count):
        start = index * record_bytes
        record = payload[start:start + record_bytes]
        decoded = {}
        for name in FIELDS:
            offset, size = offsets[name]
            value = int.from_bytes(record[offset:offset + size], "big")
            if name in S16_FIELDS and value & 0x8000:
                value -= 0x10000
            elif size == 4:
                value = tools.signed32(value)
            decoded[name] = value
        navigation_state = decoded["round1_navigation_applications"] & 0xffffffff
        decoded["round1_navigation_applications"] = navigation_state & 0x0fff
        decoded["round1_navigation_obstacle_responses"] = \
            (navigation_state >> 12) & 0xff
        decoded["round1_navigation_terrain_responses"] = \
            (navigation_state >> 20) & 0x0f
        decoded["round1_navigation_terrain_retries"] = \
            (navigation_state >> 24) & 0x0f
        camera_state = decoded["round1_scheduler_trace_count"] & 0xffffffff
        decoded["round1_scheduler_trace_count"] = camera_state & 0xff
        decoded["round1_camera_countdown"] = (camera_state >> 8) & 0x07ff
        decoded["round1_camera_phase"] = (camera_state >> 19) & 0x0f
        decoded["round1_camera_locks"] = (camera_state >> 23) & 0x0f
        decoded["round1_camera_unlocks"] = (camera_state >> 27) & 0x0f
        scheduler_state = decoded["round1_scheduler_frames"] & 0xffffffff
        decoded["round1_source_frame"] = (scheduler_state >> 16) & 0xffff
        decoded["round1_scheduler_source_frame"] = \
            (decoded["round1_source_frame"] - 1) & 0xffff
        decoded["round1_scheduler_frames"] = scheduler_state & 0xffff
        identity_state = decoded["round1_player_identity_state"] & 0xffffffff
        decoded["round1_class4e_variant1_allocations"] = \
            (identity_state >> 26) & 0x0f
        result.append(decoded)
    return result

parser = argparse.ArgumentParser()
parser.add_argument("--run", type=int, choices=(1,2), required=True)
parser.add_argument("--emulator-pid", type=int, required=True)
parser.add_argument("--timeout", type=float, default=180.0)
parser.add_argument("--coffee-shop-scene", action="store_true")
args = parser.parse_args()
inventory = json.loads((HERE / "inventory.json").read_text())
build = json.loads((ROOT / inventory["build_root"] / f"run-{args.run}/build.json").read_text())
syms = tools.symbols(inventory["required_readback_symbols"])
mcp = tools.Mcp("http://127.0.0.1:9640/mcp"); deadline=time.time()+args.timeout
while True:
    try: mcp.initialize(); break
    except Exception:
        if time.time() >= deadline: raise
        time.sleep(0.25)
run_root = ROOT / inventory["build_root"] / f"run-{args.run}"
while time.time() < deadline:
    try:
        ready = mcp.u32(syms["avsp_diag_runtime_ready"])
        frame = mcp.u32(syms["avsp_diag_live_frame"])
        if (ready == 1 and frame > 0 and
                mcp.u32(syms["runtime_ready"]) == 0):
            deadline = 0
            continue
        if (ready == 1 and frame >= EVIDENCE_LAST_FRAME and
                signed(mcp, syms["avsp_diag_live_frame_stage"]) == 7):
            break
    except Exception:
        # The pinned Windows build occasionally resets one HTTP connection
        # while the emulator remains alive. Reinitialize the bridge and keep
        # the bounded deadline authoritative.
        time.sleep(0.25)
        try: mcp.initialize()
        except Exception: pass
    time.sleep(0.05)
else:
    failed_asset_pointer = mcp.u32(syms["failed_asset"])
    failed_asset_name = ""
    invalid_tile_slots = []
    timeout_tile_pool_used = min(mcp.u32(syms["tile_pool_used"]), 218)
    for timeout_tile_index in range(timeout_tile_pool_used):
        timeout_sprite_id = mcp.u32(
            syms["tile_pool_sprite"] + timeout_tile_index * 4)
        timeout_definition = mcp.read(
            syms["__jo_sprite_def"] + timeout_sprite_id * 8, 8)
        timeout_picture = mcp.read(
            syms["__jo_sprite_pic"] + timeout_sprite_id * 8, 8)
        timeout_width = int.from_bytes(timeout_definition[0:2], "big")
        timeout_height = int.from_bytes(timeout_definition[2:4], "big")
        timeout_color_mode = int.from_bytes(timeout_picture[2:4], "big")
        if (timeout_width, timeout_height, timeout_color_mode) != (16, 16, 3):
            invalid_tile_slots.append({
                "cache_index": timeout_tile_index,
                "sprite_id": timeout_sprite_id,
                "width": timeout_width,
                "height": timeout_height,
                "color_mode": timeout_color_mode,
            })
    if failed_asset_pointer != 0:
        failed_asset_name = mcp.read(failed_asset_pointer, 64).split(b"\0", 1)[0].decode(
            "ascii", errors="replace"
        )
    timeout_state = {
        "runtime_ready": mcp.u32(syms["avsp_diag_runtime_ready"]),
        "contract_flags": mcp.u32(syms["avsp_diag_live_contract_flags"]),
        "frame_stage": signed(mcp, syms["avsp_diag_live_frame_stage"]),
        "internal_failures": mcp.u32(syms["avsp_diag_live_internal_failures"]),
        "pcm_retriggers": mcp.u32(syms["avsp_diag_live_pcm_retriggers"]),
        "runtime_ready_internal": mcp.u32(syms["runtime_ready"]),
        "slice_init_stage": signed(mcp, syms["avsp_diag_slice_init_stage"]),
        "slice_ready": mcp.u32(syms["avsp_diag_slice_ready"]),
        "frame": mcp.u32(syms["avsp_diag_live_frame"]),
        "sample_count": mcp.u32(syms["avsp_diag_live_sample_count"]),
        "startup_source_frame":
            mcp.u32(syms["avsp_diag_round1_startup_source_frame"]),
        "startup_trace_count":
            mcp.u32(syms["avsp_diag_round1_startup_trace_count"]),
        "round1_route_state":
            mcp.u32(syms["avsp_diag_round1_route_state"]),
        "tile_pool_used": mcp.u32(syms["tile_pool_used"]),
        "invalid_tile_slots": invalid_tile_slots[:8],
        "composite_sprite_count":
            mcp.u32(syms["round1_composite_sprite_count"]),
        "jo_sprite_id": mcp.u32(syms["__jo_sprite_id"]),
        "tile_unique_peak":
            mcp.u32(syms["avsp_diag_round1_native_tile_unique_peak"]),
        "tile_unique_peak_frame":
            mcp.u32(syms["avsp_diag_round1_native_tile_unique_peak_frame"]),
        "tile_pin_exhaustions":
            mcp.u32(syms["avsp_diag_round1_native_tile_pin_exhaustions"]),
        "tile_replace_calls":
            mcp.u32(syms["avsp_diag_round1_native_tile_replace_calls"]),
        "tile_replace_returns":
            mcp.u32(syms["avsp_diag_round1_native_tile_replace_returns"]),
        "encounter_state": mcp.u32(syms["avsp_diag_live_encounter_state"]),
        "player_x": signed(mcp, syms["avsp_diag_live_player_x"]),
        "player_health": signed(mcp, syms["avsp_diag_live_player_health"]),
        "alien_x": signed(mcp, syms["avsp_diag_live_alien_x"]),
        "alien_health": signed(mcp, syms["avsp_diag_live_alien_health"]),
        "alien_state": mcp.u32(syms["avsp_diag_live_alien_state"]),
        "hit_events": mcp.u32(syms["avsp_diag_live_hit_events"]),
        "ko_events": mcp.u32(syms["avsp_diag_live_ko_events"]),
        "failures": mcp.u32(syms["avsp_diag_live_failures"]),
        "fallback_count": mcp.u32(syms["avsp_diag_live_fallback_count"]),
        "round1_scheduler_failure_code":
            mcp.u32(syms["avsp_diag_round1_scheduler_failure_code"]),
        "round1_scheduler_failure_source_slot":
            hex(mcp.u32(syms["avsp_diag_round1_scheduler_failure_source_slot"])),
        "round1_scheduler_failure_state":
            hex(mcp.u32(syms["avsp_diag_round1_scheduler_failure_state"])),
        "round1_scheduler_failure_substate":
            hex(mcp.u32(syms["avsp_diag_round1_scheduler_failure_substate"])),
        "round1_scheduler_failure_animation_record":
            hex(mcp.u32(syms["avsp_diag_round1_scheduler_failure_animation_record"])),
        "failed_asset_pointer": hex(failed_asset_pointer),
        "failed_asset_name": failed_asset_name,
    }
    timeout_state["debug_status"] = mcp.call("debug_status")
    raise TimeoutError(
        "INTEGRATE-04A diagnostic did not clear and continue: "
        f"{timeout_state}"
    )
mcp.call("set_debug_option", cpu_core="interpreter")
mcp.call("pause")
tile_archive_path = ROOT / build["artifacts"]["tile_archive"]["path"]
tile_archive_bytes = tile_archive_path.read_bytes()
if (sha(tile_archive_path) != build["artifacts"]["tile_archive"]["sha256"] or
        tile_archive_bytes[:4] != b"AVTL"):
    raise RuntimeError("live VDP1 tile archive identity drift")
tile_count = int.from_bytes(tile_archive_bytes[4:8], "big")
rank_table_offset = int.from_bytes(tile_archive_bytes[12:16], "big")
texture_offset = rank_table_offset + tile_count * 4
tile_pool_used = mcp.u32(syms["tile_pool_used"])
if tile_pool_used < 1 or tile_pool_used > 218:
    raise RuntimeError(f"invalid live VDP1 tile-pool count: {tile_pool_used}")
texture_cache_identity = bytearray()
texture_mismatches = []
for tile_index in range(tile_pool_used):
    rank = mcp.u32(syms["tile_pool_rank"] + tile_index * 4)
    sprite_id = mcp.u32(syms["tile_pool_sprite"] + tile_index * 4)
    if rank >= tile_count or sprite_id >= 255:
        raise RuntimeError(
            f"invalid live VDP1 cache identity at {tile_index}: "
            f"rank={rank} sprite={sprite_id}")
    sprite_definition = mcp.read(syms["__jo_sprite_def"] + sprite_id * 8, 8)
    texture_address = int.from_bytes(sprite_definition[4:6], "big") * 8
    actual = mcp.read(0x25C00000 + texture_address, 128)
    expected_start = texture_offset + rank * 128
    expected = tile_archive_bytes[expected_start:expected_start + 128]
    texture_cache_identity.extend(rank.to_bytes(4, "big"))
    texture_cache_identity.extend(sprite_id.to_bytes(4, "big"))
    texture_cache_identity.extend(actual)
    if actual != expected:
        texture_mismatches.append({
            "pool_index": tile_index,
            "rank": rank,
            "sprite_id": sprite_id,
            "texture_address": hex(texture_address),
            "differing_bytes": sum(a != b for a, b in zip(actual, expected)),
        })
if texture_mismatches:
    raise RuntimeError(
        f"live VDP1 texture/archive drift: {texture_mismatches[:8]}")
sprite_array_distance = abs(syms["__jo_sprite_def"] - syms["__jo_sprite_pic"])
if sprite_array_distance < 255 * 8:
    raise RuntimeError(
        f"live Jo sprite arrays overlap: distance={sprite_array_distance}")
texture_integrity = {
    "archive_sha256": build["artifacts"]["tile_archive"]["sha256"],
    "cache_sha256": hashlib.sha256(texture_cache_identity).hexdigest(),
    "checked_textures": tile_pool_used,
    "mismatches": 0,
    "sprite_array_distance": sprite_array_distance,
    "sprite_high_water": signed(mcp, syms["__jo_sprite_id"]),
}
count = signed(mcp,syms["avsp_diag_live_sample_count"])
if count < 1 or count > 600:
    raise RuntimeError(f"invalid live sample count: {count}")
sample_base = mcp.u32(syms["avsp_diag_live_samples"])
expected_sample_base = 0x22600000 + 0x8D000 + 0x48000 + 0x19000
if sample_base != expected_sample_base:
    raise RuntimeError(
        f"live diagnostic cart pointer drift: {sample_base:#x} != "
        f"{expected_sample_base:#x}")
all_samples = read_samples(mcp, sample_base, count)
mapping = {"runtime_ready":"avsp_diag_runtime_ready", "interface_version":"avsp_diag_live_interface_version",
           "contract_flags":"avsp_diag_live_contract_flags", "frame_stage":"avsp_diag_live_frame_stage",
           "frame":"avsp_diag_live_frame", "hit_events":"avsp_diag_live_hit_events",
           "ko_events":"avsp_diag_live_ko_events", "route_unlocked":"avsp_diag_live_route_unlocked",
           "continued":"avsp_diag_live_continued_after_unlock", "failures":"avsp_diag_live_failures",
           "fallback_count":"avsp_diag_live_fallback_count", "canaries_ok":"avsp_diag_live_canaries_ok",
           "internal_failures":"avsp_diag_live_internal_failures",
           "pcm_retriggers":"avsp_diag_live_pcm_retriggers",
           "physical_saturn":"avsp_diag_live_physical_saturn",
           "player_health":"avsp_diag_live_player_health",
           "player_state":"avsp_diag_live_player_state",
           "player_facing":"avsp_diag_live_player_facing",
           "player_animation_record":"avsp_diag_live_player_animation_record",
           "player_assembly":"avsp_diag_live_player_assembly",
           "player_screen_y":"avsp_diag_live_player_screen_y",
           "alien_health":"avsp_diag_live_alien_health",
           "alien_state":"avsp_diag_live_alien_state",
           "alien_action":"avsp_diag_live_alien_action",
           "alien_facing":"avsp_diag_live_alien_facing",
           "alien_animation_record":"avsp_diag_live_alien_animation_record",
           "alien_assembly":"avsp_diag_live_alien_assembly",
           "alien_screen_y":"avsp_diag_live_alien_screen_y",
           "round1_spec_bound":"avsp_diag_round1_spec_bound",
           "round1_entry_valid":"avsp_diag_round1_entry_valid",
           "round1_route_state":"avsp_diag_round1_route_state",
           "round1_rng_seed":"avsp_diag_round1_rng_seed",
           "round1_player_health":"avsp_diag_round1_player_health",
           "round1_pool12_free":"avsp_diag_round1_pool12_free",
           "round1_pool16_free":"avsp_diag_round1_pool16_free",
           "round1_pool20_free":"avsp_diag_round1_pool20_free",
           "round1_pool24_free":"avsp_diag_round1_pool24_free",
           "round1_fallback_count":"avsp_diag_round1_fallback_count",
           "round1_canaries_ok":"avsp_diag_round1_canaries_ok",
           "round1_presentation_ready":"avsp_diag_round1_presentation_ready",
           "round1_presentation_seen":"avsp_diag_round1_presentation_seen",
           "round1_presentation_commands_peak":"avsp_diag_round1_presentation_commands_peak",
           "round1_entry_spawn_count":"avsp_diag_round1_entry_spawn_count",
           "round1_entry_step":"avsp_diag_round1_entry_step",
           "round1_entry_timer_decrements":"avsp_diag_round1_entry_timer_decrements",
           "round1_entry_gate8236":"avsp_diag_round1_entry_gate8236",
           "round1_entry_gate81af":"avsp_diag_round1_entry_gate81af",
           "round1_control_enabled":"avsp_diag_round1_control_enabled",
           "round1_failure_count":"avsp_diag_round1_failure_count",
           "round1_player_x":"avsp_diag_round1_player_x",
           "round1_player_z":"avsp_diag_round1_player_z",
           "round1_player_facing":"avsp_diag_round1_player_facing",
           "round1_player_source_action":"avsp_diag_round1_player_source_action",
           "round1_player_controller_updates":"avsp_diag_round1_player_controller_updates",
           "round1_scheduler_frames":"avsp_diag_round1_scheduler_frames",
           "round1_scheduler_dispatches":"avsp_diag_round1_scheduler_dispatches",
           "round1_scheduler_trace_count":"avsp_diag_round1_scheduler_trace_count",
           "round1_scheduler_order_hash":"avsp_diag_round1_scheduler_order_hash",
           "round1_actor_handler_dispatches":"avsp_diag_round1_actor_handler_dispatches",
           "round1_presentation_bindings":"avsp_diag_round1_presentation_bindings",
           "round1_state_context_bindings":"avsp_diag_round1_state_context_bindings",
           "round1_navigation_bound_x":"avsp_diag_round1_navigation_bound_x",
           "round1_navigation_bound_z":"avsp_diag_round1_navigation_bound_z",
           "round1_navigation_applications":"avsp_diag_round1_navigation_applications",
           "round1_navigation_clamps":"avsp_diag_round1_navigation_clamps",
           "round1_navigation_obstacle_responses":"avsp_diag_round1_navigation_obstacle_responses",
           "round1_navigation_terrain_responses":"avsp_diag_round1_navigation_terrain_responses",
           "round1_navigation_terrain_retries":"avsp_diag_round1_navigation_terrain_retries",
           "round1_camera_x_position":"avsp_diag_round1_camera_x_position",
           "round1_camera_x_target":"avsp_diag_round1_camera_x_target",
           "round1_camera_x_lower":"avsp_diag_round1_camera_x_lower",
           "round1_camera_x_upper":"avsp_diag_round1_camera_x_upper",
           "round1_camera_scroll2_x":"avsp_diag_round1_camera_scroll2_x",
           "round1_camera_phase":"avsp_diag_round1_camera_phase",
           "round1_camera_countdown":"avsp_diag_round1_camera_countdown",
           "round1_camera_locks":"avsp_diag_round1_camera_locks",
           "round1_camera_unlocks":"avsp_diag_round1_camera_unlocks",
           "round1_player_stop_ticks":"avsp_diag_round1_player_stop_ticks",
           "round1_player_stop_entries":"avsp_diag_round1_player_stop_entries",
           "round1_player_stop_completions":"avsp_diag_round1_player_stop_completions",
           "round1_player_stop_motion_suppressions":"avsp_diag_round1_player_stop_motion_suppressions"}
mapping.update({
           "round1_player_melee_entries":"avsp_diag_round1_player_melee_entries",
           "round1_player_melee_completions":"avsp_diag_round1_player_melee_completions",
           "round1_player_melee_selector_mask":"avsp_diag_round1_player_melee_selector_mask",
           "round1_player_melee_presentation_mask":"avsp_diag_round1_player_melee_presentation_mask",
           "round1_player_melee_interruptions":"avsp_diag_round1_player_melee_interruptions",
           "round1_player_weapon_entries":"avsp_diag_round1_player_weapon_entries",
           "round1_player_weapon_completions":"avsp_diag_round1_player_weapon_completions",
           "round1_player_weapon_attempts":"avsp_diag_round1_player_weapon_attempts",
           "round1_player_weapon_allocations":"avsp_diag_round1_player_weapon_allocations",
           "round1_player_weapon_allocation_failures":"avsp_diag_round1_player_weapon_allocation_failures",
           "round1_player_weapon_resource_debits":"avsp_diag_round1_player_weapon_resource_debits",
           "round1_player_weapon_presentation_bindings":"avsp_diag_round1_player_weapon_presentation_bindings",
           "round1_player_weapon_empty_requests":"avsp_diag_round1_player_weapon_empty_requests",
           "round1_player_weapon_empty_allocations":"avsp_diag_round1_player_weapon_empty_allocations",
           "round1_player_weapon_empty_allocation_failures":"avsp_diag_round1_player_weapon_empty_allocation_failures",
           "round1_player_weapon_empty_releases":"avsp_diag_round1_player_weapon_empty_releases",
           "round1_player_weapon_empty_presentation_bindings":"avsp_diag_round1_player_weapon_empty_presentation_bindings",
           "round1_player_weapon_interruptions":"avsp_diag_round1_player_weapon_interruptions",
           "round1_player_resource":"avsp_diag_round1_player_resource",
           "round1_player_resource_recharge":"avsp_diag_round1_player_resource_recharge",
           "round1_player_weapon_projectile_free":"avsp_diag_round1_player_weapon_projectile_free",
           "round1_player_weapon_impact_requests":"avsp_diag_round1_player_weapon_impact_requests",
           "round1_player_weapon_impact_allocations":"avsp_diag_round1_player_weapon_impact_allocations",
           "round1_player_weapon_impact_allocation_failures":"avsp_diag_round1_player_weapon_impact_allocation_failures",
           "round1_player_weapon_impact_audio_events":"avsp_diag_round1_player_weapon_impact_audio_events",
           "round1_player_weapon_impact_releases":"avsp_diag_round1_player_weapon_impact_releases",
           "round1_player_weapon_impact_presentation_bindings":"avsp_diag_round1_player_weapon_impact_presentation_bindings",
           "round1_native_weapon_forbidden_identity":"avsp_diag_round1_native_weapon_forbidden_identity",
           "round1_native_tile_pin_exhaustions":"avsp_diag_round1_native_tile_pin_exhaustions",
           "round1_native_tile_unique_peak":"avsp_diag_round1_native_tile_unique_peak",
           "round1_native_tile_unique_peak_frame":"avsp_diag_round1_native_tile_unique_peak_frame",
           "round1_native_tile_unique_overflow":"avsp_diag_round1_native_tile_unique_overflow",
           "round1_first_encounter_scheduler_updates":"avsp_diag_round1_first_encounter_scheduler_updates",
           "round1_first_encounter_player_contacts":"avsp_diag_round1_first_encounter_player_contacts",
           "round1_first_encounter_alien_contacts":"avsp_diag_round1_first_encounter_alien_contacts",
           "round1_first_encounter_player_damage_events":"avsp_diag_round1_first_encounter_player_damage_events",
           "round1_first_encounter_alien_damage_events":"avsp_diag_round1_first_encounter_alien_damage_events",
           "round1_first_encounter_lifecycle_releases":"avsp_diag_round1_first_encounter_lifecycle_releases",
           "round1_first_encounter_clear_events":"avsp_diag_round1_first_encounter_clear_events",
           "round1_first_encounter_reaction_active":"avsp_diag_round1_first_encounter_reaction_active",
           "round1_first_encounter_reaction_elapsed":"avsp_diag_round1_first_encounter_reaction_elapsed",
           "round1_native_initial_actor_render_commands":"avsp_diag_round1_native_initial_actor_render_commands",
           "round1_native_empty_effect_render_frames":"avsp_diag_round1_native_empty_effect_render_frames",
           "round1_native_presentation_decode_failures":"avsp_diag_round1_native_presentation_decode_failures",
           "round1_decode_failure_actor_type":"avsp_diag_round1_decode_failure_actor_type",
           "round1_decode_failure_actor_class":"avsp_diag_round1_decode_failure_actor_class",
           "round1_decode_failure_animation_record":"avsp_diag_round1_decode_failure_animation_record",
           "round1_decode_failure_assembly":"avsp_diag_round1_decode_failure_assembly",
           "round1_class1f_initializations":"avsp_diag_round1_class1f_initializations",
           "round1_class1f_initial_rng_calls":"avsp_diag_round1_class1f_initial_rng_calls",
           "round1_class1f_transition_completions":"avsp_diag_round1_class1f_transition_completions",
           "round1_class1f_effect_allocations":"avsp_diag_round1_class1f_effect_allocations",
           "round1_class1f_effect_allocation_failures":"avsp_diag_round1_class1f_effect_allocation_failures",
           "round1_class1f_audio_events":"avsp_diag_round1_class1f_audio_events",
           "round1_class1f_audio_command":"avsp_diag_round1_class1f_audio_command",
           "round1_class09_rng_calls":"avsp_diag_round1_class09_rng_calls",
           "round1_class4e_initializations":"avsp_diag_round1_class4e_initializations",
           "round1_class4e_releases":"avsp_diag_round1_class4e_releases",
           "round1_class44_guard_clears":"avsp_diag_round1_class44_guard_clears",
           "round1_scheduler_failure_code":"avsp_diag_round1_scheduler_failure_code"})
state = {key:signed(mcp,syms[symbol]) for key,symbol in mapping.items()}
observed_frame = state["frame"]
# The gate above observed the complete stage-7 evidence frame before issuing
# the asynchronous debugger pause.  Yaba may stop inside the following frame
# at any stage 1..7; normalize this field to the gated evidence boundary just
# as the ledger-backed frame and native counters below are normalized.
state["frame_stage"] = 7
current_sample = next((sample for sample in all_samples
                       if sample["frame"] == observed_frame), None)
if current_sample is None:
    current_sample = all_samples[-1]
evidence_sample = next((sample for sample in all_samples
                        if sample["frame"] == EVIDENCE_LAST_FRAME), None)
if evidence_sample is None:
    raise RuntimeError("fixed evidence-frame diagnostic sample is unavailable")
for key in ("round1_player_x", "round1_player_z", "round1_player_facing",
            "round1_player_source_action", "round1_player_controller_updates",
            "round1_scheduler_frames", "round1_scheduler_dispatches",
            "round1_scheduler_trace_count", "round1_scheduler_order_hash",
            "round1_actor_handler_dispatches", "round1_presentation_bindings",
            "round1_state_context_bindings", "round1_navigation_applications",
            "round1_navigation_obstacle_responses",
            "round1_navigation_terrain_responses",
            "round1_navigation_terrain_retries", "round1_camera_countdown",
            "round1_camera_phase", "round1_camera_locks",
            "round1_camera_unlocks",
            ):
    state[key] = evidence_sample[key]
state["round1_camera_scroll2_x"] = evidence_sample["camera_world_x"]
state["round1_camera_x_position"] = evidence_sample["camera_world_x"] + 64
state["round1_camera_x_target"] = state["round1_camera_x_position"]
stop_state = evidence_sample["round1_player_stop_state"] & 0xffffffff
state["round1_player_stop_ticks"] = stop_state & 0x0f
state["round1_player_stop_entries"] = (stop_state >> 4) & 0xff
state["round1_player_stop_completions"] = (stop_state >> 12) & 0xff
state["round1_player_stop_motion_suppressions"] = (stop_state >> 20) & 0x0fff
weapon_state0 = evidence_sample["round1_player_weapon_state0"] & 0xffffffff
weapon_state1 = evidence_sample["round1_player_weapon_state1"] & 0xffffffff
state["round1_player_weapon_entries"] = weapon_state0 & 0x0f
state["round1_player_weapon_completions"] = (weapon_state0 >> 4) & 0x0f
state["round1_player_weapon_attempts"] = (weapon_state0 >> 8) & 0x3f
state["round1_player_weapon_allocations"] = (weapon_state0 >> 14) & 0x1f
state["round1_player_weapon_allocation_failures"] = (weapon_state0 >> 19) & 0x1f
state["round1_player_weapon_resource_debits"] = (weapon_state0 >> 24) & 0x1f
state["round1_player_weapon_presentation_bindings"] = weapon_state1 & 0x7f
state["round1_player_weapon_empty_requests"] = (weapon_state1 >> 7) & 0x0f
state["round1_player_weapon_interruptions"] = (weapon_state1 >> 11) & 0x0f
state["round1_player_resource"] = (weapon_state1 >> 15) & 0x7f
state["round1_player_resource_recharge"] = (weapon_state1 >> 22) & 0x0f
state["round1_player_weapon_projectile_free"] = (weapon_state1 >> 26) & 0x1f
class1f_state = evidence_sample["round1_class1f_state"] & 0xffffffff
state["round1_class1f_initializations"] = class1f_state & 0x0f
state["round1_class1f_initial_rng_calls"] = (class1f_state >> 4) & 0x0f
state["round1_class1f_transition_completions"] = (class1f_state >> 8) & 0x0f
state["round1_class1f_effect_allocations"] = (class1f_state >> 12) & 0x0f
state["round1_class1f_effect_allocation_failures"] = (class1f_state >> 16) & 0x0f
state["round1_class1f_audio_events"] = (class1f_state >> 20) & 0x0f
state["round1_class1f_audio_command"] = (class1f_state >> 24) & 0xff
auxiliary_state = evidence_sample["round1_auxiliary_state"] & 0xffffffff
state["round1_class09_rng_calls"] = auxiliary_state & 0x0fff
state["round1_class4e_initializations"] = (auxiliary_state >> 12) & 0x0f
state["round1_class4e_releases"] = (auxiliary_state >> 16) & 0x0f
state["round1_class44_guard_clears"] = (auxiliary_state >> 20) & 0x0f
state["round1_scheduler_failure_code"] = (auxiliary_state >> 24) & 0xff
native_initial_state = evidence_sample["round1_native_initial_state"] & 0xffffffff
state["round1_native_initial_actor_render_commands"] = \
    native_initial_state & 0x00000fff
state["round1_native_presentation_decode_failures"] = \
    (native_initial_state >> 12) & 0x0f
state["round1_rng_seed"] = (native_initial_state >> 16) & 0xffff
for sample in all_samples[:EVIDENCE_LAST_FRAME + 1]:
    jump_state = sample["round1_player_jump_state"] & 0xffffffff
    sample["round1_player_jump_entries"] = jump_state & 0x03
    sample["round1_player_jump_completions"] = (jump_state >> 2) & 0x03
    sample["round1_player_jump_landings"] = (jump_state >> 4) & 0x03
    sample["round1_player_jump_motion_updates"] = (jump_state >> 6) & 0x3f
    sample["round1_player_jump_active"] = (jump_state >> 12) & 0x01
    sample["round1_player_jump_collision_selector"] = (jump_state >> 13) & 0x0f
    sample["round1_player_jump_presentation_selector"] = (jump_state >> 17) & 0x3f
    sample["round1_player_jump_height"] = (jump_state >> 23) & 0xff
    sample["round1_native_player_rendered"] = (jump_state >> 31) & 0x01
jump_evidence = all_samples[EVIDENCE_LAST_FRAME]
for key in ("round1_player_jump_entries", "round1_player_jump_completions",
            "round1_player_jump_landings", "round1_player_jump_motion_updates",
            "round1_player_jump_active", "round1_player_jump_collision_selector",
            "round1_player_jump_presentation_selector",
            "round1_player_jump_height"):
    state[key] = jump_evidence[key]
state["round1_native_player_render_frames"] = sum(
    sample["round1_native_player_rendered"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
for sample in all_samples[:EVIDENCE_LAST_FRAME + 1]:
    native_presentation = sample["round1_native_presentation_state"] & 0xffffffff
    sample["round1_native_weapon_parent_render_commands"] = \
        native_presentation & 0x00ff
    sample["round1_native_weapon_child_render_commands"] = \
        (native_presentation >> 8) & 0x00ff
    sample["round1_native_projectile_render_commands"] = \
        sample["round1_native_weapon_parent_render_commands"] + \
        sample["round1_native_weapon_child_render_commands"]
    sample["round1_native_presentation_decode_failures"] = \
        (native_presentation >> 16) & 0x000f
    sample["round1_native_projectile_collision_writes"] = \
        (native_presentation >> 20) & 0x003f
    sample["round1_native_projectile_damage_writes"] = \
        (native_presentation >> 26) & 0x003f
state["round1_native_projectile_render_frames"] = sum(
    sample["round1_native_projectile_render_commands"] > 0
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_native_weapon_parent_render_frames"] = sum(
    sample["round1_native_weapon_parent_render_commands"] > 0
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_native_weapon_child_render_frames"] = sum(
    sample["round1_native_weapon_child_render_commands"] > 0
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_native_projectile_render_commands_peak"] = max(
    sample["round1_native_projectile_render_commands"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_native_weapon_parent_render_commands_peak"] = max(
    sample["round1_native_weapon_parent_render_commands"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_native_weapon_child_render_commands_peak"] = max(
    sample["round1_native_weapon_child_render_commands"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_native_presentation_decode_failures"] = max(
    sample["round1_native_presentation_decode_failures"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_native_projectile_collision_writes"] = max(
    sample["round1_native_projectile_collision_writes"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_native_projectile_damage_writes"] = max(
    sample["round1_native_projectile_damage_writes"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
for sample in all_samples[:EVIDENCE_LAST_FRAME + 1]:
    identity_state = sample["round1_player_identity_state"] & 0xffffffff
    sample["round1_player_character_id"] = identity_state & 0xff
    sample["round1_weapon_parent_active"] = (identity_state >> 8) & 0xff
    sample["round1_weapon_child_active"] = (identity_state >> 16) & 0xff
    sample["round1_weapon_forbidden_actor_active"] = \
        (identity_state >> 24) & 0x01
    sample["round1_weapon_forbidden_render_seen"] = \
        (identity_state >> 25) & 0x01
state["round1_player_character_id"] = max(
    sample["round1_player_character_id"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_weapon_parent_active_peak"] = max(
    sample["round1_weapon_parent_active"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_weapon_child_active_peak"] = max(
    sample["round1_weapon_child_active"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_weapon_forbidden_actor_active"] = max(
    sample["round1_weapon_forbidden_actor_active"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["round1_weapon_forbidden_render_seen"] = max(
    sample["round1_weapon_forbidden_render_seen"]
    for sample in all_samples[:EVIDENCE_LAST_FRAME + 1])
state["frame"] = EVIDENCE_LAST_FRAME
for key in ("player_health", "player_state", "player_facing",
            "player_animation_record", "player_assembly", "player_screen_y",
            "alien_health", "alien_state", "alien_action", "alien_facing",
            "alien_animation_record", "alien_assembly", "alien_screen_y"):
    state[key] = current_sample[key]
samples = [sample for sample in all_samples
           if sample["frame"] <= EVIDENCE_LAST_FRAME]
if args.coffee_shop_scene:
    if (len(samples) != EVIDENCE_LAST_FRAME + 1 or
            any(sample["frame"] != index
                for index, sample in enumerate(samples))):
        raise RuntimeError("Coffee Shop synchronized ledger is incomplete")
    input_header = (ROOT / "src/port_v2/gameplay/round1/"
                    "spec02_round1_entry_data.h").read_text(encoding="ascii")
    input_body = input_header.split(
        "avsp_round1_coffee_shop_input_runs", 1)[1].split(
            "avsp_round1_coffee_shop_update_cadence", 1)[0]
    input_runs = [tuple(int(value, 0) for value in match)
                  for match in __import__("re").findall(
                      r"\{\s*(\d+)u,\s*(\d+)u,\s*(0x[0-9a-fA-F]+)u\s*\}",
                      input_body)]
    if not input_runs:
        raise RuntimeError("Coffee Shop source input fixture is empty")
    for sample in samples:
        source_frame = sample["round1_source_frame"]
        input_source_frame = source_frame - 1
        expected_input = next(
            (mask for first, last, mask in input_runs
             if first <= input_source_frame <= last), 0)
        if sample["input_mask"] != expected_input:
            raise RuntimeError(
                "Coffee Shop source input drift at source frame %d: %04x != %04x"
                % (input_source_frame, sample["input_mask"], expected_input))
    by_visible_source_frame = {sample["round1_source_frame"]: sample
                               for sample in samples}
    by_scheduler_source_frame = {
        sample["round1_scheduler_source_frame"]: sample
        for sample in samples}
    required_visible_source_frames = (2287, 2288, 2305, 2306, 2307)
    required_scheduler_source_frames = (2287, 2288, 2305, 2306)
    if any(frame not in by_visible_source_frame
           for frame in required_visible_source_frames):
        raise RuntimeError(
            "Coffee Shop visible source-frame window absent: %s"
            % [frame for frame in required_visible_source_frames
               if frame not in by_visible_source_frame])
    if any(frame not in by_scheduler_source_frame
           for frame in required_scheduler_source_frames):
        raise RuntimeError(
            "Coffee Shop scheduler source-frame window absent: %s"
            % [frame for frame in required_scheduler_source_frames
               if frame not in by_scheduler_source_frame])
    def scheduler_damage_at(frame):
        return by_scheduler_source_frame[frame][
            "round1_native_projectile_damage_writes"]
    def scheduler_collision_at(frame):
        return by_scheduler_source_frame[frame][
            "round1_native_projectile_collision_writes"]
    def visible_class4e_at(frame):
        return by_visible_source_frame[frame][
            "round1_class4e_variant1_allocations"]
    if (scheduler_damage_at(2288) != scheduler_damage_at(2287) or
            scheduler_collision_at(2288) !=
            scheduler_collision_at(2287)):
        raise RuntimeError("premature source-frame-2288 projectile contact")
    if not (scheduler_damage_at(2305) == 0 and
            scheduler_damage_at(2306) == 1 and
            scheduler_collision_at(2305) == 0 and
            scheduler_collision_at(2306) == 1):
        ordered_source_frames = sorted(by_scheduler_source_frame)
        first_damage_rise = next((frame for prior, frame in zip(
            ordered_source_frames, ordered_source_frames[1:])
            if scheduler_damage_at(frame) > scheduler_damage_at(prior)), None)
        first_collision_rise = next((frame for prior, frame in zip(
            ordered_source_frames, ordered_source_frames[1:])
            if scheduler_collision_at(frame) >
            scheduler_collision_at(prior)), None)
        raise RuntimeError(
            "scheduler-source-frame-2306 collision/damage chronology drift: "
            "collision=%s damage=%s first_collision=%s first_damage=%s" %
            ([scheduler_collision_at(2305), scheduler_collision_at(2306)],
             [scheduler_damage_at(2305), scheduler_damage_at(2306)],
             first_collision_rise,
             first_damage_rise))
    if visible_class4e_at(2307) != visible_class4e_at(2306) + 1:
        raise RuntimeError(
            "visible-source-frame-2307 class-0x4e impact allocation "
            "chronology drift: "
            f"{[visible_class4e_at(2306), visible_class4e_at(2307)]}")
    if not (state["runtime_ready"] == state["canaries_ok"] == 1 and
            state["round1_spec_bound"] == state["round1_entry_valid"] ==
            state["round1_canaries_ok"] == 1 and
            state["interface_version"] == 2 and
            state["contract_flags"] == 127 and
            state["round1_route_state"] == 4 and
            state["round1_fallback_count"] == 0 and
            state["round1_failure_count"] == 0 and
            state["round1_scheduler_failure_code"] == 0 and
            state["round1_native_presentation_decode_failures"] == 0 and
            state["round1_native_tile_pin_exhaustions"] == 0 and
            state["round1_native_tile_unique_overflow"] == 0 and
            state["round1_weapon_forbidden_actor_active"] == 0 and
            state["round1_weapon_forbidden_render_seen"] == 0 and
            state["round1_native_weapon_forbidden_identity"] == 0 and
            state["internal_failures"] == state["pcm_retriggers"] == 0 and
            state["failures"] == state["fallback_count"] ==
            state["physical_saturn"] == 0):
        raise RuntimeError(f"Coffee Shop source-ledger state failed: {state}")
if not args.coffee_shop_scene and not (
        state["runtime_ready"] == state["canaries_ok"] == 1 and
        state["interface_version"] == 2 and state["contract_flags"] == 127 and
        1 <= state["frame_stage"] <= 7 and
        state["hit_events"] == 3 and state["ko_events"] == 1 and
        state["route_unlocked"] == state["continued"] == 1 and
        state["internal_failures"] == 0 and state["pcm_retriggers"] == 0 and
        state["failures"] == state["fallback_count"] ==
        state["physical_saturn"] == 0): raise RuntimeError(f"live state failed: {state}")
if not args.coffee_shop_scene and not (
        state["alien_health"] == -1 and state["alien_state"] == 0 and
        state["alien_action"] == 0 and state["alien_animation_record"] == 0 and
        state["alien_assembly"] == 0):
    raise RuntimeError(f"released class-0x1f presentation remained live: {state}")
if not args.coffee_shop_scene and not (
        state["round1_spec_bound"] == state["round1_entry_valid"] ==
        state["round1_canaries_ok"] == 1 and
        state["round1_route_state"] == 4 and state["round1_rng_seed"] == 0x82fd and
        state["round1_player_health"] == 93 and
        [state[f"round1_pool{kind}_free"] for kind in (12,16,20,24)] ==
        [11,20,13,2] and state["round1_fallback_count"] == 0 and
        state["round1_failure_count"] == 0 and
        state["round1_entry_spawn_count"] == 10 and
        state["round1_entry_step"] == 8 and
        state["round1_entry_timer_decrements"] == 164 and
        state["round1_entry_gate8236"] == 0 and
        state["round1_entry_gate81af"] == 1 and
        state["round1_control_enabled"] == 1 and
        state["round1_player_x"] == 1091 and
        state["round1_player_z"] == 320 and
        state["round1_player_facing"] == 1 and
        state["round1_player_source_action"] == 514 and
        state["round1_player_controller_updates"] == 622 and
        state["round1_scheduler_frames"] == 792 and
        state["round1_scheduler_dispatches"] == 11261 and
        state["round1_scheduler_trace_count"] == 13 and
        state["round1_scheduler_order_hash"] == -1628184524 and
        state["round1_actor_handler_dispatches"] == 7815 and
        state["round1_presentation_bindings"] == 7814 and
        state["round1_state_context_bindings"] == 7814 and
        state["round1_navigation_bound_x"] == 832 and
        state["round1_navigation_bound_z"] == 256 and
        state["round1_navigation_applications"] == 622 and
        state["round1_navigation_clamps"] == 0 and
        state["round1_navigation_obstacle_responses"] == 53 and
        state["round1_navigation_terrain_responses"] == 0 and
        state["round1_navigation_terrain_retries"] == 0 and
        state["round1_camera_x_position"] == 832 and
        state["round1_camera_x_target"] == 832 and
        state["round1_camera_x_lower"] == 832 and
        state["round1_camera_x_upper"] == 832 and
        state["round1_camera_scroll2_x"] == 768 and
        state["round1_camera_phase"] == 2 and
        state["round1_camera_countdown"] == 1140 and
        state["round1_camera_locks"] == 1 and
        state["round1_camera_unlocks"] == 0 and
        state["round1_player_stop_ticks"] == 0 and
        state["round1_player_stop_entries"] == 2 and
        state["round1_player_stop_completions"] == 2 and
        state["round1_player_stop_motion_suppressions"] == 10 and
        state["round1_player_melee_entries"] == 5 and
        state["round1_player_melee_completions"] == 5 and
        state["round1_player_melee_selector_mask"] == 15 and
        state["round1_player_melee_presentation_mask"] == 15 and
        state["round1_player_melee_interruptions"] == 0 and
        state["round1_player_weapon_entries"] == 2 and
        state["round1_player_weapon_completions"] == 2 and
        state["round1_player_weapon_attempts"] == 1 and
        state["round1_player_weapon_allocations"] == 6 and
        state["round1_player_weapon_allocation_failures"] == 0 and
        state["round1_player_weapon_resource_debits"] == 1 and
        state["round1_player_weapon_presentation_bindings"] == 40 and
        state["round1_player_weapon_empty_requests"] == 1 and
        state["round1_player_weapon_empty_allocations"] == 1 and
        state["round1_player_weapon_empty_allocation_failures"] == 0 and
        state["round1_player_weapon_empty_releases"] == 1 and
        state["round1_player_weapon_empty_presentation_bindings"] == 10 and
        state["round1_player_weapon_interruptions"] == 0 and
        state["round1_player_resource"] == 16 and
        state["round1_player_resource_recharge"] == 3 and
        state["round1_player_weapon_projectile_free"] == 24 and
        state["round1_player_jump_entries"] == 1 and
        state["round1_player_jump_completions"] == 1 and
        state["round1_player_jump_landings"] == 1 and
        state["round1_player_jump_motion_updates"] == 35 and
        state["round1_player_jump_active"] == 0 and
        state["round1_player_jump_collision_selector"] == 3 and
        state["round1_player_jump_presentation_selector"] == 10 and
        state["round1_player_jump_height"] == 0 and
        state["round1_native_player_render_frames"] > 0 and
        state["round1_native_initial_actor_render_commands"] > 0 and
        state["round1_native_empty_effect_render_frames"] == 0 and
        state["round1_native_tile_pin_exhaustions"] == 0 and
        state["round1_native_tile_unique_peak"] <= 218 and
        state["round1_native_tile_unique_overflow"] == 0 and
        state["round1_class1f_initializations"] == 10 and
        state["round1_class1f_initial_rng_calls"] == 10 and
        state["round1_class1f_transition_completions"] == 10 and
        state["round1_class1f_effect_allocations"] == 2 and
        state["round1_class1f_effect_allocation_failures"] == 2 and
        state["round1_class1f_audio_events"] == 2 and
        state["round1_class1f_audio_command"] == 0x4d and
        state["round1_class09_rng_calls"] == 196 and
        state["round1_class4e_initializations"] == 2 and
        state["round1_class4e_releases"] == 2 and
        state["round1_class44_guard_clears"] == 1 and
        state["round1_scheduler_failure_code"] == 0 and
        state["round1_player_weapon_impact_requests"] == 0 and
        state["round1_player_weapon_impact_allocations"] == 0 and
        state["round1_player_weapon_impact_allocation_failures"] == 0 and
        state["round1_player_weapon_impact_audio_events"] == 0 and
        state["round1_player_weapon_impact_releases"] == 0 and
        state["round1_player_weapon_impact_presentation_bindings"] == 0 and
        state["round1_first_encounter_scheduler_updates"] == 469 and
        state["round1_first_encounter_player_contacts"] == 4 and
        state["round1_first_encounter_alien_contacts"] == 1 and
        state["round1_first_encounter_player_damage_events"] == 1 and
        state["round1_first_encounter_alien_damage_events"] == 4 and
        state["round1_first_encounter_lifecycle_releases"] == 1 and
        state["round1_first_encounter_clear_events"] == 1 and
        state["round1_first_encounter_reaction_active"] == 0 and
        state["round1_first_encounter_reaction_elapsed"] == 139 and
        state["round1_native_projectile_render_frames"] > 0 and
        state["round1_native_weapon_parent_render_frames"] > 0 and
        state["round1_native_weapon_child_render_frames"] > 0 and
        state["round1_native_projectile_render_commands_peak"] > 0 and
        state["round1_native_weapon_parent_render_commands_peak"] > 0 and
        state["round1_native_weapon_child_render_commands_peak"] > 0 and
        state["round1_player_character_id"] == 0 and
        state["round1_weapon_parent_active_peak"] == 1 and
        state["round1_weapon_child_active_peak"] > 0 and
        state["round1_weapon_forbidden_actor_active"] == 0 and
        state["round1_weapon_forbidden_render_seen"] == 0 and
        state["round1_native_weapon_forbidden_identity"] == 0 and
        state["round1_native_presentation_decode_failures"] == 0 and
        state["round1_native_projectile_collision_writes"] == 0 and
        state["round1_native_projectile_damage_writes"] == 0 and
        state["round1_presentation_ready"] == 1 and
        state["round1_presentation_seen"] == 1 and
        state["round1_presentation_commands_peak"] == 2):
    raise RuntimeError(f"Round 1 stable-entry target binding failed: {state}")
if (len(samples) != EVIDENCE_LAST_FRAME + 1 or
        any(sample["frame"] != index for index,sample in enumerate(samples))):
    raise RuntimeError("live synchronized ledger is incomplete")
contacts=[s for s in samples if s["player_contact"]]; received=[s for s in samples if s["alien_contact"]]
damage=[s for s in samples if s["player_damage"]]; misses=[s for s in samples if s["attack_miss"]]
unlock=next((i for i,s in enumerate(samples) if s["route_unlocked"]),None)

player_assemblies = {
    0x15F1F4:0x1626A4, 0x1600E8:0x1629E6, 0x1600F8:0x162A04,
    0x160108:0x1629E6, 0x160118:0x1629E6, 0x16012C:0x162A32,
    0x16013C:0x162A5A, 0x16014C:0x162A82, 0x16015C:0x162A5A,
    0x16016C:0x162A32, 0x16017C:0x162A32, 0x160190:0x162A32,
    0x1601A0:0x16144E, 0x1601B0:0x161476, 0x1601C0:0x1614A4,
    0x1601D0:0x161476, 0x1601E0:0x161476, 0x1601F4:0x162AA6,
    0x160204:0x162ABE, 0x160214:0x162AD6, 0x160224:0x162AFE,
    0x160234:0x162B26, 0x160244:0x162B5A, 0x160254:0x162B82,
    0x160264:0x162AA6, 0x160274:0x162AA6,
    0x15F2CC:0x160BC6, 0x15F2DC:0x160BC6,
    0x15F2F0:0x160CDA, 0x15F300:0x160D02,
    0x15F310:0x160D2A, 0x15F320:0x160D52,
    0x15F330:0x160D86, 0x15F344:0x160BEE,
    0x15F354:0x160C16, 0x15F364:0x160C3E,
    0x15F374:0x160C66, 0x15F384:0x160C84,
    0x15F394:0x160CAC, 0x15F3A4:0x160BEE,
    0x15F3B8:0x160BEE, 0x15F3C8:0x160CAC,
    0x15F3D8:0x160C84, 0x15F3E8:0x160C66,
    0x15F3F8:0x160C3E, 0x15F408:0x160C16,
    0x15F418:0x160BEE, 0x15F428:0x160BEE,
    0x15F43C:0x162BAA, 0x15F44C:0x162BC8,
    0x15F45C:0x162BAA, 0x15FC3C:0x162EE2,
    0x15FC4C:0x162EE2, 0x15FCE8:0x16212C,
    0x15FC60:0x162EE2,
}
spec_fixture = json.loads(
    (ROOT / "data/spec02_round1_generated_fixtures.json").read_text())
weapon_contract = spec_fixture["authority_data"]["player"][
    "weapon_projectile_resource"]["implementation_contract"]
weapon_timelines = list(weapon_contract["sufficient_action"][
    "presentation_selector_contract"]["selector_timelines"].values())
weapon_timelines.append(
    weapon_contract["empty_fallback"]["presentation_timeline"])
for timeline in weapon_timelines:
    for frame in timeline:
        record = int(str(frame["animation_record"]), 0)
        assembly = int(str(frame["assembly"]), 0)
        player_assemblies[record] = assembly
alien_assemblies = {
    0x12DDB0:0x130346,
    0x12EC04:0x12F7CC, 0x12EC14:0x12F7E4, 0x12EC24:0x12F7FC,
    0x12EC34:0x12F814, 0x12EC44:0x12F82C, 0x12EC54:0x12F85E,
    0x12EC64:0x12F890, 0x12EC74:0x12F8B8, 0x12E8EC:0x12F5DE,
    0x12E8FC:0x12FA0C, 0x12E90C:0x12FA2A, 0x12E91C:0x12FA0C,
    0x12D5E4:0x12FAE8, 0x12DD50:0x130248, 0x12DD28:0x13020C,
    0x12DD3C:0x13023A, 0x12D2F8:0x12F994, 0x12E214:0x13020C,
    0x12E224:0x13020C, 0x12E234:0x13020C, 0x12E244:0x13020C,
    0x12E254:0x130294, 0x12E268:0x130346,
}
class1f_contract = next(
    archetype for archetype in spec_fixture["authority_data"]["enemies"]
        ["archetypes"]
    if archetype["class"] == "0x1f")
for record_contract in class1f_contract["presentation_and_collision"]["records"]:
    if record_contract["classification"] != "SOURCE_CLOSED":
        raise RuntimeError("class-0x1f presentation contract is not source-closed")
    record = int(record_contract["animation_record"], 0)
    assembly = int(record_contract["assembly"], 0)
    if record in alien_assemblies and alien_assemblies[record] != assembly:
        raise RuntimeError(
            f"class-0x1f presentation contract conflicts at {record:#x}")
    alien_assemblies[record] = assembly
player_identity_drift = [
    {"frame":s["frame"], "state":s["player_state"],
     "record":hex(s["player_animation_record"]),
     "assembly":hex(s["player_assembly"]),
     "expected":hex(player_assemblies.get(s["player_animation_record"], 0))}
    for s in samples
    if (s["player_animation_record"] != 0 or s["player_assembly"] != 0) and
    player_assemblies.get(s["player_animation_record"]) != s["player_assembly"]
]
if player_identity_drift:
    raise RuntimeError(
        f"player animation-record/assembly ownership drift: {player_identity_drift[:12]}")
alien_identity_drift = [
    {"frame":s["frame"], "state":s["alien_state"],
     "action":hex(s["alien_action"]),
     "record":hex(s["alien_animation_record"]),
     "assembly":hex(s["alien_assembly"]),
     "expected":hex(alien_assemblies.get(s["alien_animation_record"], 0))}
    for s in samples if s["alien_state"] != 0 and
    alien_assemblies.get(s["alien_animation_record"]) != s["alien_assembly"]
]
if alien_identity_drift:
    raise RuntimeError(f"alien animation-record/assembly ownership drift: {alien_identity_drift[:8]}")
for before, after in zip(samples, samples[1:]):
    if (before["player_animation_record"] != 0 and
        after["player_animation_record"] != 0 and
        before["player_state"] == after["player_state"] == 0 and
        after["player_lane"] != before["player_lane"] and
        (after["player_screen_y"] - before["player_screen_y"]) *
            (after["player_lane"] - before["player_lane"]) >= 0):
        raise RuntimeError("world-z/screen-y sign drift")
# Retained input is deliberately zero after the native handoff. Native neutral
# release is guarded by its exact stop counters above and the focused host
# differential; this retained-presentation ledger must not recreate input
# authority merely to repeat that check.
for key in ("player_health", "player_state", "player_facing",
            "player_animation_record", "player_assembly", "player_screen_y",
            "alien_health", "alien_state", "alien_action", "alien_facing",
            "alien_animation_record", "alien_assembly", "alien_screen_y"):
    if state[key] != current_sample[key]:
        raise RuntimeError(f"same-tick diagnostic drift for {key}")
process=tools.process_record(args.emulator_pid); executable=Path(str(process["executable"]))
settings=Path(os.environ["APPDATA"])/"YabaSanshiro/yabause.ini"
report={"schema":1,"task_id":inventory["task_id"],"card_profile":inventory["card_profile"],
        "source_commit":build["source_commit"],"iso_sha256":build["artifacts"]["game_iso"]["sha256"],
        "state":state,"samples":samples,"chronology":{"player_contacts":len(contacts),
        "alien_contacts":len(received),"player_damage_events":len(damage),"misses":len(misses),
        "unlock_frame":unlock},
        "visual_scanout":"UNAVAILABLE_WINDOWS_ACCELERATED_SURFACE",
        "vdp1_texture_integrity":texture_integrity,
        "emulator":{"identity":"Yaba Sanshiro 1.20.37-2986eb","evidence_tier":"ONE_EMULATOR",
        "process_id":process["pid"],"executable_sha256":sha(executable),"settings_sha256":sha(settings),
        "command_line":process["command_line"]},"physical_saturn":"UNRUN","result":"PASS"}
if args.coffee_shop_scene:
    report["evidence_mode"] = "COFFEE_SHOP_SOURCE_LEDGER"
    report["source_chronology"] = {
        "scheduler_source_frame_2288_damage_writes":
            scheduler_damage_at(2288),
        "scheduler_source_frame_2305_damage_writes":
            scheduler_damage_at(2305),
        "scheduler_source_frame_2306_damage_writes":
            scheduler_damage_at(2306),
        "scheduler_source_frame_2306_collision_writes":
            scheduler_collision_at(2306),
        "visible_source_frame_2307_class4e_impact_allocations":
            visible_class4e_at(2307),
    }
output=run_root/("coffee-shop-readback.json" if args.coffee_shop_scene
                 else "readback.json")
output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="ascii")
print(f"recorded {output.relative_to(ROOT)}")
