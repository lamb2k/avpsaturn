# AvP learning notes

Running notes from the learning lane. This is research, not acceptance: it does not move
task status, candidate, gates or review state. Evidence tier is labelled on every result.
Source = offline decode of the private decrypted opcode image. MAME = retained pinned 0.289 ledgers.
Nothing here has been run on a Saturn.

## 2026-11-06: the top-level tick rule

Why this first: the handoff blocks interactive play on BLOCKED_MISSING_EXECUTABLE_TICK_CONTRACT,
and `main.c` still picks gameplay updates from captured cadence tables.

Result: most of the contract was recoverable from retained evidence, with no new capture.

### Kernel (source)

a5 = 0xff8000. Sixteen cooperative tasks of 0x20 bytes at 0xff0058, plus eight more at 0xff0158 (free stack below 0xff0a88).
Per-task fields: +0 state, +1 countdown, +2 SR, +4 PC, +8 USP,
+0xc stack top, +0x10 catch-up count (loop task).

| State | Meaning | Who sets it |
| --- | --- | --- |
| 0 | free | exit traps 1, 2, 9 |
| 1 | sleeping, countdown in +1 | trap 3 (0x106c) with d0 != 0 |
| 2 | suspended until woken | trap 3 with d0 = 0, trap 5 |
| 4 | ready | countdown reaches 0, trap 4 yield, trap 6 |
| 8 | was running, resumes via 0xdea | dispatcher at 0xde6 |
| 0xc | new, starts via 0xdfa | traps 0, 10, 7 |

- Dispatcher 0xd86: clear the vblank flag ff0266, walk tasks 0..15 in order with IRQs masked for
  each check. If the flag was set, restart from task 0. Dispatch table 0xdd0 = 0xde6, 0xdea, 0xdfa.
- Level 2 IRQ 0xe0e (vector 26): pushes video registers, samples inputs (0x1214), runs sound and
  palette steps, `ff8018++`, sets ff0266, clears ff81bc, and decrements the countdown of every
  state-1 task, moving it to state 4 at zero.
- Boot starts task 0 at 0x4538 and task 6 (offset 0xc0) at 0x14b44.

### Gameplay loop (source; task at ff00d8 in the Coffee Shop ledger)

```
0x808a: ff81bc = 0xff
        if ff81a6 == 0: ff8019++; 0x166ac (latch inputs); 0x8164 (dispatch on ff8000)
        if ff8054 bit 1: leave loop
        0x1188 (output latch)
0x8140: if ff81bc still set      -> catchup = 0; sleep 1 vblank
        else (vblank hit the tick): catchup++; if catchup >= 4 sleep, else run next tick now
```

Writer closure, from a raw opcode-image scan as well as the linear sweep:
- ff81bc: set only at 0x808a, cleared only at 0xe8c in the IRQ, read only at 0x8144.
- ff81a6: only writer 0x142e, which always stores 0 (`moveq #0,d1`). The pause branch is dead in this ROM.

### Fast-forward (source + MAME control)

Idle task 0x14b44, once per scheduler pass: if ff81b9 != 0, decrement the countdown of every state-1
task except index 3 (ff00b8). Then yield with trap 4.

So while ff81b9 is set, the gameplay task's one-vblank sleep ends on the next idle pass. Tick rate is
then bound by CPU time, not video. ff81b9 is set at 0x17154 after a pressed button (`input & 0x7f`
on a participating player, ff81bf mask) is seen on 5 polls via ff823a / ff1744. A second family at
0x158e0..0x15954 uses `& 0x70` and a 600-count timer; not yet witnessed.
Plain reading: holding a button fast-forwards scripted segments.

### Measured ticks per video frame (MAME, retained ledgers, frames 1972..5566)

Ticks = fetches of 0x808a per frame. Guard = ff81b9 nonzero at any logged event in that frame.

