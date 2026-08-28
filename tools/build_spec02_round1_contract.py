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
          "enemies", "/archetypes/3/first_segment_action_execution_contract/inner_state_0x08_program", "0x061096 transition, 0x0610f6/0x040bbe inner dispatch, 0x016644 movement, 0x0411c4 motion, and 0x0413d2 type-16 emission",
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
        f("auxiliary.coffee_shop_class47_presentation", "pickups-equipment-weapons-projectiles-hazards-destructibles", "guarded_presentation_actor_program", True,
          "auxiliary", "/first_segment_dependencies/class_0x47_type24_class02_child_presentation", "0x06b61a class-0x02 caller, 0x08eb1c four-child allocator and 0x08eb86 class-0x47 state dispatch",
          "/authority_data/auxiliary/first_segment_dependencies/class_0x47_type24_class02_child_presentation", "class-0x02 state 0x0400 allocates four source-owned presentation children; each consumes seven RNG calls and moves until the dual unsigned landing guard releases it",
          ["owner.state:u16", "owner.position:s16", "owner.direction:u8", "rng.seed:u16", "type24.free_count:u8", "frame.parity:u8"], ["type24.child[4]", "child.position:s32", "child.animation:u32", "rng.seed:u16", "type24.free_count:u8"],
          "/first_segment_dependencies/class_0x47_type24_class02_child_presentation/mutation_controls", "spawn, RNG, selector, motion, direction, terminal-guard or release mutation changes the captured class-0x47 population and trajectory"),
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
        item["classification"] = (
            "NATIVE_IMPLEMENTED" if class1f_health_write(item) and
            item["writer_pc"] in {"0x0605aa", "0x0172ba", "0x01d590",
                                  "0x01d598"}
            else "BLOCKED_MISSING_SPEC")

    route_edges = []
    for item in source["route"]["route_state_edges"]:
        if item["write_frame"] > 5566:
            continue
        edge = copy.deepcopy(item)
        edge["classification"] = (
            "NATIVE_IMPLEMENTED" if edge["write_frame"] == 2237 else
            "BLOCKED_MISSING_SPEC")
        route_edges.append(edge)

    loads = []
    for item in source["loads"]["boundaries"]:
        if int(item["visible_boundary_frame"]) > 5566:
            continue
        boundary = copy.deepcopy(item)
        boundary["classification"] = "BLOCKED_MISSING_SPEC"
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
             "collision/damage/HIT/KO/exit binding is not yet present in the "
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
             "projectile damage, signed KO clamp, HIT/KO, and fixed-pool release",
         "exact_blocker": "player health and non-class-0x1f health writers "
             "remain without a complete native Coffee Shop scene differential"},
        {"id": "coffee-shop-audio",
         "classification": "BLOCKED_MISSING_SPEC",
         "source_contract": "coffee_shop.audio_events"},
        {"id": "coffee-shop-exit-loads",
         "classification": "BLOCKED_MISSING_SPEC",
         "source_contract": "authority_data.loading.boundaries"},
        {"id": "coffee-shop-encounter-clear-and-exit",
         "classification": "BLOCKED_MISSING_SPEC",
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
    fixtures = {
        "schema": "spec02-round1-generated-fixtures-v1",
        "task": "SPEC-02-ROUND1-EXECUTABLE-CONTRACT",
        "classification": "GENERATED_ONLY_FROM_ACCEPTED_ORACLE_AND_PORT_V2",
        "authority_data": {
            "player": {key: copy.deepcopy(player[key]) for key in (
                "source_identity", "locomotion_neutral_facing",
                "route_reachable_melee_actions", "normal_jump_air_landing",
                "directional_airborne_interruption", "weapon_projectile_resource",
                "hit_ko_failure_continue_respawn",
                "route_pickup_resource_audio_load_ownership",
                "player_origin_gameplay_audio")},
            "scheduler": {key: copy.deepcopy(source["scheduler"][key]) for key in
                          ("source_identity", "frame_scheduler", "pools")},
            "navigation": {key: copy.deepcopy(source["navigation"][key]) for key in
                           ("coordinate_contract", "global_bounds", "terrain_resolver",
                            "navigation_bodies", "obstacle_response", "camera")},
            "enemies": {"scheduler": copy.deepcopy(source["enemies"]["scheduler"]),
                        "archetypes": copy.deepcopy(source["enemies"]["archetypes"])},
            "auxiliary": {"archetypes": copy.deepcopy(source["auxiliary"]["archetypes"]),
                          "first_segment_dependencies": copy.deepcopy(source["auxiliary"]["first_segment_dependencies"]),
                          "coffee_shop_type36_presentation": copy.deepcopy(source["auxiliary"]["coffee_shop_type36_presentation"]),
                          "coffee_shop_scene_component_identities": copy.deepcopy(source["auxiliary"]["coffee_shop_scene_component_identities"]),
                          "player_side_contract": copy.deepcopy(source["auxiliary"]["player_side_contract"]),
                          "navigation_body_geometry_contract": copy.deepcopy(source["auxiliary"]["navigation_body_geometry_contract"])},
            "route": {key: copy.deepcopy(source["route"][key]) for key in
                      ("route_entry", "first_entry_body", "data_contract", "segment_bindings",
                       "route_state_edges", "enemy_spawns",
                       "first_segment_recurring_spawn")},
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
    require(all(address in class1f_records and
                (class1f_records[address]["assembly"],
                 class1f_records[address]["hurt_selector"],
                 class1f_records[address]["attack_selector"]) == fields
                for address, fields in expected_hit_ko.items()) and
            class1f["presentation_and_collision"]["accepted_hit_ko_records"]
                ["fixed_frame_presentation_forbidden"] is True,
            "class-0x1f HIT/KO presentation fixture incomplete or drifted")
    class1f_actions = class1f["first_segment_action_execution_contract"]
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
                "route_exit_unchanged": True},
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
                ["0x00", "0x04", "0x06", "0x08", "0x0a", "0x0e", "0x10"] and
            len(inner8["animation_records"]) == 54 and
            all("next_animation_record" in row for row in
                inner8["animation_records"]) and
            inner8["animation_records"][0]
                ["next_animation_record"] == "0x0012d414" and
            [row["table_index_u8"] for row in
             inner8["movement"]["tables"]] ==
                [4, 11, 12, 15, 18, 19, 23, 25] and
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
                ["direction_axis_equal_u8"] == [59, 156, 89, 84] and
            inner8["observed_path_program"]["source_tables"]
                ["direction_octant_base_u8"][0] == 220 and
            inner8["observed_path_program"]["action_0x04"]
                ["captured_terminals"]["frame_3134"] ==
                "field88 zero, RNG bit set, source table zero, action 0x10" and
            inner8["observed_path_program"]["action_0x10"]
                ["overlap_transition"]["writer"] == "0x04130e" and
            inner8["observed_path_program"]["action_0x0e"]
                ["captured_selection"]["motion_selector_96_u16"] == 24 and
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
