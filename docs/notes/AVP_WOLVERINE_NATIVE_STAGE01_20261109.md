# Native Wolverine: Stage 0 identity and Stage 1 movement/timing, 2026-11-09

Lane `lane/wolverine-native-20261109`, from `aae2e10`. Tiers: HOST = the lifted game on a PC (tools/lift_runner, WSL gcc), replaying MAME 0.289 `avspu` input; BUILD = the SH-2 link (`saturn/rt/build.py`). EMULATOR (Yaba) and HARDWARE were not run. No ROM data or generated assets are committed; evidence is in `E:\AvP\learning\lane-wolverine-native`.

## 1. Does the host runner link the guest wrappers? No (until this lane)

`tools/lift_runner/apply_overrides.py` builds the golden-checked runner. It compiles `game_bind.c` with `-DHOST_CHECK` only: no `SAT_GUESTS`, so none of the `f_195ec`, `f_1cf54`, `f_1d03e`, `f_1d116`, `f_19f9a` wrappers exist; it never builds `guests.c` or `wolverine.c`; and it renames only the `overrides.txt` routines to `lifted_NNN`. A host run through it therefore cannot reach a guest hook or a fork. `tools/lift_runner/build_native_host.py` (new) builds the runner the way `build.py` builds the target: same `src/c*.c`, the `GUEST_WRAP` renames, `game_bind.c` with `-DSAT_GUESTS`, `guests.c`, `wolverine.c` and the generated fork file. The plain runner it can also build (`--guests 0`) is the "unmodified Schaefer" baseline. Wrapper reach is proved by per-routine fork-entry counters (section 2), not assumed.

## 2. Stage 0: identity (HOST, against MAME, golden_c1 = Schaefer, 272,171 vblanks)

Generator: `tools/wolverine/forkgen.py`. Nine entry routines (attack `24454`, special `24f04`, jump `2539e`, slot 0a `2501e`, gun `2576a`, pre-tick `255fa`, action 14 `24c64`, held item `24582`, table target `2f70`) plus eight private callees (`245a4 247a4 248e2 24aa6 24b2a 252aa 252e6 25606`) = 17 copied routines. Each copy is checked text-identical to its original apart from names at build time. The shipping fork is attack + special (2 routines, 13 KB of C).

Harness: `tools/wolverine/fielddiff.py` compares two `PDUMP` files vblank by vblank: the 61 interface fields (the word rows of `docs/guests/PLAYER_INTERFACE.md`) for both players, the whole 256-byte block of each, and five outbound-region hashes (collision lists, effect spawns, globals, enemy/object blocks, projectile pool). Same route, same recorded input, same golden for both sides. The mutation control (one byte of the attack routine changed) is reported DIFFERENT at vblank 1181 through the whole-block and globals checks (the mutated byte, `+80`, is not one of the 61 fields, which is why the block and region checks exist).

| Run (all vs `base`, the plain runner) | Golden check | Fork entries (attack, special, jump, 0a, gun, pre-tick, act14, held, tab) | Fields differing (of 122) | Whole-block frames | Outbound regions |
| --- | --- | --- | --- | --- | --- |
| all-9 clone, wrappers + 17 copies, all forks on | clean 272,171 of 272,171, missed IRQ 0 | 2346, 19652, 89, 2846, 53746, 244323, 252, 784, 7 | 0 | 0 | 0 |
| all-9 binary, mask 0 (wrappers pass through) | clean 272,171 | all 0 | 0 | 0 | 0 |
| shipping fork binary (attack + special only), forks on | clean 272,171 | 2346, 19652, then none | 0 | 0 | 0 |
| mutation control (shipping binary, one byte changed) | diverges, missed IRQs | - | 0 of the 61, whole block differs from vblank 1181 | 859 in the first 100,000 | globals 830 |

