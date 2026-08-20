# CPS-2 to Saturn source ledger

Audit/access date: 2026-08-20

Target: `avspu` (`Alien vs. Predator (USA 940520)`)

Purpose: record only sources that constrain, challenge, or validate the architecture

## Source policy

Priority is: official hardware documentation; primary implementation source; rights-owned game/disc evidence; historical first-party material; community material only as a lead. Public URLs below do not contain the private target ROMs or generated target assets. All copyrighted inputs remain local.

Confidence means confidence that the source supports the stated claim, not that the resulting port behavior has been proven. `Primary-local` means a rights-owned or directly generated local artifact. `Primary-public` means official documentation or project source. `Derived` means a reproducible output from a primary input.

## Exact target set

The source of record for canonical names, sizes, CRC-32, and SHA-1 is the official MAME 0.289 `avspu` machine definition and list XML. The local SHA-256 column was measured from `avspu/` on 2026-08-20. `mame.exe -rompath . -verifyroms avspu` returned `romset avspu [avsp] is good` and `1 romsets found, 1 were OK.`

| Field | Value |
|---|---|
| Set | `avspu` |
| Description | `Alien vs. Predator (USA 940520)` |
| Parent / ROM parent | `avsp` / `avsp` |
| Source driver | `capcom/cps2.cpp` |
| Year / manufacturer | 1994 / Capcom |
| Visible display | 384x224, rotate 0, 59.637405 Hz |
| Raw timing | pixel clock 8,000,000; htotal 512, visible 64..447; vtotal 262, visible 16..239 |
| MAME device choice | `qsound_hle` in the `avspu` list XML |

### Canonical ROM inventory

| Region | File | Bytes | CRC-32 | MAME SHA-1 | Local SHA-256 |
|---|---|---:|---|---|---|
| maincpu | `avpu.03d` | 524288 | `42757950` | `e6acae73a300c0e07c21f776e6aa87628184b152` | `a1293c015bfaf6327f749f85a3ab49dae6204b4b3da66cf88e58c2b1fe0b4f5c` |
| maincpu | `avpu.04d` | 524288 | `5abcdee6` | `205e1ac8f4e359fd04e3a1e12425ba0b8330b1c1` | `e4060c9896a907fb4d0f408d4770e4464aa795ad6e5d279427f6c4db184e8d95` |
| maincpu | `avp.05d` | 524288 | `fbfb5d7a` | `5549bc9d780753bc9c10fba82588e5c3d4a2acb2` | `8b3d64528df3e771317d5f0b5d7a4a097eaf5ef0021e060c82352966c2dddd60` |
| maincpu | `avp.06` | 524288 | `190b817f` | `9bcfc0a015ffba9cdac25b6270939a9690de5da7` | `d681d2dd66068c979e5c272d0c5d7d98f5809fb9e2a00c3f84806dc2026c8784` |
| gfx | `avp.13m` | 2097152 | `8f8b5ae4` | `457ce959aa5db3a003de7dda2b3799b2f1ae279b` | `a25a1ebba42045476e98c9994a12bb70031eb80accdcd8ba4d4fd9a45c03405c` |
| gfx | `avp.15m` | 2097152 | `b00280df` | `bc1291a4a222d410bc99b6f1ed392067d9c3999e` | `f3f962d18331cb15db5eb495ab6bc623b992c2a495a8ccb249780854a8b547da` |
| gfx | `avp.17m` | 2097152 | `94403195` | `efaad001527a5eba8f626aea9037ac6ef9a2c295` | `3b6c31d3cc08567a2b6e35f7e7e520589363f788cebcf127eadd1878829d8a3d` |
| gfx | `avp.19m` | 2097152 | `e1981245` | `809ccb7f10262e227d5e9d9f710e06f0e751f550` | `8783f64c3f4620b907a4716e785ba4d1b4547f52a94d6f0458b8964142509614` |
| gfx | `avp.14m` | 1048576 | `39933b1e` | `911754d8930e0df71a3d929e4bc80f9efb9ad1ff` | `af3727cdcca23893e9a251896f3f47de6040a00cc5c0c470bf6747341c2da7e1` |
| gfx | `avp.16m` | 1048576 | `85412860` | `25595161500eae9c9b329ca37a4b306ab8b96430` | `a51251cc7685a645a605a231219797565fc84a353d8acb1d34c2e3f339a53520` |
| gfx | `avp.18m` | 1048576 | `2e2beb06` | `0de6bdca37a4ac05568b23cb071c66f51f737c08` | `5f828881f93a633a7d4f9d9a043c115a807ae122eeea5b35aa5c4e0ce7f763d6` |
| gfx | `avp.20m` | 1048576 | `e4798d1a` | `7c90a9b98eba9b26992d3d02875b64431b941c24` | `be8499cbe08f042a39334c19834611e684e372fc62bf010ebf7105b321e30ddb` |
| audiocpu | `avp.01` | 131072 | `2d3b4220` | `2b2d04d4282550fa9f6e1ad8528f20d1f2ac02eb` | `88f7f38e64c5d5c16264768230fc599a4f8de5904633a814789a192a8baa19b3` |
| qsound | `avp.11m` | 2097152 | `83499817` | `e65b0ebd61ddc748842a9d4d92404b5305307623` | `4b25c0c1517e6b3951997779928da95d03f5b431c672491254bbce2c017af9a4` |
| qsound | `avp.12m` | 2097152 | `f4110d49` | `f27538776cc1ba8213f19f98728ed8c02508d3ac` | `986821590c13ba2b27eee43cc44c68cb61f225fb6a354b818c7ada5451fc7d9e` |
| key | `avspu.key` | 20 | `4e68e346` | `60d5a12c77d07efc01f48968f4a12c59bf6b629e` | `a2c615d23c610c2617d43f2a1ea8cb4d0ce5f7d24b3cb7dc122f07f8724a956f` |

