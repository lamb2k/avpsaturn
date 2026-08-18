# MSHvSF Saturn architecture evidence map

This map records what the official Saturn reference proves today and keeps
hardware responsibility unresolved where no trace exists. It is an evidence
index, not a reverse-engineered design specification.

## Verified package structure

The unchanged raw BIN contains a valid Saturn boot header for product
`T-1238G`, version `V1.000`, dated `19980903`, with the title
`MARVEL SUPER HEROES VS. STREET FIGHTER`. The ISO9660 data track has a flat
414-file root totaling 393,365,484 file bytes. The cue describes one data track
and eleven audio tracks.

The boot fields declare a `0x1800`-byte IP area, first-program load address
`0x060f0000`, and `0x10000`-byte first-read envelope. Pairing that envelope to
a specific ISO member remains unresolved until the boot file-read and SH-2 PC
path are traced.

The largest families are 235 `.ST2`, 79 `.PAC`, 71 `.ADP`, and 14 `.BIN`
members. Names and extensions are navigation leads only. They do not establish
compression, ownership, load address, or runtime purpose without decoder or
trace evidence.

The source cue points at a missing `.iso` filename. The launcher corrects only
that reference in a temporary cue, selects a 32 Mbit cartridge, and reaches the
licensed legal screen, title, and attract gameplay in Yaba Sanshiro 2 v1.20.37.

## Verified deterministic runtime path

Yaba Sanshiro's native play recorder restores a fixed compressed backup image
and applies exact Port 1 and Port 2 controller bytes at recorded frames. The
verified route cold-boots, selects Versus, chooses Ryu/Ken versus Spider-Man/
Captain America, leaves P2 neutral, and captures Ryu idle, walk, jump, normal
collision, visible health response, hit reaction, and recovery. Two cold runs
produced the same hashes for all 25 screenshot anchors.

This proves repeatable external behavior, not internal hardware ownership. The
canonical report is `data/mshvsf_saturn_first_pass.json`; RAM, VDP, SCSP, CD,
and DMA responsibilities remain open until traced.

Platform capacities, measured disc-package envelopes, open peak fields, and the
required next trace for every resource are tracked in
`data/mshvsf_hardware_budget.json`. The package-family measurements come from
`data/mshvsf_saturn_asset_topology.json`; they are storage evidence only and are
not treated as decompressed or simultaneously resident bytes.

## Measured normal-hit memory window

Stock Yaba Sanshiro v1.20.37 exposes a localhost MCP debug server. The
deterministic Ryu replay was paused at exact frames 3540 (idle), 3828
(normal-active), 3840 (impact), and 3900 (recovery), and every mapped work,
cartridge, video, color, and sound region was dumped and hashed. Raw bytes stay
ignored; `data/mshvsf_saturn_runtime_memory.json` is the tracked analysis.

| Transition | High work RAM | Low work RAM | Sound RAM | VDP1 VRAM | Cartridge DRAM | VDP2 VRAM |
|---|---:|---:|---:|---:|---:|---:|
| Idle to normal-active | 15,186 bytes / 42 pages | 948 / 8 | 16,124 / 5 | 43,889 / 21 | 0 / 0 | 0 / 0 |
| Normal-active to impact | 10,295 / 39 | 92 / 2 | 16,193 / 5 | 5,443 / 5 | 0 / 0 | 0 / 0 |
| Impact to recovery | 11,182 / 39 | 72 / 3 | 16,168 / 5 | 2,996 / 5 | 0 / 0 | 0 / 0 |

The cartridge contains 3,549,571 nonzero bytes across 909 4 KiB pages and is
byte-identical throughout this combat window. VDP2 VRAM is likewise stable,
while the sequential VDP1 list changes from 296 commands at idle to 334 at
normal-active, 308 at impact, and 307 at recovery. These are strong residency
and renderer-activity leads, but nonzero bytes are not an allocator high-water
mark and a sequential scan is not complete VDP1 jump/call traversal.

## Responsibility and budget map

| Resource | Verified evidence | Current responsibility | Next proof |
|---|---|---|---|
| SH-2 CPUs | Saturn executable members and successful boot | `UNRESOLVED` | Trace boot, loader, game loop, and interrupt ownership |
| VDP1 | Exact-frame dumps show 296/334/308/307 sequential commands and localized combat changes | Foreground submission confirmed; list ownership `UNRESOLVED` | Traverse command jumps/calls and map textures to package residency |
| VDP2 | VRAM and registers are byte-stable across the four gameplay anchors | Stable stage residency for this window; layer ownership `UNRESOLVED` | Decode layer enables, maps, and transition-time loads |
| Work RAM | Differential dumps localize normal-hit changes to 39-42 high-RAM pages and 2-8 low-RAM pages | Gameplay state is active in both regions; structures `UNRESOLVED` | Join changed ranges to SH-2 writers, health, actors, and collision |
| 32 Mbit expansion RAM | 3,549,571 nonzero bytes across 909 pages; byte-stable from idle through recovery | Stable combat-window residency confirmed; allocation ownership `UNRESOLVED` | Capture team/stage loading and compare cart configurations |
| SCSP | Sound RAM changes in five pages and one SCSP-register byte changes per transition | Event-associated audio activity confirmed; voice/sample ownership `UNRESOLVED` | Trace slot writes and isolate normal versus hit events |
| CD block | One data track plus eleven audio tracks | Disc transport verified; event routing `UNRESOLVED` | Log file reads and CDDA commands during the slice |
| DMA | No direct trace | `UNRESOLVED` | Record transfers during loading and active gameplay |

## Static leads requiring proof

- `00LOAD.BIN` contains valid SH-2 instructions and names `SYS.BIN` and
  `CPK.BIN`; its exact boot/load responsibility is not yet traced.
- `MM.BIN`, `SYS.BIN`, and `MVSOPEN.BIN` each branch over an `MBI1` marker at
  offset `0x4`. In each file, the big-endian word at `0x0c` points to another
  `MBI1` marker. This proves a repeatable module/container boundary relation,
  not the field's full semantics.
- `MM.BIN` statically names player, background, sound, and ADP package
  families. That makes it a strong file-read trace target, not a confirmed
  ownership assignment.
- `SYS.BIN` names `HMM.BIN`, `DIRBUF.BIN`, `NORMAL.BIN`, and `MVSOPEN.BIN` and
  contains an `EXT RAM ERROR.` diagnostic string.
- `CPK.BIN` contains exact aligned constants `0x22400000` and `0x22600000`,
  consistent with the two cartridge DRAM bank windows used by the pinned
  Saturn environment. It also contains exact constants in VDP1, VDP2, and
  SCSP spaces. Static constants are trace leads; they do not prove access,
  allocation, lifetime, or ownership.
- `MEMFIX.PAC`, `SEL.PAC`, `SEL2.PAC`, and character-named PAC/ADP files are
  useful capture breakpoints, not decoded formats.
- `M15_SRYU.ADP` is character-named, but its audio content and routing are not
  established.

The static program evidence is in
`data/mshvsf_saturn_program_inventory.json`; disc evidence is in
`data/mshvsf_saturn_disc_manifest.json`. Any architecture claim promoted above
`UNRESOLVED` must point to a runtime trace or a validated decoder and include a
falsification test.
