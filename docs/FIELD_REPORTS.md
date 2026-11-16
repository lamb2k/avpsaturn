# Field reports (v0.1.0-beta)

Player reports passed on by the owner, with status. Each stays here until fixed in a release or dropped by the owner.

| Date | Setup | Report | Status / lead |
|---|---|---|---|
| 2026-11-15 | Emulator, cart set to None (GitHub #1) | Boot stops on coloured bands, no words | Fix on fix/boot-error-text: the stop screen now says what is wrong (cart missing / not working, disc read, crash), with codes and where to report. |
| 2026-11-16 | Saroo | Several players can't boot | Likely Saroo's RAM cart mode: forum reports say it is per-game patched and fails on homebrew that needs the cart. No AvP-specific report found online. Need from reporters: what the screen shows, firmware, launched from the Saroo menu or Fenrir, RAM cart mode on or off. Diagnostic disc option: `AVP_ABUS_BIOS` (cart left on BIOS bus timing). |
| 2026-11-16 | Fenrir, real Saturn | "Speckley garbled graphics on screen whenever there is loading or paused" | New, not in our notes. The beta disc has only run in emulators. Lead (unconfirmed): loads or the pause path writing graphics memory while the old picture is still shown. First: try to reproduce on the strict Ymir with the beta disc; if clean, it needs a console capture. |
| 2026-11-16 | Fenrir, real Saturn | "Predator grab and punch animation is garbled" | Probably known: INTEGRATION.md (disc 3e) lists "the automatic grab uses placeholder poses" as being fixed; it is not in the beta's known issues. Check the grab on the beta disc, and whether the fix reached release/v0.1.0-beta. |
