# HW-01 Probe 3 physical operator procedure

Do not write, flash, burn, or copy an image until the exact target and boot
method are recorded and the user explicitly authorizes that write. Running
`physical_preflight.ps1` is read-only and does not authorize a later write.

## Automatic diagnostic sequence

Boot the exact `probe3.iso`/`probe3.cue` pair named in `HASHES.sha256`. No
controller input is required. The image runs:

1. `PROBE3_REPRESENTATIVE`: source frame 5637, 567 requested/submitted AvP
   workload tile draws, followed by one untimed actual-command-table census
   frame.
2. `PROBE3_PEAK_909`: source frame 5776, exactly 909 requested/submitted AvP
   workload tile draws, followed by one untimed actual-command-table census
   frame.
3. `PROBE3_OVERLOAD`: the exact 909-workload-draw body with a declared zero-field
   diagnostic deadline, followed by its untimed census frame. The shared
   deadline predicate must trip; this is a detector control, not a production
   budget.
4. `PROBE3_TEN_MINUTE_ALTERNATING_SOAK`: the image resets soak-only counters,
   anchors elapsed duration to the independent VBlank clock, alternates
   representative and peak in fixed 60-elapsed-field blocks, excludes the
   overload body, and runs at least 36,000 measured NTSC fields with no overlay.
   Completed workload submissions are reported separately from elapsed fields.

Do not reset between modes. Capture the final summary screen and read the
624-byte schema-3 `avsp_probe3_telemetry` block at the manifest address when the boot
method provides a debug/readback channel. The on-screen checksum and telemetry
`summary_checksum` must agree.

## Immediate pass/fail rules

The image enters its embedded soak only when the actual reachable VDP1 census
separately reports 567/909/909 AvP workload tile draws, the same submitted
workload draw-call counts, one auxiliary SGL scaled-sprite sentinel, total
reachable hardware draws of 568/910/910, three state commands, one terminator,
and total reachable table entries of 572/914/914. Stored nonzero slots are
reported as stored extent and are never substituted for reachable entries.
Each census must have no invalid link, loop, traversal failure, early end, or
truncation; overload has tripped the shared predicate; both canaries are
intact; cart source, VDP1 destination, and cart-to-VDP1 path validity are 1; and
asset failures/failure reason/missed fields/late lists are zero for the two
measured modes. Any hang, corruption, mismatch, missing summary, canary or asset
failure, illegal copy direction, missed field, or late list is a failure.

The overload control passes only by tripping its declared detector safely. It
must not be counted as a production deadline failure. Physical timing must
show the required 15 percent margin from the Probe-only SCU sprite-draw-end
interrupt timestamp and measured FRC field period; next-field EDSR alone is
not evidence. Emulator timing is never accepted for that condition.

Do not start a separate manual Probe soak. Retain uninterrupted video/readback
while this exact image runs its built-in 36,000-field alternating soak. The
summary appears only after it completes or immediately after a hard failure.

## Evidence naming

Use `YYYYMMDD-HHMMSS-hw01-<console>-<mode>-<run>-<kind>.<ext>`, where mode is
`representative`, `peak909`, `overload`, or `soak`; run is `r1` or `r2`; and
kind is `screen`, `video`, `telemetry`, `setup`, or `notes`. Never overwrite a
prior capture. Record each file SHA-256 in the result record.

## Return to the approved slice

After Probe 3, stop and obtain explicit authorization for any required target
write. Boot only the packaged `integrate-03-approved.iso`/`.cue` pair whose ISO
hash is `4a1427749833ee3860c1a802c02105e921171c266693f9c612fd6e64a3cd98ef`.
Cold boot, execute the fixed controller record, cold boot and repeat, then run
the ten-minute integrated soak. Probe evidence does not change INTEGRATE-03's
current `APPROVED`/physical-`UNRUN` status by itself.
