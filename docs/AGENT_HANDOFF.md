# Agent handoff: native AvP Saturn port

Updated: 2026-08-18 EDT. **Next body: finish S2 in dependency order** — first
resolve and exactly validate the general Family-1 part-stream walk, then promote
it to reusable C, integrate one live street-alien `AvspActor`, and render its
semantic object list per CPS2 object. See the hyper-detailed
`docs/NEXT_AGENT_PROMPT.md`; do not integrate from the current partial 3-entry
geometry check.

Session order, newest first. **S2 record extraction — PASSED:** 614 reachable
records, 10,244 bytes in 63 spans, and the interpreter over that 10 KB
reproduces the full 2 MB program image on every counter. **S2 animation walk —
interpreter VALIDATED:** 5,738 of the game's own pointer moves predicted, 23,676
frames predicted exactly free-running, longest run 732 frames; runtime
integration still open. **S1 actor spine — PASSED:** 481,566 actor loads with 0
field mismatches, and the C collision port reproduces the Python falsification
exactly on all eight counters. **Plan re-sequenced** around the actor spine into
slice steps S1–S6, with the renderer decision (old phase A) deferred into S2
after measurement showed the shipped build already draws more VDP1 sprite fill
than the candidate pipeline needs. **Milestone 2 (collision records) executed,
not closed**; **milestone 1 (street-alien emission) closed**.

**Naming.** Two vocabularies only: **Capability Gate 1** conditions (and the
nine full-game conditions) for acceptance, and slice steps **S1-S6** with
their **checks** for work. Milestones, phases A-E, slice V and the legacy
phases 0-4 are retired names kept only in the historical sections below; the
map is at the top of `docs/PARITY_PLAN.md`.

