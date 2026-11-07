/* Home mode (SAT_HOME, new modes only; the arcade build has none of this): title menu, options, pause. Runs on the master between task walks with the game held.
   While held the vblank runs only pad, picture and sound (kernel.c), so no game state moves. Text is the game's own scroll 1 font, drawn by saturn/gfx. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
extern u8 RAMB[];
extern u32 sat_pad_raw;
extern u32 sat_vblanks_now(void);
extern void sat_home_set(int block_off, int value);
extern int sat_home_get(int block_off);
extern void sat_home_restart(void);
volatile int sat_home_hold;
volatile int sat_home_mode;            /* 0 off, 1 text over the held picture, 2 text alone */
char sat_home_text[28][44];
/* Where the menus are, read by the bot over MCP. */
volatile u32 sat_home_screen;          /* 0 none, 1 home, 2 options, 3 pause */
volatile u32 sat_home_cursor;
#define G(a) RAMB[(a) - 0xff0000u]
#define P_UP 0x1000u
#define P_DOWN 0x2000u
#define P_LEFT 0x4000u
#define P_RIGHT 0x8000u
#define P_START 0x0800u
#define P_A 0x0400u
#define P_B 0x0100u
#define P_C 0x0200u
#define P_COIN 0x0040u
extern volatile u32 sat_duel_on;
u32 sat_home_inject;
#define inject sat_home_inject
static u32 coin_on, coin_gap;
u32 sat_home_prev = 0xffff;
#define prev sat_home_prev

static int shown;
#define IN_ATTRACT (G(0xff81b0) != 0)
#define PAUSE_OK (!IN_ATTRACT && G(0xff8001) == 2 && G(0xff8380) != 0 && G(0xff8384) != 4)

/* Second pad: idle while held; Start only as the duel's start path sends it, or to join or continue in play. */
u32 sat_home_pad2(u32 raw)
{
    if (sat_home_hold) return 0xffff;
    if (inject && sat_duel_on && G(0xff818c) >= 2) return (inject & 4) ? raw | P_START : raw & ~P_START;
    if (IN_ATTRACT) return raw | P_START;
    return raw;
}
/* Pad word as the game sees it (pad.c): idle while held; Start belongs to these menus where they own it. */
u32 sat_home_pad(u32 raw)
{
    u32 cred = G(0xff818c);
    if (sat_home_hold) return 0xffff;
    raw |= P_COIN;
    /* No coin to insert at home: the game's own credit path, through its own coin line, keeps a credit ready whenever one is wanted. Free play's own coinage is not used: its paths are outside the census the stage files keep ROM for. */
    if (coin_gap) coin_gap--;
    if (coin_on) { coin_on--; raw &= ~P_COIN; }
    else if (!coin_gap && cred < (sat_duel_on ? 2u : 1u) && (inject || !IN_ATTRACT)) { coin_on = 6; coin_gap = 40; raw &= ~P_COIN; }
    if (inject) {
        if (cred) { inject--; return (inject & 4) ? raw | P_START : raw & ~P_START; }
        return raw | P_START;
    }
    if (IN_ATTRACT || PAUSE_OK) return raw | P_START;
    return raw;
}

void sat_home_clear(void) { int r, c; for (r = 0; r < 28; r++) for (c = 0; c < 44; c++) sat_home_text[r][c] = 0; }
/* High bit: highlight colour. */
void sat_home_put(int r, int c, const char *s, int hi) { for (; *s && c < 44; s++, c++) sat_home_text[r][c] = (char)(*s == ' ' ? 1 : (*s | (hi ? 0x80 : 0))); }
void sat_home_centre(int r, const char *s, int hi) { int n = 0; while (s[n]) n++; sat_home_put(r, (44 - n) / 2, s, hi); }

void sat_home_frame(void) { u32 v = sat_vblanks_now(); while (sat_vblanks_now() == v) ; }
u32 sat_home_edges(void) { u32 raw = sat_pad_raw & 0xffff, e = prev & ~raw; prev = raw; return e; }

int sat_home_list(int screen, int row0, const char *const *items, int n, int start, u32 idle)
{
    int cur = start, i;
    u32 t = 0;
    sat_home_screen = (u32)screen;
    for (;;) {
        u32 e;
        for (i = 0; i < n; i++) sat_home_centre(row0 + i * 2, items[i], i == cur);
        sat_home_cursor = (u32)cur;
        sat_home_frame();
        e = sat_home_edges();
        if (e) t = 0;
        if (idle && ++t > idle) return -1;
        if (e & P_UP) cur = cur ? cur - 1 : n - 1;
        if (e & P_DOWN) cur = cur + 1 < n ? cur + 1 : 0;
        if (e & (P_START | P_A | P_C)) return cur;
    }
}

extern void sat_home_menu(void);

static void pause_menu(void)
{
    static const char *const items[] = { "RESUME", "QUIT TO TITLE" };
    int pick;
    sat_home_hold = 1;
    sat_home_clear();
    { int r, c; for (r = 7; r < 17; r++) for (c = 12; c < 32; c++) sat_home_text[r][c] = 1; }
    sat_home_centre(9, "PAUSE", 1);
    sat_home_mode = 1;
    prev = sat_pad_raw & 0xffff;
    pick = sat_home_list(3, 13, items, 2, 0, 0);
    sat_home_screen = 0;
    sat_home_mode = 0;
    sat_home_hold = 0;
    if (pick == 1) sat_home_restart();
}

/* Once per task walk. */
void sat_home_poll(void)
{
    u32 raw = sat_pad_raw & 0xffff, e = prev & ~raw;
    prev = raw;
    if (inject && !IN_ATTRACT) inject = 0;
    if (inject) return;
    if (IN_ATTRACT) {
        /* First sight once the boot warning has gone, then on Start. */
        if ((!shown && G(0xff8001) == 8) || (e & P_START)) { shown = 1; sat_home_menu(); }
    } else if ((e & P_START) && PAUSE_OK)
        pause_menu();
}
