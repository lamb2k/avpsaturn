"""Generate the sparse ROM windows the runtime object decoder reads.

Measures the exact source addresses the corpus decode touches (poses,
assemblies, dx/dy tables) by running the proven decoder over sampled frames
of every paired capture route with an address-recording Rom wrapper. It groups
adjacent touched 256-byte pages into windows, then trims each window's exposed
edges to the first and last byte actually read, and emits:

  * generated/avsp_emit_windows.h - the window bytes (git-ignored, contains
    bytes from the private program image), as AvspRomSpan initializers.
  * data/avsp_emit_windows.json   - tracked manifest: window ranges, sizes,
    SHA-256 of each window and of the source image. No ROM bytes.

The generated view is then verified: the sampled frames are re-decoded
through ONLY the windows and every result must equal the full-image decode.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from decode_avsp_object_stream import Rom, decode_family2_entry  # noqa: E402
import verify_avsp_object_corpus as V      # noqa: E402

ROM_PATH = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
PAGE = 256
SAMPLE_STRIDE = 7   # every 7th frame per route keeps the run fast
SPEC_FIXTURE_PATH = ROOT / "data/spec02_round1_generated_fixtures.json"


class RecordingRom(Rom):
    def __init__(self, data):
        super().__init__(data)
        self.touched = set()
        self.touched_bytes = set()

    def _record(self, offset, size):
        self.touched.add(offset // PAGE)
        self.touched.add((offset + size - 1) // PAGE)
        self.touched_bytes.update(range(offset, offset + size))

    def u16(self, o):
        self._record(o, 2)
        return super().u16(o)

    def u32(self, o):
        self._record(o, 4)
        return super().u32(o)


class WindowRom(Rom):
    """Reads through the generated windows only; anything else raises."""

    class _ImageLen:
        def __len__(self):
            return 0x200000

    def __init__(self, windows):
        self.windows = windows  # list of (base, bytes)
        self.d = self._ImageLen()  # only len(rom.d) is consulted by callers

    def _at(self, o, need):
        for base, blob in self.windows:
            if base <= o and o + need <= base + len(blob):
                return blob[o - base:o - base + need]
        raise IndexError("outside windows: 0x%06x" % o)

    def u16(self, o):
        b = self._at(o, 2)
        return (b[0] << 8) | b[1]

    def u32(self, o):
        b = self._at(o, 4)
        return int.from_bytes(b, "big")


def decode_route_sample(rom, root):
    results = []
    frames = sorted(root.glob("workram_*.bin"))[::SAMPLE_STRIDE]
    for wpath in frames:
        work = wpath.read_bytes()
        if len(work) != 0x8000:
            continue
        ax, ay = V.read_anchors(work)
        for n in range((0x10000 - 0x8380) // V.ACTOR_STRIDE):
            so = (V.ACTOR_ANCHOR - V.WORKRAM_BASE) + n * V.ACTOR_STRIDE
            if so + V.ACTOR_STRIDE > len(work):
                break
            try:
                flat, meta = V.decode_actor_entries(rom, work, so, ax, ay)
            except IndexError:
                flat = None
            if flat is not None:
                results.append((wpath.name, so, tuple(flat)))
    return results


def load_spec02_round1_presentations():
    """The exact short-lived Round 1 assemblies, derived from SPEC-02.

    These actors are shorter-lived than the retained capture-corpus sampling
    window.  Keeping their source addresses in the accepted fixture and
    deriving this list prevents the Saturn content window from becoming a
    second, hand-maintained gameplay contract.
    """
    fixture_bytes = SPEC_FIXTURE_PATH.read_bytes()
    fixture = json.loads(fixture_bytes)
    authority = fixture["authority_data"]
    weapon = authority["player"][
        "weapon_projectile_resource"]["implementation_contract"]
    parent = weapon["record4_parent_class0"]
    child = weapon["record4_child_class4"]
    result = []
    seen = set()
    for kind, records, object_or in (
            ("projectile-parent",
             parent["initialization"]["presentation_records"],
             int(parent["initialization"]["object_or_u16"], 16)),
            ("projectile-child",
             [record for sequence in child["initialization"][
                 "variant_presentation_sequences"].values()
              for record in sequence],
             int(child["initialization"]["object_or_u16"], 16))):
        for record in records:
            assembly = int(record["assembly"], 16)
            for facing in (0, 1):
                key = (kind, assembly, facing)
                if key in seen:
                    continue
                seen.add(key)
                result.append({
                    "kind": kind,
                    "animation_record": int(record["animation_record"], 16),
                    "assembly": assembly,
                    "facing": facing,
                    "coordinate_mode": 0,
                    "palette": 0,
                    "object_or": object_or,
                })
    def add_records(kind, records, facings, modes, object_or, palettes=(0,)):
        for record in records:
            assembly = int(record["assembly"], 16)
            animation_record = int(record["animation_record"], 16)
            for facing in facings:
                for mode in modes:
                    for palette in palettes:
                        key = (kind, assembly, facing, mode, palette)
                        if key in seen:
                            continue
                        seen.add(key)
                        result.append({
                            "kind": kind,
                            "animation_record": animation_record,
                            "assembly": assembly,
                            "facing": facing,
                            "coordinate_mode": mode,
                            "palette": palette,
                            "object_or": object_or,
                        })

    jump = authority["player"][
        "directional_airborne_interruption"]["directional_actions"][
            "implementation_contract"]
    jump_actor = jump["presentation_actor_fields"]
    add_records("player-button1",
                weapon["sufficient_action"]["presentation_timeline"],
                (0, 1), (jump_actor["coordinate_mode_u8"],),
                int(jump_actor["object_or_u16"], 16),
                (jump_actor["palette_u8"],))
    add_records("player-button1-empty",
                weapon["empty_fallback"]["presentation_timeline"],
                (0, 1), (jump_actor["coordinate_mode_u8"],),
                int(jump_actor["object_or_u16"], 16),
                (jump_actor["palette_u8"],))
    empty_effect = weapon["empty_effect_variant1_contract"]
    empty_actor = empty_effect["initialization"][
        "presentation_actor_fields"]
    add_records("class10-empty-effect",
                empty_effect["active_state"]["presentation_records"],
                (empty_actor["facing_u8"],),
                (empty_actor["coordinate_mode_u8"],),
                int(empty_actor["object_or_u16"], 16),
                (empty_actor["palette_u8"],))
    add_records(
        "player-button3",
        [{"animation_record": record["record"],
          "assembly": record["assembly"]} for sequence in
         jump["presentation_selector_sequences"].values()
         for record in sequence],
        (0, 1),
        (jump_actor["coordinate_mode_u8"],),
        int(jump_actor["object_or_u16"], 16),
        (jump_actor["palette_u8"],))
    locomotion = authority["player"]["locomotion_neutral_facing"]
    add_records(
        "player-button3-cleanup",
        [{"animation_record": record["animation_record"],
          "assembly": record["assembly"]} for record in
         locomotion["release_transition"]["presentation"]
         if record["animation_record"].lower() == "0x15f1f4"],
        (0, 1),
        (jump_actor["coordinate_mode_u8"],),
        int(jump_actor["object_or_u16"], 16),
        (jump_actor["palette_u8"],))

    class1f = authority["enemies"]["archetypes"][3][
        "initial_transition_contract"]
    add_records("class1f-initial",
                [record for sequence in class1f["animation_sequences"]
                 for record in sequence["records"]], (1,), (1,), 0x8000,
                tuple(sorted({actor["palette_u8"]
                              for actor in class1f["actors"]})))
    class1f_authority = authority["enemies"]["archetypes"][3]
    class1f_current = class1f_authority[
        "current_state_implementation_contract"]
    def address_key(value):
        return "0x%08x" % int(str(value), 16)

    class1f_records = {
        address_key(record["animation_record"]): record
        for record in class1f_authority["presentation_and_collision"][
            "records"]
    }
    current_addresses = {
        address_key(class1f_current["spawn"]["initial_actor"][
            "animation_record"]),
        address_key(class1f_current["actions"]["above_lane_0x0600"][
            "animation_record"]),
        address_key(class1f_current["actions"]["reposition_0x1a00"][
            "animation_record"]),
    }
    for action in ("approach_0x1600", "attack_0x1800"):
        current_addresses.update(
            address_key(record["animation_record"])
            for record in class1f_current["actions"][action]["records"])
    current_addresses.update(
        address_key(address) for address in
        class1f_authority["presentation_and_collision"][
            "accepted_hit_ko_records"]["record_addresses"])
    missing_current = sorted(current_addresses - class1f_records.keys())
    if missing_current:
        raise AssertionError(
            "class-0x1f current presentation records are absent: %s" %
            ", ".join(missing_current))
    # The current actor can be struck on either side in a perturbed route.
    # Preserve both source facing transforms; this is presentation residency,
    # not a new facing rule.
    add_records("class1f-current",
                [class1f_records[address]
                 for address in sorted(current_addresses)],
                (0, 1), (1,), 0x8000, (0x15,))
    dependencies = authority["auxiliary"]["first_segment_dependencies"]
    class09 = dependencies["class_0x09_type20_rng_owner"]
    add_records("class09-initial",
                [record for sequence in class09["animation_sequences"]
                 for record in sequence["records"]], (0,), (0,), 0)
    class4e = dependencies["class_0x4e_type24_variant4_effect"]
    add_records("class4e-initial", class4e["animation_records"],
                (0,), (2,), 0x8000)
    class44 = dependencies["class_0x44_type24_command_guard_owner"]
    class44_actor = class44["state0_presentation_actor"]
    add_records("class44-initial", class44["animation_records"],
                (class44_actor["facing_u8"],),
                (class44_actor["coordinate_mode_u8"],),
                int(class44_actor["object_or_u16"], 16))
    return result, hashlib.sha256(fixture_bytes).hexdigest()


class FixturePoseRom:
    """Supply one synthetic pose record while preserving assembly reads."""

    def __init__(self, rom, assembly):
        self.rom = rom
        self.assembly = assembly
        self.d = rom.d

    def u16(self, offset):
        if offset == 0x120002:
            return 0
        return self.rom.u16(offset)

    def u32(self, offset):
        if offset == 0x120004:
            return self.assembly
        return self.rom.u32(offset)


def decode_spec02_presentations(rom, presentations):
    """Decode fixture-owned assemblies through the proven generic walker."""
    results = []
    for item in presentations:
        work = bytearray(0x8000)
        slot = V.ACTOR_ANCHOR - V.WORKRAM_BASE
        work[slot] = 1
        work[slot + 0x0d] = item["coordinate_mode"]
        work[slot + 0x0e] = item["palette"]
        work[slot + 0x0f] = item["facing"]
        work[slot + 0x10:slot + 0x12] = (944).to_bytes(2, "big")
        work[slot + 0x14:slot + 0x16] = (320).to_bytes(2, "big")
        work[slot + 0x1c:slot + 0x20] = (0x120000).to_bytes(4, "big")
        work[slot + 0x2e:slot + 0x30] = item["object_or"].to_bytes(2, "big")
        flat, reason = V.decode_actor_entries(
            FixturePoseRom(rom, item["assembly"]), bytes(work), slot,
            720, 256)
        if flat is None:
            raise AssertionError("SPEC-02 assembly 0x%06x rejected: %s" %
                                 (item["assembly"], reason))
        results.append((item["kind"], item["assembly"], item["facing"],
                        tuple(flat)))
    return results


def main() -> int:
    data = ROM_PATH.read_bytes()
    rec = RecordingRom(data)
    roots = [ROOT / ".deps/mame" / r for r in
             ("enemy_actions", "stalker_actions", "boss_actions", "boss_ko")]

    full_results = []
    for root in roots:
        full_results.extend(decode_route_sample(rec, root))
    spec_presentations, fixture_sha256 = load_spec02_round1_presentations()
    spec_full_results = decode_spec02_presentations(rec, spec_presentations)
    print("sampled decodes: %d, touched pages: %d"
          % (len(full_results), len(rec.touched)))

    # merge touched pages into windows
    pages = sorted(rec.touched)
    windows = []
    start = prev = pages[0]
    for p in pages[1:]:
        if p == prev + 1:
            prev = p
            continue
        windows.append((start * PAGE, (prev - start + 1) * PAGE))
        start = prev = p
    windows.append((start * PAGE, (prev - start + 1) * PAGE))
    trimmed = []
    for base, size in windows:
        end = base + size
        used = [offset for offset in rec.touched_bytes
                if base <= offset < end]
        trimmed_base = min(used)
        trimmed_end = max(used) + 1
        trimmed.append((trimmed_base, trimmed_end - trimmed_base))
    windows = trimmed
    blobs = [(base, data[base:base + size]) for base, size in windows]
    total = sum(size for _, size in windows)
    print("windows: %d, total bytes: %d" % (len(windows), total))

    # verification: identical decode through the windows alone
    wrom = WindowRom(blobs)
    check_results = []
    for root in roots:
        check_results.extend(decode_route_sample(wrom, root))
    if check_results != full_results:
        print("VERIFY FAIL: window decode differs from full-image decode")
        return 1
    spec_check_results = decode_spec02_presentations(wrom,
                                                     spec_presentations)
    if spec_check_results != spec_full_results:
        print("VERIFY FAIL: SPEC-02 presentation window decode differs")
        return 1
    print("verify: window-only decode identical on all %d sampled decodes"
          % len(check_results))

    out_h = ROOT / "generated" / "avsp_emit_windows.h"
    lines = ["/* Generated by tools/gen_avsp_emit_windows.py. Do not edit, do"
             " not commit.\n * Contains bytes from the private program image."
             " */\n#ifndef AVSP_EMIT_WINDOWS_H\n#define AVSP_EMIT_WINDOWS_H\n"
             "\n#include \"../avsp_emit.h\"\n"]
    for i, (base, blob) in enumerate(blobs):
        rows = []
        for off in range(0, len(blob), 16):
            rows.append(",".join("0x%02x" % b for b in blob[off:off + 16]))
        lines.append("static const unsigned char avsp_emit_win_%02d[%d] = {\n    %s,\n};\n"
                     % (i, len(blob), ",\n    ".join(rows)))
    lines.append("static const AvspRomSpan avsp_emit_windows[%d] = {\n" % len(blobs))
    for i, (base, blob) in enumerate(blobs):
        lines.append("    { avsp_emit_win_%02d, 0x%06XUL, %dUL },\n"
                     % (i, base, len(blob)))
    lines.append("};\n\n#define AVSP_EMIT_WINDOW_COUNT %d\n\n#endif\n" % len(blobs))
    out_h.write_text("".join(lines))

    manifest = {
        "schema": 1,
        "classification": "window manifest only - no ROM bytes",
        "source_image": {"sha256": hashlib.sha256(data).hexdigest(),
                         "bytes": len(data)},
        "page_bytes": PAGE,
        "sample_stride": SAMPLE_STRIDE,
        "sampled_decodes": len(full_results),
        "spec02_round1_presentations": {
            "fixture": str(SPEC_FIXTURE_PATH.relative_to(ROOT)).replace(
                "\\", "/"),
            "fixture_sha256": fixture_sha256,
            "decoded_variants": len(spec_full_results),
            "unique_assemblies": len({item["assembly"]
                                      for item in spec_presentations}),
            "verified_identical": True,
        },
        "windows": [{"base": "0x%06x" % base, "size": size,
                     "sha256": hashlib.sha256(data[base:base + size]).hexdigest()}
                    for base, size in windows],
        "total_bytes": total,
        "verified_identical": True,
    }
    out_j = ROOT / "data" / "avsp_emit_windows.json"
    out_j.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print("wrote %s and %s" % (out_h, out_j))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
