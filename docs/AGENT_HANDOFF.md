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

## Owner course correction (2026-08-31) — fold into the in-flight body

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

## Exact next experiment

Close the complete Coffee Shop-reachable record-type-20/class-`0x05` source
program exposed by the scene differential. Source slots `0x00ffb180` and
`0x00ffb280` enter at frame 2673. The latter receives the source special contact
at frame 3891, transitions `0x0200 -> 0x0400 -> 0x0402 -> 0x0404 -> 0x0604`,
consumes its source RNG, allocates the second class-`0x4e` variant-1 impact in
slot `0x00ffc200`, and releases at frame 3931. Native currently omits this
program, leaving RNG two calls behind and causing the later class-`0x1f`
action/collision divergence.

Use the existing full-scene capture, decrypted program, and accepted evidence
first. If exact dispatch, guards, writers, or release fields remain absent,
perform only the smallest bounded MAME Oracle follow-up and amend the existing
auxiliary SPEC fixture. Implement the whole reusable class program, not a
frame/slot exception. Then run focused differential, mutations, fixture checks,
Target, one pinned scene run, and regenerate the complete census. Paired cold
Emulator and full WGC remain reserved for a coherent program or scene gate.
