/* AvP Saturn graphics library (backlog items 15, 16).
 *
 * Reads the game's own state and draws it by concept. Nothing here emulates a register or a CPS renderer:
 *   work RAM, RAMB          display shadows at 0xff8000 + n, scroll positions at 0xffee1a..
 *   object RAM, PAGE[0x70]  the object list at 0x708000
 *   graphics RAM, PAGE[0x90..0x92]  tile maps, row scroll, palette
 * Sprites go to VDP1, three tile layers to VDP2 NBG0..2, four palette pages to CRAM.
 *
 * Call sat_gfx_frame() once per game vblank, at the point the game's level 2 IRQ (0xe0e) would start, before the IRQ
 * body runs: the body moves the next-frame scroll values into the words read here. Layers read at vblank N show from N, the sprite
 * list read at N shows from N+1 (VDP1 plots it during that field). The board has the same one field gap between them (MAME: list from
 * entry N, layers from entry N+1, both in the still at entry N+2).
 */
#ifndef SAT_GFX_H
#define SAT_GFX_H

#define SAT_GFX_SCREEN_W 352
#define SAT_GFX_SCREEN_H 224
#ifndef SAT_VDP1_HW_ERASE
#define SAT_VDP1_HW_ERASE 0
#endif
/* Experiment only; disabled unless explicitly selected in KERNEL_CFLAGS.
 * Manual V-blank erase covers the first 160 rows; the normal clear polygon
 * covers the rest. See docs/notes/VDP1_HARDWARE_ERASE.md before a console run. */
#if SAT_VDP1_HW_ERASE
#if SAT_GFX_SCREEN_W != 352 || SAT_GFX_SCREEN_H != 224
#error Recalculate the VDP1 hardware erase budget for this display mode
#endif
#define SAT_VDP1_ERASE_ROWS 160
/* OUT entry calls this with master IPL 15 so IN cannot rearm it midway. */
void sat_gfx_vblank_out(void);
/* Call with master interrupts masked before a long GFS/CD load. A zero return
 * leaves TVMR untouched: restore interrupts and retry the load later. */
int sat_gfx_erase_suspend(void);
extern unsigned long sat_gfx_erase_reduced, sat_gfx_erase_full, sat_gfx_erase_canceled;
#endif
/* SAT_GFX_FIT, a crop still choice for the owner: 0 the 1:1 centre crop. 1 scale the 384 wide picture to 352: VDP2 zoom on NBG0 and NBG1, scaled VDP1 sprites, HUD flush. 2 the crop, HUD flush. */
#ifndef SAT_GFX_FIT
#define SAT_GFX_FIT 1   /* scaled: the owner's default, 2026-11-07 */
#endif
#if SAT_GFX_FIT == 3 /* test build: A and B on one image, switched at run time for a same-frame comparison */
extern volatile int sat_fit_scale;
#define SAT_FIT_ON (*(volatile int *)((unsigned long)&sat_fit_scale | 0x20000000UL))
#define SAT_GFX_CROP_X (SAT_FIT_ON ? 0 : 16)
#define SAT_GFX_SRC_W (SAT_FIT_ON ? 384 : 352)
#elif SAT_GFX_FIT == 1
#define SAT_GFX_CROP_X 0
#define SAT_GFX_SRC_W 384
#else
#define SAT_GFX_CROP_X 16 /* 1:1 centre crop of the 384 wide picture */
#define SAT_GFX_SRC_W 352
#endif
#define SAT_GFX_PAGES 4
#define SAT_GFX_BANKS_PER_PAGE 32
/* Two 32 KB tables. Keep the existing four-bar reserve even without SAT_READOUT.
 * SAT_VLOG adds sixteen plot-serial polygons after the sprites; they need their
 * own reserve or a full list overwrites the other table (or texture RAM). */
#ifdef SAT_VLOG
#define SAT_GFX_MAX_COMMANDS (1016 - 16)
#else
#define SAT_GFX_MAX_COMMANDS 1016
#endif
#define SAT_GFX_SPRITE_SLOTS 3584 /* 448 KB of 128 byte textures */
/* Optional previous-list slot hints. Two bytes per entry in high work RAM;
 * zero keeps the original lookup and allocates nothing. A hint is accepted
 * only when the live slot still holds the requested tile. Size this from the
 * target link, then measure whole-frame tails before enabling a release. */
#ifndef SAT_GFX_SLOT_HINTS
#define SAT_GFX_SLOT_HINTS 0
#endif
#if SAT_GFX_SLOT_HINTS < 0 || SAT_GFX_SLOT_HINTS > 1024
#error SAT_GFX_SLOT_HINTS must be between 0 and 1024
#endif
#ifdef SAT_GFX_SLOT_HINT_STATS
#if SAT_GFX_SLOT_HINTS == 0
#error SAT_GFX_SLOT_HINT_STATS requires SAT_GFX_SLOT_HINTS
#endif
typedef struct
{
    unsigned long queries, hits, fallbacks, beyond_limit;
} SatGfxSlotHintStats;
extern SatGfxSlotHintStats sat_gfx_slot_hint_stats;
#endif
/* Experimental vertical pairs. 0 keeps the tile path; 16 or 32 reserves that
 * many 16 x 32 textures within the existing sprite VRAM. No pack grows.
 * Each pair reuses two ordinary slots and their existing SlotRec metadata. */
