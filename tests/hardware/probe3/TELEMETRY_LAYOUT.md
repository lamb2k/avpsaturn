# Probe 3 telemetry block

The fixed linker-visible symbol is `avsp_probe3_telemetry`. The release-probe3
manifest records its exact low-work-RAM address. All values are native SH-2
32-bit unsigned words. The block is 252 bytes; readers must reject any other
schema or size.

| Offset | Field |
| ---: | --- |
| `0x00` | `canary_begin` (`0xA53C19E7`) |
| `0x04` | `magic` (`PRB3`, `0x50524233`) |
| `0x08` | `schema` (`1`) |
| `0x0c` | `status` |
| `0x10` | `mode` |
| `0x14` | `mode_frame` |
| `0x18` | `frame_number` |
| `0x1c` | `workload_checksum_word` |
| `0x20` | `reachable_commands` |
| `0x24` | `drawn_commands` |
| `0x28` | `vdp1_draw_end_state` |
| `0x2c` | `draw_end_deadline_fields` |
| `0x30` | `cpu_prepare_ticks` |
| `0x34` | `texture_bytes_copied` |
| `0x38` | `copy_count` |
| `0x3c` | `copy_ticks` |
| `0x40` | `legal_copy_direction` |
| `0x44` | `cram_writes` |
| `0x48` | `cartridge_read_bytes` |
| `0x4c` | `missed_fields` |
| `0x50` | `late_command_lists` |
| `0x54` | `skipped_fields` |
| `0x58` | `repeated_fields` |
| `0x5c` | `canary_state` |
| `0x60` | `asset_failures` |
| `0x64` | `failure_reason` |
| `0x68` | `overload_expected` |
| `0x6c` | `overload_tripped` |
| `0x70` | `representative_high_water` |
| `0x74` | `peak_high_water` |
| `0x78` | `summary_checksum` |
| `0x7c` | `complete` |
| `0x80` | representative `AvspProbe3ModeResult` (40 bytes) |
| `0xa8` | peak-909 `AvspProbe3ModeResult` (40 bytes) |
| `0xd0` | overload `AvspProbe3ModeResult` (40 bytes) |
| `0xf8` | `canary_end` (`0xA53C19E7`) |

Each 40-byte mode result contains, in order: reachable high water, drawn high
water, CPU-preparation tick high water, texture-byte high water, copy-count
high water, copy-tick high water, cartridge-read-byte high water, missed
fields, late command lists, and detector-tripped state.

The displayed summary checksum is calculated only after the bounded schedules
finish. The measurement phase has no telemetry overlay. Emulator tick and
field values prove instrumentation semantics only and are not physical Saturn
timing evidence.
