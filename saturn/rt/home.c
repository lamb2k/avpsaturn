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
volatile u32 sat_home_warp;
/* Screen adjust and button map (home_cold.c): this power-on only. btn: Saturn button index (A B C X Y Z L R) for the game's gun, attack, jump. */
struct { signed char nx, ny; u8 btn[3]; } sat_home_cfg = { 0, 0, { 2, 0, 1 } };
static const u16 btn_bit[8] = { 0x0400, 0x0100, 0x0200, 0x0040, 0x0020, 0x0010, 0x0008, 0x0080 };
/* The pad word with the chosen buttons moved onto C (gun), A (attack), B (jump); X Y Z L R read idle to the game. */
u32 sat_home_remap(u32 p)
{
    static const u16 to[3] = { 0x0200, 0x0400, 0x0100 };
    u32 o = p | 0x07f8u;
    int i;
    for (i = 0; i < 3; i++) if (!(p & btn_bit[sat_home_cfg.btn[i] & 7])) o &= ~(u32)to[i];
    return o;
}           /* stage word to start at, 0 off (see sat_home_poll) */
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
u32 sat_home_prev = 0xffff;
#define prev sat_home_prev

#ifdef SAT_HOME_NOFIRST
static int shown = 1;
#else
static int shown;
#endif
#define IN_ATTRACT (G(0xff81b0) != 0)
#define PAUSE_OK (!IN_ATTRACT && G(0xff8001) == 2 && G(0xff8380) != 0 && G(0xff8384) != 4)

/* Second pad: idle while held; Start only as the duel's start path sends it, or to join or continue in play. */
#ifdef SAT_DUEL_MENU
extern u8 sat_duel_stun[2];
#define STUN(i) if (sat_duel_on && sat_duel_stun[i]) raw |= ~P_START & 0xffffu   /* hitstun: no moves, Start still pauses */
#else
#define STUN(i)
#endif
u32 sat_home_pad2(u32 raw)
{
    if (sat_home_hold) return 0xffff;
    STUN(1);
    if (inject && sat_duel_on && G(0xff818c) >= 2) return (inject & 4) ? raw | P_START : raw & ~P_START;
    if (IN_ATTRACT) return raw | P_START;
    return raw;
}
/* Pad word as the game sees it (pad.c): idle while held; Start belongs to these menus where they own it. */
u32 sat_home_pad(u32 raw)
{
    u32 cred = G(0xff818c);
    if (sat_home_hold) return 0xffff;
    STUN(0);
    raw |= P_COIN;
    /* No coin to insert at home, and no coin sound: a credit is simply there whenever one is wanted. The game's start path spends it. Free play's own coinage is not used: its paths are outside the census the stage files keep ROM for. */
    if (cred < (sat_duel_on ? 2u : 1u) && (inject || !IN_ATTRACT)) { G(0xff818c) = (u8)(sat_duel_on ? 2 : 1); cred = G(0xff818c); }
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
        for (i = 0; i < n; i++) sat_home_centre(row0 + i * (n > 4 ? 1 : 2), items[i], i == cur);
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
#if SAT_GFX_FIT == 3   /* test build: pad Z switches picture fit, pad Y holds the game */
    {
        extern volatile int sat_fit_scale;
        if (e & 0x10) *(volatile int *)((unsigned long)&sat_fit_scale | 0x20000000UL) ^= 1;
        if (e & 0x20) {
            sat_home_hold = 1;
            for (;;) {
                sat_home_frame();
                e = sat_home_edges();
                if (e & 0x10) *(volatile int *)((unsigned long)&sat_fit_scale | 0x20000000UL) ^= 1;
                if (e & 0x20) break;
            }
            sat_home_hold = 0;
            e = 0;
        }
    }
#endif
    /* Start at another stage (set by a bot over MCP, or a menu): the game's start path sets the stage word to 2; it is replaced
       with the chosen word while it reads 2, so the stage's own setup reads the new one. Re-armed in attract. */
    {
        static u32 warp_polls;
        if (IN_ATTRACT) warp_polls = 0;
        else if (sat_home_warp && warp_polls < 120 && (G(0xff81e8) << 8 | G(0xff81e9)) == 2) {
            G(0xff81e8) = (u8)(sat_home_warp >> 8); G(0xff81e9) = (u8)sat_home_warp; if (G(0xff8380)) warp_polls++;
        }
    }
    if (inject && !IN_ATTRACT) inject = 0;
    if (inject) return;
    if (IN_ATTRACT) {
        /* First sight once the boot warning has gone, then on Start. */
        /* The game's own title (mode 4) is the backdrop: logo and art as the game draws them. Start elsewhere in the attract goes back to it. */
        static u32 title_at;   /* the logo fades in: wait for it */
        if (G(0xff8001) != 4) title_at = 0;
        else if (!title_at) title_at = sat_vblanks_now();
        if (title_at && sat_vblanks_now() - title_at > 150 && (!shown || (e & P_START))) { shown = 1; sat_home_menu(); }
        else if ((e & P_START) && !title_at) { shown = 0; sat_home_restart(); }
    } else if ((e & P_START) && PAUSE_OK)
        pause_menu();
}
