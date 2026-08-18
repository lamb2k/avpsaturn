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

## Responsibility and budget map

| Resource | Verified evidence | Current responsibility | Next proof |
|---|---|---|---|
| SH-2 CPUs | Saturn executable members and successful boot | `UNRESOLVED` | Trace boot, loader, game loop, and interrupt ownership |
| VDP1 | Deterministic gameplay visibly renders foreground objects; hardware ownership is not traced | `UNRESOLVED` | Capture command tables around the Ryu slice |
| VDP2 | Deterministic gameplay visibly renders a stage background; hardware ownership is not traced | `UNRESOLVED` | Capture register state and layer maps around the same frames |
| Work RAM | Runtime boots | `UNRESOLVED` | Differential dumps for actor, projectile, collision, and health state |
| 32 Mbit expansion RAM | Successful emulator configuration | Requirement and allocation `UNRESOLVED` | Compare no-cart, smaller-cart, and 4 MB traces |
| SCSP | Runtime emits audio | Voice and sample responsibility `UNRESOLVED` | Trace slot writes and RAM transfers per isolated event |
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
