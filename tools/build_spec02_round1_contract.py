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
        f("player.weapon_projectile_resources", "predator-warrior-player-authority", "state_record", True,
          "player", "/weapon_projectile_resource", "0x021eac Button1 weapon body and record-type-4 projectile allocation",
          "/authority_data/player/weapon_projectile_resource", "Button1/B1+B2 source guards own allocation, resource debit/recharge, collision, removal, and presentation continuity",
          ["input.new_edges:u16", "player.resource:s16", "target.pointer:u32"], ["player.state:u16", "player.resource:s16", "projectile.record", "player.animation:u32"],
          "/weapon_projectile_resource/counterfactuals", "projectile, target, or resource suppression changes the causal route"),
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
          "navigation", "/global_bounds", "0x01b000 bounds and 0x0b1baa terrain resolver",
          "/authority_data/navigation", "current route bounds and terrain record constrain source world x/z before screen projection",
          ["player.x:s16", "player.z:s16", "route.bound_x:s16", "route.bound_z:s16"], ["player.x:s16", "player.y:s16", "player.z:s16"],
          "/counterfactuals", "directional or navigation-body mutation changes the completing route"),
        f("navigation.obstacle_collision", "round1-navigation-terrain-camera", "collision_table", True,
          "navigation", "/obstacle_response", "0x01d930 minimum-penetration obstacle response",
          "/authority_data/navigation/obstacle_response", "current actor and obstacle boxes overlap before minimum-penetration resolution",
          ["player.box", "obstacle.box", "player.position:s16"], ["player.position:s16"],
          "/counterfactuals/oracle08_directional_and_obstacle_controls", "obstacle removal discriminates the measured nonrectangular route"),
        f("camera.route_lock_unlock", "round1-navigation-terrain-camera", "route_table", True,
          "navigation", "/camera", "0x0b0706 camera target writer and 19 source lock/unlock runs",
          "/authority_data/navigation/camera", "route controller guard owns target/lock transition; player x or a fixed frame alone cannot unlock",
          ["route.state:s16", "camera.controller", "player.position:s16"], ["camera.target:s16", "camera.position:s16"],
          "/counterfactuals/oracle11_directional_perturbation", "completing perturbation changes camera/navigation timing"),
        f("enemy.state_ai", "round1-enemy-archetypes", "actor_state_table", True,
          "enemies", "/archetypes", "type-12 dispatch table 0x01b9b6 and four required source routines",
          "/authority_data/enemies/archetypes", "signed class dispatch and current state/substate select the recovered enemy body",
          ["enemy.class:s8", "enemy.state:u16", "enemy.substate:u16", "player.pointer:u32"], ["enemy.state:u16", "enemy.substate:u16", "enemy.position:s16", "enemy.facing:u8"],
          "/archetypes/0/counterfactuals", "class removal or offense suppression changes the source route"),
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
                          "player_side_contract": copy.deepcopy(source["auxiliary"]["player_side_contract"]),
                          "navigation_body_geometry_contract": copy.deepcopy(source["auxiliary"]["navigation_body_geometry_contract"])},
            "route": {key: copy.deepcopy(source["route"][key]) for key in
                      ("route_entry", "data_contract", "segment_bindings",
                       "route_state_edges", "enemy_spawns")},
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
