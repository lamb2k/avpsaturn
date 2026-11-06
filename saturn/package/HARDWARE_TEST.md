# AvP Saturn: first console test

Status: UNRUN on hardware. Everything so far ran on Yaba Sanshiro only. Emulator timings do not predict the console.

## You need

- NTSC Saturn with the 4 MB RAM cart (32 Mbit, the kind sold with King of Fighters 97 or X-Men vs Street Fighter).
- This folder written to a CD-R (cue and raw tracks) or loaded on an optical drive emulator.
- A standard pad in port 1.
- A way to record the screen, if you can, for reading the bars.

Check `SHA256SUMS.txt` first. It names the commit the image came from.

## Controls

| Pad | Game |
| --- | --- |
| X | Coin |
| Start | 1P start, continue |
| C | Gun, confirm |
| A | Attack |
| B | Jump |
| D-pad | Move |

## Steps

1. Boot with the cart in. If it stops on a black screen at once, the cart check failed: reseat the cart and retry.
2. Wait for the warning, then the title.
3. Press X once, then Start. Credits should drop and the character select should appear.
4. Pick Predator Warrior with C.
5. Play Round 1: Coffee Shop, the street, then the boss.
6. Stand still until you are knocked out. Press X, Start, then C to continue. You should come back with full health.
7. Beat the boss, or get as far as you can.

## What to report

For each step: pass or fail, and what happened.

- Crash or hang: when, and what was on screen.
- Garbled sprites or backgrounds, flicker, black boxes.
- Sound: are effects there, is music there, does it stutter or stop after a door or a new section.
- Whether the game loads between sections: it should not touch the disc after boot, apart from CD audio.
- Console model and region, cart name, CD-R or which drive emulator, and the commit line from `SHA256SUMS.txt`.

## Frame-cost bars

Three thin bars sit at the top left of the screen. Each 8 pixels is 1 ms.

- Green, top: game logic on the main CPU, last finished frame.
- Blue, middle: drawing on the second CPU, last picture.
- White, bottom: fixed length, 16.7 ms, one 60 Hz field.

A bar past the white one means that part missed 60 Hz. The timer is restarted at each vblank, so a frame that runs long resets the reading and the bar can look short: read the bars over several seconds, and record video if possible.

## Known limits

See `KNOWN_LIMITS` in docs/STATUS.md for the state of this build. Round 1 only: the image holds Round 1 data, and other rounds are not built. The cart hold only this round's tiles, so a tile the pack lacks draws blank.
