# AvP Saturn

Alien vs. Predator (Capcom CPS2 arcade, 1994) as a native Sega Saturn game.

![Alien vs. Predator, Sega Saturn cover](docs/images/cover/avp-saturn-cover.jpg)

*Cover art by the production team, for this repository and its release notes.*

**Play it in a browser:** https://avp.retronetplay.com (emulator build; it needs no download).

- **Now:** the arcade game, with all four characters to pick from, plus a home menu with a Smash-style Duel, Boss Rush, Stage Select and Options.
- **Coming next:** menus laid out like Capcom's own Saturn ports, a NOW LOADING indicator, a music player, and a disc that fits on an 80-minute CD-R.
- **Needs:** a Saturn with the 4 MB RAM cartridge.
- **Tested:** on emulators only. It hasn't run on a real Saturn yet.

**Beta:** read the [v0.1.0-beta release notes](docs/RELEASE_NOTES_BETA.md): what's in it, what you need and what's next.

![Round 1 gameplay, Saturn beta](docs/images/release/round1-gameplay.gif)

**[Watch the 52-second beta capture (MP4)](docs/media/avp-saturn-beta.mp4)**

| Title menu | Character select | Round 1 |
|---|---|---|
| ![Title menu](docs/images/release/title-menu.jpg) | ![Character select](docs/images/release/character-select.jpg) | ![Round 1 fight](docs/images/release/round1-fight.jpg) |

**Intended for software preservation.** This project exists to preserve Alien vs. Predator as playable software on the Sega Saturn. Build it only from a ROM set you are authorized to use; the game itself belongs to its rights holders (see [NOTICE.md](NOTICE.md)). The general CPS2-to-Saturn tooling and playbook live in [lamb2k/cps2saturn](https://github.com/lamb2k/cps2saturn).

This private, authorized preservation project targets MAME set `avspu`, `Alien vs. Predator (USA 940520)`, as a native NTSC Sega Saturn port requiring the 32 Mbit expansion-RAM cartridge.

## Architecture

The project now follows a title-specific hybrid architecture:

- exact ROM identity and reproducible offline extraction;
- sparse original-address data where useful;
- selective lifting of bounded 68000 game logic;
- native SH-2 input, simulation, collision, stage, render, audio, load, and telemetry systems;
- MAME 0.289 as a deterministic differential oracle;
- VDP1 per-16x16-tile 4bpp baseline, VDP2 stage/final composition, fixed cart phases, and SCSP PCM plus CDDA.

The complete decision is [docs/research/CPS2_TO_SATURN_RESET.md](docs/research/CPS2_TO_SATURN_RESET.md). Its [source ledger](docs/research/CPS2_TO_SATURN_SOURCE_LEDGER.md) and [evidence ledger](docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md) define what is known and what remains unverified.

## Current state

The repository has strong MAME extraction, actor/collision/animation/object analyzers, deterministic manifests, palette/bounds checks, and bounded Saturn render fixtures. The old mixed runtime and playable-skeleton prototype now enter subsystem salvage benches; neither is production gameplay authority or a parity gate.

The former RP presentation roadmap is archived under `docs/archive/pre-reset-2026-08-20/`. It is not active guidance. [docs/PARITY_PLAN.md](docs/PARITY_PLAN.md) is the only roadmap, [project_state.yaml](project_state.yaml) is machine-readable state, [data/port_v2_migration_map.yaml](data/port_v2_migration_map.yaml) is the subsystem ledger, and the active bounded body is the task card named by project state.

## Active documents

- [AGENTS.md](AGENTS.md)
- [docs/GOAL.md](docs/GOAL.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/PARITY_PLAN.md](docs/PARITY_PLAN.md)
- [docs/TEST_PLAN.md](docs/TEST_PLAN.md)
- [docs/HARDWARE_TEST.md](docs/HARDWARE_TEST.md)
- [docs/AGENT_HANDOFF.md](docs/AGENT_HANDOFF.md)
- [project_state.yaml](project_state.yaml)
- the task card named by [project_state.yaml](project_state.yaml)

## Toolchain

- Jo Engine commit `556d081146211b6a1cfa6591d70f9487d406758b`, plus `engine-patches/joengine-4bpp-sprites.patch`
- SH-ELF GCC 9.3.0
- MAME 0.289, pinned under `.deps/mame/mame0289`
- Yaba Sanshiro `1.20.37-2986eb`
- Python 3 and WSL GCC for generators and strict host tests

Use `setup_engine.ps1` and `setup_emulator.ps1` only in a disposable or dedicated implementation worktree when setup is required. The main audit worktree is intentionally dirty and contains private evidence.

## Checks and builds

Use DEV, BENCH, and CHECKPOINT verification from [docs/TEST_PLAN.md](docs/TEST_PLAN.md). Run split repository lanes only at the risk boundaries named by the active card:

```powershell
.\verify.ps1 -Lane Fast
.\verify.ps1 -Lane Oracle
.\verify.ps1 -Lane Target -TargetProfile EncounterTest -BuildOnly
.\verify.ps1 -Lane Full
```

`Full` calls `test.ps1`, which regenerates tracked evidence, so use an isolated copy unless the checkpoint explicitly owns every resulting file. A normal target build is:

```powershell
.\build.ps1 -Clean -Release
```

Read back `build/last_compile_profile.txt` and `build/hardware_release_manifest.txt`; only `release-normal-release` plus the required semantic/render/final-scanout emulator readback can satisfy Saturn-facing acceptance. Emulator output is not a substitute for the physical checks in [docs/HARDWARE_TEST.md](docs/HARDWARE_TEST.md).

## Content boundary

Do not commit or distribute ROMs, keys, disc images, raw captures, generated copyrighted graphics/audio, memory dumps, ISO/cue files, or disassembly bytes. Screenshots and the short capture under `docs/images/release/` and `docs/media/` are owner-approved release media (2026-11-14); add no other screenshots. Commit code, schemas, manifests of hashes/counts, tests, and documentation only.
