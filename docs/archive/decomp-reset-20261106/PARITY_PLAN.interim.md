# AvP Saturn plan

Decomp campaign, set by the owner 2026-11-06; see AGENTS.md. Old plan: docs/archive/decomp-reset-20261106/PARITY_PLAN.old.md.

1. **First gate (go or no-go):** reachable size and functions with computed jumps; SH-2 -O2 size per 68000 byte on at least 100 lifted functions, against 2 MB work RAM + 4 MB cart with per-round CD overlays; SH-2 cycles for a busy tick, MODELLED unless cycle-counted.
2. **Scaffold:** lifter for all reachable code, flat big-endian work RAM at original offsets, cooperative tasks on real stacks or state machines.
3. **Hardware layer:** object list to VDP1, scroll to VDP2, palette to CRAM, sound command to SCSP/CDDA. Reuse tile, palette, AVT2 and memory work.
4. **Decomp:** readable C lanes, hottest and most-called first, behaviour gate per function.
5. **First playable:** Predator Warrior, Round 1 start to boss, in emulator with a pad; then a real-Saturn package with a 4 MB cart.
