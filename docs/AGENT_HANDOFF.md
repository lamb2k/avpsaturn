# REIMPLEMENT-13 active agent handoff

Resume the persistent AvP Goal on `codex/avp-playable-loop-pivot` from the branch
head. The active card remains `REIMPLEMENT-13-SOURCE-CLOSED-ROUND1`. The branch
head is a verified partial implementation, not Coffee Shop acceptance. The
accepted candidate intentionally remains
`d04a65a2253175c6e820140feefc35419e2cca07`.
Workflow pivot / Preserved evidence work: Resume the AvP salvage Goal; retain SALVAGE-00-OLD-BUILD-BASELINE, USER-01-PLAYER-BASELINE-REVIEW, and evidence candidate `597f4ed517d4e715d814ff841bd00d3977803f85`.

Read `project_state.yaml`, this handoff, the active task card, and current SPEC-02 contract/generated fixtures completely. Do not create another Goal,
roadmap, workflow, branch, task hierarchy, coverage system, or writer. Preserve USER-09 `CHANGES_REQUESTED`, SALVAGE-08 inactive, physical Saturn `UNRUN`, and all accepted locks. Never stage/reset/overwrite user-owned
`data/avsp_anim_records.json` or `history.txt`; stage owned paths explicitly.

## Owner course correction (2026-08-31) — completed in the in-flight body

Read this before continuing the uncommitted working-tree body. Do not restart,
revert the completed class-`0x05` program, or reopen accepted work; fold these
in at the current position.

1. The in-flight Target-size correction contains a hardware-invalid transfer;
   fix it before this body commits. The composite scratch now resolves to the
   cartridge bank (`AVSP_COMPOSITE_SCRATCH_BASE = AVSP_CART_DRAM1_BASE + ...`,
   `main.c`), but `jo_sprite_add_4bits_image` and
   `jo_sprite_replace_4bits_image` still upload it through
   `jo_dma_copy(picture->data, JO_VDP1_VRAM + ...)`
   (`.deps/joengine/jo_engine/sprites.c:175`), and `jo_dma_copy` is
   unconditionally `slDMACopy` (`jo/tools.h:164`) — SCU DMA. Boot-time pool
   initialization and every runtime composite replace are therefore SCU DMA
   transfers from A-bus (cart) to B-bus (VDP1 VRAM), which the SCU does not
   support — the sibling of the accepted "SCU DMA cannot write the A-bus"
   disc-load rule. Emulators do not enforce this bus restriction, so a paired
   Emulator PASS cannot prove it. Correct at the owning boundary: route
   cart-sourced VDP1 uploads through an explicit CPU copy (the code already
   reaches into `__jo_sprite_def`), or return the scratch to work RAM and
   recover the bytes another way. Add a real control rejecting an SCU-DMA
   A-bus endpoint on this path, and record the platform rule: no SCU DMA
   transfer with an A-bus endpoint; cart-sourced VDP1 uploads are
   CPU-mediated.
2. At this body's boundary, run paired cold Emulator and full WGC even though
   the whole-scene census is RED. The cart placement of the Round 1 runtime
   pools and scratch, the RLE terrain reconstruction, and the accumulated
   runtime bodies since the last paired run are platform-visible and need
   emulator-tier evidence now. Label the DMA point above physical-tier-only
   regardless of the emulator result.
3. After this body checkpoints, record as the next dependency-ready body a
   bounded memory-plan program (do not start it mid-chain): document the
   complete memory map (work-RAM linked-image limit; every cart carve with
   base, size, owner, load phase), size each carve for the complete Round 1
   route from the accepted ORACLE-11 census, add per-region build-time
   asserts, and move generated read-only SPEC fixture tables into one
   deterministic hashed cart content archive loaded at the existing boot
   load. Placement rule: mutable per-frame state prefers work RAM; read-only
   content prefers cart. Loading boundaries follow source seams only: the
   existing boot load; a Round 1 -> Round 2 stage-boundary load when needed
   (label ADAPTED for USER-10); intra-round loads only if census math proves
   all-resident cannot fit, under camera-locked transitions respecting the
   CDDA no-data-read rule; never mid-combat. No further ad-hoc size squeezes
   after this body — size pressure routes to the memory-plan program.
4. Hygiene: delete or ignore the untracked `.baseline_size/` directory at
   this checkpoint; it must not be committed. The two protected user files
   remain untouched.

Resolution: boot now reserves VDP1 texture storage without presenting an A-bus
source to Jo's SCU-DMA upload; runtime composite replacement uses an explicit
SH-2 CPU longword copy. Four mutations reject reintroducing an SCU-DMA A-bus
endpoint. Two cold pinned-emulator runs and a window-only cadence-1 WGC pass
were completed at this RED scene boundary. Those emulator results do not prove
the bus rule; the DMA boundary remains physical-tier-only and physical Saturn
is still `UNRUN`.

