**Test build for SAROO and Satiator players.** For general play, use [v0.1.2](https://github.com/lamb2k/avpsaturn/releases/tag/v0.1.2-beta).

## What's new since test2

- **Now loading.** The first black screen displays NOW LOADING while the game starts.
- **More specific error reports.** The startup error screen shows where a ROM.BIN load stopped. Runtime errors include the task and stage.
- **Razor Claws.** Fixed a crash triggered by Linn's head bounce. The low-health bounce played through in headless emulation.
- **Audio.** Restored the Warrior's damage sound after continuing in the opening stage. The separate SAROO report of silent Predator hits is still under investigation.

## How to report

Include your loader and firmware, RAM cartridge, and whether you used normal or safe timing. If you see an error screen, please post a photo. Both downloads show build `1122 FD6`.

- If you use a WASCA 4 MB cartridge with Satiator, try a cold boot with each download and report where each stops or whether it reaches the title. [WASCA boot report](https://github.com/lamb2k/avpsaturn/issues/3)
- If Predator sprites corrupt during a grab, try the same grab in each download and share a clip. [Predator sprite report](https://github.com/lamb2k/avpsaturn/issues/4)
- If Razor Claws still freezes, share the character, move, and boss health. [Razor Claws freeze report](https://github.com/lamb2k/avpsaturn/issues/6)
- If a Predator hit is silent on SAROO, share the character, stage, and attack. [SAROO audio report](https://github.com/lamb2k/avpsaturn/issues/2)

## Download

- `avp_saturn_test3_normal.zip` uses the standard cartridge timing.
- `avp_saturn_test3_safe.zip` keeps the existing bus timing after the cartridge check for the Satiator comparison.

Unzip either download into its own folder and start the `.cue` file from your loader menu. The two images share the same game data and audio. Both reached gameplay in headless emulation. Hardware checks are pending.
