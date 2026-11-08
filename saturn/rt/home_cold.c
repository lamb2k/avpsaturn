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
#ifndef HOME_CFG_T   /* home.c has it when both are in one unit (tests/home_lives_test.c) */
typedef struct { signed char nx, ny; u8 btn[3]; u8 lives; } HomeCfg;
#endif
extern HomeCfg sat_home_cfg;
/* Player settings: the game's own bytes in its settings block, both copies, and the RAM byte its boot code loads them to. */
typedef struct { const char *label; u8 off; u16 ram; u8 n; const char *const *names; } Opt;
#ifdef SAT_GUESTS
#include "guests.h"
#define GAME_OPTS 5
#else
#define GAME_OPTS 4
#endif
static const char *const on_off[] = { "OFF", "ON" };
static const char *const sound[] = { "MONAURAL", "STEREO" };
/* The game's own eight extend rules (its text table at 0xdd60; index 0 prints nothing). */
static const char *const extend[] = { "NONE", "100000 ONLY", "400000 ONLY", "1000000 ONLY", "100000 400000", "400000 500000", "800000 600000", "1200000 1000000" };
static const Opt opts[] = {
    { "DIFFICULTY", 0x10, 0x81cf, 8, 0 },
    { "EXTEND", 0x11, 0x81d0, 8, extend },
    { "CONTINUE", 0x01, 0x81be, 2, on_off },
    { "LIVES", 0xff, 0, 9, 0 },          /* not the game's: sat_home_cfg.lives, see opt_get */
#ifdef SAT_GUESTS
    { "BONUS CHARACTERS", 0xfe, 0, 4, sat_guest_row_names },   /* not the game's: sat_guest_sel (guests.c), OFF by default */
#endif
    { "AUDIO", 0x04, 0x81d2, 2, sound },
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
/* A screen inside the menus, as Capcom's Saturn option screens draw it (MSHvSF OPTION MODE): a translucent panel over the game's logo
   (the menu layer NBG3 with per-dot colour calculation, sat_gfx.c), the screen's name as its header at the top, the page under it. */
/* LIVES shows the arcade's start lives until one is chosen: stock from the game's table at 0x21330 by its lives byte (settings 0x12 = ff81d1), plus 1.
   (The game adds 1 more for settings 4 to 7 when the player's +0xff flag is set; the default shows without it.) */
static const u8 start_stock[8] = { 0, 1, 2, 4, 0, 1, 2, 4 };
static int opt_get(const Opt *o) {
#ifdef SAT_GUESTS
    if (o->off == 0xfe) return sat_guest_sel;
#endif
    return o->off == 0xff ? (sat_home_cfg.lives ? sat_home_cfg.lives - 1 : start_stock[sat_home_get(0x12) & 7]) : sat_home_get(o->off); }
static void opt_set(const Opt *o, int v) {
#ifdef SAT_GUESTS
    if (o->off == 0xfe) { sat_guest_sel = (u8)v; return; }
#endif
    if (o->off == 0xff) sat_home_cfg.lives = (u8)(v + 1); else { sat_home_set(o->off, v); RAMB[o->ram] = (u8)v; } }
/* MSHvSF's OPTION MODE layout: the whole picture under the panel, the screen's name in large letters at the top, rows two apart from row 7 with
   labels ending at column 20 and values from column 23, "PRESS START BUTTON TO EXIT" at the bottom. Mode 4 also takes the logo's sprites off. */
#define ROW(i) (7 + 2 * (i))
#define FOOT 25
extern void sat_home_big(int, const char *);
extern int sat_home_list_gap;
static void sub(const char *title)
{
    int r, c;
    clear();
    for (r = 0; r < 28; r++) for (c = 0; c < 44; c++) sat_home_text[r][c] = 1;
    sat_home_big(3, title);
    sat_home_mode = 4;
}
static void label(int r, const char *s, int hi) { int n = 0; while (s[n]) n++; put(r, 21 - n, s, hi); }
static void value(int r, const char *s, int hi) { put(r, 23, s, hi); }
static void foot(void) { centre(FOOT, "PRESS START BUTTON TO EXIT", 0); }
/* One page of the game's settings: opts[first..first+n), then up to two items that open screens (returns 1 or 2), then EXIT. B goes back;
   Start on a setting leaves too, as Capcom's Saturn option screens do ("PRESS START BUTTON TO EXIT"). */
static int opt_page(const char *title, u32 screen, int first, int n, const char *x1, const char *x2)
{
    int cur = 0, i, x = (x1 ? 1 : 0) + (x2 ? 1 : 0);
    sat_home_screen = screen;
    for (;;) {
        u32 e;
        sub(title);
        for (i = 0; i < n; i++) {
            const Opt *o = &opts[first + i];
            int v = opt_get(o);
            char num[2];
            num[0] = (char)('1' + v); num[1] = 0;
            label(ROW(i), o->label, i == cur);
            value(ROW(i), o->names ? o->names[v] : num, i == cur);
        }
        if (x1) label(ROW(n), x1, cur == n);
        if (x2) label(ROW(n + 1), x2, cur == n + 1);
        label(ROW(n + x), "EXIT", cur == n + x);
        foot();
        sat_home_cursor = (u32)cur;
        frame();
        e = edges();
        if (e & P_B) return 0;
        if (e & P_UP) cur = cur ? cur - 1 : n + x;
        if (e & P_DOWN) cur = cur < n + x ? cur + 1 : 0;
        if (cur >= n) { if (e & (P_START | P_A | P_C)) return cur < n + x ? cur - n + 1 : 0; continue; }
        if (e & P_START) return 0;
        if (e & (P_LEFT | P_RIGHT | P_A | P_C)) {
            const Opt *o = &opts[first + cur];
            int v = opt_get(o);
            v = (e & P_LEFT) ? (v ? v - 1 : o->n - 1) : (v + 1 < o->n ? v + 1 : 0);
            opt_set(o, v);
        }
    }
}
static void sound_test(void);
static void music(void);
static void screen_adjust(void);
static void buttons(void);
/* OPTIONS, as Capcom's Saturn fighters lay it out: GAME (difficulty, extend, continue), BUTTONS, SOUND (mode, demo sound, sound test), SCREEN ADJUST, EXIT. */
static void options(void)
{
    static const char *const items[] = { "GAME OPTION", "BUTTON CONFIG.", "SOUND OPTION", "SCREEN ADJUST", "EXIT" };
    int pick = 0;
    for (;;) {
        sub("OPTION MODE");
        sat_home_list_gap = 2;
        pick = menu_list(2, ROW(0), items, 5, pick < 0 ? 0 : pick, 0);
        sat_home_list_gap = 0;
        if (pick == -2) return;
        if (pick == 0) opt_page("GAME OPTION", 10, 0, GAME_OPTS, 0, 0);
        else if (pick == 1) buttons();
        else if (pick == 2) { int x; while ((x = opt_page("SOUND OPTION", 11, GAME_OPTS, 2, "SOUND TEST", "SE TEST")) != 0) { if (x == 1) music(); else sound_test(); } }
        else if (pick == 3) screen_adjust();
        else return;
    }
}

/* Home settings beyond the game's own block: screen adjust and button map. Kept in work RAM (home.c) for this power-on; backup saves are not decided. */
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
        sub("SE TEST");
        
        hex4(b, id); label(ROW(0), "SOUND ID", 0); value(ROW(0), b, 1);
        centre(ROW(3), "A PLAY  C STOP", 0);
        foot();
        sat_home_cursor = id;
        frame();
        e = edges();
        if (e & (P_B | P_START)) return;
        if (e & P_LEFT) id = id ? id - 1 : 0x38c;
        if (e & P_RIGHT) id = id < 0x38c ? id + 1 : 0;
        if (e & P_UP) id = id + 16 <= 0x38c ? id + 16 : id;
        if (e & P_DOWN) id = id >= 16 ? id - 16 : id;
        if (e & P_A) sound_send(id >> 8, id & 0xff, 0, 0);
        if (e & P_C) sound_send(0xff, 0, 0, 0);
    }
}
/* Music: the game's 24 songs on the disc's 26 CD audio tracks (02 to 27; 0x18 and 0x1f have an intro track before their loop), played by their sound
   command through the same mailbox as the game, so the driver starts the CD track as in play. Names: where the stage files use each song
   (WORK/rounds.json sound sets); songs every stage file carries are named by number only. Left/right pick, A plays, C stops, B leaves. */
