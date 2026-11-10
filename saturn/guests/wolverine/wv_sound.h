/* Wolverine's own sounds (lane wv-sounds). The clips come from Marvel Super Heroes vs. Street Fighter (tools/wolverine/wv_sound.py renders them from the user's own ROM set
 * through MAME and tools/wolverine/wv_audio.py puts them into the stage sound packs of the Wolverine stage files); nothing here carries sample data.
 *
 * A Wolverine sound is an ordinary AvP sound command in the unused range WV_CMD_BASE..: the stage pack has a row for it (priority, channel, level, clip), so the stock
 * player (saturn/audio/sat_audio.c) plays it with the same channel and priority rules as the game's own sounds. wv_sfx() sends one the way the game's sender does,
 * through the sound mailbox, so it costs no state, no low work RAM and no change to sat_audio.c.
 *
 * Without the sound assets (a build with no wv_sound/ in the guest assets) the packs have no row for these commands and wv_sfx() is a no-op. It is safe to call from
 * the game's task, once per sound; at most 3 per video frame are kept by the player (the pending ring holds 4 and the game's own sender uses one). */
#ifndef WV_SOUND_H
#define WV_SOUND_H

#define WV_CMD_BASE 0x2c0    /* AvP driver table 0x276..0x2ff are null entries: nothing else sends them */

/* ids; tools/wolverine/wv_sound.py SOUNDS has the same list (tests/test_wolverine_sound.py checks the two agree) */
enum {
    WV_SFX_SELECT = 0,       /* character select: his shout when he is picked (MSHvSF 0x21a); in the front end file only */
    WV_SFX_INTRO,            /* round entrance: "Let's go, bub." (0x207) */
    WV_SFX_CLAW_L,           /* claw swing, light (0x124) */
    WV_SFX_CLAW_M,           /* claw swing, medium (0x125) */
    WV_SFX_CLAW_H,           /* claw swing, heavy (0x126) */
    WV_SFX_ATK_A,            /* attack shout, short "huh" (0x20a) */
    WV_SFX_ATK_B,            /* attack shout "yeah" (0x20b) */
    WV_SFX_ATK_D,            /* attack shout "ha" (0x20d) */
    WV_SFX_ATK_H,            /* heavy attack shout (0x209) */
    WV_SFX_HURT_A,           /* hurt voice (0x203) */
    WV_SFX_HURT_B,           /* hurt voice, short (0x202) */
    WV_SFX_KO,               /* knocked out: his scream (0x200) */
    WV_SFX_TORNADO,          /* "Tornado Claw!" (0x204) */
    WV_SFX_BERSERKER,        /* "Berserker Barrage!" (0x206) */
    WV_SFX_CLAW_HIT_L,       /* claw hits an enemy, light, sharp (MSHvSF 0x10e) */
    WV_SFX_CLAW_HIT_H,       /* claw hits an enemy, heavy (0x243) */
    WV_SFX_BERSERKER_GRUNT,  /* a grunt per Berserker contact (0x20c) */
    WV_SFX_COUNT
};

/* Play sound `id` (WV_SFX_*) centred; wv_sfx_pan() with a pan 0..0x20 (0x10 centre, 0 left), the game's own pan scale. Unknown ids are ignored. */
void wv_sfx(int id);
void wv_sfx_pan(int id, int pan);
#endif