The file `avspu/dl-1425.bin` is 24,576 bytes with SHA-256 `524a25bcd153be24594d37c0dbd334fe4f384f77da73c2058dc60fc1f581cf18`. It is an extra local QSound DSP dependency and is not a canonical `avspu` list-XML member; MAME 0.289 configures this machine with `qsound_hle`. It must not be included in the target-set hash contract.

### Derived program and graphics spaces

| Local artifact | Bytes | SHA-256 | Meaning / permitted use | Caveat |
|---|---:|---|---|---|
| `.deps/mame/actorprobe/decrypted_program_2m.bin` | 2097152 | `0c14f4094d25787401aa949657620ff495ae8606c1cfd8ae2d059b94c3d478e9` | MAME 68000 program/data address-space dump; use for absolute data tables and pointer-addressed bytes. | Do not decode instructions from it; CPS-2 opcode fetch has a separate decrypted space. |
| `.deps/mame/actorprobe/decrypted_opcodes_2m.bin` | 2097152 | `e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501` | MAME decrypted opcode-fetch space; use for instruction decoding, including PC-relative code tables. | PC-relative data must be attributed to the correct address space. |
| `.deps/mame/captures/gfx_region.bin` | 16777216 | `ed6afd62ecbc3defddf4d8001b9dbe8735db1112fc7d38c9e21d77383cbd7671` | MAME-decoded graphics region used by extraction tools. | A derived decoder output, not a ROM-set member; preserve input and decoder pins. |

`tools/mame_dump_code_spaces.lua:1-25` is the local procedure distinguishing `program` and `opcodes`. MAME's CPS-2 source maps a separate opcode address space and decrypts into it (`.deps/mame-source/cps2.cpp:1316-1318`, `1743`, `10931`).

## Consequential public and local sources