| Ledger | Guard off: 0 / 1 tick | Guard on: 1 / 2 / 3 / 4 / 5 ticks |
| --- | --- | --- |
| a3 baseline (b3 aggregate counts identical) | 40 / 3486 | 1 / 1 / 54 / 13 / 0 |
| p3 input perturbed | 40 / 3479 | 1 / 1 / 29 / 37 / 8 |
| m3 wake write suppressed | 1 / 3594 (no guard frames) | none |

- With the guard off, a frame never ran more than one tick, in any ledger.
- Suppressing the wake write removes every multi-tick frame: the m3 control is causal.
- Guard-on rate moves with the scene (mean 3.14 in a3, 3.66 in p3). It has no fixed source value.
- IRQ count was exactly 1 per frame on every compared frame of a3, b3 and p1.
- Overrun branch: 71 times in a3, 12 of them guard-off. Those guard-off frames still ran one tick,
  and catch-up never exceeded 2 in a3 (3 in p1). The four-tick limit was never reached.
- Zero-tick frames: the loop task is held inside a tick or in other route work during transitions
  (2260, 2265, 5524..5549, 5551..5559, 5562, 5564; 5566 is the window edge). The ledger's
  `stack_return` column only repeats the task pointer, so the holding caller is NOT yet identified.
- Task ff00b8 (index 3, excluded from fast-forward) suspended 3592 times in 3595 frames: it keeps
  video rate during fast-forward. Its job is not yet identified.

### What this means for the native rule

Proposed contract, not yet implemented or tested natively:

1. Run one gameplay tick per video frame while ff81b9 is clear. This is what the source does when a
   tick fits, and the measured overruns did not change the count. This is NOT the guessed loop the
   card forbids: it now has a source rule and a causal control behind it.
2. While ff81b9 is set, run N ticks per frame. N is a port policy, since the source's N comes from
   68000 speed. Measured MAME range is 3..5. Whether SH-2 can afford it is unmeasured.
3. Keep task 3 at video rate in both modes.
4. Model transition holds as a real suspended continuation, not as a frame table.

MAME's 68000 timing is an approximation of the board. Overrun counts and guard-on rates may differ
on real CPS2 hardware, so they are emulator-tier only. Rules 1 and 3 come from code and do not depend on it.

### Readiness list status (`analyze_oracle11_actor_scheduler.py --interactive-readiness`)

| Missing field | Now |
| --- | --- |
| Writers and IRQ/reset order of ff81bc, ff81a6 | Closed for writers and IRQ order; reset order not checked |
| Trap 3 suspend/resume, countdown, video boundary | Closed (source) |
| 0x14b44 owner: ff81b9 writers, excluded index 3, trap 4 | Mostly closed; 0x158e0 family and other writers unwitnessed |
| Input sampling order across resumes | Partly: hardware read in IRQ, latched per tick at 0x166ac |
| Hitstop order across resumes | Open |
| Route entry/exit suspend and resume inside a pool traversal | Open: holding caller not identified |
| Independent changed-input witness | p3 is one witness for the fast-forward window; not whole-route |

The analyzer and the state file were not edited. These are claims for the next implementer to verify.

### Reproduce

```
python tools/learn_dis68k.py 8060 80c0 8140 8170 14b44 14b92
python tools/learn_tick_rule.py .deps/mame/oracle11_scheduler_clock_a3
python tools/learn_tick_runs.py .deps/mame/oracle11_scheduler_clock_a3   # also p3, m3
python tools/learn_task_census.py .deps/mame/oracle11_scheduler_clock_a3
```

A linear disassembly sweep of the first 1 MB, for cross-references, is at E:\AvP\learning\sweep.txt.
It is private ROM-derived data and stays on this PC. A sweep can desynchronize in mixed code and data,
so only the ff81bc/ff81a6 closure was re-checked by raw scan; other writer lists are leads.

## Next learning steps, in order

1. Identify the holding caller for zero-tick frames: new bounded read of the a7 chain at 0x1060, or
   offline decode of the ff8000 route handlers at 0x8170.
