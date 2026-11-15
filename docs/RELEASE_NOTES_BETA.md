# AvP Saturn v0.1.0 beta

![Alien vs. Predator, Sega Saturn cover](images/cover/avp-saturn-cover.jpg)

Alien vs. Predator, Capcom's 1994 arcade brawler, running natively on the Sega Saturn. The arcade's 68000 game code
has been translated to C and rebuilt around the Saturn's own hardware, with no emulation layer in between.

This is the first public beta. You can play the whole game from start to finish, but on a real Saturn it still slows
down when the screen gets busy. Bug reports are very welcome.

## Download

Grab `avp_saturn_beta_v0.1.0.zip` below, unzip it, and load the `.cue` file.

You'll need one of these:

- An NTSC Saturn with the 4 MB RAM cartridge, running the disc from an optical drive emulator (we test on a Fenrir)
  or a burned CD-R. The disc is 63.5 minutes, so a 74 or 80 minute blank works.
- An emulator that supports the 4 MB cartridge, such as Yaba Sanshiro or Ymir.

No Saturn handy? Play it in your browser at https://avp.retronetplay.com.

## Screenshots

![Round 1 gameplay](images/release/round1-gameplay.gif)

**[Watch a 47-second clip, with sound (MP4)](media/avp-saturn-beta.mp4)**

| Title menu | Attract intro | Character select |
|---|---|---|
| ![Title menu](images/release/title-menu.jpg) | ![Attract intro](images/release/intro.jpg) | ![Character select](images/release/character-select.jpg) |
| **Round 1: City of Despair** | **Coffee Shop** | **Round 1 fight** |
| ![Round 1 card](images/release/round1-card.jpg) | ![Coffee Shop](images/release/round1-coffee-shop.jpg) | ![Round 1 fight](images/release/round1-fight.jpg) |

*Captured in Yaba Sanshiro from this disc.*

## What's in this build

- The full arcade game for one or two players, all the way to the ending.
- Dutch Schaefer, Linn Kurosawa, Predator Warrior and Predator Hunter.
- The arcade music as CD audio, plus the original sound effects.
- A home menu with Arcade, Versus, Boss Rush, Stage Select and Options.
- Versus is a two-player duel, with aliens dropping in to keep things messy.
- Options for lives, button layout, sound test and screen adjust. Your settings are saved to backup memory.
- Pause at any time, and quit back to the title.
- Wolverine as a bonus character. Beat the game to unlock him, or turn him on in Options.

## Known issues

- Slowdown in crowded fights on real hardware. This is the main thing we're working on.
- A handful of rarely heard sound effects are missing in some stages.
- We've played earlier builds on a real Saturn, but this exact disc has only been tested in emulators so far.

If something looks, sounds or plays wrong, [open an issue](https://github.com/lamb2k/avpsaturn/issues) and tell us
the stage and what was happening on screen.

## Next up

- Full speed on real hardware.
- Menus styled after Capcom's own Saturn releases.

## Legal

AvP Saturn is a fan preservation project. Alien vs. Predator and its characters belong to their owners; see
[NOTICE.md](../NOTICE.md). Only build from a ROM set you're entitled to use. Our general CPS2-to-Saturn tools are in
[lamb2k/cps2saturn](https://github.com/lamb2k/cps2saturn).