All nine routines are reached by this route, so identity is exercised, not only argued by construction, for every one (the plan expected slot 0a, action 14 and the jump to be unreached). Identity is **exact on HOST** for both the diagnostic clone and, separately, the shipping configuration. Not covered: the target (SH-2) objects and anything outside the Schaefer route; the shipping fork was compiled without the patch layer for this proof (the patch layer's own identity is its apply/undo test, section 4).

## 3. Pacing reference: the current skin chain (HOST, free-run, scripted pad)

`FREERUN=1` takes one interrupt per frame once every task has blocked instead of placing it from the golden, and `PADSCRIPT` replaces player 1's pad word after the player first stands free in stage 02 (vblank 1133). Used because the skin changes game timing, so the golden no longer matches. Each trial is a separate run from the stage start, before the first enemy reaches the player (about vblank 1380). `tools/wolverine/pacing.py` measures a guest trace (`wv_host_trace`): ticks are vblanks, one player update per vblank, a held tick counts; "active" is the ticks with a hit box live; the trial pad is `window_sweep.py gen`.

Presses are 4 frames long (a 1-frame tap is lost whenever the skin holds that tick's native update; found while building the harness, listed under findings).

| Stage | Reference (current skin) startup / active / recovery = total | Native Linn-speed pass startup / active / recovery = total | Change |
| --- | --- | --- | --- |
| LP1 | 3 / 8 / 5 = 16 | 2 / 4 / 6 = 12 | 25% faster |
| LP2 | 3 / 8 / 5 = 16 | 2 / 4 / 6 = 12 | 25% faster |
| HP | 0 / 31 / 20 = 51 (the capture's hit box is out from its first pose) | 3 / 5 / 8 = 16 | 69% faster, active 31 -> 5: **flagged** |
| HK (the kick) | 3 / 18 / 7 = 28 | unchanged, 3 / 18 / 7 = 28 | none, see section 5 |

Next-input window (stage 1 to 2, second press swept from 4 to 40 ticks after the first):

| | Reference | Native pass |
| --- | --- | --- |
| Earliest press that chains | 5 (a 4-frame press ends at 4) | 5 |
| LP2 starts | at tick 16 for any press from 5 to 20, at the press for a later one | at tick 12 for presses 5 to 12, at the press later |
| HP starts (second press already inside) | tick 32 | tick 24 |
| HK | 83 (HP at 32 + its 51 ticks) | 44 (HP at 28 + 16, with a press at 16) |

Both chains latch: one press inside the first move produces the second and third stage with no further press. The kick follows by itself after the third stage. The press-to-start gap, not the press, is what the native pass shortens. **Owner pacing note:** the owner approved the reference. Linn-speed LP is 25% faster, HP is three times faster with a 5-tick hit window instead of 31, and the HP/HK order is unchanged. This pass is default off; the owner compares it against the reference before it becomes anything else.

## 4. Stage 1: patch layer, walk weight, timings

Code: `saturn/guests/wolverine/wolverine.c` under `SAT_WV_NATIVE` (default off, an unchanged build otherwise), `tools/wolverine/nativepatch.py`, `tools/wolverine/native_patch.json`, `saturn/rt/build.py` (flags, fork file, patch table).

- **Patch layer, backup placed explicitly in the cart tail.** Four 2-byte duration words in Schaefer's attack frame records (script A: `163644` 2 to 1, `163654` 6 to 4; script B: `163698` 6 to 5, `1636b8` 2 to 4). The generated `wv_patch.inc` holds each entry's original and patched 16-bit word as `const` data (8 bytes an entry, 32 bytes, in the cart tail with the other guest tables), so there is **no RAM backup at all**. Apply and undo are stateless: write `now` over `orig`, or back; any other byte pattern is counted (`wv_patch_bad`, 1 byte) and left alone. It is applied in the `f_195ec` pre-hook, before the player update that reads the records, so a page a stage load restored is patched again on the next tick. `nativepatch.py` refuses a patch on a ROM page any stage file drops (a dropped page holds spilled tiles): the kick records (`164ef0`, `164f10`, `164f30`, `164f40`) are on a dropped page in stage 26, so the kick is not patched.
- **Walk weight.** Schaefer's: the skin's x1.375 `wv_speed` step is bypassed (`sp = 16`) under the flag. `wv_speed_tab` and `gen_c.py` are untouched.
- **Attack timings.** Native taps ended after 15 ticks; patched to 12 (stages 1 and 2) and 16 (stage 3). The capture's own poses and hit-box windows are played over the agreed startup/active/recovery with a piecewise-linear time warp; the step shown at each tick is a 28-byte table made by `gen_c.py` (appended at its end: `wv_warp_*`; the anchor, `wv_lift` and box code is untouched); no hit box is live during the agreed startup (`wv_in_startup`), because the capture's HP box is out from its first pose. Chain detection follows the stage's native length (`nat_atk`).
- **Hurt boxes** are untouched: the collision hook still pokes the per-pose MSHvSF hurt boxes (owner-approved).

Measured on HOST (free-run, same pad script, `base` = stock Schaefer, `skin` = this build with the flag off, `native` = flag on):

| Check | base | skin (reference) | native |
| --- | --- | --- | --- |
| Walk right, 60 ticks of walk state, px per tick | 1.88 | 2.58 | 1.88 (exactly Schaefer's) |
| Walk left, 60 ticks | 1.88 | 2.58 | 1.88 |
| Chain tap lengths (ticks), LP1 / LP2 / HP / HK | native tap 15 with no contact (a landed hit adds hitstop, +7 seen) | 16 / 16 / 51 / 28 | 12 / 12 / 16 / 28 |
| Pre-contact fields differing from base, 61 fields, matched start | - | 8 | 8, the same eight (`+06 +1e +24 +2c +6e +92 +e2 +f2`); inside `stage1_allowlist.json` |
| Damage per accepted hit on the stage 02 enemies (HP) | 24 light, 31 strong | 24, 31 | 24, 31 (records untouched) |
| Special health cost, 10 specials with enemies near | 6 every time | 6 on 7 of 10, 0 on 3 | identical to skin |

The MAME walk figure of 2.08 px per tick (100 px in 48 ticks, including the start) and the 1.88 above differ by definition (steady walk-state ticks here), not by build: base and native are bit-identical.

Valid transitions: in the isolated chain trial all three builds show only stand to attack and attack to stand (the stock set). The open-loop whole-route replay (the same recorded pad) diverges between the three builds within 200 vblanks, so its aggregate hit counts (303 / 206 / 191 events, 118 / 92 / 90 attack entries, base / skin / native) describe different games and are **not** a comparison. It is kept only as a smoke test: all three runs reach the end of the route with no stall and the native run adds no state outside the stock set (its extra edges are `02000a` and `0204xx` variants that the plain run reaches by other edges).

Unit tier (HOST, synthetic, no ROM): `tests/wolverine_native_test.c`, strict C90 `-Werror`: patch apply, idempotence, exact undo, page-restore re-apply, refusal of an unexpected layout, tick-hook patch and undo; warp steps over the agreed 2/4/6; startup hit-box gate; fork gate (Wolverine only, guest on only, never an enemy block); walk step adds nothing. Plus `test_forkgen_synthetic`.

## 5. Findings the owner or the next lane needs

1. **The special's 6-health cost is charged on connect, not on activation.** `f_1b492` (the drain) indexes a table `[0, 6, 6, ...]` by the byte at `+9f`, which the special increments when it hits; a whiff costs 0. Stock Schaefer therefore pays 6 only when the special lands. The plan says "6 per accepted activation". On HOST the current skin's special missed three times in ten (its boxes differ from Schaefer's) and was free on those. The owner decides: keep the stock rule (cost on connect), or charge on entry in the fork.
2. **A 1-frame tap is eaten when the skin holds that tick.** Held ticks skip the native update, which is where the pad is read. Every chain measurement here uses 4-frame presses. A real press lasts several frames, but a fast tap could be lost; the fork can read the pad on held ticks.
3. **HP's capture box is live for 31 ticks, from its first pose.** The reference HP is a long multi-pose hit window. The native pass compresses it to 5 ticks after a 3-tick startup; whether a long window matters for hit count is a balance question for the owner (the engine accepts one hit per target per contact either way, observed: 24 and 31 HP only).
4. **Kick (HK) is not retimed.** Its native records are on a ROM page stage 26 drops, so the patch layer refuses them; the presentation is therefore left at 28. Options: patch it everywhere but stage 26, handle stage 26 in the fork routine (Stage 2), or keep 28.
5. **Host guest code was byte-order wrong:** `wolverine.c` read the game's 16-bit words with a native `u16` load, right on the big-endian SH-2 and wrong on a little-endian PC. Fixed for the host only (`WV_HOST_ROM`); the target code is unchanged.

## 6. Linked build numbers (BUILD = SH-2 link, `saturn/rt/build.py`, flags `POSE_KEYS=0 KEEP_ROUND_FILES=1 KERNEL_CFLAGS="-DSAT_HOME -DSAT_DUEL_MENU -DSAT_GUESTS -DSAT_GUEST_DEFAULT=1 [extra]"`, assets D6; none of these was booted)

| | native OFF (this branch) | `-DSAT_WV_NATIVE` (patch layer, walk, timings, attack + special fork) | `-DSAT_WV_NATIVE -DSAT_WV_FORK_ALL` (nine routines, test only) |
| --- | --- | --- | --- |
| hw_free (high RAM) | 4,616 | 4,616 | 4,616 |
| lw_free (low RAM) | 76 | 92 (+16) | 92 |
| cart_free (tail slack) | 6,432 | 4,204 | 7,880 (cold1 moved down 20 KB) |
| `.cold1` size | 0x1c6e0 (116,448) | 0x1cf94 (118,676, +2,228) | 0x21138 (135,480, +19,032) |
| `cold1_at` | 0x27e2000 | 0x27e2000, **same 4 KB page: tile room unchanged** | 0x27dd000: 20 KB = 160 fewer tiles in main |
| `wolverine.o` text / rodata / bss | 5,740 / 19,518 / 250 | 5,852 / 19,590 / 234 | same |
| fork file text | - | 2,044 (attack 956 + special 982 + two 40-byte wrappers) | 18,848 |
| ISO | 384,839,680 | 384,839,680 | not packaged for fit |
| Round files | kept | rebuilt (cold1 end moved) | rebuilt |

- **Native OFF is byte-identical to the pre-native source.** `HW.BIN`, `LW.BIN`, `COLD1.BIN` of this branch with the flag off equal those of `aae2e10` built on the same work directory (cmp); same hw_free 4,616, lw_free 76, cart_free 6,432, iso size. (The anim lane's own `w1` was built from an older source and is not a valid comparison.)
- **Memory the patch layer adds.** Backup: **0 bytes of RAM**; the originals are 32 bytes of const data in the cart tail. New mutable state: 1 byte (`wv_patch_bad`) in low RAM. Net low RAM is +16 free because the walk-scale remainders (`sx_ sz_ xb_ zb_`, 16 bytes) compile away when the scale is off. High RAM is untouched. So "no additional main RAM" is proved by the linked map: hw 0, lw -17 bytes of use.
- **The first native build grew the tail by 2,556 bytes and crossed the 4 KB boundary.** The tail is sized by `(content + 0x1fff) & ~0xfff`; this build had 2,336 bytes of room before the boundary, so that version moved `cold1_at` down one page (32 sprite tiles; the round files rebuilt). Generating the warp table in `gen_c.py` (replacing about 350 bytes of code) and a 16-bit patch table brought growth to 2,228 bytes, 108 under the boundary. Any further tail growth in Stage 2 of more than 108 bytes costs 32 tiles at once.

fit.py (all 76 stage files, assets D6, `POSE_KEYS=0` as the build): **gate False, one file: `stage24_ma`**, Wolverine drops 2,873 tiles against Schaefer's 2,872; own tiles dropped 0, missing guest keys none, 1,511 Wolverine tiles, `cart_pack_room` 1,630,208 (equal to the recorded fit of the same assets: the D6 `fit.json` of the anim lane has the identical rows, so this is the 0-tile margin the brief expected, now at minus one, **not caused by native**; a native build leaves the room unchanged). The first native build, before the size fix, lowered the room to 1,626,112 and failed the same file by the same one tile and no other.

Tests (WSL, `python3 -m unittest discover tests`): 93 run, 63 pass, 30 errors, all 30 are the known private-dependency load errors (baseline 61 pass and 30 errors, plus the two tests added here). `test_wolverine_*`: 24 of 24 pass, including the strict C90 `-Werror` builds of the clock test in five configurations (flag off) and the new native test.

## 7. Inferred, not measured

- The SH-2 timing of any of this (the tick hook now runs the patch sync and the warp lookup every player update; cheap by inspection, not measured), the kick's native length, damage at any target but the stage 02 dummies, and anything on Yaba or hardware.
- That `-DSAT_WV_NO_FORK` builds on the target (the switch exists, it was not linked).
- Mid-fight behaviour of the patch layer across save/load and stage loads: the apply is stateless and re-applied each tick, tested only on synthetic memory and in host free-run through stage 02, not through a stage change.
- That the open-loop pad route shows nothing wrong beyond what the isolated trials show.
- The 61-field comparison covers the player blocks; enemies and objects are covered by region hashes (identity) and by HP only (Stage 1).