## Verified active boundary
The accumulated Coffee Shop program work is preserved. The latest bounded
correction makes type-16 collision depend on the source current player hurt
selector 17. The fabricated native frame-3878 hit is gone; the legitimate
frame-3877 HIT, frame-3878 special entry, frame-3891 selector-11 contact, and
class-`0x1f` special-KO trajectory through release frame 4002 remain exact.
The focused player-HIT lane passes nine real mutations and Oracle/SPEC/header
validation passes.

Target `LiveEncounterBench` BUILD_ONLY passes with GAME.BIN 417840 bytes and
BSS end `0x060bfef0`. The exact 4096-byte terrain selector map is reconstructed
from a deterministic 383-run encoding, preserving all source selectors while
remaining inside the existing memory carve. The combat overlay remains
byte-identical at SHA-256
`171f0dfa25d8a1fe94d2889f89c78e71bd3b1cfffa9fd5ff11964b1fc23815fe`.
Fast and Oracle reach the intentional full-host RED boundary at source frame
3782 (stage-progress call count 8 versus 7); no candidate promotion is made.

### Coffee Shop class-0x05 and cartridge upload checkpoint

The complete Coffee Shop-reachable record-type-20/class-`0x05` program is now
bound through accepted Oracle evidence, SPEC-02, generated fixtures, native C,
and real mutations. Slots `0x00ffb180` and `0x00ffb280` execute the source
`0x0200 -> 0x0400 -> 0x0402 -> 0x0404 -> 0x0604` program with selector-11
contact, RNG `0xcb46 -> 0x61a7`, command `0x0074`, dual trajectories, natural
class-`0x4e` variant-1 impact allocation in `0x00ffc200`, and release at source
frame 3931. Oracle auxiliary validation passes 114 mutations, SPEC-02 passes
180 mutations, and the focused native lane passes four real mutations.

Contract SHA-256 is
`bcba36794f1aa4e21012fda54d61745302a71ae33fa0d3480bc68d06a04156a3`;
fixture SHA-256 is
`be1aba966091941aba3de87e7d8574908b850f3529733b7e610e1b45fe38fc31`.
Target `LiveEncounterBench` BUILD_ONLY passes with GAME.BIN 408704 bytes, BSS
end `0x060bad80`, and `/GAME.BIN` SHA-256
`84fc1c479ecebef8b1f608fae3d2e7472adacba28fe4e1883711288797ff8bb8`.

The composite scratch remains in cartridge A-bus space, but boot pool creation
no longer supplies that pointer to Jo's SCU-DMA upload and runtime replacement
uses an explicit SH-2 CPU longword copy into VDP1 VRAM. The focused platform
test rejects four SCU-DMA/A-bus endpoint mutations. Governing platform rule:
no SCU DMA transfer may have an A-bus endpoint; cart-sourced VDP1 uploads are
CPU-mediated. This boundary is physical-tier-only; paired emulator evidence
cannot prove it, and physical Saturn remains `UNRUN`.

Two cold pinned Yaba runs pass deterministically with normalized ISO SHA-256
`47775bf876d2f6e3328f9452ea076ba73728ea6b5efcf28ef0badeb6916fe409`.
Real window-only Windows Graphics Capture covers every source frame 2280..2310.
The inspected full-speed WebP SHA-256 is
`7c1e6e3bafd379ef1a611d76a21d2f33bf6a61418ba6a1e10297585a63b967a8`;
the cadence-1 contact-sheet SHA-256 is
`45560cc804fb1ad226d55aa1ade170bde1a6c13c57f9976dd09d05b409c4a4dc`.
Predator identity, P1-only HUD, class-`0x1f`, impact cadence, both VDP2 planes,
palette, priority, and residency remain coherent. A transient frame-2287
capture-surface failure was rejected and recaptured from a fresh cold process.

The whole Coffee Shop census remains intentionally RED at native frame 4006,
scheduler code 29, after the class-`0x05` release is exact. This later boundary
does not reopen this completed program or promote the accepted candidate.

## Exact next experiment

Execute the bounded complete-Round-1 memory-plan program before expanding the
Coffee Shop scene farther. Document the work-RAM linked-image limit and every
cartridge carve with base, size, owner, and load phase. Size each carve once for
the complete accepted ORACLE-11 Round 1 census, add per-region build-time
assertions, and move the generated read-only SPEC terrain, timer/selector,
animation-record, and collision tables into one deterministic hashed cartridge
content archive loaded at the existing boot seam.

Mutable per-frame state prefers work RAM; read-only content prefers cartridge.
Permit only the existing boot load, a Round 1-to-Round 2 stage-boundary load
when needed and explicitly labeled `ADAPTED` for USER-10, or a census-proven
intra-round source seam under a camera lock that respects the CDDA no-data-read
rule and is never mid-combat. Do not make another ad-hoc size squeeze. After the
memory program passes, return to the earliest Coffee Shop frame-4006
player-collision divergence and rerun every completed scene regression affected
by the shared placement/runtime change.
