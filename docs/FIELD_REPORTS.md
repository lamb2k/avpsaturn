# Field reports (v0.1.0-beta and later)

Player reports passed on by the owner, with status. Each stays here until fixed in a release or dropped by the owner.

| Date | Setup | Report | Status / lead |
|---|---|---|---|
| 2026-11-15 | Emulator, cart set to None (GitHub #1) | Boot stops on coloured bands, no words | Fixed in v0.1.1: the stop screen says what is wrong (cart missing / not working, disc read, crash), with codes and where to report. |
| 2026-11-16 | Saroo | Several players cannot boot | v0.1.1: cause found in the SAROO firmware source (it runs its RAM cart on its own A-bus timing, ASR0 0x38803880; our loader overwrote it). The loader now keeps that timing. 2026-11-17: a player confirms it boots and plays on SAROO. |
| 2026-11-16 | Fenrir, real Saturn | "Speckley garbled graphics on screen whenever there is loading or paused" | Fixed in v0.1.2, confirmed clean on the owner's Saturn + Fenrir. Checked cart reads of the menu font and palettes, menu CRAM written only on change, NOW LOADING waits for shown pictures and holds only its own layer, and a per-boot cart soak test (256 KB, four patterns) that drops a failing cart to the BIOS A-bus timing (yellow band). Neither Ymir nor Mednafen reproduced it, so which change cured it is not known. |
| 2026-11-16 | Fenrir, real Saturn | "Predator grab and punch animation is garbled" | Fixed in v0.1.2, confirmed clean on the owner's Saturn + Fenrir (same changes as above; the sprite art is read from the cart). |
| 2026-11-17 | SAROO | Boots and plays stage 1; freezes on the load into stage 2 | New. Version, screen state at the freeze and repeatability not yet known. The stage 1 load (title to stage) uses the same loader path and works, so the difference is in what stage 2's load does: leads are where its data sits in STORE.BIN (320 MB, far seeks), the compressed-tile streaming read (GFS non-blocking), or CD audio playing when the read starts. Neither emulator models SAROO. |
