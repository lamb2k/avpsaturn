**Test build for SAROO players.** If you're not on a SAROO, stick with [v0.1.2](https://github.com/lamb2k/avpsaturn/releases/tag/v0.1.2-beta).

A SAROO player told us the game now boots and plays, but freezes while loading stage 2. We can't test on a SAROO ourselves, so this build is our best guess at a fix. Please try it and let us know.

## What's changed from v0.1.2

- **Loads can't freeze any more.** If the disc stops sending data during a stage load, the game now gives up after a few seconds and tries again, up to three times. If all three fail, it shows the error screen with a code instead of freezing.
- **SAROO reads stage graphics differently.** On SAROO, the stage graphics are now read in one go and then unpacked, rather than unpacked while they stream in.
- **Black start-up screen.** The coloured bars at start-up are gone. If you see a single yellow line, your RAM cart failed the speed check and the game switched to a slower, safer setting. A photo would help.

We've only tested this in an emulator, with the SAROO read path switched on: stage 1 and stage 2 load and play normally there.

## How to report

[Open an issue](https://github.com/lamb2k/avpsaturn/issues) or reply wherever you found this, and tell us:

1. Did stage 2 load?
2. If you got an error screen, a photo of it.
3. Your SAROO firmware version.

## Download

Grab `avp_saturn_test_saroo_load.zip` below, unzip it, and start the `.cue` file from the SAROO menu.