Two standing facts. **No Saturn AvP exists to compare against — this port is the
first**, so MAME's CPS2 `avspu` is always the fidelity oracle. **"Gate" means
Capability Gate 1 only**; a step's own criteria are checks, and a green check is
not gate progress (see `AGENTS.md` and the plan's Terminology section).

**Full-game goal audit: 0/9 conditions closed. Capability Gate 1: 0/7
conditions closed.** The indexes are at
[PARITY_PLAN.md#full-game-goal-progress-index](PARITY_PLAN.md#full-game-goal-progress-index)
and
[PARITY_PLAN.md#capability-gate-1-progress-index](PARITY_PLAN.md#capability-gate-1-progress-index).
The current capture-derived Round 1 route remains a useful regression baseline,
but it does not satisfy Gate 1's ROM-derived animation, collision, AI or stage-
table requirements and cannot close a full-game condition. Do not describe the
project as functionally parity complete or hardware-ready.

## S2 prompt and evidence-contract audit (2026-08-18)

The continuation contract was reconciled against the live source, test, this
handoff, and `PARITY_PLAN.md` before further implementation. The direction is
unchanged — finish S2 — but four precision corrections are now binding:

1. A CPS2 object is a **four-word entry** `[X,Y,code,attr]`. The C container was
   renamed from `AvspObjectWord` to `AvspObjectEntry`; five observed objects are
   five entries, not five words.
2. The current `avsp_emit_test` is a **partial geometry check**, not a complete
   ROM-only decoder. ROM supplies `dx/dy`; route-matched live capture supplies
   origin and actor `+0x2E`; the captured oracle still supplies code/attr. It
   proves X/Y for three observed entries and no more.
3. The two 6-byte source entries between the third and fourth observed writes
   are proven consumed, but their emission behaviour is `UNRESOLVED`. The old
   narrow watch window cannot distinguish writes outside its range from a
   conditional non-emitting path. A widened live trace or reachable-path CFG
   must decide it.
4. S2's oracle check is exact over a population declared before comparison:
   100% of eligible route/actor/family entries must match with zero unexplained
   mismatches. A reported or high match percentage is not a pass; S3-only
   formats may be excluded only when enumerated by reason.

`docs/NEXT_AGENT_PROMPT.md` now gives the complete ordered continuation:
route-matched widened trace, reachable-path part-stream decode, exact oracle
falsification, reusable C, one live street-alien `AvspActor`, then the real
per-object VDP1 consumer. It also records why both naming layers remain: S1-S6
are execution steps with checks; Capability Gate 1 is the seven-condition Round
1 acceptance contract. S-steps are not milestones or gates. This audit changes
no shipped gameplay or disc content.

Verification after the naming/comment correction:

- `test.ps1` passed: controller route reached Round 2 in 4,485 model frames,
  the 12,000-frame soak passed, actor/collision counters stayed exact, the S2
  animation walk retained its 732-frame longest exact run, and the renamed
  object-entry geometry check passed all three current entries.
- `build.ps1 -Clean -Release -SkipHostTests` passed, including SH-2 compile/link
  of `avsp_emit.c` and all ISO member size/SHA-256 checks.
- The regenerated ignored manifest is `profile=normal-release` with compile
  stamp `release-normal-release`; ISO 5,541,888 bytes, run-dependent SHA-256
  `5802871415fabcebc1ecdaa7974385be5a5ea7e5be7f0d3e78290b3ec23c10e3`;
  cue SHA-256 remains
  `bfc58c7020d90952e93bef7ecba32dea8d4faddf6ce6a90e1054206ee1807b12`.
- No MAME, Yaba Sanshiro, Mednafen, or RetroArch process from this checkout was
  running after verification. No emulator boot or physical-hardware check was
  run because shipped runtime behaviour did not change.

## Plan re-sequenced around the actor spine (2026-08-18)

The execution order in [`PARITY_PLAN.md`](PARITY_PLAN.md#master-execution-plan-2026-08-18)
was rebuilt. The seven Gate 1 acceptance conditions are **unchanged**; only the
order of work and its exit checks changed. New order: **A** decide the renderer by
measurement, **B** build the actor spine on one street alien, **C** widen to
Round 1's cast, **D** stage tables and enemy logic, **E** budget/validate/hardware.

Why: milestone 2 decoded the collision record format and falsified it, then could
not integrate, because the records are indexed by the live ROM animation-record
pointer at actor `+0x1C` and no native actor carries one. Stage triggers and AI
read actor fields through the same record, so four of five remaining milestones
were queued behind one missing abstraction. The runtime has no record pointer
because its unit of work is a precomposed pose picture (`main.c` cels through
`jo_sprite_add_4bits_image`, capture-derived pose tables, scalar lane collision
in `capability_model.c`), which gives ROM assemblies no consumer.

**Standing rule:** do not decode another ROM table in isolation while phase A or
B is open. Milestone 2 is the demonstration — correct, falsified, and inert.

## S2 integration — part 1 done, the object emitter decoded (2026-08-18)

**Part 1, linking: DONE.** `avsp_actor.c` and `avsp_anim_script.c` are in `SRCS`
and the Saturn image builds clean with them. That proves both are SH-2-clean and
link into the runtime. **They are linked, not yet called** — `main.c` still runs
the cel path, and `generated/avsp_anim_records.h` is not referenced by anything
in the image yet, so nothing in the shipped runtime's behaviour changed.

**Part 2, the object emitter: DECODED from the game's own code.** This is the
specification the next body implements. Two sibling loops, selected by facing:

```text
non-flipped 0x0AA1A8..0x0AA1DA        flipped 0x0AA1DC..0x0AA21E
  D2 = long (A0)+        ; code|attr from the assembly part list
  D2.b &= 0xE0           ; keep the attribute's high bits
  D2.b += A4[+0x0E]      ; add the actor's palette base
                              flipped only: D2 ^= D1        ; flip mask
                              flipped only: D4 = ((attr>>4)&0xF0)+0x10   ; nx*16
  D3 = long (A5-0x64F4)  ; the actor's screen origin
                              flipped only: D3.w -= D4      ; right edge at origin
  D3.w += word (A2)+     ; X += dx     (flipped: -= dx)
  D3.w &= 0x3FF
  D3.w |= A6[+0x2E]      ; priority and block-size bits
  swap D3
  D3.w += word (A2)+     ; Y += dy
  D3.w &= 0x3FF
  write long D3 -> X|Y   ; 0x0AA1CC / 0x0AA210
  write long D2 -> code|attr ; 0x0AA1CE / 0x0AA212
  D2 = word (A0)+        ; per-part advance for the offset table
  A2 += D2.w
  dbra D0                ; D0 = part count - 1
```

So the assembly at pose record `+4` is a part list of **6-byte entries** — a
`long` code|attr followed by a `word` that advances the separate `A2` offset
table — and `A2` supplies a `dx`,`dy` word pair per part. `(attr>>4)&0xF0 + 0x10`
confirms the block width comes from attribute bits 8-11, matching MAME's
`cps2_render_sprites`, and the flipped loop places the block's right edge at the
origin, which is the CPS2 flip semantics.

**This also resolves an oddity in the historical milestone-1 log.** The recorded `A0` values
jumped `0x12F748 -> 0x12F75A`, a stride of 0x12 rather than 6. The loop advances
`A0` by exactly 6 per visited source entry; the 0x12 gap proves that two
additional entries were consumed. The narrow watchpoint evidence does **not**
prove whether those entries wrote to object slots outside the watched range or
were consumed without emission. The 6-byte source stride is confirmed; the
emission/skip behaviour is still `UNRESOLVED` and must be settled by a widened
live trace or reachable-path control-flow trace.

**Still unresolved for part 2, each needing its source named before use:**
`A2`'s initial value, `D1`'s flip mask, the actor field at `+0x2E`, and the
screen origin at `(A5-0x64F4)`. Recover each from live evidence, then falsify the
whole emitter against the captured object lists — the 5,302-frame oracle is the
right check and it is what makes part 2 verifiable offline.

### Correction and live verification of the above (2026-08-18, same session)

The four unresolved inputs were investigated with a **live, register-capturing
MAME probe** (`tools/mame_probe_emitter_pc.lua`, untracked one-off diagnostic,
not a proof artifact) rather than more static disassembly, because the static
tool (`.deps/mame/actorprobe/disasm_full.txt`) is a naive linear scan with no
control-flow awareness and cannot be trusted to have found true instruction
boundaries on its own. Findings, each checked against real execution:

- **The static decode was right; the PC attribution needs a caveat.** Live
  capture confirms the writer PCs for the alien's own writes really are
  `0x000AA214` (X|Y) and `0x000AA216` (code|attr), exactly as milestone 1
  recorded — but those addresses are **not** store instructions; they are two
  instructions *after* the true stores at `0x0AA210`/`0x0AA212`. MAME's `pc`
  debugger symbol reports the position 2 instructions past the causing
  instruction for this store pattern, evidently a consequence of 68000
  prefetch/PC-update timing. **Anyone reading a raw watchpoint PC log from this
  project should expect a possible small forward skew, not assume the reported
  PC is the store's own address**, and should verify against live register
  capture as done here rather than trust it blindly.
- **`A0` stride and part-table base: CONFIRMED live.** `a0=0012F73C` at the
  first part, advancing by exactly 6 per part (`0012F73C -> 0012F742 -> ...`),
  matching the loop's per-part reads (`move.l (A0)+` for the 4-byte code|attr,
  then `move.w (A0)+` for the 2-byte `A2` advance amount).
- **`A2`'s initial value: CONFIRMED live, with corroboration.** `a2=0x1FDB68`
  for the alien's frame-4214 emission — consistent with the hypothesized
  `A2 = 0x1FD1C8 + word[0x1FD1C8 + selector*2]` formula, and `0x1FD1C8` is
  independently attested elsewhere in this project's own history as a known
  ROM layout-table base. `A2` advances by exactly 4 per part (two words: a
  `dx,dy` pair), confirmed across multiple consecutive part writes.
- **`D1` (flip mask): CONFIRMED live, matching the oracle.** `d1=0x00000020`
  (bit 5 set) for this alien at frame 4214, which is exactly `flip_x=1` — the
  flip state the oracle fixture already records for this actor. `D1`'s own
  source (which routine sets it, and from what actor field) is not yet traced.
- **`A4 == A6`: CONFIRMED live.** Both equal `0xFF9DC0`, the emitting alien
  itself — the two "different" actor pointers debated earlier are the same
  actor. This resolves the concern that `+0x2E` might belong to a separate
  camera/world structure: it does not, it is a field on the emitting actor.
- **The screen origin at `(A5-0x64F4)` (`0xFF1B0C`/`0xFF1B0E`, since
  `A5=0x00FF8000` is a fixed global anchor, confirmed constant across the
  entire captured watchpoint log): CONFIRMED to be a per-actor SCRATCH value,
  not a frame-global camera constant.** A write watchpoint on that address
  shows a single writer, `PC 0x000AA5E4`, firing once per actor per frame with
  `a4`/`a6` equal to whichever actor is about to emit — i.e. this is a "compute
  this actor's screen origin" step that runs immediately before each actor's
  own part-emission loop. Filtered to the alien (`a4=a6=0xFF9DC0`) at frame
  4214: origin X (the long's low word, used first, before the swap) = `259`,
  origin Y (the long's high word, used after the swap) = `201`. Reconciled
  against the oracle's slot-0 word `[0x8113,0x0099,...]`: `xpos=275`,
  `259 + delta_x(16) = 275`; `ypos=153`, `201 + delta_y(-48) = 153`. Both close
  with small, plausible per-part pixel offsets — this is corroborating evidence
  for the whole model, not just the origin address.
- **`+0x2E` (actor field OR'd into the X word): NOT YET RESOLVED, open
  contradiction.** Reading the alien's own `+0x2E` word directly from the
  existing `.deps/mame/collision_probe/workram.bin` capture at frame 4214 gives
  `0x0000`. But the observed output word is `0x8113` (priority bits set), and
  if `+0x2E` truly contributes nothing, the OR step cannot be the source of
  those bits from this actor. **Do not trust the `+0x2E` OR hypothesis as
  written until this is resolved.** The most likely explanations, in order of
  suspicion: (a) the priority bits come from elsewhere in the sequence not yet
  correctly transcribed for the flipped variant (the flipped loop subtracts a
  *part-local* computed width `D4`, derived from the part's own attr bits, not
  from `+0x2E`, before the OR — the width and the OR are two separate steps
  that may have been conflated in the part-1 write-up); (b) `+0x2E` is written
  dynamically earlier in the SAME frame by another routine and the offline
  capture's sample timing does not reflect that, unlike the scratch-origin case
  which was captured live at the exact write. **Next step to close this:**
  extend the live probe to capture `D2` and `D3` register values at the actual
  store PCs (`0x0AA210`/`0x0AA212`, not the reported `0x0AA214`/`0x0AA216`) for
  a handful of parts, and re-derive the OR/width contribution from those, rather
  than reasoning about it from static disassembly alone.

### `+0x2E` resolved: the contradiction was a route-mixing bug, not the game's

The `+0x2E` "open contradiction" above was investigated further in the same
session, live. Two decisive tests:

1. **A write watchpoint on `0xFF9DC0+0x2E` never fired** across the whole
   capture window. So the field is not a per-frame scratch value the way the
   origin is; whatever it holds, it holds constant through this window.
2. **A periodic live read of `0xFF9DC0+0x0D` and `+0x2E`, filtered to the
   correct route, gives `+0x0D=0x01` and `+0x2E=0x8000`** — both non-zero,
   both contradicting the earlier `0x00`/`0x0000` reading from the offline
   `.deps/mame/collision_probe/workram.bin` capture.

The offline capture was not wrong about its own route — **it is a different
route.** `collision_probe` replays the `round1_debug_overlays` input schedule
(right, gun, attack, jump on a fixed schedule, debug DIPs enabled);
the object-emission work uses the `replay4200` anchor plus a short `P1 Left`
tail. Both are internally deterministic and both are legitimate, but "source
frame 4214" names a different game state in each — different player input
history means a different alien, a different pose, or both, sitting at the
same 0xC0-grid address by frame 4214. Reading one route's capture and treating
it as ground truth for the other route's frame numbering was the actual bug,
not anything wrong with the emitter model. **This is now a standing caution for
this project:** two different capture routes must never be cross-referenced by
source-frame number as if they shared a timeline.

With `+0x2E=0x8000` (the correct, route-matched live value) and the previously
established width formula, the per-part X/Y arithmetic was checked against the
five watched entries of the frame-4214 emission. The first three can be
reconstructed independently with the currently understood source walk; the
last two remain blocked by two intervening source entries. Inputs are the ROM's
own `dx/dy` table (read directly from `decrypted_program_2m.bin` at the
live-captured `A2` addresses) plus the confirmed origin, width and `+0x2E`:

```text
X_masked = (origin_x - width - dx) & 0x3FF ; width = 16 * (((attr>>8)&0xF)+1)
X_final  = X_masked | 0x8000                ; 0x8000 = confirmed +0x2E value
Y_masked = (origin_y + dy) & 0x3FF
Y_final  = Y_masked                         ; no OR for Y ("ori.w #0" is a no-op)
```

**Slots 0, 1 and 2 match exactly**, both X and Y. The expected X/Y output was
not used as a calculation input: `dx/dy` came from ROM and origin/`+0x2E` came
from route-matched live capture. The code/attribute words were already known
from the captured oracle, so this proves the geometry formula, not a complete
ROM-to-object decoder:

| slot | dx | dy | width | X (computed) | X (actual) | Y (computed) | Y (actual) |
|---|---|---|---|---|---|---|---|
| 0 | -48 | -48 | 32 | `0x8113` | `0x8113` | `0x099` | `0x0099` |
| 1 | -48 | -32 | 80 | `0x80E3` | `0x80E3` | `0x0A9` | `0x00A9` |
| 2 | -16 | -16 | 32 | `0x80F3` | `0x80F3` | `0x0B9` | `0x00B9` |

This confirms the geometry formula for those three entries: origin, per-part
width, the `+0x2E` OR, and the flipped variant's subtract-not-add convention.
It does not close code/attribute derivation, the full source walk, or entries
3/4; the oracle still supplies code/attribute to the current C test.

**Slots 3 and 4 (in watch-window order) do not yet match.** The raw source
address gap is proven: `0x12F75A - 0x12F748 = 0x12`, so two full 6-byte source
entries were visited between the third and fourth observed writes, each with
its own `A2` advance word. What the narrow capture cannot distinguish is whether
those entries emitted outside `0x7080A0..0x7080CE` or a conditional path
suppressed their writes. Getting entries 3/4 and the complete actor emission to
match requires a widened actor-scoped object-RAM trace plus reachable control
flow. Do not bake either explanation into the walker before that evidence.

A related loose end, resolvable the same mechanical way: the palette
contribution at actor `+0x0E` was **inferred, not yet live-read** — working
backward from slot 0's known raw and final attr bytes gives `+0x0E=0x11`,
which independently matches milestone 1's original palette observation
(`palette 0x11`) for this same actor/pose. A live read would make this
`CONFIRMED` rather than `DECODED-by-inference`.

**The part-table header (budget/count/selector, 3 words preceding the first
part) was not located.** The address hypothesized by simple 6-byte backward
offset from the first part (`0x12F732`) does not hold a plausible header
(`count` decoded as `65482`, not a small integer). This does not block the
confirmed slots — the loops themselves never re-read the header, only walk
parts sequentially — but the header format is still needed to determine a
part count from ROM data alone rather than from watchpoint-observed gaps, which
matters once this moves from "confirmed for one captured pose" to "general for
any pose".

### The object-entry geometry formula is now C, tested; `bsr $0AA59A` identified as the origin routine

`avsp_emit.h`/`.c` implements the confirmed formula
(`X = ((origin_x - width - dx) & 0x3FF) | or_value`, `Y = (origin_y + dy) &
0x3FF`) and `tests/avsp_emit_test.c` checks it against parts 0-2 exactly, using
ROM-read `dx`/`dy` and the already-proven oracle `code`/`attr` — wired into
`test.ps1`. Committed and cross-compiles clean for SH-2 (confirmed by a Saturn
build during this session); not called from `main.c` yet, same as
`avsp_actor.c`/`avsp_anim_script.c`.

**New finding: the per-actor origin scratch is written by `bsr $0AA59A`, called
once per dispatch from the SAME entry point that reads the 3-word header**
(`0x0AA00E..0x0AA038`). Disassembled in full:

```text
0aa59a: moveq #0, D1
0aa59c: move.b (0xF,A4), D1        ; actor facing byte
0aa5a0: move.l (A0)+, D2           ; consumes ONE part-table entry
0aa5a2: move.w (0x14,A4), D3       ; actor world_y
0aa5a6: sub.w  (-0x27C,A5), D3     ; minus a fixed camera/scroll-Y anchor
... (facing-conditional add/sub of D2, giving the Y half of the origin)
0aa5c4: move.w (0x10,A4), D3       ; actor world_x
0aa5c8: sub.w  (-0x278,A5), D3     ; minus a fixed camera/scroll-X anchor
... (facing-conditional add/sub of D2, giving the X half of the origin)
0aa5e0: move.l D3, (-0x64F4,A5)    ; the confirmed origin scratch write
0aa5e4: lsl.b  #5, D1              ; the confirmed D1 flip mask (bit 5 = facing)
0aa5e6: rts
```

This resolves two things at once: **`D1`'s own source** is the actor's own
facing byte at `+0x0F`, shifted into bit 5 — so the flip mask is not a
mystery input, it is derived from a field S1's actor record already carries.
And **the origin computation itself** is now readable: it is `actor world
position minus a fixed camera/scroll anchor` (two constants at `(A5-0x27C)`
and `(A5-0x278)`, not yet read live), adjusted by one part-table long (`D2`)
whose role is not yet named.

**Still not resolved: exact part count / the skip mechanism.** `bsr $0AA59A`
consuming one part-table entry means the header is further back than the
`extra=6` position tried previously. A systematic search over header
candidates at `extra=0..18` bytes before part0 finds several with plausible
small `(budget, count, selector)` triples (`extra=10`: `9,3,39`; `extra=12`:
`6,9,3`; `extra=14`: `12,6,9`; `extra=16`: `0,12,6`) but **none give a total
part count consistent with the 5 confirmed object-buffer writes** once the
1-entry `bsr` consumption is added back. The 2-entry gap between slots 2 and 3
observed earlier in this session is therefore still unexplained by a single
extra `bsr` call; either the header format assumed here (3 words,
budget/count/selector) is wrong, or something else consumes entries
mid-loop. This needs either a reachable-path control-flow graph built with
Capstone as the instruction decoder
(the naive flat scan `.deps/mame/actorprobe/disasm_full.txt` has already
produced one confirmed misalignment this session, at
`0xAA732`-adjacent addresses) or a live disassemble-at-runtime pass, not more
hand-parsing of the flat scan.

None of this is wired into any committed C code yet; `avsp_collision.c` and the
runtime remain untouched. This is discovery evidence for the still-open part 2
of S2's integration, recorded so the next session does not have to re-derive
what is now confirmed, and does not repeat either the `+0x2E` mistake, the
cross-route mixing that caused it, or re-search header offsets already tried
and ruled out here.

**Capability Gate 1 stays 0/7; the full-game goal stays 0/9.**

### The "2-hidden-entries" mystery is resolved, the attr transform is fixed, and the pose-to-header chain is derived (2026-08-18, later same day)

Body A/B of `docs/NEXT_AGENT_PROMPT.md` made four further findings, all live-verified
against the route-matched `replay4200`/`enemy_actions` capture (never mixed with
`collision_probe`), before consulting the oracle only for final comparison:

**1. No entries are skipped.** What earlier sessions read as "2 hidden/skipped
part-table entries between observed object-buffer writes 2 and 3" is actually the
boundary between **two independently-dispatched groups**: a wide write-tap over
the whole object buffer (`0x708000`, length `0x2000`) plus a loop-top breakpoint
at `0x0AA1DC` (the confirmed `move.l (A0)+,D2` instruction) showed a clean 1:1
correspondence between loop iterations and object-buffer writes, with zero
unaccounted iterations, across both oracle frames (4214, 4253). `MEASURED` via
`tools/mame_trace_emitter_full.lua` (untracked one-off, kept per convention).

**2. The group header format is proven exactly.** Each group has its own 3-word
header (`+0x00` budget u16, `+0x02` count u16 — the *exact* raw iteration count,
not count-1 — `+0x04` selector u16, resolved through the `0x1FD1C8` table via
`selector*2` to give the per-group A2/dx-dy-table base) followed by one 4-byte
long consumed by `bsr $0AA59A` (the origin routine) before the first part.
Verified exactly for 4 independent group instances (2 groups x 2 oracle frames).

**3. Origin is per-GROUP, not per-actor-frame.** `bsr $0AA59A` runs once per
group and can produce a different `(origin_x, origin_y)` for a later group in the
same actor-frame (frame 4214: group1=(259,201), group2=(321,203); frame 4253:
group1=(319,190), group2=(379,203)), captured via a fourth instrument watching the
origin scratch write at `(A5-0x64F4)`.

**4. The attr word needs a byte transform before use.** The raw ROM attr is a
template, not the stored value: the real code applies
`andi.b #0xE0,D2` (mask low byte to bits 5-7) then `add.b (0xE,A4),D2` (add the
actor's palette byte) then `eor.b D1,D2` (XOR the facing-derived flip mask),
*before* using the result both as the output attr and (via `move.w D2,D4`) for
width. With this applied, `tools/decode_avsp_object_stream.py` reproduces
**all 10 object entries across both oracle frames exactly** (code, attr, x, y —
zero oracle values used as calculation inputs, only for comparison).
`palette_byte`/`flip_byte` are still caller-supplied per-actor live-trace inputs
(`0x11`/`0x20` for this street-alien instance), not yet derived from a general
actor-record read.

**5. The pose-to-group-header chain is derivable from ROM alone (n=2, not yet
generalized).** The actor's `+0x1C` field (already established by the S2
animation-walk validation as the live animation-record/pose pointer) led to a
pose record whose `assembly` field (per `avsp_anim_script.h`, pose `+4`) plus
`4` gives the first group's header address exactly, in both oracle cases
(`0x12F72A+4=0x12F72E`; `0x12FEBC+4=0x12FEC0`). The second group's header is
the first group's header plus `12 + count*6` bytes (its own 6-byte header +
4-byte bsr-consumed long + `count` 6-byte parts + a constant 2-byte gap whose
bytes were `0x0006` in both instances) — also exact in both cases (30 bytes and
24 bytes respectively). **Not yet resolved:** the 4 bytes immediately before the
first group's header are a *fixed* constant pair (`0x000c, 0x0006`) identical in
both poses, so they do not encode "how many groups to dispatch" — Body A's live
trace independently established exactly 2 dispatch calls for this actor, but
nothing ROM-side yet proves that count generalizes to other poses/actors. A
plausible-looking third header exists at the same stride past group2 in both
cases but is not actually called per the live trace, so it is either an unused
table continuation or belongs to a different pose — do not assume an N-group
loop from this alone.

**Still blocking a ROM-only (no-live-trace) decoder, in priority order:** the two
camera-anchor constants inside `bsr $0AA59A` at `(A5-0x27C)`/`(A5-0x278)` (not
yet read live — needed to compute origin from actor world position without a
live capture), confirming the per-actor-type dispatch count generalizes beyond
this one actor/pose pair, and deriving `palette_byte`/`flip_byte` from the actor
record rather than supplying them by hand. The declared-eligible-subset run
against the full 5,302-frame oracle (`data/avsp_sprite_demand.json`) required by
`NEXT_AGENT_PROMPT.md` Body B item 6 has **not** been done yet — only the 2
hand-verified frames (10 entries) are proven exact so far.

Committed: `tools/decode_avsp_object_stream.py` (attr-transform fix) and
`data/avsp_object_stream.json` at `b6f5a4e`.

## Status across S1-S6 (2026-08-18, end of session)

| Step | Status |
|---|---|
| S1 actor spine | **PASSED.** 481,566 actor-field loads, 0 mismatches; the collision predicate ported to C reproduces the Python falsification exactly on all 8 counters. |
| S2 animation walk | **VALIDATED.** Interpreter predicts 23,676 of the game's own frames exactly free-running from one seed; 614 records extracted to 63 spans (10 KB), proven to reproduce the full 2 MB image on every counter. |
| S2 object emitter | **X/Y geometry formula confirmed and coded** for 3/5 observed object entries. `dx/dy` are ROM-derived and expected X/Y are not calculation inputs, but origin/`+0x2E` are route-matched live values and code/attr are supplied by the oracle; this is **not** a complete ROM-only decoder. The general part-table walk remains open (header/count/advance/emission mechanism); **not called by `main.c`**; **VDP1 per-object renderer not started**. |
| S2 integration into `main.c` | **Not started.** No live actor in the shipped runtime carries an `AvspActor` or ticks `avsp_anim_frame_tick`. A same-session proof-of-concept overlay was built, boot-tested successfully (real Round 1 combat played through to the Round 2 title without regressing), but was inconclusive on visual confirmation and was removed before committing rather than left in an unverified state. |
| S3 (widen to full cast) | Not started; depends on S2. |
| S4 (collision integration) | Not started; `avsp_collision.c` exists and is proven (S1) but nothing calls it from gameplay; depends on S2 for live selectors. |
| S5 (AI/PRNG) | Not started. |
| S6 (hardware) | Not started. |

**The current normal-release build (no debug flags, no autoplay) is the one to
hand to a person who wants to actually play the game** — it is the existing
capture-derived pipeline, unaffected by any S1/S2 work this session, and it
plays through Round 1 to Round 2 as already documented in `README.md`. None of
this session's ROM-driven work has reached that build's rendering yet.

## S2 animation walk — interpreter VALIDATED, integration open (2026-08-18)

S2 has two halves. The **validation** half is done; the **integration** half
(linking the interpreter into the Saturn build, driving pose selection from
`+0x1C`, and producing the object list) is not started.

The oracle is the capture itself: every actor's `+0x1C` is the live
animation-record pointer, sampled once per source frame, so a faithful reading
of the script format must reproduce the pointer's movement.
`tests/avsp_anim_walk_test.c`, wired into `test.ps1`, over the same two
full-work-RAM windows:

**Check A — permitted transitions.** Of 32,624 frame-to-frame observations:
26,050 holds, **5,738 moves the script predicts exactly**, 32 external re-points
that coincide with an observable actor event, and **804 unexplained** — 87.7% of
all non-hold transitions predicted.

**Check B — free-running prediction.** Seeded once at a pointer change and then
ticked with no further help: 1,435 runs, 1,188 predicting at least one frame,
**23,768 frames predicted exactly**, and a **longest exact run of 732 frames**.
This is the check that matters, because it exercises hold duration and not just
control flow. An interpreter with the wrong record size, duration field or jump
rule produces runs of one to three frames, not twelve seconds of frame-perfect
animation.

Per actor type (script moves / unexplained / longest exact run):

| type | moves | unexplained | longest run |
|---|---|---|---|
| 0 (player) | 390 | 121 | 71 |
| 4 | 319 | 12 | 37 |
| **12 (street alien)** | **1,897** | **299** | **160** |
| 20 (Stalker) | 178 | 118 | 8 |
| 24 | 1,921 | 134 | 278 |
| 28 | 896 | 54 | 240 |
| 32 | 0 | 3 | 732 |
| 36 | 137 | 63 | 60 |

**What the 804 unexplained are, and are not.** They are not interpreter errors —
check B rules that out. They are the game re-pointing an actor's animation for a
reason the script does not contain: an AI decision, an action change, an input.
The test's "external" classifier only catches re-points that coincide with a
state or hit-value change, which is why most land in "unexplained" rather than
"external". For street aliens that is roughly one re-point every 78 actor-frames,
which is what a beat-'em-up enemy switching between approach, attack and recover
looks like. **Supplying those decisions is S5**, and until S5 exists the runtime
will need to seed the pointer from somewhere on every action change.

**Check C — the shipped record subset: PASS, exactly.** The Saturn build cannot
carry the arcade program image, so it carries only the records the game actually
reaches. `tools/gen_avsp_anim_records.py` walks the script's own control flow
from every observed `+0x1C` seed and extracts **614 reachable records, 10,244
bytes in 63 spans**, each keeping its original source address; the interpreter
gained an `AvspAnimSpan` sparse form so reads resolve by address in either
storage. Re-running the identical measurement over those 10 KB reproduces the
full 2 MB image **on every counter, including every per-type breakdown**. That
is the round-trip proof that the extraction is complete and correctly addressed.
`data/avsp_anim_records.json` is the tracked manifest (addresses, counts and
hashes, no record bytes); `generated/avsp_anim_records.h` is git-ignored because
it contains program-image bytes.

**Remaining in S2:** `avsp_actor.c`, `avsp_anim_script.c`, and `avsp_emit.c` are
already in `SRCS` and cross-compile, but are not called by `main.c`. First
resolve the general part-stream header/count/advance/emission mechanism and
require exact agreement over the declared eligible population of the 5,302-
frame oracle. Then drive one street alien from actor `+0x1C`, produce its
semantic object list, and render it through the real per-object VDP1 path. The
interpreter advances an animation but does not choose one, so until S5 supplies
the decisions the runtime must seed the pointer on every action change and label
that bridge `ADAPTED`.

**Capability Gate 1 stays 0/7; the full-game goal stays 0/9.**

## S1 actor spine — PASSED (2026-08-18)

**Terminology note:** "Gate" means **Capability Gate 1**, the seven-condition
acceptance contract. A slice step's own pass criteria are **checks**.

The first time this project's decoded data does anything. Host-only; no shipped
runtime behaviour changed, no Saturn build, no emulator run.

**New files.** `avsp_actor.h` / `.c` (the native actor record),
`avsp_collision.h` / `.c` (the C port of the game's overlap test and guards),
`data/avsp_actor_layout.json` (tracked, evidence-labelled field map naming the
routine address that proves each field), `tests/avsp_actor_test.c`, wired into
`test.ps1`. `tools/decode_avsp_collision.py` now also emits an
`avsp_collision_families` lookup so C can resolve a family from an actor's
`+0x50`; **only the 10 trusted families are emitted**, the 10 suspect ones are
deliberately omitted.

**Check 1 — actor fields: PASS.** 481,566 actor loads across the two full-work-RAM
windows (4201–5500 and 13000–14600), **0 field mismatches**. Every field is
re-read straight from the capture and compared, not sampled.

**Check 2 — the collision predicate in C: PASS, exactly.** The C port reproduces
`tools/verify_avsp_collision.py` on all eight counters:

| counter | C | Python |
|---|---|---|
| pairs, active but no overlap | 21,908 | 21,908 |
| pairs, overlap latched | 25 | 25 |
| pairs, overlap guarded | 2,516 | 2,516 |
| pairs, overlap unguarded | 24 | 24 |
| latch explained, defender side | 25 | 25 |
| latch explained, attacker side | 19 | 19 |
| latch, simultaneous broadcast | 8 | 8 |
| latch, unexplained | 4 | 4 |

Two independent implementations — Python over the raw program image and
captures, C over the generated header and the actor record — agree on every
number. That is a cross-implementation verification, not a re-run.

**One real difference found and fixed during the port**, worth recording because
it would have silently changed the population under measurement: the C initially
counted 29,278 non-overlapping pairs against Python's 21,908 while every
geometry counter already matched. The cause was the **participation contract**,
not the geometry — the reference implementation treats an actor as taking part
only when it is in a live state *and* carries a usable animation record *and* a
usable table-set pointer. Aligning the C to that contract made all eight
counters agree. The lesson generalises to every later port: geometry agreeing is
not the same as the two implementations measuring the same population.

**What this does NOT close.** Capability Gate 1 stays **0/7** and the full-game goal stays
**0/9**. Nothing ROM-driven has reached the Saturn runtime: `capability_model.c`
still uses its inferred lane/reach checks and the boss 21/55/97 and Stalker
schedules, and `avsp_collision.c` runs beside it, not in front of it. Swapping
the runtime over is S4, and it needs S2 first so the selectors come from a live
animation record instead of a capture.

**Reproduce:**

```powershell
.	est.ps1
```

or directly, under WSL gcc with `-std=c90 -pedantic -Wall -Wextra -Werror`:
`gcc ... avsp_actor.c avsp_collision.c tests/avsp_actor_test.c -o build/avsp_actor_test && ./build/avsp_actor_test`

## Sprite demand measured (2026-08-18)

AvP and the reference title run on **the same CPS2 arcade hardware**, so the
source primitive is identical and only volume differs. The demand half of the
renderer question was therefore answerable offline, from AvP's own captured
object lists, with no Saturn code and no renderer prototype.

`tools/measure_avsp_sprite_demand.py` -> `data/avsp_sprite_demand.json`
(deterministic, counts only, no graphics data), over **5,302 captured frames**
across the street wave, Stalkers and the Chrysalis boss, decoding fields exactly
as MAME 0.289 `cps2_render_sprites` / `find_last_sprite` do:

| Measure | Peak | Mean |
|---|---|---|
| objects per frame | 86 (frame 5800) | 40.7 |
| **16x16 tiles per frame** | **909** (frame 5776) | 346.3 |
| **live 16-colour palettes per frame** | **13** (frame 4923) | 6.5 |
| distinct tile codes per frame | 547 (frame 4159) | 251.9 |
| largest single object | 55 tiles (frame 4157) | — |

- **Colour RAM is not the constraint.** 13 live banks at worst; Saturn CRAM
  holds 128 sixteen-colour banks in 5:5:5 mode 1. The risk that could have
  killed a per-tile pipeline is measured and comfortable. The current eight-bank
  allocation, sized for precomposed per-palette cels, is the tight thing.
- **AvP's object list is not shaped like the reference title's.** Across 215,646
  captured objects, **83.6% are blocked sprites averaging 8.51 tiles**; only
  16.4% are 1x1. So granularity is worth ~10x: one command per 16x16 tile costs
  **909** commands at peak, one command per CPS2 object costs **86**. Per-object
  is also the more faithful mapping - the object entry is the hardware's unit,
  and every AvP object fits one VDP1 normal sprite (largest is 55 tiles; VDP1
  reaches 504x255). The reference title's per-tile shape is therefore **not
  copied**; its representation half (16-colour bank mode, flip in `CMDCTRL`,
  jump-next linked list, source order as draw order) transfers directly.
- **The remaining question is VDP1 throughput at the chosen granularity**
  (`UNRESOLVED`). Fill is the same either way (~233k pixels at peak, same pixels
  drawn); command count is not. Probe: slice V emits per-object commands, keeps
  per-tile as the fallback, and measures real frame time at the peak frame 5776.

**Correction to milestone 1's report.** `decode_x` in
`tools/analyze_street_alien_object_emission.py` read block width from the X word.
Per MAME, block width/height are ATTR bits 8-11 and 12-15; the X word carries
only priority and position. The decoder and `data/street_alien_object_emission.json`
are corrected, now also reporting `block_width_tiles` / `block_height_tiles`.
The emission gate is unaffected and still passes 20/20 on both frames — it
compares raw words, not decoded fields.

## Official Saturn reference-port findings (research lane, 2026-08-18)

**There is no Saturn Alien vs Predator.** Capcom never shipped one; this port is
the first. No phase is gated on matching a Saturn AvP, no such reference exists
to look for, and the fidelity oracle is always MAME's CPS2 `avspu` under
identical input.

The only official CPS2-to-Saturn port available for study is a **different
game**: Marvel Super Heroes vs. Street Fighter, in the isolated research lane at
worktree `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-MSHvSF`, branch
`codex/mshvsf-reference-lane`, immutable checkpoint **`dc5d3ea`**. That lane is
not merged and must not be.

**Findings that have passed an AvP validation probe: none yet.** Per the lane's
own promotion gate (`docs/MSHVSF_TO_AVP_TRANSFER_MATRIX.md`), a reference result
may change AvP's *method* or add a probe, but cannot close an AvP condition
without AvP evidence. Two items crossed as method only:

1. **Rendering-granularity hypothesis (`INFERRED`, drives phase A).** On the
   reference title every reachable VDP1 command at all four measured anchors is
   a 16x16 normal sprite in colour-bank mode, linked jump-next, with flip in
   `CMDCTRL`. That is the shape in which a source assembly *is* the command
   list, which is what would let an AvP actor carry a ROM record instead of a
   picture. **Falsified by:** AvP's own phase-A measurement showing a per-tile
   pipeline exceeding AvP's colour-RAM or VDP1 budget on the same route. AvP's
   cast size, sprite dimensions and scrolling-beat'em-up load differ from a
   two-character fighter's, so the answer can legitimately differ.
2. **Evidence-label discipline (`ADAPTED`, adopted).** The lane's
   `MEASURED / DECODED / INFERRED / ADAPTED / UNRESOLVED` labelling, with
   `INFERRED` requiring a falsifier and `UNRESOLVED` requiring a probe, is now
   recorded in the parity plan for new AvP artifacts. Adopted because two
   consecutive AvP sessions lost time to unlabelled metadata that was wrong.

**No MSHvSF timing values, gameplay constants, addresses, package sizes, command
counts, colour-bank counts, code or assets were imported.** The reference
numbers (1,233 drawn commands, 296-334 reachable, 772 stored slots, 128
populated banks with 12-14 live) are cited here only as the reference lane's
measurements of a different game; they are explicitly **not** AvP budgets.

## Capability Gate 1 — collision records (milestone 2, 2026-08-18)

**Milestone 2 result: NOT CLOSED. The record format is decoded from the game's
own routines and survives a controlled falsification test, but native collision
is deliberately UNCHANGED.** Gate 1 stays **0/7**; full-game stays **0/9**. The
blocker is named at the end of this section and is structural, not a defect.

### The format, read out of the code (not inferred)

Caller `0x01CF84..0x01CFC6`, duplicated at `0x01D064..0x01D0A6`:

```text
A0 = [A6+0x1C]        attacker animation record
D2 = A0[+9]           attack-box selector; 0 => actor cannot hit
A0 = [A1+0x1C]        defender animation record
D3 = A0[+8]           hurt-box selector;   0 => actor cannot be hit
A3 = [A6+0x50]  ; A3 += word[A3+2] ; A3 += D2*16   -> attack entry (stride 16)
A2 = [A1+0x50]  ; A2 += word[A2+0] ; A2 += D3*8    -> hurt entry   (stride 8)
bsr 0x01D25E          -> overlap test; the caller's "bhi" means no overlap
```

Overlap test `0x01D25E..0x01D312` is **three axes of centre + half-extent**, not
left/top/right/bottom:

- depth: `d = (hurt[+4] + def[+0x18]) - (atk[+4] + atk_actor[+0x18])`, miss when
  `|d| > atk[+5] + hurt[+5]`; `d` is kept **signed** for the Y axis;
- x: `atk[+0]` negated when the attacker's `+0x0F` facing byte is non-zero, plus
  `+0x10`; same for the defender; miss when the separation exceeds
  `atk[+2] + hurt[+2]`;
- y: `atk[+1] + d + atk_actor[+0x14]` versus `hurt[+1] + def[+0x14]`; miss when
  the separation exceeds `atk[+3] + hurt[+3]`. The depth delta feeding the Y
  axis is the belt-scroller's depth-to-screen projection.

Record bytes: `+0` signed x centre, `+1` signed y centre, `+2`/`+3` unsigned
x/y half-extents, `+4` signed z centre, `+5` unsigned z half-extent. Hurt `+7`
is a role byte read at `0x01D314` (meaning **not** proven). Attack `+0x0A` is
the knockback treatment, `+0x0E` is the value written to the defender's `+0x2C`
on a hit — and, per `0x01CFD2..0x01CFDA`, to the **attacker's** `+0x2C` too when
its own is still zero. That second write is why a naive "who got hit" classifier
mis-scores the evidence.

Coordinates are actor-local, so one record set serves every actor sharing the
family pointer at `+0x50`. Actor records are `0xC0` apart on one grid anchored at
the player slot `0xFF8380` (confirmed: every distinct A4/A6 in the milestone-1
watchpoint log lands on it).

### Decoded coverage

`tools/decode_avsp_collision.py` → `data/avsp_collision.json` (tracked,
coordinates only, no ROM bytes) and `generated/avsp_collision.h` (ignored).
20 family table-sets were censused; **10 are trusted** and 10 are flagged
`suspect_not_a_box_family` because their attack table does not follow their hurt
table at a whole number of 8-byte entries — for those the two words at `+0/+2`
are probably not box offsets at all, and the report says so rather than
publishing invented boxes. Trusted families include the player (`0x11AE02`,
24 hurt entries exact, 12 attack observed), street aliens (`0x130AC8`, 16 hurt
exact, 9 attack observed; also `0x130984`), the Stalkers (`0x06D516`,
`0x06DE6C`) and the boss family (`0x13E97A`, 34 hurt exact, 15 attack observed).
Hurt counts are **exact** (the adjacency gap proves them); attack counts are an
**observed bound** from the censused route, not a proven table length.

### Falsification (the controlled hit/whiff test)

`tools/verify_avsp_collision.py` re-implements the game's test from the tracked
report plus live actor context, over two bounded full-work-RAM captures
(street route 4201–5500, boss route 13000–14600):

- **whiff side: 21,908** `(attacker, defender, frame)` triples had an active
  attack selector and an active hurt selector with **no** box overlap, and not
  one produced a hit. A wrong coordinate convention, facing transform or depth
  axis would show up here immediately;
- **hit side: 44 of 56** `+0x2C` latch events are explained exactly — same pair,
  same frame (or the one before), and the attack record's `+0x0E` equal to the
  latched value — 25 defender-side and 19 attacker-side;
- 2,516 overlapping pairs produced no latch and are accounted for by the guards
  the caller actually tests (defender state ≠ 1, defender `+0x70` set, or the
  per-attacker latch at defender `+0x68 + attacker[+0xD1]` already equal to the
  attacker's `+0x67`); 24 overlapped un-guarded without latching (1% residual,
  most likely intra-frame ordering the end-of-frame sample cannot see);
- **12 latch events are not explained** and are named, not smoothed over: 8 are
  one simultaneous same-value broadcast at frame 5463 (all live actors latch at
  once — not a pairwise box event, path unidentified); 4 are singles — frame
  4250 value 8 and frame 5481 value 12 on the street route, and a player/boss
  pair at frame 13942 value 3. The two street singles line up with the player's
  gun and a Stalker contact, i.e. **the projectile/weapon path is a different
  routine that is not decoded here.**

`tools/test_avsp_collision.py` checks the report's structure and anchors: all
pass, including the independent prediction that **selector 0 is an inactive
record in every trusted family** — the callers reject selector 0 before any
table read, and nothing in the decoder forces that outcome.

### Evidence (SHA-256)

- `data/avsp_collision.json`
  `49ce678bee49d331a3b9e6cee97708b7644c5b0727de477ffc89671bf64bd78c` (486,317 B),
  deterministic: `--verify-deterministic` re-decodes in-process and agrees.
- `.deps/mame/collision_probe/workram.bin` (ignored, 42,598,400 B)
  `52b710835e9fbcd279a04a9e1ea284ded9132bdc6ea0b9ce9cf0f845669d6f59`.
- `.deps/mame/collision_probe_boss/workram.bin` (ignored, 52,461,568 B)
  `6896ab7feddb3e7b9f4638bab74794c14fd239be79cce78ce6ab80f829500246`.
- Program image (ignored, private, 2,097,152 B)
  `0c14f4094d25787401aa949657620ff495ae8606c1cfd8ae2d059b94c3d478e9`.

The pre-existing `.deps/mame/round1_debug_hitboxes/actor_state.bin` was tried
first and is **insufficient for attribution**: it dumps only `0xFF8300..0xFF8FFF`
and `0xFFA000..0xFFBFFF`, so every enemy actor slot below `0xFFA000` is absent.
`tools/mame_capture_collision_probe.lua` replays that capture's route verbatim
and dumps the whole work RAM instead, with no screenshots.

### Exact reproduction commands

```powershell
$env:AVSP_CP_CAPTURE_ROOT=".deps/mame/collision_probe"; $env:AVSP_CP_STATE_NAME="avspu_stage1_debug_hitboxes"; $env:AVSP_CP_ROW2="0x80"; $env:AVSP_CP_FIRST_FRAME="4201"; $env:AVSP_CP_FINAL_FRAME="5500"
.deps\mame\mame0289\mame.exe avspu -rompath . -video none -sound none -nothrottle -skip_gameinfo -cfg_directory .deps\mame\cfg_debugoverlay -nvram_directory .deps\mame\nvram_debugoverlay -state_directory .deps\mame\captures -snapshot_directory .deps\mame -autoboot_delay 0 -autoboot_script .\tools\mame_capture_collision_probe.lua
```

(repeat with `collision_probe_boss` / 13000 / 14600), then:

```powershell
python tools\decode_avsp_collision.py --rom .deps\mame\actorprobe\decrypted_program_2m.bin --census-workram .deps\mame\collision_probe\workram.bin --census-workram .deps\mame\collision_probe_boss\workram.bin --verify-deterministic
```

```powershell
python tools\verify_avsp_collision.py --report data\avsp_collision.json --rom .deps\mame\actorprobe\decrypted_program_2m.bin --workram .deps\mame\collision_probe\workram.bin --first-frame 4201 --workram .deps\mame\collision_probe_boss\workram.bin --first-frame 13000 --max-unexplained 12
```

### Why native collision was NOT changed — the blocker

The records are indexed by **animation-record bytes `+8` and `+9`**, read
through the actor's live ROM animation-record pointer at `+0x1C`. The native
runtime has no such pointer: pose *selection* for the player, street aliens and
Stalkers still walks the capture-derived clip/step tables in
`generated/avsp_boss_animation.h` and the `/SPR4/*.RLE` archives, and only the
Chrysalis *composition* path touches ROM data at all (milestone-1 / condition-1
status, unchanged). So there is no runtime value that can index these tables.
Consuming the boxes today would mean hand-mapping each native pose to a ROM
selector — exactly the "pose-specific replacement constants by hand" this
assignment forbids, and it would bake a second inferred layer under a
ROM-derived name.

**The dependency is phase B**, which links ROM animation records into the
runtime. Once an actor carries its live record pointer, the selector bytes and
therefore these boxes follow directly, and `capability_model.c` can drop the
21/55/97 boss schedule and the Stalker schedule in one coherent change.

**Next bounded command for the agent that resumes this:** decode the
projectile/weapon collision path (the frame-4250 value-8 and frame-5481 value-12
singles above) by putting stock-MAME watchpoints on the defender's `+0x2C` byte
across those two frames and recording the writer PC — that is the one remaining
collision path in Round 1 that this decode does not cover.

`capability_model.c`, `tests/capability_model_test.c` and every build artefact
are untouched by this body. No build, soak, ISO or emulator gate was run,
because no native code changed and running them would prove nothing about this
work.

## Capability Gate 1 — street-alien emission (2026-08-18 execution)

**Milestone 1 result: PASS. Frames 4214 AND 4253 both reproduce 20/20** from a
fresh deterministic run, independently located and then compared to the oracle.
Gate 1's seven acceptance conditions remain **0/7 closed**; this milestone
advances conditions 1 and 5 and does not close either.

**What the instrument does.** The wrapper/watchpoint/analyzer are scenario-
parameterized (no logic tied to actor `0xFFA000`, object base `0x7080A0`, frame
4253, or the five slots). The Lua installs exactly 20 word-write watchpoints at
`0x7080A0..0x7080C6` (bank 1; no `0x7000A0` watchpoints) plus one bank-select
watchpoint at `0x8040E0`, and per source frame in the window dumps
`workram_<src>.bin`, `objbuf_<src>.bin` (the logical write buffer at
`0x708000`) and `objact_<src>.bin` (the ACTIVE/display share — `:objram1` when
the `0x8040E0` bank bit is 0, else `:objram2`). The analyzer locates the alien
independently (first run of five consecutive `0x4xxx` codes), decodes
X/Y/code/attr, matches the oracle, attributes each frame's decoded words to the
watchpoint burst that wrote them, and records SHA-256 of every dump.

**Why 4253 failed earlier this session, and the correction.** The failure was in
the instrument, not the fixture. Two defects, both now fixed:

1. **Off-by-one source-frame label.** The watcher labelled notifier call `k` as
   source frame `state_frame + k`, but call 1 only requests the state load, so
   call `k` ends source frame `state_frame + k - 1`. Every dump was named one
   frame too high. Verified by comparing dumps against the oracle route's own
   work RAM (`.deps/mame/enemy_actions/workram_*.bin`): the old labels matched
   original frame `N-1`; the corrected labels match `N`.
2. **Unreplayed post-anchor route tail.** The oracle came from the cold-boot
   route in `tools/mame_capture_enemy_actions.lua`, whose route does **not**
   stop at frame 4200: it presses **P1 Left at 4201, releases at 4210**, and
   holds **`0xFF83C1 = 0x65`** (P1 health) every frame from 4200 on. Loading the
   4200 anchor and running with no inputs is a different route — the player never
   turns, so the scroll origin and the alien's approach diverge. The watcher now
   replays that tail (parameterized: `AVP_OE_TAIL_DIR`, `_ON`, `_OFF`,
   `AVP_OE_TAIL_HOLD_ADDR`, `_VALUE`).

The prior session's conclusion that the fixture's 4253 was captured under an
unknown route was wrong: the route is `mame_capture_enemy_actions.lua`, and it
reproduces exactly.

**Independent proof that the run reproduces the oracle route.** Against the
oracle route's own dumps, over the whole window 4213–4254:

- Work RAM differs by **exactly 1 byte per frame**, `0xFF8392` (`0x70` vs
  `0x30`) — the low byte of a sub-pixel fraction whose integer half
  (`0xFF8391`) agrees. It is a residue of the state save/load boundary, is
  constant across the window, and changes nothing observable.
- The **whole 8 KB active object bank at 4253 is byte-identical** to the oracle
  instrument's own sample (`objram_active_04253.tsv`). At 4214 the display-bank
  phase after a state load leads the cold-boot route by one frame (our
  `objact_04214` equals the oracle instrument's active bank at 4215), and the
  alien's own 20 words are identical on both surfaces at both frames.
- Two independent end-to-end runs produced **identical SHA-256** for every dump.

**Frame 4214 (anti-hardcoding control) — 20/20.** Located independently at
`0x7080A0` (write buffer) and word indices 80/84/88/92/96 in the active bank.
Writer burst attributed 20/20: X|Y at **PC `0x000AA214`**, code|attr at **PC
`0x000AA216`**, part-table pointers **A0 = `0x12F73C`/`0x12F742`/`0x12F748`/
`0x12F75A`/`0x12F760`**, emitting actor **A4 = A6 = `0xFF9DC0`**.

**Frame 4253 (target) — 20/20.** Located independently at `0x7080A8` in the
write buffer (one extra leading object that frame) and at word indices
80/84/88/92/96 in the active bank — the indices the milestone's exit gate
names. Writer burst attributed 20/20: same PCs `0x000AA214`/`0x000AA216`, a
**different** part-table family **A0 = `0x12FECE`/`0x12FED4`/`0x12FEE6`/
`0x12FEEC`/`0x12FEF2`**, same emitting actor **A4 = A6 = `0xFF9DC0`**.
Different pose, different ROM part table, same code path — the anti-hardcoding
property the control frame exists to prove.

**Watchpoint window (deviation from the body-1 capture contract, deliberate).**
The contract said "exactly 20 word-write watchpoints at `0x7080A0..0x7080C6`".
With a 20-word window only a 16/20 prefix of frame 4253's burst is attributable,
because the alien's slot run starts one object later that frame. The wrapper now
takes `-WatchWords` (default = `-Words`) and this capture used **24**
watchpoints at `0x7080A0..0x7080CE`, plus the one bank watchpoint — still well
under the empirical 34 ceiling, still no `0x7000A0` mirror watchpoints. Widening
it changed no dump: every SHA-256 below is identical to the 20-watchpoint run.

**Fixture metadata corrected (values untouched).**
`data/street_alien_object_emission_oracles.json` declared
`state: avspu_stage1_debug_hitboxes @ 4200`. That was wrong and unreproducible
(the debug-master state leaves the alien idle). The scenario block now records
the true origin — the `mame_capture_enemy_actions.lua` cold-boot route, capture
root `.deps/mame/enemy_actions`, sampled surface = active/display share — under
`provenance_correction_2026_08_18`. **Every slot word and actor signature is
byte-identical to the original fixture**; only provenance metadata changed. The
analyzer now takes `--state` and records the state the run actually used, so
`scenario.state` can no longer inherit the fixture's declared state.

**Open metadata defect — the fixture names the wrong actor (not a wrong
address).** Actor records are **`0xC0` bytes** apart: every distinct A6 in the
watchpoint log lands on that grid (`0xFF9C40`, `0xFF9D00`, `0xFF9DC0`,
`0xFF9E80`, `0xFF9F40`, `0xFFA000`, `0xFFA0C0`, `0xFFA180`, `0xFFA240`,
`0xFFA300`, `0xFFA3C0`, plus the player at `0xFF8380`), and each holds the same
field layout (`+0x08` type, `+0x0F` facing, `+0x10` worldX, `+0x14` worldY,
`+0x1C` anim, `+0x50`). So `0xFFA000` **is** a valid street-alien actor — it is
simply **not the actor that emits the gated slots**. The emitter is `0xFF9DC0`,
by two independent lines: the watchpoint bursts carry `A4 = A6 = 0xFF9DC0` at
both frames, and with the camera provably static between the frames (the pal-05
scenery sits at px 317/333/349 in both) the sprite's slot-0 screen X advances
`275 → 335` (Δ+60) against `0xFF9DC0`'s worldX `1257 → 1313` (Δ+56, the 4 px
residual being the pose's part-0 offset change), while `0xFFA000` moves Δ+111
and no other actor is within 15 px. The oracle's `actor_signatures` do reproduce
exactly at `0xFFA000`, so they stay a valid reproduction check — they just
describe a bystander alien. Correcting `scenario.actor_base` and
`actor_signatures` to `0xFF9DC0` is left for the next agent, together with a
re-derivation of what the current signature fields were meant to witness.

**Raw evidence (SHA-256, `.deps/mame/object_emission/`), MAME 0.289, driver
`avspu`, state `avspu_stage1_replay4200`
(`eec85f7ddda96acfb8a715df008538f9414418adcfa1d14b331b51634f51312b`):**
workram_04214 `e38a6f090bc5390232e5778ea110b147d46f09b0c62857c968c14ab8a386d40c`
(32768 B); objbuf_04214 = objact_04214
`2d0a506190e316c4a9fe3a61ce96ddee96fc4900880fea6341173acdee7b51b0` (8192 B);
workram_04253 `a643a5f3c5505edb1b1460a7209c8e2dde9782ffa83c04a94485e809718b2f04`
(32768 B); objbuf_04253
`b8f18151d881c519259e51c95a57cb2912f30e3c3c26fc8bb978fb5561e76327` (8192 B);
objact_04253 `57102b601a4970765aaae6690bdb5609f56f4ffae03a8a0d3668cc975bc95969`
(8192 B). Neighbours 4213/4215/4252/4254 are dumped too. Oracle-route reference
samples: `objram_active_04214.tsv`
`6cacdf3893b98fcaca58e1da9e88a63bcfe7fbff781b07d01eed6e40b8a81a9d`,
`objram_active_04253.tsv`
`5001f04eb21d7486189fcdec3c2b6e3abca3e69918dc4f702dcbe5a275ec262c`.

**Exact reproduction command** (run from
`C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`; the wrapper runs the
capture and the analyzer):

```powershell
.\capture_street_alien_object_emission.ps1 -State avspu_stage1_replay4200 -StateFrame 4200 -FrameA 4214 -FrameB 4253 -ActorBase FFA000 -ObjectListBase 7080A0 -Words 20 -WatchWords 24 -BankSelectRegister 8040E0 -RawDir .deps\mame\object_emission -SkipSave
```

`-SkipSave` reuses the existing `replay4200.sta`; without it phase 1 re-saves it
via the cold-boot path. Pass hex arguments **without** a `0x` prefix — the Lua
side parses them with `tonumber(v, 16)`, which rejects `0x`. Expected output is
`gate_pass=True failing=[]` with `4214: match=20/20 slot=0x7080a0` and
`4253: match=20/20 slot=0x7080a8`.

**Next work (milestone 2 boundary).** Milestone 1's exit gate is met, so the
next body is phase A (decide the renderer by measurement) per
`docs/PARITY_PLAN.md`. Carry these two items into phase B/C, before the
street-alien decoder is promoted: correct the fixture's `actor_base` /
`actor_signatures` to the emitting actor `0xFF9DC0` (with a re-derivation of
what the current signature fields witness), and consider making the watchpoint
window follow the located slot run instead of a fixed base, so attribution does
not depend on choosing `-WatchWords` by hand. MAME confirmed **not running** at
the end of this session.

## Current resume point: master plan intercept

> **SUPERSEDED 2026-08-18.** The emission gate this section assigns is CLOSED —
> see "Capability Gate 1 — street-alien emission (2026-08-18 execution)" above.
> The static call-chain evidence below is retained because it is still the map
> of the object-list builder; the instructions and the "still red" status are
> not. Milestone 2 has since run too; the next executable body is **phase A**.

The plan of record is now
[`PARITY_PLAN.md#master-execution-plan-2026-08-18`](PARITY_PLAN.md#master-execution-plan-2026-08-18).
Its order supersedes every older resume list in this handoff.

[`NEXT_AGENT_PROMPT.md`](NEXT_AGENT_PROMPT.md) now holds the milestone-2
collision assignment. It does not authorize phase B, Marvel research or
full-game content expansion.

**Resume with one focused proof, not another broad disassembly pass.** The
static chain has been checked against
`.deps/mame/actorprobe/disasm_full.txt`:

```text
0xA99DC list builder (A1=0x708000; header, emitters, trailer)
  -> per-group emitters 0xAA886..0xAA8EA
  -> 0xA9B48 common actor loop
  -> 0xA9B80 actor-type jump table
  -> per-type handler
  -> Family 1 body emitter 0xAA4A4..0xAA598
     or Family 2 effect emitter 0xAA644..0xAA7F8
```

That proves where and how the CPS2 object list is built. **Closed since:** the
two-frame five-slot proof now passes 20/20 on both frames, with the emitter
pinned to PCs `0x000AA214`/`0x000AA216` inside the Family-1 body emitter and the
per-part source layout walked through `A0` (`0x12F73C…` at 4214, `0x12FECE…` at
4253, i.e. inside the `0x12FE06..0x12FEEE` window this section predicted). Still
**not** proven: the street alien's exact group/type path and Family-1 variant
selection, and the actor `+0x1c`/`+0x50` relationship to those tables.

### Immediate trace and gate (COMPLETE — historical)

1. Start from the verified frame-4200 state under stock MAME 0.289 `-debug`.
2. Install exactly 20 write watchpoints for logical object-buffer word indices
   80..99, addresses `0x7080A0..0x7080C6` inclusive. `0xA99DC` is proven to
   initialize `A1=0x708000`; do not add simultaneous `0x700000` watchpoints.
   This stays under the empirical 34-watchpoint ceiling.
3. In one bounded run, capture bank-select register `0x8040E0` per frame and
   prove the source-frame mapping for frames 4214 and 4253 from synchronized
   actor/work-RAM evidence. Record `(frame, pc, address, width, data)` plus the
   live source/actor context needed to identify `A0` and the now-proven
   emitting context `A4=A6=0xFF9DC0`.
   If the debugger action cannot print every address register, combine writer
   PCs with synchronized RAM and the static jump table; do not widen into
   another address sweep.
4. Resolve the street alien's group-list entry, type byte at actor `+0x08`,
   `type>>1` jump-table target, Family-1 sibling, and `A0` source long/deltas.
5. Produce a deterministic analyzer that regenerates all four words at slot
   indices 80/84/88/92/96 for both frames, not only the codes. Frame 4214 is
   the different-pose anti-hardcoding control:
   `[8113,0099,4efe,0131]`, `[80e3,00a9,4ef6,0431]`,
   `[80f3,00b9,4fc8,0131]`, `[8121,007b,473a,2431]`, and
   `[8111,00ab,479c,1331]`. Frame 4253 is the target:
   `[814f,009e,4df8,0131]`, `[810f,00ae,4ef0,0531]`,
   `[815b,007b,4b04,2531]`, `[814b,00ab,4a88,1431]`, and
   `[816b,006b,4958,0131]`; ordering, bank, and frame relation also remain part
   of the gate.
6. The derivation must read new capture/RAM evidence before consulting the
   validation fixture. It must fail if frame-4253 constants are hard-coded.

The execution body added, and has now committed,
`capture_street_alien_object_emission.ps1`,
`tools/mame_watch_street_alien_object_emission.lua`,
`tools/analyze_street_alien_object_emission.py`,
`data/street_alien_object_emission_oracles.json` and
`data/street_alien_object_emission.json`, with raw evidence ignored under
`.deps/mame/object_emission/`. The wrapper/watcher/analyzer accept scenario
parameters so the proof can be reused for another AvP actor; street-alien
defaults are permitted, output-specific derivation constants are not.

Only after both frames pass may the selector-12/street-alien decoder be
promoted or committed. A writer PC sequence without source-data derivation is
discovery evidence, not the gate.

### Port interpretation correction

Do **not** recreate the raw CPS2 `0x708000` buffer on Saturn as an end in
itself. Its four-word records, 10-bit coordinate packing, flags, and bank flip
are the CPS2 renderer contract. They are the extraction oracle used to prove
the ROM/source decoder. Normalize them to semantic object fields—position,
tile/code identity, palette, dimensions, flip, priority, order, and
lifetime—then emit the equivalent native VDP1/VDP2 representation. The Saturn
side must reproduce behavior and presentation, not the arcade machine's memory
encoding.

### Marvel research applied to AvP

The isolated MSHvSF research lane is preserved at
`codex/mshvsf-reference-lane` checkpoint `43e88ac`; it is not merged into this
branch. Its immediate contribution is evidence discipline: every mapping must
name source address/data/function, destination sink, test, falsification,
confidence, and uncertainty. The earlier invalid comparison of the
`0x0169da` video-RAM tilemap writer against object RAM is the concrete reason
to enforce that rule.

At Saturn-integration time, add the MSHvSF-derived AvP probes for cartridge and
work-RAM lifetimes, VDP1 command/VRAM pressure, VDP2 and SCSP usage, DMA/CD
access, media ownership, and a semantic normal-hit event fixture. MSHvSF
Hadouken, fighter timing, addresses, package sizes, module formats, and
untraced hardware ownership are not AvP facts and do not block the five-slot
gate.

**Activation rule for the next agent:** every Marvel task must finish the
sentence, “This will decide whether AvP should ___.” If it cannot name a
near-term Saturn design decision and an AvP validation probe, leave it on the
research backlog.

Use Marvel at these points:

1. **Not now:** the AvP frame-4214/4253 five-slot source-decoder gate is closed
   (2026-08-18); the current not-now body is milestone 2, replacing inferred
   collision. Marvel cannot identify AvP's 68000 group/type handler or its
   hitbox records.
2. **After AvP's referenced tile set is measured, before choosing its actor
   renderer:** trace Marvel work RAM, both cartridge banks, VDP1 command tables,
   and VDP1 VRAM at the existing idle/normal/hit anchors. Use the result to
   compare AvP's precomposed-cel and per-part-command prototypes.
3. **When AvP stage package/load ownership is known:** trace Marvel VDP2,
   file reads, DMA, and CDDA across character/stage transition. Use it to shape
   AvP load windows, then prove them first on the scrolling Round 1 Gate 1
   route and later on cumulative full-game transitions.
4. **When AvP audio ownership is being finalized:** trace one Marvel effect,
   voice, and music transition through SCSP/CDDA and CD access.
5. **Before final Saturn budgeting:** capture a Marvel tag/super stress route.
   It is more useful for peak VDP1, RAM, CPU, and DMA pressure than Hadouken.
6. **Only when AvP reaches projectile/effect design:** add the Marvel Hadouken
   path for projectile allocation, lifetime, collision, effect commands, and
   audio routing. It is not a first-pass prerequisite.

The complete trigger/transfer table and promotion rules are in
`PARITY_PLAN.md` under “Applicable MSHvSF research findings.” Marvel evidence
becomes an AvP implementation decision only after an AvP-specific probe passes.

**Repository guardrail:** AvP work stays on `codex/avp-master-plan` (or a new
branch descended from its accepted checkpoint); Marvel work stays on
`codex/mshvsf-reference-lane`. Do not merge the branches or bulk cherry-pick
the Marvel evidence package. Before switching or staging, inspect branch/HEAD/
status and stage explicit paths only. If both lanes run concurrently, use a
separate worktree or task rather than alternating a dirty checkout. Preserve
the untracked ROM directory, `nvram/`, `snap/`, and one-off diagnostics; never
add, reset, clean, or delete them as part of lane management.

**Position audit: scoped PASS; full pixel-exact coverage OPEN.**
`tools/verify_position_gate.py` compares the previous frame's actor world
coordinates plus ROM assembly origin/layout words against captured object RAM.
Current scope: 408 geometry frames, 408 matched and 0 unmatched; 1,443 tested
parts split into **1,435 directly exact pairs, 0 sibling-origin residuals,
8 observed x=0/y=-4 settling residuals, and 0 other residuals** (X is now
1,443/1,443 exact). Phase 2 extended the JSON from 12 to 28 assemblies, so every
one of the 408 frames now resolves to a decoded assembly; the shared-code-set
sibling ambiguity is additionally resolved by the actor-slot record pointer at
frame f−1 (see below), which drives the 63 former sibling-delta parts to exact.
(The earlier 801/793 and 1,372/63 counts are from earlier scopes and are
superseded.)

Model (world coordinates are 16.16 fixed point at actor slot 0x23D0/0x23D4,
world Y is up, objects render one frame behind, from f−1):

    left_ring  = wx(f−1) + origin_x − lx + 64 − width
    top_ring   = 464 − origin_y + ly − wy(f−1)

* `origin_x/origin_y`, and per part `lx/ly`, come from the selector-6 assembly
  the animation record selects (`data/avsp_animation_scripts.json`).
* `64` is VISIBLE_LEFT; `464` is the single global Y constant
  (`C(part) + origin_y − ly == 464` for every part; equivalently
  `K = origin_x + 64` for the X edge).
* Compare in the 1024 game ring (low 10 bits of the object X/Y words).
  `shift_x`/`shift_y` are capture-tool unwraps, **not** game state — the model
  predicts the raw ring position, so do not add them.
* Layout words may be read from `offset_program.bin` relative to base 0x1FD1C8,
  or from `offset_full_program.bin` relative to base 0x1E0000; those sources
  agree at the tested addresses. The old wrong values came from pairing the
  full window with base 0x1F6000. The position audit deliberately passes
  `layout_data=None` and uses the first form.

The earlier +48/−10 residual pair is **not a magic offset**: it is the origin
delta between two assemblies that share a code set. Assembly 3 has an
airborne table at 0x13e04c (origin −52, +23) and an at-rest table at 0x13e44c
(origin −62, −25); picking the wrong one shifts X by −10 and Y by +48. Their
per-code layout words are identical, so the only difference is the origin.

The gate now resolves this by **selecting the origin with the actor-slot record
pointer at frame f−1** — the same one-frame source the world coordinates use.
The record at f−1 points at the table actually being rendered, and when its
code set equals the captured frame's code set the gate adopts that table's
origin (layout words unchanged). A one-off diagnostic confirmed this drives
**63/63** former sibling-delta parts to (0, 0); using the pointer at frame f
only reaches 54/63 because the record sometimes advances one entry before the
visual pose changes (sub-frame timing), so the f−1 source is the correct one.
As a safety net the gate still decodes every pointer-reachable table and keeps
an explained origin-delta set: any residual not driven to zero is passed only
if it is in that set, never as a general tolerance.

The 8 settling parts (frames 12689 and 13165, uniform −4 Y, X-exact) are
**formally bounded**, not just observed:
* **Exhaustive:** the residual table across all 1,443 tested parts contains
  only `(0,0)` and `(0,−4)`; X is 1,443/1,443 exact. So `(0,−4)` is the *only*
  non-zero residual in the entire scope — the model's total error is one value.
* **Whole-pose:** every part in each of the two frames shifts by the same
  `(0,−4)`; it is a global actor-Y offset, not a per-part layout/tile defect.
* **Settle context:** the integer world Y decelerates to a rest value just
  before each frame (…285→279→274→274 and …242→231→224→224), and the implied
  world Y that would zero the residual is the rest value **minus 4** in both
  cases. The on-screen Y therefore applies one final downward settle step
  while the world RAM has already clamped to rest. A lagging display-Y channel
  at 0x23D8 eases into `wy_hi` (271,273,274 vs 285,279,274), confirming a
  separate eased display Y in the slot. The one-step trail is the expected
  mechanism; the exact object-Y writer is **not yet disassembled**, so this is
  a bound, not a derivation.

The gate recognises only that precise residual in that recent-world-Y-change
context (and never allows a general ±4 tolerance). Run
`python tools\verify_position_gate.py` for the scoped audit; `--verbose` lists
settling frames and unexpected residuals; `--require-exact` is the
goal-strength gate and currently exits nonzero only because these 8 settling
parts are not directly exact (coverage itself is complete: 408/408 matched).

Remaining before this gate is exhaustive:
* 8 tested parts are not directly exact, all the x=0/y=−4 settling parts
  (0 unexplained, 0 sibling-delta; the only non-zero residual in scope).
  Full pixel-exact coverage needs only the −4 settling **derived**; it is NOT
  a coverage gap — all 408 frames match.
* Derive the −4 vertical settling by disassembling the object-Y-from-world-Y
  writer (the one-step settle trail); the bound above is the safety net until
  then.

**Pose format gate: PASS for 28/28 decoded boss assemblies (29 oracle poses).**
Every tested assembly reproduces a captured oracle crop with **0 differing
pixels**, in both the default and `--self-contained` modes. The gate deliberately
uses captured object-RAM screen geometry to isolate code/tile/palette and
composition correctness; the position audit above is the independent
ROM-origin/layout check.

Phase 2 extended the decoded set from the 12 program-referenced assemblies to
all 28 assemblies the boss poses actually display (poses 0–28; poses 0 and 1
share 0x13dfec). The set is now sourced data-drivenly from
`generated/avsp_boss_rom_data.json`, which already maps each pose to its 0-diff
assembly, unioned with the program-referenced addresses (a subset). Five trace-only
assemblies — 0x13e0e8, 0x13e10c, 0x13e130, 0x13e3b0 (mid-attack transients) and
0x13e44c (an at-rest sibling) — are decoded by the generator but **intentionally
excluded** from the JSON: they have no captured-pose oracle, and the pose gate
requires every listed assembly to 0-diff an oracle (a no-oracle entry would turn
the gate red). They are reported in `excluded_no_oracle_assemblies` rather than
silently dropped or forced to pass. Key
fixes: (1) corrected selector-6 decoder to read `count` entries starting at
+12 with signed origin at +8; (2) switched object positions from ROM script
origin+layout to MAME object RAM screen coordinates (`screen_x`, `screen_y`)
because the ROM script uses animation-local space while the renderer uses
screen space; (3) fixed `compose_assembly` to use `screen_x`/`screen_y` keys;
(4) fixed oracle dump to write the best-matching pose instead of always pose 0;
(5) removed double-flip (tile-order reversal + image flip) — the reference
renderer reverses tile order AND pixel positions, not the image itself.

**Previous budget-as-entry-count findings are superseded.** `count`, not
`budget`, is the object-command count; budget accounts for expanded tile cells,
and the signed layout adjustment advances the layout chain.

**Direction as of 2026-08-17: functional parity by ROM translation, with an
instrumented MAME build retained only as a contingency. Stock MAME 0.289 debug
overlays now work, and stock debugger watchpoints must be tried before any
custom build. The plan of record is
[PARITY_PLAN.md](PARITY_PLAN.md); read it after this file. This handoff says
where work stopped, the parity plan says where it is going.**

Read this file before taking any action. The user wants a private, capture-
faithful, native Sega Saturn port of the complete US `avspu` game. Round 1 from
the frontend through the Round 2 title is Capability Gate 1, not the final
destination. Complete single-player precedes mandatory original-player-count
multiplayer validation. Do not reframe success as an emulator, approximate
demo, host-only simulation or focused animation viewer.

## Repository state

- Repository: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`
- Current documentation/planning branch: `codex/avp-master-plan`, created from
  AvP checkpoint `5327c3a`; `d9e40fd` is the parent of the full-game scope-
  synchronization checkpoint. Run `git rev-parse HEAD` for the current commit.
- Street-alien emission gate checkpoint: `40e7f76` (`Close street-alien
  five-slot emission gate (Gate 1 milestone 1)`), the first code/data commit on
  this branch. It commits the wrapper, watcher, analyzer, anchor-state script,
  the oracle fixture (values unchanged, provenance corrected) and the analyzer
  report. Raw evidence stays ignored under `.deps/mame/object_emission/`.
- `docs/GOAL.md`, `docs/PARITY_PLAN.md`, this handoff, repository bootstrap,
  test/hardware documents and `docs/NEXT_AGENT_PROMPT.md` share one hierarchy:
  complete `avspu` is the destination, Round 1 is Capability Gate 1. The
  street-alien emission proof is **closed**; the next-agent execution body is
  milestone 2, replacing inferred collision.
- AvP production baseline remains `prototype/private-capability-test` at
  `5327c3a`; this planning branch does not rewrite its history.
- MSHvSF research remains isolated on `codex/mshvsf-reference-lane` at
  `43e88ac`. Do not merge that branch into AvP; promote only an AvP-specific
  probe/result through a deliberate AvP commit.
- Phase 1 (stabilization) checkpoint: `c1de5f5` (`Stabilize Chrysalis
  ROM-composition slice (Phase 1 checkpoint)`). It commits the
  ROM-composition runtime change plus the promoted generators, C90 pose-record
  interpreter and host test, self-contained pose gate, reference interpreter, and
  work-RAM play-sequence trace. It is an ancestor, not the current HEAD.
- Street-alien extraction checkpoint: `5327c3a` (`Record street-alien
  record/assembly extraction checkpoint (Phase 2a)`), the AvP baseline from
  which this planning branch was created.
- Goal-audit checkpoint: `068ff6b` (`Audit goal progress and harden validation
  gates`), following position-gate implementation `483f088` and handoff command
  update `020aa5b`.
- Pre-existing untracked scratch file: `check_tail.py`. It is not part of the
  checkpoint and was preserved rather than deleted or committed.
- Current disc profile: `normal-release`; `build/last_compile_profile.txt` now
  says `release-normal-release` after the 2026-08-18 `-Release` build, so the
  build mode and profile are consistent. This is still not the final hardware
  candidate; run `build.ps1 -Clean -Release` for the real final image.
- `main.c` (plus the promoted tools/tests/data) is COMMITTED at `c1de5f5`: the
  Chrysalis boss composes from ROM (`compose_boss_rom_pose`,
  `generated/avsp_boss_rom.h`) and no longer loads `BACT`/`BHIT`/`BKO` for
  animation. The ISO below reflects that committed change.
- Current ISO: 5,541,888 bytes, SHA-256
  `31d53a6ea4552b6c3dc75afdb0b5d3ee07c97b38f4c3a36f821833c1897dbad6` (the
  2026-08-18 Chrysalis ROM-composition release, rebuilt for the Phase 1
  checkpoint; supersedes the 5,410,816-byte `be49e9aef82d3a02f98eb1370ea7cbcdf6a6a6014074d7a4d853aad7b7b42062`
  image from checkpoint `068ff6b`). The size growth is the ROM tile/palette/pose
  data. NOTE: the whole-image SHA-256 is build-run-dependent — `build.ps1` runs
  `mkisofs` without `-r`/`-mtime`/`-D`, so the embedded per-file/volume
  timestamps change the image bytes (same 5,541,888 size) on every rebuild; the
  prior run recorded `418b801c...`. Verify by byte size and the stable per-member
  hashes, not the whole-image hash, unless comparing two images from the same
  build run.
- Current cue SHA-256: `bfc58c7020d90952e93bef7ecba32dea8d4faddf6ce6a90e1054206ee1807b12`.
- Both values match `build/hardware_release_manifest.txt` at
  `profile=normal-release`.
- Goal-audit tool/report SHA-256 values:
  - `tools/decode_avsp_animation_scripts.py`:
    `0119260b02eae113e9bf19a141a99b33d4a0526bdf3fd7604c48a526915db9d7`
  - `data/avsp_animation_scripts.json`:
    `7d63775a983e0fc7489a3017bdd3947933e2fb2e51df4eed306c7ee4ea071ef6`
  - `tools/verify_pose_gate.py`:
    `e697888bb58ab01ca00b654fb3a81b48e975376bcf7bdcead22f62bad5bd5679`
  - `tools/verify_position_gate.py`:
    `ce5d074fd7a8f3bb3f617ae71ac15d4122984feb40cd10af126d87bb5c3310fb`
  (`decode_avsp_animation_scripts.py` and `avsp_animation_scripts.json`
  changed this checkpoint: the record tail bytes +8/+9 are now labelled
  per-record as interaction-table selectors (readers 0x1cf94/0x1cf88) and
  +10..+15 are kept explicitly unlabeled; the raw tail is retained and the
  28-assembly set is unchanged. `verify_pose_gate.py` and
  `verify_position_gate.py` are unchanged; the pose gate still reports 28/28
  and the position gate 1,435/0/8/0 with X 1,443/1,443.)
- Goal-audit verification:
  - `test.ps1`: PASS; controller-only model reached Round 2 in 4,485 frames and
    the 12,000-frame deterministic soak passed.
  - `build.ps1`: PASS; normal disc-profile ISO/cue rebuilt and every member
    checked by the build matched its expected size/SHA-256.
  - `tools/verify_pose_gate.py`: PASS, 28/28 assemblies (29 oracle poses),
    zero differing pixels, in both default and self-contained modes.
  - `tools/verify_position_gate.py`: scoped PASS (1,435 exact pairs, 0
    sibling, 8 settling, 0 other; 408/408 frames matched, 0 unmatched;
    X 1,443/1,443 exact); `--require-exact` exits 1 as expected while 8
    settling parts remain non-exact (all classified, none unexplained).
- No MAME process from this checkout remained after the overlay checkpoint.
  Do not kill an emulator owned by another checkout or concurrent session.

Implementation and documentation files in this checkpoint:

- `AGENTS.md`
- `build.ps1`
- `capability_model.c`
- `main.c`
- `makefile`
- `prepare_avsp_port.ps1`
- `tests/capability_model_test.c`
- `tools/extract_avspu_stage1.py`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/HARDWARE_TEST.md`
- `docs/TEST_PLAN.md`
- `docs/AGENT_HANDOFF.md`
- `CLAUDE.md`

New tracked source/evidence files:

- `capture_boss_ko.ps1`
- `data/boss_ko_capture.json`
- `tools/analyze_boss_ko.py`
- `tools/mame_capture_boss_ko.lua`
- `capture_frontend.ps1`
- `data/frontend_capture.json`
- `tools/analyze_frontend.py`
- `tools/mame_capture_frontend.lua`
- `tools/analyze_frontend_segments.py`
- `data/frontend_segments.json`
- `tools/analyze_frontend_geometry.py`
- `data/frontend_geometry.json`
- `capture_frontend_wipe.ps1`
- `tools/mame_capture_frontend_wipe.lua`
- `data/frontend_geometry_cadence1.json`

`git diff --check` passes; only existing LF-to-CRLF warnings are emitted.

## Agent bootstrap files

- `AGENTS.md` (added in `14493fa`) is the canonical, harness-neutral
  repository instruction file. `CLAUDE.md` is a thin tracked pointer for
  Claude Code sessions, which auto-load `CLAUDE.md`; keep `AGENTS.md`
  canonical and `CLAUDE.md` minimal so they cannot diverge.
- Agent sessions may start in the parent workspace
  `C:\Game Dev\BrooklynBangoutX`, a separate non-Git project workspace for the
  unrelated Brooklyn Bang Out game. An untracked `CLAUDE.md` there maps the
  workspace and routes agents into this repository; recreate it from this
  section if it is lost.
- The reusable skill is canonical at
  `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn` and reaches Claude
  Code through the machine-local directory junction
  `C:\Users\lambd\.claude\skills\port-cps2-to-sega-saturn` (recreate with
  `New-Item -ItemType Junction` after a profile reset; it is tracked
  nowhere).
- Where `AGENTS.md` says `apply_patch`, Claude Code sessions use their
  Edit/Write tools with the same preserve-unrelated-work discipline.

## Active frontend-fidelity checkpoint

This is evidence and sizing work only. It is not integrated into the Saturn
runtime yet, and it must not be described as a finished exact frontend.

- `capture_frontend.ps1` audits the private `avspu` ROM set with MAME 0.289,
  reuses or regenerates the raw capture, and runs the analyzer with bundled
  Python.
- The deterministic input route mirrors `tools/mame_capture_stage1.lua`.
- Raw samples cover CPS2 frames 1320 through 2160 inclusive at cadence 2: 421
  samples, 241 unique full frames, and 292 pose runs.
- Raw capture files are intentionally ignored under
  `.deps\mame\frontend`: 1,264 files and 170,685,151 bytes at this checkpoint.
  Regenerate them with `capture_frontend.ps1 -Refresh`; do not add ROMs or raw
  captures to Git.
- A second ignored raw capture exists at `.deps\mame\frontend_wipe`: 130 files
  and about 17 MB, frames 1870..1912 at cadence 1. Regenerate it with
  `capture_frontend_wipe.ps1 -Refresh`. It is a separate directory so the
  cadence-2 capture above is never cleared.
- Tracked report `data/frontend_capture.json` SHA-256 is
  `eefdf8c0d9be6da796e9b61c52d8e89f7a4890d6380978b97543781037175f3f`.
- Full independent-palette RLE would be 15,528,546 bytes and is rejected.
- Start transition, frames 1770..1798: 15 samples, 9 unique frames, 116-color
  union, 41,758-byte coalesced stable-palette delta. This fits one retired
  78,848-byte frontend allocation.
- Character confirmation, frames 1800..2038: 120 samples, 31 unique frames,
  188-color union, 137,715-byte coalesced stable-palette delta. It does not fit
  one retired frontend allocation. The RGB-to-first-palette-pen experiment is
  worse at 208,630 bytes and is not exact because duplicate palette colors make
  reverse pen identity ambiguous.
- Round 1 title, frames 2040..2160, has a 915-color union and still needs
  segmentation into stable layers, palette fades, and changed regions.
- SUPERSEDED for both windows by "Frontend segmentation result 2026-08-17"
  below. These two sizing bullets remain as the record of what the cadence-2
  storage experiment measured, but stored frames are no longer the intended
  representation for either window. Read that section before acting on them.
- MAME's CPS2 final screen bitmap is RGB32 here. The captured
  `pixels_####.bin` files are 384x224x4 final colors, not native stable palette
  indices.
- Cadence 2 is exploratory for storage characterization. Recapture the chosen
  representation at cadence 1 before calling it capture-exact.
- No runtime, generated Saturn archive, ISO, or release-manifest content was
  changed by this frontend checkpoint.

Deterministic source hashes:

- `capture_frontend.ps1`: `ad12c2a33c4d5838cdebc0d60ae16b4a1fd003454bd4305334de2b85eb5cb1c6`
- `tools/mame_capture_frontend.lua`: `59c8c6c53e9f3bc994fad9d6b55ebe3f78097390b1b6208c2b0c74155f951568`
- `tools/analyze_frontend.py`: `e7cf211482ae9c4521fc9a31c4d89e05efc4d3f3b5c4eb8f379dcd1b07bc3ddf`
- `tools/analyze_frontend_segments.py`:
  `01e99fd85e6c05eba6f437b4f0aeb89d3aad090fa4f915602ccd3e0c61bc3f8b`
- `data/frontend_segments.json`:
  `67ff4e52bfa53751567ea9adf1e3b7d9c6be1cea81ce0d220575a343265b072b`
- `tools/analyze_frontend_geometry.py`:
  `358197875022ea85a17e8d0969de9b34f2151f4ef321870b9f1d507ada36604e`
- `data/frontend_geometry.json`:
  `98af6e62dea6e3e11192a683601e84a2640333c4323bde9323528707d19375d3`
- `capture_frontend_wipe.ps1`:
  `1b9d27997d38e629f76d9a8f3448706da7d7938ae5750def77e07c7ef069ca29`
- `tools/mame_capture_frontend_wipe.lua`:
  `2ac0391ee05d337ff20ca36839ec538a64d3dfabcb56ffd9834269aea06aa242`
- `data/frontend_geometry_cadence1.json`:
  `9a98eb7ad39321b797311ea474ef4fc8bbd01167d101d05ce28fc897a62f694e`

## Process and restart state

- No MAME, Yaba Sanshiro, Mednafen, or RetroArch process was running at the
  checkpoint. No capture/build command is partially active.
- The latest `normal-release` disc-profile ISO/cue remains the verified image
  listed above; its compile stamp is `debug-normal-release`, so it is regression
  evidence rather than the final physical-hardware candidate. The frontend
  analyzer did not rebuild or overwrite it.
- A reuse-only run of `capture_frontend.ps1` passed the ROM audit, reproduced
  every report total, and reproduced the report SHA-256 exactly.
- `tools/analyze_frontend.py` passes `py_compile`; the Pillow 14 deprecation was
  removed with a compatible fallback.
- An ignored accidental directory exists at
  `.deps\mame\.deps\mame\frontend` (421 files, 6,424,401 bytes) from an earlier
  relative snapshot path. It is not used. It may be removed later only after
  resolving and checking that exact absolute path.
- The reusable skill at
  `C:\Users\lambd\.codex\skills\port-cps2-to-sega-saturn` records RGB32
  frontend-capture limits, cadence-1 release gating, full-screen crop checks,
  and whole-block allocator alignment rules. Its start step now names
  `AGENTS.md` as canonical with `CLAUDE.md` as the Claude Code pointer.
  `references/workflow.md` additionally records the generalizable lessons from
  the segmentation result: inspect frames before designing a codec because a
  window may be a native composition rather than video; detect fades against
  the most colourful frame, never the first; check RLE against raw before
  assuming compression; collapse repeated frames before sizing; and read the
  state machine to find the frame that starts CDDA.
- The skill now carries the corrected parity-era method: preserve the existing
  Saturn platform pipeline; use ROM translation for systematic animation,
  stage and AI data; use captures as regression evidence; activate retained
  debug tools without per-frame forcing; try stock debugger watchpoints first;
  keep a custom MAME build and entity spawner as contingencies; map actor fields
  on demand; and compare events for functional parity. It also records the
  ROM-derived SH-2 interpreter, exact referenced-tile working set, and measured
  composed-cel versus per-tile VDP1 decision.
- Skill hashes: `SKILL.md`
  `7adc7092f8c11f49a65c33b0161436cafc51b51f7045a73f48e347af8f7cf2ac`;
  `references/workflow.md`
  `ecc81fe344e6a4cc462882b0e24cb8b1575291d79b8185e58e9bc11180f58745`;
  `agents/openai.yaml`
  `038134e6c419dc5654b404dac81317a21900e342e208841f44cd959b837c7e2b`.

## What the KO slice contains

- A separate deterministic capture loaded from verified state `avspu_stage1_boss_12660`.
- Natural lethal impact at CPS2 source frame 13491, reducing Chrysalis health 3 to 0.
- Exact KO visual interval 13492 through 13919 inclusive: 428 frames.
- 24 exact object poses and 36 pose runs, palette bank 27 throughout.
- Temporal unwrapping of both CPS2 10-bit X and Y coordinates.
- Maximum unwrapped composite 240x112, inside the declared 288x192 Saturn canvas.
- Exact per-frame pivot trajectory in generated signed-short X/Y arrays.
- New `/SPR4/BKO.RLE`: 43,232 bytes, SHA-256 `9ad615f5e61615142d5be3b91a10fd16e9519ff304d204da704f9fe6e609f78a`.
- Eight archive poses are new after deduplication against the base and hit archives.
- Boss clips now total six: 1, 44, 106, 189, 40, and 428 frames.
- Production timing keeps the boss in KO through all 428 source frames, holds the corpse 60 more frames, aligns boss-defeat timer 0 to source 13920, boss-clear audio to 14070, and Stage Clear to 14160.
- A `-BossKoTest` build profile repeats the KO. Its diagnostic-only final-frame hold makes corpse inspection easier and does not change normal-release timing.

## Verified evidence

- Host capability tests pass.
- Controller-only route reaches the Round 2 boundary in 4,485 native model frames.
- Deterministic 12,000-frame soak passes.
- `-BossKoTest` compiles and builds a Saturn ISO.
- Focused ISO verifies `BACT.RLE`, `BHIT.RLE`, `BKO.RLE`, `SACT.RLE`, and all event PCM members byte-for-byte by SHA-256.
- A clean Yaba Sanshiro launch from the exact AvP temporary absolute-path cue renders the capture-derived Chrysalis KO launch, airborne tumble, changing poses, and final low corpse pose without an asset error.
- `run.ps1` avoids Yaba 1.20.37 stale relative-cue state by generating `%TEMP%\AvPSaturnCapabilityTest\game.yaba.cue` with absolute ISO/WAV paths. Still inspect the command line and screen; unrelated stale emulator instances have existed.

## Full-route allocation resolution

The original `-EncounterTest` failure was reproduced exactly:

```text
BKO.RLE: Out of memory
```

Root cause: Jo Engine reuses but does not split a freed allocation. Loading the
5,900-byte hit archive first consumed the complete retired 78,848-byte
character-select block, so the second allocation could not use its apparent
tail. `load_boss_supplement_archives()` now makes one 49,137-byte allocation
and reads both files into fixed subranges before CDDA begins. The BKO subrange
starts at four-byte-aligned offset 5,904; the first unaligned attempt reached
the boss but correctly exposed `BOSS ACTION RLE` during KO decoding.

The aligned build passes both failures. In Yaba Sanshiro, the exact
`-EncounterTest` disc entered Stage 1, reached Chrysalis with Stalker adds,
rendered the changing 428-frame KO tumble, and arrived at the visible `ROUND 2
WAR IN THE UNDERPASS` card without an allocation, archive, RLE, palette, or
VDP1 error. Host tests still reach Round 2 in 4,485 frames and the 12,000-frame
deterministic soak passes.

## Plan review 2026-08-17

An independent feasibility pass checked the frontend plan against the tracked
report, `main.c`, and `docs/ARCHITECTURE.md`. The architecture holds; these
findings bound the remaining design:

- Representability is guaranteed. No captured frame exceeds 174 colours
  (report `maximum_colours_in_one_frame`), so every frontend frame fits one
  256-colour VDP2 palette. The 915-colour Round 1 union only forbids one
  whole-window stable palette, not per-segment palettes.
- CPS2 pen identity is not required for the frontend. The VDP2 route-still
  path is output-lossless: any consistent per-segment index assignment that
  reproduces exact final RGB is exact. The RGB32 capture limitation blocks
  pen-native claims only; do not spend more effort reversing pens here.
- CORRECTION to an earlier claim in this section: CDDA does **not** start
  after the Round 1 title. `cap_confirm_character()` sets
  `world->encounter_started = 1` at character confirmation
  (`capability_model.c:659`), and `main.c:1809` starts track 2 on that flag.
  Ordering inside the confirm-entry frame is: release scene 1, load the
  49,137-byte supplements (`main.c:1610`), then start CDDA (`main.c:1809`).
  The confirm-entry frame therefore carries the **last legal data-track
  read**. Both the character-confirm animation and the Round 1 title play
  while CDDA is active, so pre-CDDA streaming is not available to them and
  every payload they need must already be resident.
- Both retired 78,848-byte blocks are already committed: block 0 holds the
  64,118-byte Stalker archive from CHARACTER_SELECT (`main.c:1595`), block 1
  holds the 49,137-byte boss supplements from CHARACTER_CONFIRM
  (`main.c:1610`). Whole-block reuse strands the 14,730- and 29,711-byte
  tails. There is no free frontend block; treat "fit it in the retired
  blocks" as unavailable unless those archives are deliberately rescheduled.
- Cadence-2 sizes are lower bounds for characterization only. Measure at
  cadence 1 before fixing any layout.
- CRAM fade updates must land in vblank. The scene path already rewrites the
  shared 256-colour bank per state change; reuse it and verify per-frame
  update size against the vblank budget on hardware, not only Yaba Sanshiro.
- Memory arithmetic from documented payloads: player archive 417,488, alien
  archive 131,552, boss base 119,868, Stalker archive 64,118, supplements
  49,137, resident event PCM 2,095,772, withdrawal 396,708 until its
  barricade release into the 221,184-byte decode pool, plus thirteen route
  stills, two 78,848-byte frontend surfaces, and the 78,848-byte decode
  buffer, against 4 MiB cartridge plus work RAM. The budget closes only
  because of phase overlays. New frontend animation payloads are compatible
  if they live in the retired-block/overlay regime; never move them into the
  cold-boot working set, which already exhausted the bounded startup heap
  once in Yaba Sanshiro.

## Frontend segmentation result 2026-08-17

`tools/analyze_frontend_segments.py` (new) measures unique-frame transitions,
separates palette-only steps from structural steps, reports changed-pixel
bounding boxes, and greedily splits each window against a byte budget. It
writes `data/frontend_segments.json`. `tools/analyze_frontend.py` was
deliberately left untouched so its tracked report hash stays the checkpoint
anchor; the repository already uses one analyzer per investigation.

Verification of the new tool: its numpy RLE and coalesced-delta primitives
reproduce `analyze_frontend.py` byte-for-byte on `start_transition`
(strict 42,145 and coalesced 41,758, matching the tracked report). Do not
change those primitives without repeating that comparison.
`data/frontend_capture.json` still hashes `eefdf8c0...`, unchanged.

Measured at cadence 2, fitted to 352x224:

- `start_transition` 1770..1798: 15 runs over 9 distinct images, 116-colour
  union, 42,102 bytes, one segment. Fits one block. Unchanged conclusion.
- `character_confirm` 1800..2038: 47 runs over **31 distinct images**, so
  frames repeat non-consecutively and a distinct-image cache beats
  re-encoding every run. 188-colour union, 19 palette-only steps, 27
  structural steps, 103,962 bytes total, splitting into 75,115 + 34,692.
- `round_1_title` 2040..2160: 26 runs over 26 distinct images, 915-colour
  union, 506,973 bytes, peak 66,055 changed pixels in one step (84% of the
  screen). **Storage is infeasible**: a busy mid-window frame costs
  78,848 raw + ~465 palette bytes, so one frame alone exceeds one
  78,848-byte block, and its count/value RLE *expands* to ~84,500 bytes.
  Cadence 1 roughly doubles this to about 1 MB.
- The fade hypothesis was tested and **falsified**. Fades from black cannot be
  a function of a dark base frame, so the test was repeated against the most
  colourful frame in each window. That reference covers only 3/25 Round 1
  frames and 4/46 confirm frames. Neither window is a global CRAM fade; do
  not re-propose one.

Inspecting the frames explains why storage is the wrong representation:

- Frame 1800 is the four-panel character-select grid with the countdown.
  Frame 1900 shows those panels collapsing into horizontal bands. Frame 2038
  is black. The window is a **geometric panel wipe of an image that is
  already resident** in the 78,848-byte character-select surface.
- Frame 2040 is `ROUND 1 / CITY OF DESPAIR` text on black. Frame 2086 is the
  **live gameplay scene** (street, barricade, HUD, Predator, aliens) with the
  title text over it. Frame 2160 is the same scene with the text gone. The
  915-colour union is the street scene, not title art.

Architectural conclusion: neither window should ship as stored frames. Both
are native compositions of assets the runtime already holds.

- Character confirm is a VDP1 scaled-sprite or VDP2 line-scroll/window
  transform of the resident selection surface. Payload is a per-frame
  source/destination rectangle table, on the order of hundreds of bytes.
- Round 1 title is the existing native scene (reconstructed VDP2 street,
  VDP1 HUD overlays, actor archives) plus a small text overlay and a reveal.
  The runtime already renders all of it; only the text overlay and the
  reveal schedule are new.

This removes the RAM blocker rather than working around it, and it is the
only path consistent with "native SH-2 code, not stored video". The cost
moves from megabytes of pixels to a small geometry/timing table, but the
capture-exactness burden moves with it: the native transform must be proven
against a cadence-1 capture frame by frame, not asserted.

## Character-confirm wipe solved 2026-08-17

`tools/analyze_frontend_geometry.py` (new) recovers the confirm transition as
native geometry and validates it against the raw capture. It writes
`data/frontend_geometry.json`. The run raises rather than reporting a weak
result if either claim below fails, and a negative test confirms it: feeding
it the wrong static frame raises `frame 1884 is not the static frame inside
rows 40..223`.

Validated over the 13 sampled frames 1884..1908:

- The wipe is a **row shutter, not a vertical squeeze**. Every row of every
  wipe frame is byte-identical to static frame 1852 or entirely black, with
  no resampled or partially matching rows. This was visible in the capture as
  the countdown digits keeping their exact size while the panels vanish.
- The visible band closes **linearly and symmetrically**: 4 rows per source
  frame per edge about a fixed centre at row 131.5, from content rows 40..223
  to fully black. All 11 fitted top residuals are 0.
- Fitted start is source frame 1885. Cadence 2 determined this only to +/-1
  source frame, so it was confirmed by an independent cadence-1 capture; see
  the confirmation below.

### Cadence-1 confirmation

`capture_frontend_wipe.ps1` and `tools/mame_capture_frontend_wipe.lua` capture
frames 1870..1912 at cadence 1 into `.deps\mame\frontend_wipe` (130 files,
about 17 MB, ignored). The lua input schedule is byte-identical to
`tools/mame_capture_frontend.lua`, so the route matches; the script refuses to
clear `.deps\mame\frontend`, so the cadence-2 capture backing the other
reports cannot be destroyed. The report is
`data/frontend_geometry_cadence1.json`.

Both captures agree on every model parameter, from different cadences,
directories, and static reference frames:

| parameter | cadence 2 | cadence 1 |
| --- | --- | --- |
| rows per source frame per edge | 4 | 4 |
| centre row | 131.5 | 131.5 |
| content rows | 40..223 | 40..223 |
| start source frame | 1885 (+/-1) | **1885 (+/-0)** |

The cadence-1 run fits 22 moving samples with zero residuals and observes the
last held sample at 1885 itself, so the start frame is now pinned rather than
extrapolated. Resume step 4 is satisfied for the wipe.

The first cadence-1 run failed usefully: `top edge is not linear: steps
[0 x14, 4 x22]`. The window legitimately contains a held prefix, and the
fitter had assumed the whole window was moving. It now locates the static
prefix, fits only the moving samples, and cross-checks the extrapolated start
against the last held sample, requiring `0 <= start - last_held < cadence`.
That check is what makes the cadence-2 and cadence-1 results comparable
instead of coincidentally similar.

Consequences:

- The confirm wipe needs **0 bytes of stored animation**. The Saturn clips the
  already-resident 78,848-byte character-select surface to a row band, which
  a progressive blackout of the VDP2 bitmap reproduces exactly. The existing
  release of that surface at CHARACTER_CONFIRM entry (`main.c:1610`) does not
  conflict with it; resume step 3 records the verified reasoning.
- The Round 1 title text is 110x37 at (132,90) with 9 colours: 4,070 bytes
  raw, about 2,035 bytes as one 4bpp VDP1 cel. That is the only genuinely new
  frontend asset.
- The blinking `PRESS START` element at (242,2), 103x29, is already
  implemented as a fixed VDP1 overlay.

Total new payload for the whole frontend animation is therefore on the order
of 2 KB, against roughly 1 MB for the stored-frame path that was rejected.

Not yet characterized in the confirm window: the 1800..1852 selected-panel
blink (regions 32x27 at (42,61) and 86x52 at (15,54), alternating structural
and single-CRAM-entry steps) and the exact appearance schedule of the title
text and `PRESS START` blinks between 1954 and 2034. Per-step boxes for all
of them are in `data/frontend_segments.json`.

## Shutter integrated 2026-08-17

The confirm shutter is now in the runtime, not only in analysis.

- `capability_model.h` declares `CAP_CONFIRM_SHUTTER_START_TIMER` 85,
  `CAP_CONFIRM_SHUTTER_ROWS_PER_FRAME` 4, and content rows 40..223.
  `cap_confirm_shutter_band()` in `capability_model.c` returns the band for a
  confirm timer and 0 once closed. Confirm timer 0 is source frame 1800, so
  timer 85 is source frame 1885; the model's existing 240-frame confirm hold
  already aligns Round title to source 2040.
- `tests/capability_model_test.c` adds `test_capture_exact_confirm_shutter()`,
  which asserts the model against all 43 sampled bands from the cadence-1
  capture, plus centre invariance and closed-stays-closed. That table is
  evidence: if an implementation change breaks it, fix the implementation.
- `main.c` adds `apply_confirm_shutter()`, called from `draw_world()` during
  CHARACTER_CONFIRM. It blacks only the rows newly hidden since the previous
  frame, four at each edge, straight into the VDP2 bitmap. No stored frames,
  no source surface, no change to the load or CDDA schedule.

Verified so far:

- Host tests pass, including the new shutter test and the existing
  12,000-frame soak; the controller-only route still reaches Round 2 in 4,485
  frames.
- `build.ps1` normal-release and `build.ps1 -EncounterTest` both compile,
  link, and build ISOs with every required member verified by size and
  SHA-256. No new compiler warnings.
- The working disc was rebuilt as `profile=normal-release` after the
  diagnostic build, so `game.iso`/`game.cue` are not a diagnostic image.

NOT yet verified: nobody has watched the shutter run in an emulator. The next
action for this change is a Yaba Sanshiro boot to confirm the band closes
smoothly, the countdown stays legible to the end, and no VDP2 tearing or
partial-row artefact appears. Until then, describe it as built and host-tested,
not as visually confirmed.

## Direction change 2026-08-17: ROM logic translation

The user set a new target: **functional parity, not frame-exact parity**, reached
by translating game logic out of the ROM rather than inferring it from screen
captures. Treat the capture-a-clip-and-bind-it method as superseded for new
work. Existing captured evidence stays valid as a cross-check.

Rationale, and it is now demonstrated rather than assumed:

- The project already reconstructs the full 16 MiB CPS2 graphics region
  byte-for-byte, so every tile of every animation is already available. Screen
  capture was only ever re-deriving the *assembly instructions*, which exist in
  ROM as compact tables.
- Frame extraction does not scale: each new actor or action needs its own
  deterministic capture, analyzer, archive, and slice of a 4 MB budget that
  already closes only through phase overlays. Unobserved actions are simply
  missing. Table extraction covers every actor and action at once and shrinks
  with coverage because poses share tiles.

### Animation script tables located

`tools/mame_probe_actor_struct.lua` dumps each tracked actor's struct every
frame; `tools/mame_dump_rom_window.lua` dumps a 68000 program-ROM window.
Findings from the `avspu_stage1_boss_12660` state, 240 frames:

- The actor array has a **0xC0 (192-byte) stride**, confirming the spacing of
  the known actors at `FFA240`, `FFA300`, `FFA3C0`.
- Of 96 struct words, 34 change during animation.
- Words `w1c:w1e` form a 32-bit **animation-script pointer into program ROM**,
  taking 29 observed values in `0x13CC18..0x13CEC4`; those canonicalize to six
  programs plus 23 mid-program aliases.
- Word `w88` takes 224 distinct values over 240 frames and is very likely a
  per-frame timer or counter.
- Normal script records are 16 bytes, followed when required by a four-byte
  jump pointer. Big-endian fields proven so far: `+0` duration; `+2` control
  word (bit-15 flip, seven-bit sequence index, low parameter byte); `+4`
  assembly pointer; eight-byte tail. Bytes `+8/+9` are interaction selectors,
  not X/Y offsets; they are labelled per-record in the report and the
  remaining tail (`+10..+15`) is kept explicitly unlabeled.
- The pointer advances by the record size and then **jumps backwards to
  `0x13CD0C`**, which is visited twice: the script has an explicit loop, so the
  format includes control flow, not just a frame list.
- Sprite-assembly pointers observed: `0x13DEA0`, `0x13DE46`, `0x13DFEC`,
  `0x13E00A`, `0x13E04C`, `0x13E44C`. These target the next table to decode.

### Animation script structure checkpoint

The private decrypted ROM window now decodes 29 observed boss pointers into
six canonical programs plus aliases with
`tools/decode_avsp_animation_scripts.py`. The tracked report is
`data/avsp_animation_scripts.json`. Twelve selector-6 assemblies are decoded as
budget, object count, offset-table index, signed origin, then
`(code, attribute, layout-adjust)` entries. The layout chain advances by
`4 + s16(layout_adjust)`. All 12 pass the format-isolating pose check with zero
differing pixels; the independent position audit has a scoped pass but full
coverage remains open as recorded at the top of this handoff.

The updater disassembly from the MAME opcode space establishes the format:
normal pose records are 16 bytes, with duration at `+0`, flags at `+2`, and an
assembly pointer at `+4`. After `+0x10`, a negative flags word causes the
updater to follow the long pointer at the next address, making the apparent
20-byte transitions four-byte jump records plus a normal record. Bytes `+8`
and `+9` are consumed as interaction-table selectors by `0x1cf88` and
`0x1cf94`; they are not yet proven X/Y offsets. `0x88e16` copies all 16 bytes
into actor scratch, so the remaining tail semantics still need consumer-level
mapping. The decoder now writes those two selector bytes per record as
`tail_byte_8_selector` / `tail_byte_9_selector` and keeps `+10..+15` in
`tail_bytes_10_15_unlabeled` (raw `tail_hex` / `tail_bytes` are retained). In
the boss data byte `+9` is 0 for every pose and byte `+8` ranges over
{1, 2, 7, 8}; `+10/+11` hold a 16-bit word (6..9) with four zero bytes after.

Reproduce the structural decode after regenerating the ignored private MAME
window:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\decode_avsp_animation_scripts.py
```

The decoder expects the 0x13c000..0x13f000 script window, the 0x1fd1c8 table
window, and the 0x1e0000..0x200000 layout window. Regenerate those ignored
windows with `tools/mame_dump_code_spaces.lua` by setting `AVSP_ROM_FIRST`,
`AVSP_ROM_LAST`, `AVSP_ROM_OUT_PROGRAM`, and `AVSP_ROM_OUT_OPCODES`.

The associated opcode-space dumper is `tools/mame_dump_code_spaces.lua`; raw
program/opcode dumps remain ignored under `.deps\mame\actorprobe`.

The decoder/report hashes in the older structural checkpoint are superseded by
the goal-audit checkpoint hashes near the top/final repository-state update.
The opcode dumper itself remains:

- `tools/mame_dump_code_spaces.lua`:
  `1f22a221c87c5ab2bc07eeab0608cc2bb10d980f5a574cd5f73f0a4bf246ccd6`.

### Street-alien extraction checkpoint (Phase 2a, second actor)

Checkpoint commit: `5327c3a` (the clean extraction boundary; confirm with
`git rev-parse HEAD`). Documented 2026-08-18.

This generalises the ROM animation-record walker and the assembly-discovery
path — it reuses `tools/decode_avsp_animation_scripts.py` against a second
actor. It does **not** yet exercise the planned ahead-of-time 68000 code
translator or any `avsp_core_*` interface. The boss record format was the first
actor through that record path; the street-alien is the second, and it proves
the record path generalises. Findings from read-only scans of the existing
`.deps/mame/enemy_actions` per-frame dumps plus one short ROM-window boot:

- The street-alien (actor_id 31) occupies actor slot `0xFFA000` in the
  `enemy_actions` run, so its struct base is workram file offset `0x2000`. That
  run already has the full boss-equivalent per-frame dump set
  (`workram`/`objram_active`/`cps_a_regs`/`palette`, frames 4080..6200), so its
  programs need **no new capture**.
- Scanning all 2121 `workram_*.bin` for the `w1c:w1e` animation-script pointer
  yields **48 distinct pointers in `0x12D2F8..0x12EC74`** (hi-word `0x0012`).
  They canonicalise, through the same record walker, to **12 programs**.
- The record format is identical to the boss: 16-byte pose records (duration
  `+0`, flags `+2`, assembly pointer `+4`, 8-byte tail) plus a 4-byte jump
  record when the flags word is negative. Sample program `0x12D2F8` walks to 4
  poses (duration 6, tail byte `+8`=1, `+9`=0) and a `flags=0x8000` record
  whose jump loops back to `0x12D2F8` — the same explicit-loop structure.
- The 12 programs reference **28 distinct sprite assemblies in
  `0x12F5AC..0x130346`**, all within one dumped window
  (`.deps/mame/actorprobe/rom_window_12c_134.bin`, `0x12C000..0x134000`,
  SHA-256 `8df491bbb3f0e52f762f6064e8d40ed5419ff63bfe6134fb03270177a7aef417`),
  produced by `tools/mame_dump_rom_window.lua`:
  `set "AVSP_ROM_FIRST=0x12c000" && set "AVSP_ROM_LAST=0x134000" && set
  "AVSP_ROM_OUT=.deps/mame/actorprobe/rom_window_12c_134.bin" &&
  .deps\mame\mame0289\mame.exe avspu -rompath . -video none -sound none
  -nothrottle -skip_gameinfo -autoboot_delay 0 -autoboot_script
  .\tools\mame_dump_rom_window.lua`.
- Decoding those 28 assemblies against the shared global offset table
  (`0x1FD1C8`) and layout window (`0x1E0000..0x200000`) gives selector
  distribution **`{2: 2, 6: 5, 12: 21}`**. Selectors 2 and 6 reuse the boss
  dumps cleanly (selector-6 layout addresses `0x1FDC1C..0x1FDD44` are in-window).
  **Selector 12 is a new, unmapped assembly format the boss never used, and only
  its raw prefix is structurally suggestive — every field after the selector
  word is still unproven.** Across the 21 selector-12 assemblies the second word
  (`+02`, a selector-6 "budget" if the analogy held) is `0x0006` in 17 and
  `0x0002` in 4, and the fourth word (`+06`, a selector-6 "offset-index" if the
  analogy held) is `0x0002` in 10, `0x0003` in 7 and `0x2210` in 4. Those four
  `[0x000c, 0x0002, 0x0009, 0x2210]` heads break the selector-6 reading (a
  `0x2210` offset-index is implausible into the small layout table), so the
  field interpretation is **not universal**. The entry body and the meaning of
  every word after the selector must be established by the assembly-renderer /
  updater disassembly — exactly how selectors 2/6/10 were originally
  characterised — not by guessing from the raw words.
- `data/enemy_action_capture.json`'s per-frame `animation` field was re-checked
  against the live workram `w1e` word: **335/335 samples match** (e.g. frame
  4214 = `0xEC04` in both). It is a valid per-frame script-pointer index, not
  stale.
- The **player** is the only actor still missing RAM-side dumps:
  `tools/mame_capture_player_action.lua` has the object-bank tap and objram/
  palette/snapshot writers but no per-frame `workram` (`read_range`) and no
  `:cps_a_regs`/`:cps_b_regs` share dumps, so the player needs a lua edit plus a
  re-capture before its programs can be walked. The **stalkers**
  (`0xFFA240`/`0xFFA300`) already have the full dump set and follow the same path.

Next for the street-alien, and disassembly progress. Two corrections to the
earlier note, then the current evidence boundary.

**Correction 1 — the object is a 4-word CPS2 object descriptor, not a 2-word
pair.** The proven extractor (`tools/extract_avspu_stage1.py`,
`decode_object_entries`) reads each object as four consecutive 16-bit words
`[x, y, code, attribute]`: `screen_x = (x & 0x3FF) - VISIBLE_LEFT`,
`screen_y = (y & 0x3FF) - VISIBLE_TOP` with `VISIBLE_LEFT=64`,
`VISIBLE_TOP=16`; priority = `(x >> 13) & 7`; `tile_code = code +
((y & 0x6000) << 3)`; `attribute` bits 0-4 = colour, bits 8-11 = X-tiles-1,
bits 12-15 = Y-tiles-1, bit 5 = flip-x, bit 6 = flip-y. `STAGE1_OBJECT_GROUPS`
confirms actors occupy 4-word object slots. The earlier "each entry is a
(tile-code, position) word pair, code + 0x1000" reading is wrong.

**Correction 2 — these are three tilemap/video-RAM handlers, and `0x016b3c` is a valid third one.** `0x0169da`, `0x016a88` and `0x016b3c` all write **two-word tilemap cells** into CPS2 **graphics/video RAM** (`0x900000–0x92FFFF`); they do **not** write four-word CPS2 **object-RAM** sprites (object RAM is at `0x700000–0x701FFF` and `0x708000–0x709FFF`). `0x0169da` is the 64-cell variant (destination base `0x904000`, `andi #$3f`, setup `jsr $b2672`; reached by `jsr $169da.l` from `0x086dcc` and `0x086e00`); `0x016a88` is the 32-cell variant (destination base `0x908000`, `andi #$1f`, setup `jsr $b2bc2`; reached by `jmp $16a88.l` from `0x073f52` and `0x095f88`); `0x016b3c` is a valid third related handler. All read the assembly pointer from record+4. The `+0x1000` operation is proven **only** for this tilemap-writing path. The selector dispatch is **not** a
`cmpi.w` cascade (0 sites for #6/#12 in the whole 2MB); it is a per-selector
actor-list mechanism (0x16924–0x169ca push the actor onto per-type stacks at
`($6eXX,A5)`) plus a jump table (0x169cc).

**Established this session (read-only):**
- Selector 12 is the *dominant* street-alien selector: scanning every frame's
  current assembly gives `{12: 1770, 6: 202, 2: 101}`. The walk clip is
  selector-6; attack/hit/KO are largely selector-12.
- The animation-script pointer is a full 32-bit value at actor `+0x1C/+0x1E`;
  the JSON `animation` field is its low word (`w1e`) — the 335/335 match above
  is on that low word. The current record is read at the exact script pointer
  (it already lands on a record; no 16-byte re-alignment), and its `+4` is the
  current assembly pointer.
- The selector-12 assembly is **not** a flat `[sel, budget, count, ...]` list.
  Assembly `0x12F5DE` (frame 4253, an attack pose) is a repeating 15-word block:
  `[0x000c, 0x0002, 0x0009, 0x2210, 0x002a, 0xffb9, 0x0006, 0x463d, 0x0002,
  0x0018, 0x2710, 0x0024, 0xfffa, 0xfffe, 0x4605]`.
- The selector-12 assembly words are **not** the final object fields (for frame
  4253 the alien tiles carry codes `0x4600`/`0x4bf0`/`0x47bd`, attributes
  `0x5431`/`0x0131`/`0x1231`; none appears verbatim in the assembly). The
  transform is a **self-contained stream rewrite in the handler**, NOT the
  boss's offset-table (`0x1FD1C8`) / layout-window path.

**PROVEN tilemap handler + entry reads (from the disassembly, `disasm_full.txt`
basepc 0):** `0x0169da` is a tilemap/video-RAM writer (destination base
`0x904000`, `jsr $b2672`); `0x016a88` is the 32-cell sibling (base `0x908000`,
`jsr $b2bc2`); `0x016b3c` is a valid third related handler. The algorithm below
is **proven tilemap behavior** — it emits two-word cells into video RAM, NOT
four-word CPS2 object-RAM sprites, so it is the wrong sink for a sprite pose
cross-check. Dispatch (0x016924–0x0169ca) routes by the actor-type byte `(A6)`,
pushing the actor onto per-type lists at `($6eXX,A5)`; the assembly selector
(word 0) is read and discarded, not a dispatch key at this level. The handler
reads the assembly pointer from `record+4` (`016a1a`) and then:

```
016a1e: move.w (A1)+, D6     ; assembly[0] = selector (read, discarded)
016a20: move.w (A1)+, D6     ; assembly[1] = OUTER loop count (tilemap rows)
016a22: move.w (A1)+, D5     ; assembly[2] = INNER loop count (cells/row)
016a28: move.w D5, D0
; per entry (inner loop, 016a2a..016a58):
016a2a: move.w (A1)+, D1     ; P = next assembly word
016a2c: bmi    $16a80        ;   P < 0  -> blank-slot path
016a2e: addi.w #$1000, D1    ;   P >= 0 -> P += 0x1000  (tile code, absolute)
016a32: move.w D1,  (A0)+    ;   emit (P + 0x1000)
016a34: move.w (A1)+,(A0)+   ;   emit Q (verbatim)
016a36: ... andi #$3f / bank-rollover ... dbra D0
016a7a: dbra D6              ; outer loop: tilemap destination advances to the
                             ;   next row (video-RAM addressing, +0x40)
; blank-cell path (016a80):
016a80: move.w (A1)+, D1     ;   discard one assembly word
016a82: lea    ($4,A0), A0   ;   skip 4 bytes = 2 tilemap words (one empty cell)
016a86: bra    $16a36
```

So each entry is a **2-word group (P, Q)** written to the video-RAM tilemap:
`P >= 0` → the tilemap receives `(P+0x1000)` then `Q` (a two-word cell);
`P < 0` → one assembly word is consumed and A0 advances four bytes (two
tilemap words = one skipped cell). Header = `[selector, outer_count,
inner_count]`; the data cursor starts at assembly word 3. This is the exact
word→**tilemap-cell** mapping; it is read from the disassembly, not inferred,
and it is **proven tilemap behavior only** — it does not describe CPS2
object-RAM sprite emission.

**Frame-4253 object comparison — INVALID as a selector-12 sprite-decoder gate
(wrong sink).** I emulated the `0x0169da` tilemap algorithm above and compared
its output to the captured `objram_active_04253.tsv`. That comparison is **not a
valid sprite-decoder gate**: `0x0169da` writes two-word cells into **video RAM**
(destination base `0x904000`), whereas the captured street-alien objects live in
**CPS2 object RAM** (`0x700000–0x701FFF` / `0x708000–0x709FFF`). Comparing a
tilemap writer's output to object RAM tests the **wrong renderer**, so the
earlier "RED" result proves nothing about the sprite path. The `+0x1000`
transform is proven **only** for the tilemap path and must not be applied to
object-RAM fields.

**Unproven lead (sprite path — keep, do not bake in):** the captured frame-4253
object codes (slots `[80,88,92,96]` = `0x4df8 0x4b04 0x4a88 0x4958`, plus slot
21 `0x4ef0`) appear **verbatim** — not in `+0x1000` form — in the ROM at
`0x12FE06–0x12FEEE` in a `[code, attr_template, delta]` 3-word structure, in
slot order 20–24: `0x4df8 0x0110 0x0000 | 0x4ef0 0x0510 0x0000 | 0x4b04 0x2510
0x0038 | 0x4a88 0x1410 0x0004 | 0x4958 0x0110 0x0000`. The attr high bytes
(`01 05 25 14 01`) match the captured attrs (`0x0131 0x0531 0x2531 0x1431
0x0131`); the attr low byte is `0x10` in ROM vs `0x31` captured. This is a
**strong lead for the actual sprite path**, but its format and pointer
relationship are **unproven** and must not be baked into the das decoder.

**Historical next investigation — SUPERSEDED by the proven dispatcher/emitter
below.** At this point the correct direction was to locate the real 68000
object-RAM writer instead of comparing `0x0169da` tilemap output. The session
initially proposed probing both `0x700000` and `0x708000`; the later static
chain proved `0xA99DC` sets `A1=0x708000`. The current contract therefore uses
only 20 logical watchpoints at `0x7080A0..0x7080C6` and records `0x8040E0` as
bank metadata. The source-data gate and prohibition on promoting selector 12
remain current.

**Historical object-RAM location hunt — superseded by the proven emitter
below:** empirical probing before the dispatcher was found recorded:
- **Object-bank select register = `0x8040e0`** (word, bit 0 = bank). It
  **alternates every frame**: 4250→1, 4251→0, 4252→1, **4253→0 (`:objram1`
  active)**, 4254→1. Frame 4253 displays from bank 0; the writer may target the
  *other* (back) bank — do not assume active == write bank.
- **68000 work RAM = `0xFF8000–0xFFFFFF`** (actors at `0xFFA000`, confirmed).
  All CPS-A registers (`cps_a_regs_*`) point at **video-RAM** bases
  (`0x9000xx`), never object RAM.
- **`0x708000+0xA4` (word 82) is the only object-RAM-ish write found near
  `0x708000`**: it fires every frame with a **constant `data=0x00000020`**,
  writer **PC `0x000AA760`**. **Now identified** (see the proven emitter
  below): it is one part's attr low word from the per-actor sprite emitter
  (`move.w #$20, D2; bsr $aa740` at `0xAA7F0`). It is **not** the street-alien
  body (which carries code `0x4df8`, x `0x814f`) — that body is emitted by a
  different variant of the same routine family.
- **`0x700000+0xA4` never fired** in the window, and the street-alien code
  `0x4df8` appears at **no** probed base: `0x000000–0x01FFFF` (0x1000 step) and
  `0x700000–0x712000` (0x2000 step). The CPU writer window was not identified
  by that sweep; the later dispatcher proof below resolves it as `0x708000`.
- **MAME 0.289 Lua API limits (empirical):** without `-debug`, `cpu.get_reg("PC")`
  ERRs and `machine.devices[":maincpu"].debug` is **nil**. Under `-debug`,
  `debug:wpset(program,"w",addr,size,nil,action)` works and the `action` string
  exposes `wpaddr`/`wpdata`/`pc`; but `debug:execute()` / `debugger:execute()`
  **do not exist** (no `meminfo`/`memmap` via execute), `-listmem` is **not
  supported** in this build, and `machine.memory.shares` exposes **no CPU
  address range** (iterate `regions`/`shares` with `pairs`). `autoboot_command`
  **hangs**; a from-boot run is slow/unreliable here. State-load + **≤34**
  `wpset` watchpoints is the reliable method; a 128-watchpoint sweep **stalls**
  in load/install.

**PROVEN object-RAM sprite emitter (this session, from
`.deps/mame/actorprobe/disasm_full.txt`, basepc 0).** The CPS2 object-RAM
sprite table is written by a **per-actor, per-part routine at `0xAA644–0xAA7F8`**
which calls a **4-word entry-writer subroutine at `0xAA740–0xAA75E`**. The
writer emits exactly one 4-word object slot per call:
```
0aa740: subi.w #$8, D0            ; D0 -= 8
0aa744: subi.w #$8, D1            ; D1 -= 8
0aa748: andi.w #$3ff, D0
0aa74c: or.w   ($2e,A6), D0       ; X |= context flags
0aa750: move.w D0, (A1)+          ; word 0 = ((D0-8)&0x3ff)|($2e,A6)
0aa752: andi.w #$3ff, D1
0aa756: ori.w  #$0, D1
0aa75a: move.w D1, (A1)+          ; word 1 = (D1-8)&0x3ff
0aa75c: move.l D2, (A1)+          ; words 2,3 = D2 (32-bit code/attr)
0aa75e: rts
```
Per slot: **word0 = X+flags, word1 = Y, words2-3 = D2** (D2 high word = code,
low word = attr). **`A1` is the object-RAM write pointer** (the routine
observed writing to `0x708000`).
**Per-part source reader (drives the writer).** Register map: `A4` = actor
work-RAM slot (street alien = `0xFFA000`); `A2` = `($1c,A4)` = the
**animation/assembly pointer** (matches the prior "actor +0x1C" finding); `A0` =
`($50,A4)` + per-part offset = source-data pointer; `A5` = work-RAM base with
the actor's X at `(-$64f2,A5)` and Y at `(-$64f4,A5)`; `A6` = context with
`($8,A6)` = a type (compared to `#$14`) and `($2e,A6)` = flags OR'd into word0.
The reader computes `X = baseX + signedByte(source)`, `Y = baseY -
signedByte(source)`, seeds the code/attr long `D2` with `#$100000`/`#$200000`/
`#$310000` depending on actor type `($8,A4)`/`($8,A6)`, then `bsr $aa740` per
part (up to 4 parts/actor). The base X/Y at `(-$64f2,A5)`/`(-$64f4,A5)` is
itself set (`0xAA5C4–0xAA616`) from `($10,A4)`/`($14,A4)` minus `($278,A5)`/
`($27c,A5)` plus constants, sign flipped by `($f,A4)` flag bits.
**TWO emitter families** both advance `(A1)+` (the object-RAM write pointer),
so the per-frame object table is a series of 4-word entries emitted by
whichever family the per-actor dispatcher selects:
- **Family 1 (`0xAA4A4–0xAA598`) = the code-carrying body emitter.** It writes
  `move.l D3,(A1)+; move.l D2,(A1)+` (two longs = `[X, Y, code, attr]`), where
  **`D2` is a source long loaded via `move.l (A0)+, D2`** — so the **tile
  CODE (e.g. `0x4df8`) is the HIGH word of the source data**, and the attr
  (low word) is the source low word modified by `andi.b #$e0; add.b ($e,A4);
  eor.b D1(type)`. D3 = `[X<<16 | Y]` (X = `(-$64f4,A5)`-based, OR'd with
  `($2e,A6)`; Y from source). **This is the variant that carries the
  `0x4958–0x4ef0` codes (the street-alien body).** Several sibling variants
  (0xAA4A4 / 0xAA4F0 / 0xAA51E / 0xAA55C) differ in how the code/attr low byte
  is derived (mirroring / palette / type XOR).
- **Family 2 (`0xAA644–0xAA7F8`) = the effect/glow emitter** (the `bsr $aa740`
  writer above), D2 seeded by `#$100000`/`#$200000`/`#$310000` (the `0x20`
  part observed at `0x708000+0xA4`).
**Dispatcher + full pipeline (this session).** The per-frame object table is
built by the routine at **`0xA99DC`**: it sets **`A1 = 0x708000`** (`movea.l
#$708000, A1`), writes an 8-word **header** (`move.l #$20000100,(A1)+; move.l
#$0,(A1)+` ×2), then calls the per-actor emitters **`bsr $aa9a2 / $aa840 /
$aa886 / $aa8ae / $aa8d6 / $aa9fc / $aa8ea / $aa8c2 / $aa89a / $aa8fe`** (each
loads its actor's `A4`/`A5`/`A6` and emits 4-word entries to `(A1)+`, advancing
the pointer), writes a 4-word **trailer** (`move.l #$80008000,(A1)+` ×2 = the
CPS2 end-of-list marker), and returns to the main loop (`jmp $1388`). So
**`0x708000` is the object-RAM write buffer**; the street-alien's five slots
(oracle words 80,84,88,92,96) are emitted by one of those per-actor `bsr`
targets (family-1 variant), positioned after the header + preceding actors.
The per-actor routines in the `0xAA840–0xAA9FC` range are the callers that set
up `A4`/`A5`/`A6` and branch into the family-1/family-2 writers above. The
per-type emitters **`0xAA886 / 0xAA89A / 0xAA8AE / 0xAA8C2 / 0xAA8D6 / 0xAA8EA`**
each read a per-type actor count from `($6e82/$6e87/$6e88/$6e8a/$6e8b/$6e91,
A5)`, load a base pointer from `($6e5c/$6e66/$6e68/$6e6c/$6e6e/$6e7a, A5)`, and
jump to the **common per-actor loop at `0xA9B48`** (which sets up `A4`/`A5`/
`A6` per actor and reaches the family-1/family-2 writers). **`A5` is the main
work-RAM game-state base**; the actors sit at `A5 + offset` (e.g. `($380,A5)`,
`($480,A5)`, `($6a80,A5)`), so the street alien's `A4` is `A5 + <its slot
offset>`. `0xAA840` is an actor-list **sort** (by `($18,A3)`), and `0xAA910`
initializes the per-type pointer/count fields.
**Third-level dispatch (this session, `0xA9B48` internal).** The common loop is
itself a **per-actor-type jump table**: `movea.w (A3)+, A6` (load the actor),
`move.b ($8,A6), D0; lsr.w #1, D0` (index = actor **type `($8,A6)` >> 1**),
`move.w ($24,PC,D0.w), D0` then `jsr ($20,PC,D0.w)` — a **jump table at
`0xA9B80`** with target `0xA9B80 + table[type>>1]`. So each actor is dispatched
to a **per-type handler** (e.g. `0xA9B90`/`0xA9BA0`, `0xA9CB4`, `0xA9C5C`; the
`0xA9CB6` handler begins `movea.l ($1c,A4), A0`), which then drives the
family-1/family-2 emitters. The full chain is therefore:
`0xA99DC` (dispatcher, `A1=0x708000`) → per-group emitters `0xAA886–0xAA8EA` →
common loop `0xA9B48` → **per-type jump table `0xA9B80`** → per-type handler →
family-1 (`0xAA4A4–0xAA598`) / family-2 (`0xAA644–0xAA7F8`) writers. Which of
the six per-group emitters owns the street alien (actor slot `0xFFA000`), and
which per-type handler its type selects, are not yet determined — both depend on
the street alien's type/count fields at frame 4253 (a runtime value).
**Still to resolve (do NOT treat the street-alien reproduction as done):**
(1) **RESOLVED — `A1` (object-RAM write base) = `0x708000`, set at the
dispatcher `0xA99DC`** (`movea.l #$708000, A1`); the table is header +
per-actor entries + `0x80008000` trailer. (2) the exact per-part source layout
(the `(A0)`-relative fields for the family-1 `[code, attr]` long and the X/Y
deltas) and the `($50,A4)`/`($1c,A4)` → `0x12FE06–0x12FEEE` link, and which of
the ten per-actor `bsr` targets emits the street alien (actor slot `0xFFA000`);
(3) reproducing the five frame-4253 slots exactly (family selection, order,
base X/Y, deltas, code high word, attr low word, palette/type XOR, the `(-$8,·)`
offsets, the `& 0x3ff` + `($2e,A6)` flags, and the preceding-actor entries that
position the street alien at words 80-99).
**Concrete next step (resume here):** (a) **[DONE]** dispatcher + `A1` base
found (`0xA99DC`, `A1=0x708000`); (b) **identify which of the ten per-actor
`bsr` targets (`$aa9a2/$aa840/$aa886/$aa8ae/$aa8d6/$aa9fc/$aa8ea/$aa8c2/
$aa89a/$aa8fe`) emits the street alien** (actor slot `0xFFA000`): read that
routine's `A4`/`A5`/`A6` setup and which family-1 variant it reaches; (c) map
the per-part source layout (`(A0)`-relative fields for the `[code, attr]` long
+ X/Y deltas) and the `($50,A4)`/`($1c,A4)` → `0x12FE06–0x12FEEE` link;
(d) a focused wpset (≤34, state-load frame 4200) on `0x708000` words 80-99 to
capture frames 4214 and 4253 with writer PCs while recording `0x8040E0`, then
match each slot to its family-1 variant and source long; (e) reproduce both
five-slot lists exactly (the gate).
The `0x12FE06–0x12FEEE` lead and the "do not promote selector-12 until all five
slots reproduce exactly" gate stand as above.

**Repository state:** the unrelated untracked directory `Marvel Super Heroes vs.
Street Fighter/` is present in the working tree; it is not part of this project
and is left untouched. All untracked one-off diagnostics
(`tools/diag_sel12_*.py`, `tools/probe_*.py`, `tools/diag_*.py`, etc.) are
preserved. The Phase 2a extraction checkpoint commit is `5327c3a`.

### Next steps for this direction

1. [Done] All 408 geometry frames now match a decoded assembly in the 28-assembly
   JSON (was 162 unmatched at the 12-assembly scope). The record-pointer timing /
   shared-code-set selection is also resolved: the actor-slot record pointer at
   frame f−1 selects the true sibling table and drives all 63 sibling-delta parts
   to exact (sibling-delta now 0).
2. [Done] The 16-byte record tail is labelled per-record in the report: bytes
   `+8`/`+9` are interaction-table selectors (readers `0x1cf94` / `0x1cf88`;
   `0x88e16` copies all 16 bytes to scratch) and bytes `+10..+15` are kept
   explicitly unlabeled pending a proven consumer (raw tail retained).
3. [Bounded] The `x=0/y=-4` settling (8 parts) is the only non-zero residual
   in scope and is formally bounded (see above); it is a whole-pose one-step
   settle trail. Derive it by disassembling the object-Y-from-world-Y writer;
   resolving it makes `--require-exact` pass.
4. Decode actor-local hitbox records for all required player/alien/Stalker/
   Chrysalis poses and replace inferred range/contact schedules.
5. Locate and extract Round 1 spawn, camera, scroll and trigger tables.
6. Disassemble one complete labeled AI writer path, map only the actor fields it
   consumes, and identify/record PRNG use before translation.
7. Extend ROM animation extraction to every required Round 1 actor, then build
   the SH-2 interpreter and retain captures only as regression oracles.

Note on RNG: if AI decisions consume a PRNG, functional parity requires the
same generator and call order for behaviour to match, even though exact frame
equality is no longer the target. Identify RNG use before translating AI.

### External resources found 2026-08-17

Web research turned up three externally documented resources that change how
much of this work has to be derived from scratch. None of them are ROM data;
they are documentation and open hardware descriptions.

**1. AvP retains Capcom's own development tools in the retail ROM.** Documented
by the sudden-desu.net teardown. This is the highest-value find, because two of
the tools produce exactly the data functional parity needs:

- `0xFF81C7` byte, non-zero, is the master debug enable.
- `0xFF806C..0xFF806E` cache debug DIP rows 1..3. Relevant bits: row 2 bit 7
  **display hitboxes**, row 2 bit 6 **display stage collision**, row 1 bit 0
  entity spawner plus info display, row 1 bit 1 entity monitor, row 1 bit 2
  player monitor, row 3 bit 2 extended entity info, row 3 bit 1 disable CPU in
  attract demos.
- `0xFF81D8` enables the software switch interface, which disables the entity
  spawner because their inputs conflict.
- A hidden test menu runs when `0xFF21AA` equals 2 during the standard test
  menu; nothing in the retail code sets it. It contains a character/pattern
  viewer with hitbox measurement, scroll-layer viewers with a collision "Hit
  Mode", a story-text viewer, and per-actor arrangement tools.
- Three debug routines survive but are disconnected, at disassembly offsets
  `0xB1998` entity info, `0xB1866` player info, `0xB1A84` extended entity info.
  They need `A6` set up and `D0=0` inside a task context.
- The entity spawner is driven by **Player 4** inputs, which standard MAME AvP
  configuration does not provide.

Why this matters: the port currently infers hit windows indirectly by watching
health values change across captured frames, which is how the boss contact
offsets 21/55/97 were derived. The game will draw the real boxes. The same
applies to stage collision, which is currently approximated.

**Initial failures are resolved.** Writing the RAM flags every frame does not
work, and loading `avspu_stage1_boss_12660` with the DIPs does not rerun boot
initialisation. Cold boot with Development hardware and the active-low fields
held from frame 0 still leaves the retail ROM's cache bytes clear because its
physical-DIP-to-RAM copy routine was removed. The verified path injects
`FF806C |= 01` plus the requested `FF806D` row-2 bit once at frame 1200, after
startup RAM clearing. The game's own `0x1434` routine then sets `FF81C7=01` by
frame 1230 and retains it. `tools/mame_probe_debug_overlays.lua` and the
Round 1 capture scripts implement and validate this path.

**2. Complete CPS2 hardware schematics.** Loic Petit's project publishes
schematics for the A-board, B-board, E-board and QSound amplifier, plus reverse
engineering of the custom chips DL-0921 (CPS-B-21), DL-1727, DL-1827, DL-1927
and DL-2027, with an online viewer. This is authoritative documentation for
layer assembly, palette copying, raster effects and video timing, which is what
the Saturn VDP1/VDP2 path has to reproduce.

**3. Open FPGA cores.** Jotego's jtcores/jtcps implement CPS1/1.5/2 in Verilog
and the repository also carries KiCAD schematics of arcade boards.

Confirmed independently: CPS2 work RAM is `0xFF0000..0xFFFFEF`, which is
consistent with the actor array at `0xFFA240` and the debug flags above all
living in the same region.

### FPGA cores

The user raised leveraging FPGA cores. They help the rendering half, not the
logic half, and are worth using for exactly that: an open Verilog CPS core is a
precise specification of sprite/tilemap priority, masking, and palette
behaviour, which is what the Saturn VDP1/VDP2 path must reproduce. Game logic
still lives in the ROM, so cores do not shortcut AI or animation scripts. Their
second use is as an independent oracle to cross-check MAME where MAME's
behaviour looks driver-specific, as already happened with the RGB32 frontend
screen.

## 2026-08-17 stock-MAME overlay checkpoint

The critical-path Phase 1 instrument now works in stock MAME 0.289. The exact
activation sequence is:

1. Persist `:HW_TYPE` Hardware = Development and the active-low overlay DIP
   fields before frame 0 in an isolated configuration directory.
2. Cold boot the retail `avspu` ROM.
3. At frame 1200, after startup RAM clearing, inject the retained
   software-switch bytes once: `FF806C |= 01` and `FF806D |= 80` for hitboxes
   or `40` for collision.
4. Let the game's own routine at `0x1434` derive master enable `FF81C7=01`; it
   is active by frame 1230 and remains active without further RAM writes.

Physical DIPs alone are a recorded negative control, not the solution. With
Development mode and the correct port reads already active, `FF806C`,
`FF806D`, and `FF81C7` remained zero because the retail ROM removed the copy
routine. Do not repeat that path. Also note that Start suicides a live player
when the debug master is active; the deterministic route therefore pulses
Start only for frontend selection or while health is zero/invalid during a
continue.

Tracked entry points and SHA-256 hashes:

- `capture_debug_overlays.ps1`:
  `bd5ae530b322c172c846e2522c048301bb89e7efbe8814b886f533ad9d234ebf`
- `capture_round1_debug_overlays.ps1`:
  `be98c94c421ae1f322ec680f6d278614e0550e6a2581b3960a748ad3942ae395`
- `tools/mame_configure_debug_switches.lua`:
  `194e3a11167d70004372134982fa29da0cce04a0aaaa7d2a27350d3e2bfbaab4`
- `tools/mame_probe_debug_overlays.lua`:
  `c7064f17edf43c04ad3474c0a40132dd63b234ea02198bb2f71c024a9c197a6c`
- `tools/mame_capture_round1_debug_overlays.lua`:
  `6f7383ba90b2002e53cb473ca448ff330e4f2c4825223738c8a8b3756f3aed56`
- `tools/analyze_round1_debug_overlays.py`:
  `27663db07a5f3686e6efd4b5e2047258d9de8a729e7706aa21649cb640656d74`
- `data/round1_debug_overlays.json`:
  `a49c7d01e4bfa050c480b8d5a9dc6a6a2feb69a44ba230f900d2f3fb09a395d5`

Raw ignored evidence:

- Hitboxes: frames 4201..15000 at cadence 1, 10,800 synchronized screenshots
  and actor-RAM samples, 124,416,000 RAM bytes. SHA-256 of `actor_state.bin`:
  `3a8a76751e9a5a0f857afeb35cdc2737f40cec8fea1cb2cf05241c908de24a7a`.
  Visual evidence covers the player, street aliens, Stalker and Chrysalis;
  frame 15000 is the Round 1 results screen.
- Stage collision: frames 4201..17791 at cadence 30, 454 synchronized samples,
  5,230,080 RAM bytes. SHA-256 of `actor_state.bin`:
  `6731a17d28186f84097ca243915d7911599afcae8548bebd3e74dcc2bc1df1a3`.
  Frame 17791 is the first post-boss dialogue and stops before Round 2 play.
- The tracked manifest hashes the key screenshots and validates both datasets.
  These are **capture-exact debug evidence**, not Saturn assets.

Reproduce or validate from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_round1_debug_overlays.ps1 -Mode Hitboxes
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_round1_debug_overlays.ps1 -Mode Collision
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_round1_debug_overlays.py
```

Add `-Refresh` to a capture command only when intentionally replacing its raw
ignored dataset; it also regenerates that mode's cold-boot seed state.

The earlier 15000-frame collision run was structurally valid but ended in the
live Chrysalis fight. Extending to 18000 proved the route crossed into Round 2;
the final deterministic boundary was then tightened to 17791. The first full
hitbox continuation also reached a Continue screen because the route only
recognized health zero; treating `health >= 80` as the invalid/continue state
fixed it. These errors are resolved in the committed scripts.

Remaining gate: the boxes are visibly captured but not yet decoded into
numerical actor-local geometry. Do not claim offsets 21/55/97 are replaced
until that extraction is complete.

## 2026-08-17 actor-labeled hitbox geometry checkpoint

`tools/analyze_hitbox_geometry.py` pairs four clear white debug boxes with the
white pivot markers and records the corresponding actor-state context in
`data/round1_hitbox_geometry.json`. This is **capture-exact overlay geometry**:
Stalker and player at frame 13700, plus Chrysalis and player at frame 14400.
The pivot-relative candidates are now explicit, for example Stalker
`[-16,-81,41,-4]` and the player `[-17,-80,28,-1]` at frame 13700. They are
not yet the native collision tables; all Round 1 poses and actor types still
need validation before replacing 21/55/97 and the Stalker contact schedule.

Reproduce it with:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_hitbox_geometry.py
```

Tracked hashes:

- `tools/analyze_hitbox_geometry.py`:
  `29bf26d2ca60685fbc910eecd8c7b890c354ecd96ad842e894f6bd33b6540de4`.
- `data/round1_hitbox_geometry.json`:
  `5cb1fb504d8a02b502518a2d0789eedd0cca9780104451366fc1017f215e8d8a`.

## 2026-08-17 screen-space bracket extraction checkpoint

`tools/analyze_hitbox_brackets.py` now deterministically recognizes the live
white corner-bracket geometry in selected hitbox screenshots. It handles both
the corner-run form and the complete top/bottom-edge form used by different
poses. `data/round1_hitbox_brackets.json` records the selected Round 1 frames
and their screen-space rectangles. The result is **capture-exact screen-space
evidence**, not actor-local collision data: HUD/text false positives still
require actor pairing, and no 21/55/97 offset has been replaced.

Validation command:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_hitbox_brackets.py `
    .deps\mame\round1_debug_hitboxes\overlay_04201.png `
    .deps\mame\round1_debug_hitboxes\overlay_04300.png `
    .deps\mame\round1_debug_hitboxes\overlay_06000.png `
    .deps\mame\round1_debug_hitboxes\overlay_07000.png `
    .deps\mame\round1_debug_hitboxes\overlay_11000.png `
    .deps\mame\round1_debug_hitboxes\overlay_13000.png `
    .deps\mame\round1_debug_hitboxes\overlay_13700.png `
    .deps\mame\round1_debug_hitboxes\overlay_14000.png `
    .deps\mame\round1_debug_hitboxes\overlay_14400.png `
    -o .\data\round1_hitbox_brackets.json
```

Tracked hashes:

- `tools/analyze_hitbox_brackets.py`:
  `a692e99163f23643dd83f6d977792269dddecb4cecbdc0c94a6a76215dda539c`.
- `data/round1_hitbox_brackets.json`: `c3654c7649abeddabcc16c4f767632f8e04aa53e30d38009b0401352227347f9`.

The first hash above is the canonical SHA-256.

## 2026-08-17 stock-MAME writer watchpoint checkpoint

Stock MAME's debugger watchpoint API is sufficient for the next phase. The
reproducible command is:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_actor_writer_watchpoints.ps1 -Frames 600
```

It loads `avspu_stage1_debug_hitboxes` at frame 4200, installs write
watchpoints over every 0xC0 actor slot's animation pointer (`w1c:w1e`), action
(`w06`) and state (`w0c`) fields through `maincpu.debug:wpset`, then runs 600
frames. MAME emits the raw writer lines to ignored `error.log`; the tracked
analyzer produces `data/actor_writer_watchpoints.json`.

Verified result: 2,132 events (1,632 animation-pointer, 210 action, 290 state).
The dominant animation writers are PCs `0x1652A`, `0x16550`, `0x165DE` and
`0x1665E`; state/action writers include `0x40E14`, `0x607E8`, `0x607F8`,
`0x608D4`, `0x6093C`, `0x60EDE`, `0x60F22`, `0x41BE2`, `0x41BEE`,
`0x6104E` and `0x61058`. These are discovery evidence, not translated code.

The first API attempt passed the string `"program"` as the debugger address
space and crashed stock MAME with an access violation inside
`device_debug::wpset`. Passing the actual `maincpu` program-space object fixes
it; the working script contains that correction. No custom MAME build was
needed.

Tracked watchpoint files and SHA-256:

- `capture_actor_writer_watchpoints.ps1`:
  `82d1cc3ce5d2671c83108a47ef38929a6f7fd8f65814f6cc1dd1ad2047f679a8`
- `tools/mame_watch_actor_writers.lua`:
  `15a81685a959c4c777963996f66e91da93fe896de9961b3412a8fe8c54b2de5c`
- `tools/mame_watch_actor_writers.txt`:
  `5017ec12909136dc1485bd65916c1539ccb4317ecc1e0c30efe61fe0b12fc85d`
- `tools/analyze_watchpoint_log.py`:
  `892eb4108abe9c66343bedd8e9d35d75937bd63d73f9df84045d71130b1d2758`
- `data/actor_writer_watchpoints.json`:
  `1377dd04392b7aea0283386cb81f00beeb78d9d24ce5c7a9e79555194bb3f0c0`

The dominant animation-writer PCs are now correlated with the ROM updater:
`0x16536`, `0x165c4` and `0x16644` advance 16-byte records and follow negative-
flag jump pointers. The first stock-MAME windowed debugger helper was
discarded, but the opcode-space dump is now machine-readable through
`tools/mame_dump_code_spaces.lua` and is recorded in the animation-script
checkpoint above. Next work is to decode the assembly records and pair the
extracted brackets with actor/object origins to obtain actor-local geometry.
Do not translate AI or replace native runtime tables until the pixel-exact pose
gate remains passing.

## 2026-08-17 animation-script audit: dedup + flags-word fix

Two confirmed bugs from the current decoded data have been fixed in the decoder:

1. **"29 programs" overcount** — Programs 0x13cc18 and 0x13cc28 are the same
   animation entered one record apart (and similar snapshots like 0x13ce08 →
   0x13ce28). The previous walker only followed 4-byte jump records, missing
   mid-animation snapshots landing on pose records. Fixed `_walker_to_first_pose()`
   to walk forward 16 bytes per pose, detect negative-flags jump records,
   follow them, and return the canonical loop target. Now correctly reports:
   - **29 script pointers from TSV → 6 unique canonical programs → 23 aliases**
   - Programs 1-2: 8-pose looping idle animations (sequences 0-7)
   - Programs 3-6: single-pose hold loops (KO/hit frames, flip_x=0x80)

2. **Word at +2 mislabeled as "flags"** — The high byte is
   `(flip 0x80 | sequence index)` and the low byte is an independent parameter:
   `0x06` = index 0, param 6; `0x0A` = index 1, param 10; `0x1B` = index 7,
   param 27; `0x00` = index 0, param 0. Decoded output now uses fields
   `word_plus2_raw`, `word_plus2_high_byte`, `word_plus2_low_byte`,
   `flip_x`, `sequence_index`, `param_byte`. The zero-terminator branch still
   never fires; all 6 programs end as "loop" (expected if AI exits by rewriting
   the script pointer).

Tools affected: `tools/decode_avsp_animation_scripts.py`
Data: `data/avsp_animation_scripts.json` SHA-256 changed.

## SPR4 binary oracle analysis notes

- All 17 `cd/SPR4/*.BIN` files are 18432 bytes (0x4800) except
  `HITFX.BIN` (2048) and `SHADOW.BIN` (512).
- Player files first non-zero at 0x74D–0x751; enemy files at 0x16AB–0x26EB.
- File is a grid of 192-byte stride records with header bytes encoding pose/mode:
  0x0A = idle, 0x66 = hit/special, 0xCC = special, 0x22 = shadow/mask,
  0xAA = padding/separator.
- Within each block, run-length encoded tile data uses 0xAA as separator and
  0x99/0x9D/0xDD/0x66/0x77/0x44/0x55/0x33 as tile color/luma values.
- The SPR4 format appears to pre-compose tiles from the CPS2 graphics region,
  providing an oracle for the selector-6 pixel check.

The SPR4 file format is **not yet decoded into named fields**. The goal is to
match the selector-6 assembly to the SPR4 pose pixel-for-pixel.

## Session notes: selector-6 tile decoding progress

**Superseded investigation.** The fixed-point/layout and packed-source guesses
previously recorded here were disproved by the count/origin/command decoder and
the 12/12 pose gate. Do not use them. Current selector-6 structure, position
model, exact limitations and commands are at the top of this handoff and in
`PARITY_PLAN.md` under "Pose and position checks".

## Resume in this order

**Superseded for new work by [PARITY_PLAN.md](PARITY_PLAN.md).** The numbered
list below finishes the frontend slice under the old capture-and-bind method
and is still correct for that slice. For anything beyond it, start at the
parity plan's Phase 1 and ROM-decode path. The custom MAME Phase 0 is a
contingency only.

1. Re-run `tools/analyze_round1_debug_overlays.py` against the ignored raw
   evidence and verify the tracked manifest is unchanged.
2. Decode the displayed hitboxes into numerical actor-local geometry for the
   player, street aliens, Stalker and Chrysalis. Validate those real boxes
   against, then replace, the inferred boss schedules 21/55/97 and the inferred
   Stalker contact.
3. Use the completed stock-MAME writer evidence to disassemble the remaining
   state/action PCs and identify AI/RNG consumers. Do not build custom MAME
   unless stock watchpoints demonstrably fail.
4. Extend the green 12-assembly boss format gate to the unmatched attack/hit
   poses and all required Round 1 actors; make the full position gate exact.
5. Compute the exact Round 1 referenced tile set, translate required 68k AI and
   stage tables to native C/data, and build the MAME/native event comparison.
6. Replace `player_pose_for_frame()` and the hand-written `cap_world_step()`
   behaviour only for actors whose required ROM tables and routines are proven.
   Measure composed cels versus per-tile VDP1 commands on hardware before
   choosing.

The older capture-and-bind resume list below is retained only as historical
context for the frontend slice; it is not the current work queue.

1. Verify branch, HEAD, clean status, the release manifest profile, and that no
   emulator retained a stale cue.
2. The repository is already an independent Git repo even though it lives
   under `BrooklynBangoutX`. Relocation to `C:\Game Dev\AvPSaturnCapabilityTest`
   is optional organization work, not a technical requirement. If relocating,
   preserve `.git` plus the ignored private ROM, dependency, emulator, audio,
   and capture inputs; verify the old checkout before removing anything.
3. RESOLVED, no change needed to the existing load schedule. The wipe does not
   need the character-select source block at all, so nothing conflicts with
   releasing it at CHARACTER_CONFIRM entry. Verified in `main.c`:
   - `activate_frontend_scene()` copies the surface into the VDP2 bitmap once
     and early-returns while the scene is unchanged (`main.c:737-752`), so
     the bitmap already holds the image after the confirm-entry frame.
   - `copy_snapshot_to_background()` is row-aligned at
     `background_bitmap + y * BACKGROUND_WIDTH` (`main.c:723-735`), so hiding
     one row is exactly the `jo_dma_copy(empty_row, target,
     BACKGROUND_WIDTH)` that function already performs.
   - `sequence_scene_for_world()` has no CHARACTER_CONFIRM case
     (`main.c:779`), so it returns -1 and `activate_route_sequence()`
     early-returns without touching the bitmap during the whole wipe
     (`main.c:817`). Nothing else rewrites the bitmap until ROUND_TITLE
     selects `AVSP_SEQUENCE_ROUND_1_TITLE`, which repaints it wholesale.
   The shutter is therefore a destructive progressive blackout of the VDP2
   bitmap, which is safe because the band only ever shrinks. Cost is eight
   row DMAs per source frame (four rows at each edge) of `BACKGROUND_WIDTH`
   bytes. It uses no cartridge RAM and is outside the phase-overlay budget.
   Implement it that way rather than extending any surface lifetime.
4. DONE for the wipe: the cadence-1 capture pinned the start frame at 1885
   and reproduced every other parameter. If the wipe model is changed, re-run
   both captures and require agreement again. A frame the shutter cannot
   reproduce is evidence the model is wrong, not a reason to restore a
   stored-frame fallback.
5. Characterize the two remaining confirm elements the same way: the
   1800..1852 selected-panel blink and the 1954..2034 title-text and
   `PRESS START` schedules. Extract the 110x37 nine-colour title text as one
   4bpp VDP1 cel.
6. Implement the shutter as the progressive VDP2 bitmap blackout described in
   step 3, driven by the fitted model, and add a host-model test that walks
   the band schedule deterministically. Then compose the Round 1 title from
   the existing native scene plus that text cel and a reveal schedule.
   Integrate
   menu -> character confirm -> Round 1 and run host, focused, full-route,
   then clean normal-release gates.
7. Verify the complete Gate 1 first-level route audibly in a captured real-time
   run.
8. Run the normal release on physical NTSC Saturn hardware with a digital pad
   and 32 Mbit RAM cartridge; verify crop/black bars, audio, KO, and Round 2.
9. Forward-test the reusable skill and assemble the full-port team evidence
   package only after the faithful hardware slice passes.

## Reproduction commands

From the repository root in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -BossKoTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run.ps1

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -EncounterTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run.ps1

# Reuse the raw frontend capture and reproduce the tracked report:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_frontend.ps1

# Reproduce the frontend segmentation result (needs the raw capture present):
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_frontend_segments.py --report

# Capture the wipe at cadence 1 and confirm the shutter model independently.
# This never touches .deps\mame\frontend:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_frontend_wipe.ps1

# Validate the character-confirm shutter model and its geometry report:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_frontend_geometry.py --report

# Measure an ad-hoc window without touching the tracked report:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\analyze_frontend_segments.py --window probe:1800:1900

# Regenerate the ignored raw frontend capture from verified MAME/ROM inputs:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\capture_frontend.ps1 -Refresh

# Final clean release only after full-route changes pass:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -Clean -Release

# Pixel-exact pose gate: each decoded assembly must reproduce a captured pose
# with 0 differing pixels. Currently 28/28 assemblies pass (29 oracle poses).
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\verify_pose_gate.py

# Scoped position audit: predicted from world(f-1) + ROM layout vs capture.
# Scoped PASS permits only explicit sibling-origin and observed settling
# classes. --require-exact is the goal-strength gate and currently must fail.
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\verify_position_gate.py
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
    .\tools\verify_position_gate.py --require-exact
```

The build scripts locate their bundled Python/MAME/Jo Engine dependencies; do not assume `python` is on PATH. A bundled Python is also available at `C:\Users\lambd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

## Superseded pixel-gate investigation

The earlier "selector-6 tile decoding blocked" conclusion is superseded. The
format-isolating pose check now passes 28/28 decoded boss assemblies (29 oracle
poses) with zero differing pixels. The valid remaining blockers are complete
actor/pose coverage, exact position coverage, native table/routine integration,
and the event-level parity harness; see the goal-progress index.

## Remaining product-level work

- Close all seven Capability Gate 1 conditions, starting with the street-alien
  object-emission proof. Replace capture-bound animation and hand-authored
  collision/AI/stage logic with ROM-derived tables and translated routines.
- Verify the complete Gate 1 route audibly and on physical NTSC Saturn hardware
  with a digital controller and 32 Mbit cartridge. This closes only Gate 1.
- Inventory and generalize extraction/runtime interfaces for every remaining
  actor, stage, item, weapon, routine and audio event, then integrate remaining
  rounds in arcade order with a cumulative route after each addition.
- Complete every selectable character's single-player route through final boss,
  ending and credits before adding the arcade revision's original simultaneous-
  player capability.
- Complete maximum-player stress and full-route validation with the required
  multitap, then run the final physical-hardware release gates.
- Keep the full-game goal at 0/9 until every global condition in `GOAL.md`
  closes; no Round 1 or single-actor proof may close one by itself.
- Forward-test and refine the private skill after Gate 1, then assemble the
  full-port evidence package before proposing anything beyond private use.

## 2026-08-18 Chrysalis ROM-composition vertical slice

Capability Gate 1 animation condition 1 and full-game animation condition 2
stay OPEN, but the **Chrysalis boss** now has a
proven *tile-composition* vertical slice: the runtime composes all 29 of the
boss's poses (all 6 actions) from ROM-referenced 4bpp tiles in the real Saturn
build, with no `/SPR4/*.RLE` boss archive in the animation path. Two caveats
keep this from being full ROM-driven animation: (a) production pose *selection*
still uses the capture-derived per-frame clip/step tables in
`generated/avsp_boss_animation.h` (`boss_pose_for_frame`), and (b) the ROM
animation-script / selector-6 interpreter is decoded only host-side (Python)
and is not yet linked into the runtime.

### What changed in `main.c` (committed at `c1de5f5`)

- New `compose_boss_rom_pose(int pose)` composes a boss pose straight from
  `generated/avsp_boss_rom.h`: for `pr = avsp_boss_rom_poses[pose]` it iterates
  `avsp_boss_rom_parts[pr->part_offset .. +part_count]` in reverse, writing each
  part's `avsp_boss_rom_part_tiles`/`avsp_boss_rom_tiles` 4bpp pen+1
  (high-nibble-first) into the `288x192` `boss_action_image.data`
  (`AVSP_BOSS_DECODED_BYTES` = 27,648), applying per-pixel flip and a pen-15
  transparency skip. Palette bank is 7; the sprite is added with
  `jo_sprite_add_4bits_image`.
- The retired archive path is gone from the RUNTIME ANIMATION PATH: the
  `BACT`/`BHIT`/`BKO` cold-boot / character-select loads, their four archive
  globals, two `#define`s, the teardown frees, and the cold-boot
  `load_boss_action_archive() &&` / `load_boss_supplement_archives()` guards in
  `frame_callback` were removed. `draw_boss` calls `compose_boss_rom_pose(pose)`
  on pose change.
- The three archives **remain on disc and are still SHA-256-verified by the
  build ISO gate** — they are now host-test regression oracles (`test.ps1` reads
  `build/avsp_cd/SPR4`), NOT the animation runtime path. `build.ps1`,
  `prepare_avsp_port.ps1`, and the ISO manifest member list are UNCHANGED on
  purpose.
- `tools/verify_pose_gate.py` gained a `--self-contained` mode
  (`_run_batch_selfcontained`) that reproduces the 12 canonical assemblies
  purely from the ROM assembly (layout words at `0x1FD1C8`) + the oracle
  archives, independent of `main.c`.
- `test.ps1` and `tools/decode_avsp_animation_scripts.py` carry small edits from
  the prior ROM-decode work (now committed at `c1de5f5`).
- **Unchanged (still capture-derived): pose *selection*.** `draw_boss` still
  calls `boss_clip_for_action` → `boss_pose_for_frame`, which walks the
  capture-derived `avsp_boss_step_counts/durations/poses` tables in
  `generated/avsp_boss_animation.h` to pick the pose index per frame. Only the
  *composition* of the selected pose moved to ROM tiles. The ROM selector-6 /
  control-word animation scripts are decoded by
  `tools/decode_avsp_animation_scripts.py` (host-only) and are not yet
  interpreted in C. This is the selection/interpreter gap Phase 1 must close
  before the Chrysalis path counts as fully ROM-driven.

### Gate results this session (all PASS, Yaba Sanshiro 2 v1.20.37)

The model cannot read emulator screenshots, so each boot was judged by pixel
statistics: a `CAPABILITY TEST FAILED: <asset>` banner is a near-black static
screen (low bright-pixel count, ~0 inter-shot diff); a passing scene is busy
(high bright-pixel count) and, when animating, changes between shots (nonzero
inter-shot mean-abs-per-channel diff).

- **Self-contained pose gate**: 12/12 assemblies reproduced exactly from ROM
  data, 0 differing pixels each (`facing_flip_x=True`, 29 oracle poses).
- **Focused KO build** (replays the 428-frame KO every 600 frames): bright-pixel
  57569/57771/43792, inter-shot diff 8.42/54.34 per channel — live animating
  corpse, no banner. ISO 5,552,128 B SHA-256
  `0F209A90B2DA76BC9A9D135D839346B66789781EC62227C4ED4CF866D29A3443`.
- **Focused HIT build** (resets to the hit action every 120 frames): bright-pixel
  100826/101020/100526, diff 8.53/10.57 — PASS. ISO SHA-256
  `0719FC5851AA1F8EBFF82FD538F45943B2E2CD1AA6FF8484ED1EBB0F7A2AE5E0`.
- **Full controller route** (Round 2 in 4,485 frames, then soak): bright-pixel
  99971/63551/85570, diff 65.31/44.80 — route progressing. ISO 5,554,176 B
  SHA-256 `C3B0622DBD87191C1EADFB80F7324F91EA9122E51E16C4AC948886F3277E29CD`.
- **Clean `-Release` boot** (title, static): bright-pixel 97479/97478, diff
  0.013 — title, no banner. ISO 5,541,888 B SHA-256
  `418B801CCE4C0781E17CAF7B45E9D24FEB2B85D02CCCFDC23478BEE8084569E8`; CUE 188 B
  SHA-256 `BFC58C7020D90952E93BEF7ECBA32DEA8D4FADDF6CE6A90E1054206EE1807B12`
  (unchanged). This is this session's release build; the whole-image hash is
  run-dependent (mkisofs), so the current manifest rebuild of the same
  checkpoint is the `31d53a6e...` image recorded in "Repository state" above,
  with identical member hashes.
- Every build re-ran the host tests + 12,000-frame soak green, and the ISO
  `/SPR4/*.RLE` + `/AUDIO/*.PCM` members matched their manifest sizes/SHA-256.

### Git state (after the Phase 1 checkpoint)

- Branch `prototype/private-capability-test`; HEAD is `c1de5f5`
  (`Stabilize Chrysalis ROM-composition slice (Phase 1 checkpoint)`), which
  committed `main.c`, `test.ps1`, `tools/decode_avsp_animation_scripts.py`,
  `tools/verify_pose_gate.py` plus the 11 new files (`avsp_anim_script.c/.h`,
  `tests/avsp_anim_script_test.c`, `data/boss_play_sequence.json`, and the
  `tools/{gen_boss_rom_data,generate_boss_anim_script,build_boss_tile_workset,
  verify_boss_rom_poses,test_boss_rom_data,ref_interp,
  trace_boss_play_sequence}.py` generators). The working tree is clean apart
  from intentionally-untracked one-off diagnostics / session helpers
  (`tools/diag_*`, `tools/probe_*`, `tools/locate_*`,
  `tools/{screenshot,analyze_shots,crop_shots,window_rect}.ps1`,
  `check_tail.py`) and git-ignored `generated/` / `build/`. No ROMs, captures,
  or generated assets are tracked.
- Phase 1 re-verification (this session, all fresh, committed code): the
  self-contained pose gate reproduces 12/12 assemblies exactly from ROM data;
  the host suite + 12,000-frame soak pass; and the focused KO/HIT, full Round 1
  route, and clean `-Release` boots each render busy and animating with no
  `CAPABILITY TEST FAILED` banner.
- `build/hardware_release_manifest.txt` (git-ignored, regenerated by the
  `-Release` build) records ISO 5,541,888 / `31d53a6e...`, CUE
  `bfc58c70...`. The three `boss_*_archive_load_phase` fields (`cold-boot` /
  `retired-character-select-before-cdda`) are **historical**: the runtime no
  longer loads `BACT`/`BHIT`/`BKO` for animation; the archives are on-disc
  oracles. Do NOT "fix" them by dropping the archives from the ISO or weakening
  the member-hash gate — that would remove the host-test regression oracle.
- The "Gate results this session" section above is the ROM-work session's
  verification (Yaba window 320x208; c1de5f5-era release whole-image hash
  `418b801c...`). The current manifest (`31d53a6e...`) is a same-checkpoint
  rebuild with identical member hashes; the whole-image hash is run-dependent
  (mkisofs), so verify by byte size + member hashes, not the whole-image value.

### What remains for condition 1 (not closed)

- **The Chrysalis path is a composition slice, not full ROM animation.**
  Production pose *selection* still uses the capture-derived clip/step tables
  in `generated/avsp_boss_animation.h`, and the ROM selector-6 / control-word
  script interpreter is not yet linked into C. Link the interpreter (or
  otherwise replace the clip tables with ROM-driven pose sequencing) so the
  boss's timing/sequence is also ROM-derived.
- The player, street aliens, and Stalkers still select captured
  `/SPR4/*.RLE` pose archives through generated frame tables. Decode their ROM
  programs/assemblies and route them through the same tile-composition path
  (retiring their archives) before condition 1 can close.
- Phase 1 (stabilize the Chrysalis slice) is **complete** and committed at
  `c1de5f5`; the Phase 1 checklist above is satisfied. Next is Phase 2 (prove
  the static translator) per `docs/PARITY_PLAN.md`.
