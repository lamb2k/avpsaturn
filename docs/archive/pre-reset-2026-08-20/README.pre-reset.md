# Alien vs. Predator native Sega Saturn port

Private capability project for a native SH-2 Sega Saturn port of Capcom's US
CPS2 `avspu` revision. This is not an emulator, video player, or public ROM
distribution. Host tools translate ROM data/routines into semantic manifests
and private generated payloads; the Saturn runtime implements the game using
VDP1, VDP2, SCSP PCM, CDDA, work RAM, and a required 32 Mbit expansion cart.

Current acceptance status: **Capability Gate 1 0/7; full game 0/9**.

## Current work

The active body is the complete player-controlled presentation route from cold
boot through the Round 2 title:

`legal/QSound/Capcom/opening -> all story panels -> title -> Start transition
-> character select -> confirmation -> Round 1 title -> every Round 1 scene ->
results/intermission -> Round 2 title`.

The existing Saturn route boots and reaches gameplay, but it is not yet a
faithful complete level. ROM-derived title/select objects and controls run, and
their palette, held VDP1 schedules, confirmation shutter, and ROM-derived Round
1 title pass the current checks. Scene contracts, a cadence-1 route census, and
the minimal scene runtime also exist. The active RP4 work is proving parallax,
map paging, per-object layer priority, and live Saturn resource/register state.
Full scenes, stage CDDA, real AI, complete collision, cast coverage, and
hardware proof remain open. Thirteen legacy capture-derived scene holds are
regression oracles that must leave runtime use.

The presentation target explicitly supports parallax:

- CPS scroll3 rear -> Saturn NBG1;
- CPS scroll2 main/row-scrolled -> Saturn NBG0;
- actors and transient objects -> VDP1;
- source-proven foreground-above-object content -> NBG2 or bounded VDP1.

Both planes use one endpoint-aligned 384-to-352 transform. A single flattened
gameplay bitmap is a measured fidelity gap and is not the final architecture.

For the exact restart state and next work, read:

1. [AGENTS.md](AGENTS.md)
2. [docs/GOAL.md](docs/GOAL.md)
3. [docs/AGENT_HANDOFF.md](docs/AGENT_HANDOFF.md)
4. [docs/PARITY_PLAN.md](docs/PARITY_PLAN.md)
5. [docs/ROUND1_EXECUTION_PLAN.md](docs/ROUND1_EXECUTION_PLAN.md)
6. [docs/NEXT_AGENT_PROMPT.md](docs/NEXT_AGENT_PROMPT.md)
7. For a long autonomous coding run only:
   [docs/AUTONOMOUS_EXECUTION_BOOK.md](docs/AUTONOMOUS_EXECUTION_BOOK.md)

## Architecture overview

- Native SH-2 game/world logic; no 68000 interpreter.
- ROM-derived animation script interpreter and semantic object emitter.
- Source-derived collision over the same animation record used for rendering.
- VDP1 per-object actor rendering from referenced 4bpp tiles.
- VDP2 multi-plane presentation with measured scroll/priority and optional line
  scroll.
- ROM-derived scene programs for maps, palettes, objects, fades, masks, input,
  timing, and audio.
- Fixed F0/F1/G0 presentation lifetimes in 4 MB expansion RAM.
- Compact first-stage loader plus `/GAME.BIN` staged through low work RAM.
- CDDA for long music and SCSP PCM for cues/voices, with no data-track reads
  during an uninterrupted CDDA interval.

The project currently depends on Jo Engine/SGL for startup and selected Saturn
services, but project modules own the game semantics and resource layout. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## What is measured today

- Reconstructed 16 MiB graphics region matches MAME's graphics region.
- Animation records, jumps, selected assembly families, and a 732-frame script
  walk are decoded/checked.
- The street-alien assembly/emission path is checked; selected boss assemblies
  reproduce capture oracles pixel-for-pixel.
- Street defender collision consumes source-derived records on the same frame
  as rendering.
- ROM-derived title/select object order, cursor anchors, selection propagation,
  and 352x224 clipping run on Saturn.
- Staged loader reaches an advancing native `WAVE_ONE` state in pinned Yaba.
- Street scroll2 and scroll3 move at different rates, proving parallax is
  required.

These are mechanism proofs. They do not establish complete gameplay, audio,
performance, or hardware parity.

## Repository and content boundary

This repository intentionally excludes:

- ROMs and decrypted opcode images;
- raw MAME captures and save states;
- generated copyrighted graphics/audio and private payloads;
- ISO/cue/WAV files, emulator state, and trace logs.

Tracked manifests contain semantic metadata, hashes, sizes, addresses, and test
results needed to reproduce work with privately supplied inputs. Do not publish
or redistribute generated game content. See [NOTICE.md](NOTICE.md).

The repository is independent even though its checkout is nested inside
`C:\Game Dev\BrooklynBangoutX`. Run Git from this directory. The active branch
at the current handoff is `codex/avp-master-plan`; its dirty tree is intentional.
Do not reset, clean, or bulk-stage untracked diagnostics.

## Toolchain

Build and capture scripts locate bundled dependencies themselves:

- SH-2 GCC/Jo Engine/SGL under the project dependency cache;
- stock MAME 0.289 for deterministic source observation;
- bundled Python at
  `%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`;
- pinned Yaba Sanshiro 1.20.37 for the current emulator readback workflow.

Do not assume `python`, `mame`, or the SH-2 compiler is on PATH.

## Build and checks

From this repository in PowerShell:

```powershell
.\test.ps1
.\build.ps1 -FrontendShotTest -Clean
.\build.ps1 -FrontendTest -Clean
.\build.ps1 -EncounterTest -Clean
.\build.ps1 -Clean -Release
```

Use only the profiles relevant to the current verification order; a focused
profile is not the release candidate. `build.ps1` verifies staged boot ISO
members and rejects a game BSS end past `0x060c0000`.

Normal verification order:

1. deterministic analyzers/converters and negative controls;
2. host tests, full `test.ps1`, and deterministic regeneration;
3. focused Saturn build and member hashes;
4. visible emulator register/VRAM/CRAM/runtime readback;
6. normal digital-pad no-skip route through Round 2 title;
7. `-EncounterTest` through `COMPLETE`;
8. clean normal-release title boot;
9. physical hardware only when its prerequisites are met.

Never use `-Release` to hide a Jo memory check. The current configuration uses
`JO_MAX_SPRITE=128` and `JO_FS_MAX_FILES=128`; every clean build must re-check
the map and live sprite high-water.

## Controls

Target digital-pad mapping:

- D-pad: source directions/lane movement;
- Saturn A/B/C: the three source action buttons;
- Start: Start/pause where source state supports it;
- X: diagnostic HUD only in diagnostic builds.

Character select is a non-wrapping 2x2 grid. A/B/C confirm; no cancel action was
measured. Predator Warrior is the only accepted gameplay character in the
current work body; other selections remain explicitly `ADAPTED`.

## Hardware target

- NTSC Saturn;
- digital controller;
- 32 Mbit / 4 MB expansion RAM cartridge;
- exact cue with data and CDDA tracks;
- sustained 60 Hz and ten-minute soak.

The current build is **not hardware-ready**. Follow
[docs/HARDWARE_TEST.md](docs/HARDWARE_TEST.md) only after the emulator,
presentation, audio, and memory prerequisites pass.
