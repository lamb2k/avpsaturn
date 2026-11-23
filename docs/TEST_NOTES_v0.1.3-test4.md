**Test build for SAROO and Satiator players.** For general play, use [v0.1.2](https://github.com/lamb2k/avpsaturn/releases/tag/v0.1.2-beta).

## Changes since test3

- **WASCA boot.** Both images load ROM.BIN directly and check cartridge RAM after loading. This bypasses the compressed load where both test3 variants stopped on the reported setup.
- **Predator.** Restored Warrior and Hunter attack sounds in the affected stage packs, including Warrior’s re-entry attack. Fixed two Warrior grab poses where Wolverine’s tiles could overwrite Warrior’s upper body.
- **Razor Claws.** Restored foreground railing priority. Headless checks also verified Linn’s head bounce, the boss clear, and the transition to Stage 3.

## How to report

- On Satiator with WASCA in 4 MB mode, cold-boot both variants and see whether they reach the opening stage. Include the Satiator firmware and menu, the WASCA version, the timing variant, and a photo of any stop screen. An official 4 MB cart is a useful comparison if you have one. [WASCA boot report](https://github.com/lamb2k/avpsaturn/issues/3)
- For Predator issues, include the character, stage, and move. Try Warrior’s first-scene grab solo and with Wolverine. [SAROO audio report](https://github.com/lamb2k/avpsaturn/issues/2) · [Satiator grab report](https://github.com/lamb2k/avpsaturn/issues/4)
- In Stage Select 2-2, check the railing before and after pause. With Linn, bounce off Razor Claws and continue into Stage 3. [Layering report](https://github.com/lamb2k/avpsaturn/issues/5) · [Freeze report](https://github.com/lamb2k/avpsaturn/issues/6)

## Download

- `avp_saturn_test4_normal.zip` uses standard cartridge timing.
- `avp_saturn_test4_safe.zip` keeps the existing bus timing after the cartridge check.

Unzip each download into its own folder and open its `.cue` file. Both builds show `1122 TEST4 RAW`, with `SAFE` added on the safe variant. Each ZIP contains checksums for all 27 tracks. The headless tests passed on the packaged images. Physical Saturn confirmation is pending.
