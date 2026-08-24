# HW-01 Probe 3 physical operator procedure

Do not write, flash, burn, or copy an image until the exact target and boot
method are recorded and the user explicitly authorizes that write. Running
`physical_preflight.ps1` is read-only and does not authorize a later write.

## Automatic diagnostic sequence

Boot the exact `probe3.iso`/`probe3.cue` pair named in `HASHES.sha256`. No
controller input is required. The image runs:

1. `PROBE3_REPRESENTATIVE`: source frame 5637, 567 reachable/drawn commands,
   for 120 fields.
2. `PROBE3_PEAK_909`: source frame 5776, exactly 909 reachable/drawn commands,
   for 120 fields.
3. `PROBE3_OVERLOAD`: the exact 909-command body with a declared zero-field
   diagnostic deadline, for one bounded field. This is a detector control, not
   a production budget.

Do not reset between modes. Capture the final summary screen and read the
252-byte `avsp_probe3_telemetry` block at the manifest address when the boot
method provides a debug/readback channel. The on-screen checksum and telemetry
`summary_checksum` must agree.

## Immediate pass/fail rules

The diagnostic is eligible to proceed to the ten-minute alternating soak only
when representative is 567/567, peak is 909/909, overload is 909/909 with its
detector tripped, both canaries are intact, legal copy direction is 1, and
asset failures/failure reason/missed fields/late lists are zero for the two
measured modes. Any hang, corruption, mismatch, missing summary, canary or asset
failure, illegal copy direction, missed field, or late list is a failure.

The overload control passes only by tripping its declared detector safely. It
must not be counted as a production deadline failure. Physical timing must
show the required 15 percent margin; emulator timing is never accepted for
that condition.

After the three modes pass, run a ten-minute physical soak alternating the
representative and peak schedules and retain uninterrupted video/readback.

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
