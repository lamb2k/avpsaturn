# AvP audio command path (lane 3)

Tiers: **source** (read from code), **unicorn-differential** (`learn_unit.py`), **MAME** (`learn_run_probe.py`, MAME 0.289). Nothing here ran on a Saturn or a CPS2 board.
Sound names stay UNKNOWN: numbers and owners are evidence, what a sound "is" is not. Private dumps: `E:\AvP\learning\audio` and `mame\audio_base`, `mame\audio_ff`.

## The path

```
gameplay -> sound helper (0x1a62..0x3a88) or music request (0x3bdc)
         -> audio_enqueue (0x1916) -> ring ff0a88, 64 x 16 bytes
vblank   -> audio_vblank_tick (0x1870) -> at most one entry to the Z80 mailbox
Z80 IRQ, 250 Hz -> copy mailbox to its ring f100 (16 entries), mark ready
Z80 main -> one command per IRQ; sequencer on every 4th IRQ -> QSound registers
```

### 68000 side (source, unicorn-differential)

- **Ring:** base ff0a88, head ff801e (send), tail ff8020 (fill), mask 0x3f0. One slot stays empty: **63 usable**.
- **Full:** `audio_enqueue_always` returns nonzero and the command is lost. Callers restore registers without testing it.
- **Muted demo:** `audio_enqueue` drops silently when ff81ad (saved demo-sound option) is 0 and ff81b0 (attract) is set.
  Control sends call 0x1922 directly, so they bypass this.
- **Entry:** three longs: sound, voice, sweep.

| Long | Bytes | Z80 mailbox | Meaning |
| --- | --- | --- | --- |
| sound | high word | c003, c004 | Control parameter |
| sound | low word | c000, c001 | Sound number, or 0xff + control code |
| voice | byte 1 | c006 | Pan mode, low 3 bits |
| voice | byte 2 | c007 | Pan 0..0x20, 0x10 centre |
| voice | byte 3 | c008 | Pan span |
| sweep | low word | c009, c00a | Pan rate |
| sweep | high word | c00b, c00c | Second rate (modes 5, 6, 7) |

Voice byte 0 and the last 4 entry bytes never cross.

- **Handshake:** c00f (68000 61801f). Z80 writes 0xff after copying; the send writes 0.
- **Helpers:** 199 entries (`tools/learn_audio_helpers.py`, 0 faults). Shapes: 74 alternating with pan, 1 alternating, 62 fixed with pan, 62 fixed. 194 distinct first numbers. A few also touch actor fields, so only the 5 gated helpers count as reconstructed; the rest are a census.
- **Alternating pairs** use neighbouring channels (0x3d on 13, 0x108 on 14; 0x4d on 9, 0x118 on 10), so a repeat does not cut the last one.
- **Pan:** x minus camera, clamped to 0..0x17f, through a 48-step curve. `audio_pan_from_screen_x` states it as a formula, gated against the ROM table.
- **Music request:** see `audio_music_request`. Request high byte negative: fade out, set ff837c delay; route code polls it. 0x3bdc has 58 call sites.

### Z80 side (source; dispatcher and 72 commands also witnessed in retained MAME ledgers)

Dispatch at 0x1bd reads the header byte at the table entry for `command mod 0x38d`.

| Class | Test | Table entries | Behaviour |
| --- | --- | --- | --- |
| Null | Pointer 0 | 439 | Ignored |
| Music | Header 0 | 26 | 0x48d: resets tempo and fade, loads tracks f600 + 0x40n, no priority. A zero track offset stops that track |
| SFX | Header 1..0x7f = priority | 444 | 0x218: per channel f200 + 0x40n |
| Direct sample | Header >= 0x80 | **0** | 0x53a path, slots fa00, QSound ADPCM registers. No table entry reaches it |
| Control | Number 0xff, code | 12 valid | 0x7cf |

