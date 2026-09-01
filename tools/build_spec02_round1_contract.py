#!/usr/bin/env python3
"""Build the compact SPEC-02 Round 1 contract and generated fixtures."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/spec02_round1_executable_contract.json"
FIXTURES = ROOT / "data/spec02_round1_generated_fixtures.json"
SOURCES = {
    "coverage": "data/round1_system_coverage.yaml",
    "player": "data/oracle11_predator_warrior_authority.json",
    "scheduler": "data/oracle11_actor_scheduler_lifecycle.json",
    "navigation": "data/oracle11_round1_navigation.json",
    "enemies": "data/oracle11_round1_enemy_archetypes.json",
    "class00_program": "data/spec02_class00_type12_program.json",
    "class01_program": "data/spec02_class01_type12_program.json",
    "class06_program": "data/spec02_class06_type12_program.json",
    "class07_program": "data/spec02_class07_type20_program.json",
    "class10_program": "data/spec02_class10_type24_program.json",
    "class3d_program": "data/spec02_class3d_type24_program.json",
    "class49_program": "data/spec02_class49_type24_program.json",
    "class4b_program": "data/spec02_class4b_type24_program.json",
    "class4e_program": "data/spec02_class4e_type24_program.json",
    "auxiliary": "data/oracle11_round1_auxiliary_authority.json",
    "route": "data/oracle11_round1_encounter_route_authority.json",
    "boss": "data/oracle11_round1_boss_orchestration.json",
    "handoff": "data/oracle11_round1_handoff.json",
    "rng": "data/oracle11_round1_rng.json",
    "audio_transport": "data/oracle11_global_audio_load_release.json",
    "audio_handlers": "data/oracle11_global_audio_handlers.json",
    "audio_triggers": "data/oracle11_global_audio_trigger_owners.json",
    "loads": "data/oracle11_global_load_release_boundaries.json",
    "writers": "data/oracle11_round1_writer_reconciliation.json",
    "player_port": "tests/port_v2/predator_warrior_action/contract.json",
    "enemy_port": "tests/port_v2/street_alien_ai/contract.json",
    "collision_port": "tests/port_v2/collision_bench/contract.json",
    "hitko_port": "tests/port_v2/combat/hit_ko/approved_contract.json",
    "camera_port": "tests/port_v2/camera_stage/approved_contract.json",
    "hud_port": "tests/port_v2/hud/approved_contract.json",
    "pcm_port": "tests/port_v2/audio/pcm/approved_contract.json",
    "cdda_port": "tests/port_v2/cdda_residency/approved_contract.json",
}
ORACLE_KEYS = {
    "player", "scheduler", "navigation", "enemies", "auxiliary", "route",
    "boss", "handoff", "rng", "audio_transport", "audio_handlers",
    "audio_triggers", "loads", "writers",
}
SCENE_CLASSIFICATIONS = {
    "NATIVE_IMPLEMENTED", "SOURCE_BOUND_PRESENTATION_ONLY",
    "NOT_REQUIRED_FOR_THIS_SCENE", "BLOCKED_MISSING_SPEC",
    "BLOCKED_MISSING_SOURCE_EVIDENCE",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("ascii")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind_animation_collision_selectors(
        value: object, records: dict[int, dict[str, object]]) -> None:
    if isinstance(value, list):
        for item in value:
            bind_animation_collision_selectors(item, records)
        return
    if not isinstance(value, dict):
        return
    animation = value.get("animation_record")
    if isinstance(animation, str):
        try:
            address = int(animation, 16)
        except ValueError:
            address = -1
        record = records.get(address)
        if record is not None:
            hurt = int(record["hurt_selector_u8"])
            attack = int(record["attack_selector_u8"])
            has_plain = "hurt_selector" in value or "attack_selector" in value
            has_current = ("current_hurt_selector_u8" in value or
                           "current_attack_selector_u8" in value)
            has_suffixed = ("hurt_selector_u8" in value or
                            "attack_selector_u8" in value)
            if has_plain:
                value["hurt_selector"] = hurt
                value["attack_selector"] = attack
            if has_current:
                value["current_hurt_selector_u8"] = hurt
                value["current_attack_selector_u8"] = attack
            if has_suffixed or (not has_plain and not has_current):
                value["hurt_selector_u8"] = hurt
                value["attack_selector_u8"] = attack
    for item in value.values():
        bind_animation_collision_selectors(item, records)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pointer(value: object, path: str) -> object:
    current = value
    if path == "/":
        return current
    for token in path.strip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def field(field_id: str, family: str, kind: str, signed: bool,
          source_key: str, source_pointer: str, source_identity: str,
          fixture_path: str, guard: str, reads: list[str], writes: list[str],
          mutation_pointer: str, mutation_effect: str) -> dict[str, object]:
    return {
        "id": field_id,
        "authority_family": family,
        "classification": "SOURCE_CLOSED",
        "type": kind,
        "signed": signed,
        "source": {
            "artifact": SOURCES[source_key],
            "json_pointer": source_pointer,
            "routine_table_or_frame": source_identity,
        },
        "fixture_path": fixture_path,
        "transition_guard": guard,
        "reads": reads,
        "writes": writes,
        "mutation_control": {
            "artifact": SOURCES[source_key],
            "json_pointer": mutation_pointer,
            "expected_discriminating_effect": mutation_effect,
        },
    }


def build_fields() -> list[dict[str, object]]:
    f = field
    return [
        f("player.input_locomotion_neutral", "predator-warrior-player-authority", "state_record", True,
          "player", "/locomotion_neutral_facing", "0x0203e6 input decode and 0x0196ac player update",
          "/authority_data/player/locomotion_neutral_facing", "decoded direction changes locomotion; ten zero-vector ticks enter neutral without changing facing",
          ["input.current:u16", "player.state:u16", "player.velocity:s32"], ["player.position:s32", "player.facing:u8", "player.state:u16"],
          "/locomotion_neutral_facing/counterfactuals/hold_right", "release timing or facing mutation changes the neutral trace"),
        f("player.melee_action_equipment", "predator-warrior-player-authority", "state_table", False,
          "player", "/route_reachable_melee_actions", "0x02021c Button2 dispatch and source close-combo tables",
          "/authority_data/player/route_reachable_melee_actions", "new Button2 edge selects the context action; recovery edge inside the 30-tick window advances the source selector",
          ["input.new_edges:u16", "player.state:u16", "player.followup:u8"], ["player.state:u16", "player.animation:u32", "player.assembly:u32", "player.collision_selector:u8"],
          "/route_reachable_melee_actions/counterfactuals", "selector timing or assembly substitution produces a source differential"),
        f("player.airborne_interruptions", "predator-warrior-player-authority", "state_table", True,
          "player", "/directional_airborne_interruption", "0x020406 air dispatch table; reachable phases 0x0400..0x0410",
          "/authority_data/player/directional_airborne_interruption", "source input edge and current air phase select directional, Button1, Button2, landing, or HIT cancellation",
          ["input.current:u16", "input.new_edges:u16", "player.state:u16", "player.height:s32"], ["player.state:u16", "player.velocity:s32", "player.animation:u32", "player.facing:u8"],
          "/directional_airborne_interruption/counterfactuals", "phase or interruption mutation changes a targeted air route"),
        f("player.airborne_button1_projectile", "predator-warrior-player-authority", "guarded_actor_program", True,
          "player", "/directional_airborne_interruption/airborne_actions/button1/record4_class03", "0x023858 player allocation and 0x030382 record-type-4 class-3 state machine",
          "/authority_data/player/directional_airborne_interruption/airborne_actions/button1/record4_class03", "accepted airborne Button1 edge/resource guard allocates the class-3 actor; current state/substate, collision and bounds own motion, children, effects and release",
          ["player.state:u16", "input.current:u8", "player.resource:s16", "actor.state:u16", "actor.position:s32", "actor.health:s16", "camera.position:s16"], ["player.state:u16", "actor.record", "actor.position:s32", "actor.collision", "record4.child", "record36.effect", "pool.free_count:u8"],
          "/directional_airborne_interruption/airborne_actions/button1/record4_class03/suppression_control", "suppressing only source writer 0x02387e removes the actor lifetime and changes later fixed-pool allocation identity without changing player/route/score projection"),
        f("player.weapon_projectile_resources", "predator-warrior-player-authority", "state_record", True,
          "player", "/weapon_projectile_resource", "0x021eac Button1 weapon body and record-type-4 projectile allocation",
          "/authority_data/player/weapon_projectile_resource", "Button1/B1+B2 source guards own allocation, resource debit/recharge, collision, removal, and presentation continuity",
          ["input.new_edges:u16", "player.resource:s16", "target.pointer:u32"], ["player.state:u16", "player.resource:s16", "projectile.record", "player.animation:u32"],
          "/weapon_projectile_resource/counterfactuals", "projectile, target, or resource suppression changes the causal route"),
        f("player.button1_stage_progress", "predator-warrior-player-authority", "guarded_global_program", True,
          "player", "/weapon_projectile_resource/implementation_contract/sufficient_action/source_stage_progress", "0x024094/0x024096 caller and 0x0179e2..0x017b74 helper",
          "/authority_data/player/weapon_projectile_resource/implementation_contract/sufficient_action/source_stage_progress", "a sufficient Button1 action entry calls the guarded source helper before resource debit, projectile allocation, and the actor scheduler",
          ["global.a5+0x01b0:u8", "global.a5+0x0226:u16", "global.a5+0x01ea:s16", "global.a5+0x021a:s16", "global.a5+0x021c:s16"], ["global.a5+0x0226:u16", "global.a5+0x01ea:s16"],
          "/weapon_projectile_resource/implementation_contract/sufficient_action/source_stage_progress/mutation_controls", "wrong delta, threshold, action-entry timing, or direct stage initialization changes the scheduler-visible class-0x1f action-0x0c branch"),
        f("player.weapon_projectile_impact_variant", "predator-warrior-player-authority", "attack_record_field", False,
          "player", "/weapon_projectile_resource/implementation_contract/record4_parent_class0/collision_table/attack_entries/1/impact_variant_u8", "0x01d622 reads attack-record +0x08; parent record 0x02fc58 contains 0x0a",
          "/authority_data/player/weapon_projectile_resource/implementation_contract/record4_parent_class0/collision_table/attack_entries/1/impact_variant_u8", "a current-state projectile collision copies the absolute signed attack-record +0x08 byte into the allocated class-0x4e variant",
          ["projectile.attack_record:u32", "attack_record+0x08:s8", "type24.free_count:u8"], ["type24.class4e.variant:u8"],
          "/weapon_projectile_resource/counterfactuals", "projectile collision suppression removes the impact actor and its downstream RNG transaction"),
        f("player.weapon_parent_class49_effect", "predator-warrior-player-authority", "guarded_presentation_actor_program", True,
          "player", "/weapon_projectile_resource/implementation_contract/record4_parent_class0/effect_allocation", "0x02f94c phase guard/caller, 0x08f0c6 allocator and 0x08f080 class-0x49 dispatch",
          "/authority_data/player/weapon_projectile_resource/implementation_contract/record4_parent_class0/effect_allocation", "each eligible parent active-state update requests one variant-0 class-0x49 actor; fixed-pool availability and its eight-tick state program own visibility and release",
          ["global.phase19:u8", "projectile.position:s16", "projectile.animation_record:u32", "type24.free_count:u8"], ["type24.class49.record", "type24.class49.position:s16", "type24.class49.animation:u32", "type24.free_count:u8"],
          "/weapon_projectile_resource/implementation_contract/record4_parent_class0/effect_allocation/mutation_controls", "phase guard, variant, timer, allocation, presentation, dispatch or release mutation changes the Coffee Shop class-0x49 population and fixed-pool identity"),
        f("player.special_scene_effects", "predator-warrior-player-authority", "guarded_actor_program", True,
          "player", "/weapon_projectile_resource/special_implementation_contract", "0x01a7e6 guard, 0x01a89a action writer, character-0 dispatcher 0x023132 and type-24 class-0x4b/class-0x3d writers",
          "/authority_data/player/weapon_projectile_resource/special_implementation_contract", "the exact current/previous B1/B2/B3 guard enters character-0 action 0x0800; source animation events own class-0x4b and class-0x3d allocation, selector 11 contact, audio and six-health completion cost",
          ["input.current:u8", "input.previous:u8", "player.state:u16", "player.action:u16", "player.health:s16", "player.contact:u8", "type24.free_count:u8"], ["player.action:u16", "player.animation:u32", "player.health:s16", "type24.class4b", "type24.class3d", "audio.command:u16"],
          "/weapon_projectile_resource/special_implementation_contract/mutation_controls", "wrong character routine, guard, state, selector, child class, health cost or fixed-frame completion is rejected"),
        f("player.hit_ko_continue_respawn", "predator-warrior-player-authority", "state_table", True,
          "player", "/hit_ko_failure_continue_respawn", "0x022f98 HIT/KO bodies and 0x00e8a4 continue controller",
          "/authority_data/player/hit_ko_failure_continue_respawn", "signed health selects HIT or KO; source countdown and credited input guards own continue and return to control",
          ["player.health:s16", "player.hit_value:s16", "credits.bcd:u8", "input.new_edges:u16"], ["player.state:u16", "player.health:s16", "credits.bcd:u8", "route.state:s16"],
          "/hit_ko_failure_continue_respawn/counterfactuals", "health threshold, input, or credit mutation discriminates HIT/KO/continue"),
        f("scheduler.fixed_pools", "actor-scheduler-allocation-lifecycle", "pool_table", False,
          "scheduler", "/pools", "0x01729e pool initialization and 0x017654 allocation/release",
          "/authority_data/scheduler/pools", "allocate only from a nonempty low-word LIFO free list; active zero skips dispatch",
          ["pool.free_count:u8", "pool.free_cursor:u16", "actor.class:s8"], ["pool.free_count:u8", "pool.free_cursor:u16", "actor.record"],
          "/targeted_counterfactuals", "pool/class removal changes actor population and route state"),
        f("scheduler.update_order", "actor-scheduler-allocation-lifecycle", "ordered_table", False,
          "scheduler", "/frame_scheduler", "0x00849e..0x0084ce scheduler call order",
          "/authority_data/scheduler/frame_scheduler", "exhaust each active pool in ascending slot order before the next record type",
          ["actor.active:u8", "actor.class:s8"], ["actor.state", "actor.position", "actor.lifecycle"],
          "/targeted_counterfactuals", "class removal exposes scheduler-order differences"),
        f("scheduler.source_visible_camera_globals", "actor-scheduler-allocation-lifecycle", "scheduler_global_table", True,
          "navigation", "/scheduler_visible_globals", "0x041c36 reads A5+0x278/A5+0x27c after camera writers 0x0b04ca/0x0b06fa and 0x0b04f4/0x0b081c",
          "/authority_data/navigation/scheduler_visible_globals", "the class-0x1f actor scheduler consumes preserved pre-update signed camera X/Z, never the post-player current sample",
          ["camera.position_x:s16", "camera.position_z:s16", "scheduler.phase"], ["enemy.wander_target_x:s16", "enemy.wander_target_z:s16", "enemy.direction:u8"],
          "/scheduler_visible_globals/mutation_control", "substituting post-player current camera state changes frame-3525 slot 0x00ffa3c0 from source record 0x0012d488 to 0x0012d50c"),
        f("navigation.terrain_bounds", "round1-navigation-terrain-camera", "signed_geometry_table", True,
          "navigation", "/global_bounds", "0x01b000 signed global bounds",
          "/authority_data/navigation/global_bounds", "current route bounds constrain source world x/z before obstacle and terrain response",
          ["player.x:s16", "player.z:s16", "route.bound_x:s16", "route.bound_z:s16"], ["player.x:s16", "player.y:s16", "player.z:s16"],
          "/counterfactuals", "directional or navigation-body mutation changes the completing route"),
        f("navigation.terrain_interpreter", "round1-navigation-terrain-camera", "guarded_geometry_program", True,
          "navigation", "/terrain_resolver/implementation_contract", "0x0b1baa dispatcher, 0x0b208c selector, and reachable kind-0/2/4/6 handlers",
          "/authority_data/navigation/terrain_resolver/implementation_contract", "source cell selection binds one eight-byte record; kind and branch selector choose exact signed arithmetic",
          ["player.x:s16", "player.z:s16", "terrain.cell+2:u8", "terrain.record[0..7]"], ["player.x:s16", "player.z:s16", "player.velocity:s16", "player.contact_flags:u8"],
          "/terrain_resolver/records", "wrong record byte, signedness, handler, axis, or retry token changes a directional terrain response"),
        f("navigation.obstacle_collision", "round1-navigation-terrain-camera", "collision_table", True,
          "navigation", "/obstacle_response/implementation_contract", "0x01db8a point/box overlap and 0x01d930 minimum-penetration response",
          "/authority_data/navigation/obstacle_response/implementation_contract", "source player point overlaps the selected obstacle attack box",
          ["player.x:s16", "player.z:s16", "obstacle.position:s16", "obstacle.attack_box"], ["player.position:s16", "player.velocity:s16", "player.contact_flags:u8"],
          "/obstacle_response/implementation_contract/dynamic_control", "obstacle-box or axis mutation changes the measured x=1091 response"),
        f("navigation.coffee_shop_obstacle_lifecycle", "round1-navigation-terrain-camera", "guarded_actor_program", True,
          "navigation", "/obstacle_response/lifecycle_contract", "0x01bece scene-record spawn, 0x06de92 class body, and 0x01d4aa damage transition",
          "/authority_data/navigation/obstacle_response/lifecycle_contract", "camera threshold, fixed-pool availability, current damage, animation and physics guards own spawn through release",
          ["camera.bound_x:u16", "record36.free_count:u8", "obstacle.state:u16", "obstacle.health:s16", "player.attack_record:u32"],
          ["obstacle.record", "record36.children", "obstacle.state:u16", "obstacle.position:s32", "pool.free_count:u8"],
          "/obstacle_response/lifecycle_contract/transition_suppression", "suppressing the exact damage-state writer keeps the obstacle and changes actor, route, audio and RNG chronology"),
        f("camera.route_lock_unlock", "round1-navigation-terrain-camera", "route_table", True,
          "navigation", "/camera/implementation_contract", "0x0b04bc initialization, 0x0b0680/0x0b0786 target arithmetic, and 0x028910 Coffee Shop guard",
          "/authority_data/navigation/camera/implementation_contract", "eligible player extrema move the target inside route bounds; the entry controller owns lock and unlock guards",
          ["route.state:s16", "entry_controller.state:u16", "entry_controller.phase:u8", "camera.record:s16", "player.position:s16"], ["camera.target:s16", "camera.position:s16", "route.bound:s16", "VDP2.plane_scroll:s16"],
          "/camera/implementation_contract/dynamic_checkpoints", "wrong target constant, speed table, guard, or update ordering changes the measured camera trace"),
        f("enemy.state_ai", "round1-enemy-archetypes", "actor_state_table", True,
          "enemies", "/archetypes", "type-12 dispatch table 0x01b9b6 and four required source routines",
          "/authority_data/enemies/archetypes", "signed class dispatch and current state/substate select the recovered enemy body",
          ["enemy.class:s8", "enemy.state:u16", "enemy.substate:u16", "player.pointer:u32"], ["enemy.state:u16", "enemy.substate:u16", "enemy.position:s16", "enemy.facing:u8"],
          "/archetypes/0/counterfactuals", "class removal or offense suppression changes the source route"),
        f("enemy.class00_type12_whole_program", "round1-enemy-archetypes", "guarded_actor_program", True,
          "class00_program", "/", "0x03f09c class entry, explicit top/inner/action/substate dispatch tables, and every Round 1-reachable branch",
          "/authority_data/enemies/archetypes/0/whole_routine_implementation_contract", "outer state, active inner state, action and substate dispatch select only the source-decoded class program; source guards, exact-width arithmetic and accepted shared helpers own every transition",
          ["enemy.outer_state:u16", "enemy.action_substate:u16", "enemy.position:s16/s32", "enemy.facing:u8", "enemy.timer:u8/u16", "enemy.health:s16", "enemy.animation_record:u32", "player.position:s16", "camera.position:s16", "route.globals", "rng.seed:u16"], ["enemy.state:u16", "enemy.action_substate:u16", "enemy.position:s16/s32", "enemy.facing:u8", "enemy.timer:u8/u16", "enemy.animation_record:u32", "enemy.collision_selectors:u8", "enemy.health:s16", "player.health:s16", "pool.free_count:u8", "rng.seed:u16"],
          "/mutation_controls", "dispatch, operand width, signed branch, field offset, transition, RNG order, presentation selector, collision, damage or release mutation changes the paired class-0x00 semantic witness"),
        f("enemy.class01_type12_whole_program", "round1-enemy-archetypes", "guarded_actor_program", True,
          "class01_program", "/", "0x0407b0 class entry, 25 explicit computed-dispatch tables, and every Round 1-reachable branch",
          "/authority_data/enemies/archetypes/1/whole_routine_implementation_contract", "outer state, active inner state, action, phase, spawn variant and action-16 variant dispatch select only the source-decoded class program; exact-width reads/writes, branch order and accepted shared helpers own every transition",
          ["enemy.outer_state:u16", "enemy.action_substate:u16", "enemy.position:s16/s32", "enemy.facing:u8", "enemy.timer:u8/u16", "enemy.health:s16", "enemy.animation_record:u32", "enemy.action_locals", "player.position:s16", "camera.position:s16", "route.globals", "rng.seed:u16"], ["enemy.state:u16", "enemy.action_substate:u16", "enemy.position:s16/s32", "enemy.facing:u8", "enemy.timer:u8/u16", "enemy.animation_record:u32", "enemy.collision_selectors:u8", "enemy.health:s16", "player.health:s16", "enemy.action_locals", "pool.free_count:u8", "rng.seed:u16"],
          "/mutation_controls", "dispatch, operand width, read/write field, signed branch, transition, RNG order, presentation selector, collision, damage or release mutation changes the paired class-0x01 semantic witness"),
        f("enemy.class06_type12_whole_program", "round1-enemy-archetypes", "guarded_actor_program", True,
          "class06_program", "/", "0x04956c class entry, 29 explicit computed-dispatch tables, and every Round 1-reachable branch",
          "/authority_data/enemies/archetypes/2/whole_routine_implementation_contract", "outer state, action, phase, hit/interruption state and source selectors dispatch only through the bounded source program; exact-width guards, arithmetic, RNG order and accepted shared helpers own every transition",
          ["enemy.outer_state:u16", "enemy.action_substate:u16", "enemy.position:s16/s32", "enemy.velocity:s32", "enemy.facing:u8", "enemy.timer:u8/u16", "enemy.health:s16", "enemy.animation_record:u32", "enemy.action_locals", "player.position:s16", "camera.position:s16", "route.globals", "rng.seed:u16"], ["enemy.state:u16", "enemy.action_substate:u16", "enemy.position:s16/s32", "enemy.velocity:s32", "enemy.facing:u8", "enemy.timer:u8/u16", "enemy.animation_record:u32", "enemy.collision_selectors:u8", "enemy.health:s16", "player.health:s16", "effect.record", "pool.free_count:u8", "rng.seed:u16"],
          "/mutation_controls", "dispatch, sentinel, operand width, read/write field, signed branch, transition, RNG order, presentation, collision, damage, effect or release mutation changes the paired class-0x06 semantic witness"),
        f("auxiliary.class07_type20_whole_program", "round1-projectile-pickup-hazard", "guarded_actor_program", True,
          "class07_program", "/", "0x06d1aa class entry, top-state and active-state dispatch tables, and every Round 1-reachable branch",
          "/authority_data/auxiliary/archetypes/1/whole_routine_implementation_contract", "outer and active state dispatch only through the bounded source program; exact-width movement, double-buffered navigation, contact, presentation and accepted shared helpers own every transition",
          ["actor.outer_state:u8/u16", "actor.active_phase:u8", "actor.contact_state:u8/u16", "actor.position:s16", "actor.movement:s16", "actor.facing:u8", "actor.timer:u8", "actor.animation_record:u32", "route.globals"], ["actor.state:u8/u16", "actor.position:s16", "actor.movement:s16", "actor.animation_record:u32", "actor.collision_selectors:u8", "actor.navigation_buffers", "pool.free_count:u8", "audio.command:u16"],
          "/mutation_controls", "dispatch, operand width, field offset, signed branch, transition, presentation, collision, navigation buffering, command or release mutation changes the paired class-0x07 semantic witness"),
        f("auxiliary.class10_type24_whole_program", "round1-projectile-pickup-hazard", "guarded_actor_program", True,
          "class10_program", "/", "0x079ffc class entry, four-way top-state dispatch, six source variant selectors, and every Round 1-reachable branch",
          "/authority_data/auxiliary/archetypes/5/whole_routine_implementation_contract", "outer state dispatches only through the bounded source program; variant-indexed signed offsets and animation records, exact current-state guards, presentation updates and fixed-pool release own every transition",
          ["actor.outer_state:u16", "actor.variant:u8", "actor.direction:u8", "actor.position:s16", "actor.animation_branch:s16", "actor.animation_event:u8", "variant.tables"], ["actor.state:u16", "actor.position:s16", "actor.animation_record:u32", "actor.presentation_fields", "pool.free_count:u8"],
          "/mutation_controls", "dispatch, operand width, field offset, signed branch, variant selector, movement table, animation table, presentation or release mutation changes the paired class-0x10 semantic witness"),
        f("auxiliary.class3d_type24_whole_program", "round1-projectile-pickup-hazard", "guarded_actor_program", True,
          "class3d_program", "/", "0x0887c8 class entry, four-way top-state dispatch, sixteen-entry signed movement table, and every Round 1-reachable branch",
          "/authority_data/auxiliary/archetypes/6/whole_routine_implementation_contract", "outer state dispatches only through the bounded source program; retained slot fields, anchor restoration, variant-indexed signed movement, animation terminal guard and fixed-pool release own every transition",
          ["actor.outer_state:u16", "actor.variant:u8", "actor.direction:u8", "actor.position:s16", "actor.anchor:s16", "actor.animation_branch:s16", "movement.table"], ["actor.state:u16", "actor.variant:u8", "actor.position:s16", "actor.animation_record:u32", "actor.presentation_fields", "pool.free_count:u8"],
          "/mutation_controls", "dispatch, operand width, field offset, signed branch, retained-y rule, movement selector/sign, animation, presentation or release mutation changes the paired class-0x3d semantic witness"),
        f("auxiliary.class49_type24_whole_program", "round1-projectile-pickup-hazard", "guarded_actor_program", True,
          "class49_program", "/", "0x08f080 class entry, four-way top-state dispatch, variant-0 and variant-1 allocation helpers, and every Round 1-reachable branch",
          "/authority_data/auxiliary/archetypes/9/whole_routine_implementation_contract", "outer state dispatches only through the bounded source program; source phase guards select the two allocation helpers, retained slot animation fields preserve fixed-pool identity, the timer and variant-1 global delta own lifetime and motion, and fixed-pool release owns removal",
          ["actor.outer_state:u8", "actor.variant:u8", "actor.position:s16", "actor.animation_record:u32", "actor.animation_timer:u16", "actor.animation_branch:s16", "global.phase:u8", "global.variant1_x_delta:s16", "type24.free_count:u8"], ["actor.active:u8", "actor.class:u8", "actor.state:u8", "actor.variant:u8", "actor.position:s16", "actor.animation_record:u32", "actor.lifetime_timer:u8", "actor.presentation_fields", "type24.free_count:u8"],
          "/mutation_controls", "dispatch, helper variant, phase guard, timer, retained animation field, position copy, global delta, presentation or release mutation changes the paired class-0x49 semantic witness"),
        f("auxiliary.class4b_type24_whole_program", "round1-projectile-pickup-hazard", "guarded_actor_program", True,
          "class4b_program", "/", "0x08f86e class entry, four-way top-state dispatch, 32-record animation program, owner-contact guard, and every Round 1-reachable branch",
          "/authority_data/auxiliary/archetypes/10/whole_routine_implementation_contract", "outer state dispatches only through the bounded source program; player-owned contact and animation-event guards, exact facing-relative position setup, shared animation wrap semantics, visibility submission and fixed-pool release own every transition",
          ["actor.outer_state:u8", "actor.position:s16", "actor.facing:u8", "actor.animation_record:u32", "actor.animation_timer:u16", "actor.animation_branch:s16", "actor.owner_pointer:u16", "owner.contact:u8", "owner.animation_event:u8"], ["actor.state:u8", "actor.position:s16", "actor.animation_record:u32", "actor.presentation_fields", "type24.free_count:u8"],
          "/mutation_controls", "dispatch, owner guard, facing offset, vertical placement, animation sequence/wrap, visibility or release mutation changes the paired class-0x4b semantic witness"),
        f("auxiliary.class4e_type24_whole_program", "round1-projectile-pickup-hazard", "guarded_actor_program", True,
          "class4e_program", "/", "0x0927f6 class entry, four-way top-state dispatch, 26-entry animation table, eight-pair RNG jitter table, variant-24/25 facing branch, and every Round 1-reachable impact variant",
          "/authority_data/auxiliary/archetypes/11/whole_routine_implementation_contract", "outer state dispatches only through the bounded source program; the copied impact variant selects presentation, variants 24/25 use facing-relative X displacement, all other variants consume exactly one source RNG call for jitter, and animation terminal order plus fixed-pool release own lifetime",
          ["actor.outer_state:u8", "actor.variant:u8", "actor.position:s16", "actor.reaction_facing:u8", "actor.animation_record:u32", "actor.animation_timer:u16", "actor.animation_branch:s16", "rng.seed:u16", "variant.tables"], ["actor.state:u8", "actor.position:s16", "actor.animation_record:u32", "actor.presentation_fields", "rng.seed:u16", "type24.free_count:u8"],
          "/mutation_controls", "dispatch, impact variant, RNG order, jitter mask/table, variant-24/25 facing branch, animation selector/terminal order, presentation or release mutation changes the paired class-0x4e semantic witness"),
        f("enemy.initial_transition_execution", "round1-enemy-archetypes", "guarded_state_program", True,
          "enemies", "/archetypes/3/initial_transition_contract", "0x0606aa/0x0606d4/0x0606fc initializers and 0x060b1a..0x060c1c transition bodies",
          "/authority_data/enemies/archetypes/3/initial_transition_contract", "route-global, timer, animation-branch, landing and source-pool guards own the three initial class-0x1f bodies",
          ["enemy.state:u16", "enemy.substate:u16", "enemy.timer:u8/u16", "enemy.animation_branch:s16", "route.entry_guard:u8", "rng.seed:u16", "type24.free_count:u8"], ["enemy.state:u16", "enemy.substate:u16", "enemy.position:s32", "enemy.velocity:s32", "enemy.animation:u32", "type24.effect.record", "audio.command:u16"],
          "/archetypes/3/initial_transition_contract/mutation_controls", "guard, timer, movement, facing, selector, RNG, effect or audio mutation changes the bounded first-segment trace"),
        f("enemy.class1f_current_state", "round1-enemy-archetypes", "guarded_actor_program", True,
          "enemies", "/archetypes/3/current_state_implementation_contract", "0x060532/0x06075a class-0x1f state dispatch and 0x06b3f2 first dynamic spawn controller",
          "/authority_data/enemies/archetypes/3/current_state_implementation_contract", "native fixed-pool state, controller guards, current collision and signed health own the bounded first encounter",
          ["enemy.state:u16", "enemy.substate:u16", "enemy.position:s16", "enemy.timer:u16", "player.position:s16", "player.attack_selector:u8", "rng.seed:u16", "pool.free_count:u8"], ["enemy.record", "enemy.position:s16", "enemy.facing:u8", "enemy.animation:u32", "enemy.health:s16", "player.health:s16", "pool.free_count:u8", "encounter.state:u8"],
          "/archetypes/3/current_state_implementation_contract/mutation_controls", "spawn, movement, facing, RNG, contact, damage, reaction, removal or retained-authority mutation changes the bounded first-encounter trace"),
        f("enemy.class1f_first_segment_actions", "round1-enemy-archetypes", "guarded_actor_program", True,
          "enemies", "/archetypes/3/first_segment_action_execution_contract", "0x060546 initializer, 0x060772/0x060798 current-action dispatch, and 0x0165c4 animation/movement interpreter",
          "/authority_data/enemies/archetypes/3/first_segment_action_execution_contract", "each active fixed-pool class-0x1f record executes its source variant, action/substate, animation record, movement vector, collision, release and RNG guards in scheduler order",
          ["enemy.variant:u8", "enemy.state:u16", "enemy.action:u16", "enemy.facing:u8", "enemy.position:s32", "enemy.animation_record:u32", "enemy.animation_timer:u16", "enemy.animation_branch:s16", "player.position:s32", "route.globals", "rng.seed:u16"], ["enemy.state:u16", "enemy.action:u16", "enemy.facing:u8", "enemy.position:s32", "enemy.animation_record:u32", "enemy.collision_selectors:u8", "enemy.health:s16", "pool.free_count:u8", "living_enemy_count:u16", "rng.seed:u16"],
          "/archetypes/3/first_segment_action_execution_contract/mutation_controls", "variant, action target, branch order, selector, record, movement, timer, release, RNG or single-synthetic-actor substitution changes the causal first-segment trace"),
        f("enemy.class1f_inner_state_0x08", "round1-enemy-archetypes", "guarded_actor_program", True,
          "enemies", "/archetypes/3/first_segment_action_execution_contract/inner_state_0x08_program", "0x061096 transition, 0x0610f6/0x040bbe inner dispatch, 0x041c36/0x041d6c group-band occupancy, 0x016644 movement, 0x0411c4 motion, and 0x0413d2 type-16 emission",
          "/authority_data/enemies/archetypes/3/first_segment_action_execution_contract/inner_state_0x08_program", "the action-0x16 terminal, target-side, latch, RNG and facing guards enter inner state 0x08; scheduler-owned action, animation and motion guards alone advance it and positive animation events alone emit type-16 actors",
          ["enemy.outer_state:u8", "enemy.inner_state:u8", "enemy.action:u8", "enemy.action_phase:u8", "enemy.inner_timer:u16", "enemy.animation_timer:u16", "enemy.animation_branch:s16", "enemy.animation_record:u32", "enemy.direction:u8", "enemy.facing:u8", "enemy.position:s32", "enemy.velocity:s32", "enemy.target:u16", "enemy.latches:u8", "player.position:s32", "route.gameplay_gate:s16", "route.interruption:u8", "rng.seed:u16", "type16.free_count:u8"], ["enemy.inner_state:u8", "enemy.action:u8", "enemy.action_phase:u8", "enemy.inner_timer:u16", "enemy.action_timer:u8", "enemy.position:s32", "enemy.velocity:s32", "enemy.facing:u8", "enemy.animation_record:u32", "enemy.animation_timer:u16", "enemy.animation_branch:s16", "enemy.collision_selectors:u8", "enemy.latches:u8", "rng.seed:u16", "type16.actor_record"],
          "/archetypes/3/first_segment_action_execution_contract/inner_state_0x08_program/mutation_control", "suppressing the exact inner-state writer removes every inner-0x08 context and its three animation-event-owned type-16 spawns; fixed-frame or authored emission is rejected"),
        f("enemy.presentation_collision_hitko", "round1-enemy-archetypes", "presentation_collision_table", True,
          "enemies", "/archetypes", "per-class writer windows, animation records, assemblies, selectors, damage and HIT/KO transitions",
          "/authority_data/enemies/archetypes", "current state/phase owns presentation and collision selectors; signed health owns HIT/KO",
          ["enemy.state:u16", "enemy.health:s16", "collision.hit_value:s16"], ["enemy.animation:u32", "enemy.assembly:u32", "enemy.health:s16", "enemy.state:u16"],
          "/archetypes/3/counterfactuals", "presentation, offense, or class mutation produces a discriminating difference"),
        f("auxiliary.lifecycle_effects", "pickups-equipment-weapons-projectiles-hazards-destructibles", "actor_state_table", True,
          "auxiliary", "/archetypes", "type-16/20/24 dispatch tables and twelve route-reachable classes",
          "/authority_data/auxiliary/archetypes", "current class/state owns lifecycle, presentation, collision, player effect, and RNG consumption",
          ["actor.class:s8", "actor.state:u16", "player.position:s16"], ["actor.state:u16", "actor.active:u8", "player.health:s16", "player.resource:s16"],
          "/archetypes/0/counterfactual", "corrected class/type suppression removes actors and changes the causal state"),
        f("auxiliary.coffee_shop_class08_health_pickup", "pickups-equipment-weapons-projectiles-hazards-destructibles", "guarded_actor_and_pickup_program", True,
          "auxiliary", "/first_segment_dependencies/class_0x08_type20_health_pickup", "0x01bece stage-record interpreter, 0x06d53c class-0x08 parent, 0x0bc692 drop selector, 0x0a38e4 class-0x0a pickup, and 0x019fec player interaction",
          "/authority_data/auxiliary/first_segment_dependencies/class_0x08_type20_health_pickup", "the source stage guard owns the parent; current record-4 collision owns the drop; scheduler-ordered RNG, record-28 motion, hurt-box overlap, health update, audio command, animation terminal, and fixed-pool release own the pickup lifecycle",
          ["route.camera_right_edge:u16", "stage.record", "record20.health:s16", "record4.attack_record:u32", "rng.seed:u16", "record28.position:s32", "player.position:s32", "player.health:s16", "input.button2_edge:u8"], ["record20.actor", "record20.state:u16", "record28.actor", "record28.position:s32", "rng.seed:u16", "player.state:u16", "player.health:s16", "audio.command:u16", "record28.active:u8"],
          "/first_segment_dependencies/class_0x08_type20_health_pickup/mutation_controls", "stage guard, fixed-frame spawn, collision record, damage, RNG, scheduler order, movement, landing, hurt box, health, audio, terminal or release mutation changes the captured Coffee Shop scene"),
        f("auxiliary.coffee_shop_class05_reactive_prop", "pickups-equipment-weapons-projectiles-hazards-destructibles", "guarded_actor_program", True,
          "auxiliary", "/first_segment_dependencies/class_0x05_type20_reactive_prop", "0x01bece stage-record interpreter, 0x06c9ee..0x06cc56 class-0x05 dispatcher, current-state collision writers 0x01d0c8..0x01d6f8, and fixed-pool release 0x017706",
          "/authority_data/auxiliary/first_segment_dependencies/class_0x05_type20_reactive_prop", "the source stage guard owns two actors; selector-11 current-state collision owns the single reaction, command, RNG, class-0x4e impact, dual trajectory, landing and release program",
          ["route.camera_right_edge:u16", "stage.record", "player.attack_record:u32", "record20.state:u16", "record20.position:s32", "record20.hurt_selector:u8", "rng.seed:u16", "frame.phase:u8", "type24.free_count:u8"], ["record20.actor", "record20.state:u16", "record20.position:s32", "record20.facing:u8", "record20.animation:u32", "record20.health:s16", "rng.seed:u16", "audio.command:u16", "type24.class4e.actor", "pool.free_count:u8"],
          "/first_segment_dependencies/class_0x05_type20_reactive_prop/mutation_controls", "stage order, collision record, selector, damage, facing, RNG, audio, timer, trajectory, projection, landing, impact or release mutation changes the captured Coffee Shop scene"),
        f("auxiliary.coffee_shop_class4e_variant10_impact", "pickups-equipment-weapons-projectiles-hazards-destructibles", "guarded_presentation_actor_program", True,
          "auxiliary", "/first_segment_dependencies/class_0x4e_type24_variant4_effect/variant10_collision_effect", "0x01d622 impact allocation and 0x0927f6 class-0x4e state dispatch",
          "/authority_data/auxiliary/first_segment_dependencies/class_0x4e_type24_variant4_effect/variant10_collision_effect", "source collision at frame 2362 allocates variant 10; scheduler-owned state 0 consumes one RNG call before animation and fixed-pool release",
          ["projectile.attack_record:u32", "defender.hurt_box", "defender.position:s16", "rng.seed:u16", "type24.free_count:u8"], ["type24.class4e.record", "type24.class4e.position:s16", "type24.class4e.animation:u32", "rng.seed:u16", "type24.free_count:u8"],
          "/first_segment_dependencies/class_0x4e_type24_variant4_effect/variant10_collision_effect/mutation_controls", "variant field, effect suppression, RNG, animation or release mutation changes the frame-2363 population and downstream class-0x09 selector"),
        f("auxiliary.coffee_shop_class47_presentation", "pickups-equipment-weapons-projectiles-hazards-destructibles", "guarded_presentation_actor_program", True,
          "auxiliary", "/first_segment_dependencies/class_0x47_type24_class02_child_presentation", "0x06b61a class-0x02 caller, 0x08eb1c four-child allocator and 0x08eb86 class-0x47 state dispatch",
          "/authority_data/auxiliary/first_segment_dependencies/class_0x47_type24_class02_child_presentation", "class-0x02 state 0x0400 allocates four source-owned presentation children; each consumes seven RNG calls and moves until the dual unsigned landing guard releases it",
          ["owner.state:u16", "owner.position:s16", "owner.direction:u8", "rng.seed:u16", "type24.free_count:u8", "frame.parity:u8"], ["type24.child[4]", "child.position:s32", "child.animation:u32", "rng.seed:u16", "type24.free_count:u8"],
          "/first_segment_dependencies/class_0x47_type24_class02_child_presentation/mutation_controls", "spawn, RNG, selector, motion, direction, terminal-guard or release mutation changes the captured class-0x47 population and trajectory"),
        f("auxiliary.coffee_shop_class43_population", "pickups-equipment-weapons-projectiles-hazards-destructibles", "guarded_presentation_actor_program", True,
          "auxiliary", "/first_segment_dependencies/class_0x43_type24_class01_scene_population", "0x06b3a8/0x06b3ae class-0x01 callers, 0x08cde6 grouped allocator and 0x08ce44 class-0x43 state dispatch",
          "/authority_data/auxiliary/first_segment_dependencies/class_0x43_type24_class01_scene_population", "class-0x01 terminal animation allocates two four-actor source-owned presentation groups; scheduler-ordered seven-call initialization owns the downstream Round 1 RNG trajectory",
          ["owner.state:u16", "owner.animation_branch:s16", "owner.position:s16", "owner.direction:u8", "rng.seed:u16", "type24.free_count:u8", "frame.parity:u8"], ["type24.child[8]", "child.state:u16", "child.position:s32", "child.animation:u32", "rng.seed:u16", "type24.free_count:u8"],
          "/first_segment_dependencies/class_0x43_type24_class01_scene_population/mutation_controls", "owner guard, group/order, RNG, selector, motion, direction, landing, projection or release mutation changes the captured class-0x43 population and downstream trajectory"),
        f("route.first_entry_body", "encounters-waves-scripted-triggers", "entry_spawn_and_guard_table", True,
          "route", "/first_entry_body", "0x028874 ten-row spawn table and 0x0214dc player entry-script decoder",
          "/authority_data/route/first_entry_body", "active class-0x01/type-32 controller dispatches the ten-row table; the signed player animation terminator clears the selected g8236 bit before the exact route guard advances state",
          ["controller.state:u16", "pool.free_count:u8", "player.script_cursor:u32", "g8236:u8", "g81af:u8"], ["enemy.record[10]", "pool.free_count:u8", "player.state:u16", "route.state:s16"],
          "/first_entry_body/suppression_control", "suppressing only writer 0x02151e retains entry state and prevents route state 4"),
        f("route.segments_edges", "encounters-waves-scripted-triggers", "route_table", True,
          "route", "/segment_bindings", "94 source segments and 14 exact route-state writer edges",
          "/authority_data/route", "source route/controller guards, never presentation labels, frames, or actor count alone, own transitions",
          ["route.state:s16", "route.controller", "actor.state"], ["route.state:s16", "encounter.state", "camera.lock"],
          "/counterfactuals", "route and offense perturbations discriminate segment edges"),
        f("route.enemy_spawns", "encounters-waves-scripted-triggers", "spawn_table", True,
          "route", "/enemy_spawns", "56 exact source enemy spawns with caller chains and source windows",
          "/authority_data/route/enemy_spawns", "source table/controller guard and successful record-12 allocation own each spawn",
          ["route.state:s16", "encounter.controller", "pool.free_count:u8"], ["enemy.record", "pool.free_count:u8"],
          "/counterfactuals", "class removal and offense suppression discriminate spawn ownership"),
        f("route.first_segment_recurring_spawn", "encounters-waves-scripted-triggers", "guarded_spawn_program", True,
          "route", "/first_segment_recurring_spawn", "0x0287fc controller initializer, 0x0288ba intro-gate transition, 0x0288e2 current guard, 0x028a12 primary writer, 0x028b5a auxiliary writer and class-0x1f KO progress writer 0x061070",
          "/authority_data/route/first_segment_recurring_spawn", "source controller initialization, class-0x44 intro-gate release, class-0x1f KO progress, countdown/progress guards, phase counters and successful record-12 allocation own recurring class-0x1f spawns",
          ["route.state:s16", "controller.state_substate:u16", "controller.timer40:u16", "controller.timer42:u16", "controller.limit:u16", "intro_gate.u8", "phase.u8", "class1f.state_substate:u16", "class1f.health:s16", "progress:u16", "camera.position:s16", "rng.seed:u16", "pool.free_count:u8"], ["controller.state_substate:u16", "controller.timers:u16", "progress:u16", "enemy.record", "living_enemy_count:u16", "controller.index:u16", "rng.seed:u16", "pool.free_count:u8"],
          "/first_segment_recurring_spawn/intro_gate_suppression_control", "suppressing only the class-0x44 writer leaves the controller at 0x0202 with timer 60 and prevents primary or auxiliary recurring spawns; fixed-frame advancement is rejected"),
        f("route.coffee_shop_exit_controller", "encounters-waves-scripted-triggers", "guarded_exit_route_program", True,
          "route", "/first_segment_recurring_spawn/exit_controller_program", "0x0288e2 phase dispatcher, 0x028ba6 withdrawal timer, player program 0x00129b64, route writers 0x008418/0x00c84c/0x0083d4 and route-zero dispatcher 0x00837c",
          "/authority_data/route/first_segment_recurring_spawn/exit_controller_program", "controller progress, source timers, player-script terminal writer and route-zero loader resumes own Coffee Shop withdrawal, centralized teardown and next-scene handoff; living enemy count and fixed frames do not",
          ["route.state:s16", "controller.state_substate:u16", "controller.timer42:u16", "progress:u16", "progress_snapshot:u16", "player.script_cursor:u32", "player.position:s32", "g8236:u8", "g81af:u8", "g837c:s16", "loader.resume:u8"], ["controller.state_substate:u16", "controller.timer42:u16", "route.state:s16", "player.state:u16", "player.position:s32", "player.facing:u8", "pool.free_count:u8", "load.event"],
          "/first_segment_recurring_spawn/exit_controller_program/mutation_controls", "wrong progress threshold, kill gate, fixed-frame transition, script cursor, motion vector, terminal writer, teardown mode or mid-round read is rejected"),
        f("boss.phases_spawns", "round1-boss", "boss_phase_table", True,
          "boss", "/controller_contract", "class-0x02 type-32 controller, 11 phases, eight boss-room spawns",
          "/authority_data/boss", "controller state/phase and source countdown guards own boss spawns and phase transitions",
          ["boss.controller_state:u16", "boss.health:s16", "pool.free_count:u8"], ["boss.controller_state:u16", "boss.record", "encounter.state"],
          "/counterfactuals/suppress_boss_offense", "boss-offense suppression changes phase and RNG timelines"),
        f("boss.clear", "round1-boss", "guarded_transition", True,
          "boss", "/boss_clear_guard", "controller state 0x0400 terminal writer to 0xff81f3 and route consumer 0x008418",
          "/authority_data/boss/boss_clear_guard", "defeated boss death tail and controller countdown zero permit the exact clear write",
          ["boss.state:u16", "boss.health:s16", "boss.controller_countdown:u16"], ["boss.controller_state:u16", "route.clear:u8"],
          "/counterfactuals/suppress_exact_clear_writer", "suppressing only the clear writer holds the route in Round 1"),
        f("rng.coffee_shop_stage_setup", "rng-consumption", "guarded_rng_transaction", True,
          "rng", "/owner_partition/global_route_and_controller/groups/0/coffee_shop_entry_transaction", "0x017a1e stage-row selection, 0x017ac6..0x017b74 signed stage arithmetic and 0x017af0 shared RNG call",
          "/authority_data/rng/owner_partition/global_route_and_controller/groups/0/coffee_shop_entry_transaction", "the source type-0x1c Coffee Shop row guard consumes exactly one RNG value and clamps the signed stage parameter before the ten class-0x1f initializers",
          ["route.state:s16", "player.variant:u16", "stage.record_type:u8", "stage.selectors:u8/u16", "stage.bounds:s16", "rng.seed:u16"], ["stage.parameter:s16", "rng.seed:u16"],
          "/owner_partition/global_route_and_controller/groups/0/coffee_shop_entry_transaction/suppression_control", "suppressing only the two RNG seed writes shifts every initial class-0x1f seed and changes the downstream route projection"),
        f("rng.shared_recurrence_order", "rng-consumption", "u16_recurrence", False,
          "rng", "/algorithm", "0x017c5e recurrence; 2,280 ordered Round 1 calls",
          "/authority_data/rng", "each accepted owner calls the shared recurrence at its exact scheduler position",
          ["rng.seed:u16"], ["rng.seed:u16", "caller.result:u16"],
          "/counterfactuals/freeze_rng", "freezing seed 0x8def prevents route completion"),
        f("audio.command_handler_transaction", "gameplay-audio-load-release", "audio_command_table", False,
          "audio_handlers", "/command_transactions", "audio CPU dispatcher 0x01bd..0x0294 and 909-entry command table",
          "/authority_data/audio/command_transactions", "copied 16-byte command resolves through its exact table entry and handler; bus writes are grouped by transaction",
          ["audio.command:u16", "audio.payload[16]"], ["audio.state", "qsound.transactions"],
          "/command_transactions/0/causal_effect", "command suppression produces a discriminating grouped QSound difference"),
        f("audio.nonplayer_trigger", "gameplay-audio-load-release", "audio_trigger_table", False,
          "audio_triggers", "/trigger_groups", "175 exact owner/caller/guard/command groups",
          "/authority_data/audio/nonplayer_trigger_groups", "owner class/type/state/substate and hashed local caller guard reach the shared wrapper",
          ["owner.state", "owner.substate", "route.state"], ["audio.command_queue[16]"],
          "/trigger_groups/0/handler_transaction/causal_control", "trigger suppression changes downstream QSound with gameplay projection unchanged"),
        f("audio.player_trigger", "gameplay-audio-load-release", "audio_trigger_table", False,
          "player", "/player_origin_gameplay_audio/trigger_edges", "38 player-side caller/command edges to wrapper 0x003a88 and queue 0x001922",
          "/authority_data/player/player_origin_gameplay_audio", "player action/state/substate guard and exact caller enqueue the bound command/arguments",
          ["player.state:u16", "player.substate:u16", "player.action:u16"], ["audio.command_queue[16]"],
          "/player_origin_gameplay_audio/score_negative_control", "audio suppression changes QSound while packed-BCD score remains unchanged"),
        f("loading.route_packages", "gameplay-audio-load-release", "load_boundary_table", False,
          "loads", "/boundaries", "four source route package boundaries at frames 5565, 5566, 6200, and 12799",
          "/authority_data/loading/boundaries", "route guard owns loader callers, destination, legal read window, completion/failure state, and next route state",
          ["route.state", "loader.package", "destination.owner"], ["residency.package", "load.state", "route.next_state"],
          "/boundaries/0/failure_control", "destination suppression changes package identity without changing gameplay projection"),
        f("handoff.stage_clear", "stage-clear-failure-continue-round2-handoff", "state_table", True,
          "handoff", "/stage_clear_player_action", "player phases 0x1000/0x1002/0x1004 and four post-clear route edges",
          "/authority_data/handoff", "accepted boss clear enters source player clear phases and guarded route transitions",
          ["route.clear:u8", "player.state:u16", "transition.countdown:u16"], ["player.state:u16", "route.state:s16", "load.request"],
          "/counterfactuals", "clear suppression, boss removal, and no-continue cannot fabricate handoff"),
        f("handoff.stable_round2", "stage-clear-failure-continue-round2-handoff", "route_state", True,
          "handoff", "/round2_handoff", "stable Round 2 interactive route state 4 at source frame 15331",
          "/authority_data/handoff/round2_handoff", "all four source route edges and legal loads complete before Round 2 control is returned",
          ["route.state:s16", "player.state:u16", "load.state"], ["route.stage:u16", "route.state:s16", "player.control:bool"],
          "/counterfactuals", "noncompleting controls never reach the stable Round 2 signature"),
        f("hud.current_state_projection", "stage-clear-failure-continue-round2-handoff", "hud_state", True,
          "player", "/route_pickup_resource_audio_load_ownership", "player health/resource/score writers and same-state accepted HUD Port V2 interface",
          "/platform_interfaces/hud_port", "HUD reads current gameplay state after the owning update and cannot own gameplay transitions",
          ["player.health:s16", "player.resource:s16", "score.bcd", "boss.health:s16"], ["hud.semantic_state"],
          "/route_pickup_resource_audio_load_ownership/mutation_controls", "resource/pickup mutations change current HUD state without giving HUD authority"),
        f("pcm_cdda.gameplay_ownership", "gameplay-audio-load-release", "audio_load_event", False,
          "audio_triggers", "/trigger_groups", "source trigger groups plus accepted PCM/CDDA Port V2 interfaces",
          "/platform_interfaces/pcm_port", "gameplay trigger command and route load ownership request the accepted PCM/CDDA adapter; playback cannot advance route state",
          ["audio.command:u16", "route.load_owner"], ["pcm.request", "cdda.request", "audio.ownership"],
          "/trigger_groups/0/handler_transaction/causal_control", "command suppression changes audio transaction without changing route gameplay"),
    ]


def build_coffee_shop_scene_manifest(source: dict[str, dict]) -> dict[str, object]:
    census = copy.deepcopy(source["route"]["coffee_shop_scene_census"])
    native_pairs = {
        (4, 0), (4, 4), (12, 0x1f), (20, 0x09), (20, 0x0a),
        (20, 0x01), (20, 0x02),
        (24, 0x10), (24, 0x3d), (24, 0x44), (24, 0x45), (24, 0x47),
        (24, 0x49), (24, 0x4b), (24, 0x4e),
        (32, 0x01), (36, 0x05),
    }
    implementation_blockers = {
        (0, 0): "complete scene player state/animation and current "
                "collision/damage/HIT/KO/exit binding is not yet present",
        (4, 0x03): "class-0x03 airborne Button1 has a focused native subset "
                   "but lacks the complete scene collision/impact/effect/"
                   "release differential",
    }

    def actor_classification(item: dict[str, object]) -> str:
        if item["source_classification"] == "BLOCKED_MISSING_SOURCE_EVIDENCE":
            return "BLOCKED_MISSING_SOURCE_EVIDENCE"
        pair = (int(item["type"]), int(str(item["class"]), 16))
        return ("NATIVE_IMPLEMENTED" if pair in native_pairs else
                "BLOCKED_MISSING_SPEC")

    for item in census["actor_lifetimes"]:
        item["classification"] = actor_classification(item)
        pair = (int(item["type"]), int(str(item["class"]), 16))
        if pair in implementation_blockers:
            item["exact_blocker"] = implementation_blockers[pair]
        item["assembly_and_behavior_binding"] = item.get(
            "source_contract", item.get("exact_blocker"))
    for item in census["class_type_inventory"]:
        item["classification"] = actor_classification(item)
        pair = (int(item["type"]), int(str(item["class"]), 16))
        if pair in implementation_blockers:
            item["exact_blocker"] = implementation_blockers[pair]
    for item in census["audio_events"]:
        item["classification"] = "BLOCKED_MISSING_SPEC"
    class1f_lifetimes = [
        item for item in census["actor_lifetimes"]
        if int(item["type"]) == 12 and int(str(item["class"]), 16) == 0x1f]

    def class1f_health_write(item: dict[str, object]) -> bool:
        if item["target_pool"] != "record12":
            return False
        frame = int(item["frame"])
        slot = int(str(item["target_slot"]), 16)
        return any(int(str(actor["source_slot"]), 16) == slot and
                   int(actor["first_frame"]) <= frame <= int(actor["last_frame"])
                   for actor in class1f_lifetimes)

    for item in census["health_writes"]:
        player_collision_write = (
            item["frame"] == 2750 and item["attacker"] == "0xffa240" and
            item["defender"] == "0xff8380" and
            item["attack_record"] == "0x130b5c" and
            item["writer_pc"] == "0x01d5ee")
        item["classification"] = (
            "NATIVE_IMPLEMENTED" if player_collision_write or (
                class1f_health_write(item) and
                item["writer_pc"] in {"0x0605aa", "0x0172ba", "0x01d590",
                                      "0x01d598"})
            else "BLOCKED_MISSING_SPEC")

    route_edges = []
    for item in source["route"]["route_state_edges"]:
        if item["write_frame"] > 5566:
            continue
        edge = copy.deepcopy(item)
        edge["classification"] = (
            "NATIVE_IMPLEMENTED" if edge["write_frame"] in
                {2237, 5452, 5523, 5561} else
            "BLOCKED_MISSING_SPEC")
        route_edges.append(edge)

    loads = []
    for item in source["loads"]["boundaries"]:
        if int(item["visible_boundary_frame"]) > 5566:
            continue
        boundary = copy.deepcopy(item)
        boundary["classification"] = "NATIVE_IMPLEMENTED"
        boundary["native_binding"] = "ADAPTED_PRESENTATION_RESIDENCY_NOOP"
        loads.append(boundary)

    camera_runs = []
    for item in source["navigation"]["camera"]["camera_lock_and_unlock_runs"]:
        if item["first_frame"] > 5566 or item["last_frame"] < 1972:
            continue
        run = copy.deepcopy(item)
        run["classification"] = "NATIVE_IMPLEMENTED"
        camera_runs.append(run)

    required_terrain = set(source["navigation"]["terrain_resolver"]
                           ["implementation_contract"]
                           ["first_segment_geometry_universe"]
                           ["selectors_u8"])
    terrain_records = []
    implementation_records = source["navigation"]["terrain_resolver"][
        "implementation_contract"]["implementation_records"]
    for item in implementation_records:
        if item["selector_u8"] not in required_terrain:
            continue
        record = copy.deepcopy(item)
        record["classification"] = "NATIVE_IMPLEMENTED"
        terrain_records.append(record)

    systems = [
        {"id": "coffee-shop-entry-controller",
         "classification": "NATIVE_IMPLEMENTED",
         "source_contract":
             "authority_data.route.first_entry_body"},
        {"id": "coffee-shop-player",
         "classification": "BLOCKED_MISSING_SPEC",
         "source_contract": "authority_data.player",
         "exact_blocker": "complete scene state/animation and current "
             "collision/damage/HIT/KO binding is not yet present in the "
             "implementation fixture"},
        {"id": "coffee-shop-obstacle",
         "classification": "NATIVE_IMPLEMENTED",
         "source_contract":
             "authority_data.navigation.obstacle_response.implementation_contract"},
        {"id": "coffee-shop-terrain",
         "classification": "NATIVE_IMPLEMENTED",
         "source_contract":
             "authority_data.navigation.terrain_resolver.implementation_contract"},
        {"id": "coffee-shop-camera",
         "classification": "NATIVE_IMPLEMENTED",
         "source_contract":
             "authority_data.navigation.camera.implementation_contract"},
        {"id": "coffee-shop-class03-air-weapon",
         "classification": "BLOCKED_MISSING_SPEC",
         "source_contract": "authority_data.player.directional_airborne_"
             "interruption.airborne_actions.button1.record4_class03",
         "exact_blocker": implementation_blockers[(4, 0x03)]},
        {"id": "coffee-shop-class1f-current-authority",
         "classification": "NATIVE_IMPLEMENTED",
         "source_contract": "authority_data.enemies.archetypes[class=0x1f]."
             "current_state_implementation_contract + "
             "first_segment_action_execution_contract"},
        {"id": "coffee-shop-current-collision-damage",
         "classification": "BLOCKED_MISSING_SPEC",
         "source_contract": "coffee_shop.health_writes",
         "implemented_subset": "class-0x1f initialization, player melee/"
             "projectile damage, signed KO clamp, HIT/KO, fixed-pool release, "
             "and the frame-2750 class-0x1f-to-player current-state damage/"
             "hitstop transaction",
         "exact_blocker": "player health and non-class-0x1f health writers "
             "remain without a complete native Coffee Shop scene differential"},
        {"id": "coffee-shop-audio",
         "classification": "BLOCKED_MISSING_SPEC",
         "source_contract": "coffee_shop.audio_events"},
        {"id": "coffee-shop-exit-loads",
         "classification": "NATIVE_IMPLEMENTED",
         "source_contract": "authority_data.loading.boundaries"},
        {"id": "coffee-shop-encounter-clear-and-exit",
         "classification": "NATIVE_IMPLEMENTED",
         "source_contract": "authority_data.route.route_state_edges"},
    ]
    all_items = (census["actor_lifetimes"] + census["audio_events"] +
                 census["health_writes"] + route_edges + loads + camera_runs +
                 terrain_records + systems)
    counts = {name: sum(item["classification"] == name for item in all_items)
              for name in sorted(SCENE_CLASSIFICATIONS)}
    blocked_pairs = [item for item in census["class_type_inventory"]
                     if item["classification"].startswith("BLOCKED_")]
    return {
        "schema": "spec02-coffee-shop-scene-manifest-v1",
        "scope": census["scope"],
        "source_frame_range": census["source_frame_range"],
        "capture_identity": census["capture_identity"],
        "pool_scan": census["pool_scan"],
        "pool_layout_source": census["pool_layout_source"],
        "animation_collision_selectors":
            census["animation_collision_selectors"],
        "actor_lifetimes": census["actor_lifetimes"],
        "class_type_inventory": census["class_type_inventory"],
        "audio_events": census["audio_events"],
        "health_writes": census["health_writes"],
        "route_edges": route_edges,
        "load_boundaries": loads,
        "navigation": {
            "obstacle": dict(copy.deepcopy(source["navigation"]
                                  ["obstacle_response"]
                                  ["implementation_contract"]),
                             classification="NATIVE_IMPLEMENTED"),
            "terrain_records": terrain_records,
            "camera_runs": camera_runs,
        },
        "systems": systems,
        "classification_counts": counts,
        "blocked_class_type_pairs": blocked_pairs,
        "acceptance_gate": {
            "source_actor_lifetimes": 747,
            "source_class_type_pairs": 38,
            "source_audio_events": 279,
            "source_health_writes": 149,
            "source_damage_writes": 30,
            "missing_or_extra_entities_allowed": False,
            "silent_omission_allowed": False,
            "scene_differential_pass": False,
            "ready": False,
        },
    }


def build_fixtures(source: dict[str, dict]) -> dict[str, object]:
    player = source["player"]
    player_authority = {key: copy.deepcopy(player[key]) for key in (
        "source_identity", "locomotion_neutral_facing",
        "route_reachable_melee_actions", "normal_jump_air_landing",
        "directional_airborne_interruption", "weapon_projectile_resource",
        "hit_ko_failure_continue_respawn",
        "route_pickup_resource_audio_load_ownership",
        "player_origin_gameplay_audio")}
    selector_records = {
        int(item["animation_record"], 16): item
        for item in source["route"]["coffee_shop_scene_census"]
            ["animation_collision_selectors"]["records"]
    }
    bind_animation_collision_selectors(player_authority, selector_records)
    locomotion_execution = player_authority["locomotion_neutral_facing"][
        "first_segment_execution_contract"]
    locomotion_execution["current_collision_selector_projection"] = {
        "guard": "the current locomotion animation record owns collision lookup metadata",
        "actor_hurt_selector_u8": 17,
        "actor_attack_selector_u8": 0,
        "collision_lookup_hurt_selector_u8": 17,
        "rule": (
            "native current selectors derive from animation-record bytes "
            "+0x08/+0x09; captured actor event/link bytes are rejected"
        ),
        "source_frames": [2602, 2678],
    }
    player_authority["locomotion_neutral_facing"][
        "actor_state_projection"] = {
            "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "spec_executable": True,
            "control_state_u16": "0x0200",
            "action_projection": [
                {"source_action_u16": "0x0200", "substate_u16": "0x0000",
                 "meaning": "cleanup"},
                {"source_action_u16": "0x0202", "substate_u16": "0x0002",
                 "meaning": "walk or idle locomotion dispatch"},
                {"source_action_u16": "0x0204", "substate_u16": "0x0004",
                 "meaning": "directional release stop"},
            ],
            "projection_rule": (
                "while locomotion owns the player, actor state remains 0x0200 "
                "and actor substate receives the low byte of the source action"
            ),
            "visible_samples": [
                {"source_frame_u16": 2238, "state_u16": "0x0200",
                 "substate_u16": "0x0000"},
                {"source_frame_u16": 2239, "state_u16": "0x0200",
                 "substate_u16": "0x0002"},
            ],
            "evidence": {
                "coffee_shop_scene_actors_sha256": source["route"]
                    ["coffee_shop_scene_census"]["capture_identity"]
                    ["completion_a"]["coffee_shop_scene_actors.tsv"],
                "locomotion_source_contract":
                    "data/oracle11_predator_warrior_authority.json#/locomotion_neutral_facing/release_transition",
            },
            "mutation_control": {
                "mutation": "write the complete 0x0200 source action prefix into actor substate",
                "rejected_source_frame_u16": 2239,
                "rejected_substate_u16": "0x0200",
                "fixed_frame_substitute": False,
            },
        }
    weapon_projection = player_authority["weapon_projectile_resource"][
        "implementation_contract"]
    weapon_projection["empty_fallback"]["entry_projection"] = {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "spec_executable": True,
        "entry_rule": (
            "write state 0x0200 and action/substate 0x1a00 while preserving "
            "the current animation record, assembly, timer, branch, and "
            "current collision selectors; bind the 0x1a02 active record on "
            "the following player update"
        ),
        "entry_writes": {
            "state_u16": "0x0200",
            "action_u16": "0x1a00",
            "substate_u16": "0x1a00",
        },
        "entry_preserves": [
            "animation_record:u32", "assembly:u32",
            "animation_timer:u16", "animation_branch:s16",
            "current_hurt_selector:u8", "current_attack_selector:u8",
        ],
        "active_replacement": {
            "visible_update_offset_u8": 1,
            "state_u16": "0x0200",
            "action_u16": "0x1a02",
            "substate_u16": "0x1a02",
            "animation_record": "0x0015fcfc",
            "assembly": "0x00161772",
            "animation_timer_u16": 4095,
            "animation_branch_s16": -32768,
            "current_hurt_selector_u8": 1,
            "current_attack_selector_u8": 0,
        },
        "coffee_shop_witnesses": [
            {"prior_frame_u16": 2521, "entry_frame_u16": 2522,
             "active_frame_u16": 2523,
             "prior_animation_record": "0x0015f1f4",
             "entry_animation_record": "0x0015f1f4"},
            {"prior_frame_u16": 2611, "entry_frame_u16": 2612,
             "active_frame_u16": 2613,
             "prior_animation_record": "0x0015f228",
             "entry_animation_record": "0x0015f228"},
        ],
        "rng_calls": [],
        "mutation_controls": [
            "reject fixed idle presentation on a walking entry",
            "reject binding the active presentation on the entry update",
            "reject delaying the active presentation past the next update",
        ],
    }
    weapon_projection["player_actor_projection"] = {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "spec_executable": True,
        "rule": (
            "player actor state remains 0x0200; player actor substate receives "
            "the complete source action word while Button1 owns the action, "
            "then receives 0x0000 cleanup and 0x0002 return locomotion"
        ),
        "selector_ownership": (
            "captured player actor +0x25/+0x26 event/link bytes are not "
            "collision selectors; the native current collision selectors "
            "derive from animation-record bytes +0x08/+0x09"
        ),
        "visible_runs": [
            {"first_frame_u16": 2252, "last_frame_u16": 2252,
             "state_u16": "0x0200", "substate_u16": "0x0c00",
             "hurt_selector_u8": 1, "attack_selector_u8": 0},
            {"first_frame_u16": 2253, "last_frame_u16": 2255,
             "state_u16": "0x0200", "substate_u16": "0x0c02",
             "hurt_selector_u8": 1, "attack_selector_u8": 0},
            {"first_frame_u16": 2256, "last_frame_u16": 2272,
             "state_u16": "0x0200", "substate_u16": "0x0c04",
             "hurt_selector_u8": 1, "attack_selector_u8": 0},
            {"first_frame_u16": 2273, "last_frame_u16": 2273,
             "state_u16": "0x0200", "substate_u16": "0x0000",
             "hurt_selector_u8": 1, "attack_selector_u8": 0},
            {"first_frame_u16": 2274, "last_frame_u16": 2274,
             "state_u16": "0x0200", "substate_u16": "0x0002",
             "hurt_selector_u8": 1, "attack_selector_u8": 0},
            {"first_frame_u16": 2522, "last_frame_u16": 2522,
             "state_u16": "0x0200", "substate_u16": "0x1a00",
             "hurt_selector_u8": 1, "attack_selector_u8": 0},
            {"first_frame_u16": 2523, "last_frame_u16": 2538,
             "state_u16": "0x0200", "substate_u16": "0x1a02",
             "hurt_selector_u8": 1, "attack_selector_u8": 0},
            {"first_frame_u16": 2539, "last_frame_u16": 2539,
             "state_u16": "0x0200", "substate_u16": "0x0000",
             "hurt_selector_u8": 1, "attack_selector_u8": 0},
            {"first_frame_u16": 2540, "last_frame_u16": 2540,
             "state_u16": "0x0200", "substate_u16": "0x0002",
             "hurt_selector_u8": 1, "attack_selector_u8": 0},
        ],
        "evidence": {
            "coffee_shop_scene_actors_sha256": source["route"]
                ["coffee_shop_scene_census"]["capture_identity"]
                ["completion_a"]["coffee_shop_scene_actors.tsv"],
            "button1_source_contract":
                "data/oracle11_predator_weapon_projectile_resource.json#/implementation_contract/sufficient_action",
            "resource_timer_contract":
                "data/oracle11_predator_weapon_projectile_resource.json#/implementation_contract/resource_tick + data/oracle07_predator_warrior_action_graph_equipment.json#/equipment_contract/gun/resource/recharge_cadence_frames",
        },
        "mutation_control": {
            "mutations_rejected": [
                "copy only the source inner-state byte into actor substate",
                "copy animation-record selector metadata into player actor +0xa5/+0xa6",
            ],
            "first_rejected_frame_u16": 2252,
            "fixed_frame_substitute": False,
        },
    }
    weapon_projection["record4_parent_class0"]["child_emitter_state"][
        "state_projection"] = {
            "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "spec_executable": True,
            "field_mapping": {
                "source_state_u16": "(state_u8 << 8) | inner_state_u8",
                "source_substate_u16": "0x0000",
            },
            "coffee_shop_first_parent": [
                {"first_frame_u16": 2287, "last_frame_u16": 2287,
                 "state_u8": 4, "inner_state_u8": 0,
                 "source_state_u16": "0x0400"},
                {"first_frame_u16": 2288, "last_frame_u16": 2317,
                 "state_u8": 4, "inner_state_u8": 2,
                 "source_state_u16": "0x0402"},
                {"first_frame_u16": 2318, "last_frame_u16": 2318,
                 "state_u8": 6, "inner_state_u8": 2,
                 "source_state_u16": "0x0602"},
            ],
            "emitter_entry_order": [
                "write inner state 2",
                "decrement the existing initial child cadence",
                "allocate the first child when cadence reaches zero",
            ],
            "first_child_visible_frame_u16": 2288,
            "evidence": {
                "coffee_shop_scene_actors_sha256": source["route"]
                    ["coffee_shop_scene_census"]["capture_identity"]
                    ["completion_a"]["coffee_shop_scene_actors.tsv"],
                "parent_source_contract":
                    "data/oracle11_predator_weapon_projectile_resource.json#/implementation_contract/record4_parent_class0/child_emitter_state",
            },
            "mutation_control": {
                "mutations_rejected": [
                    "omit the inner-state-2 transition",
                    "delay child allocation while changing inner state",
                    "project inner state into source actor +0x06 substate",
                    "copy parent facing into the allocator-cleared child",
                ],
                "first_rejected_frame_u16": 2288,
                "fixed_frame_substitute": False,
            },
        }
    weapon_projection["record4_parent_class0"]["child_emitter_state"].update({
        "child_initial_facing_u8": 0,
        "child_facing_rule": (
            "the record-4 allocator clears child facing to zero; parent "
            "facing is read only for the row-x sign and is not copied"),
        "coffee_shop_collision_child_witnesses": [
            {"source_slot": "0x00ff8900", "variant_u8": 1,
             "first_visible_frame_u16": 2908, "facing_u8": 0,
             "parent_source_slot": "0x00ff8880", "parent_facing_u8": 1},
            {"source_slot": "0x00ff8800", "variant_u8": 2,
             "first_visible_frame_u16": 2914, "facing_u8": 0,
             "parent_source_slot": "0x00ff8880", "parent_facing_u8": 1},
        ],
    })
    weapon_projection["record4_child_class4"][
        "fixed_slot_reuse_presentation"] = {
            "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "spec_executable": True,
            "allocator": "0x01773e",
            "release": "0x017754",
            "allocation_writer": "0x02f9dc child-emitter body",
            "rule": (
                "record-type-4 release and reallocation do not clear the "
                "prior animation presentation fields before the new actor's "
                "state-0 dispatch; retain them for the allocation-visible "
                "source frame, then replace them during state-0 initialization"
            ),
            "retained_fields": [
                "animation_record_u32", "assembly_u32",
                "animation_timer_u16", "animation_branch_s16",
            ],
            "coffee_shop_slot_0xff8800": {
                "prior_terminal_visible_frame_u16": 2333,
                "prior_state_u16": "0x0400",
                "prior_variant_u8": 0,
                "retained_animation_record": "0x0003088c",
                "retained_assembly": "0x00030b28",
                "retained_animation_timer_u16": 1,
                "retained_animation_branch_s16": -32768,
                "reuse_visible_frame_u16": 2371,
                "reuse_state_u16": "0x0000",
                "reuse_variant_u8": 2,
                "initialization_visible_frame_u16": 2372,
                "initialized_state_u16": "0x0200",
                "initialized_animation_record": "0x00030944",
                "initialized_assembly": "0x00030bd6",
                "initialized_animation_timer_u16": 2,
                "initialized_animation_branch_s16": 0,
            },
            "evidence": {
                "coffee_shop_scene_actors_sha256": source["route"]
                    ["coffee_shop_scene_census"]["capture_identity"]
                    ["completion_a"]["coffee_shop_scene_actors.tsv"],
                "allocator_write_set":
                    "data/oracle11_predator_weapon_projectile_resource.json#/implementation_contract/record4_parent_class0/allocation_writes",
                "child_source_contract":
                    "data/oracle11_predator_weapon_projectile_resource.json#/implementation_contract/record4_child_class4",
            },
            "mutation_control": {
                "mutation": (
                    "clear the retained presentation fields at release or "
                    "before the child allocation becomes visible"
                ),
                "rejected_visible_frame_u16": 2371,
                "mutant_animation_record": "0x00000000",
                "source_animation_record": "0x0003088c",
                "trajectory_fields_unchanged": [
                    "state", "substate", "x", "y", "z", "facing",
                ],
                "fixed_frame_substitute": False,
            },
        }
    registration = weapon_projection["current_state_collision_damage"][
        "registration_and_pair_eligibility"]
    registration["new_allocation_registration_boundary"] = {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "spec_executable": True,
        "rule": (
            "a record-4 actor allocated and initialized during the current "
            "record-4 scan receives its collision identity immediately but "
            "cannot enter the record-4 attacker list until the next source "
            "scheduler invocation"
        ),
        "coffee_shop_slot_0xff8880": {
            "identity_assignment_frame_u16": 2305,
            "collision_identity_u8": 42,
            "allocation_visible_frame_u16": 2306,
            "attacker_list_absent_frame_u16": 2305,
            "attacker_list_present_frame_u16": 2306,
            "source_contact_frame_u16": 2306,
            "source_target_slot": "0xffa180",
            "source_attack_record": "0x030cd2",
        },
        "attacker_lists": [
            {"source_frame_u16": 2305,
             "slots": ["0xff8700", "0xff8800"]},
            {"source_frame_u16": 2306,
             "slots": ["0xff8700", "0xff8800", "0xff8880"]},
        ],
        "evidence": {
            "collision_lists_sha256": player[
                "weapon_projectile_resource"]["provenance"]
                ["collision_registration_evidence"]
                ["coffee_shop_collision_lists.tsv"],
            "collision_identity_assignments_sha256": player[
                "weapon_projectile_resource"]["provenance"]
                ["collision_registration_evidence"]
                ["coffee_shop_collision_identity_assignments.tsv"],
            "scene_health_writes_sha256": player[
                "weapon_projectile_resource"]["provenance"]
                ["collision_registration_evidence"]
                ["coffee_shop_scene_health_writes.tsv"],
        },
        "mutation_control": {
            "mutation": "register a newly initialized record-4 actor in the same scheduler invocation",
            "rejected_effect": (
                "premature frame-2305 collision damages slot 0xff9d00 and "
                "creates a second frame-2306 target write"
            ),
            "first_rejected_visible_frame_u16": 2306,
            "fixed_frame_substitute": False,
        },
    }
    registration["collision_to_reaction_handoff"] = {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "spec_executable": True,
        "rule": (
            "the record4-v-record12 collision scheduler writes health and the "
            "outer HIT state after the defender's record-type-12 update; it "
            "must retain the defender's current substate and presentation "
            "until that defender's next record-type-12 scheduler update"
        ),
        "coffee_shop_slot_0xffa180": {
            "collision_scheduler_source_frame_u16": 2306,
            "collision_visible_frame_u16": 2307,
            "health_before_s16": 87,
            "health_after_s16": 56,
            "state_u16": "0x0202",
            "substate_u16": "0x0000",
            "animation_record": "0x0012eb5c",
            "hurt_selector_u8": 1,
            "attack_selector_u8": 1,
            "next_record12_visible_frame_u16": 2308,
            "next_state_u16": "0x0202",
            "next_substate_u16": "0x0002",
            "next_animation_record": "0x0012e04c",
            "next_hurt_selector_u8": 1,
            "next_attack_selector_u8": 1,
        },
        "scheduler_order": [
            "record-type-4 actor updates",
            "record-type-12 actor updates",
            "record4-v-record12 collision scheduler",
            "next source scheduler invocation record-type-12 reaction bind",
        ],
        "evidence": {
            "coffee_shop_scene_actors_sha256": source["route"]
                ["coffee_shop_scene_census"]["capture_identity"]
                ["completion_a"]["coffee_shop_scene_actors.tsv"],
            "coffee_shop_scene_health_writes_sha256": source["route"]
                ["coffee_shop_scene_census"]["capture_identity"]
                ["completion_a"]["coffee_shop_scene_health_writes.tsv"],
            "hit_transition_source":
                "data/oracle11_round1_enemy_archetypes.json#/archetypes/3/damage_hit_ko/hit_ko_transitions",
        },
        "mutation_control": {
            "mutations_rejected": [
                "bind HIT substate and presentation in the collision scheduler",
                "delay the health or outer-state write until the next record-type-12 update",
            ],
            "first_rejected_visible_frame_u16": 2307,
            "fixed_frame_substitute": False,
        },
    }
    route = {key: copy.deepcopy(source["route"][key]) for key in
             ("route_entry", "first_entry_body", "data_contract", "segment_bindings",
              "route_state_edges", "enemy_spawns",
              "first_segment_recurring_spawn")}
    route["first_entry_body"]["route4_player_activation_order"] = {
        "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
        "spec_executable": True,
        "route_writer": {
            "field": "0xff8008:s16",
            "value_s16": 4,
            "writer_pc": "0x00c170",
            "write_frame_u16": 2237,
            "visible_sample_frame_u16": 2238,
        },
        "visible_player_sample": {
            "source_frame_u16": 2238,
            "state_u16": "0x0200",
            "substate_u16": "0x0000",
        },
        "scheduler_rule": (
            "sample route-state player eligibility at the start of each source "
            "scheduler invocation; a route 2-to-4 write by the entry controller "
            "does not dispatch the player during that same invocation"
        ),
        "scheduler_order": [
            "entry-controller using current route state",
            "player only when route state was 4 at invocation start",
            "fixed actor pools in accepted scheduler order",
        ],
        "evidence": {
            "entry_samples_sha256": source["route"]["first_entry_body"]
                ["capture_identity"]["completion_a"]["files"]
                ["entry_samples.tsv"],
            "route_edge_source_contract":
                "data/oracle11_round1_encounter_route_authority.json#/route_state_edges/0",
            "player_entry_source_contract":
                "data/oracle11_round1_encounter_route_authority.json#/first_entry_body/player_entry_script",
        },
        "mutation_control": {
            "mutation": "dispatch player after observing the same-invocation route 4 write",
            "rejected_visible_sample": {
                "source_frame_u16": 2238,
                "state_u16": "0x0800",
                "substate_u16": "0x0200",
            },
            "fixed_frame_substitute": False,
        },
    }
    fixtures = {
        "schema": "spec02-round1-generated-fixtures-v1",
        "task": "SPEC-02-ROUND1-EXECUTABLE-CONTRACT",
        "classification": "GENERATED_ONLY_FROM_ACCEPTED_ORACLE_AND_PORT_V2",
        "authority_data": {
            "player": player_authority,
            "scheduler": {key: copy.deepcopy(source["scheduler"][key]) for key in
                          ("source_identity", "frame_scheduler", "pools")},
            "navigation": {key: copy.deepcopy(source["navigation"][key]) for key in
                           ("coordinate_contract", "global_bounds", "terrain_resolver",
                            "navigation_bodies", "obstacle_response",
                            "scheduler_visible_globals", "camera")},
            "enemies": {"scheduler": copy.deepcopy(source["enemies"]["scheduler"]),
                        "archetypes": copy.deepcopy(source["enemies"]["archetypes"])},
            "auxiliary": {"archetypes": copy.deepcopy(source["auxiliary"]["archetypes"]),
                          "first_segment_dependencies": copy.deepcopy(source["auxiliary"]["first_segment_dependencies"]),
                          "coffee_shop_type36_presentation": copy.deepcopy(source["auxiliary"]["coffee_shop_type36_presentation"]),
                          "coffee_shop_scene_component_identities": copy.deepcopy(source["auxiliary"]["coffee_shop_scene_component_identities"]),
                          "player_side_contract": copy.deepcopy(source["auxiliary"]["player_side_contract"]),
                          "navigation_body_geometry_contract": copy.deepcopy(source["auxiliary"]["navigation_body_geometry_contract"])},
            "route": route,
            "boss": {key: copy.deepcopy(source["boss"][key]) for key in
                     ("boss_actor_contract", "controller_contract", "boss_room_spawns",
                      "boss_defeat_bridge", "boss_clear_guard", "rng")},
            "handoff": {key: copy.deepcopy(source["handoff"][key]) for key in
                        ("stage_clear_player_action", "transition_countdown", "route_edges",
                         "load_release_ownership", "round2_handoff")},
            "rng": {key: copy.deepcopy(source["rng"][key]) for key in
                    ("algorithm", "consumption", "owner_partition")},
            "audio": {
                "transport": copy.deepcopy(source["audio_transport"]["accepted_subcheckpoint"]),
                "dispatcher": copy.deepcopy(source["audio_handlers"]["dispatcher"]),
                "handler_paths": copy.deepcopy(source["audio_handlers"]["handler_paths"]),
                "command_transactions": copy.deepcopy(source["audio_handlers"]["command_transactions"]),
                "nonplayer_trigger_groups": copy.deepcopy(source["audio_triggers"]["trigger_groups"]),
            },
            "loading": {"boundaries": copy.deepcopy(source["loads"]["boundaries"])},
        },
        "platform_interfaces": {key: copy.deepcopy(source[key]) for key in
            ("player_port", "enemy_port", "collision_port", "hitko_port",
             "camera_port", "hud_port", "pcm_port", "cdda_port")},
        "optional_unknowns": {
            "semantic_sound_names": "UNKNOWN",
            "semantic_package_names": "UNKNOWN",
            "required_for_round1": False,
        },
        "forbidden_runtime_inputs": ["raw traces", "disassembly notes", "68000 bytecode",
                                     "fixed-frame fallback", "presentation-owned gameplay"],
    }
    class00 = next(item for item in
                   fixtures["authority_data"]["enemies"]["archetypes"]
                   if item["class"] == "0x00" and item["type"] == 12)
    class00["whole_routine_implementation_contract"] = copy.deepcopy(
        source["class00_program"])
    class01 = next(item for item in
                   fixtures["authority_data"]["enemies"]["archetypes"]
                   if item["class"] == "0x01" and item["type"] == 12)
    class01["whole_routine_implementation_contract"] = copy.deepcopy(
        source["class01_program"])
    class06 = next(item for item in
                   fixtures["authority_data"]["enemies"]["archetypes"]
                   if item["class"] == "0x06" and item["type"] == 12)
    class06["whole_routine_implementation_contract"] = copy.deepcopy(
        source["class06_program"])
    class07 = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x07" and item["type"] == 20)
    class07["whole_routine_implementation_contract"] = copy.deepcopy(
        source["class07_program"])
    class10 = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x10" and item["type"] == 24)
    class10["whole_routine_implementation_contract"] = copy.deepcopy(
        source["class10_program"])
    class3d = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x3d" and item["type"] == 24)
    class3d["whole_routine_implementation_contract"] = copy.deepcopy(
        source["class3d_program"])
    class49 = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x49" and item["type"] == 24)
    class49["whole_routine_implementation_contract"] = copy.deepcopy(
        source["class49_program"])
    class4b = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x4b" and item["type"] == 24)
    class4b["whole_routine_implementation_contract"] = copy.deepcopy(
        source["class4b_program"])
    class4e = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x4e" and item["type"] == 24)
    class4e["whole_routine_implementation_contract"] = copy.deepcopy(
        source["class4e_program"])
    fixtures["scene_manifests"] = {
        "coffee_shop": build_coffee_shop_scene_manifest(source)}
    return fixtures


def build_artifacts() -> tuple[dict[str, object], dict[str, object]]:
    source = {key: load(ROOT / path) for key, path in SOURCES.items()}
    for key in ORACLE_KEYS:
        require(source[key]["status"] == "SOURCE_CLOSED", f"unaccepted Oracle input: {key}")
    gate = source["coverage"]["spec02_closure_gate"]
    require(gate["spec02_eligible"] is True, "SPEC-02 zero-gap gate closed")
    require(all(gate[key] == 0 for key in ("required_observed", "required_partial",
                                           "required_unknown", "unmapped_actor_class_type_pairs",
                                           "unmapped_route_edges", "orphan_authoritative_writers")) and
            not any(gate["unowned_events"].values()), "SPEC-02 gate has a gap")
    fixtures = build_fixtures(source)
    source_hashes = {key: {"artifact": path, "sha256": digest(ROOT / path)}
                     for key, path in SOURCES.items()}
    fields = build_fields()
    fields.append(field(
        "scene.coffee_shop_manifest", "encounters-waves-scripted-triggers",
        "scene_manifest", True, "route", "/coffee_shop_scene_census",
        "source frames 1972..5566 across all initialized actor pools",
        "/scene_manifests/coffee_shop",
        "every source-observed Coffee Shop entity and event has exactly one explicit implementation-readiness classification",
        ["all source actor pools", "route.state", "camera.state",
         "audio.command_queue", "health writers"],
        ["native scene actor/state/event projection"],
        "/coffee_shop_scene_census/negative_controls",
        "omitting a pool, actor lifetime, command, health write, or blocker fails the scene manifest"))
    fields.append(field(
        "scheduler.coffee_shop_source_update_cadence", "actor-scheduler-lifecycle",
        "source_frame_update_count", False, "route",
        "/first_segment_recurring_spawn/source_update_cadence",
        "accepted byte-identical recurring-controller transactions at 0x0288e2 for slot 0xffd180",
        "/authority_data/route/first_segment_recurring_spawn/source_update_cadence",
        "one full native gameplay update per captured controller invocation; zero preserves prior gameplay state",
        ["diagnostic source frame:u16"],
        ["entry/player/actor scheduler update count:u8"],
        "/first_segment_recurring_spawn/source_update_cadence/mutation_control",
        "changing an exceptional cadence count changes controller timer, state, and spawn chronology"))
    for item in fields:
        item["source"]["evidence_hash"] = source_hashes[
            next(k for k, v in SOURCES.items() if v == item["source"]["artifact"])
        ]["sha256"]
    fixture_bytes = canonical(fixtures)
    contract = {
        "schema": "spec02-round1-executable-contract-v1",
        "task": "SPEC-02-ROUND1-EXECUTABLE-CONTRACT",
        "status": "ACCEPTED",
        "classification": "SOURCE_CLOSED_ROUND1_EXECUTABLE_CONTRACT",
        "scope": "Predator Warrior from stable Round 1 entry through boss defeat, stage clear, and stable interactive Round 2 handoff",
        "required_unknown_count": 0,
        "adapted_required_count": 0,
        "field_contracts": fields,
        "source_artifacts": source_hashes,
        "generated_fixtures": {"artifact": FIXTURES.relative_to(ROOT).as_posix(),
                               "sha256": hashlib.sha256(fixture_bytes).hexdigest()},
        "coverage_gate": copy.deepcopy(gate),
        "accepted_port_v2_interfaces": [SOURCES[key] for key in
            ("player_port", "enemy_port", "collision_port", "hitko_port",
             "camera_port", "hud_port", "pcm_port", "cdda_port")],
        "protected_boundaries": {"production_runtime_writes": 0,
                                 "yaba_runs": 0, "frontend_active": False,
                                 "user09": "CHANGES_REQUESTED",
                                 "physical_saturn": "UNRUN"},
        "next_card": "REIMPLEMENT-13-SOURCE-CLOSED-ROUND1",
    }
    validate(contract, fixtures, source)
    return contract, fixtures


def validate(contract: dict[str, object], fixtures: dict[str, object],
             source: dict[str, dict] | None = None) -> None:
    if source is None:
        source = {key: load(ROOT / path) for key, path in SOURCES.items()}
    require(contract["status"] == "ACCEPTED" and
            contract["classification"] == "SOURCE_CLOSED_ROUND1_EXECUTABLE_CONTRACT",
            "SPEC-02 status drift")
    require(contract["required_unknown_count"] == 0 and
            contract["adapted_required_count"] == 0, "required uncertainty admitted")
    gate = contract["coverage_gate"]
    require(gate["spec02_eligible"] is True and
            gate == source["coverage"]["spec02_closure_gate"], "coverage gate drift")
    require(contract["generated_fixtures"]["sha256"] ==
            hashlib.sha256(canonical(fixtures)).hexdigest(), "fixture identity drift")
    require(fixtures["classification"] == "GENERATED_ONLY_FROM_ACCEPTED_ORACLE_AND_PORT_V2" and
            fixtures["optional_unknowns"]["required_for_round1"] is False,
            "fixture scope drift")
    scene = fixtures["scene_manifests"]["coffee_shop"]
    scheduler_globals = fixtures["authority_data"]["navigation"][
        "scheduler_visible_globals"]
    require(
        scheduler_globals["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
        scheduler_globals["consumer"]["routine"] == "0x041c36" and
        [(row["a5_offset_u16"], row["absolute_address"], row["type"],
          row["width_bytes"], row["native_scheduler_field"])
         for row in scheduler_globals["fields"]] == [
            (0x0278, "0xff8278", "s16", 2, "camera_x_previous"),
            (0x027c, "0xff827c", "s16", 2, "camera_z_previous"),
        ] and
        [[writer["pc"] for writer in row["writers"]]
         for row in scheduler_globals["fields"]] == [
            ["0x0b04ca", "0x0b06fa"],
            ["0x0b04f4", "0x0b081c"]] and
        [[reader["pc"] for reader in row["readers"]]
         for row in scheduler_globals["fields"]] == [
            ["0x041cb0"], ["0x041cb8"]] and
        scheduler_globals["mutation_control"][
            "baseline_source_frame_3525_animation_record"] ==
            "0x0012d488" and
        scheduler_globals["mutation_control"][
            "known_wrong_native_animation_record"] == "0x0012d50c" and
        scheduler_globals["mutation_control"][
            "rng_prefix_must_remain_exact"] is True,
        "scheduler-visible camera globals fixture incomplete or drifted")
    class08_pickup = fixtures["authority_data"]["auxiliary"][
        "first_segment_dependencies"]["class_0x08_type20_health_pickup"]
    require(
        class08_pickup["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
        class08_pickup["spec_executable"] is True and
        class08_pickup["fixed_frame_substitute_forbidden"] is True and
        class08_pickup["stage_spawn"]["record"] == {
            "allocator_selector_u16": 4,
            "character_guard_u8": 0,
            "class_variant_word_u16": "0x0800",
            "gate_u16": 816,
            "lane_guard_s8": 0,
            "x_s16": 1280,
            "y_s16": 317} and
        class08_pickup["parent"]["current_state_collision"]
            ["attack_record"]["address"] == "0x0002fc58" and
        class08_pickup["parent"]["drop"]["seed_before"] == "0x8be5" and
        class08_pickup["parent"]["drop"]["seed_after"] == "0xa388" and
        class08_pickup["parent"]["post_drop_program"]["debris"]
            ["internal_coordinate_format"].startswith(
                "two signed 24.8 trajectories") and
        class08_pickup["parent"]["post_drop_program"]["debris"]
            ["visible_position_projection"].startswith(
                "0x06d72e copies only") and
        class08_pickup["pickup"]["scheduler_order"].startswith(
            "record-type-20 parent drop allocation precedes") and
        class08_pickup["pickup"]["initialization"]
            ["motion_substate_u16"] == 0x0002 and
        class08_pickup["pickup"]["movement"]["first_landing_result"]
            ["position_write"] ==
            "replace only y_fp high word with ground_z and preserve the current fractional low word" and
        class08_pickup["pickup"]["movement"]["second_landing_result"]
            ["position_write"] ==
            "replace only y_fp high word with ground_z and preserve the current fractional low word" and
        class08_pickup["pickup"]["player_interaction"]["action_u16"] ==
            "0x0e00" and
        class08_pickup["pickup"]["player_interaction"][
            "input_sample_rule"].startswith(
                "the eligible current-frame target/input guard latches pickup ownership") and
        class08_pickup["pickup"]["player_interaction"]["health_before_s16"] ==
            85 and
        class08_pickup["pickup"]["player_interaction"]["health_after_s16"] ==
            95 and
        class08_pickup["pickup"]["player_interaction"]["audio_edge"]
            ["command_u16"] == "0x0206" and
        class08_pickup["pickup"]["collection"]["first_absent_frame_u16"] ==
            3103,
        "Coffee Shop class-0x08 health-pickup fixture incomplete or drifted")
    class05_prop = fixtures["authority_data"]["auxiliary"][
        "first_segment_dependencies"]["class_0x05_type20_reactive_prop"]
    require(
        class05_prop["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
        class05_prop["spec_executable"] is True and
        class05_prop["dispatch"] == "0x06c9ee" and
        [(row["address"], row["x_s16"], row["y_s16"])
         for row in class05_prop["stage_records"]] == [
            ("0x0015c188", 1264, 293),
            ("0x0015c1a8", 1284, 268)] and
        class05_prop["current_state_collision"]["attack_record"][
            "address"] == "0x0011af76" and
        class05_prop["current_state_collision"]["hurt_record"][
            "address"] == "0x0006cd50" and
        class05_prop["reaction_program"]["state_0x0400"][
            "seed_after"] == "0x61a7" and
        class05_prop["reaction_program"]["state_0x0404"]["primary"][
            "x_velocity_s32"] == -0x00050000 and
        class05_prop["current_state_collision"]["impact_allocation"][
            "source_slot"] == "0x00ffc200" and
        class05_prop["capture_identity"]["byte_identical"] is True and
        class05_prop["fixed_frame_substitute_forbidden"] is True and
        class05_prop["retained_gameplay_authority"] is False,
        "Coffee Shop class-0x05 reactive-prop fixture incomplete or drifted")
    class16 = fixtures["authority_data"]["auxiliary"][
        "first_segment_dependencies"]["class_0x1f_type16_0x06_projectile"]
    require(
        class16["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
        class16["spec_executable"] is True and
        class16["current_state_collision"]["attack_selector_u8"] == 1 and
        class16["current_state_collision"]["player_hurt_selector_u8"] == 17 and
        class16["current_state_collision"]["attack_record"]["address"] ==
            "0x0003589e" and
        class16["current_state_collision"]["player_hurt_record"]["address"] ==
            "0x0011ae8e" and
        "wrong current player hurt selector" in class16["mutation_controls"],
        "Coffee Shop type-16 current-state collision fixture incomplete or drifted")
    class4b = fixtures["authority_data"]["auxiliary"][
        "first_segment_dependencies"]["predator_special_type24_effects"][
            "class_0x4b"]
    require(
        class4b["state_0x0200"]["owner_contact_lifetime"].startswith(
            "player writer 0x01986a clears") and
        class4b["state_0x0200"]["coffee_shop_wrap_witness"] == {
            "terminal_record_frame_u16": 2835,
            "wrapped_record_frame_u16": 2836,
            "wrapped_animation_record": "0x0008f8e0"},
        "Coffee Shop class-0x4b contact/wrap fixture incomplete or drifted")
    player_hit = fixtures["authority_data"]["player"][
        "hit_ko_failure_continue_respawn"]["nonlethal_hit"][
            "first_segment_execution_contract"]
    coffee_hit_program = fixtures["authority_data"]["player"][
        "hit_ko_failure_continue_respawn"]["nonlethal_hit"][
            "coffee_shop_reachable_program"]
    require(player_hit["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            player_hit["spec_executable"] is True and
            player_hit["states"] == {
                "control_outer_u16": 0x0200, "hit_outer_u16": 0x0202,
                "entry_substate_u16": 0x0000,
                "shake_substate_u16": 0x0200,
                "motion_substate_u16": 0x0202,
                "return_substate_u16": 0x0204} and
            player_hit["phase_0x0200"]["writes"] == {
                "next_substate_u16": 0x0202,
                "x_velocity_s32_16_16": 0x0001C000,
                "x_acceleration_s32_16_16": -0x00002000} and
            player_hit["entry_writes"]["carried_record"] == {
                "animation_record": "0x0015f278",
                "assembly": "0x00160af2", "visible_timer_u16": 1,
                "hurt_selector_u8": 17, "attack_selector_u8": 0} and
            player_hit["phase_0x0200"]["presentation"] == {
                "animation_record": "0x0015eee8",
                "assembly": "0x00160ede", "timer_u16": 8,
                "branch_s16": -0x8000, "hurt_selector_u8": 0,
                "attack_selector_u8": 0} and
            player_hit["phase_0x0204"]["presentation"] == {
                "animation_record": "0x0015f1f4",
                "assembly": "0x001626a4", "timer_u16": 4095,
                "branch_s16": -0x8000, "hurt_selector_u8": 1,
                "attack_selector_u8": 0} and
            player_hit["shake"]["table_s16"] == [2, -2] * 16 and
            player_hit["phase_0x0204"]["return_visible_frame_u16"] ==
                2778 and
            player_hit["audio"]["command_u16"] == 0x003b and
            player_hit["rng"] == {"calls": [], "consumption_order": []},
            "first-segment player HIT fixture incomplete or drifted")
    require(
        coffee_hit_program["classification"] ==
            "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
        coffee_hit_program["spec_executable"] is True and
        len(coffee_hit_program["instances"]) == 5 and
        [row["hit_kind_u8"] for row in
         coffee_hit_program["instances"]] == [6, 9, 6, 9, 10] and
        [row["shake_count_u8"] for row in
         coffee_hit_program["instances"]] == [10, 20, 10, 20, 10] and
        [row["motion_index_u8"] for row in
         coffee_hit_program["instances"]] == [2, 8, 2, 8, 4] and
        coffee_hit_program["source_action_interruption"] == {
            "classification": "SOURCE_CLOSED_IMPLEMENTATION_FIELDS",
            "spec_executable": True,
            "guard_routine": "0x01a7e6",
            "action_writer": "0x01a892..0x01a8a0",
            "hit_phase_dispatch_pc": "0x01ab52",
            "dispatch_substate_u16": 0x0202,
            "queue_rule": "a qualifying source special edge observed while the shared HIT body is active remains pending until phase 0x0202 evaluates 0x01a7e6; advancing the edge out of the pending queue during shake is forbidden",
            "input_runs": [
                {"first_frame_u16": 3870, "last_frame_u16": 3874,
                 "input_mask_u8": "0x58"},
                {"first_frame_u16": 3875, "last_frame_u16": 3876,
                 "input_mask_u8": "0x48"},
                {"first_frame_u16": 3877, "last_frame_u16": 3877,
                 "input_mask_u8": "0x08"}],
            "terminal_hit_visible_frame_u16": 3877,
            "special_entry_visible_frame_u16": 3878,
            "special_startup_visible_frame_u16": 3879,
            "special_entry_state_u16": 0x0200,
            "special_entry_substate_u16": 0x0800,
            "mutation_control": {
                "reject_edge_loss_during_shake": True,
                "reject_dispatch_before_phase_0x0202": True,
                "reject_fixed_frame_special_entry": True}} and
        coffee_hit_program["mutation_control"]["mutated_writes_u16"] == 2,
        "Coffee Shop player HIT program fixture incomplete or drifted")
    activation = fixtures["authority_data"]["route"]["first_entry_body"][
        "route4_player_activation_order"]
    require(activation["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            activation["spec_executable"] is True and
            activation["route_writer"] == {
                "field": "0xff8008:s16", "value_s16": 4,
                "writer_pc": "0x00c170", "write_frame_u16": 2237,
                "visible_sample_frame_u16": 2238} and
            activation["visible_player_sample"] == {
                "source_frame_u16": 2238, "state_u16": "0x0200",
                "substate_u16": "0x0000"} and
            activation["mutation_control"]["rejected_visible_sample"]
                ["substate_u16"] == "0x0200" and
            activation["mutation_control"]["fixed_frame_substitute"] is False,
            "route-4 player activation ordering fixture drift")
    cadence = fixtures["authority_data"]["route"][
        "first_segment_recurring_spawn"]["source_update_cadence"]
    require(cadence["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            cadence["default_updates_per_source_frame_u8"] == 1 and
            cadence["exceptions"] == [
                {"source_frame_u16": 2075, "updates_u8": 3},
                {"source_frame_u16": 2165, "updates_u8": 4},
                {"source_frame_u16": 2260, "updates_u8": 0},
                {"source_frame_u16": 2265, "updates_u8": 0}] and
            cadence["source_capture"]["sha256"] ==
                source["route"]["first_segment_recurring_spawn"]
                ["capture_identity"]["completion_a"]["files"]
                ["progression_transactions.tsv"] and
            cadence["spec_executable"] is True,
            "Coffee Shop source update cadence fixture drift")
    reuse = fixtures["authority_data"]["route"][
        "first_segment_recurring_spawn"]["primary_writer"][
            "fixed_point_record_reuse"]
    recurring = fixtures["authority_data"]["route"][
        "first_segment_recurring_spawn"]
    primary_presentation = recurring["primary_writer"][
        "post_allocation_dispatch"]
    auxiliary_presentation = recurring["auxiliary_writer"][
        "post_allocation_dispatch"]
    require(
        reuse["classification"] == "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
        reuse["field_types"] == {
            "x_fp": "s32 16.16", "y_fp": "s32 16.16",
            "x_writer": "s16 high word", "y_writer": "s16 high word"} and
        reuse["source_samples"]["pre_release_frame_2508"] == {
            "x_fp_s32": "0x02bc8000", "y_fp_s32": "0x01389000",
            "x_fraction_u16": "0x8000", "y_fraction_u16": "0x9000"} and
        reuse["source_samples"]["post_allocation_frame_2511"] == {
            "x_fp_s32": "0x02a08000", "y_fp_s32": "0x01489000"} and
        reuse["source_samples"]["first_motion_frame_2514"] == {
            "x_fp_s32": "0x02a7e200", "y_fp_s32": "0x01470900"} and
        reuse["source_samples"]["second_motion_frame_2517"] == {
            "x_fp_s32": "0x02af4400", "y_fp_s32": "0x01458200"} and
        reuse["mutation_control"]["rejected_frame_2514"] == {
            "x_fp_s32": "0x02a76200", "y_fp_s32": "0x01467900"} and
        reuse["mutation_control"]["rejected_frame_2517"] == {
            "x_fp_s32": "0x02aec400", "y_fp_s32": "0x0144f200"} and
        reuse["spec_executable"] is True,
        "Coffee Shop recurring fixed-point reuse fixture drift")
    require(
        primary_presentation["presentation_ownership"] ==
            "reused_record_residue" and
        primary_presentation["presentation_writer_pcs"] == [] and
        primary_presentation["mutation_control"]
            ["fixed_post_allocation_pose_forbidden"] is True and
        auxiliary_presentation["presentation_ownership"] ==
            "reused_record_residue" and
        auxiliary_presentation["presentation_writer_pcs"] == [] and
        auxiliary_presentation["source_samples"]
            ["post_allocation_frame_2572"]["animation_record"] ==
                "0x0012e778" and
        auxiliary_presentation["source_samples"]
            ["first_action_frame_2573"] == {
                "slot": "0xffa240", "logical_selector_u8": 0x35,
                "animation_record": "0x0012e38c",
                "animation_timer_u16": 8,
                "animation_branch_s16": 0,
                "assembly": "0x0013065e"} and
        auxiliary_presentation["mutation_control"] == {
            "clear_reused_presentation_rejected": True,
            "fixed_primary_pose_rejected": True,
            "decimal_35_selector_rejected": True},
        "Coffee Shop recurring presentation reuse fixture drift")
    scene_items = (scene["actor_lifetimes"] + scene["audio_events"] +
                   scene["health_writes"] + scene["route_edges"] +
                   scene["load_boundaries"] + scene["navigation"]["camera_runs"] +
                   scene["navigation"]["terrain_records"] + scene["systems"])
    require(scene["schema"] == "spec02-coffee-shop-scene-manifest-v1" and
            scene["source_frame_range"] == [1972, 5566] and
            scene["capture_identity"]["byte_identical"] is True and
            len(scene["pool_scan"]) == 11 and
            len(scene["actor_lifetimes"]) == 747 and
            len(scene["class_type_inventory"]) == 38 and
            len(scene["audio_events"]) == 279 and
            len(scene["health_writes"]) == 149 and
            sum(item["damage_writer"] for item in
                scene["health_writes"]) == 30 and
            len(scene["route_edges"]) == 4 and
            len(scene["load_boundaries"]) == 2 and
            len(scene["navigation"]["camera_runs"]) == 7 and
            len(scene["navigation"]["terrain_records"]) == 3 and
            all(item["classification"] in SCENE_CLASSIFICATIONS
                for item in scene_items) and
            all(item["classification"] in SCENE_CLASSIFICATIONS
                for item in scene["class_type_inventory"]) and
            next(item for item in scene["class_type_inventory"]
                 if item["type"] == 12 and item["class"] == "0x1f")
                 ["classification"] == "NATIVE_IMPLEMENTED" and
            sum(scene["classification_counts"].values()) == len(scene_items) and
            len(scene["blocked_class_type_pairs"]) == 21 and
            scene["acceptance_gate"] == {
                "source_actor_lifetimes": 747,
                "source_class_type_pairs": 38,
                "source_audio_events": 279,
                "source_health_writes": 149,
                "source_damage_writes": 30,
                "missing_or_extra_entities_allowed": False,
                "silent_omission_allowed": False,
                "scene_differential_pass": False,
                "ready": False},
            "Coffee Shop scene manifest incomplete or falsely accepted")
    weapon_contract = fixtures["authority_data"]["player"][
        "weapon_projectile_resource"]["implementation_contract"]
    weapon_source_input = weapon_contract["source_input"]
    weapon_action = weapon_contract["sufficient_action"]
    stage_progress = weapon_contract["sufficient_action"][
        "source_stage_progress"]
    require(weapon_source_input["physical_to_action_visible_frames_u8"] == 2 and
            weapon_source_input["native_input_pipeline_updates_u8"] == 1 and
            weapon_source_input["action_dispatch_delay_updates_u8"] == 1 and
            weapon_action["parent_allocation_tick"] == 1 and
            stage_progress["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            stage_progress["spec_executable"] is True and
            stage_progress["caller"]["player_state_program"] ==
                "0x024060" and
            stage_progress["caller"]["delta_load_pc"] == "0x024094" and
            stage_progress["caller"]["helper_call_pc"] == "0x024096" and
            stage_progress["caller"]["delta_u16"] == 3 and
            stage_progress["caller"]["action_entry_tick_u8"] == 0 and
            stage_progress["helper"]["entry"] == "0x0179e2" and
            stage_progress["helper"]["return"] == "0x017b74" and
            stage_progress["helper"]["guard"] == {
                "field": "a5+0x01b0:u8",
                "predicate": "u8(a5+0x01b0) == 0",
                "checked_before_add_and_before_route_bounds": True} and
            stage_progress["helper"]["fields"] == {
                "progress": "a5+0x0226:u16",
                "stage_parameter": "a5+0x01ea:s16",
                "upper_bound": "a5+0x021a:s16",
                "lower_bound": "a5+0x021c:s16"} and
            stage_progress["helper"]["field_layout"] == {
                "guard": {"a5_offset_u16": 0x01b0,
                          "absolute": "0x00ff81b0", "width_u8": 1,
                          "signed": False},
                "stage_parameter": {"a5_offset_u16": 0x01ea,
                                    "absolute": "0x00ff81ea",
                                    "width_u8": 2, "signed": True},
                "upper_bound": {"a5_offset_u16": 0x021a,
                                "absolute": "0x00ff821a", "width_u8": 2,
                                "signed": True},
                "lower_bound": {"a5_offset_u16": 0x021c,
                                "absolute": "0x00ff821c", "width_u8": 2,
                                "signed": True},
                "progress": {"a5_offset_u16": 0x0226,
                             "absolute": "0x00ff8226", "width_u8": 2,
                             "signed": False}} and
            (stage_progress["helper"]["progress_threshold_u16"],
             stage_progress["helper"]["progress_mask_u16"],
             stage_progress["helper"]["stage_domain_limit_u16"],
             stage_progress["helper"]["stage_domain_mask_u16"],
             stage_progress["helper"]["coffee_shop_lower_bound_s16"],
             stage_progress["helper"]["coffee_shop_upper_bound_s16"]) ==
                (8, 7, 32, 31, 8, 16) and
            stage_progress["helper"]["rng_calls"] == [] and
            [(row["source_frame_u16"], row["progress_before_u16"],
              row["progress_after_add_u16"],
              row["progress_after_mask_u16"],
              row["stage_before_s16"], row["stage_after_s16"])
             for row in stage_progress["coffee_shop_calls"][:3]] == [
                (2252, 0, 3, 3, 8, 8),
                (2342, 3, 6, 6, 8, 8),
                (2432, 6, 9, 1, 8, 9)] and
            len(stage_progress["coffee_shop_calls"]) == 15 and
            stage_progress["capture_identity"][
                "byte_identical_selected_rows"] is True and
            stage_progress["fixed_frame_substitute"] is False,
            "Predator Button1 stage-progress fixture incomplete or drifted")
    child_emitter = weapon_contract["record4_parent_class0"][
        "child_emitter_state"]
    require(child_emitter["child_initial_facing_u8"] == 0 and
            child_emitter["child_facing_rule"] ==
                "the record-4 allocator clears child facing to zero; parent facing is read only for the row-x sign and is not copied" and
            [(row["source_slot"], row["variant_u8"], row["facing_u8"],
              row["parent_facing_u8"]) for row in
             child_emitter["coffee_shop_collision_child_witnesses"]] == [
                ("0x00ff8900", 1, 0, 1),
                ("0x00ff8800", 2, 0, 1)],
            "record-4 child allocator-cleared facing drift")
    child_reuse = weapon_contract[
            "record4_child_class4"]["fixed_slot_reuse_presentation"]
    require(child_reuse["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            child_reuse["spec_executable"] is True and
            child_reuse["allocator"] == "0x01773e" and
            child_reuse["release"] == "0x017754" and
            child_reuse["retained_fields"] == [
                "animation_record_u32", "assembly_u32",
                "animation_timer_u16", "animation_branch_s16"] and
            child_reuse["coffee_shop_slot_0xff8800"] == {
                "prior_terminal_visible_frame_u16": 2333,
                "prior_state_u16": "0x0400", "prior_variant_u8": 0,
                "retained_animation_record": "0x0003088c",
                "retained_assembly": "0x00030b28",
                "retained_animation_timer_u16": 1,
                "retained_animation_branch_s16": -32768,
                "reuse_visible_frame_u16": 2371,
                "reuse_state_u16": "0x0000", "reuse_variant_u8": 2,
                "initialization_visible_frame_u16": 2372,
                "initialized_state_u16": "0x0200",
                "initialized_animation_record": "0x00030944",
                "initialized_assembly": "0x00030bd6",
                "initialized_animation_timer_u16": 2,
                "initialized_animation_branch_s16": 0} and
            child_reuse["mutation_control"][
                "rejected_visible_frame_u16"] == 2371 and
            child_reuse["mutation_control"]["fixed_frame_substitute"] is False,
            "record-4 child fixed-slot presentation retention drift")
    button3 = fixtures["authority_data"]["player"][
        "directional_airborne_interruption"]["directional_actions"][
            "implementation_contract"]
    require(button3["spec_executable"] is True and
            button3["source_input"]["button3_mask_u8"] == "0x40" and
            [entry["x_velocity_s32_16_16"]["raw_s32"]
             for entry in button3["vector_table"]] ==
            [0, 0, -0x000f0000, -0x00090000,
             0x00090000, 0x00088000] and
            button3["input_facing_mapping"][3]["entry_index"] == 4 and
            button3["initialization"]["non_down"][
                "opposite_facing_horizontal"]["collision_level_u8"] == 8 and
            button3["motion_and_landing"]["landing_0x023630"][
                "presentation_selector_u8"] == 10 and
            button3["motion_and_landing"]["phase_0x040a"][
                "negative_velocity_transition"]["phase_timer_s16"] == 10 and
            button3["presentation_actor_fields"]["coordinate_mode_u8"] == 0 and
            button3["presentation_actor_fields"]["palette_u8"] == 0 and
            button3["presentation_actor_fields"]["object_or_u16"] == "0x8000" and
            button3["rng_calls"] == [],
            "Button3 implementation fixture incomplete or drifted")
    class03 = fixtures["authority_data"]["player"][
        "directional_airborne_interruption"]["airborne_actions"]["button1"][
            "record4_class03"]
    require(class03["spec_executable"] is True and
            class03["record_type_u8"] == 4 and class03["class_u8"] == 3 and
            class03["dispatch"] == "0x030382" and
            class03["state_sequence_u8"] == [0, 2, 4, 6] and
            class03["allocation"]["active_writer"] == "0x02387e" and
            class03["player_phase_0x0406"]["presentation_selector_u8"] == 18 and
            len(class03["player_phase_0x0406"]["presentation_records"]) == 5 and
            class03["initialization"]["collision_table_u32"] ==
                "0x0002fc3c" and
            len(class03["initialization"]["presentation_records"]) == 8 and
            class03["initialization"]["presentation_records"][-1][
                "branch_s16"] == -32768 and
            len(class03["active_state"]["low_nibble_motion_tables_s16"]) == 15 and
            len(class03["active_state"]["high_nibble_motion_tables_s16"]) == 12 and
            class03["active_state"]["direction_index_range_u8"] == [0, 63] and
            class03["active_state"]["vectors_per_motion_table"] == 64 and
            all(len(rows) == 64 for rows in
                class03["active_state"]["low_nibble_motion_tables_s16"].values()) and
            all(len(rows) == 64 for rows in
                class03["active_state"]["high_nibble_motion_tables_s16"].values()) and
            class03["child_emitter_state"]["cadence_reload_u8"] == 4 and
            class03["effect_allocation"]["record_type_u8"] == 24 and
            class03["effect_allocation"]["class_u8"] == 0x49 and
            class03["effect_allocation"]["variant_u8"] == 1 and
            class03["effect_allocation"]["timer_u8"] == 8 and
            class03["effect_allocation"]["accepted_auxiliary_contract"][
                "dispatch"] == "0x08f080" and
            class03["effect_allocation"]["audio_command"] is None and
            class03["suppression_control"]["suppressed_writes"] == 1 and
            class03["rng_calls"] == [],
            "airborne Button1 class-3 implementation fixture drift")
    class00 = next(item for item in
                   fixtures["authority_data"]["enemies"]["archetypes"]
                   if item["class"] == "0x00" and item["type"] == 12)
    class00_program = class00["whole_routine_implementation_contract"]
    require(class00_program == source["class00_program"] and
            class00_program["status"] == "SPEC_EXECUTABLE" and
            class00_program["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            len(class00_program["reachable_state_substate_contexts"]) == 39 and
            len(class00_program["dispatch"]["active_action_high_byte"]) == 17 and
            len(class00_program["dispatch"]["action_substate_low_byte"]) == 8 and
            class00_program["normalized_source_program"]["instruction_count"] == 904 and
            len(class00_program["dynamic_witness"]["contexts"]) == 39 and
            class00_program["dynamic_witness"]["counts"] == {
                "entries": 5821, "samples": 6397, "writes": 40876,
                "rng_calls": 194, "player_damage_writes": 2} and
            all(class00_program["mutation_controls"].values()) and
            class00_program["implementation_rules"]
                ["runtime_68000_interpretation_forbidden"] is True and
            class00_program["implementation_rules"]
                ["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x00/type-12 whole-routine fixture incomplete or drifted")
    class01 = next(item for item in
                   fixtures["authority_data"]["enemies"]["archetypes"]
                   if item["class"] == "0x01" and item["type"] == 12)
    class01_program = class01["whole_routine_implementation_contract"]
    require(class01_program == source["class01_program"] and
            class01_program["status"] == "SPEC_EXECUTABLE" and
            class01_program["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            len(class01_program["reachable_state_substate_contexts"]) == 32 and
            len(class01_program["dispatch"]) == 25 and
            sum(row["entry_count"] for row in
                class01_program["dispatch"].values()) == 119 and
            class01_program["normalized_source_program"]
                ["instruction_count"] == 1620 and
            len(class01_program["normalized_source_program"]
                ["field_access_profiles"]) == 69 and
            class01_program["dynamic_witness"]["counts"] == {
                "entries": 3304, "samples": 3796, "writes": 30904,
                "rng_calls": 131, "player_damage_writes": 1} and
            all(class01_program["mutation_controls"].values()) and
            class01_program["implementation_rules"]
                ["runtime_68000_interpretation_forbidden"] is True and
            class01_program["implementation_rules"]
                ["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x01/type-12 whole-routine fixture incomplete or drifted")
    class06 = next(item for item in
                   fixtures["authority_data"]["enemies"]["archetypes"]
                   if item["class"] == "0x06" and item["type"] == 12)
    class06_program = class06["whole_routine_implementation_contract"]
    require(class06_program == source["class06_program"] and
            class06_program["status"] == "SPEC_EXECUTABLE" and
            class06_program["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            len(class06_program["reachable_state_substate_contexts"]) == 40 and
            len(class06_program["dispatch"]) == 29 and
            sum(row["entry_count"] for row in
                class06_program["dispatch"].values()) == 137 and
            class06_program["normalized_source_program"]
                ["instruction_count"] == 1788 and
            len(class06_program["normalized_source_program"]
                ["field_access_profiles"]) == 92 and
            len(class06_program["normalized_source_program"]
                ["external_transfers"]) == 29 and
            class06_program["dynamic_witness"]["counts"] == {
                "entries": 8855, "samples": 9482, "writes": 101686,
                "rng_calls": 216, "player_damage_writes": 13} and
            all(class06_program["mutation_controls"].values()) and
            class06_program["implementation_rules"]
                ["runtime_68000_interpretation_forbidden"] is True and
            class06_program["implementation_rules"]
                ["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x06/type-12 whole-routine fixture incomplete or drifted")
    class07 = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x07" and item["type"] == 20)
    class07_program = class07["whole_routine_implementation_contract"]
    require(class07_program == source["class07_program"] and
            class07_program["status"] == "SPEC_EXECUTABLE" and
            class07_program["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            len(class07_program["reachable_state_substate_contexts"]) == 2 and
            len(class07_program["dispatch"]) == 2 and
            sum(row["entry_count"] for row in
                class07_program["dispatch"].values()) == 7 and
            class07_program["normalized_source_program"]
                ["instruction_count"] == 135 and
            len(class07_program["normalized_source_program"]
                ["field_access_profiles"]) == 33 and
            len(class07_program["normalized_source_program"]
                ["external_transfers"]) == 10 and
            class07_program["dynamic_witness"]["counts"] == {
                "entries": 26565, "samples": 28446, "writes": 26619,
                "rng_calls": 0, "player_effects": 0} and
            all(class07_program["mutation_controls"].values()) and
            class07_program["implementation_rules"]
                ["runtime_68000_interpretation_forbidden"] is True and
            class07_program["implementation_rules"]
                ["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x07/type-20 whole-routine fixture incomplete or drifted")
    class10 = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x10" and item["type"] == 24)
    class10_program = class10["whole_routine_implementation_contract"]
    require(class10_program == source["class10_program"] and
            class10_program["status"] == "SPEC_EXECUTABLE" and
            class10_program["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            len(class10_program["reachable_state_substate_contexts"]) == 3 and
            len(class10_program["dispatch"]) == 1 and
            sum(row["entry_count"] for row in
                class10_program["dispatch"].values()) == 4 and
            class10_program["variant_tables"]["entry_count"] == 6 and
            class10_program["normalized_source_program"]
                ["instruction_count"] == 28 and
            len(class10_program["normalized_source_program"]
                ["field_access_profiles"]) == 10 and
            len(class10_program["normalized_source_program"]
                ["external_transfers"]) == 4 and
            class10_program["dynamic_witness"]["counts"] == {
                "entries": 4769, "samples": 4694, "writes": 23665,
                "rng_calls": 0, "player_effects": 0} and
            all(class10_program["mutation_controls"].values()) and
            class10_program["implementation_rules"]
                ["runtime_68000_interpretation_forbidden"] is True and
            class10_program["implementation_rules"]
                ["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x10/type-24 whole-routine fixture incomplete or drifted")
    class3d = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x3d" and item["type"] == 24)
    class3d_program = class3d["whole_routine_implementation_contract"]
    require(class3d_program == source["class3d_program"] and
            class3d_program["status"] == "SPEC_EXECUTABLE" and
            class3d_program["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            len(class3d_program["reachable_state_substate_contexts"]) == 3 and
            len(class3d_program["dispatch"]) == 1 and
            sum(row["entry_count"] for row in
                class3d_program["dispatch"].values()) == 4 and
            class3d_program["movement_table"]["entry_count"] == 16 and
            class3d_program["normalized_source_program"]
                ["instruction_count"] == 34 and
            len(class3d_program["normalized_source_program"]
                ["field_access_profiles"]) == 11 and
            len(class3d_program["normalized_source_program"]
                ["external_transfers"]) == 4 and
            class3d_program["dynamic_witness"]["counts"] == {
                "entries": 11476, "samples": 12811, "writes": 121404,
                "rng_calls": 0, "player_effects": 0} and
            all(class3d_program["mutation_controls"].values()) and
            class3d_program["implementation_rules"]
                ["runtime_68000_interpretation_forbidden"] is True and
            class3d_program["implementation_rules"]
                ["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x3d/type-24 whole-routine fixture incomplete or drifted")
    class49 = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x49" and item["type"] == 24)
    class49_program = class49["whole_routine_implementation_contract"]
    require(class49_program == source["class49_program"] and
            class49_program["status"] == "SPEC_EXECUTABLE" and
            class49_program["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            len(class49_program["reachable_state_substate_contexts"]) == 3 and
            len(class49_program["dispatch"]) == 1 and
            sum(row["entry_count"] for row in
                class49_program["dispatch"].values()) == 4 and
            class49_program["normalized_source_program"]
                ["instruction_count"] == 39 and
            len(class49_program["normalized_source_program"]
                ["field_access_profiles"]) == 12 and
            len(class49_program["normalized_source_program"]
                ["external_transfers"]) == 4 and
            class49_program["dynamic_witness"]["counts"] == {
                "entries": 4808, "samples": 4209, "writes": 19339,
                "rng_calls": 0, "player_effects": 0} and
            class49_program["allocation_helpers"]["variant0"]["variant_u8"] == 0 and
            class49_program["allocation_helpers"]["variant1"]["variant_u8"] == 1 and
            all(class49_program["mutation_controls"].values()) and
            class49_program["implementation_rules"]
                ["runtime_68000_interpretation_forbidden"] is True and
            class49_program["implementation_rules"]
                ["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x49/type-24 whole-routine fixture incomplete or drifted")
    class4b = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x4b" and item["type"] == 24)
    class4b_program = class4b["whole_routine_implementation_contract"]
    require(class4b_program == source["class4b_program"] and
            class4b_program["status"] == "SPEC_EXECUTABLE" and
            class4b_program["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            len(class4b_program["reachable_state_substate_contexts"]) == 3 and
            len(class4b_program["dispatch"]) == 1 and
            sum(row["entry_count"] for row in
                class4b_program["dispatch"].values()) == 4 and
            class4b_program["normalized_source_program"]
                ["instruction_count"] == 26 and
            len(class4b_program["normalized_source_program"]
                ["field_access_profiles"]) == 8 and
            len(class4b_program["normalized_source_program"]
                ["external_transfers"]) == 5 and
            class4b_program["dynamic_witness"]["counts"] == {
                "entries": 661, "samples": 810, "writes": 4080,
                "rng_calls": 0, "player_effects": 0} and
            len(class4b_program["state_contract"]["state0"]
                ["animation_records"]) == 32 and
            all(class4b_program["mutation_controls"].values()) and
            class4b_program["implementation_rules"]
                ["runtime_68000_interpretation_forbidden"] is True and
            class4b_program["implementation_rules"]
                ["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x4b/type-24 whole-routine fixture incomplete or drifted")
    class4e = next(item for item in
                   fixtures["authority_data"]["auxiliary"]["archetypes"]
                   if item["class"] == "0x4e" and item["type"] == 24)
    class4e_program = class4e["whole_routine_implementation_contract"]
    require(class4e_program == source["class4e_program"] and
            class4e_program["status"] == "SPEC_EXECUTABLE" and
            class4e_program["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            len(class4e_program["reachable_state_substate_contexts"]) == 3 and
            len(class4e_program["dispatch"]) == 1 and
            sum(row["entry_count"] for row in
                class4e_program["dispatch"].values()) == 4 and
            class4e_program["variant_tables"]["entry_count"] == 26 and
            class4e_program["variant_tables"]["reachable_variant_u8"] ==
                [0, 1, 4, 5, 10, 20, 24, 25] and
            class4e_program["normalized_source_program"]
                ["instruction_count"] == 31 and
            len(class4e_program["normalized_source_program"]
                ["field_access_profiles"]) == 8 and
            len(class4e_program["normalized_source_program"]
                ["external_transfers"]) == 5 and
            class4e_program["dynamic_witness"]["counts"] == {
                "entries": 848, "samples": 909, "writes": 3732,
                "rng_calls": 80, "player_effects": 0} and
            len(class4e_program["presentation_collision"]["records"]) == 53 and
            all(class4e_program["mutation_controls"].values()) and
            class4e_program["implementation_rules"]
                ["runtime_68000_interpretation_forbidden"] is True and
            class4e_program["implementation_rules"]
                ["unknown_state_or_transition_logic_allowed"] is False,
            "class-0x4e/type-24 whole-routine fixture incomplete or drifted")
    class1f = next(item for item in
                   fixtures["authority_data"]["enemies"]["archetypes"]
                   if item["class"] == "0x1f")
    class1f_records = {row["animation_record"]: row for row in
                       class1f["presentation_and_collision"]["records"]}
    expected_hit_ko = {
        "0x0012d2f8": ("0x0012f994", 1, 0),
        "0x0012dd50": ("0x00130248", 1, 0),
        "0x0012e214": ("0x0013020c", 14, 0),
        "0x0012e224": ("0x0013020c", 14, 0),
        "0x0012e234": ("0x0013020c", 14, 0),
        "0x0012e244": ("0x0013020c", 14, 0),
        "0x0012e254": ("0x00130294", 0, 0),
        "0x0012e268": ("0x00130346", 0, 0),
    }
    expected_first_button1_targets = {
        "0x0012eb5c": ("0x0012f762", 1, 0),
        "0x0012ec74": ("0x0012f8b8", 2, 0),
    }
    require(all(address in class1f_records and
                (class1f_records[address]["assembly"],
                 class1f_records[address]["hurt_selector"],
                 class1f_records[address]["attack_selector"]) == fields
                for address, fields in expected_hit_ko.items()) and
            class1f["presentation_and_collision"]["accepted_hit_ko_records"]
                ["fixed_frame_presentation_forbidden"] is True,
            "class-0x1f HIT/KO presentation fixture incomplete or drifted")
    require(all(address in class1f_records and
                (class1f_records[address]["assembly"],
                 class1f_records[address]["hurt_selector"],
                 class1f_records[address]["attack_selector"]) == fields
                for address, fields in expected_first_button1_targets.items()),
            "class-0x1f first Button1 target selectors incomplete or drifted")
    class1f_damage = class1f["current_state_implementation_contract"][
        "damage_hit_ko_removal"]
    class1f_collision_facing = class1f_damage[
        "common_collision_reaction_facing"]
    require(class1f_collision_facing["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            class1f_collision_facing["source_entry"] == "0x01d416" and
            class1f_collision_facing["reaction_facing_writer"] ==
                "0x01d448" and
            class1f_collision_facing["facing_xor_writer"] == "0x01d44e" and
            class1f_collision_facing["source_window_sha256"] ==
                "aab16f054a654c0cbb500ed9df53f80b56ee323a7bee89b03351f1f69f3564e6" and
            class1f_collision_facing["guard"] == {
                "excluded_target_type_u8": 0x14,
                "excluded_target_classes_u8": [0x11, 0x20, 0x10, 0x26],
                "coffee_shop_class1f_type12_reaches_writer": True,
                "coffee_shop_attack_record": "0x02fc58",
            } and
            class1f_collision_facing["facing_xor_u8"] == 1 and
            class1f_collision_facing["coffee_shop_control"] == {
                "source_frame_u16": 3830,
                "target_slot": "0x00ffa000",
                "reaction_facing_u8": 1,
                "facing_u8": 0,
                "health_s16": -1,
                "outer_state_u16": 0x0400,
            },
            "class-0x1f common collision reaction-facing fixture incomplete or drifted")
    class1f_hit = class1f_damage["source_hit_entry_program"]
    require(class1f_hit["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            class1f_hit["capture_identity"]["byte_identical"] is True and
            class1f_hit["entry_guard"]["recovery_timer_actor_2c_u8"] == 8 and
            class1f_hit["reaction_table"]
                ["reaction_selector_actor_4d_u8"] == 0x36 and
            class1f_hit["reaction_table"]["hit_mode_actor_46_u8"] == 2 and
            class1f_hit["reaction_record"]["animation_record"] ==
                "0x0012e04c" and
            class1f_hit["reaction_record"]["assembly"] == "0x001308a6" and
            class1f_hit["visible_result"] == {
                "action_phase_u16": 2,
                "animation_record": "0x0012e04c",
                "assembly": "0x001308a6",
                "facing_u8": 1,
                "health_s16": 56,
                "slot": "0x00ffa180",
                "source_frame": 2308,
                "state_u16": 514,
            } and
            class1f_hit["recovery"]["captured_values_before_decrement"] ==
                [8, 7, 6, 5, 4, 3, 2, 1, 0] and
            class1f_hit["recovery"]["next_action_phase_u16"] == 0x0200 and
            class1f_hit["recovery"]["transition_scheduler_boundary"]
                ["recovery_transition_returns_before_action_dispatch"] is True and
            class1f_hit["recovery"]["transition_scheduler_boundary"]
                ["transition_visible_source_frame"] == 2317 and
            class1f_hit["recovery"]["transition_scheduler_boundary"]
                ["launch_visible_source_frame"] == 2318 and
            class1f_hit["entry_rng_calls"] == [] and
            class1f_hit["action_dispatch"]["required_action_phases_u16"] ==
                [0x0200, 0x0202, 0x0204, 0x0206, 0x0208, 0x020A] and
            class1f_hit["source_hit_program"]["phase_0x0200_launch"]
                ["observed_written_motion"]["x_velocity_s32_16_16"] ==
                -0x1C000 and
            class1f_hit["source_hit_program"]["phase_0x0202_first_flight"]
                ["landing_visible_frame"] == 2364 and
            class1f_hit["source_hit_program"]["phase_0x0204_landing_hold"]
                ["captured_values_before_decrement"] == [3, 2, 1] and
            class1f_hit["source_hit_program"]["phase_0x0206_bounce"]
                ["observed_motion_after_facing"]
                ["y_acceleration_s32_16_16"] == -0xC000 and
            class1f_hit["source_hit_program"]["phase_0x0208_rng_hold"]
                ["timer_initial_u8"] == 10 and
            class1f_hit["source_hit_program"]
                ["phase_0x020a_terminal_animation"]["records"][-1]
                ["animation_record"] == "0x0012ded8" and
            class1f_hit["source_hit_program"]["animation_sequences"]
                ["reaction_0x36"]["records"][0]["animation_record"] ==
                "0x0012e04c" and
            class1f_hit["source_hit_program"]["selector_context_rule"]
                ["generic_action_selector_0x36_record"] == "0x0012e410" and
            class1f_hit["source_hit_program"]["selector_context_rule"]
                ["generic_action_selector_binding_forbidden"] is True and
            class1f_hit["source_hit_program"]["normal_return"]
                ["class1f_resume_at_2414"] == "0x0200:1600" and
            class1f_hit["source_hit_program"]["normal_return"]
                ["class_tail"] == {
                    "entry": "0x061060",
                    "write": "actor+0x85:u8 = 0",
                    "style85_after_u8": 0,
                    "source_window_sha256":
                        "e736553ff1aa855cdd3f210b41bf58e3a24d79571acb07ccb6afc9a5cad4076b",
                } and
            class1f_hit["source_hit_program"]["normal_return"]
                ["preserved_resume_fields"] == {
                    "source_frame": 2413,
                    "dispatch_pc": "0x0607e8",
                    "actor_85_style_u8": 0,
                    "actor_a3_u8": 0,
                    "actor_a4_u8": 1,
                    "actor_a5_u8": 1,
                    "actor_a6_u8": 1,
                    "actor_b0_u8": 2,
                    "facing_u8": 1,
                    "actor_x_s16": 582,
                    "actor_z_s16": 310,
                    "player_x_s16": 944,
                    "player_z_s16": 320,
                } and
            class1f_hit["rng"]["calls"] == 1 and
            class1f_hit["rng"]["seed_before_u16"] == 0xEDD9 and
            class1f_hit["rng"]["seed_after_u16"] == 0xC9A2 and
            class1f_hit["rng"]["result_low_nibble_u8"] == 2 and
            class1f_hit["rng"]["timer_table_row_u8"] ==
                [10, 10, 10, 10, 40, 40, 40, 40,
                 60, 60, 60, 90, 90, 90, 120, 120] and
            class1f_hit["rng"]["selected_timer_u8"] == 10 and
            class1f_hit["mutation_control"]["mutations"] == 2 and
            class1f_hit["mutation_control"]["mutant_animation_record"] ==
                "0x0012dc50" and
            class1f_hit["mutation_control"]
                ["fixed_frame_or_generic_reaction_rejected"] is True,
            "class-0x1f source HIT entry fixture incomplete or drifted")
    class1f_ko = class1f_damage["source_projectile_ko_program"]
    require(class1f_ko["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            class1f_ko["capture_identity"]["byte_identical"] is True and
            class1f_ko["collision_visible_result"] == {
                "source_frame": 2363,
                "source_slot": "0x00ffa3c0",
                "active_u8": 1,
                "outer_state_u16": 0x0400,
                "action_substate_u16": 0,
                "health_s16": -1,
                "prior_health_s16": 87,
                "preserved_animation_record": "0x0012d638",
            } and
            class1f_ko["scheduler_handoff"]["source_frame"] == 2364 and
            class1f_ko["scheduler_handoff"]["active_u8"] == 2 and
            class1f_ko["scheduler_handoff"]["outer_state_u16"] == 0x0402 and
            class1f_ko["scheduler_handoff"]
                ["recovery_values_before_decrement_u8"] ==
                    [8, 7, 6, 5, 4, 3, 2, 1, 0] and
            class1f_ko["scheduler_handoff"]
                ["reaction_selector_actor_4d_u8"] == 0x36 and
            class1f_ko["scheduler_handoff"]["hit_mode_actor_46_u8"] == 0 and
            class1f_ko["scheduler_handoff"]["hit_kind_actor_49_u8"] == 0x15 and
            class1f_ko["state_program"]["states_u16"] ==
                [0x0400, 0x0402, 0x0404, 0x0600] and
            class1f_ko["state_program"]["action_phases_u16"] ==
                [0, 0x0200, 0x0400, 0x0600] and
            class1f_ko["state_program"]["launch"]
                ["y_velocity_s32_16_16"] == 0x98000 and
            class1f_ko["state_program"]["launch"]
                ["y_acceleration_s32_16_16"] == -0x5000 and
            class1f_ko["state_program"]["first_landing"]
                ["timer_actor_2a_u8"] == 3 and
            class1f_ko["state_program"]["bounce"]
                ["y_acceleration_s32_16_16"] == -0xC000 and
            class1f_ko["state_program"]["removal_hold"]
                ["timer_actor_2a_u8"] == 60 and
            class1f_ko["state_program"]["release"]
                ["release_writer"] == "0x0176ba" and
            class1f_ko["state_program"]["rng_calls"] == [] and
            class1f_ko["state_program"]["animation_sequences"]
                ["reaction_0x36"]["records"][0]["animation_record"] ==
                    "0x0012e04c",
            "class-0x1f projectile KO fixture incomplete or drifted")
    class1f_actions = class1f["first_segment_action_execution_contract"]
    class1f_player_collision = class1f_actions[
        "current_state_player_collision"]
    require(class1f_actions["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            class1f_actions["capture_identity"]["byte_identical"] is True and
            len(class1f_actions["initializer"]["variants"]) == 10 and
            [row["action_u8"] for row in
             class1f_actions["current_dispatch"]["action_targets"]] ==
                list(range(0, 32, 2)) and
            class1f_actions["current_dispatch"]["action_targets"][11] ==
                {"action_u8": 22, "target": "0x060c2e"} and
            class1f_actions["current_dispatch"]["required_state_contexts"] ==
                ["0x0200:0000", "0x0200:0200", "0x0200:0400",
                 "0x0200:0402", "0x0200:0404", "0x0200:0406",
                 "0x0200:0408", "0x0200:0600", "0x0200:0800",
                 "0x0200:0a00", "0x0200:0c00", "0x0200:0c02",
                 "0x0200:0c04", "0x0200:0e00", "0x0200:0e02",
                 "0x0200:0e04", "0x0200:1000", "0x0200:1200",
                 "0x0200:1400", "0x0200:1402", "0x0200:1404",
                 "0x0200:1406", "0x0200:1408", "0x0200:1600",
                 "0x0200:1800", "0x0200:1a00", "0x0200:1c00",
                 "0x0200:1e00"] and
            [row["selector_u8"] for row in
             class1f_actions["animation_selector_table"]["selectors"]] ==
                [0, 1, 34, 35, 36, 43, 52, 53, 54, 55, 56, 60, 62, 68, 69, 70,
                 71, 72, 73, 74, 76, 77] and
            [row["table_index_u8"] for row in
             class1f_actions["movement_tables"]] == [1, 8] and
            class1f_actions["movement_tables"][1]["vectors"][8] ==
                {"direction_u8": 8, "x_delta_s16": 2048,
                 "y_delta_s16": 0} and
            class1f_actions["action_programs"]["source_bounds"]
                ["activation_field_u8"] == "actor+0x01" and
            class1f_actions["action_programs"]["source_bounds"]
                ["latched_field_u8"] == "actor+0xa2" and
            class1f_actions["action_programs"]["source_bounds"]
                ["camera_operand_u16"] == "0xff8278" and
            class1f_actions["action_programs"]["source_bounds"]
                ["phase_guard_field_u8"] == "0xff8019" and
            class1f_actions["action_programs"]["source_bounds"]
                ["phase_guard_mask_u8"] == 1 and
            class1f_actions["action_programs"]["source_bounds"]
                ["coffee_shop_hit_return_boundary"]["phase_odd"]
                ["phase_counter_u8"] == 0x97 and
            class1f_actions["action_programs"]["source_bounds"]
                ["coffee_shop_hit_return_boundary"]["phase_even"]
                ["relative_u16"] == "0xfff9" and
            class1f_actions["action_programs"]["source_bounds"]
                ["coffee_shop_hit_return_boundary"]["phase_even"]
                ["next_visible_source_frame_u16"] == 2471 and
            class1f_actions["action_programs"]["source_bounds"]
                ["x_max_u16"] == 0x05f0 and
            class1f_actions["action_programs"]["source_bounds"]
                ["camera_relative_bias_u16"] == 0x0070 and
            class1f_actions["action_programs"]["source_bounds"]
                ["camera_relative_span_u16"] == 0x0260 and
            class1f_actions["action_programs"]["source_bounds"]
                ["failure_outer_state_u16"] == 0x0600 and
            class1f_actions["action_programs"]
                ["animation_movement_helper_0x0165c4"]
                ["source_body_sha256"] ==
                "b35c9aaf0a5328ff35e6ccb5c9d278fef7f898201fc6e005e69d11bd566a970b" and
            class1f_actions["action_programs"]
                ["animation_movement_helper_0x0165c4"]
                ["movement_cadence"] ==
                "only on timer expiry after binding the next animation record" and
            class1f_actions["action_programs"]
                ["animation_movement_helper_0x0165c4"]
                ["movement_record"] == "newly bound next animation record" and
            class1f_actions["action_programs"]["direction_helper_0x061032"]
                ["upper_directions_by_a5_u8"] == [0x16, 0x0a] and
            class1f_actions["action_programs"]["direction_helper_0x061032"]
                ["lower_directions_by_a5_u8"] == [0x1a, 0x06] and
            class1f_actions["action_programs"]["action_0x0c"]
                ["initial_selector_u8"] == 0x35 and
            class1f_actions["action_programs"]["action_0x0c"]
                ["middle_selector_u8"] == 0x36 and
            class1f_actions["action_programs"]["action_0x0c"]
                ["coffee_shop_auxiliary_spawn"]["initial_animation_record"] ==
                    "0x0012e38c" and
            class1f_actions["action_programs"]["action_0x0e"]
                ["z_velocity_table_s32_16_16"] ==
                [-0x00010000, -0x00014000, -0x00018000, -0x00020000] and
            class1f_actions["action_programs"]["action_0x04"]
                ["selector_groups_u16"] ==
                [[55], [56], [43, 43, 43, 55], [43, 43, 56]] and
            class1f_actions["action_programs"]["action_0x04"]
                ["timer_stage_parameter_field"] == "0xff81ea:u16" and
            class1f_actions["action_programs"]["action_0x04"]
                ["timer_stage_offsets_u8"] ==
                [0] * 5 + [32] * 8 + [64] * 6 + [96] * 5 + [128] * 8 and
            len(class1f_actions["action_programs"]["action_0x04"]
                ["timer_rows_u8"]) == 5 and
            all(len(row) == 32 for row in
                class1f_actions["action_programs"]["action_0x04"]
                ["timer_rows_u8"]) and
            class1f_actions["action_programs"]["action_0x04"]
                ["coffee_shop_observation"]["timer_result_u8"] == 6 and
            class1f_actions["action_programs"]["action_0x04"]
                ["coffee_shop_observation"]["guard_field_u8"] == 1 and
            class1f_actions["action_programs"]["action_0x04"]
                ["phase_0_guard_ownership"]["field"] == "actor+0x6e:u8" and
            class1f_actions["action_programs"]["action_0x04"]
                ["phase_0_guard_ownership"]["initial_group_rule"] ==
                    "phase 0 performs no direct actor+0x6e write; the source selector-registration helper owns the clear before later collision can set it" and
            class1f_actions["action_programs"]["action_0x04"]
                ["phase_0_guard_ownership"]["collision_set_captured_pc"] ==
                    "0x01cbba" and
            class1f_actions["action_programs"]["action_0x04"]
                ["phase_0_guard_ownership"]
                ["selector_rebind_clear_captured_pc"] == "0x01d76e" and
            class1f_actions["action_programs"]["action_0x04"]
                ["phase_0_guard_ownership"]["capture_identity"]
                ["byte_identical"] is True and
            {key: class1f_actions["action_programs"]["action_0x16"]
                ["latched_retry_transition"][key] for key in (
                    "accepted_source_write_frame_u16",
                    "visible_source_frame_u16", "transition_latch_u8",
                    "a6_u8", "seed_before_u16", "seed_after_u16",
                    "timer_index_u8", "timer_u8", "next_action_u8",
                    "facing_after_u8", "selector_u8",
                    "animation_record_u32",
                    "fixed_frame_substitute_forbidden")} == {
                        "accepted_source_write_frame_u16": 2409,
                        "visible_source_frame_u16": 2410,
                        "transition_latch_u8": 1,
                        "a6_u8": 2,
                        "seed_before_u16": 0x4bdf,
                        "seed_after_u16": 0xe3c2,
                        "timer_index_u8": 2,
                        "timer_u8": 30,
                        "next_action_u8": 0x1a,
                        "facing_after_u8": 0,
                        "selector_u8": 35,
                        "animation_record_u32": "0x0012d5e4",
                        "fixed_frame_substitute_forbidden": True} and
            class1f_actions["attack_timer_table_u8"] ==
                [30] * 4 + [60] * 4 + [120] * 4 + [160] * 4 and
            {key: class1f_actions["suppression_control"][key] for key in (
                "writer_pc", "suppressed_writes", "baseline_transition_rows",
                "mutant_transition_rows", "baseline_lifecycle_releases",
                "mutant_lifecycle_releases", "baseline_main_aux_spawns",
                "mutant_main_aux_spawns", "baseline_final_route",
                "mutant_final_route", "fixed_frame_substitute")} == {
                    "writer_pc": "0x0607e8", "suppressed_writes": 179,
                    "baseline_transition_rows": 337,
                    "mutant_transition_rows": 627,
                    "baseline_lifecycle_releases": 22,
                    "mutant_lifecycle_releases": 23,
                    "baseline_main_aux_spawns": [15, 3],
                    "mutant_main_aux_spawns": [16, 3],
                    "baseline_final_route": 4, "mutant_final_route": 4,
                    "fixed_frame_substitute": False} and
            class1f_actions["suppression_control"]["action4_timer"] == {
                "writer_pc": "0x060944", "suppressed_writes": 1,
                "baseline_timer_u8": 6, "mutant_timer_u8": 0,
                "first_difference_frame": 2798,
                "first_difference_slot": "0x00ffa240",
                "score_unchanged": True, "audio_dispatch_unchanged": True,
                    "route_exit_unchanged": True} and
            class1f_player_collision["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            class1f_player_collision["capture_identity"]
                ["byte_identical"] is True and
            class1f_player_collision["attacker"] == {
                "table_set": "0x130ac8",
                "attack_table": "0x130b4c",
                "selector_source": "current animation record byte +9",
                "animation_record": "0x0012d8a0",
                "attack_selector_u8": 1,
                "attack_record": "0x130b5c",
                "box": {"x_center": -37, "x_half": 38,
                        "y_center": 53, "y_half": 8,
                        "z_center": 0, "z_half": 8},
                "hit_value_u8": 10,
                "knockback_mode_s8": 0} and
            class1f_player_collision["defender"] == {
                "table_set": "0x11ae02",
                "hurt_table": "0x11ae06",
                "selector_source": "current animation record byte +8",
                "animation_record": "0x0015f278",
                "hurt_selector_u8": 17,
                "hurt_record": "0x11ae8e",
                "box": {"x_center": 1, "x_half": 20,
                        "y_center": 45, "y_half": 46,
                        "z_center": 0, "z_half": 6}} and
            class1f_player_collision["observed_transaction"]
                ["writer_pc"] == "0x01d5ee" and
            class1f_player_collision["observed_transaction"]
                ["damage_s16"] == 10 and
            class1f_player_collision["observed_transaction"]
                ["hitstop_u8"] == 10 and
            class1f_player_collision["observed_transaction"]
                ["attack_hold_first_frame_u16"] == 2751 and
            class1f_player_collision["observed_transaction"]
                ["attack_hold_last_frame_u16"] == 2761 and
            class1f_player_collision["observed_transaction"]
                ["attack_advance_frame_u16"] == 2762,
            "class-0x1f first-segment action fixture incomplete or drifted")
    inner8 = class1f_actions["inner_state_0x08_program"]
    require(inner8["classification"] ==
                "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            inner8["capture_identity"]["byte_identical"] is True and
            inner8["entry_transition"]["writer_pc"] == "0x0610c8" and
            inner8["entry_transition"]["timer_u16"] == 600 and
            inner8["dispatch"]["scheduler_position"] ==
                "type-12 ascending fixed-pool source slot" and
            list(inner8["route_reachable_action_handlers"]) ==
                ["0x00", "0x02", "0x04", "0x06", "0x08", "0x0a",
                 "0x0c", "0x0e", "0x10"] and
            len(inner8["animation_records"]) == 152 and
            all("next_animation_record" in row for row in
                inner8["animation_records"]) and
            next(row for row in inner8["animation_records"]
                 if row["animation_record"] == "0x0012d404")
                ["next_animation_record"] == "0x0012d414" and
            [row["table_index_u8"] for row in
             inner8["movement"]["tables"]] ==
                [4, 11, 12, 14, 15, 18, 19, 23, 25, 27] and
            len(inner8["rng_calls"]) == 13 and
            inner8["action_0x0e_motion"]["phase_2_terminal"]
                ["x_velocity_by_facing_s32_16_16"] == [65536, -65536] and
            inner8["action_0x0e_motion"]["phase_2_terminal"]
                ["y_velocity_s32_16_16"] == 786432 and
            inner8["action_0x0e_motion"]["phase_2_terminal"]
                ["y_acceleration_s32_16_16"] == -38400 and
            inner8["type16_emission"]["observed_source_spawn_frames"] ==
                [3253, 3258, 3263] and
            inner8["type16_emission"]["fixed_frame_spawn_forbidden"] is True and
            inner8["observed_path_program"]["action_0x00"]
                ["captured_rng_call_counts"]["frame_3004_style_match"] == 4 and
            inner8["observed_path_program"]["source_tables"]
                ["field88_by_rng_low_nibble_u8"] ==
                [1, 2, 1, 2, 1, 1, 2, 1, 2, 1, 1, 1, 1, 2, 1, 2] and
            len(inner8["observed_path_program"]["source_tables"]
                ["wander_direction_delta_same_style_u8"]) == 32 and
            len(inner8["observed_path_program"]["source_tables"]
                ["direction_octant_base_u8"]) == 32 and
            inner8["observed_path_program"]["source_tables"]
                ["direction_axis_equal_u8"] == [4, 12, 28, 20] and
            inner8["observed_path_program"]["source_tables"]
                ["direction_octant_base_u8"][0] == 0 and
            inner8["observed_path_program"]["source_tables"]
                ["wander_target_origin"] == {
                    "x_s16": "global+0x0278 camera_x",
                    "z_s16": "global+0x027c camera_z",
                    "z_offset_s16": 48} and
            inner8["observed_path_program"]
                ["wander_group_occupancy_program"]
                ["Coffee_Shop_coverage"]["select_calls"] == 30 and
            inner8["observed_path_program"]
                ["wander_group_occupancy_program"]
                ["Coffee_Shop_coverage"]["occupancy_writes"] == 56 and
            inner8["observed_path_program"]
                ["wander_group_occupancy_program"]
                ["camera_band_thresholds_u16"] == [96, 192, 288, 384] and
            inner8["observed_path_program"]
                ["wander_group_occupancy_program"]
                ["least_populated_branch"]["classification"] ==
                    "NOT_REQUIRED_FOR_COFFEE_SHOP" and
            inner8["observed_path_program"]
                ["wander_group_occupancy_program"]
                ["capture_identity"]["byte_identical"] is True and
            inner8["observed_path_program"]
                ["wander_group_occupancy_program"]
                ["mutation_control"]["baseline"]["direction_u8"] == 26 and
            inner8["observed_path_program"]
                ["wander_group_occupancy_program"]
                ["mutation_control"]["mutant"]["direction_u8"] == 27 and
            inner8["observed_path_program"]["action_0x04"]
                ["captured_terminals"]["frame_3134"] ==
                "field88 zero, RNG bit set, signed timer -1, action 0x10" and
            inner8["observed_path_program"]["action_0x06"]
                ["selector_by_style"] == [
                    {"style85_u8": 0, "selector_u8": 34,
                     "start_animation_record": "0x0012d590"},
                    {"style85_u8": 1, "selector_u8": 35,
                     "start_animation_record": "0x0012d5e4"}] and
            len(inner8["observed_path_program"]["action_0x06"]
                ["Coffee_Shop_observed_runs"]) == 11 and
            inner8["observed_path_program"]["action_0x06"]
                ["mutation_control"]
                ["first_discriminating_source_frame"] == 3242 and
            inner8["observed_path_program"]["action_0x08"]["phase_2"]
                ["Coffee_Shop_control"]["substate_u16"] == "0x0e00" and
            inner8["observed_path_program"]["action_0x10"]
                ["phase_terminal_movement_binding"]
                ["Coffee_Shop_control"]["selector_u8"] == 66 and
            inner8["observed_path_program"]["action_0x10"]
                ["phase_terminal_movement_binding"]
                ["Coffee_Shop_control"]["animation_record"] ==
                    "0x0012ee98" and
            inner8["observed_path_program"]["action_0x04"]
                ["timer_selector_program"]
                ["variant0_bank_by_stage_parameter_u8"][9] == 1 and
            inner8["observed_path_program"]["action_0x04"]
                ["timer_selector_program"]
                ["signed_timer_banks_s8"][1][2] == -1 and
            inner8["observed_path_program"]["action_0x02"]
                ["Coffee_Shop_observed_frames"] == 79 and
            inner8["observed_path_program"]["action_0x02"]
                ["presentation_binding"]["selector_by_style"] == [
                    {"style85_u8": 0, "selector_u8": 0,
                     "start_animation_record": "0x0012e8a8"},
                    {"style85_u8": 1, "selector_u8": 1,
                     "start_animation_record": "0x0012e8ec"}] and
            inner8["observed_path_program"]["action_0x02"]
                ["presentation_binding"]["movement_on_bind"] is False and
            len(inner8["observed_path_program"]["action_0x02"]
                ["Coffee_Shop_observed_runs"]) == 6 and
            inner8["observed_path_program"]["action_0x02"]
                ["mutation_control"]["position_unchanged_on_bind"] is True and
            inner8["movement"]["terrain_tail"]["source_entry"] ==
                "0x0b1baa" and
            inner8["movement"]["terrain_tail"]
                ["Coffee_Shop_reachable_class1f_sync_guard_zero"] is True and
            inner8["movement"]["terrain_tail"]["mutation_control"]
                ["proposed_world_z_without_tail_s16"] == 338 and
            inner8["movement"]["terrain_tail"]["mutation_control"]
                ["resolved_world_z_s16"] == 327 and
            inner8["movement"]["terrain_tail"]["mutation_control"]
                ["omitted_tail_rejected"] is True and
            inner8["observed_path_program"]["action_0x0c"]
                ["classification"] ==
                    "SOURCE_CLOSED_IMPLEMENTATION_FIELDS" and
            inner8["observed_path_program"]["action_0x0c"]
                ["Coffee_Shop_observed_actor_frames"] == 236 and
            inner8["observed_path_program"]["action_0x0c"]
                ["phase_0"]["variant0_plan_by_rng_index_u16"][15] == 14 and
            inner8["observed_path_program"]["action_0x0c"]
                ["phase_0"]["selector_rows"][6]["selector_u8"] == 48 and
            inner8["observed_path_program"]["action_0x0c"]
                ["phase_2"]["timer_row_u8"][29] == 14 and
            len(inner8["observed_path_program"]["action_0x0c"]
                ["phase_2"]["timer_rows_u8"]) == 5 and
            inner8["observed_path_program"]["action_0x0c"]
                ["phase_2"]["timer_rows_u8"][1][29] == 14 and
            inner8["observed_path_program"]["action_0x0c"]
                ["phase_2"]["fixed_observed_stage_guard_forbidden"] is True and
            inner8["observed_path_program"]["action_0x0c"]
                ["collision_damage"]["Coffee_Shop_player_damage"]
                ["damage_s16"] == 15 and
            inner8["observed_path_program"]["action_0x0c"]
                ["phase_exclusive_hit_ko_dispatch_guard"]
                ["Coffee_Shop_negative_control"]["reaction_dispatch"] is False and
            inner8["observed_path_program"]["action_0x0c"]
                ["phase_exclusive_hit_ko_dispatch_guard"]
                ["accepted_reaction_state_pairs"][0] == {
                    "recovery_kind_u16": 1,
                    "outer_states_u16": [0x0202]} and
            inner8["observed_path_program"]["action_0x04"]
                ["complete_dispatch_contract"]["per_update_proximity_first"]
                ["helper"] == "0x041db8" and
            inner8["observed_path_program"]["action_0x04"]
                ["complete_dispatch_contract"]["clear_tail"]
                ["Coffee_Shop_control"]["animation_timer_u16"] == 5 and
            inner8["observed_path_program"]["action_0x10"]
                ["overlap_transition"]["base_writes"]["writer"] ==
                    "0x04130e" and
            inner8["observed_path_program"]["action_0x10"]
                ["overlap_transition"]["style85_nonzero_override"]
                ["selector_u8"] == 36 and
            inner8["observed_path_program"]["action_0x10"]
                ["initializer"]["x_offset_selector_by_rng_low_nibble_u8"] ==
                    [0, 0, 2, 2, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4] and
            inner8["observed_path_program"]["action_0x10"]
                ["initializer"]["x_offsets_s16"] == [96, 112, 208] and
            inner8["observed_path_program"]["action_0x10"]
                ["initializer"]["Coffee_Shop_reachable_phases_u8"] == [0, 6] and
            inner8["observed_path_program"]["action_0x0e"]
                ["captured_selection"]["motion_selector_96_u16"] == 24 and
            inner8["action_0x0e_motion"]["phase_4_arithmetic"][3] ==
                "on landing retain the accumulated y_fp unchanged; do not snap its high word to z_s16" and
            inner8["action_0x0e_motion"]["phase_4_Coffee_Shop_control"]
                ["result_y_fp_s32_16_16"] == "0x013aba00" and
            inner8["action_0x0e_motion"]["phase_8_terminal_writes"] == {
                "source_entry": "0x040e40", "action_u16": 0,
                "wander_cursor_u8": 0, "field95_u8": 0} and
            inner8["route_interaction"]["timeout_return"]["source_entry"] ==
                "0x0610f6" and
            inner8["route_interaction"]["timeout_return"]
                ["source_exit_helper"] == "0x0610d4" and
            inner8["route_interaction"]["timeout_return"]
                ["source_window_sha256"] ==
                "e1e231c72ee8540740c632f54bcb2f960262dfd88f1b657fbce4be1d82b497cf" and
            inner8["route_interaction"]["timeout_return"]["writes"] == {
                "special_latch_ad_u8": 0,
                "inner_timer_u16": 0,
                "outer_state_u16": 0x0200,
                "action_substate_u16": 0,
            } and
            inner8["route_interaction"]["timeout_return"]
                ["coffee_shop_control"]["return_frame_u16"] == 3881 and
            inner8["observed_path_program"]
                ["fixed_frame_or_authored_transition_forbidden"] is True and
            inner8["mutation_control"] == {
                "baseline_inner8_present": True,
                "baseline_type16_spawn_frames": [3253, 3258, 3263],
                "fixed_frame_or_authored_type16_spawn_rejected": True,
                "mutant_inner8_present": False,
                "mutant_type16_spawn_frames": [],
                "suppressed_writer": "0x0610c8",
                "suppressed_writes": 3},
            "class-0x1f inner-state-0x08 fixture incomplete or drifted")
    ids = set()
    families = set()
    required = {"id", "authority_family", "classification", "type", "signed",
                "source", "fixture_path", "transition_guard", "reads", "writes",
                "mutation_control"}
    for item in contract["field_contracts"]:
        require(required <= set(item), f"field metadata missing: {item.get('id')}")
        require(item["id"] not in ids, f"duplicate field: {item['id']}")
        ids.add(item["id"]); families.add(item["authority_family"])
        require(item["classification"] == "SOURCE_CLOSED" and
                isinstance(item["signed"], bool), f"field classification/type drift: {item['id']}")
        require(item["transition_guard"] and item["reads"] and item["writes"] and
                "UNKNOWN" not in item["transition_guard"].upper() and
                "FALLBACK" not in item["transition_guard"].upper(),
                f"vacuous or unknown field contract: {item['id']}")
        src = item["source"]
        key = next((k for k, v in SOURCES.items() if v == src["artifact"]), None)
        require(key is not None and src["evidence_hash"] == digest(ROOT / SOURCES[key]) and
                src["routine_table_or_frame"], f"field provenance drift: {item['id']}")
        require(pointer(source[key], src["json_pointer"]) is not None,
                f"source pointer drift: {item['id']}")
        mutation = item["mutation_control"]
        mkey = next((k for k, v in SOURCES.items() if v == mutation["artifact"]), None)
        require(mkey is not None and pointer(source[mkey], mutation["json_pointer"]) is not None and
                mutation["expected_discriminating_effect"], f"mutation control drift: {item['id']}")
        require(pointer(fixtures, item["fixture_path"]) is not None,
                f"fixture pointer drift: {item['id']}")
    expected_families = set(source["coverage"]["route_segment_authority_matrix"]["authority_families"])
    require(expected_families <= families, "authority family missing from SPEC-02")
    for key, identity in contract["source_artifacts"].items():
        require(identity["artifact"] == SOURCES[key] and
                identity["sha256"] == digest(ROOT / SOURCES[key]),
                f"source artifact drift: {key}")
    require(contract["protected_boundaries"] == {
        "production_runtime_writes": 0, "yaba_runs": 0, "frontend_active": False,
        "user09": "CHANGES_REQUESTED", "physical_saturn": "UNRUN"},
        "protected boundary crossed")
    require(contract["next_card"] == "REIMPLEMENT-13-SOURCE-CLOSED-ROUND1",
            "SPEC-02 successor drift")


def main() -> None:
    contract, fixtures = build_artifacts()
    FIXTURES.write_bytes(canonical(fixtures))
    OUT.write_bytes(canonical(contract))
    print(f"SPEC-02 contract PASS fields={len(contract['field_contracts'])} "
          f"fixtures_sha256={contract['generated_fixtures']['sha256']}")


if __name__ == "__main__":
    main()
