#!/usr/bin/env python3
"""Build and execute the SPEC-01 bounded first-live-encounter contract."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data" / "spec01_first_live_encounter_schema.json"
ORACLE07 = ROOT / "data" / "oracle07_predator_warrior_action_graph_equipment.json"
ORACLE08 = ROOT / "data" / "oracle08_round1_navigation_bounds.json"
ORACLE09 = ROOT / "data" / "oracle09_street_alien_state_facing_presentation.json"
PLAYER_INTERFACE = ROOT / "tests" / "port_v2" / "predator_warrior_action" / "contract.json"
ALIEN_INTERFACE = ROOT / "tests" / "port_v2" / "street_alien_ai" / "contract.json"
LIVE_INTERFACE = ROOT / "tests" / "port_v2" / "integration" / "live_encounter" / "contract.json"
SOURCE_COMBAT = ROOT / "data" / "avsp_source_combat_presentation_contract.json"
SLICE_INTERFACE = ROOT / "src" / "port_v2" / "integration" / "slice" / "slice.c"
OUT = ROOT / "data" / "spec01_first_live_encounter_executable_contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii") + b"\n"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def provenance(path: Path, pointer: str) -> dict[str, str]:
    return {"artifact": path.relative_to(ROOT).as_posix(),
            "sha256": digest(path), "json_pointer_or_symbol": pointer}


def field(field_id: str, family: str, kind: str, signed: bool,
          classification: str, source: dict[str, str], guard: str,
          reads: list[str], writes: list[str], mutation: str) -> dict[str, object]:
    return {
        "id": field_id, "family": family, "type": kind, "signed": signed,
        "classification": classification, "required_for_reimplementation": True,
        "provenance": source, "guard": guard, "reads": reads,
        "writes": writes,
        "mutation_control": {"family": family, "mutation": mutation,
                             "expected_result": "REJECT"},
    }


def project_screen_y(contract: dict, world_z: int, height: int = 0) -> int:
    rule = contract["navigation"]["screen_projection"]
    return (rule["screen_anchor_y"] + rule["world_z_sign"] *
            (world_z - rule["source_anchor_z"]) - height)


def resolve_player_navigation(contract: dict, requested_x: int,
                              requested_z: int) -> tuple[int, int]:
    nav = contract["navigation"]["coffee_shop_player"]
    z = min(max(requested_z, nav["world_z_min"]), nav["world_z_max"])
    maximum_x = nav["world_x_max"]
    if z >= nav["upper_obstacle_guard"]["world_z_at_or_above"]:
        maximum_x = nav["upper_obstacle_guard"]["world_x_max"]
    x = min(max(requested_x, nav["world_x_min"]), maximum_x)
    return x, z


def rng_step(seed: int) -> int:
    high = ((3 * seed) & 0xffff) >> 8
    low = ((seed & 0xff) + high) & 0xff
    return (high << 8) | low


def attack_timer(seed_after: int) -> int:
    return 30 if (seed_after & 0xff) < 0x40 else 120


def clear_allowed(target_ko: bool, target_inactive: bool,
                  timer_elapsed: bool = False,
                  presentation_flag: bool = False) -> bool:
    del timer_elapsed, presentation_flag
    return target_ko and target_inactive


def alien_contact_allowed(contract: dict, action_elapsed: int, dx: int,
                          floor_delta: int) -> bool:
    rule = contract["collision"]["alien_attack_contact"]
    return (action_elapsed in rule["contact_offsets"] and floor_delta == 0 and
            abs(dx) <= rule["maximum_measured_contact_distance_x"])


def combo_dispatch(contract: dict, *, edge: bool, held: bool,
                   startup: bool, recovery: bool, followup_counter: int,
                   completed_step: int) -> int | None:
    combo = contract["player"]["close_combo"]
    if not edge or held or startup:
        return None
    if recovery and followup_counter > 0 and completed_step < combo["step_count"]:
        return completed_step + 1
    return 1


def _contains_forbidden(value: object, tokens: list[str]) -> bool:
    if isinstance(value, str):
        upper = value.upper()
        return any(token in upper for token in tokens)
    if isinstance(value, list):
        return any(_contains_forbidden(item, tokens) for item in value)
    if isinstance(value, dict):
        return any(_contains_forbidden(item, tokens) for item in value.values())
    return False


def build_report() -> dict[str, object]:
    schema = load(SCHEMA)
    o7, o8, o9 = load(ORACLE07), load(ORACLE08), load(ORACLE09)
    player_interface = load(PLAYER_INTERFACE)
    alien_interface = load(ALIEN_INTERFACE)
    live_interface = load(LIVE_INTERFACE)
    source_combat = load(SOURCE_COMBAT)

    require(o7["classification"] == "MEASURED_MAME_SOURCE_BOUNDED_CONTROLLER_CONTRACT",
            "ORACLE-07 not accepted source contract")
    require(o8["classification"] == "MEASURED_MAME_SOURCE_NAVIGATION_AND_BOUNDS_CONTRACT",
            "ORACLE-08 not accepted source contract")
    require(o9["classification"] ==
            "MEASURED_MAME_SOURCE_BOUNDED_ALIEN_STATE_PRESENTATION_CONTRACT",
            "ORACLE-09 not accepted source contract")
    require(live_interface["fidelity"] ==
            "SOURCE_BOUND_WITH_ADAPTED_SINGLE_ALIEN_CLEAR",
            "live encounter adaptation identity drift")

    p7 = lambda pointer: provenance(ORACLE07, pointer)
    p8 = lambda pointer: provenance(ORACLE08, pointer)
    p9 = lambda pointer: provenance(ORACLE09, pointer)
    pplayer = lambda pointer: provenance(PLAYER_INTERFACE, pointer)
    plive = lambda pointer: provenance(LIVE_INTERFACE, pointer)
    pslice = lambda symbol: provenance(SLICE_INTERFACE, symbol)

    fields = [
        field("player.input_edges", "player_action_equipment", "u16", False,
              "SOURCE_BOUND_ACCEPTED", p7("/input_map"),
              "new decoded edges only; held input is not an edge",
              ["input.current_mask", "input.previous_mask"],
              ["player.input_edges"], "replace edge dispatch with level dispatch"),
        field("player.combo_followup_counter", "player_action_equipment", "u8", False,
              "MEASURED", p7("/combo_contract/state_fields/followup_counter"),
              "live only after a completed close step; expires at zero",
              ["player.completed_close_step", "frame_tick"],
              ["player.combo_followup_counter"], "change reset from 30 to 90"),
        field("player.close_selector", "player_action_equipment", "enum_u8", False,
              "SOURCE_BOUND_ACCEPTED", p7("/combo_contract/events"),
              "Button2 edge; advance only inside live follow-up window",
              ["player.input_edges", "player.combo_followup_counter",
               "player.completed_close_step"],
              ["player.close_selector", "player.animation_record",
               "player.assembly"], "cycle selector without an accepted edge"),
        field("player.action_facing", "player_action_equipment", "enum_u8", False,
              "MEASURED", p7("/facing_and_movement"),
              "latched for active action; locomotion updates only after control returns",
              ["player.control_facing", "player.action_state"],
              ["player.action_facing", "render.flip_x"], "flip mid-action"),
        field("player.animation_record", "player_action_equipment", "u32", False,
              "SOURCE_BOUND_ACCEPTED", p7("/presentation_identity/sequences"),
              "selected by active source action and elapsed frame",
              ["player.close_selector", "player.action_elapsed"],
              ["player.animation_record"], "substitute a record from another step"),
        field("player.assembly", "player_action_equipment", "u32", False,
              "SOURCE_BOUND_ACCEPTED", p7("/presentation_identity/sequences"),
              "read only from active animation record +0x04",
              ["player.animation_record"], ["player.assembly"],
              "select assembly independently from animation record"),
        field("player.action_local_equipment_flag", "player_action_equipment", "u8", False,
              "MEASURED", p7("/equipment_contract"),
              "gun/special writers only; never a visible-weapon selector",
              ["player.source_action"], ["player.action_local_equipment_flag"],
              "infer visible weapon from flag"),
        field("player.world_x", "navigation", "s16", True,
              "SOURCE_BOUND_ACCEPTED", p8("/segment_bounds/coffee_shop_lock"),
              "Coffee Shop bounds and obstacle response apply before commit",
              ["input.left", "input.right", "navigation.segment"],
              ["player.world_x"], "widen maximum to 1200"),
        field("player.world_z", "navigation", "s16", True,
              "SOURCE_BOUND_ACCEPTED", p8("/coordinate_contract"),
              "Up increases source world-z; Down decreases it; terrain and lower bound apply",
              ["input.up", "input.down", "navigation.segment"],
              ["player.world_z", "player.world_y"], "invert world-z input signs"),
        field("player.screen_y", "projection", "s16", True,
              "ADAPTED_EXPLICIT_ACCEPTED_INTERFACE", pslice("avsp_port_v2_slice_motion_step"),
              "project source world-z with negative screen sign; never copy world-z",
              ["player.world_z", "player.height"], ["render.player_screen_y"],
              "change world-z projection sign to positive"),
        field("alien.target", "alien_state_presentation", "pointer_u16", False,
              "MEASURED", p9("/target/one_player_target"),
              "one active P1 target only in this bounded contract",
              ["player.active", "player.ko"], ["alien.target"],
              "retarget to another slot"),
        field("alien.state_action", "alien_state_presentation", "enum_u16", False,
              "SOURCE_BOUND_ACCEPTED", p9("/bounded_state_contract"),
              "authored route state; no generic behavior-tree substitution",
              ["alien.route_tick", "alien.rng_seed", "alien.crossing_latch"],
              ["alien.state", "alien.inner", "alien.action"],
              "replace authored approach with generic face-target"),
        field("alien.facing", "alien_state_presentation", "enum_u8", False,
              "MEASURED", p9("/bounded_state_contract/right_to_left_crossing_0x1a00"),
              "written with source state; action 0x1600 remains facing 1 on opening route",
              ["alien.state", "alien.action"], ["alien.facing", "render.flip_x"],
              "face target every frame"),
        field("alien.animation_record", "alien_state_presentation", "u32", False,
              "SOURCE_BOUND_ACCEPTED", p9("/bounded_state_contract"),
              "state-owned record and elapsed frame",
              ["alien.state", "alien.action", "alien.action_elapsed"],
              ["alien.animation_record"], "use stale record after state change"),
        field("alien.assembly", "alien_state_presentation", "u32", False,
              "SOURCE_BOUND_ACCEPTED", p9("/presentation_identity"),
              "read from current animation record +0x04 in same semantic tick",
              ["alien.animation_record"], ["alien.assembly"],
              "randomly substitute staff or another actor-family assembly"),
        field("alien.rng_seed", "alien_state_presentation", "u16", False,
              "MEASURED", p9("/scheduler_rng_hit_ko/rng_recurrence"),
              "consume exactly at measured source selection",
              ["alien.rng_seed"], ["alien.rng_seed", "alien.attack_timer"],
              "replace recurrence or consume on render"),
        field("alien.health_state", "alien_state_presentation", "s16", True,
              "SOURCE_BOUND_ACCEPTED", p9("/scheduler_rng_hit_ko/hit_recovery_ko_removal"),
              "collision/damage authority only; presentation cannot change health or removal",
              ["collision.hit_value", "alien.health"],
              ["alien.health", "alien.state", "alien.removed"],
              "clear actor from animation completion"),
        field("collision.player_attack_selector", "collision_damage", "u8", False,
              "SOURCE_BOUND_ACCEPTED", p7("/presentation_identity/close_contact_source_bound_identity"),
              "selector belongs to current player animation/action state",
              ["player.animation_record", "player.close_selector"],
              ["collision.attack_box", "collision.hit_value"],
              "use selector from a different presentation"),
        field("collision.alien_hurt_selector", "collision_damage", "u8", False,
              "SOURCE_BOUND_ACCEPTED", p7("/presentation_identity/close_contact_source_bound_identity"),
              "source class-0x1F hurt selector 1 with table 0x130ac8",
              ["alien.animation_record"], ["collision.hurt_box"],
              "shrink hurt box independently"),
        field("collision.damage", "collision_damage", "s16", True,
              "SOURCE_BOUND_ACCEPTED", p7("/presentation_identity/close_contact_source_bound_identity"),
              "apply only on source box overlap and clear per-attacker latch",
              ["collision.attack_box", "collision.hurt_box", "collision.latch"],
              ["alien.health", "collision.latch"],
              "apply damage without overlap"),
        field("encounter.clear", "encounter_authority", "bool", False,
              "ADAPTED_EXPLICIT_ACCEPTED_INTERFACE", plive("/clear_authority"),
              "target KO observed and target inactive; timer and presentation are ignored",
              ["encounter.target_ko", "alien.removed"],
              ["encounter.clear", "route.unlocked"], "allow timer-only clear"),
        field("camera.lock", "encounter_authority", "s16", True,
              "SOURCE_BOUND_ACCEPTED", p8("/camera_and_route/coffee_shop_lock"),
              "retain accepted camera lock until adapted clear authority succeeds",
              ["encounter.clear", "player.world_x"], ["camera.world_x"],
              "unlock from unsupported player x"),
        field("diagnostic.alien_state", "diagnostic_observability", "enum_u16", False,
              "ADAPTED_EXPLICIT_ACCEPTED_INTERFACE", plive("/interface"),
              "sample after gameplay state update in same frame",
              ["alien.state", "alien.inner", "alien.health"],
              ["diagnostic.alien_state", "diagnostic.alien_health"],
              "leave overlay state stale"),
        field("diagnostic.presentation_identity", "diagnostic_observability", "sha256", False,
              "SOURCE_BOUND_ACCEPTED", p9("/presentation_identity"),
              "state/facing/record/assembly/object/tile identity sampled together",
              ["alien.state", "alien.facing", "alien.animation_record", "alien.assembly"],
              ["diagnostic.presentation_identity"],
              "report animation from a different state tick"),
    ]

    attacks = []
    sequences = o7["presentation_identity"]["sequences"]
    identities = o7["presentation_identity"]["close_contact_source_bound_identity"]
    for event, identity in zip(o7["combo_contract"]["events"], identities):
        key = f"close_{event['step']}"
        attacks.append({
            "step": event["step"], "input_frame": event["input_frame"],
            "action_start_frame": event["action_start_frame"],
            "contact_frame": event["contact_frame"], "return_frame": event["return_frame"],
            "attack_selector": event["attack_selector"],
            "presentation": copy.deepcopy(sequences[key]),
            "contact_identity": copy.deepcopy(identity),
        })

    o8_lock = o8["segment_bounds"]["coffee_shop_lock"]
    approach = o9["bounded_state_contract"]["authored_approach_0x1600"]
    alien_attack = o9["bounded_state_contract"]["rng_attack_0x1800"]
    crossing = o9["bounded_state_contract"]["right_to_left_crossing_0x1a00"]
    above = o9["bounded_state_contract"]["above_lane_reposition_inner_8"]
    contact = o9["scheduler_rng_hit_ko"]["hit_recovery_ko_removal"]

    report: dict[str, object] = {
        "schema": 1,
        "task": "SPEC-01-FIRST-LIVE-ENCOUNTER-EXECUTABLE-CONTRACT",
        "classification": "EXECUTABLE_SOURCE_BOUND_BOUNDED_ENCOUNTER_WITH_EXPLICIT_ADAPTATIONS",
        "scope": "one-player Predator Warrior versus one type-12 class-0x1F actor in the Coffee Shop live diagnostic; not generic AI, complete Round 1, multiplayer, frontend, or physical Saturn",
        "provenance": {
            "schema_sha256": digest(SCHEMA),
            "oracle07_sha256": digest(ORACLE07),
            "oracle08_sha256": digest(ORACLE08),
            "oracle09_sha256": digest(ORACLE09),
            "player_interface_sha256": digest(PLAYER_INTERFACE),
            "alien_interface_sha256": digest(ALIEN_INTERFACE),
            "live_interface_sha256": digest(LIVE_INTERFACE),
            "source_combat_sha256": digest(SOURCE_COMBAT),
            "slice_projection_interface_sha256": digest(SLICE_INTERFACE),
        },
        "required_behavior_unknown_count": 0,
        "field_contracts": fields,
        "player": {
            "input_map": copy.deepcopy(o7["input_map"]),
            "movement": {"direction_latency_frames": player_interface["direction_latency_frames"],
                "world_differentials_per_20_ticks": player_interface["movement_differentials"],
                "world_z_rule": "Up positive; Down negative; projection owns screen inversion"},
            "close_combo": {"step_count": 4, "followup_counter_frames": 30,
                "dispatch": "new Button2 edge only",
                "held": "no auto-repeat", "startup_repeat": "buffered no dispatch",
                "live_recovery_edge": "advance one step", "expired_edge": "restart step 1",
                "automatic_selector_cycle": False, "attacks": attacks},
            "facing": {"control": "horizontal input updates source facing",
                "active_action": "latched", "render_sign": {"0": -1, "1": 1}},
            "equipment": {"action_local_flag_offset": "0xad",
                "visible_weapon_authority": "animation_record_and_assembly_only",
                "visible_weapon_inference_from_flag": False,
                "independent_assembly_selection": False},
        },
        "navigation": {
            "coffee_shop_player": {
                "bound_x": o8_lock["bound_x"],
                "world_x_min": o8_lock["observed_x"][0],
                "world_x_max": o8_lock["observed_x"][1],
                "world_z_min": o8_lock["observed_lower_z"],
                "world_z_max": o8["terrain_constraint"]["accepted_max_world_z"],
                "shape": "EXPLICIT_ADAPTED_ENVELOPE_FROM_MEASURED_UPPER_AND_LOWER_ROUTES",
                "upper_obstacle_guard": {"world_z_at_or_above": 320,
                    "world_x_max": o8["walkable_shape"]["upper_middle_samples"]["rightmost_x"],
                    "obstacle_slot": o8["obstacle"]["actor_slot"],
                    "obstacle_world": o8["obstacle"]["world_position"],
                    "obstacle_hurt_box": o8["obstacle"]["hurt_box"]},
                "lower_route_witness": o8["walkable_shape"]["lower_sample"],
                "enemy_uses_player_clamp": False,
            },
            "screen_projection": {"classification": "ADAPTED_EXPLICIT_ACCEPTED_INTERFACE",
                "source_anchor_z": 319, "screen_anchor_y": 178,
                "world_z_sign": -1,
                "formula": "screen_y=178-(world_z-319)-height",
                "up_input_screen_delta_sign": -1,
                "down_input_screen_delta_sign": 1},
        },
        "alien": {
            "identity": copy.deepcopy(o9["target"]),
            "scheduler": copy.deepcopy(o9["scheduler_rng_hit_ko"]["scheduler"]),
            "spawn": copy.deepcopy(o9["bounded_state_contract"]["spawn"]),
            "authored_approach": {"action": "0x1600", "facing": 1,
                "frames": 38, "displacement": {"x": 111, "world_z": -23},
                "presentation_cycle": copy.deepcopy(approach["presentation_cycle"]),
                "generic_face_target": False},
            "rng_attack": {"action": "0x1800", "facing": 1,
                "seed_before": alien_attack["rng"]["seed_before"],
                "seed_after": alien_attack["rng"]["seed_after"],
                "timer": alien_attack["first_sample"]["timer"],
                "fixed_seed_timer": alien_attack["fixed_rng_control"]["result_timer"],
                "contact_offsets": alien_attack["contact_offsets"],
                "damage_each": alien_attack["damage_each_native_health_units"],
                "presentation_cycle": copy.deepcopy(alien_attack["presentation_cycle"]),
                "player_input_cancels_or_rerolls": False},
            "right_to_left_crossing": {"classification": "MEASURED_BOUNDED_DELAYED_ROUTE_RESPONSE",
                "source_cross_after_frame": crossing["player_cross_write_after_frame"],
                "source_response_frame": crossing["source_write_frame"] + 1,
                **copy.deepcopy(crossing["same_tick_identity"]),
                "immediate_universal_flip": False},
            "above_lane_reposition": {"classification": "MEASURED_BOUNDED_ROUTE_RESPONSE",
                **copy.deepcopy(above["same_tick_identity"])},
            "hit_ko_removal": copy.deepcopy(contact),
            "rendered_hit_identities": copy.deepcopy(
                o9["presentation_identity"]["rendered_source_bound_hit_identities"]),
            "state_owned_presentation": True,
            "generic_ai_fallback": False,
        },
        "collision": {
            "player_attacks": [{"step": item["step"],
                "attack_selector": item["attack_selector"],
                "collision": copy.deepcopy(item["contact_identity"]["collision"]),
                "object_identity_sha256": item["contact_identity"]["object_identity_sha256"],
                "tile_identity_sha256": item["contact_identity"]["tile_identity_sha256"]}
                for item in attacks],
            "alien_attack_contact": {"classification": "MEASURED_BOUNDED_CONTACT_ENVELOPE",
                "contact_offsets": alien_attack["contact_offsets"],
                "damage_native_units": alien_attack["damage_each_native_health_units"],
                "maximum_measured_contact_distance_x": 68,
                "required_floor_delta": 0,
                "guessed_legacy_distance_x_160_forbidden": True,
                "scope": "bounded action 0x1800 contact witness; not a generic alien collision volume"},
            "already_hit_latch_required": True,
            "presentation_owns_damage": False,
        },
        "encounter": {
            "fidelity": live_interface["fidelity"],
            "entry": "real player movement crosses bounded encounter entry",
            "active": "one target class-0x1F actor active",
            "clear": {"requires_target_ko": True, "requires_target_inactive": True,
                "timer_can_clear": False, "presentation_can_clear": False},
            "camera": {"retain_approved_movement": True,
                "coffee_shop_source_lock_x": o8["camera_and_route"]["coffee_shop_lock"]["scroll2_x"],
                "unlock_after_adapted_clear_only": True,
                "guessed_source_unlock_guard": False},
            "frontend_activation": False,
        },
        "diagnostics": {
            "same_tick_fields": ["player.state", "player.selector", "player.facing",
                "player.animation_record", "player.assembly", "player.world_x",
                "player.world_z", "player.screen_y", "alien.state", "alien.inner",
                "alien.action", "alien.health", "alien.facing",
                "alien.animation_record", "alien.assembly", "collision.contact",
                "collision.damage", "encounter.state", "camera.world_x"],
            "alien_overlay_updates_on_state_or_health_change": True,
            "stale_state_or_presentation_allowed": False,
        },
        "reference_fixtures": {
            "projection": [{"world_z": 319, "height": 0, "screen_y": 178},
                {"world_z": 327, "height": 0, "screen_y": 170},
                {"world_z": 224, "height": 0, "screen_y": 273},
                {"world_z": 319, "height": 15, "screen_y": 163}],
            "navigation": [{"request": [840, 320], "resolved": [864, 320]},
                {"request": [1184, 320], "resolved": [1091, 320]},
                {"request": [1184, 224], "resolved": [1184, 224]},
                {"request": [1200, 400], "resolved": [1091, 327]}],
            "combo": [{"edge": True, "held": False, "startup": False,
                "recovery": False, "counter": 0, "completed": 0, "result": 1},
                {"edge": False, "held": True, "startup": False,
                 "recovery": False, "counter": 29, "completed": 1, "result": None},
                {"edge": True, "held": False, "startup": True,
                 "recovery": False, "counter": 29, "completed": 1, "result": None},
                {"edge": True, "held": False, "startup": False,
                 "recovery": True, "counter": 28, "completed": 1, "result": 2},
                {"edge": True, "held": False, "startup": False,
                 "recovery": True, "counter": 0, "completed": 1, "result": 1}],
            "rng": [{"before": 0x7301, "after": 0x595a, "timer": 120},
                {"before": 0x0001, "after": 0x0001, "timer": 30}],
            "alien_contact": [{"elapsed": 48, "dx": -63, "floor": 0, "result": True},
                {"elapsed": 119, "dx": -68, "floor": 0, "result": True},
                {"elapsed": 48, "dx": -69, "floor": 0, "result": False},
                {"elapsed": 47, "dx": -63, "floor": 0, "result": False},
                {"elapsed": 48, "dx": -63, "floor": 1, "result": False}],
            "clear": [{"ko": False, "inactive": False, "timer": True,
                "presentation": True, "result": False},
                {"ko": True, "inactive": False, "timer": True,
                 "presentation": True, "result": False},
                {"ko": True, "inactive": True, "timer": False,
                 "presentation": False, "result": True}],
        },
        "deferred_out_of_scope": ["generic alien AI and range model",
            "other enemy archetypes", "multiplayer targeting and scaling",
            "later Round 1 terrain and generalized source camera unlock guard",
            "frontend and complete game route", "physical Saturn behavior"],
        "saturn_emulator": "UNRUN",
        "physical_saturn": "UNRUN",
    }
    validate(report, schema)
    execute_fixtures(report)
    mutation_self_test(report, schema)
    return report


def validate(report: dict[str, object], schema: dict | None = None) -> None:
    if schema is None:
        schema = load(SCHEMA)
    require(report["schema"] == schema["contract_schema"], "SPEC-01 schema drift")
    for key in schema["required_top_level"]:
        require(key in report, f"SPEC-01 missing top-level field: {key}")
    require(report["classification"] ==
            "EXECUTABLE_SOURCE_BOUND_BOUNDED_ENCOUNTER_WITH_EXPLICIT_ADAPTATIONS",
            "SPEC-01 classification drift")
    require(report["required_behavior_unknown_count"] == 0,
            "SPEC-01 required behavior is unresolved")
    require(report["saturn_emulator"] == "UNRUN" and
            report["physical_saturn"] == "UNRUN", "Saturn status overclaim")

    allowed_types = set(schema["allowed_types"])
    allowed_classes = set(schema["allowed_required_classifications"])
    required_metadata = set(schema["required_field_metadata"])
    families = set()
    identifiers = set()
    for item in report["field_contracts"]:
        require(required_metadata <= set(item), f"field metadata missing: {item.get('id')}")
        require(item["id"] not in identifiers, f"duplicate field id: {item['id']}")
        identifiers.add(item["id"])
        require(item["type"] in allowed_types, f"invalid field type: {item['id']}")
        require(isinstance(item["signed"], bool), f"signedness missing: {item['id']}")
        require(item["classification"] in allowed_classes,
                f"required field classification invalid: {item['id']}")
        require(item["required_for_reimplementation"] is True,
                f"field not required: {item['id']}")
        require(item["guard"] and item["reads"] and item["writes"],
                f"guard/read/write inventory vacuous: {item['id']}")
        source = item["provenance"]
        require(set(source) == {"artifact", "sha256", "json_pointer_or_symbol"} and
                len(source["sha256"]) == 64,
                f"field provenance invalid: {item['id']}")
        mutation = item["mutation_control"]
        require(mutation["family"] == item["family"] and mutation["mutation"] and
                mutation["expected_result"] == "REJECT",
                f"field mutation control invalid: {item['id']}")
        require(not _contains_forbidden(item, schema["unknown_tokens_forbidden_in_required_fields"]),
                f"required field contains forbidden unknown/fallback token: {item['id']}")
        families.add(item["family"])
    require(families == set(schema["required_mutation_families"]),
            "field-family mutation coverage drift")

    require(report["player"]["close_combo"]["automatic_selector_cycle"] is False,
            "automatic player selector cycle admitted")
    require([item["attack_selector"] for item in
             report["player"]["close_combo"]["attacks"]] == [1, 2, 3, 4],
            "player selector order drift")
    require(report["player"]["equipment"]["visible_weapon_inference_from_flag"] is False and
            report["player"]["equipment"]["independent_assembly_selection"] is False,
            "disconnected player equipment/presentation admitted")
    nav = report["navigation"]
    require(nav["screen_projection"]["world_z_sign"] == -1 and
            nav["screen_projection"]["up_input_screen_delta_sign"] == -1,
            "screen projection inversion drift")
    require(nav["coffee_shop_player"]["world_x_min"] == 864 and
            nav["coffee_shop_player"]["world_x_max"] == 1184 and
            nav["coffee_shop_player"]["upper_obstacle_guard"]["world_x_max"] == 1091 and
            nav["coffee_shop_player"]["enemy_uses_player_clamp"] is False,
            "navigation authority drift")
    alien = report["alien"]
    require(alien["authored_approach"]["generic_face_target"] is False and
            alien["right_to_left_crossing"]["facing"] == 0 and
            alien["right_to_left_crossing"]["animation_record"] == "0x12d5e4" and
            alien["right_to_left_crossing"]["assembly"] == "0x12fae8" and
            alien["state_owned_presentation"] is True and
            alien["generic_ai_fallback"] is False,
            "alien state/facing/presentation drift")
    require([item["animation_record"] for item in
             alien["rng_attack"]["presentation_cycle"]] ==
            ["0x12e8ec", "0x12e8fc", "0x12e90c", "0x12e91c"],
            "alien attack presentation drift")
    require([item["assembly"] for item in
             alien["rng_attack"]["presentation_cycle"]] ==
            ["0x12f5de", "0x12fa0c", "0x12fa2a", "0x12fa0c"],
            "alien attack assembly drift")
    collision = report["collision"]
    require(collision["player_attacks"][0]["collision"]["enemy_table_set"] ==
            "0x130ac8" and
            collision["alien_attack_contact"]["maximum_measured_contact_distance_x"] == 68 and
            collision["alien_attack_contact"]["guessed_legacy_distance_x_160_forbidden"] is True and
            collision["presentation_owns_damage"] is False,
            "collision/damage authority drift")
    clear = report["encounter"]["clear"]
    require(clear == {"requires_target_ko": True, "requires_target_inactive": True,
                      "timer_can_clear": False, "presentation_can_clear": False},
            "encounter clear authority drift")
    require(report["encounter"]["frontend_activation"] is False,
            "frontend activated by SPEC-01")
    require(report["diagnostics"]["alien_overlay_updates_on_state_or_health_change"] is True and
            report["diagnostics"]["stale_state_or_presentation_allowed"] is False and
            "alien.assembly" in report["diagnostics"]["same_tick_fields"],
            "diagnostic same-tick observability drift")
    for key, value in report["provenance"].items():
        require(key.endswith("sha256") and len(value) == 64 and
                all(ch in "0123456789abcdef" for ch in value),
                f"SPEC-01 provenance drift: {key}")


def execute_fixtures(report: dict[str, object]) -> None:
    fixtures = report["reference_fixtures"]
    for item in fixtures["projection"]:
        require(project_screen_y(report, item["world_z"], item["height"]) ==
                item["screen_y"], "projection fixture failed")
    for item in fixtures["navigation"]:
        require(resolve_player_navigation(report, *item["request"]) ==
                tuple(item["resolved"]), "navigation fixture failed")
    for item in fixtures["combo"]:
        require(combo_dispatch(report, edge=item["edge"], held=item["held"],
                               startup=item["startup"], recovery=item["recovery"],
                               followup_counter=item["counter"],
                               completed_step=item["completed"]) == item["result"],
                "combo fixture failed")
    for item in fixtures["rng"]:
        after = rng_step(item["before"])
        require(after == item["after"] and attack_timer(after) == item["timer"],
                "RNG fixture failed")
    for item in fixtures["alien_contact"]:
        require(alien_contact_allowed(report, item["elapsed"], item["dx"],
                                      item["floor"]) == item["result"],
                "alien contact fixture failed")
    for item in fixtures["clear"]:
        require(clear_allowed(item["ko"], item["inactive"], item["timer"],
                              item["presentation"]) == item["result"],
                "clear fixture failed")


def mutation_self_test(report: dict[str, object], schema: dict | None = None) -> None:
    if schema is None:
        schema = load(SCHEMA)
    mutations = []
    changed = copy.deepcopy(report)
    changed["field_contracts"][0]["writes"] = []
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["field_contracts"][1]["classification"] = "UNKNOWN"
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["player"]["close_combo"]["automatic_selector_cycle"] = True
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["navigation"]["screen_projection"]["world_z_sign"] = 1
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["navigation"]["coffee_shop_player"]["upper_obstacle_guard"]["world_x_max"] = 1184
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["alien"]["right_to_left_crossing"]["facing"] = 1
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["alien"]["rng_attack"]["presentation_cycle"][0]["assembly"] = "0x12fa0c"
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["collision"]["alien_attack_contact"]["maximum_measured_contact_distance_x"] = 160
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["encounter"]["clear"]["timer_can_clear"] = True
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["diagnostics"]["same_tick_fields"].remove("alien.assembly")
    mutations.append(changed)
    changed = copy.deepcopy(report)
    changed["physical_saturn"] = "PASS"
    mutations.append(changed)
    for index, mutant in enumerate(mutations):
        try:
            validate(mutant, schema)
            execute_fixtures(mutant)
        except ValueError:
            continue
        raise ValueError(f"SPEC-01 mutation {index} unexpectedly passed")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print(f"SPEC-01 PASS {OUT.relative_to(ROOT)} sha256={digest(OUT)}")


if __name__ == "__main__":
    main()
