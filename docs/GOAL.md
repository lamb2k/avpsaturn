# Project goal

Produce a faithful, native NTSC Sega Saturn port of MAME set `avspu`,
`Alien vs. Predator (USA 940520)`, using the 32 Mbit expansion-RAM cartridge.
The first acceptance target remains a deterministic, gameplay-valid physical
Saturn capability slice; the eventual target remains the complete port.

Development now uses a human-in-the-loop salvage-and-promotion process. Treat
the old mixed runtime as a source of reusable loading, graphics, animation,
input, VDP1, VDP2, palette, HUD, audio, diagnostic, build, and emulator systems,
not as final gameplay authority. Isolate each subsystem, test it on a dedicated
bench, self-review its Saturn diagnostic in the pinned emulator, obtain human
review for subjective appearance or feel, choose a salvage decision, promote
it behind a clean `port_v2` interface, and integrate one dependency at a time.

`docs/PARITY_PLAN.md` is the only roadmap. `project_state.yaml` and its active
task card drive the interactive loop. Prototype and lab work may prove reuse,
adapters, repairs, or replacement needs, but does not itself advance parity,
normal-release, emulator-acceptance, or physical-capability gates.

The selected architecture in `docs/research/CPS2_TO_SATURN_RESET.md` remains
authoritative: offline ROM extraction, traceable original data, bounded
selective lifting, native Saturn subsystems, and differential validation
against MAME 0.289. A general CPS-2 emulator, whole-program recompiler,
generalized Capcom engine, or captured-gameplay substitute is out of scope.
