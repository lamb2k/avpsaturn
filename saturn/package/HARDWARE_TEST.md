# AvP Saturn: first console test

Status: UNRUN on hardware. Everything so far ran on Yaba Sanshiro only. Emulator timings do not predict the console.

## You need

- NTSC Saturn with the 4 MB RAM cart (32 Mbit, the kind sold with King of Fighters 97 or X-Men vs Street Fighter).
- Either disc from this folder (avp_saturn.cue normally) written to a CD-R (cue and raw tracks) or loaded on an optical drive emulator.
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

Thin bars sit near the top left of the screen, over the score bar. Each 8 pixels is 1 ms, so the screen's 352 pixels hold 44 ms.

- Green, top: game logic on the main CPU, last finished frame.
- Blue, second: drawing on the second CPU, last picture.
- White, third: fixed length, 16.7 ms, one 60 Hz field.
- Magenta, fourth: VDP1's time for the sprite list. It only updates while you hold Y.

A bar past the white one means that part missed 60 Hz. A frame that runs long restarts the timer, so read over several seconds. Record video and step through it if you can.

## Numbers we need

Do these in the same busy place, the Coffee Shop fight, for about 20 seconds each. Write down typical and worst bar lengths in pixels.

| Test | Disc | Hold | Decides |
| --- | --- | --- | --- |
| A. Game and drawing | avp_saturn.cue | nothing | Green and blue: console frame cost |
| B. VDP1 full | avp_saturn.cue | Y | Magenta: fetch plus fill |
| C. VDP1 fetch only | avp_saturn.cue | Y and Z | Magenta: nearly fetch alone. Sprites look like garbage in this test, that is expected |
| D. DMA on | avp_saturn_dma.cue | nothing, then Y | Compare blue and magenta with A and B |

- Fill is B minus C. If fetch dominates, merging tile rows is worth doing; if fill dominates, it is not.
- Blue in D lower than in A with no corruption means tile DMA stays on.
- Note any corruption on the DMA disc. SCU DMA from the cart is not legal in every direction, so this may misbehave: that is a result, not a failure of the test.

## Known limits

- Round 1 only. Round 2 shows its title card, then is not built: stop there.
- Tiles the pack lacks draw blank. Letters and digits are missing in places on the title and round cards, and some attract and select graphics.
- Under 60 fps in busy fights is expected. Only Yaba has run this, split into legs with save states.
- Music is CD audio and effects are 8 bit 11 kHz. Effects run about 3 dB quiet against MAME on Yaba.
- Settings live in RAM. Nothing saves.
