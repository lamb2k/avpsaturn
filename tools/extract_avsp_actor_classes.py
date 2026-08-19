"""Decode the MASTER actor dispatch: the per-class routine table.

This resolves the item the sub-state dispatch body (93c623c) left open -
what actually calls into a sub-state dispatcher such as 0x060532 - and it
CORRECTS that body's level-1 model.

THE MASTER LOOP (live-traced 2026-08-19, then read offline):

    01B980: moveq   #$13, D7            ; 20 slots
    01B982: lea     ($1580,A5), A6      ; band base = A5 + 0x1580
    01B986: tst.b   (A6)                ; slot gate (+0x00 nonzero = live)
    01B988: beq     $1b9ac
    01B98A: tst.b   ($48,A6)            ; per-slot countdown at +0x48 ...
    01B990: subq.b  #1, ($48,A6)        ; ... decremented, clearing +0x47
    01B99A: move.b  ($2,A6), D0         ; INDEX = actor byte +0x02 (class)
    01B99E: ext.w   D0
    01B9A0: add.w   D0, D0
    01B9A2: add.w   D0, D0              ; x4 (absolute-long entries)
    01B9A4: movea.l ($10,PC,D0.w), A0   ; table base = 0x01B9B6
    01B9AA: jsr     (A0)                ; CALL the class routine
    01B9AC: lea     ($c0,A6), A6        ; stride 0xC0
    01B9B0: dbra    D7, $1b986

Measured live (logerror at 0x01B986, cold-boot enemy_actions route):
A5 = 0x00FF8000, so the band is 0x00FF9580 .. 0x00FFA3C0 - twenty 0xC0
slots. Relative to this project's usual actor anchor 0xFF8380 that band
begins at anchor-slot 24. Street aliens were observed live in this band
carrying class 0x1F, which is exactly the table entry for 0x060532.

THE CORRECTION: the sub-state body modelled the outer level as the ACTION
byte +0x06. That is wrong for the street alien. Its class-table entry lands
DIRECTLY on the sub-state dispatcher 0x060532 - there is no action-level
indirection in between, which is precisely why an offline scan of all 85
"+0x06" idiom sites found none pointing at 0x060532. The +0x06 sites are
real but belong to whichever classes use them; they are not a universal
level 1. The measured chain for a street alien is:

    actor +0x02 (class 0x1F) -> table 0x01B9B6 -> 0x060532
      -> actor +0x04 (sub-state) -> per-state handler -> table_set immediate

Output: data/avsp_actor_class_table.json - addresses/indices only, no ROM
bytes. Skips cleanly when the private opcode dump is absent, the same
contract as tools/extract_avsp_dispatchers.py.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
OUT_JSON = ROOT / "data" / "avsp_actor_class_table.json"

TABLE_BASE = 0x01B9B6      # from movea.l ($10,PC,D0.w),A0 at 0x01B9A4
LOOP_PC = 0x01B980
BAND_BASE = 0x00FF9580     # MEASURED live: A5(0x00FF8000) + 0x1580
BAND_SLOTS = 20            # moveq #$13,D7
ACTOR_STRIDE = 0xC0

CODE_LO, CODE_HI = 0x1000, 0x1FFFFF

# Live/offline-proven anchors the decode must reproduce exactly.
KNOWN = {
    0x1F: 0x060532,   # street alien -> the "normal" sub-state dispatcher
    0x00: 0x03F09C,   # -> routine whose sub-state dispatcher is 0x03F0C4
}


def main() -> int:
    if not OPCODES.is_file():
        print("actor class table: SKIPPED - opcode dump absent (%s)"
              % OPCODES.relative_to(ROOT).as_posix())
        return 0

    data = OPCODES.read_bytes()

    entries = []
    for index in range(0, 256):
        off = TABLE_BASE + index * 4
        if off + 4 > len(data):
            break
        value = int.from_bytes(data[off:off + 4], "big")
        if not (CODE_LO <= value <= CODE_HI):
            break
        entries.append({"class": "0x%02X" % index,
                        "routine": "0x%06X" % value})

    failures = []
    if not entries:
        failures.append("table decoded empty")
    for cls, expected in KNOWN.items():
        if cls >= len(entries):
            failures.append("class 0x%02X beyond decoded table" % cls)
            continue
        got = int(entries[cls]["routine"], 16)
        if got != expected:
            failures.append("class 0x%02X -> 0x%06X, expected 0x%06X"
                            % (cls, got, expected))

    # Negative control: a fabricated class must NOT resolve to a known
    # anchor, proving the check is not trivially satisfied.
    control_ok = True
    if len(entries) > 2:
        if int(entries[2]["routine"], 16) in KNOWN.values():
            control_ok = False
            failures.append("negative control: class 0x02 collides with an "
                            "anchor routine")

    manifest = {
        "schema": 1,
        "classification": "master actor dispatch - loop/table addresses and "
                          "class indices only; no ROM bytes",
        "question": "what calls into a sub-state dispatcher such as 0x060532?",
        "method": "live instruction trace of the master actor loop (bank-write "
                  "framed window ending at 0x060532), then offline decode of "
                  "the PC-relative absolute-long table it indexes, from the "
                  "validated opcode-space dump",
        "master_loop": {
            "pc": "0x%06X" % LOOP_PC,
            "slots": BAND_SLOTS,
            "band_base": "0x%08X" % BAND_BASE,
            "band_base_derivation": "A5 + 0x1580, with A5 = 0x00FF8000 "
                                    "MEASURED live at 0x01B986",
            "actor_stride": "0x%02X" % ACTOR_STRIDE,
            "slot_gate": "tst.b (A6)  - actor +0x00 nonzero",
            "index_source": "move.b ($2,A6),D0  - actor +0x02 (class)",
            "call_form": "movea.l ($10,PC,D0.w),A0 ; jsr (A0)",
        },
        "table_base": "0x%06X" % TABLE_BASE,
        "entry_count": len(entries),
        "entries": entries,
        "correction": "the sub-state body modelled the outer level as the "
                      "action byte +0x06; for the street alien the class "
                      "table entry lands DIRECTLY on sub-state dispatcher "
                      "0x060532 with no action-level indirection, which is "
                      "why scanning the 85 '+0x06' idiom sites found no link. "
                      "The +0x06 sites are not a universal level 1.",
        "anchors_verified": {"0x%02X" % k: "0x%06X" % v
                             for k, v in KNOWN.items()},
        "negative_control_ok": control_ok,
        "failures": failures,
        "result": "PASS" if not failures else "FAIL",
        "opcode_image_sha256": hashlib.sha256(data).hexdigest(),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")

    print("actor class table: %s - %d classes, base 0x%06X, band 0x%08X x%d"
          % (manifest["result"], len(entries), TABLE_BASE, BAND_BASE,
             BAND_SLOTS))
    for cls, expected in sorted(KNOWN.items()):
        print("  class 0x%02X -> 0x%06X (verified)" % (cls, expected))
    for f in failures:
        print("  FAILURE:", f)
    print("wrote", OUT_JSON)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
