#!/usr/bin/env python3
"""RP6 gate: structural verification of the semantic scene manifest.

Checks, against the tracked census only (no private material required):

1. the manifest tiles the complete census route with no gaps or overlaps;
2. every scene maps one-to-one onto a census group (range, provisional ID,
   composition fields, audio count);
3. signature IDs are unique and re-derivable from the census content,
   and runtime_scene_ids follow the policy exactly: index + 1, range
   1..0x7FFF, zero invalid, unique, pinned to the census SHA-256;
4. the transition chain is exactly the route order and ends with the
   route-end sentinel;
5. every scene either carries an evidence-bound label or a needs-label
   review flag - silent unlabeled scenes are not allowed;
6. negative controls: a shifted range, a forged signature ID, a broken
   transition, a silently unlabeled scene, a zero runtime ID, a duplicate
   runtime ID, a runtime ID above 0x7FFF, an unresolved transition
   target, and a mismatched census hash must each be detected.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from gen_avsp_scene_manifest import signature_id  # noqa: E402


import hashlib


def check(manifest: dict, census: dict, census_bytes: bytes) -> list[str]:
    errors: list[str] = []
    scenes = manifest["scenes"]
    groups = census["groups"]
    digest = hashlib.sha256(census_bytes).hexdigest()
    if manifest.get("source_census_sha256") != digest:
        errors.append("source census hash mismatch: manifest pins "
                      f"{manifest.get('source_census_sha256')}, census is "
                      f"{digest}")
    if len(scenes) != len(groups):
        errors.append(f"scene count {len(scenes)} != groups {len(groups)}")
        return errors

    route = census["route"]
    expected_next = route["first_frame"]
    seen_ids = set()
    seen_runtime_ids: set[int] = set()
    recomputed: dict[str, int] = {}
    for index, (scene, group) in enumerate(zip(scenes, groups)):
        if scene["first_frame"] != expected_next:
            errors.append(f"scene {index}: gap/overlap at frame "
                          f"{scene['first_frame']} (expected "
                          f"{expected_next})")
        expected_next = scene["last_frame"] + 1
        for field in ("first_frame", "last_frame", "frames",
                      "boundary_reason", "provisional_scene_id"):
            if scene[field] != group[field if field != "provisional_scene_id"
                                     else "provisional_scene_id"]:
                errors.append(f"scene {index}: {field} diverges from census")
        comp = scene["composition"]
        for field in ("layer_bases", "video_control", "object_count_min",
                      "object_count_max", "scroll_min", "scroll_max",
                      "rowscroll_unique_hashes", "palette_hashes"):
            if comp[field] != group[field]:
                errors.append(f"scene {index}: composition.{field} diverges")
        if scene["audio"]["qsound_change_frames"] != \
                group["qsound_change_frames"]:
            errors.append(f"scene {index}: audio count diverges")
        sid = signature_id(group)
        occurrence = recomputed.get(sid, 0)
        recomputed[sid] = occurrence + 1
        expect_sid = sid if not occurrence else f"{sid}-{occurrence}"
        if scene["signature_id"] != expect_sid:
            errors.append(f"scene {index}: signature ID "
                          f"{scene['signature_id']} != recomputed "
                          f"{expect_sid}")
        if scene["signature_id"] in seen_ids:
            errors.append(f"scene {index}: duplicate signature ID")
        seen_ids.add(scene["signature_id"])
        rid = scene["runtime_scene_id"]
        if rid != index + 1:
            errors.append(f"scene {index}: runtime_scene_id {rid} != "
                          f"index + 1")
        if rid == 0 or rid > 0x7FFF:
            errors.append(f"scene {index}: runtime_scene_id {rid} out of "
                          f"1..0x7FFF")
        if rid in seen_runtime_ids:
            errors.append(f"scene {index}: duplicate runtime_scene_id")
        seen_runtime_ids.add(rid)
        if scene["label"] is None and "needs-label" not in \
                scene["review_flags"]:
            errors.append(f"scene {index}: unlabeled without review flag")
        if scene["label"] is not None and not scene["label_evidence"]:
            errors.append(f"scene {index}: label without evidence")
        transition = scene["transition"]
        if index + 1 < len(scenes):
            if (transition["target_signature_id"] !=
                    scenes[index + 1]["signature_id"] or
                    transition["target_runtime_scene_id"] !=
                    scenes[index + 1]["runtime_scene_id"]):
                errors.append(f"scene {index}: transition target diverges")
        else:
            if (transition["target_signature_id"] is not None or
                    transition["target_runtime_scene_id"] is not None):
                errors.append("last scene: transition must be route-end")
    if expected_next != route["last_frame"] + 1:
        errors.append(f"route ends at {expected_next - 1}, census says "
                      f"{route['last_frame']}")
    labels = [s["label"] for s in scenes if s["label"]]
    if len(set(labels)) != len(labels):
        errors.append("labels are not unique")
    return errors


def main() -> None:
    manifest = json.loads(
        (ROOT / "data" / "avsp_scene_manifest.json").read_text())
    census_bytes = (ROOT / "data" / "round1_route_census.json").read_bytes()
    census = json.loads(census_bytes.decode())

    errors = check(manifest, census, census_bytes)
    if errors:
        for error in errors[:20]:
            print("FAIL:", error)
        raise SystemExit(1)

    controls = {}

    def detect(mutate):
        mutated = copy.deepcopy(manifest)
        mutate(mutated)
        return bool(check(mutated, census, census_bytes))

    def set_field(index, field, value):
        def mutate(m):
            m["scenes"][index][field] = value
        return mutate

    controls["shifted_range"] = detect(
        lambda m: m["scenes"][10].update(
            first_frame=m["scenes"][10]["first_frame"] + 1))
    controls["forged_signature_id"] = detect(
        set_field(20, "signature_id", "Sdeadbeefdead"))
    controls["broken_transition"] = detect(
        lambda m: m["scenes"][30]["transition"].update(
            target_signature_id=m["scenes"][0]["signature_id"]))
    controls["unresolved_transition_target"] = detect(
        lambda m: m["scenes"][30]["transition"].update(
            target_runtime_scene_id=9999))

    def unlabel(m):
        m["scenes"][40]["label"] = None
        m["scenes"][40]["label_evidence"] = None
        m["scenes"][40]["review_flags"] = []
    controls["silent_unlabeled"] = detect(unlabel)
    controls["runtime_id_zero"] = detect(
        set_field(5, "runtime_scene_id", 0))
    controls["runtime_id_duplicate"] = detect(
        set_field(6, "runtime_scene_id", 6))
    controls["runtime_id_over_range"] = detect(
        set_field(7, "runtime_scene_id", 0x8000))

    def wrong_hash(m):
        m["source_census_sha256"] = "0" * 64
    controls["census_hash_mismatch"] = detect(wrong_hash)

    failed = [name for name, detected in controls.items() if not detected]
    labelled = manifest["labelled_scenes"]
    print(f"scene manifest: {manifest['scene_count']} scenes verified, "
          f"{labelled} labelled, controls "
          f"{'PASS' if not failed else 'FAIL ' + ','.join(failed)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
