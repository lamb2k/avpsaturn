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
byte-identical throughout this combat window. VDP2 VRAM is likewise stable.
Nonzero bytes remain an occupancy lead, not an allocator high-water mark.

## Measured VDP1 command-list control flow

The sequential scan has been replaced by a real command-processor traversal that
honours jump, call, return and skip modes and the single hardware return-address
register. The tracked report is
`data/mshvsf_saturn_vdp1_control_flow.json`; the traversal is
`reference_engine/vdp1.py`, shared with the memory analyzer so there is one
implementation.

| Anchor | Reachable slots | Sequentially stored | Stored nonzero slots | Residue past terminator | Drawn commands |
|---|---:|---:|---:|---:|---:|
| idle 3540 | 296 | 296 | 772 | 476 | 293 |
| normal-active 3828 | 334 | 334 | 772 | 438 | 331 |
| impact 3840 | 308 | 308 | 772 | 464 | 305 |
| recovery 3900 | 307 | 307 | 772 | 465 | 304 |

`MEASURED` on Marvel, with each finding's falsification recorded in the report:

- Every reachable command at all four anchors uses `JUMP_NEXT`. The list is a
  flat run to a draw-end command, with zero links followed and zero control-flow
  anomalies. The earlier sequential reading was therefore correct here, but that
  agreement is now shown rather than assumed.
- The command table holds 772 contiguous nonzero 32-byte slots at every anchor
  while the live list reaches only 296 to 334. The excess is residue from longer
  earlier lists, so nonzero extent is neither this frame's command count nor an
  allocator high-water mark.
- All 1,233 drawn commands across the four anchors are **16x16 normal sprites**.
  No other size, and no scaled or distorted sprite command, appears in any
  reachable set. The official port draws per 16x16 tile rather than from
  precomposed cels.
- Every drawn command uses `CMDPMOD` 0x0880: 16-colour bank mode with `CMDCOLR`
  as the CRAM bank address. Twelve to fourteen distinct banks are live per
  anchor, spaced 16 entries apart.
- Horizontal flip is carried in `CMDCTRL` character-read-direction bits, not by
  storing mirrored art: 101 to 107 `FLIP_X` commands per anchor, plus `FLIP_Y`
  and `FLIP_XY` at normal-active.
- Referenced texture spans total 19,968 bytes at idle, 23,552 at normal-active,
  21,632 at impact, and 21,504 at recovery, across 17 to 26 merged spans. These
  are the bytes commands reference, not proof of allocation or lifetime.

VDP1 registers read back as all zeros through the debug interface, so the real
draw-start address and frame-buffer control state stay `UNRESOLVED`. A single
captured frame also cannot show a control-flow mode the game uses only in scenes
outside this window.

## Measured VDP2 colour ownership and SCSP slot activity

The tracked report is `data/mshvsf_saturn_vdp2_scsp.json`. Two of these results
are negative, and the negatives are what make the remaining gaps actionable.

- The **VDP2 register block reads back as all zeros** at all four anchors, 0 of
  288 bytes non-zero. Layer enables, plane maps, priorities and scroll values
  therefore cannot be decoded from this capture at all. VDP2 layer assignment
  stays `UNRESOLVED` for an instrument reason, and its probe now names a
  register write watchpoint rather than a better parser.
- Every VDP1 sprite colour bank measured at every anchor resolves into a
  **populated** 16-colour bank of VDP2 colour RAM. All 128 colour-RAM banks are
  populated, 12 to 14 are referenced per anchor, and banks are 16 entries apart.
  Colour-bank sprites therefore spend a **VDP2 colour-RAM** budget, not a VDP1
  texture budget.
- Colour RAM changes **inside** the combat window while VDP2 VRAM does not: 16
  bytes in one bank across idle to normal-active, none across normal-active to
  impact, and 35 bytes across three banks from impact to recovery.
- Only **three of thirty-two SCSP slots** hold any non-zero register content, and
  every active slot's registers are byte-identical across all four anchors.
  Exactly one byte of the SCSP common-register region changes per transition, and
  it is the same byte every time.
- Sound RAM nevertheless changes by roughly 16 KiB across five pages on every
  transition. Static slots plus a per-transition buffer refill is consistent with
  a continuously-playing mixed stream rather than a slot keyed per game event.
  That reading is `INFERRED`: four sampled frames cannot see a register write
  that happens between them.

Cue attribution stays `UNRESOLVED`, and its probe moved accordingly: slot
registers cannot attribute a cue when they never change, so the evidence lives in
the sound-RAM refill regions and needs a write watchpoint plus a whiff control.

## Responsibility and budget map

| Resource | Verified evidence | Current responsibility | Next proof |
|---|---|---|---|
| SH-2 CPUs | Saturn executable members and successful boot | `UNRESOLVED` | Trace boot, loader, game loop, and interrupt ownership |
| VDP1 | Real control-flow traversal reaches 296/334/308/307 commands, all `JUMP_NEXT`, all 16x16 sprites in 16-colour bank mode | Per-tile foreground submission confirmed; list *ownership* and the writer still `UNRESOLVED` | Identify the SH-2 code that builds the list and map texture spans to package residency |
| VDP2 | VRAM byte-stable across the four anchors; colour RAM populated in all 128 banks and changing during combat; **register block reads back all zeros** | Owns sprite colour for the VDP1 path (`MEASURED`); layer ownership `UNRESOLVED` because the registers are unreadable through this instrument | Observe VDP2 register *writes* with a watchpoint; a better parser cannot help |
| Work RAM | Differential dumps localize normal-hit changes to 39-42 high-RAM pages and 2-8 low-RAM pages | Gameplay state is active in both regions; structures `UNRESOLVED` | Join changed ranges to SH-2 writers, health, actors, and collision |
| 32 Mbit expansion RAM | 3,549,571 nonzero bytes across 909 pages; byte-stable from idle through recovery | Stable combat-window residency confirmed; allocation ownership `UNRESOLVED` | Capture team/stage loading and compare cart configurations |
| SCSP | Three of 32 slots hold register content and none change across the window, while sound RAM moves ~16 KiB across five pages per transition | Delivers a refilled mixed stream rather than a slot keyed per event (`INFERRED`); cue attribution `UNRESOLVED` | Watchpoint sound-RAM writes across an isolated attack and impact, with a whiff control |
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
