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
#define HOME_IDLE 1800u                /* 30 s on the title menu, then the attract runs */
extern volatile u32 sat_duel_on;
static u32 inject;
static u32 prev = 0xffff;
static int shown;
#define IN_ATTRACT (G(0xff81b0) != 0)
#define PAUSE_OK (!IN_ATTRACT && G(0xff8001) == 2 && G(0xff8380) != 0 && G(0xff8384) != 4)

/* Second pad: idle while held; Start only as the duel's start path sends it, or to join or continue in play. */
u32 sat_home_pad2(u32 raw)
{
    if (sat_home_hold) return 0xffff;
    if (inject && sat_duel_on) return (inject & 4) ? raw | P_START : raw & ~P_START;
    if (IN_ATTRACT) return raw | P_START;
    return raw;
}
/* Pad word as the game sees it (pad.c): idle while held; Start belongs to these menus where they own it. */
u32 sat_home_pad(u32 raw)
{
    if (sat_home_hold) return 0xffff;
    if (inject) { inject--; return (inject & 4) ? raw | P_START : raw & ~P_START; }
    if (IN_ATTRACT || PAUSE_OK) return raw | P_START;
    return raw;
}

static void clear(void) { int r, c; for (r = 0; r < 28; r++) for (c = 0; c < 44; c++) sat_home_text[r][c] = 0; }
/* High bit: highlight colour. */
static void put(int r, int c, const char *s, int hi) { for (; *s && c < 44; s++, c++) sat_home_text[r][c] = (char)(*s == ' ' ? 1 : (*s | (hi ? 0x80 : 0))); }
static void centre(int r, const char *s, int hi) { int n = 0; while (s[n]) n++; put(r, (44 - n) / 2, s, hi); }

static void frame(void) { u32 v = sat_vblanks_now(); while (sat_vblanks_now() == v) ; }
static u32 edges(void) { u32 raw = sat_pad_raw & 0xffff, e = prev & ~raw; prev = raw; return e; }

static int menu_list(int screen, int row0, const char *const *items, int n, int start, u32 idle)
{
    int cur = start, i;
    u32 t = 0;
    sat_home_screen = (u32)screen;
    for (;;) {
        u32 e;
        for (i = 0; i < n; i++) centre(row0 + i * 2, items[i], i == cur);
        sat_home_cursor = (u32)cur;
        frame();
        e = edges();
        if (e) t = 0;
        if (idle && ++t > idle) return -1;
        if (e & P_UP) cur = cur ? cur - 1 : n - 1;
        if (e & P_DOWN) cur = cur + 1 < n ? cur + 1 : 0;
        if (e & (P_START | P_A | P_C)) return cur;
    }
}

/* Player settings: the game's own bytes in its settings block, both copies, and the RAM byte its boot code loads them to. */
typedef struct { const char *label; u8 off; u16 ram; u8 n; const char *const *names; } Opt;
static const char *const on_off[] = { "OFF", "ON" };
static const char *const sound[] = { "MONAURAL", "STEREO" };
/* The game's own eight extend rules (its text table at 0xdd60; index 0 prints nothing). */
static const char *const extend[] = { "NONE", "100000 ONLY", "400000 ONLY", "1000000 ONLY", "100000 400000", "400000 500000", "800000 600000", "1200000 1000000" };
static const Opt opts[] = {
    { "DIFFICULTY", 0x10, 0x81cf, 8, 0 },
    { "EXTEND", 0x11, 0x81d0, 8, extend },
    { "CONTINUE", 0x01, 0x81be, 2, on_off },
    { "SOUND", 0x04, 0x81d2, 2, sound },
    { "DEMO SOUND", 0x03, 0x81ad, 2, on_off },
};
#define OPTS (int)(sizeof opts / sizeof opts[0])
static void options(void)
{
    int cur = 0, i;
    sat_home_screen = 2;
    for (;;) {
        u32 e;
        clear();
        centre(3, "OPTIONS", 1);
        for (i = 0; i < OPTS; i++) {
            const Opt *o = &opts[i];
            int v = sat_home_get(o->off);
            char num[2];
            num[0] = (char)('1' + v); num[1] = 0;
            put(8 + i * 2, 8, o->label, i == cur);
            put(8 + i * 2, 22, o->names ? o->names[v] : num, i == cur);
        }
        centre(8 + OPTS * 2 + 1, "EXIT", cur == OPTS);
        sat_home_cursor = (u32)cur;
        frame();
        e = edges();
        if (e & P_B) return;
        if (e & P_UP) cur = cur ? cur - 1 : OPTS;
        if (e & P_DOWN) cur = cur < OPTS ? cur + 1 : 0;
        if (cur == OPTS) { if (e & (P_START | P_A | P_C)) return; continue; }
        if (e & (P_LEFT | P_RIGHT | P_A | P_C)) {
            const Opt *o = &opts[cur];
            int v = sat_home_get(o->off);
            v = (e & P_LEFT) ? (v ? v - 1 : o->n - 1) : (v + 1 < o->n ? v + 1 : 0);
            sat_home_set(o->off, v);
            RAMB[o->ram] = (u8)v;
        }
    }
}

static void home_menu(void)
{
#ifdef SAT_DUEL_MENU   /* until the duel is finished */
    static const char *const items[] = { "START GAME", "OPTIONS", "DUEL" };
#define HOME_ITEMS 3
#else
    static const char *const items[] = { "START GAME", "OPTIONS" };
#define HOME_ITEMS 2
#endif
    int pick = 0;
    sat_home_hold = 1;
    sat_home_mode = 2;
    prev = sat_pad_raw & 0xffff;
    for (;;) {
        clear();
        centre(5, "ALIEN VS PREDATOR", 1);
        pick = menu_list(1, 12, items, HOME_ITEMS, pick < 0 ? 0 : pick, HOME_IDLE);
        if (pick != 1) break;
        options();
    }
    sat_home_screen = 0;
    sat_home_mode = 0;
    sat_home_hold = 0;
    sat_duel_on = pick == 2;
    if (pick == 0 || pick == 2) inject = 900;       /* the game's own start path; ends when the game leaves attract */
}

static void pause_menu(void)
{
    static const char *const items[] = { "RESUME", "QUIT TO TITLE" };
    int pick;
    sat_home_hold = 1;
    clear();
    { int r, c; for (r = 7; r < 17; r++) for (c = 12; c < 32; c++) sat_home_text[r][c] = 1; }
    centre(9, "PAUSE", 1);
    sat_home_mode = 1;
    prev = sat_pad_raw & 0xffff;
    pick = menu_list(3, 13, items, 2, 0, 0);
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
        if ((!shown && G(0xff8001) == 8) || (e & P_START)) { shown = 1; home_menu(); }
    } else if ((e & P_START) && PAUSE_OK)
        pause_menu();
}
