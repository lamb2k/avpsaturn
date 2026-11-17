**Test build for SAROO players.** If you're not on a SAROO, stick with [v0.1.2](https://github.com/lamb2k/avpsaturn/releases/tag/v0.1.2-beta).

A SAROO player found the game freezes late in the stage 2 boss fight, around when the boss changes state near death. We can't make it happen in an emulator (there the boss fight plays through to stage 3), so this build is set up to catch it.

## What's new since test1

- **No more silent freezes.** If the game hits an error or crashes during play, it now shows the error screen instead of freezing on the last picture.
- **Freeze detector.** If the game stops responding for 10 seconds, it shows the error screen. The ERROR and DETAIL numbers on it point to the exact spot in the code where it stopped.

Still included from test1: loads retry instead of freezing, and the black start-up screen.

## How to report

If you see the error screen, **a photo of it is all we need.** [Open an issue](https://github.com/lamb2k/avpsaturn/issues) or reply wherever you found this, and include your SAROO firmware version. If it freezes with no error screen, please tell us that too.

## Download

Grab `avp_saturn_test_saroo_watch.zip` below, unzip it, and start the `.cue` file from the SAROO menu.