| Source | Date or commit | Tier | Claim supported | Subsystem | Confidence | Conflict / caveat |
|---|---|---|---|---|---|---|
| [MAME 0.289 release](https://github.com/mamedev/mame/releases/tag/mame0289) and local `mame.exe` | Release 2026-07-30; executable SHA-256 `af6966108d9b52c22465c6d50f4e5d50cc371b50f2d27dc443935f287aad37a3` | Primary-public/local | Canonical emulator version for set identity, list XML, deterministic traces, and ROM verification. | Target, oracle | High | MAME is an oracle model, not physical CPS-2 proof for every undocumented behavior. |
| [MAME CPS-2 driver at tag mame0289](https://github.com/mamedev/mame/blob/mame0289/src/mame/capcom/cps2.cpp) | Tag `mame0289`; accessed 2026-08-20 | Primary-public | `avspu` ROM definition, CPS-2 object RAM, opcode decrypt mapping, sprite expansion and priority. | ROM, CPU, video | High | Local `.deps/mame-source/cps2.cpp` is a copied source snapshot; the binary/tag remains the pin. |
| [MAME CPS video implementation](https://github.com/mamedev/mame/blob/mame0289/src/mame/capcom/cps1_v.cpp) | Tag `mame0289`; accessed 2026-08-20 | Primary-public | CPS scroll layer, palette, tile map, and row-scroll semantics used by extractors. | Stage/video | High | Comments include known emulation uncertainties; do not turn a comment into hardware fact. |
| [MAME QSound implementation](https://github.com/mamedev/mame/blob/mame0289/src/devices/sound/qsound.cpp) | Tag `mame0289`; accessed 2026-08-20 | Primary-public | QSound is a sixteen-channel sample player with DSP command/data behavior and about 24.038 kHz output in the LLE model. | Audio | High for implementation, Medium for physical unknowns | `avspu` uses MAME's HLE device in list XML; use QSound source to understand semantics, not as proof of exact local output. |
| [MAME 0.289 debugger](https://docs.mamedev.org/debugger/index.html), [Lua debugger API](https://docs.mamedev.org/luascript/ref-debugger.html), [memory commands](https://docs.mamedev.org/debugger/memory.html) | Docs 0.289; accessed 2026-08-20 | Primary-public | Breakpoints/watchpoints, register and address-space access, save/load, and raw memory export can form the deterministic oracle. | Validation | High | Determinism still depends on pinned config/NVRAM/input and complete field selection. |
| [Sega VDP1 User's Manual ST-013-R3-061694](https://antime.kapsi.fi/sega/files/ST-013-R3-061694.pdf) | 1994-06-16; accessed 2026-08-20 | Primary-public, official Sega | Command tables, ordering/jumps, normal sprites, 4bpp 16-color bank mode, draw/frame behavior, VRAM constraints. | VDP1 | High | Official manual describes capability, not AvP workload performance. |
| [Sega VDP2 User's Manual ST-58-R2-060194](https://antime.kapsi.fi/sega/files/ST-058-R2-060194.pdf) | 1994-06-01, v1.1; accessed 2026-08-20 | Primary-public, official Sega | Scroll screens, pattern-name data, priorities, CRAM, and NBG0/NBG1 line-scroll tables. | VDP2 | High | Plane assignment remains an AvP design decision requiring hardware proof. |
| [Saturn Overview Manual ST-103-R1-040194](https://antime.kapsi.fi/sega/files/ST-103-R1-040194.pdf) | 1994-04-01; accessed 2026-08-20 | Primary-public, official Sega | VDP2 performs final scroll/sprite priority composition and output. | Final scanout | High | High-level overview; register details come from VDP2 manual. |
| [Saturn SCSP User's Manual ST-077-R2-052594](https://antime.kapsi.fi/sega/files/ST-077-R2-052594.pdf) | 1994-05-25; accessed 2026-08-20 | Primary-public, official Sega | 32 slots, PCM/FM capabilities, sound-memory cycle and DMA constraints. | Audio | High | Does not dictate how Capcom mapped QSound events. |
| [Saturn Extended RAM Cartridge Manual, Technical Bulletin 47](https://antime.kapsi.fi/sega/files/ST-TECH-47.pdf) | v1.02; accessed 2026-08-20 | Primary-public, official Sega | 8/32 Mbit IDs; CPU access; SH-2/SCU DMA read and write restrictions. | Cart/memory | High | The existing project specifically requires 32 Mbit. Hardware timing is still measured locally. |
| [Sega Saturn Dual CPU User's Guide ST-202-R1-120994](https://antime.kapsi.fi/sega/files/ST-202-R1-120994.pdf) | 1994-12-09; accessed 2026-08-20 | Primary-public, official Sega | Master/slave share external devices; concurrent shared globals require sequencing. | CPU scheduling | High | Does not show a second SH-2 would be useless; it supports deferring it until a bounded job is measured. |
| [Sega VDP1 Basic Processing Guide ST-157-R1-092994](https://antime.kapsi.fi/sega/files/ST-157-R1-092994.pdf) | 1994-09-29; accessed 2026-08-20 | Primary-public, official Sega | `SPR_WaitDrawEnd` and explicit application command/VRAM control make draw-end a required measurement. | VDP1 validation | High | Project uses Jo/SGL, not this library directly; the hardware obligation remains. |
| [N64Recomp](https://github.com/N64Recomp/N64Recomp/blob/main/README.md) | `main` as accessed 2026-08-20 | Primary-public project source | Static recompilation needs symbols/metadata, function boundaries, indirect-call handling, relocations/overlays, and a platform runtime. | Translation prior art | High for N64Recomp; Medium for analogy | Different source CPU/platform and ELF ecosystem. It is evidence about missing work, not a ready 68000-to-SH-2 tool. |
| [Jo Engine official source](https://github.com/johannes-fetz/joengine) | Local pin `556d081146211b6a1cfa6591d70f9487d406758b`; source commit date 2026-05-01 | Primary-public/local | Actual engine/API/build source used by the Saturn runtime. | SDK/runtime | High | Local checkout has the required private patch and is therefore intentionally dirty. Setup default URL is public; current Git remote is a local mirror. |
| `engine-patches/joengine-4bpp-sprites.patch` | SHA-256 `845bde3e67100c96a52132fa13db05bacf9411ef68a9eb34dd80e04a063b086d` | Primary-local | Adds project-required 4bpp sprite and audio-status behavior. | VDP1/audio | High for code presence | Emulator and host readbacks do not equal physical proof. |
| Yaba Sanshiro package | `1.20.37-2986eb`; archive SHA-256 `c34ff6766633f319bdb993481e4b82c9297d4e2a1ff1fda73a3cff4d380c2f5c`; EXE SHA-256 `016112708fc77ec53b8a36c4ef52e300a78b3fb079e815f60b1a51fa1661999c` | Primary-local binary | One pinned Saturn-emulator validation environment. | Emulator | High for identity | One-emulator results stay “proven only in one emulator.” A locally modified source checkout at `71c973f...` is diagnostic and is not the clean package pin. |
| SH-ELF GCC / host tools | SH GCC 9.3.0; GNU Make 4.2.1; Python 3.13.0; WSL GCC 13.3.0 | Primary-local tool output | Reproduces target compile and strict host tests. | Build/test | High | Python resolution differs between `build.ps1` and `test.ps1`; invocations should pass it explicitly. |

## Repository-derived sources

| Source | Date or commit | Tier | Claim supported | Subsystem | Confidence | Conflict / caveat |
|---|---|---|---|---|---|---|
| `data/avsp_object_corpus_verification.json` | Live tree 2026-08-20 | Derived from MAME traces/ROM | 18,986 eligible: 18,025 exact, 961 game-omitted, zero mismatches. | Object emission | High | Verifies the emitter for eligible objects; game omissions remain excluded. Header comments contain older counts and have drifted. |
| `data/avsp_sprite_demand.json` | Live tree 2026-08-20 | Derived from MAME traces | 5,302 frames; mean 40.67 objects/346.31 tiles; peak 86 objects/909 tiles; peak 13 palettes. | VDP1/palette budget | High for demand | It is explicitly demand-side only and proves no Saturn performance. |
| `data/rp4_street_readback.json` and `data/rp4_street_live_readback.json` | RP4/live dirty evidence | Derived emulator readback | Exact bounded two-plane/object fixture and live VDP1 controls. | VDP1/VDP2 | Medium-High | Live dirty capture values differ from the older handoff text; pin the artifact used. One emulator, no hardware. |
| `data/avsp_residency_budget.json` | RP5 `6ac45b3` plus live artifacts | Derived static model | Fixed cart/VRAM/work-RAM budget and declared gaps. | Memory/audio | Medium | Debug Encounter headroom is only 320 bytes; live allocator/SCSP high-water is missing. |
| `data/round1_rowscroll_classification.json` | RP7 `e79f666` | Derived MAME trace | Six frontend scenes need line scroll; captured gameplay scenes and RP4 street do not. | VDP2/scene schema | High for traced route | Does not prove untraced/full-game scenes. Runtime schema has no line-scroll opcode yet. |
| `data/avsp_palette_coverage.json` | Live tree 2026-08-20 | Derived MAME trace and archive | Ten shipped banks versus 15 route references; five uncovered; not a CRAM capacity limit. | Palette/assets | High | The live path currently renders only a narrow actor subset, so this is a scope gap rather than universal visible corruption. |
| `test.ps1` and `tests/*` | Isolated run 2026-08-20, exit 0 | Primary local test procedure / derived result | Host models, bounds, deterministic generators, retained oracle comparisons, and negative controls pass. | Validation | High for asserted checks | Tests regenerate data, so the audit ran them in a shadow copy. They do not build a normal release or prove audio/hardware. |
| `build/hardware_release_manifest.txt` | 2026-08-20 07:50 local | Derived build artifact | Current ignored ISO identity and packaged audio/assets. | Build | High for artifact identity | `profile=encounter-test`, so it is not a hardware release candidate despite the filename. |

## Rights-owned original Saturn-port evidence

This lane is deliberately separate: `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-MSHvSF`, branch `codex/mshvsf-reference-lane`, clean commit `dc5d3ea81ac8751b312234bac95d51370151a8e5`.

| Source | Date / identity | Tier | Claim supported | Subsystem | Confidence | Conflict / caveat |
|---|---|---|---|---|---|---|
| `docs/MSHVSF_SATURN_ARCHITECTURE.md` | Disc product `T-1238G`, `V1.000`, date `19980903`; report at `dc5d3ea` | Primary-local disc/runtime analysis | One data and 11 audio tracks; deterministic combat anchors; 32 Mbit cart; flat VDP1 lists; per-16x16-tile 4bpp sprites; live CRAM; SCSP observations. | Original port | High for measured bytes/commands | It is one title. VDP2 registers read all zero in the instrument; layer ownership is unresolved. SCSP streaming interpretation is inferred. |
| `data/mshvsf_saturn_first_pass.json` | Two cold runs, 25 identical screenshot hashes | Derived from original disc | Deterministic reference route and bounded memory/graphics/audio snapshots. | Oracle/reference | High for captured route | Screenshot identity is not full semantic identity. |
| `data/mshvsf_porting_patterns.json` | At `dc5d3ea` | Derived policy | A method can be reusable after proof, but a Capcom practice remains candidate until a second official port confirms it. | Generalization | High | This policy is intentionally stricter than the available one-title evidence. |

MSHvSF findings support trying a per-tile baseline and fixed cart residency. They do not specify AvP actor behavior, stage mapping, memory layout, disc packaging, or audio routing, and they do not justify a generalized Capcom engine.

## Source conflicts and resolution rules

1. **Live repository versus status prose:** use commit/artifact facts and current code. Older RP4 prose is historical and cannot override RP5-RP7 commits or live data.
2. **MAME demand versus Saturn capacity:** MAME establishes what must be drawn; only emulator plus physical Saturn telemetry establishes whether the Saturn method finishes on time.
3. **Original-port observation versus general rule:** one MSHvSF measurement is a candidate pattern. Require AvP-specific proof and another official title before generalization.
4. **Static budget versus live residency:** file sizes and nonzero bytes are not allocator occupancy. Require high-water, transfer, lifetime, and canary evidence.
5. **Internal readback versus visible output:** command/VRAM/CRAM equality does not prove final VDP2 scanout. Require final capture with provenance.
6. **Program versus opcode image:** data/pointers come from the program/data view; decoded instructions come from the opcode-fetch view. A tool must declare which it consumed.

## Minimum provenance record for new artifacts

Every new generated artifact must record:

- target set, parent, and region/revision;
- canonical contributing ROM file names, CRC-32, MAME SHA-1, and local SHA-256;
- source region, address space (`program`, `opcodes`, `gfx`, `audiocpu`, `qsound`), offset, and length;
- MAME executable version/hash and capture configuration when a trace is involved;
- extractor path and Git commit/dirty fingerprint;
- full command/parameters and schema version;
- output byte length and SHA-256;
- runtime consumer and lifetime/phase;
- evidence tier and explicit exclusions.

An artifact without this record may be used as a diagnostic lead but not as acceptance evidence.
