# Next agent prompt: S2 integration — put the ROM animation walk in the runtime

Continue the private native Alien vs Predator Saturn port using the
`port-cps2-to-sega-saturn` skill.

Repository:

```text
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
```

Expected branch: `codex/avp-master-plan`.

**Terminology:** "Gate" means **Capability Gate 1**, the seven-condition
acceptance contract. A slice step's own pass criteria are **checks**.

**This prompt authorizes the integration half of S2 only.** Not S3, not
collision rewiring (S4), not AI (S5), not stage work.

## Read and verify first

1. The skill's `SKILL.md` and `references/workflow.md`.
2. `AGENTS.md` and `CLAUDE.md`.
3. `docs/GOAL.md`.
4. `docs/AGENT_HANDOFF.md` — "S2 animation walk", "S1 actor spine",
   "Phase A: AvP sprite demand measured".
5. `docs/PARITY_PLAN.md` — the slice table, the slice-V design retained for
   S2/S3, and "How game logic gets translated".
6. `docs/TEST_PLAN.md` and `docs/HARDWARE_TEST.md`.

Record branch, HEAD, recent commits and `git status`. Preserve every existing
untracked/private ROM, MAME state, raw capture, `nvram/`, `snap/`,
`check_tail.py`, `tools/diag_*`, `tools/probe_*`, screenshot and helper file.
Stage explicit paths only. Never `git add -A`, `git add .`, reset, clean or a
broad stash. Do not switch, merge or cherry-pick the Marvel lane; do not edit
the separate MSHvSF worktree.

## What is already done, and must not be redone

- **S1 passed.** `avsp_actor.h/.c` mirrors the game's `0xC0` actor record;
  481,566 loads, 0 field mismatches. `avsp_collision.h/.c` ports the overlap
  test and guards and reproduces the Python falsification exactly on all eight
  counters.
- **S2 validation passed.** The interpreter in `avsp_anim_script.c` predicts
  5,738 of the game's own pointer moves, and free-running from a single seed it
  predicts 23,676 frames exactly, longest run 732 frames.
- **S2 record extraction passed.** `tools/gen_avsp_anim_records.py` extracts the
  614 reachable records — **10,244 bytes in 63 spans** at their original
  addresses — and the interpreter over those 10 KB reproduces the full 2 MB
  program image on every counter (check C). The interpreter's `AvspAnimSpan`
  sparse form is what makes that possible.
- **Sprite demand measured.** Peak 86 objects / 909 tiles per frame, 83.6% of
  objects blocked averaging 8.51 tiles, 13 live palettes against 128 CRAM banks,
  per-frame texture delta 5.7 KB mean / 29.5 KB peak.

## Sole objective

Make the Saturn runtime animate one street alien from ROM records, and render it
from the object list those records produce.

Three parts, in this order:

1. **Link the interpreter — DONE.** `avsp_actor.c` and `avsp_anim_script.c` are
   already in `SRCS` and the Saturn image builds clean with them (ELF 709,853 B,
   ISO 5,554,176 B). They are linked but not called: `main.c` still runs the cel
   path and nothing references `generated/avsp_anim_records.h` yet. What remains
   of this part is to give the runtime's street alien an `AvspActor` carrying a
   live `anim_record`, ticked once per frame by `avsp_anim_frame_tick`.

2. **Emit the object list.** The emitter is now **decoded from the game's code** -
   the full specification, both facing variants, is in the handoff section
   "S2 integration — part 1 done, the object emitter decoded". Implement that,
   do not re-derive it. In short: the pose record's `+4` assembly is a part list
   of 6-byte entries (a `long` code|attr plus a `word` advancing a separate
   offset table), and that offset table supplies a `dx`,`dy` word pair per part.
   Four inputs remain unresolved and **must have their source named before use**:
   `A2`'s initial value, `D1`'s flip mask, the actor field at `+0x2E`, and the
   screen origin at `(A5-0x64F4)`. Recover each from live evidence, then falsify
   the whole emitter against the captured object lists.

3. **Render per CPS2 object.** One VDP1 normal sprite per object,
   `nx*16 x ny*16`, 16-colour bank mode, flip in `CMDCTRL`, jump-next linked,
   source list order as draw order, with a per-block texture cache. The full
   design and its fallback are in `PARITY_PLAN.md` under the retained slice-V
   detail. Per-tile is the fallback if per-object misses 60 Hz; report both
   command counts either way.

## Exit checks

1. **Object list matches.** For the street-alien actor over the street-fight
   window, the object entries the runtime produces match MAME's captured active
   object list for the same source frame. This is the oracle slice V could not
   use and this step can: 5,302 captured frames under `.deps/mame/enemy_actions`,
   `.deps/mame/stalker_actions` and `.deps/mame/boss_actions`. Report matched
   frames and the first mismatch.
2. **The alien animates from ROM data on Saturn**, with its `/SPR4` pose archive
   no longer loaded for that actor.
3. **Frame time at the peak frame** (86 objects / 909 tiles, source frame 5776)
   measured and reported with the instrument named. Emulator frame time is
   indicative only; 60 Hz binds on physical Saturn per `docs/HARDWARE_TEST.md`.

## The dependency check A exposed

The interpreter *advances* an animation; it does not *choose* one. The 804
unexplained transitions are the game re-pointing the record on an AI decision,
action change or input — about one every 78 actor-frames for a street alien.
Until S5 translates those decisions, the runtime must seed the pointer on every
action change. **Seed it from the existing capture-derived action schedule and
label that `ADAPTED` in the handoff.** Do not invent a decision rule, and do not
present a seeded animation as ROM-driven behaviour: the *animation* is
ROM-driven in this step, the *decision to start it* is not yet.

## Boundaries

- Do not rewire collision to `avsp_collision.c` yet — that is S4, and it needs
  the selectors this step makes live.
- Do not touch the boss, Stalkers or the player in this step; one street alien.
- Do not decode further ROM tables. The standing rule from milestone 2 holds.
- Never commit ROM bytes, tile data, raw screenshots, RAM dumps or disc members.
  `generated/avsp_anim_records.h` is git-ignored for exactly this reason.
- Restore `normal-release` after any diagnostic build.

## Acceptance

The integration half of S2 passes when check 1 passes with reported counts,
check 2 renders on Saturn, and check 3 has a measured frame time from a named
instrument. It closes **no** Capability Gate 1 condition: Gate 1 stays 0/7 and
the full-game goal stays 0/9, because one actor's animation is not Round 1's
animation and nothing has been validated on physical hardware.

## Handoff discipline

Update `docs/AGENT_HANDOFF.md` and `docs/PARITY_PLAN.md` with the result and
honest status; record branch, HEAD, dirty files, raw paths, hashes and exact
commands; stop MAME and emulator processes or record their ownership; stage
explicit files only; commit one coherent checkpoint if the checks pass.

## What comes next (do not start it here)

S3 widens the spine to the player, remaining street aliens, Stalkers and
Chrysalis. S4 rewires collision onto `avsp_collision.c` and retires the inferred
Chrysalis 21/55/97 and Stalker schedules. S5 translates the enemy decisions that
this step has to seed by hand.