#ifndef SAT_GFX_SPRITE_PAIRS
#define SAT_GFX_SPRITE_PAIRS 0
#endif
#ifndef SAT_GFX_PAIR_REUSE
#define SAT_GFX_PAIR_REUSE 0 /* pair ordinary slots only when already contiguous; no VRAM reservation */
#endif
#if SAT_GFX_PAIR_REUSE != 0 && SAT_GFX_PAIR_REUSE != 1
#error SAT_GFX_PAIR_REUSE must be 0 or 1
#endif
#if SAT_GFX_PAIR_REUSE && SAT_GFX_SPRITE_PAIRS
#error Select either SAT_GFX_PAIR_REUSE or SAT_GFX_SPRITE_PAIRS
#endif
#if (SAT_GFX_PAIR_REUSE || SAT_GFX_SPRITE_PAIRS) && (defined(SAT_KEYLOG) || defined(SAT_READOUT) || defined(SAT_ABL))
#error Disable sprite pair experiments for SAT_KEYLOG, SAT_READOUT and SAT_ABL captures
#endif
#if SAT_GFX_SPRITE_PAIRS != 0 && SAT_GFX_SPRITE_PAIRS != 16 && SAT_GFX_SPRITE_PAIRS != 32
#error SAT_GFX_SPRITE_PAIRS must be 0, 16 or 32
#endif
/* Cold pair creation competes with normal uploads. Bound it independently of
 * hot hits: default two pairs, at most 512 extra texture bytes per build. */
#ifndef SAT_GFX_PAIR_UPLOAD_BUDGET
#define SAT_GFX_PAIR_UPLOAD_BUDGET 2
#endif
#if SAT_GFX_SPRITE_PAIRS && (SAT_GFX_PAIR_UPLOAD_BUDGET < 1 || SAT_GFX_PAIR_UPLOAD_BUDGET > SAT_GFX_SPRITE_PAIRS)
#error SAT_GFX_PAIR_UPLOAD_BUDGET must be between 1 and SAT_GFX_SPRITE_PAIRS
#endif
#if (SAT_GFX_PAIR_REUSE || SAT_GFX_SPRITE_PAIRS) && defined(SAT_GFX_PAIR_STATS)
/* Cumulative, cleared by init: successful hot hits, uploads, fallbacks and
 * commands saved. Diagnostic counters only; four target longs = 16 bytes. */
extern unsigned long sat_gfx_pair_hits, sat_gfx_pair_uploads;
extern unsigned long sat_gfx_pair_fallbacks, sat_gfx_pair_saved;
#endif
#ifdef SAT_HOME
#define SAT_GFX_S1_SLOTS 768 /* 0x18000-0x1e000; the menu layer (NBG3) map and its font take the rest */
#define SAT_GFX_HOME_FONT 880 /* font cells at 0x1ee00, after the menu map (0x1e000, 28 rows); panel cell at +58 */
#else
#define SAT_GFX_S1_SLOTS 992 /* 4 stay clear */
#endif
#define SAT_GFX_S2_SLOTS 1024
#define SAT_GFX_S3_SLOTS 512

typedef struct
{
    unsigned long frames;
    unsigned short objects;           /* objects in this frame's list */
    unsigned short commands;          /* VDP1 sprite commands this frame */
    unsigned short commands_peak;
    unsigned short uploads;           /* sprite textures copied this frame */
    unsigned short uploads_peak;
    unsigned short sprite_slots_used; /* distinct sprite textures this frame */
    unsigned short sprite_slots_peak;
    unsigned short layer_uploads;     /* layer tiles copied this frame */
    unsigned short layer_writes;      /* tile map and row scroll words changed this frame */
    unsigned short layer_slots_peak[3];
    unsigned short colours_written;
    unsigned short top_bank;          /* highest palette bank drawn this frame, proves the path above 16 */
    unsigned long missing;            /* tile not in the pack: drawn as nothing */
    unsigned long refused_commands;   /* capacity refusal: over the command table */
    unsigned long refused_sprite;     /* capacity refusal: every texture slot is in use this frame */
    unsigned long refused_layer;      /* capacity refusal: every layer slot is in use this frame */
    unsigned long refused_bank;       /* capacity refusal: palette reference outside the CRAM map */
    unsigned long nonmonotone;        /* priority cases one sprite level cannot express */
} SatGfxStats;

extern SatGfxStats sat_gfx_stats;

/* pack: SGP1 tile pack, tools/satgfx_pack.py. Aligned to 4, stays readable for the life of the library.
 * Returns 1, or 0 for a bad pack (nothing is touched). */
int sat_gfx_init(const void *pack);

/* A new pack between rounds, with the slave idle: same keys mean same pixels, so tiles already in VRAM stay. Returns 1, or 0 for a bad pack. */
int sat_gfx_swap_pack(const void *pack);
void sat_gfx_display(int on);

/* Draw the current game state: snapshot then draw. */
void sat_gfx_frame(void);

/* The two halves, for two CPUs. sat_gfx_snapshot copies what drawing needs out of game state and runs on the game's CPU, with the buffer
 * not in use by sat_gfx_draw. sat_gfx_draw reads only that buffer and owns the video chips, caches and stats. The caller does the handoff. */
/* The same snapshot in two halves for the two-CPU path: _begin copies registers, palette, rows and objects; the caller hands the picture to the slave and wakes it;
   _layers then copies the layer cells while the slave builds the sprite commands. The slave waits for _layers to finish before it reads a layer cell. */
void sat_gfx_snapshot_begin(void);
void sat_gfx_snapshot_layers(void);
/* Both halves in a row: the single-CPU path (standalone, host fixtures). */
#define sat_gfx_snapshot() (sat_gfx_snapshot_begin(), sat_gfx_snapshot_layers())
void sat_gfx_draw(void);

/* CRAM bank of a CPS palette page and bank, or -1 when outside the map: the capacity refusal. */
int sat_gfx_bank(int page, int bank);

/* Saturn colour for a CPS colour word: brightness applied as the board does. */
unsigned short sat_gfx_colour(unsigned short cps);

#endif
