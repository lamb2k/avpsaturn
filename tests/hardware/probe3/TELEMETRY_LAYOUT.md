# Probe 3 telemetry block

`avsp_probe3_telemetry` is a 624-byte, linker-visible low-work-RAM block.
Schema 3 readers must use the manifest address and reject any size/schema
drift. Values are native SH-2 32-bit unsigned words.

| Offset | Field |
| ---: | --- |
| `0x000` | `canary_begin` |
| `0x004` | `magic` |
| `0x008` | `schema` |
| `0x00c` | `status` |
| `0x010` | `phase` |
| `0x014` | `mode` |
| `0x018` | `mode_frame` |
| `0x01c` | `frame_number` |
| `0x020` | `workload_checksum_word` |
| `0x024` | `requested_workload_tile_draws` |
| `0x028` | `submitted_workload_draw_calls` |
| `0x02c` | `vdp1_draw_end_state` |
| `0x030` | `draw_end_deadline_fields` |
| `0x034` | `detector_enabled` |
| `0x038` | `detector_predicate_tripped` |
| `0x03c` | `field_delta` |
| `0x040` | `field_start_timestamp` |
| `0x044` | `field_period_ticks` |
| `0x048` | `cpu_prepare_start_timestamp` |
| `0x04c` | `cpu_prepare_end_timestamp` |
| `0x050` | `transfer_start_timestamp` |
| `0x054` | `transfer_end_timestamp` |
| `0x058` | `submission_timestamp` |
| `0x05c` | `draw_end_timestamp` |
| `0x060` | `draw_end_timestamp_reliable` |
| `0x064` | `draw_end_margin_ticks` |
| `0x068` | `draw_end_margin_percent_x100` |
| `0x06c` | `total_frame_margin_ticks` |
| `0x070` | `total_frame_margin_percent_x100` |
| `0x074` | `timer_wrapped` |
| `0x078` | `timer_divisor` |
| `0x07c` | `timer_calibration_field_ticks` |
| `0x080` | `texture_bytes_copied` |
| `0x084` | `copy_count` |
| `0x088` | `copy_ticks` |
| `0x08c` | `cart_texture_source_valid` |
| `0x090` | `vdp1_texture_destination_valid` |
| `0x094` | `cart_to_vdp1_path_valid` |
| `0x098` | `cram_writes` |
| `0x09c` | `cartridge_read_bytes` |
| `0x0a0` | `missed_fields` |
| `0x0a4` | `late_command_lists` |
| `0x0a8` | `skipped_fields` |
| `0x0ac` | `repeated_fields` |
| `0x0b0` | `canary_state` |
| `0x0b4` | `asset_failures` |
| `0x0b8` | `copy_path_failures` |
| `0x0bc` | `failure_reason` |
| `0x0c0` | `overload_expected` |
| `0x0c4` | `overload_tripped` |
| `0x0c8` | `representative_workload_tile_draw_high_water` |
| `0x0cc` | `peak_workload_tile_draw_high_water` |
| `0x0d0` | `soak_target_fields` |
| `0x0d4` | `soak_elapsed_fields` |
| `0x0d8` | `soak_workload_fields` |
| `0x0dc` | `soak_block_fields` |
| `0x0e0` | `soak_requested_workload_high_water` |
| `0x0e4` | `soak_submitted_workload_high_water` |
| `0x0e8` | `soak_cpu_ticks_high_water` |
| `0x0ec` | `soak_transfer_ticks_high_water` |
| `0x0f0` | `soak_min_draw_margin_ticks` |
| `0x0f4` | `soak_min_draw_margin_percent_x100` |
| `0x0f8` | `soak_missed_fields` |
| `0x0fc` | `soak_late_lists` |
| `0x100` | `soak_skipped_fields` |
| `0x104` | `soak_repeated_fields` |
| `0x108` | `soak_canary_failures` |
| `0x10c` | `soak_asset_failures` |
| `0x110` | `soak_copy_path_failures` |
| `0x114` | `summary_checksum` |
| `0x118` | `complete` |
| `0x11c` | representative result (112 bytes) |
| `0x18c` | peak-909 result (112 bytes) |
| `0x1fc` | overload result (112 bytes) |
| `0x26c` | `canary_end` |

Each mode result uses these relative offsets:

| Offset | Field |
| ---: | --- |
| `+0x00` | `workload_tile_draw_high_water` |
| `+0x04` | `submitted_workload_draw_high_water` |
| `+0x08` | `cpu_prepare_ticks_high_water` |
| `+0x0c` | `texture_bytes_high_water` |
| `+0x10` | `copy_count_high_water` |
| `+0x14` | `copy_ticks_high_water` |
| `+0x18` | `cart_read_bytes_high_water` |
| `+0x1c` | `missed_fields` |
| `+0x20` | `late_lists` |
| `+0x24` | `detector_tripped` |
| `+0x28` | `min_draw_margin_ticks` |
| `+0x2c` | `min_draw_margin_percent_x100` |
| `+0x30` | census `requested_workload_tile_draws` |
| `+0x34` | census `submitted_workload_draw_calls` |
| `+0x38` | census `stored_nonzero_slots` |
| `+0x3c` | census `reachable_table_entries` |
| `+0x40` | census `workload_tile_draw_commands` |
| `+0x44` | census `auxiliary_draw_commands` |
| `+0x48` | census `sgl_scaled_sprite_sentinel_draw_commands` |
| `+0x4c` | census `total_reachable_draw_commands` |
| `+0x50` | census `reachable_state_commands` |
| `+0x54` | census `reachable_skipped_commands` |
| `+0x58` | census `terminator_present` |
| `+0x5c` | census `invalid_link` |
| `+0x60` | census `loop_detected` |
| `+0x64` | census `traversal_failure` |
| `+0x68` | census `premature_end` |
| `+0x6c` | census `table_truncated` |

The FRC runs at the recorded divisor 32. `field_period_ticks` is calibrated
from consecutive NTSC V-blank timestamps. `draw_end_timestamp` is the first
Probe-only observation in the SCU sprite-drawing-finished interrupt, not a
next-field EDSR inference. Draw margin is one measured field period minus the
draw-end offset from that draw field's start. Total-pipeline margin uses two
field periods from CPU-preparation start through draw end. Percentages are
hundredths of one percent (`1500` means 15.00%).

The command census runs only in the separate precheck validation frames. It
reports AvP workload tile draws and their submitted Jo calls separately from
the production SGL 8x1 scaled-sprite sentinel (`CMDCTRL 0x0501`, texture
source `0x07ff00`). Total reachable hardware draws include both. Reachable
state commands, the terminator, total reachable entries, and stored nonzero
slots are distinct measurements; 567 and 909 are never total-table counts.

The 36,000-field soak has no overlay, excludes overload, and measures duration
from the independent VBlank field clock. `soak_workload_fields` separately
counts completed submissions and is never substituted for elapsed fields.
Representative and peak alternate in fixed 60-elapsed-field blocks, and the
summary appears only after field 36,000. Emulator timings validate
instrumentation only; physical telemetry alone can satisfy the 15-percent
condition.
