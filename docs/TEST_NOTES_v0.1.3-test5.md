**Satiator/WASCA compatibility test.** The [v0.1.3 beta](https://github.com/lamb2k/avpsaturn/releases/tag/v0.1.3-test4) is the general download.

This build uses safe cartridge timing and loads all startup files and stage graphics directly. It keeps the beta's gameplay data and disc audio. The stop screen identifies it as `1123 TEST5 RAW SAFE`.

## Download

Extract `avp_saturn_test5_safe.zip` into its own folder. Open `avp-field-diagnostics.cue` with all 27 tracks beside it. The outer `SHA256SUMS.txt` verifies the ZIP, and the manifest inside verifies the tracks.

## Verification

The direct-load image passed cold boot and the solo Warrior 1-1 to 1-2 transition headlessly. A separate headless run started from Stage Select 2-2, cleared Razor Claws, and reached 3-1. The packaged image differs from the tested image only in the on-screen build label. Physical Saturn verification is pending.

When testing resumes on Satiator/WASCA in 4 MB mode, use a cold boot and play through the sub-level transitions. A photo of any stop screen is enough to identify the build and failure. [WASCA report](https://github.com/lamb2k/avpsaturn/issues/3)

## Source and disc layout

This uses the v0.1.3 beta runtime and safe loader settings. The build label is `AVP_DIAG_BUILD=1123_TEST5_RAW`. The package uses the plain shared sector store for all 287 round files and uncompressed versions of the beta's boot files. The disc occupies 290,379 sectors including audio and gaps.
