# Field reports (v0.1.0-beta and later)

Player reports passed on by the owner, with status. Each stays here until fixed in a release or dropped by the owner.

| Date | Setup | Report | Status / lead |
|---|---|---|---|
| 2026-11-15 | Emulator, cart set to None (GitHub #1) | Boot stops on coloured bands, no words | Fixed in v0.1.1: the stop screen says what is wrong (cart missing / not working, disc read, crash), with codes and where to report. |
| 2026-11-16 | Saroo | Several players cannot boot | v0.1.1: cause found in the SAROO firmware source (it runs its RAM cart on its own A-bus timing, ASR0 0x38803880; our loader overwrote it). The loader now keeps that timing. 2026-11-17: a player confirms it boots and plays on SAROO. |
| 2026-11-16 | Fenrir, real Saturn | "Speckley garbled graphics on screen whenever there is loading or paused" | Fixed in v0.1.2, confirmed clean on the owner's Saturn + Fenrir. Checked cart reads of the menu font and palettes, menu CRAM written only on change, NOW LOADING waits for shown pictures and holds only its own layer, and a per-boot cart soak test (256 KB, four patterns) that drops a failing cart to the BIOS A-bus timing (yellow band). Neither Ymir nor Mednafen reproduced it, so which change cured it is not known. |
| 2026-11-16 | Fenrir, real Saturn | "Predator grab and punch animation is garbled" | Fixed in v0.1.2, confirmed clean on the owner's Saturn + Fenrir (same changes as above; the sprite art is read from the cart). |
| 2026-11-17 | SAROO | Boots and plays; freezes late in the stage 2 boss fight (Razor Claws), about when the boss changes state near death. With v0.1.3-test1 it got further (boss at 1 pixel of health). First relayed as "stage 2 froze when loading" | Not reproduced: Ymir beats the boss into stage 3. Found that any stop after start-up (sat_fatal, CPU exception) showed no screen, so a stop looked like a freeze. v0.1.3-test2 build: the stop screen works in play, and a freeze watch stops with the master PC after 10 s without a finished frame or a new picture. Next: a photo of that screen. |
