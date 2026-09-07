# Project goal

Build a faithful native NTSC Sega Saturn port of `avspu`,
Alien vs. Predator (USA 940520), using the 32 Mbit expansion-RAM cartridge.

## Current delivery: R7C

One-player Predator Warrior, real controller input, direct Round1 entry,
complete stage, boss defeat, stage clear and stable Round2 handoff.
No captured-frame gameplay authority, missing scene population, authored clear
or plausible fallback. A faithful partial scene is not a completed level.

Source ROM data and bounded source routines are recovered offline into
executable SPEC and native C. MAME is the semantic reference, not the Saturn
runtime. Retain the accepted title-specific Port V2 platform and presentation
adapters; no new engine, general translator or CPS-2 runtime emulator.

The 2026-09-07 same-day request sets urgency, not acceptance. Report the actually
verified interactive extent. Complete source census and SPEC do not prove
playable native Round1. Do not show MAME footage as Saturn output.

## Later release scope, not today's work

The longer-term release covers cold boot, frontend, all stages/endings/credits,
Predator Warrior, Major Schaefer, Predator Hunter and Linn Kurosawa, and up to
three simultaneous local players. These remain separately gated future work.
The FIRST LIVE GAMEPLAY ENCOUNTER was technical substrate, not final gameplay
authority. Frontend now depends on explicit USER-10 full-Round1 review.

## Control and acceptance

PARITY_PLAN is the only roadmap. project_state and the active card own execution.
Continue native source-program/scene closure; do not restart the earlier
human-in-the-loop salvage-and-promotion process for accepted systems.
The title-specific deterministic Port V2 game uses current gameplay state and
current input. Rendering/audio consume state/events and never invent outcomes.

Preserve all approved locks and private evidence. Source, host, Target, emulator,
human and physical evidence remain distinct. Physical work follows HARDWARE_TEST;
no emulator or user review constitutes physical Saturn proof.
