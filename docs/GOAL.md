# Project goal

Produce a faithful, native NTSC Sega Saturn port of MAME set `avspu`,
*Alien vs. Predator (USA 940520)*, using the 32 Mbit expansion-RAM cartridge.
The release target is the complete title: cold boot, legal/logos, attract, title,
credits/start, character select, every stage and boss, continue and game-over
paths, each applicable ending, and credits.

The roster target is all four measured selectable characters:

1. Predator Warrior
2. Major Schaefer
3. Predator Hunter
4. Linn Kurosawa

The multiplayer target is up to three simultaneous local players through the
required Saturn controller and multitap topology. Neither four-character
gameplay parity nor three-player hardware behavior is assumed proven; both
remain evidence-gated future work.

The first acceptance target remains a deterministic physical Saturn capability
slice. It retires hardware risk but is not proof of production control, enemy
AI, encounter progression, or a complete gameplay loop. The next
category-changing milestone is `FIRST LIVE GAMEPLAY ENCOUNTER`: one player,
Predator Warrior, and one autonomous class `0x1F` street alien in one measured
Round 1 encounter, driven by real controller input and current gameplay state
rather than fixed-frame choreography. Frontend expansion follows that live
encounter and its explicit human playability review.

Development uses a human-in-the-loop salvage-and-promotion process. Treat the
old mixed runtime as a source of reusable loading, graphics, animation, input,
VDP1, VDP2, palette, HUD, audio, diagnostic, build, and emulator systems, not
as final gameplay authority. Isolate each subsystem, test it on a dedicated
bench, self-review its Saturn diagnostic in the pinned emulator, obtain human
review for subjective appearance or feel, choose a salvage decision, promote
it behind a clean `port_v2` interface, and integrate one dependency at a time.

The production destination is a title-specific deterministic Port V2 game
kernel surrounded by MAME-oracle, host-test, Saturn, content, and temporary
legacy adapters. Presentation consumes semantic game state and events; it does
not own gameplay outcomes. Migration proceeds incrementally by abstraction so
accepted behavior remains runnable while legacy coupling is displaced.

`docs/PARITY_PLAN.md` is the only roadmap. `project_state.yaml` and its active
task card drive the interactive loop. Prototype, lab, host, MAME, emulator, and
human-review results may prove bounded claims, but do not themselves advance
physical Saturn gates.

The selected architecture in `docs/research/CPS2_TO_SATURN_RESET.md` remains
authoritative for source identity and Saturn constraints: offline ROM
extraction, traceable original data, bounded selective lifting, native Saturn
subsystems, and differential validation against MAME 0.289. A general CPS-2
emulator, whole-program recompiler, generalized Capcom engine, general ECS, or
captured-gameplay substitute is out of scope.