2. Identify task 3 (ff00b8) and the other live tasks (ff00f8, ff0158, ff0178).
3. Hitstop: where it sits relative to the loop tick and the pool order 0x849e..0x84ce.
4. Check what the source does to audio and object output during fast-forward.

## 2026-11-06, second pass: the four follow-up questions

Same tiers as above. Nothing native was changed, and no card or gate moved.
Reproduce with `tools/learn_task_resume.py` and `tools/learn_dis68k.py`.

### Long-lived and transient tasks

| Task | Entry | Evidence | What it does |
| --- | --- | --- | --- |
| 0 (ff0058) | 0x4538 | source | Top-level start; fade wrappers at entry. Details not read |
| 3 (ff00b8) | 0xe658 | source, started at 0x53a0 | Per-player pass over ff8380/480/580, dispatched on +0xd4, with one-vblank sleep. Handlers read the coin/credit block ff8186 |
| 4 (ff00d8) | 0x8062 | source + MAME | Gameplay loop |
| 5 (ff00f8) | 0xb395a at 0x812a is the spawn found | MAME frames 5151..5523 only | Unconfirmed: the one resume value seen, 134590, is 0x20dbe |
| 6 (ff0118) | 0x14b44 | source | Idle: fast-forward decrement, drains the spawn ring |
| pool (ff0158, ff0178) | table 0x14b92, by command high byte | MAME resume values 0xab4c0 and 0x18164 match table entries 2 and 0 | Transient helpers from ring ff8086: fades and similar |

Task 3 is credit, continue and join logic by inference: its handlers read the coin block, but no handler
was traced end to end. This would explain why fast-forward excludes it: the player's credit timing keeps
real time. Task 3 is also stopped by route code (trap 2 at 0x157b0, trap 5 at 0x85e6, 0x878e).

### Zero-tick frames

Most likely holder (source, with an indirect MAME witness): the fade wait at 0x1614a and its siblings.
It sets ff837b, queues a helper via 0x1620a, then sleeps one vblank in a loop until ff837b clears.
Route handlers call it at around 25 sites.

- USP at the loop task's suspend is ff04a8 on normal frames and ff04a0 or ff04a4 in holds, so a hold is
  one or two calls deeper, inside the tick dispatched from 0x809e.
- Pool helper tasks are alive across the same frames (ff0178 5523..5540; ff0158 up to 5552).
- NOT proven: no ledger logged the return chain, and 2260/2265 show normal depth ff04a8. Those two are a
  different cause, not yet explained. A bounded read of the stack at 0x1060 would settle this.

Consequence for a native version: a route tick can span many video frames, so it needs a real
continuation or state machine around these waits.

### Hitstop

No global hitstop was found. It is a per-actor byte, +0x2c, consumed inside each actor body during pool
traversal, e.g. 0x40baa: if nonzero, decrement it and skip the action dispatch, then still run 0x167ac.
Similar test-and-decrement pairs exist at 0x197fe, 0x1aad0, 0x1b234, 0x1cfd2. The existing native
`source_hitstop` follows this shape.

- It counts gameplay ticks, not vblanks, so it would run faster in fast-forward.
- +0x2c also has other uses in other classes (long writes at 0x17676 and others), so match it per class.
- Order: inside the 0x8164 route dispatch of each tick, in the pool order 0x849e..0x84ce. Inputs were
  latched earlier in that tick by 0x166ac. Whether all classes consume it the same way was not surveyed.

### Audio and objects during fast-forward

Audio (source + MAME): commands go into a ring of 64 16-byte entries at ff0a88, head ff801e, tail ff8020.
The IRQ sends at most one per vblank, and only when the sound CPU handshake byte 61801f reads 0xff.
So extra ticks can queue faster, but output stays at most one per frame.
Measured: 921 commands over frames 2031..15191 (`oracle11_audio_sample_descriptors_a`), never more than one
in a frame. Only 1 of them fell in 5449..5559, so the ring under fast-forward load is barely witnessed.

