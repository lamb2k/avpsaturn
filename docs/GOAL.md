# Project goal

Produce a faithful, native NTSC Sega Saturn port of MAME set `avspu`, `Alien vs. Predator (USA 940520)`, using the 32 Mbit expansion-RAM cartridge.

The fastest acceptable proof is a gameplay-valid physical-hardware slice, not a title/menu demonstration. It must preserve deterministic input-visible behavior, collision/hit response, animation cadence/content, stage layers/priority/palette, audio event timing, 352x224 framing contract, load ownership, and input/frame timing.

The authoritative architecture is `docs/research/CPS2_TO_SATURN_RESET.md`: offline ROM extraction, sparse traceable original data, selective lifting of bounded 68000 behavior, native Saturn subsystems, and differential validation against MAME 0.289.

The project explicitly does not require or authorize a general CPS-2 emulator, whole-program decompilation/recompiler, generalized Capcom porting engine, or captured gameplay substitution before the first slice.

Current status and active body: `project_state.yaml` and the task card it names.
