# Next agent prompt: S2 - resolve the part-table walk, then integrate

Continue the private native Alien vs Predator Saturn port using the
`port-cps2-to-sega-saturn` skill.

Repository:

```text
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
```

Expected branch: `codex/avp-master-plan`.

**Terminology:** "Gate" means **Capability Gate 1**, the seven-condition
acceptance contract. A step's own pass criteria are **checks**.

**This prompt authorizes finishing S2 only.** Not S3, not S4, not S5, not
stage work.

## Read and verify first

1. The skill's `SKILL.md` and `references/workflow.md`.
2. `AGENTS.md` and `CLAUDE.md`.
3. `docs/GOAL.md`.
4. `docs/AGENT_HANDOFF.md` — read the full S2 sequence in order: "S2
   integration - part 1 done, the object emitter decoded", "Correction and
   live verification of the above", "`+0x2E` resolved", "The object-word
   formula is now C, tested; `bsr $0AA59A` identified as the origin routine",
   and "Status across S1-S6". Do not skip any of these - each corrects or
   extends the one before it, and re-deriving what they already establish
   wastes the exact evidence this trail exists to save.
5. `docs/PARITY_PLAN.md` - the slice table and "How game logic gets
   translated".
6. `docs/TEST_PLAN.md` and `docs/HARDWARE_TEST.md`.

Record branch, HEAD, recent commits and `git status`. Preserve every existing
untracked/private ROM, MAME state, raw capture, `nvram/`, `snap/`,
`check_tail.py`, `tools/diag_*`, `tools/probe_*`, screenshot and helper file.
Stage explicit paths only. Never `git add -A`, `git add .`, reset, clean or a
broad stash. Do not switch, merge or cherry-pick the Marvel lane; do not edit
the separate MSHvSF worktree.

## What is already done, confirmed, and must not be re-derived

- **S1 passed**: `avsp_actor.h/.c`, `avsp_collision.h/.c`, both tested exactly
  against the game's own data.
- **S2 animation walk validated**: the interpreter predicts the game's own
  pointer with a 732-frame exact free-running run; 614 records extracted to 63
  spans (10 KB) proven to reproduce the full program image on every counter.
- **S2 object-word formula confirmed and coded**: `avsp_emit.h/.c` implements
  `X = ((origin_x - width - dx) & 0x3FF) | or_value`,
  `Y = (origin_y + dy) & 0x3FF`, `width = 16*(((attr>>8)&0xF)+1)`.
  `tests/avsp_emit_test.c` proves it exact for 3 of 5 parts, from ROM data
  alone, wired into `test.ps1`.
- **The origin routine is fully disassembled**: `bsr $0AA59A`
  (`0x0AA59A..0x0AA5E6`), called once per actor dispatch. It reads the actor's
  facing byte at `+0x0F` (source of the `D1` flip mask, confirmed: shifted
  into bit 5 at `0x0AA5E4`), computes `origin = actor_world_position -
  fixed_camera_anchor`, adjusted by one part-table long it consumes itself,
  and writes the result to `(A5-0x64F4)`.
- **Both spine sources cross-compile clean for SH-2** (confirmed by an actual
  Saturn build this session) but nothing in `main.c` calls them.

## The one open technical question

**The part-table header format and total part count.** A systematic search
over header candidate offsets before part0 (accounting for `bsr $0AA59A`'s own
one-entry consumption) found several offsets with small, plausible
`(budget, count, selector)` triples, but **none reconcile to the 5 confirmed
object-buffer writes** for the captured pose. There is also a confirmed
2-entry gap in the part-table between watched slots 2 and 3 that a single
`bsr` call does not explain. See the handoff section naming the exact offsets
tried and ruled out - do not re-run that search from scratch.

**Do not keep hand-parsing the flat disassembly for this.** It has already
produced one demonstrated misalignment this session. Use `capstone` (vendored
under `.deps/capstone`) for control-flow-aware disassembly starting from the
confirmed entry point `0x0AA00E`, or trace it live via a MAME watchpoint/step
probe (see `tools/mame_probe_emitter_pc.lua`, an untracked one-off diagnostic
kept for reference - it is not itself a proof and should not be committed).

