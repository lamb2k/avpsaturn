/* Home mode, the part that need not stay in work RAM: title menu and options. Linked into the cart's cold area, read from disc at boot; only pause stays in work RAM (home.c). */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
extern u8 RAMB[];
extern u32 sat_pad_raw;
extern void sat_home_set(int block_off, int value);
extern int sat_home_get(int block_off);
extern volatile int sat_home_hold, sat_home_mode;
extern volatile u32 sat_home_screen, sat_home_cursor, sat_duel_on;
extern char sat_home_text[28][44];
extern u32 sat_home_inject, sat_home_prev;
extern void sat_home_clear(void), sat_home_frame(void);
extern void sat_home_put(int, int, const char *, int), sat_home_centre(int, const char *, int);
extern u32 sat_home_edges(void);
extern int sat_home_list(int, int, const char *const *, int, int, u32);
#define P_UP 0x1000u
#define P_DOWN 0x2000u
#define P_LEFT 0x4000u
#define P_RIGHT 0x8000u
#define P_START 0x0800u
#define P_A 0x0400u
#define P_B 0x0100u
#define P_C 0x0200u
#define HOME_IDLE 1800u                /* 30 s on the title menu, then the attract runs */
#define inject sat_home_inject
#define prev sat_home_prev
#define clear sat_home_clear
#define put sat_home_put
#define centre sat_home_centre
#define frame sat_home_frame
#define edges sat_home_edges
#define menu_list sat_home_list
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
/* Text under the game's own logo: clear cells hide the game's start and credits lines. */
static void panel(int top)
{
    int r, c;
    clear();
    for (r = top; r < 28; r++) for (c = 0; c < 44; c++) sat_home_text[r][c] = 1;
}
static void options(void)
{
    int cur = 0, i;
    sat_home_screen = 2;
    for (;;) {
        u32 e;
        panel(19);
        for (i = 0; i < OPTS; i++) {
            const Opt *o = &opts[i];
            int v = sat_home_get(o->off);
            char num[2];
            num[0] = (char)('1' + v); num[1] = 0;
            put(20 + i, 8, o->label, i == cur);
            put(20 + i, 22, o->names ? o->names[v] : num, i == cur);
        }
        centre(20 + OPTS + 1, "EXIT", cur == OPTS);
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

void sat_home_menu(void)
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
    sat_home_mode = 1;
    prev = sat_pad_raw & 0xffff;
    for (;;) {
        panel(19);
        pick = menu_list(1, 20, items, HOME_ITEMS, pick < 0 ? 0 : pick, HOME_IDLE);
        if (pick != 1) break;
        options();
    }
    sat_home_screen = 0;
    sat_home_mode = 0;
    sat_home_hold = 0;
    sat_duel_on = pick == 2;
    if (pick == 0 || pick == 2) inject = 900;       /* the game's own start path; ends when the game leaves attract */
}