Objects (source only): the object bank flip at 0x28ebc, 0x29b34 and the fade path only fires if ff81a2 is
zero; it then sets ff81a2 until the next IRQ clears it. At most one flip per vblank. In a 3-tick frame,
only the first tick that submits can flip. Not witnessed per frame in any ledger, and it was not traced
which tick's list the hardware finally shows.

For a port this suggests: run the extra fast-forward ticks without rendering them, and keep one audio
send per frame. This is a lead, not a tested design.

## Remaining unknowns

1. Stack chain at 0x1060 for hold frames, and the cause of 2260/2265 (needs a small new MAME read).
2. Task 5's real entry, and an end-to-end trace of task 3.
3. Per-frame object flips under fast-forward (MAME).

## 2026-11-06, source campaign: route wait closed

Method, gate and lanes are in AVP_SOURCE_CAMPAIGN.md. Reconstruction lives in `source_recon/`.

### Command/result continuation at 0x1614a / ff837b (source + MAME)

- Waiter: gameplay task sets ff837b, pushes command 0x0800 (fade out) or 0x0804 (fade in) with param 1 on ring ff8086, then sleeps one
  frame at a time until ff837b clears. About 25 sites plus 45 direct users of the flag, all shaped the same.
- Ring: head ff801a, tail ff801c, 64 pairs, full ring drops the command. Idle task (0x14b1c) pops one per pass, only with a free pool task.
  Command high byte selects a task entry at 0x14b92 (8 entries); low byte is the helper's state; param is +0x12/+0x13 (repeat, sleep).
- Helper 0xab4c0 starts child palette task (command 0x0000 or 0x0002), polls ff8378, on fade-out clears palette and object state via 0xac15e, sleeps 4+param, clears ff837b.
- Writers of ff837b: 70 reachable uses; only 6 clears, all in these helpers. Result of the "command" is just that flag and ff8378.
- Fade rule: per frame, each palette's first colour decides. Top nibble 0 means done, else add -0x1000 to all 16 colours. The sum of the four masks reaches -4 when black.

Durations, MAME probe hold_b, Coffee Shop route, 16 fades:

| Wait | Measured frames | C model |
| --- | --- | --- |
| Out, from full | 25 (419, 646, 952, 5523), 26 (1085, 1231, 1938) | 25 |
| Out, black, not flagged | 10 (82) | 10 |
| Out, already flagged black | 7 (1259, 5550) | 7 |
| In, from black | 18 (94, 986, 1114) | 18 |

The 25 versus 26 split is a one-frame phase; cause not identified. The fade-in stage constant is fitted to the measurement, since counting from source gives 18 or 19.
Native contract: `route_wait_begin/route_wait_frame` in `source_recon/avsrc_fade.c`. No frame table: duration comes from palette state and ff8378.

### Zero-tick frames: answered

All 39 are explained (MAME, hold_a, frames 1972..5566):
- 5524..5549 and 5551..5559: the gameplay task in 0x1614a, from the ff837b set/clear pairs at 5523/5548 and 5550/5557.
- 5562, 5564: the same flag set from 0xc05a at frame 5563. Its clear is outside the window.
- 2260, 2265: no sleep and no tick from task ff00d8 in the frame: the tick begun earlier ran through the whole frame. CPU overrun, MAME timing only. A port should not reproduce it.
- The stack read at 0x1060 was not needed and is unreliable: at the fetch tap SP gives junk chains. Set/clear pairs and task id settle it.

### Object flips under fast-forward (MAME)

ff81a4 toggles at most once per frame, across 3,594 frames: 0 flips 137, 1 flip 3,457. In all 68 multi-tick frames, exactly one. It usually comes first in the frame (55 of 68, before any new tick begins), so what is displayed is the tick that finished right after the vblank; later ticks' lists are not shown. Main writer 0xa9a42.
For a port: render one tick per video frame, and in fast-forward skip rendering of the rest. This is now measured.

### Second fast-forward path

0x158e0 was never fetched in the route (0 hits to 5566). Still unwitnessed. It stays source-only, no native need yet.
