#!/usr/bin/env python3
"""Generate the bounded native Round 1 entry tables from SPEC-02 fixtures."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data/spec02_round1_generated_fixtures.json"
CONTRACT = ROOT / "data/spec02_round1_executable_contract.json"
OUT = ROOT / "src/port_v2/gameplay/round1/spec02_round1_entry_data.h"

KINDS = (
    "AVSP_ROUND1_ENTRY_SET_POSITION",
    "AVSP_ROUND1_ENTRY_SET_SUBHANDLER",
    "AVSP_ROUND1_ENTRY_SOURCE_18",
    "AVSP_ROUND1_ENTRY_DWELL",
    "AVSP_ROUND1_ENTRY_DWELL",
    "AVSP_ROUND1_ENTRY_SOURCE_16",
    "AVSP_ROUND1_ENTRY_DWELL",
    "AVSP_ROUND1_ENTRY_TERMINATE",
)
LENGTHS = (6, 2, 2, 4, 4, 2, 4, 2)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> str:
    fixtures = json.loads(FIXTURES.read_text(encoding="ascii"))
    body = fixtures["authority_data"]["route"]["first_entry_body"]
    spawns = body["spawn_table"]["rows"]
    player = body["player_entry_script"]
    commands = player["source_program"]["commands"]
    program = bytes.fromhex(player["source_program"]["hex"])
    scheduler = fixtures["authority_data"]["scheduler"]
    scheduler_order = scheduler["frame_scheduler"]["required_round1_order"]
    dispatches = []
    for pool in scheduler["pools"]:
        for dispatch in pool["required_round1_dispatch"]:
            dispatches.append((pool["record_type"], int(dispatch["class"], 16)))
    class1f = next(archetype for archetype in
                   fixtures["authority_data"]["enemies"]["archetypes"]
                   if archetype["type"] == 12 and archetype["class"] == "0x1f")
    presentation = class1f["presentation_and_collision"]
    presentation_rows = presentation["records"]
    dispatch_entry = int(class1f["dispatch_entry"], 16)
    state_contexts = [tuple(int(part, 16) for part in context.split(":"))
                      for context in class1f["state_phase_contexts"]]
    navigation = fixtures["authority_data"]["navigation"]
    global_bounds = navigation["global_bounds"]
    locomotion = fixtures["authority_data"]["player"]["locomotion_neutral_facing"]
    input_decode = locomotion["input_decode"]
    release = locomotion["release_transition"]
    direction_resolver = input_decode["resolver_table"]
    melee = fixtures["authority_data"]["player"]["route_reachable_melee_actions"]
    close_combo = melee["close_combo"]
    melee_dispatch = melee["dispatch"]
    melee_sequences = close_combo["animation_sequences"]
    melee_selectors = close_combo["attack_selectors"]
    melee_steps = close_combo["step_values"]
    melee_strikes = []
    weapon = fixtures["authority_data"]["player"][
        "weapon_projectile_resource"]["implementation_contract"]
    weapon_states = weapon["state_dispatch"]
    weapon_volley = weapon["sufficient_volley"]
    weapon_resource = weapon["resource_tick"]
    weapon_empty = weapon["empty_fallback"]
    weapon_frames = weapon["presentation_timeline"]
    empty_frames = weapon_empty["presentation_timeline"]
    weapon_return_frame = weapon["return_frame"]
    first_segment_bounds = next(
        run for run in global_bounds["baseline_bound_runs"]
        if run["route"] == 4 and run["bound_x"] == 720 and
        run["bound_z"] == 256 and run["frames"] == 333)
    if len(spawns) != 10 or len(commands) != len(KINDS):
        raise ValueError("SPEC-02 entry cardinality drift")
    if [int(row["sequence"]) for row in spawns] != list(range(10)):
        raise ValueError("SPEC-02 entry spawn order drift")
    if sum(LENGTHS) != len(program) or player["timer_semantics"]["loads"] != [60, 60, 44]:
        raise ValueError("SPEC-02 entry program/timer drift")
    if scheduler_order != [12, 16, 20, 24] or len(dispatches) != 16:
        raise ValueError("SPEC-02 Round 1 scheduler/dispatch drift")
    records = [int(row["animation_record"], 16) for row in presentation_rows]
    if (presentation["orphan_records"] != 0 or
        presentation["record_count"] != len(presentation_rows) or
        records != sorted(records) or len(records) != len(set(records))):
        raise ValueError("SPEC-02 class-0x1f presentation table drift")
    if (dispatch_entry != 0x060532 or state_contexts != sorted(state_contexts) or
        len(state_contexts) != len(set(state_contexts))):
        raise ValueError("SPEC-02 class-0x1f state context drift")
    if (global_bounds["x_min"] != "bound_x + 0x20" or
        global_bounds["x_max"] != "bound_x + 0x160" or
        global_bounds["z_min"] != "bound_z + 0x10" or
        global_bounds["z_max"] != "bound_z + 0x90" or
        navigation["coordinate_contract"]["up_world_z_delta_sign"] != 1 or
        navigation["coordinate_contract"]["down_world_z_delta_sign"] != -1):
        raise ValueError("SPEC-02 first-segment global bounds drift")
    if (direction_resolver != [255, 2, 6, 255, 4, 3, 5, 255,
                              0, 1, 7, 255, 255, 255, 255, 255] or
        release["walking_action"] != "0x0202" or
        release["stop_action"] != "0x0204" or
        release["stop_timer"]["ticks"] != 10 or
        release["stop_guard"] !=
            "+0x0c direction becomes negative when no valid direction is held" or
        release["cleanup_writer"] !=
            "0x01a3fa writes inner/action long 0x02000000" or
        release["idle_phase_writer"] !=
            "0x0198de writes action low byte 0x02 on the next update" or
        release["facing_rule"] !=
            "neutral performs no +0x0f write and preserves the last directional facing"):
        raise ValueError("SPEC-02 locomotion-to-neutral transition drift")
    if (melee["classification"] != "SOURCE_CLOSED" or
        melee["input_guard"] !=
            "new Button2 edge from actor +0xee/+0xef bit 5" or
        melee_dispatch["common_action"] != "0x0600" or
        melee_dispatch["target_context_action"] != "0x1400" or
        melee_dispatch["target_context_guard"] != "actor +0x5a nonzero" or
        close_combo["entry"] != "0x022588" or
        close_combo["followup_window"]["ticks"] != 30 or
        close_combo["held_input_rule"] !=
            "held Button2 does not create a new edge or auto-chain" or
        melee_selectors != [1, 2, 3, 4] or melee_steps != [0, 1, 2, 3] or
        melee["rng_consumption"] !=
            "none for selector or assembly choice; state selects the measured animation record"):
        raise ValueError("SPEC-02 route-reachable melee contract drift")
    for selector in melee_selectors:
        sequence = melee_sequences[f"close_{selector}"]
        strikes = [row for row in sequence
                   if row["attack_selector"] == selector]
        if len(strikes) != 1:
            raise ValueError("SPEC-02 melee strike presentation drift")
        melee_strikes.append(strikes[0])
    if (weapon["classification"] != "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" or
        weapon["source_input"]["button1_mask"] != "0x0010" or
        weapon_states != {
            "sufficient_entry_action": "0x0c00",
            "sufficient_active_action": "0x0c02",
            "empty_entry_action": "0x1a00",
            "empty_active_action": "0x1a02",
            "cleanup_action": "0x0000",
            "return_locomotion_action": "0x0002"} or
        weapon_volley["attempt_counter_type"] != "s8" or
        weapon_volley["attempt_counter_initial"] != 12 or
        weapon_volley["cadence_counter_type"] != "u8" or
        weapon_volley["cadence_initial"] != 1 or
        weapon_volley["cadence_reload"] != 4 or
        weapon_volley["spawn_tick_offsets"] != list(range(0, 48, 4)) or
        weapon_volley["cleanup_tick_offset"] != 49 or
        weapon_volley["return_to_locomotion_tick_offset"] != 50 or
        weapon_volley["recovery_edge"] != {
            "input_tick_offset": 48,
            "cleanup_tick_offset": 49,
            "second_entry_tick_offset": 50} or
        weapon_volley["resource_debit"] != 3 or
        weapon_volley["resource_clamp_min"] != 0 or
        weapon_volley["resource_capacity"] != 64 or
        weapon_volley["recharge_countdown_after_success"] != 12 or
        weapon_volley["rng_calls"] != 0 or
        weapon_resource["normal_recharge_reload"] != 2 or
        weapon_resource["depleted_recharge_reload"] != 6 or
        weapon_empty["timer_type"] != "u8" or
        weapon_empty["timer_initial"] != 16 or
        weapon_empty["cleanup_tick_offset"] != 17 or
        weapon_empty["return_to_locomotion_tick_offset"] != 18 or
        weapon_empty["damaging_projectile_count"] != 0 or
        weapon["movement_facing"]["baseline_invariant"] is not True):
        raise ValueError("SPEC-02 Button1 action/resource contract drift")
    allocation = weapon_volley["successful_allocation_writes"]
    blocker = weapon["projectile_lifecycle_implementation_blocker"]
    if (allocation != {
            "active_increment": 1,
            "attack_table": "0x03136a",
            "class": "0x05",
            "facing": "copy player facing",
            "owner": "player low-word pointer",
            "position": "copy player x/y/z",
            "variant": "0 except attempt counter 4 writes 1"} or
        blocker["spec_executable"] is not False or
        len(blocker["missing_fields"]) != 5):
        raise ValueError("SPEC-02 projectile allocation/blocker drift")
    projectile_authority = fixtures["authority_data"]["player"][
        "weapon_projectile_resource"]["authority_separation"][
            "projectile_lifecycle"]
    if (projectile_authority["pool"] !=
            "record type 4; base 0xff8680; capacity 24; stride 0x80" or
        projectile_authority["allocator"] != "0x01773e" or
        projectile_authority["class"] != "0x05"):
        raise ValueError("SPEC-02 projectile allocator identity drift")
    if ([row["tick"] for row in weapon_frames] != list(range(50)) or
        [row["tick"] for row in empty_frames] != list(range(18)) or
        weapon_frames[0]["action"] != 0x0c00 or
        any(row["action"] != 0x0c02 for row in weapon_frames[1:49]) or
        weapon_frames[49]["action"] != 0 or
        empty_frames[0]["action"] != 0x1a00 or
        any(row["action"] != 0x1a02 for row in empty_frames[1:17]) or
        empty_frames[17]["action"] != 0 or
        weapon_return_frame != {
            "tick": 50, "action": 2, "substate": 2,
            "animation_record": "0x00163158",
            "assembly": "0x00165488", "hurt_selector": 1,
            "attack_selector": 0}):
        raise ValueError("SPEC-02 Button1 presentation timeline drift")

    cursor = int(player["initial_cursor"], 16)
    step_rows = []
    for index, (command, kind, length) in enumerate(zip(commands, KINDS, LENGTHS)):
        opcode = int(command["opcode"], 16)
        args = bytes.fromhex(command["arguments_hex"])
        encoded = bytes([opcode]) + args
        if encoded != program[cursor - int(player["initial_cursor"], 16):
                              cursor - int(player["initial_cursor"], 16) + length]:
            raise ValueError(f"SPEC-02 entry command {index} encoding drift")
        if len(encoded) != length:
            raise ValueError(f"SPEC-02 entry command {index} length drift")
        arg0 = arg1 = arg2 = 0
        if kind == "AVSP_ROUND1_ENTRY_SET_POSITION":
            arg0 = int(player["position"]["x"])
            arg1 = int(player["position"]["z"])
        elif kind == "AVSP_ROUND1_ENTRY_SET_SUBHANDLER":
            arg0 = 8
        elif kind == "AVSP_ROUND1_ENTRY_SOURCE_18":
            arg0 = args[0]
        elif kind == "AVSP_ROUND1_ENTRY_DWELL":
            arg0 = args[0]
            arg1 = int.from_bytes(args[1:3], "big")
        elif kind == "AVSP_ROUND1_ENTRY_SOURCE_16":
            arg0 = args[0]
        step_rows.append((kind, opcode, arg0, arg1, arg2, cursor, cursor + length))
        cursor += length
    if cursor != int(player["source_program"]["last_exclusive"], 16):
        raise ValueError("SPEC-02 entry terminal cursor drift")

    lines = [
        "#ifndef AVSP_SPEC02_ROUND1_ENTRY_DATA_H",
        "#define AVSP_SPEC02_ROUND1_ENTRY_DATA_H",
        "",
        f"/* contract_sha256={sha(CONTRACT)} */",
        f"/* fixtures_sha256={sha(FIXTURES)} */",
        f"#define AVSP_ROUND1_ENTRY_PROGRAM_SHA256 \"{player['source_program']['sha256']}\"",
        "",
        "static const unsigned char avsp_round1_entry_program[AVSP_ROUND1_ENTRY_PROGRAM_BYTES] =",
        "{",
    ]
    for offset in range(0, len(program), 13):
        chunk = ", ".join(f"0x{value:02X}u" for value in program[offset:offset + 13])
        lines.append(f"    {chunk}{',' if offset + 13 < len(program) else ''}")
    lines.extend(["};", "", "static const AvspRound1EntrySpawnSpec avsp_round1_entry_spawns[AVSP_ROUND1_FIRST_SPAWN_COUNT] =", "{"])
    for row in spawns:
        post = row["post_initial_dispatch"]
        lines.append(
            "    { %su, %du, %d, %d, %d, 0x%02Xu, %du, %du, %du, %du, %du, %su, %d }," % (
                row["slot"], row["record_type"], row["x"], row["y"], row["z"],
                int(row["class"], 16), row["variant"], row["source_action"],
                post["state"], post["substate"], post["facing"],
                post["animation_record"], post["health"]))
    lines.extend(["};", "", "static const AvspRound1EntryStepSpec avsp_round1_entry_steps[AVSP_ROUND1_ENTRY_STEP_COUNT] =", "{"])
    for kind, opcode, arg0, arg1, arg2, first, last in step_rows:
        lines.append(
            f"    {{ {kind}, 0x{opcode:02X}u, {arg0}u, {arg1}u, {arg2}u, 0x{first:08X}UL, 0x{last:08X}UL }},")
    lines.extend([
        "};", "",
        "static const unsigned char avsp_round1_scheduler_pool_order[AVSP_ROUND1_SCHEDULER_POOL_COUNT] =",
        "{",
        "    " + ", ".join(f"{value}u" for value in scheduler_order),
        "};", "",
        "static const AvspRound1DispatchSpec avsp_round1_required_dispatches[AVSP_ROUND1_REQUIRED_DISPATCH_COUNT] =",
        "{",
    ])
    for record_type, actor_class in dispatches:
        lines.append(f"    {{ {record_type}u, 0x{actor_class:02X} }},")
    lines.extend([
        "};", "",
        f"#define AVSP_ROUND1_CLASS1F_PRESENTATION_COUNT {len(presentation_rows)}u",
        "static const AvspRound1PresentationSpec avsp_round1_class1f_presentation[AVSP_ROUND1_CLASS1F_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in presentation_rows:
        lines.append(
            "    { %sUL, %sUL, %du, %du }," % (
                row["animation_record"], row["assembly"],
                row["hurt_selector"], row["attack_selector"]))
    lines.extend([
        "};", "",
        f"#define AVSP_ROUND1_CLASS1F_DISPATCH_ENTRY 0x{dispatch_entry:06X}UL",
        f"#define AVSP_ROUND1_CLASS1F_STATE_CONTEXT_COUNT {len(state_contexts)}u",
        "static const AvspRound1StateContextSpec avsp_round1_class1f_state_contexts[AVSP_ROUND1_CLASS1F_STATE_CONTEXT_COUNT] =",
        "{",
    ])
    for state, substate in state_contexts:
        lines.append(f"    {{ 0x{state:04X}u, 0x{substate:04X}u }},")
    bound_x = first_segment_bounds["bound_x"]
    bound_z = first_segment_bounds["bound_z"]
    lines.extend([
        "};", "",
        "static const AvspRound1NavigationBoundsSpec avsp_round1_first_segment_bounds =",
        "{",
        f"    {bound_x}, {bound_z}, {bound_x + 0x20}, {bound_x + 0x160},",
        f"    {bound_z + 0x10}, {bound_z + 0x90}",
        "};", "",
        "static const AvspRound1PlayerLocomotionSpec avsp_round1_player_locomotion =",
        "{",
        f"    {int(release['walking_action'], 16)}u,",
        f"    {int(release['stop_action'], 16)}u,",
        "    512u,",
        f"    {release['stop_timer']['ticks']}u,",
        "    {" + ", ".join(f"{value}u" for value in direction_resolver) + "}",
        "};", "",
        "static const AvspRound1PlayerMeleeSpec avsp_round1_player_melee =",
        "{",
        f"    {int(melee_dispatch['common_action'], 16)}u,",
        f"    {int(melee_dispatch['target_context_action'], 16)}u,",
        f"    {close_combo['followup_window']['ticks']}u,",
        f"    {len(melee_selectors)}u,",
        "    {" + ", ".join(f"{value}u" for value in melee_selectors) + "},",
        "    {" + ", ".join(f"{value}u" for value in melee_steps) + "}",
        "};", "",
        "static const AvspRound1PresentationSpec avsp_round1_player_melee_strikes[AVSP_ROUND1_PLAYER_MELEE_COUNT] =",
        "{",
    ])
    for row in melee_strikes:
        lines.append(
            "    { %sUL, %sUL, %du, %du }," % (
                row["record"], row["assembly"], row["hurt_selector"],
                row["attack_selector"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerWeaponSpec avsp_round1_player_weapon =",
        "{",
        f"    {int(weapon_states['sufficient_entry_action'], 16)}u,",
        f"    {int(weapon_states['sufficient_active_action'], 16)}u,",
        f"    {int(weapon_states['empty_entry_action'], 16)}u,",
        f"    {int(weapon_states['empty_active_action'], 16)}u,",
        f"    {int(weapon_states['cleanup_action'], 16)}u,",
        f"    {int(weapon_states['return_locomotion_action'], 16)}u,",
        f"    {weapon_volley['attempt_counter_initial']},",
        f"    {weapon_volley['cadence_initial']}u,",
        f"    {weapon_volley['cadence_reload']}u,",
        f"    {weapon_empty['timer_initial']}u,",
        f"    {weapon_volley['resource_capacity']}u,",
        f"    {weapon_volley['resource_debit']}u,",
        f"    {weapon_volley['recharge_countdown_after_success']}u,",
        f"    {weapon_resource['normal_recharge_reload']}u,",
        f"    {weapon_resource['depleted_recharge_reload']}u,",
        "    0x05,",
        "    0x8680u,",
        "    0x0080u,",
        "    0x8380u,",
        "    0x03136aUL",
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_frames[AVSP_ROUND1_PLAYER_WEAPON_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in weapon_frames:
        lines.append(
            "    { %du, %du, %sUL, %sUL, %du, %du }," % (
                row["action"], row["substate"], row["animation_record"],
                row["assembly"], row["hurt_selector"],
                row["attack_selector"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_empty_frames[AVSP_ROUND1_PLAYER_EMPTY_PRESENTATION_COUNT] =",
        "{",
    ])
    for row in empty_frames:
        lines.append(
            "    { %du, %du, %sUL, %sUL, %du, %du }," % (
                row["action"], row["substate"], row["animation_record"],
                row["assembly"], row["hurt_selector"],
                row["attack_selector"]))
    lines.extend([
        "};", "",
        "static const AvspRound1PlayerWeaponFrameSpec avsp_round1_player_weapon_return_frame =",
        "{",
        "    %du, %du, %sUL, %sUL, %du, %du" % (
            weapon_return_frame["action"], weapon_return_frame["substate"],
            weapon_return_frame["animation_record"],
            weapon_return_frame["assembly"],
            weapon_return_frame["hurt_selector"],
            weapon_return_frame["attack_selector"]),
        "};", "", "#endif", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = build()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="ascii") != rendered:
            raise SystemExit("generated SPEC-02 Round 1 entry header is stale")
        print("SPEC-02 Round 1 entry data: PASS (generated header current)")
        return
    OUT.write_text(rendered, encoding="ascii", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
