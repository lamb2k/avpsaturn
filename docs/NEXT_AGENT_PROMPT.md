# Next agent prompt: bounded S4 class/table-set and HIT/KO integration

## Scope lock

Execute only the bounded S4 body below. Do not start the frontend, S5 AI,
stage traversal, remaining cast conversion, or physical-hardware claims in the
same checkpoint.

Read the repository startup documents in the order required by `AGENTS.md`.
The newest handoff section, "Per-class table_set evidence", supersedes older
caller-search and broad HIT/KO-population language.

## Established evidence — do not re-derive

- Master actor dispatch: `0x01B980` indexes the 43-entry table at `0x01B9B6`
  with actor class byte `+0x02`.
- Per-class constants, checked offline and cross-matched to live instruction
  traces:
  - `0x00 -> 0x0012CE5C`
  - `0x06 -> 0x0013E97A`
  - `0x1F -> 0x00130AC8`
- Exact semantic anchors: HIT `5191..5226` is 36/36; KO `5330..5469` is
  140/140; both remain class `0x1F` with zero constant mismatches.
- Broader matches are record-signature populations only: 240
  `hit_anchor_record_signature` frames and 564
  `ko_anchor_record_signature` frames. Do not call them semantic HIT/KO.
- Corpus result: 25,104 active street actor-frames, zero per-class constant
  mismatches. Each class has a working corrupted-constant control.
- The current runtime drives only street WALK/ATTACK through ROM animation and
  uses one hardcoded `0x00130AC8`. HIT/KO/spawn remain counted `GAP` frames.
- The current defender hurt box is ROM-derived, but player attack reach and
  lane geometry remain ADAPTED. S4 is not complete.

## Required implementation

### 1. Canonical actor fields and generated lookup

- Add `class_id` (`+0x02`), `sub_state` (`+0x04`), and `action_word`
  (`+0x06`, big-endian) to `AvspActor`.
- Extend `avsp_actor_load()` and the actor-layout host test with field-for-field
  corpus equality.
- Generate a copyright-safe class-to-`table_set` header from
  `data/avsp_table_set_states.json`; do not duplicate the three constants by
  hand in runtime source.
- Expose `int avsp_table_set_for_class(unsigned char class_id,
  unsigned long *out)` and test all three values plus an unknown-class failure.

### 2. One canonical runtime collision view per enemy

- Maintain an `AvspActor` collision view for every native enemy slot.
- Populate its animation record from `AvspAnimFrame.addr`, selectors from that
  ROM record, facing/world coordinates from the existing native model, and
  `table_set` through `avsp_table_set_for_class()`.
- The approximate capability model does not produce real CPS2 class
  transitions yet. Assign class `0x1F` only to the already validated street
  WALK/ATTACK route and any HIT/KO anchor program that passes the replay check
  below. Do not synthesize class `0x00` or `0x06` transitions.
- Count unknown class, missing animation record, unknown collision family, and
  out-of-range selector as `GAP`. Selector zero remains the measured
  cannot-be-hurt verdict.

### 3. HIT/KO record replay check before runtime enablement

- Extend the sparse animation span generator to include every exact-anchor
  HIT/KO animation record plus reachable control records from the ROM.
- Identify a ROM program entry point and use the existing interpreter; do not
  create a captured per-frame record-pointer table.
- Add a host replay comparing the interpreter's animation-record pointer on
  every exact anchor frame.
- If either trajectory is not exact, leave that action on the counted ADAPTED
  fallback and record the first mismatch. The state routine that rewrites
  `+0x1C` then becomes an explicit S5 target.
- Enable ROM HIT or KO only when its replay has zero pointer mismatches. Retire
  `GAP` only on frames whose class, record, selector, family, and decoded hurt
  entry are all measured.

### 4. Same-frame collision ordering

Split the current combined tick so each frame does this once:

1. resolve the current ROM animation record and collision view;
2. run `cap_world_step()` against that view;
3. render from the same record;
4. advance the animation driver once for the next frame.

Do not retain the documented one-frame collision lag and do not tick animation
from both collision and rendering paths.

## Required checks

1. Actor field equality, class lookup, anchor replay, and runtime collision
   host tests.
2. Full `test.ps1`.
3. Focused Saturn build plus ISO-member size/hash verification.
4. `-EncounterTest` through `COMPLETE`.
5. Live readback of `runtime_ready`, lookup misses, selector-zero, `GAP`, and
   ROM-versus-approximate hit counters.
6. Final `-Clean -Release` title/menu boot.

Keep every fallback visible and counted. This body may reduce `GAP`; it cannot
close S4 while player attack boxes, post-hit routines, projectile/broadcast
paths, inferred boss/Stalker collision, and stage collision remain open.

## Repository safety

- Stay on `codex/avp-master-plan`.
- Preserve all unrelated untracked diagnostics.
- Stage explicit paths only; never use `git add .`, `git add -A`, broad stash,
  reset, clean, or destructive checkout.
- Never commit ROMs, raw captures, logs, generated copyrighted graphics, build
  output, emulator state, or disc images.
- Update `docs/AGENT_HANDOFF.md` newest-first and leave no emulator process
  running before stopping.