**SFX rules**
- Each of the 16 channels is judged alone: a new sound takes a channel when priority >= the occupant's (0x23a). Otherwise that channel is skipped, and the rest of the sound still plays.
- Taking a channel wipes its state; no queueing and no later retry.
- At end (0xf19) priority returns to 0 and the voice silences.
- Priorities seen: 4 (34 sounds), 5 (118), 6 (232), 7 (54), 8 (5), 15 (1: number 0x30).
- SFX live on channels 5 and 7..15 (7..15 almost entirely).

**Music vs SFX**
- A music track runs on regardless, but f020 is set when its channel holds an SFX, so its writes to the voice are suppressed. When the SFX ends the music is audible again.
- Music up to 16 tracks: 0x6, 0x7 and 0xf use all 16; so music loses notes on channels SFX occupy.

**Controls** (table 0x7e3)

| Code | Handler | Effect | Sender |
| --- | --- | --- | --- |
| 0 | 0x7ff | Stop everything, silence all | `audio_stop_all` |
| 1 | 0x813 | End all SFX channels | none found in helpers |
| 2 | 0x840 | End one SFX channel (c004) | `audio_key_off_channel` |
| 3, 4 | 0x86a, 0x87a | Clear direct-sample slots. QUIRK: 4 silences QSound voice n, not a sample slot | none found in helpers |
| 5 | 0x896 | Stop music tracks; a channel holding an SFX keeps sounding | `audio_stop_music` |
| 6, 7 | 0x8d0, 0x8f6 | Music fade in, out; no-op at rate 0 or if already going that way | `audio_control` |
| 8 | 0x921 | Tempo offset f014 | one caller |
| 9 | 0x93f | Offset f01b, read at 0x14a0 | one caller |
| a, b | 0x965, 0x96b | Set, clear f041 (mirrors pan to c005) | one caller each |
| c, d | | QUIRK: handlers 0x970/0x996 exist, but `CP 12` rejects them, and the 68000 has no callers. Fade pair f030 never starts | none |

**Stereo:** the 68000 copies ff81d2 to Z80 cffe every vblank. Zero forces pan 0x10.

## Native report: the 279 of 281

Measured from `data/reimplement13_coffee_shop_scene_parity.json`:
- The **2** closed are the load boundaries. The **279** open are **all the audio events**, frames 2030..5563, classed `BLOCKED_MISSING_SPEC` natively.
- **All 279 are `SOURCE_CLOSED` at source.** They need a native sender, not more source evidence.
- By class: 274 SFX, 3 control, 2 music.
- Most frames need nothing extra: the top 7 caller sites own 188 of 279 (67%).

| Owner family | Events | Sounds (numbers) | Evidence |
| --- | --- | --- | --- |
| Player | 82 | 0x24e (36), 0x51 (15), 0x91, 0x96 (7 each), 0x203 (5) | `oracle11_predator_player_audio.json` trigger_edges |
| Enemy | 78 | 0x3d..0x3f and 0x108..0x10a, 0x35, 0x100 | `spec02_enemy_audio_owner_program.json` |
| Projectile | 70 | 0x4d..0x4f and 0x118..0x11a; all at one site, return 0x1b86e | `spec02_projectile_audio_owner_program.json` |
| Presentation | 21 | 0x7d (16), 0x30 (5) | `spec02_presentation_...` |
| Boss | 15 | 0x82, 0x83, 0x14a, 0x14b | `spec02_boss_...` |
| Pickup | 6 | 0x6d, 0x74, 0x77, 0x139, 0x142 | `oracle11_global_audio_trigger_owners.json` |
| Encounter | 4 | 0x7, 0x1f, 0xff00 x2 | `spec02_encounter_...` |
| Route | 3 | 0x254, 0x257, 0xff07 | `spec02_route_...` |

Top sites by return address: 0x1b86e 70, 0x1a7be 26, 0x1f408 20, 0x1f4f0 20, 0x3b5a 20, 0x19854 16, 0x20bb6 16.

### Sender contract for avp-native

