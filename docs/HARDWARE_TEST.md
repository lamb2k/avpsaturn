# Physical Saturn test plan

Physical evidence is mandatory for performance, final scanout, audio coexistence, input latency, and capability acceptance. Emulator or host results cannot be relabeled as hardware.

## Required setup record

- Console model/region and video standard
- 32 Mbit expansion cartridge identity
- Loader/optical method and firmware
- Digital controller identity
- Display/capture chain and latency measurement method
- Build branch, commit, compile profile, ISO/cue SHA-256, manifest SHA-256
- Test mode, input record, expected MAME oracle hash
- Ambient notes relevant to thermal/soak repeatability

## First physical proof: VDP1 render and transfer budget

Before the integrated slice, run the isolated Probe 3 executable on representative and measured 909-tile schedules.

Record per frame:

- reachable/drawn VDP1 command count;
- VDP1 draw-end state and deadline margin;
- CPU preparation cycles/time;
- texture bytes copied/uploaded;
- CRAM writes;
- DMA/copy time and legal direction;
- cartridge reads;
- missed fields or late lists;
- final scanout hash/capture.

Run per-tile variant T first. Run the bounded composite comparison variant only if T fails or is below the required margin. Include an overload negative control that demonstrably trips the detector.

Pass: zero missed fields/corruption over a ten-minute alternating representative/peak soak and at least 15% measured deadline headroom at the peak. Failure: any draw crosses frame change, persistent missed field, corruption, illegal transfer path, or less than 15% headroom.

## Integrated capability slice

Prerequisites:

- exact T0 identity/provenance pass;
- two-run MAME oracle pass;
- host lifted-logic zero-diff pass;
- normal `release-normal-release` ISO;
- bounded emulator state/render/final-scanout pass;
- no adapted fallback on the accepted path.

From cold boot:

1. Verify cartridge detection and target/build identifier.
2. Reach the deterministic gameplay checkpoint through the declared startup route.
3. Execute the fixed controller record with one player and class `0x1F` enemy.
4. Observe movement, attack/contact, hit, reaction, KO, camera/stage movement, layers, priority, palette, and 352 crop.
5. Confirm timed PCM and audible CDDA.
6. Confirm no data read occurs during the declared CDDA interval.
7. Dump/record semantic mismatch, VDP1 draw-end, CPU/transfer, arena high-water/canaries, input latency, and final-scanout counters.
8. Repeat cold boot, then run a ten-minute loop/soak.

Pass only when all 12 conditions in `docs/PARITY_PLAN.md` close against the exact normal image. Any reset, hang, audio loss, mismatch, canary damage, missed field, undeclared fallback, or unmeasured required counter is a failure or `UNRUN`, never a pass.

## Result template

```text
date/time:
operator:
console/region/video:
cart:
loader/firmware:
controller:
capture chain:
branch:
commit:
profile:
iso sha256:
manifest sha256:
oracle sha256:
test: render-budget | capability-slice
representative command/draw margin:
peak command/draw margin:
cpu/transfer high-water:
cart/work/VDP/SCSP high-water and canaries:
input-to-state/input-to-photon:
PCM result:
CDDA result:
final scanout result:
soak duration/result:
evidence artifacts:
status: PASS | FAIL | UNRUN
notes:
```