typedef struct { u8 cmd, track; const char *name; } Song;
static const Song songs[] = {
    { 0x01, 2, "ALL STAGES 1" }, { 0x03, 3, "ENDING 1" }, { 0x04, 4, "BOSS STAGES 1" }, { 0x05, 5, "TITLE" },
    { 0x06, 6, "ALL STAGES 2" }, { 0x07, 7, "ALL STAGES 3" }, { 0x08, 8, "STAGES 0A 10 22 24" }, { 0x09, 9, "ALL STAGES 4" },
    { 0x0a, 10, "ALL STAGES 5" }, { 0x0b, 11, "STAGES 12 16" }, { 0x0e, 12, "STAGE 24" }, { 0x0f, 13, "ALL STAGES 6" },
    { 0x10, 14, "ALL STAGES 7" }, { 0x11, 15, "STAGE 10" }, { 0x12, 16, "ALL STAGES 8" }, { 0x13, 17, "STAGE 1A" },
    { 0x15, 18, "STAGES 0A 10" }, { 0x16, 19, "STAGES 06 10" }, { 0x17, 20, "STAGES 12 22" }, { 0x18, 21, "STAGES 0E 1C 24" },
    { 0x1a, 23, "FRONT END" }, { 0x1b, 24, "ENDING 2" }, { 0x1c, 25, "STAGE 14" }, { 0x1f, 26, "BOSS" },
};
#define SONGS (int)(sizeof songs / sizeof songs[0])
static void music(void)
{
    static int cur;
    int playing = 0;
    sat_home_screen = 12;
    for (;;) {
        char b[8];
        u32 e;
        sub("SOUND TEST");
        
        b[0] = 'T'; b[1] = (char)('0' + songs[cur].track / 10); b[2] = (char)('0' + songs[cur].track % 10); b[3] = 0;
        label(ROW(0), b, 1);
        value(ROW(0), songs[cur].name, 1);
        if (playing) centre(ROW(1), "PLAYING", 0);
        centre(ROW(3), "A PLAY  C STOP", 0);
        foot();
        sat_home_cursor = (u32)cur | (u32)playing << 8;
        frame();
        e = edges();
        if (e & (P_B | P_START)) { if (playing) sound_send(0xff, 0, 0, 0); return; }
        if (e & P_LEFT) cur = cur ? cur - 1 : SONGS - 1;
        if (e & P_RIGHT) cur = cur + 1 < SONGS ? cur + 1 : 0;
        if (e & P_A) { sound_send(0, songs[cur].cmd, 0, 0); playing = 1; }
        if (e & P_C) { sound_send(0xff, 0, 0, 0); playing = 0; }
    }
}
/* Screen adjust: pad moves the whole picture, up to 16 pixels each way; A centres; B leaves. */
static void screen_adjust(void)
{
    sat_home_screen = 5;
    for (;;) {
        char b[8];
        u32 e;
        sub("SCREEN ADJUST");
        
        num(b, sat_home_cfg.nx); label(ROW(0), "X", 0); value(ROW(0), b, 1);
        num(b, sat_home_cfg.ny); label(ROW(1), "Y", 0); value(ROW(1), b, 1);
        centre(ROW(3), "PAD MOVES  A CENTRE", 0);
        foot();
        sat_home_cursor = (u32)(u8)sat_home_cfg.nx | (u32)(u8)sat_home_cfg.ny << 8;
        frame();
        e = edges();
        if (e & (P_B | P_START)) return;
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
        sub("BUTTON CONFIG.");
        for (i = 0; i < 3; i++) { label(ROW(i), what[i], i == cur); value(ROW(i), pads[sat_home_cfg.btn[i] & 7], i == cur); }
        label(ROW(3), "EXIT", cur == 3);
        foot();
        sat_home_cursor = (u32)cur;
        frame();
        e = edges();
        if (e & P_B) return;
        if (e & P_UP) cur = cur ? cur - 1 : 3;
        if (e & P_DOWN) cur = cur < 3 ? cur + 1 : 0;
        if (e & P_START) return;
        if (cur == 3) { if (e & (P_A | P_C)) return; continue; }
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
        sub("STAGE SELECT MODE");
        
        b[0] = (char)('0' + st / 10); b[1] = (char)('0' + st % 10); b[2] = 0;
        label(ROW(0), "STAGE", 0); value(ROW(0), b, 1);
        centre(FOOT, "PRESS START BUTTON TO PLAY", 0);
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
/* RANDOM picks from arenas that draw clean. 0e, 1c, 1e and 24 show wrong tile data in the duel (Duel 5): their round files spill sprites into
   ROM pages the stage's own walk never reads, and the duel reads some of them (with ROUND_SHARED_MIN=1 the 1c fight drew clean, s92.log).
   They come back once the duel has round files that keep those pages. */
static const u8 arenas[] = { 0x02 };
static int duel_setup(void)
{
    static const char *const labels[] = { "STOCKS", "TIME", "ALIENS" };   /* no ARENA row: the duel is stage 02 only (owner 11-08) */
    static const char *const times[] = { "OFF", "2 MIN", "3 MIN" };
    static const char *const freq[] = { "OFF", "LOW", "HIGH" };
    static int cur = 3;
    sat_home_screen = 8;
    for (;;) {
        char b[4];
        u32 e;
        int i;
        panel(19);
        centre(19, "DUEL", 0);
        for (i = 0; i < 3; i++) {
            put(20 + i, 10, labels[i], i == cur);
            b[0] = (char)('0' + sat_duel_opt.stocks); b[1] = 0;
            put(20 + i, 22, i == 0 ? (sat_duel_opt.minutes ? "-" : b) : i == 1 ? times[sat_duel_opt.minutes ? sat_duel_opt.minutes - 1 : 0] : freq[sat_duel_opt.aliens], i == cur);
        }
        sat_duel_opt.arena = 0;
        centre(24, "START", cur == 3);
        sat_home_cursor = (u32)cur;
        frame();
        e = edges();
        if (e & P_B) return 0;
        if (e & P_UP) cur = cur ? cur - 1 : 3;
        if (e & P_DOWN) cur = cur < 3 ? cur + 1 : 0;
        if (cur == 3) {
            if (e & (P_START | P_A | P_C)) {
                sat_home_warp = sat_duel_opt.arena ? arenas[sat_vblanks_now() % sizeof arenas] : 0;
                if (sat_home_warp == 2) sat_home_warp = 0;
#ifdef DUEL_ARENA_TEST   /* test build only: RANDOM always picks this stage */
                if (sat_duel_opt.arena) sat_home_warp = DUEL_ARENA_TEST;
#endif
                return 1;
            }
            continue;
        }
        if (e & (P_LEFT | P_RIGHT | P_A | P_C)) {
            int d = (e & P_LEFT) ? -1 : 1;
            if (cur == 0) sat_duel_opt.stocks = (u8)(sat_duel_opt.stocks + d < 1 ? 5 : sat_duel_opt.stocks + d > 5 ? 1 : sat_duel_opt.stocks + d);
            if (cur == 1) sat_duel_opt.minutes = (u8)((sat_duel_opt.minutes == 0 ? (d > 0 ? 2 : 3) : sat_duel_opt.minutes == 2 ? (d > 0 ? 3 : 0) : (d > 0 ? 0 : 2)));
            if (cur == 2) sat_duel_opt.aliens = (u8)((sat_duel_opt.aliens + 3 + d) % 3);
        }
    }
}
#endif
void sat_home_menu(void)
{
    /* Fixed positions: 0 arcade, 1 duel, 2 boss rush, 3 stage select, 4 options. Without the duel, item 1 is absent and the rest move up. */
#ifdef SAT_DUEL_MENU   /* until the duel is finished */
    static const char *const items[] = { "ARCADE MODE", "VERSUS MODE", "BOSS RUSH MODE", "STAGE SELECT MODE", "OPTION MODE" };
#define HOME_ITEMS 5
#define DUEL_SHIFT 0
#else
    static const char *const items[] = { "ARCADE MODE", "BOSS RUSH MODE", "STAGE SELECT MODE", "OPTION MODE" };
#define HOME_ITEMS 4
#define DUEL_SHIFT 1
#endif
    int pick = 0, p;
    sat_home_hold = 1;
    sat_home_mode = 3;                 /* title menus: text over the logo, the game's start lines hidden */
    prev = sat_pad_raw & 0xffff;
    for (;;) {
        panel(19);
        sat_home_mode = 3;
        pick = menu_list(1, 19, items, HOME_ITEMS, pick < 0 ? 0 : pick, HOME_IDLE);
        if (pick == -2) { pick = (int)sat_home_cursor; continue; }   /* B at the top level: nothing above it */
        p = pick >= 1 ? pick + DUEL_SHIFT : pick;
        sat_home_warp = 0; sat_home_rush = 0;
        if (p == 4) options();
        else if (p == 3) { if (stage_select()) { pick = 0; break; } }
#ifdef SAT_DUEL_MENU
        else if (p == 1) { if (duel_setup()) break; }   /* VERSUS MODE: duel rules, then the game's select */
#endif
        else if (p == 2) { sat_home_warp = 4; sat_home_rush = 1; pick = 0; break; }
        else break;
    }
    p = pick >= 1 ? pick + DUEL_SHIFT : pick;
    if (pick < 0 || p != 1) pick = pick < 0 ? -1 : 0; else pick = 2;
    sat_home_screen = 0;
    sat_home_mode = 0;
    sat_home_hold = 0;
    sat_duel_on = pick == 2;
    if (pick == 0 || pick == 2) inject = 900;       /* the game's own start path; ends when the game leaves attract */
}

