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

/* Home settings beyond the game's own block: screen adjust and button map. Kept in work RAM (home.c) for this power-on; backup saves are not decided. */
typedef struct { signed char nx, ny; u8 btn[3]; } HomeCfg;
extern HomeCfg sat_home_cfg;
extern int sat_gfx_nudge_x, sat_gfx_nudge_y;
extern volatile u32 sat_home_warp, sat_home_rush;
static void num(char *b, int v)   /* signed, up to 2 digits */
{
    int i = 0;
    if (v < 0) { b[i++] = '-'; v = -v; } else b[i++] = '+';
    if (v >= 10) b[i++] = (char)('0' + v / 10);
    b[i++] = (char)('0' + v % 10); b[i] = 0;
}
static void hex4(char *b, unsigned v) { static const char h[] = "0123456789ABCDEF"; int i; for (i = 0; i < 4; i++) b[i] = h[(v >> (12 - 4 * i)) & 15]; b[4] = 0; }
/* Sound test: any id of the game's sound command table (0 to 0x38c, the driver's size), sent through the game's own mailbox path as its sender writes it.
   Effects play only when their clip is in the loaded stage file; music ids start their CD track. A plays, C stops all (the game's control 0), B leaves. */
extern void sat_audio_io_write8(unsigned long, unsigned long);
static void sound_send(unsigned hi, unsigned lo, unsigned b3, unsigned b4)
{
    int i;
    for (i = 0; i < 15; i++) sat_audio_io_write8(0x618001UL + 2UL * (unsigned long)i, 0);
    sat_audio_io_write8(0x618001UL, hi); sat_audio_io_write8(0x618003UL, lo);
    sat_audio_io_write8(0x618007UL, b3); sat_audio_io_write8(0x618009UL, b4);
    sat_audio_io_write8(0x61801fUL, 0);
}
static void sound_test(void)
{
    static unsigned id = 1;
    sat_home_screen = 4;
    for (;;) {
        char b[8];
        u32 e;
        panel(19);
        centre(20, "SOUND TEST", 0);
        hex4(b, id); put(22, 18, b, 1);
        centre(24, "A PLAY  C STOP  B EXIT", 0);
        sat_home_cursor = id;
        frame();
        e = edges();
        if (e & P_B) return;
        if (e & P_LEFT) id = id ? id - 1 : 0x38c;
        if (e & P_RIGHT) id = id < 0x38c ? id + 1 : 0;
        if (e & P_UP) id = id + 16 <= 0x38c ? id + 16 : id;
        if (e & P_DOWN) id = id >= 16 ? id - 16 : id;
        if (e & P_A) sound_send(id >> 8, id & 0xff, 0, 0);
        if (e & P_C) sound_send(0xff, 0, 0, 0);
    }
}
/* Screen adjust: pad moves the whole picture, up to 16 pixels each way; A centres; B leaves. */
static void screen_adjust(void)
{
    sat_home_screen = 5;
    for (;;) {
        char b[8];
        u32 e;
        panel(19);
        centre(20, "SCREEN ADJUST", 0);
        put(22, 12, "X", 0); num(b, sat_home_cfg.nx); put(22, 15, b, 1);
        put(22, 24, "Y", 0); num(b, sat_home_cfg.ny); put(22, 27, b, 1);
        centre(24, "A CENTRE  B EXIT", 0);
        sat_home_cursor = (u32)(u8)sat_home_cfg.nx | (u32)(u8)sat_home_cfg.ny << 8;
        frame();
        e = edges();
        if (e & P_B) return;
        if ((e & P_LEFT) && sat_home_cfg.nx > -16) sat_home_cfg.nx--;
        if ((e & P_RIGHT) && sat_home_cfg.nx < 16) sat_home_cfg.nx++;
        if ((e & P_UP) && sat_home_cfg.ny > -16) sat_home_cfg.ny--;
        if ((e & P_DOWN) && sat_home_cfg.ny < 16) sat_home_cfg.ny++;
        if (e & P_A) sat_home_cfg.nx = sat_home_cfg.ny = 0;
        sat_gfx_nudge_x = sat_home_cfg.nx; sat_gfx_nudge_y = sat_home_cfg.ny;
    }
}
/* Buttons: which Saturn button gives the game's gun, attack and jump (defaults C, A, B as before). */
static const char *const pads[] = { "A", "B", "C", "X", "Y", "Z", "L", "R" };
static void buttons(void)
{
    static const char *const what[] = { "GUN", "ATTACK", "JUMP" };
    int cur = 0, i;
    sat_home_screen = 6;
    for (;;) {
        u32 e;
        panel(19);
        for (i = 0; i < 3; i++) { put(20 + i, 10, what[i], i == cur); put(20 + i, 24, pads[sat_home_cfg.btn[i] & 7], i == cur); }
        centre(24, "EXIT", cur == 3);
        sat_home_cursor = (u32)cur;
        frame();
        e = edges();
        if (e & P_B) return;
        if (e & P_UP) cur = cur ? cur - 1 : 3;
        if (e & P_DOWN) cur = cur < 3 ? cur + 1 : 0;
        if (cur == 3) { if (e & (P_START | P_A | P_C)) return; continue; }
        if (e & P_LEFT) sat_home_cfg.btn[cur] = (u8)((sat_home_cfg.btn[cur] + 7) & 7);
        if (e & P_RIGHT) sat_home_cfg.btn[cur] = (u8)((sat_home_cfg.btn[cur] + 1) & 7);
    }
}
/* Stage select: start the game at one of its own stage words (02 to 24 by 2, as the game advances them); sat_home_poll puts it in place of the start's 02. */
static int stage_select(void)
{
    static int st = 1;
    sat_home_screen = 7;
    for (;;) {
        char b[8];
        u32 e;
        panel(19);
        centre(20, "STAGE SELECT", 0);
        b[0] = (char)('0' + st / 10); b[1] = (char)('0' + st % 10); b[2] = 0;
        put(22, 21, b, 1);
        centre(24, "START PLAY  B EXIT", 0);
        sat_home_cursor = (u32)st;
        frame();
        e = edges();
        if (e & P_B) return 0;
        if (e & P_LEFT) st = st > 1 ? st - 1 : 18;
        if (e & P_RIGHT) st = st < 18 ? st + 1 : 1;
        if (e & (P_START | P_A | P_C)) { sat_home_warp = (u32)(st * 2); return 1; }
    }
}
#ifdef SAT_DUEL_MENU
/* Duel rules (duel_smash.inc reads them). Characters are picked on the game's own select screen after this, each player with its own pad. */
typedef struct { u8 stocks, minutes, aliens, p1, p2, arena; } DuelOpt;
extern DuelOpt sat_duel_opt;
extern u32 sat_vblanks_now(void);
static const u8 arenas[] = { 0x02, 0x0e, 0x1c, 0x1e, 0x24 };   /* stages played through from the home start (STATUS, home features 3) */
static int duel_setup(void)
{
    static const char *const labels[] = { "STOCKS", "TIME", "ALIENS", "ARENA" };
    static const char *const times[] = { "OFF", "2 MIN", "3 MIN" };
    static const char *const freq[] = { "OFF", "LOW", "HIGH" };
    static const char *const arena[] = { "ROUND 1", "RANDOM" };
    static int cur = 4;
    sat_home_screen = 8;
    for (;;) {
        char b[4];
        u32 e;
        int i;
        panel(19);
        centre(19, "DUEL", 0);
        for (i = 0; i < 4; i++) {
            put(20 + i, 10, labels[i], i == cur);
            b[0] = (char)('0' + sat_duel_opt.stocks); b[1] = 0;
            put(20 + i, 22, i == 0 ? (sat_duel_opt.minutes ? "-" : b) : i == 1 ? times[sat_duel_opt.minutes ? sat_duel_opt.minutes - 1 : 0] : i == 2 ? freq[sat_duel_opt.aliens] : arena[sat_duel_opt.arena], i == cur);
        }
        centre(25, "START", cur == 4);
        sat_home_cursor = (u32)cur;
        frame();
        e = edges();
        if (e & P_B) return 0;
        if (e & P_UP) cur = cur ? cur - 1 : 4;
        if (e & P_DOWN) cur = cur < 4 ? cur + 1 : 0;
        if (cur == 4) {
            if (e & (P_START | P_A | P_C)) {
                sat_home_warp = sat_duel_opt.arena ? arenas[sat_vblanks_now() % sizeof arenas] : 0;
                if (sat_home_warp == 2) sat_home_warp = 0;
                return 1;
            }
            continue;
        }
        if (e & (P_LEFT | P_RIGHT | P_A | P_C)) {
            int d = (e & P_LEFT) ? -1 : 1;
            if (cur == 0) sat_duel_opt.stocks = (u8)(sat_duel_opt.stocks + d < 1 ? 5 : sat_duel_opt.stocks + d > 5 ? 1 : sat_duel_opt.stocks + d);
            if (cur == 1) sat_duel_opt.minutes = (u8)((sat_duel_opt.minutes == 0 ? (d > 0 ? 2 : 3) : sat_duel_opt.minutes == 2 ? (d > 0 ? 3 : 0) : (d > 0 ? 0 : 2)));
            if (cur == 2) sat_duel_opt.aliens = (u8)((sat_duel_opt.aliens + 3 + d) % 3);
            if (cur == 3) sat_duel_opt.arena ^= 1;
        }
    }
}
#endif
void sat_home_menu(void)
{
    /* Fixed positions: 0 start, 1 options, 2 duel, 3 stage select, 4 sound test, 5 screen, 6 buttons, 7 boss rush. Without the duel, item 2 is absent and the rest move up. */
#ifdef SAT_DUEL_MENU   /* until the duel is finished */
    static const char *const items[] = { "START GAME", "OPTIONS", "DUEL", "STAGE SELECT", "SOUND TEST", "SCREEN ADJUST", "BUTTONS", "BOSS RUSH" };
#define HOME_ITEMS 8
#define DUEL_SHIFT 0
#else
    static const char *const items[] = { "START GAME", "OPTIONS", "STAGE SELECT", "SOUND TEST", "SCREEN ADJUST", "BUTTONS", "BOSS RUSH" };
#define HOME_ITEMS 7
#define DUEL_SHIFT 1
#endif
    int pick = 0;
    sat_home_hold = 1;
    sat_home_mode = 1;
    prev = sat_pad_raw & 0xffff;
    for (;;) {
        int p;
        panel(19);
        pick = menu_list(1, 19, items, HOME_ITEMS, pick < 0 ? 0 : pick, HOME_IDLE);
        p = pick >= 2 ? pick + DUEL_SHIFT : pick;
        sat_home_warp = 0; sat_home_rush = 0;
        if (p == 1) options();
        else if (p == 3) { if (stage_select()) { pick = 0; break; } }
#ifdef SAT_DUEL_MENU
        else if (p == 2) { if (duel_setup()) break; }
#endif
        else if (p == 4) sound_test();
        else if (p == 5) screen_adjust();
        else if (p == 6) buttons();
        else if (p == 7) { sat_home_warp = 4; sat_home_rush = 1; pick = 0; break; }
        else break;
    }
    if (pick > 0 && pick + DUEL_SHIFT != 2) pick = 0;
    sat_home_screen = 0;
    sat_home_mode = 0;
    sat_home_hold = 0;
    sat_duel_on = pick == 2;
    if (pick == 0 || pick == 2) inject = 900;       /* the game's own start path; ends when the game leaves attract */
}

