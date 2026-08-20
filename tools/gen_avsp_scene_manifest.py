#!/usr/bin/env python3
"""RP6: generate the authoritative semantic scene manifest from the RP2
census.

Every census group becomes one manifest scene carrying:

- the MEASURED source frame range and provisional bit-15 ID;
- a final stable ID content-addressed from the group signature (CPS-B hash,
  layer bases, video control, palette population), so it survives
  re-capture and re-grouping instead of depending on group order;
- input dependency derived from the composite input schedule runs;
- layer/object composition (layer bases, video control, object count range,
  scroll spans, row-scroll variety);
- audio events as the QSound change count (payloads stay private);
- the transition target (next scene's stable ID) and boundary reason;
- a semantic label ONLY where bound to recorded evidence (committed
  measurements or a reviewed private screenshot); every other scene keeps
  label null and a needs-label review flag. The runtime must treat unknown
  IDs as hard errors, never coerce them.

Tracked output: data/avsp_scene_manifest.json (hashes, counts, ranges and
labels only - no ROM bytes, no payloads).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "data" / "round1_route_census.json"
OUTPUT = ROOT / "data" / "avsp_scene_manifest.json"

# Semantic labels bound to evidence. Keys are (first_frame, last_frame) of
# the census group the evidence frame falls in; the entry names the label
# and the exact evidence. Screenshot review means the private capture PNG
# was inspected by the implementor; committed measurements cite the
# repository evidence.
LABELS: dict[tuple[int, int], dict[str, str]] = {
    (96, 438): {"label": "legal-warning",
                "evidence": "screenshot reference_00250 reviewed"},
    (456, 665): {"label": "epa-recycle",
                 "evidence": "screenshot reference_00550 reviewed"},
    (698, 971): {"label": "qsound-virtual-audio",
                 "evidence": "screenshot reference_00800 reviewed"},
    (988, 1105): {"label": "capcom-logo",
                  "evidence": "screenshot reference_01050 reviewed"},
    (1116, 1251): {"label": "opening-earth",
                   "evidence": "screenshot reference_01180 reviewed"},
    (1273, 1513): {"label": "opening-demo",
                   "evidence": "screenshot reference_01400 reviewed"},
    (1538, 1623): {"label": "opening-story-panel",
                   "evidence": "screenshot reference_01600 reviewed"},
    (1693, 1958): {"label": "character-select",
                   "evidence": "screenshot reference_01700 reviewed; "
                               "confirmation shutter interval 1860-1970 "
                               "measured at SP3 (e728c9b)"},
    (1972, 2073): {"label": "round1-title",
                   "evidence": "screenshot reference_02000 reviewed; title "
                               "composition measured at SP4 (aa0d671)"},
    (2074, 5542): {"label": "round1-street-gameplay",
                   "evidence": "RP4 street interval 3474-3674 inside this "
                               "group, reconstructed exactly (18c781f); "
                               "screenshot reference_02500 region"},
    (5567, 5658): {"label": "round1-barricade-dialogue",
                   "evidence": "screenshot reference_05600 reviewed"},
    (5659, 6199): {"label": "round1-warehouse-gameplay",
                   "evidence": "screenshot reference_06000 reviewed"},
    (7504, 9004): {"label": "round1-warehouse-stalker-2",
                   "evidence": "screenshot reference_09000 reviewed "
                               "(STALKER nameplate)"},
    (11542, 12442): {"label": "round1-warehouse-stalker-3",
                     "evidence": "screenshot reference_12000 reviewed"},
    (6201, 6692): {"label": "continue-countdown",
                   "evidence": "screenshot reference_06446 reviewed "
                               "(CONTINUE? 25 over Predator wristband)"},
    (6693, 7438): {"label": "round1-warehouse-stalker",
                   "evidence": "screenshot reference_07065 reviewed "
                               "(STALKER nameplate)"},
    (9040, 9940): {"label": "round1-warehouse-gameplay-2",
                   "evidence": "screenshot reference_09490 reviewed"},
    (9976, 11476): {"label": "round1-chrysalis-battle",
                    "evidence": "screenshot reference_10726 reviewed "
                                "(CHRYSALIS nameplate)"},
    (12478, 12798): {"label": "round1-warehouse-gameplay-3",
                     "evidence": "screenshot reference_12638 reviewed"},
    (12800, 13292): {"label": "continue-countdown-2",
                     "evidence": "screenshot reference_13046 reviewed"},
    (13293, 15039): {"label": "round1-chrysalis-battle-2",
                     "evidence": "screenshot reference_14166 reviewed "
                                 "(CHRYSALIS nameplate)"},
    (15092, 15192): {"label": "round2-title",
                     "evidence": "screenshot reference_15142 reviewed "
                                 "(ROUND 2 WAR IN THE UNDERPASS)"},
    (15193, 18000): {"label": "round2-underpass",
                     "evidence": "screenshots reference_15300 (intro "
                                 "dialogue) and reference_17800 (gameplay) "
                                 "reviewed; follows the Round 2 title"},
}

# The scripted composite route hits two CONTINUE countdowns (the player
# character dies twice); recorded so route-quality work can target them.


def stable_id(group: dict) -> str:
    """Content-addressed stable ID from the group signature."""
    payload = json.dumps({
        "cps_b": group["cps_b_sha256"],
        "layer_bases": group["layer_bases"],
        "video_control": group["video_control"],
        "palette_population": group["palette_population"],
        "map_unique_hashes": group["map_unique_hashes"],
    }, sort_keys=True).encode("ascii")
    return "S" + hashlib.sha256(payload).hexdigest()[:12]


def main() -> None:
    census = json.loads(CENSUS.read_text())
    groups = census["groups"]
    scenes = []
    seen_ids: dict[str, int] = {}
    for index, group in enumerate(groups):
        sid = stable_id(group)
        # Two groups may share a visual signature (e.g. a scene revisited);
        # keep IDs unique by suffixing the occurrence ordinal, which is
        # stable because groups are route-ordered by frame.
        occurrence = seen_ids.get(sid, 0)
        seen_ids[sid] = occurrence + 1
        if occurrence:
            sid = f"{sid}-{occurrence}"
        input_active = any(word != 0
                           for word, _count in group["input_word_runs"])
        key = (group["first_frame"], group["last_frame"])
        label = LABELS.get(key)
        scene = {
            "index": index,
            "stable_id": sid,
            "provisional_scene_id": group["provisional_scene_id"],
            "first_frame": group["first_frame"],
            "last_frame": group["last_frame"],
            "frames": group["frames"],
            "boundary_reason": group["boundary_reason"],
            "input_dependent": input_active,
            "composition": {
                "layer_bases": group["layer_bases"],
                "video_control": group["video_control"],
                "object_count_min": group["object_count_min"],
                "object_count_max": group["object_count_max"],
                "scroll_min": group["scroll_min"],
                "scroll_max": group["scroll_max"],
                "rowscroll_unique_hashes": group["rowscroll_unique_hashes"],
                "palette_hashes": group["palette_hashes"],
            },
            "audio": {"qsound_change_frames": group["qsound_change_frames"]},
            "label": label["label"] if label else None,
            "label_evidence": label["evidence"] if label else None,
            "review_flags": [] if label else ["needs-label"],
        }
        scenes.append(scene)
    for index, scene in enumerate(scenes):
        if index + 1 < len(scenes):
            scene["transition"] = {
                "target_stable_id": scenes[index + 1]["stable_id"],
                "boundary_reason": scenes[index + 1]["boundary_reason"],
            }
        else:
            scene["transition"] = {
                "target_stable_id": None,
                "boundary_reason": "route-end-of-capture",
            }

    labelled = sum(1 for s in scenes if s["label"])
    manifest = {
        "schema": "avsp-scene-manifest-v0",
        "classification": "semantic manifest over the tracked RP2 census; "
                          "stable IDs, ranges, counts, labels and evidence "
                          "strings only - no ROM bytes or payloads",
        "source_census_schema": census["schema"],
        "route": census["route"],
        "scene_count": len(scenes),
        "labelled_scenes": labelled,
        "scenes": scenes,
    }
    OUTPUT.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"scene manifest: {len(scenes)} scenes, {labelled} labelled, "
          f"{len(scenes) - labelled} flagged needs-label")


if __name__ == "__main__":
    main()