## Sole objective

1. Resolve the header/count/skip mechanism well enough to walk an arbitrary
   pose's full part list in Python, and falsify the result against the
   5,302-frame object-list oracle (not just the one already-confirmed frame).
2. Generalize `avsp_emit.c` (or add alongside it) a part-table walker
   implementing the resolved algorithm, with its own host test against the
   oracle.
3. **Then, and only then**, wire ONE `AvspActor` into `main.c` for one street
   alien: give it a live `anim_record`, tick it with `avsp_anim_frame_tick`,
   and drive its rendered object list from the resolved emitter. Seed the
   pointer on every action change from the existing capture-derived action
   schedule (label `ADAPTED`, per "The dependency check A exposed" in the
   handoff) - S5 has not translated the actual decisions yet.
4. Render per CPS2 object (one VDP1 normal sprite per object, `nx*16 x ny*16`,
   16-colour bank mode, flip in `CMDCTRL`, per-block texture cache - the
   slice-V design retained in `PARITY_PLAN.md`). This is a substantial,
   separate piece of work; do not shortcut it with a placeholder marker or a
   repositioned capture-derived sprite. If time does not allow finishing it,
   stop at a clean checkpoint after step 2 or 3 rather than ship an
   unconvincing renderer.

## What NOT to do (learned the hard way this session)

- **Do not build a "does it render" proof-of-concept overlay in `main.c` and
  leave it half-verified.** One was built, boot-tested, and removed before
  committing this session specifically because it could not be visually
  confirmed cleanly (the autoplay route moved past the relevant combat window
  before a clean before/after screenshot could isolate it). If you build a
  visual check, either get a clean, unambiguous confirmation (e.g., a paused
  frame-by-frame capture, not a live autoplay screenshot race) or don't ship
  it as evidence.
- **Do not cross-reference two different MAME capture routes by source-frame
  number.** `collision_probe` and the object-emission captures are different
  routes; "frame 4214" names different game states in each. This caused a
  real, time-costing false "contradiction" earlier this session.
- **Do not treat the flat disassembly (`disasm_full.txt`) as ground truth for
  control flow.** It is a naive linear scan; verify anything load-bearing
  against live register/memory capture, as this session's corrections did.

## Exit checks

1. Header/count/skip mechanism resolved; a Python (or C) part-table walker
   reproduces all 5 of the captured pose's object words from ROM data alone,
   AND is falsified against the full 5,302-frame oracle with a reported match
   rate.
2. One street alien in `main.c` carries a live `AvspActor`, animates via
   `avsp_anim_frame_tick`, and its object list is produced by the resolved
   emitter - not a placeholder, not a repositioned capture-derived sprite.
3. That object list renders via a real per-object VDP1 path (not the
   precomposed-cel path) at at least a basic, honest level of fidelity.
4. Frame time at the peak frame (86 objects / 909 tiles, source frame 5776)
   measured on real hardware or a close proxy, instrument named. Emulator
   frame time is indicative only.

## Acceptance

S2 passes when checks 1-3 pass; check 4 may be deferred to a follow-up if
time-constrained, but must be named as deferred, not silently skipped. It
closes **no** Capability Gate 1 condition: Gate 1 stays 0/7 and the full-game
goal stays 0/9, because one actor is not Round 1 and nothing has been
validated on physical hardware.

## Handoff discipline

Update `docs/AGENT_HANDOFF.md` and `docs/PARITY_PLAN.md` with the result and
honest status; record branch, HEAD, dirty files, raw paths, hashes and exact
commands; stop MAME and emulator processes or record their ownership; stage
explicit files only; commit one coherent checkpoint per genuinely-completed
piece rather than one large speculative commit.

## What comes next (do not start it here)

S3 widens the spine to the player, remaining street aliens, Stalkers and
Chrysalis. S4 wires `avsp_collision.c` into gameplay and retires the inferred
Chrysalis 21/55/97 and Stalker schedules. S5 translates the enemy decisions
this step has to seed by hand.
