# Alien vs. Predator native Sega Saturn port

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

The repository has strong MAME extraction, actor/collision/animation/object analyzers, deterministic manifests, palette/bounds checks, and a bounded Saturn render fixture. The current playable runtime is not yet a translated game core: most gameplay remains authored, ROM actor coverage is narrow, and stage CDDA is disabled.

The former RP presentation roadmap is archived under `docs/archive/pre-reset-2026-08-20/`. It is not active guidance. Current status lives in [project_state.yaml](project_state.yaml), and the active bounded body is the task card named there.

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

Run the split verification lanes instead of the monolithic suite during ordinary iteration:

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

Do not commit or distribute ROMs, keys, disc images, raw captures, generated copyrighted graphics/audio, memory dumps, screenshots, ISO/cue files, or disassembly bytes. Commit code, schemas, manifests of hashes/counts, tests, and documentation only.
