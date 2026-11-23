**Test6 Safe is for Satiator with WASCA in 4 MB RAM mode.** The [v0.1.3 beta](https://github.com/lamb2k/avpsaturn/releases/tag/v0.1.3-test4) is the general download.

Test6 checks the exact byte count of raw boot reads and verifies all five boot files in RAM. The stop screen identifies this image as `1123 READBACK SAFE`.

## Download and test

Extract `avp_saturn_test6_safe.zip` into its own folder. Open `avp-field-diagnostics.cue` with all 27 tracks beside it. The outer `SHA256SUMS.txt` verifies the ZIP. The manifest inside verifies the tracks.

On the affected setup, cold-boot and play solo Predator Warrior from 1-1 into 1-2. If the game stops or graphics disappear, a photo helps. Stage Select 1-2 is a separate check if the transition fails. [WASCA report](https://github.com/lamb2k/avpsaturn/issues/3)

## Verification

The packaged image passed cold boot and direct Stage Select 1-2 in headless Ymir. Two separate controls verified the stop screens for a short read and a one-byte startup file change. The 1-1 to 1-2 transition and physical Satiator/WASCA behavior need verification.

Test6 uses the Test5 Safe disc layout and replaces only its loader. The disc occupies 290,379 sectors including audio and gaps.
