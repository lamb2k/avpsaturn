# Next agent prompt: S1 — the actor spine

Continue the private native Alien vs Predator Saturn port using the
`port-cps2-to-sega-saturn` skill.

Repository:

```text
C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest
```

Expected branch: `codex/avp-master-plan`.

**This prompt authorizes S1 only.** Not the renderer, not AI, not stage work,
and no change to shipped runtime behaviour.

## Read and verify first

1. The skill's `SKILL.md` and `references/workflow.md`.
2. `AGENTS.md` and `CLAUDE.md`.
3. `docs/GOAL.md`.
4. `docs/AGENT_HANDOFF.md` — "Capability Gate 1 — collision records", "Phase A:
   AvP sprite demand measured", "Plan re-sequenced around the actor spine".
5. `docs/PARITY_PLAN.md` — the phase table and "How game logic gets translated".
6. `docs/TEST_PLAN.md`.

Record branch, HEAD, recent commits and `git status`. Preserve every existing
untracked/private ROM, MAME state, raw capture, `nvram/`, `snap/`,
`check_tail.py`, `tools/diag_*`, `tools/probe_*`, screenshot and helper file.
Stage explicit paths only. Never `git add -A`, `git add .`, reset, clean or a
broad stash. Do not switch, merge or cherry-pick the Marvel lane; do not edit
the separate MSHvSF worktree.

## Why this is first

Four separate pieces of work are blocked behind one missing abstraction: the
native runtime has no actor that carries its ROM animation-record pointer.
Collision records are decoded and falsified but unusable. Animation scripts are
decoded and `avsp_anim_script.c` is written and host-tested but **not in the
Saturn build** (`SRCS = main.c capability_model.c`). Stage triggers and AI read
actor fields through the same record.

The renderer question was considered for this slot and deferred. Every measured
budget has an order of magnitude of headroom, the shipped build already sustains
more VDP1 sprite fill than a per-object pipeline would need, and the spine's
output is "a CPS2 object list" whichever granularity the renderer later
consumes. See the deferral note in `PARITY_PLAN.md`.

## Sole objective

A native actor record that mirrors the game's own `0xC0` actor layout, proven
field-for-field against captured work RAM, and enough C to make the already
decoded collision data live.

### Layout

Mirror the ROM record for the fields the game's own code consumes. These are
already proven and must not be re-derived:

| Offset | Field |
|---|---|
| `+0x00` | state |
| `+0x08` | type |
| `+0x0F` | facing |
| `+0x10` / `+0x14` / `+0x18` | world x / y / z |
| `+0x1C` | animation-record pointer |
| `+0x2C` / `+0x2D` | hit value / hit source |
| `+0x50` | collision table-set pointer |
| `+0x67` | attacker id |
| `+0x68..0x6F` | per-attacker hit latch |
| `+0x70` | suppress |
| `+0xD1` | latch index |

Actor slots sit on a `0xC0` grid anchored at the player slot `0xFF8380`. Do not
label fields beyond what collision, animation and the differential-replay method
actually consume — an exhaustive labelling of all 96 words is explicitly not
wanted.

Prefer a tracked, evidence-labelled field map plus a generated header over a
hand-written struct, so the layout is auditable and regenerable.

## Gates

1. **Field-for-field equality.** Load captured work-RAM frames into the native
   record and read back every field above, for every live actor, across the two
   collision-probe windows (`.deps/mame/collision_probe`, 4201–5500, and
   `.deps/mame/collision_probe_boss`, 13000–14600 — 2,900 frames). Any mismatch
   fails; report counts, not a sample.

2. **The decoded collision data becomes live C.** Port the overlap predicate and
   its guards from `tools/verify_avsp_collision.py` into C consuming this record
   and `data/avsp_collision.json`, then re-run the same falsification over the
   same captures. The C result must reproduce the Python result **exactly**:
   21,908 non-overlapping active pairs producing no hit, 44 of 56 latch events
   explained, the same 12 residuals. A different number is a defect in the port,
   not a new finding.

Gate 2 is the point of S1. It converts milestone 2's correct-but-inert evidence
into working C with an exact oracle, and it is the first time this project's
decoded data does anything.

## Boundaries

- **Host-only.** No change to `main.c`, no Saturn build change, no ISO, no
  emulator run. Nothing in the shipped runtime's behaviour changes in S1.
- Add the new record and collision code **alongside** `capability_model.c`. Do
  not rewire the existing inferred collision path yet; that is S4, after the
  animation record is live and can supply the selectors.
- Do not link `avsp_anim_script.c` into the Saturn build yet — that is S2.
- Do not decode further ROM tables. The standing rule from milestone 2 holds.
- Never commit ROM bytes, tile data, raw screenshots, RAM dumps or disc members.

## Acceptance

S1 passes when both gates pass with reported counts. It closes **no** Gate 1
condition: Gate 1 stays 0/7 and the full-game goal stays 0/9, because nothing
ROM-driven has reached the runtime yet. Say so plainly in the handoff.

## Handoff discipline

Update `docs/AGENT_HANDOFF.md` and `docs/PARITY_PLAN.md` with the result and
honest status; record branch, HEAD, dirty files, raw paths, hashes and exact
commands; stop MAME and emulator processes or record their ownership; stage
explicit files only; commit one coherent checkpoint if both gates pass.

## What comes next (do not start it here)

S2 — link `avsp_anim_script.c` into the Saturn build and drive pose selection
from the record pointer at `+0x1C` instead of the capture-derived clip tables.
Its gate is the strong one: the native walk must reproduce MAME's exact
per-frame animation-record-pointer sequence across the 2,121-frame street fight.
S2 is also where the renderer work resumes, because that is the first point at
which the runtime can *produce* an object list rather than replay one.
