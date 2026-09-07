"""Negative test: the tile generator must refuse an over-budget archive.

Proves tools/gen_avsp_gfx_tiles.py's budget guard actually guards: a
--scope round1 archive must be REFUSED against the runtime's real
AVSP_TILE_REGION_BYTES carve (parsed
live from main.c, never hardcoded here so this test cannot drift out of
sync with the runtime). Also proves the on-disk archive and manifest are
left untouched by a refused run, and that --scope street still succeeds
and fits.

Requires the private captures and program image; skips cleanly without
them (matching every other test in this suite that depends on private
inputs).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "gen_avsp_gfx_tiles.py"
ARCHIVE = ROOT / "build" / "avsp_cd" / "SPR4" / "TILES.BIN"
COMBAT_OVERLAY = ROOT / "build" / "avsp_cd" / "SPR4" / "COMBAT.BIN"
MANIFEST = ROOT / "data" / "avsp_gfx_tiles.json"
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "enemy_actions"


def button3_presentation_union_is_complete(presentations, fixture):
    sequences = fixture["authority_data"]["player"][
        "directional_airborne_interruption"]["directional_actions"][
            "implementation_contract"]["presentation_selector_sequences"]
    expected = {
        (int(record["assembly"], 16), facing)
        for sequence in sequences.values()
        for record in sequence
        for facing in (0, 1)
    }
    actual = {
        (item["assembly"], item["facing"])
        for item in presentations
        if item["kind"] == "player-button3"
    }
    return actual == expected


def button3_cleanup_union_is_complete(presentations, fixture):
    release = fixture["authority_data"]["player"][
        "locomotion_neutral_facing"]["release_transition"]["presentation"]
    expected = {
        (int(record["assembly"], 16), facing)
        for record in release
        if record["animation_record"].lower() == "0x15f1f4"
        for facing in (0, 1)
    }
    actual = {
        (item["assembly"], item["facing"])
        for item in presentations
        if item["kind"] == "player-button3-cleanup"
    }
    return actual == expected


def button1_presentation_union_is_complete(presentations, fixture):
    weapon = fixture["authority_data"]["player"][
        "weapon_projectile_resource"]["implementation_contract"]
    weapon_timelines = weapon["sufficient_action"][
        "presentation_selector_contract"]["selector_timelines"].values()
    expected = {
        (kind, int(record["assembly"], 16), facing)
        for kind, timeline in (
            [("player-button1", timeline) for timeline in weapon_timelines] +
            [("player-button1-empty",
              weapon["empty_fallback"]["presentation_timeline"])])
        for record in timeline
        for facing in (0, 1)
    }
    actual = {
        (item["kind"], item["assembly"], item["facing"])
        for item in presentations
        if item["kind"] in ("player-button1", "player-button1-empty")
    }
    return actual == expected


def button1_empty_entry_carried_union_is_complete(presentations, fixture):
    authority = fixture["authority_data"]
    weapon = authority["player"]["weapon_projectile_resource"][
        "implementation_contract"]
    witnesses = weapon["empty_fallback"]["entry_projection"][
        "coffee_shop_witnesses"]
    locomotion = authority["player"]["locomotion_neutral_facing"]
    records = (locomotion["first_segment_execution_contract"][
                   "presentation"]["records"] +
               locomotion["release_transition"]["presentation"])
    assembly_by_record = {
        int(record["animation_record"], 16): int(record["assembly"], 16)
        for record in records
    }
    expected = {
        (assembly_by_record[int(witness["entry_animation_record"], 16)],
         facing)
        for witness in witnesses
        for facing in (0, 1)
    }
    actual = {
        (item["assembly"], item["facing"])
        for item in presentations
        if item["kind"] == "player-button1-empty-entry-carried"
    }
    return actual == expected


def button1_projectile_union_is_complete(presentations, fixture):
    weapon = fixture["authority_data"]["player"][
        "weapon_projectile_resource"]["implementation_contract"]
    parent = weapon["record4_parent_class0"]["initialization"][
        "presentation_records"]
    child = weapon["record4_child_class4"]["initialization"][
        "variant_presentation_sequences"]
    expected = {
        (kind, int(record["assembly"], 16), facing)
        for kind, records in (
            ("projectile-parent", parent),
            ("projectile-child",
             [record for sequence in child.values() for record in sequence]))
        for record in records
        for facing in (0, 1)
    }
    actual = {
        (item["kind"], item["assembly"], item["facing"])
        for item in presentations
        if item["kind"] in ("projectile-parent", "projectile-child")
    }
    return actual == expected


def button1_button2_special_union_is_complete(presentations, fixture):
    special = fixture["authority_data"]["player"][
        "weapon_projectile_resource"]["special_implementation_contract"]
    expected = {
        (int(record["assembly"], 16), facing)
        for record in special["initialization"]["presentation_records"]
        for facing in (0, 1)
    }
    actual = {
        (item["assembly"], item["facing"])
        for item in presentations
        if item["kind"] == "player-button1-button2-special"
    }
    return actual == expected


def empty_effect_union_is_complete(presentations, fixture):
    effect = fixture["authority_data"]["player"][
        "weapon_projectile_resource"]["implementation_contract"][
            "empty_effect_variant1_contract"]
    facing = effect["initialization"]["presentation_actor_fields"][
        "facing_u8"]
    expected = {(int(record["assembly"], 16), facing) for record in
                effect["active_state"]["presentation_records"]}
    actual = {(item["assembly"], item["facing"]) for item in presentations
              if item["kind"] == "class10-empty-effect"}
    return actual == expected


def class1f_current_union_is_complete(presentations, fixture):
    class1f = next(item for item in fixture["authority_data"]["enemies"]
                   ["archetypes"] if item["class"] == "0x1f")
    current = class1f["current_state_implementation_contract"]
    def address_key(value):
        return "0x%08x" % int(str(value), 16)

    record_map = {
        address_key(record["animation_record"]): int(record["assembly"], 16)
        for record in class1f["presentation_and_collision"]["records"]
    }
    addresses = {
        address_key(current["spawn"]["initial_actor"]["animation_record"]),
        address_key(current["actions"]["above_lane_0x0600"][
            "animation_record"]),
        address_key(current["actions"]["reposition_0x1a00"][
            "animation_record"]),
    }
    for action in ("approach_0x1600", "attack_0x1800"):
        addresses.update(address_key(record["animation_record"])
                         for record in current["actions"][action]["records"])
    action_execution = class1f["first_segment_action_execution_contract"]
    action_0c = action_execution["action_programs"]["action_0x0c"]
    action_0c_selectors = {
        action_0c["initial_selector_u8"],
        action_0c["middle_selector_u8"],
    }
    addresses.update(
        address_key(record["animation_record"])
        for selector in action_execution["animation_selector_table"][
            "selectors"]
        if selector["selector_u8"] in action_0c_selectors
        for record in selector["records"])
    addresses.update(address_key(address) for address in
                     class1f["presentation_and_collision"]
                     ["accepted_hit_ko_records"]["record_addresses"])
    expected = {(record_map[address], facing)
                for address in addresses for facing in (0, 1)}
    actual = {(item["assembly"], item["facing"])
              for item in presentations
              if item["kind"] == "class1f-current"}
    return actual == expected


def class1f_source_hit_window_union_is_complete(presentations, fixture):
    class1f = next(item for item in fixture["authority_data"]["enemies"]
                   ["archetypes"] if item["class"] == "0x1f")
    current = class1f["current_state_implementation_contract"]
    source_hit_program = current["damage_hit_ko_removal"][
        "source_hit_entry_program"]["source_hit_program"]
    addresses = {
        int(record["animation_record"], 16)
        for sequence in source_hit_program["animation_sequences"].values()
        for record in sequence["records"]}
    addresses.add(int(source_hit_program["normal_return"][
        "class1f_resume_animation_record"], 16))
    expected = {(address, facing) for address in addresses
                for facing in (0, 1)}
    actual = {(item["animation_record"], item["facing"])
              for item in presentations
              if item["kind"] == "class1f-source-hit-window"}
    return actual == expected


def class4e_retained_window_union_is_complete(presentations, fixture):
    retained = fixture["authority_data"]["auxiliary"][
        "first_segment_dependencies"][
            "class_0x4e_type24_variant4_effect"][
                "variant1_collision_effect"]["allocation"][
                    "fixed_slot_reuse_presentation"]
    expected = {
        (int(retained["animation_record"], 16),
         int(retained["assembly"], 16), facing)
        for facing in (0, 1)
    }
    actual = {
        (item["animation_record"], item["assembly"], item["facing"])
        for item in presentations
        if item["kind"] == "class4e-variant1-retained-window"
    }
    return actual == expected


def class43_population_union_is_complete(presentations, fixture):
    class43 = fixture["authority_data"]["auxiliary"][
        "first_segment_dependencies"][
            "class_0x43_type24_class01_scene_population"]
    expected = {
        (int(record["animation_record"], 16),
         int(record["assembly"], 16))
        for sequence in class43["state0"]["animation_sequences"]
        for record in sequence["records"]
    }
    actual = {
        (item["animation_record"], item["assembly"])
        for item in presentations
        if item["kind"] == "class43-population"
    }
    return actual == expected


def run(args):
    return subprocess.run([sys.executable, str(GENERATOR)] + args,
                          cwd=str(ROOT), capture_output=True, text=True)


def main() -> int:
    if not CAPTURE_ROOT.is_dir():
        print("test_avsp_gfx_tiles_budget: SKIP (private captures absent)")
        return 0

    carve_match = re.search(
        r"#define\s+AVSP_TILE_REGION_BYTES\s+(0x[0-9A-Fa-f]+|\d+)",
        (ROOT / "main.c").read_text(encoding="utf-8", errors="ignore"))
    if not carve_match:
        print("FAIL: AVSP_TILE_REGION_BYTES is unavailable")
        return 1
    carve_bytes = int(carve_match.group(1), 0)
    if COMBAT_OVERLAY.is_file() and \
            ARCHIVE.stat().st_size + COMBAT_OVERLAY.stat().st_size > carve_bytes:
        print("FAIL: street archive plus combat overlay exceeds the runtime carve")
        return 1

    sys.path.insert(0, str(ROOT / "tools"))
    from gen_avsp_emit_windows import load_spec02_round1_presentations
    presentations, _fixture_sha = load_spec02_round1_presentations()
    fixture = json.loads((ROOT / "data" /
                          "spec02_round1_generated_fixtures.json").read_text())
    if not button3_presentation_union_is_complete(presentations, fixture):
        print("FAIL: Button3 source presentation union is incomplete")
        return 1
    if not button3_cleanup_union_is_complete(presentations, fixture):
        print("FAIL: Button3 cleanup presentation union is incomplete")
        return 1
    if not button1_presentation_union_is_complete(presentations, fixture):
        print("FAIL: Button1 source presentation union is incomplete")
        return 1
    if not button1_empty_entry_carried_union_is_complete(
            presentations, fixture):
        print("FAIL: Button1 empty-entry carried presentation union is "
              "incomplete")
        return 1
    if not button1_projectile_union_is_complete(presentations, fixture):
        print("FAIL: Button1 projectile presentation union is incomplete")
        return 1
    if not button1_button2_special_union_is_complete(presentations, fixture):
        print("FAIL: Button1/Button2 special presentation union is incomplete")
        return 1
    if not empty_effect_union_is_complete(presentations, fixture):
        print("FAIL: class-0x10 source presentation union is incomplete")
        return 1
    if not class1f_current_union_is_complete(presentations, fixture):
        print("FAIL: class-0x1f current presentation union is incomplete")
        return 1
    if not class1f_source_hit_window_union_is_complete(
            presentations, fixture):
        print("FAIL: class-0x1f source HIT decoder window is incomplete")
        return 1
    if not class4e_retained_window_union_is_complete(
            presentations, fixture):
        print("FAIL: class-0x4e retained decoder window is incomplete")
        return 1
    if not class43_population_union_is_complete(presentations, fixture):
        print("FAIL: class-0x43 source presentation union is incomplete")
        return 1
    button3_indexes = [index for index, item in enumerate(presentations)
                       if item["kind"] == "player-button3"]
    if not button3_indexes or any(
            button3_presentation_union_is_complete(
                presentations[:index] + presentations[index + 1:], fixture)
            for index in button3_indexes):
        print("FAIL: Button3 presentation omission control is non-discriminating")
        return 1
    cleanup_indexes = [index for index, item in enumerate(presentations)
                       if item["kind"] == "player-button3-cleanup"]
    if not cleanup_indexes or any(
            button3_cleanup_union_is_complete(
                presentations[:index] + presentations[index + 1:], fixture)
            for index in cleanup_indexes):
        print("FAIL: Button3 cleanup omission control is non-discriminating")
        return 1
    for kind, complete in (
            ("player-button1", button1_presentation_union_is_complete),
            ("player-button1-empty", button1_presentation_union_is_complete),
            ("player-button1-empty-entry-carried",
             button1_empty_entry_carried_union_is_complete),
            ("projectile-parent", button1_projectile_union_is_complete),
            ("projectile-child", button1_projectile_union_is_complete),
            ("player-button1-button2-special",
             button1_button2_special_union_is_complete),
            ("class10-empty-effect", empty_effect_union_is_complete),
            ("class1f-current", class1f_current_union_is_complete),
            ("class1f-source-hit-window",
             class1f_source_hit_window_union_is_complete),
            ("class4e-variant1-retained-window",
             class4e_retained_window_union_is_complete),
            ("class43-population", class43_population_union_is_complete)):
        indexes = [index for index, item in enumerate(presentations)
                   if item["kind"] == kind]
        if not indexes or any(complete(
                presentations[:index] + presentations[index + 1:], fixture)
                for index in indexes):
            print("FAIL: %s presentation omission control is "
                  "non-discriminating" % kind)
            return 1

    # Establish a known-good baseline so the refused run's "untouched"
    # claim is checked against something, not against build/ debris.
    baseline = run(["--scope", "street"])
    if baseline.returncode != 0:
        print("FAIL: baseline --scope street run failed:\n" +
              baseline.stdout + baseline.stderr)
        return 1
    before_bytes = ARCHIVE.read_bytes()
    before_manifest = json.loads(MANIFEST.read_text())
    if before_manifest["scope"] != "street":
        print("FAIL: baseline manifest scope is not 'street'")
        return 1
    residency = before_manifest["presentation_residency"]
    native_presentations = before_manifest["routes"].get(
        "spec02_round1_native_presentations", {})
    if (native_presentations.get("decoded_variants") != 429 or
        native_presentations.get("unique_assemblies") != 233 or
        native_presentations.get("tiles_added") != 2233):
        print("FAIL: SPEC-02 native presentation union drifted")
        return 1
    if (residency["source_peak_unique_tiles"] != 374 or
        residency["source_peak_frame"] != 2357 or
        residency["projectile_simultaneous_bound"] != 6 or
        residency["parent_tiles_at_peak"] != 4 or
        residency["child_tiles_at_peak"] != 55 or
        residency["max_tiles_per_projectile"] != 55 or
        residency["max_tiles_per_impact"] != 0 or
        residency["per_tile_scanout_requirement"] != 653 or
        residency["composite_tile_threshold"] != 14 or
        residency["spec02_composite_unique_entries"] != 147 or
        residency["spec02_composite_texture_bytes"] != 467072 or
        residency["spec02_composite_max_texture_bytes"] != 11648 or
        residency["first_segment_composite_unique_entries"] != 194 or
        residency["first_segment_composite_texture_bytes"] != 587776 or
        residency["first_segment_composite_max_texture_bytes"] != 11648 or
        residency["first_segment_composite_frame_peak_entries"] != 11 or
        residency["first_segment_composite_frame_peak_bytes"] != 37248 or
        residency["first_segment_composite_frame_peak_frame"] != 2355 or
        residency["first_segment_composite_ranked_slot_capacities"] !=
            [11648, 10752, 4608, 4608, 3840, 3456, 3200, 3072,
             2560, 2048, 1920] or
        residency["first_segment_composite_ranked_slot_bytes"] != 51712 or
        residency["first_segment_peak_noncomposite_tiles"] != 158 or
        residency["first_segment_peak_noncomposite_frame"] != 2745 or
        residency["scene_composite_player_peak_entries"] != 2 or
        residency["scene_composite_player_peak_bytes"] != 3968 or
        residency["scene_composite_child_peak_entries"] != 1 or
        residency["scene_composite_child_peak_bytes"] != 7040 or
        residency["scene_composite_required_slots"] != 18 or
        residency["scene_composite_required_bytes"] != 90880 or
        residency["configured_composite_slots"] != 21 or
        residency["configured_composite_texture_budget"] != 126592 or
        residency["configured_composite_max_texture_bytes"] != 11648 or
        residency["startup_source_frame_range"] != [2074, 2253] or
        residency["startup_peak_noncomposite_tiles"] != 69 or
        residency["startup_peak_noncomposite_frame"] != 2208 or
        residency["retained_tile_sprite_pool"] != 218 or
        residency["mid_frame_lru_replacement_allowed"] is not False or
        residency["between_frame_composite_replacement_allowed"] is not True):
        print("FAIL: first-segment presentation residency drifted")
        return 1
    makefile = (ROOT / "makefile").read_text(encoding="utf-8")
    if ("main.o: src/port_v2/gameplay/round1/round1.h "
            "generated/avsp_emit_windows.h" not in makefile):
        print("FAIL: generated presentation windows cannot invalidate main.o")
        return 1
    jo_max_match = re.search(r"^JO_MAX_SPRITE\s*=\s*(\d+)$", makefile,
                             re.MULTILINE)
    if (jo_max_match is None or int(jo_max_match.group(1)) != 255 or
        int(jo_max_match.group(1)) <
            residency["configured_composite_slots"] +
            residency["retained_tile_sprite_pool"] + 16):
        print("FAIL: Jo sprite-definition bound/headroom drifted")
        return 1
    if ("$(JO_ENGINE_SRC_DIR)/sprites.o "
            "$(JO_ENGINE_SRC_DIR)/3d.o: makefile" not in makefile):
        print("FAIL: JO_MAX_SPRITE-dependent engine objects can become stale")
        return 1
    build_script = (ROOT / "build.ps1").read_text(encoding="utf-8")
    if ("$requiredSpriteArrayBytes = 255 * 8" not in build_script or
            "$spriteArrayDistance -lt $requiredSpriteArrayBytes" not in
            build_script):
        print("FAIL: target link does not reject overlapping Jo sprite arrays")
        return 1
    required_sprite_array_bytes = int(jo_max_match.group(1)) * 8
    if (abs(0x060BE97C - 0x060BED7C) >= required_sprite_array_bytes or
            abs(0x060BE568 - 0x060BED60) < required_sprite_array_bytes):
        print("FAIL: stale-array mutation control is non-discriminating")
        return 1

    refused = run(["--scope", "round1"])
    if refused.returncode == 0:
        print("FAIL: --scope round1 was accepted; it must be refused "
              "against the current AVSP_TILE_REGION_BYTES carve")
        return 1
    if "REFUSING to write" not in refused.stdout + refused.stderr:
        print("FAIL: round1 run failed for the wrong reason:\n" +
              refused.stdout + refused.stderr)
        return 1

    after_bytes = ARCHIVE.read_bytes()
    after_manifest = json.loads(MANIFEST.read_text())
    if after_bytes != before_bytes:
        print("FAIL: the refused round1 run modified the archive on disk")
        return 1
    if after_manifest != before_manifest:
        print("FAIL: the refused round1 run modified the manifest")
        return 1

    print("test_avsp_gfx_tiles_budget: PASS (round1 refused against a "
          "%d-byte carve; street archive and manifest untouched)"
          % before_manifest["tile_region_budget_bytes"])
    return 0


if __name__ == "__main__":
    if "--measure-only" in sys.argv:
        import hashlib
        sys.path.insert(0, str(ROOT / "tools"))
        import gen_avsp_gfx_tiles as generator
        paths = [ARCHIVE, MANIFEST, ROOT / "main.c"]
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
        run_result = subprocess.run(
            [sys.executable, str(GENERATOR), "--measure-round1-demand"],
            capture_output=True, text=True, timeout=90, check=True)
        report = json.loads(run_result.stdout)
        baseline = report["observed_demand"]
        assert report["paired_identity"]
        assert baseline["tile_count"] == 10920
        assert baseline["archive_bytes"] == 1442128
        assert baseline["frames"] == 13222
        assert baseline["peak_simultaneous_palette_banks"] == 12
        assert len(baseline["palette_banks"]) == 20
        assert baseline["segments"][0]["archive_bytes"] == 703460
        candidates = report["fixture_candidate_demand"]
        assert candidates["candidate_addresses"] == 640
        assert candidates["combined_observed_and_decoded_tile_count"] == 11745
        assert candidates["archive_lower_bound_with_observed_palettes_bytes"] == 1551028
        assert [x["assembly"] for x in candidates["decode_failures"]] == [
            "0x078ba2", "0x078bac", "0x078f90", "0x078f96"]
        assert candidates["classification"].startswith("INCOMPLETE_SIZING:")
        original_tiles = generator.entry_tile_codes
        generator.entry_tile_codes = lambda *args: set()
        mutant = generator.measure_round1_capture_demand(ROOT / ".deps/mame/full_route")
        assert mutant["tile_count"] == 0 and mutant["tile_code_sha256"] != baseline["tile_code_sha256"]
        generator.entry_tile_codes = original_tiles
        original_state = generator.RouteState
        class MissingFrame(original_state):
            def frames(self):
                for rec in super().frames():
                    if rec["frame"] != 2398:
                        yield rec
        generator.RouteState = MissingFrame
        try:
            generator.measure_round1_capture_demand(ROOT / ".deps/mame/full_route")
        except ValueError as exc:
            assert str(exc) == "incomplete Round1 capture"
        else:
            raise AssertionError("missing-frame mutation survived")
        finally:
            generator.RouteState = original_state
        assert before == [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
        print("Read-only paired demand PASS; two attributable measurement controls; zero native gameplay kills; staged archive/manifest/runtime unchanged")
        raise SystemExit(0)
    raise SystemExit(main())