1. Gameplay calls one sender at the transition the ledger's `transition_guard` names (record class, type, state, substate, caller). Not on a frame number.
2. Args are `(sound, voice, sweep)`. `avsp_scene_runtime.h` `audio_event(channel, cue_id)` cannot carry pan, mode or rates, nor the priority rule's channel choice: it needs widening or a table from sound number.
3. Link `avsrc_audio.c` for ring and senders; alternating toggles and `audio_voice_with_actor_pan` are game state and live there.
4. Drain once per video frame, never per tick. Keep it through fast-forward.
5. Playback rule to reproduce on SCSP: per-channel priority >=, SFX suppresses the music track on its channel without stopping it, music class resets music state.
6. Attract gate only matters for a frontend; R7C's direct entry can ignore it.

## Fast-forward and the ring (MAME)

Both runs: retained Coffee Shop route, frames 1..5566, `tools/learn_audio_probe.lua`, summary `tools/learn_audio_ring.py`.

| | Baseline, whole route | Baseline, 5449..5559 | Forced ff81b9=1, 2800..3400 |
| --- | --- | --- | --- |
| Condition | Unmodified | Natural fast-forward | **Forced by the probe, not natural**; route input no longer matches the game |
| Ticks per frame | 1 (mostly); 3-4 in fast-forward | 3 (53), 4 (12) | 2 (303), 3 (283) |
| Enqueued | 365 | 2 | 77 |
| Max sent in a frame | 1 | 1 | 1 |
| Max backlog at frame end | 16 | 1 | 5 |
| Latency, frames | 1: 301, 2: 43, worst 16 | 1 | 1: 68, 2: 6, worst 5 |
| Left in ring at end | 0 | 0 | 0 |
| Z80 ring backlog at frame end | 0 | 0 | 0 |

Findings:
- **Drops under fast-forward: none, and not close.** Peak backlog was 16 of 63, from the deliberate stop burst at frames 1207..1222, not fast-forward.
  Filling the ring needs a sustained rate above 1 per frame; forced fast-forward averaged 0.13 enqueued per frame.
- **Delay is real but small.** In forced fast-forward the worst was 5 frames (83 ms), at a burst of 5 in one frame (frames 2802..2806). At normal speed the same kind of burst already delays.
- **Worst latency overall** is the deliberate burst from 0x3bc0, which stops music then ends channels 15..0 except 13, in 16 frames (frames 1207..1222). Sounds requested right after are delayed by up to that much; only the attract path was witnessed.
- Forced fast-forward is not a proof for every scene: ring drops need > 63 pending, which no measured condition approached. A boss-death style burst was not forced.
- `oracle11_global_audio_load_release.json` states pointers ff816e/ff8170 and base ff0bd8. The source and probe say ff801e/ff8020/ff0a88. The ledger's mechanism is right, its address arithmetic assumed a wrong a5.

## Gates

`python tools/learn_unit.py all 500` (unicorn-differential): 22 audio units with 0 bad at 500 cases; alternating units 2000 cases. `audio_voice_with_actor_pan` changes no RAM, so it is covered through `audio_alt_*`.
Sensitivity: a wrong pan constant failed `audio_alt_1aa6`; a swapped mailbox byte failed `audio_send_pending`.
Replay (MAME values, C model): `source_recon/tests/audio_ring_replay.c` fed every enqueue from both probes; send frames and tails match, given the first-ready frame as input (Z80 boot ends between frames 79 and 82).
The gate runner gained small optional hooks in `tools/learn_unit.py` for this: `setup(rom)`, extra ranges, ignore ranges, stack. Default behaviour is unchanged. Trap fixed by it: the default stack exclusion hid ff0e00..ff0f03, which overlaps the ring end and music state. Also, `merged.bin` holds wrong bytes for small pc-relative word tables not listed in cfg `tables`; `setup` writes them from opcode space.

## Left

- The other 194 helpers: a census shape only, not gated one by one. A table-driven reconstruction is the next step.
- Z80 sequencer bytecode (0xadc onward): channel programs, envelopes and pitch are not decoded; only entry, stop and priority rules are.
- Semantic names of sounds: unknown by policy.
- Native side wiring is avp-native's.
