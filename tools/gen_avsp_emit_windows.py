"""Generate the sparse ROM windows the runtime object decoder reads.

Measures the exact source addresses the corpus decode touches (poses,
assemblies, dx/dy tables) by running the proven decoder over sampled frames
of every paired capture route with an address-recording Rom wrapper, rounds
the touched set to 256-byte pages, merges adjacent pages into windows, and
emits:

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

    def u16(self, o):
        self.touched.add(o // PAGE)
        self.touched.add((o + 1) // PAGE)
        return super().u16(o)

    def u32(self, o):
        self.touched.add(o // PAGE)
        self.touched.add((o + 3) // PAGE)
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
    """The exact route-reachable Button1 assemblies, derived from SPEC-02.

    These actors are shorter-lived than the retained capture-corpus sampling
    window.  Keeping their source addresses in the accepted fixture and
    deriving this list prevents the Saturn content window from becoming a
    second, hand-maintained gameplay contract.
    """
    fixture_bytes = SPEC_FIXTURE_PATH.read_bytes()
    fixture = json.loads(fixture_bytes)
    lifecycle = fixture["authority_data"]["player"][
        "weapon_projectile_resource"]["implementation_contract"][
            "projectile_lifecycle_contract"]
    initialization = lifecycle["initialization"]
    actor_fields = initialization["presentation_actor_fields"]
    selectors = initialization["parent_presentation_selector"]
    presentations = selectors["presentation_sequences"]
    result = []
    seen = set()
    for parent_selector in selectors["route_reachable_values"]:
        sequence = selectors["animation_selector_u8"][parent_selector]
        for phase in ("first", "terminal"):
            assembly = int(presentations[sequence][phase]["assembly"], 16)
            for facing in (0, 1):
                key = ("projectile", assembly, facing)
                if key not in seen:
                    seen.add(key)
                    result.append({
                        "kind": "projectile",
                        "assembly": assembly,
                        "facing": facing,
                        "coordinate_mode": actor_fields[
                            "coordinate_mode_u8"],
                        "palette": actor_fields["palette_u8"],
                        "object_or": int(actor_fields["object_or_u16"], 16),
                    })
    impact = lifecycle["impact_actor_contract"]["initialization"]
    impact_fields = impact["presentation_actor_fields"]
    for record in impact["variant0_presentation_records"]:
        assembly = int(record["assembly"], 16)
        key = ("impact", assembly, 0)
        if key not in seen:
            seen.add(key)
            result.append({
                "kind": "impact",
                "assembly": assembly,
                "facing": 0,
                "coordinate_mode": impact_fields["coordinate_mode_u8"],
                "palette": impact_fields["palette_u8"],
                "object_or": int(impact_fields["object_or_u16"], 16),
            })
    return result, hashlib.sha256(fixture_bytes).hexdigest()


def decode_spec02_presentations(rom, presentations):
    """Decode fixture-owned family-2 assemblies through the supplied ROM."""
    results = []
    for item in presentations:
        assembly = item["assembly"]
        top = rom.u16(assembly)
        if top != 0x0002:
            raise AssertionError("SPEC-02 assembly 0x%06x is not family 2" %
                                 assembly)
        entry = decode_family2_entry(
            rom, assembly + 4, 944, 320, item["facing"], item["palette"],
            item["object_or"], 720, 256,
            item["coordinate_mode"] > 0)
        results.append((item["kind"], assembly, item["facing"],
                        tuple(int(entry[name], 16)
                              for name in ("x", "y", "code", "attr"))))
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
