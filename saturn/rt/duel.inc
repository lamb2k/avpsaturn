/* PvP duel, included by kernel.c under SAT_HOME. docs/notes/AVP_DUEL_DESIGN.md.
   Uses the game's own player-pair hit test (0x1d03e, as 0x1c9a8 calls it in the arcade when no enemies live, with its 1 damage friendly hit).
   The attacker's tag byte +8 is set for the call, so damage_apply takes its enemy-attack path: the game's own table, by attack and by the target's health, and the game's own hit or KO state.
   Runs on the master between task walks, once per game tick, interrupts masked: a vblank body uses the same 68000 stack and registers. */
extern void f_1d03e(void);
#define PL(i) (0xff8380u + (u32)(i) * 0x100u)
#define DUEL_LINE 8   /* pixels of depth two fighters may differ by */
#define DUEL_PLAYERS 2   /* pairs are a loop, so player 3 stays open */
volatile u32 sat_duel_on;
struct { u32 hits[2], last_health[2]; } sat_duel_stats;
static u8 duel_tick_seen;
static void duel_pair(int a, int t)
{
    u32 pa = PL(a), pt = PL(t);
    if (!r8(pa) || !r8(pt) || r8(pa + 0x9e)) return;
    { int dz = (int)r16(pa + 0x18) - (int)r16(pt + 0x18); if (dz < -DUEL_LINE || dz > DUEL_LINE) return; }   /* the arcade pass wants the exact line; two players cannot hold that */
    cpu.a[6] = pa; cpu.a[1] = pt;
    w8(pa + 8, 1);
    f_1d03e();
    w8(pa + 8, 0);
    if (cpu.d[0] & 0xff) {
        w8(pt + 0x65, r8(pa + 0xd1));
        w8(pa + 0x6e, 1);
        if (!r8(pa + 0x80)) w8(pa + 0x80, 1);
        sat_duel_stats.hits[a]++;
    }
}
static void duel_tick(void)
{
    static Cpu save;
    u32 sr;
    int a, t;
    if (!sat_duel_on || r8(0xff81b0) || r8(0xff8001) != 2 || r8(0xff8019) == duel_tick_seen) return;
    duel_tick_seen = r8(0xff8019);
    __asm__ volatile ("stc sr,%0" : "=r"(sr));
    __asm__ volatile ("ldc %0,sr" : : "r"(sr | 0xf0));
    save = cpu;
    cpu.a[5] = 0xff8000; cpu.a[7] = 0xff8000;
    for (a = 0; a < DUEL_PLAYERS; a++)
        for (t = 0; t < DUEL_PLAYERS; t++)
            if (a != t) duel_pair(a, t);
    cpu = save;
    __asm__ volatile ("ldc %0,sr" : : "r"(sr));
    for (a = 0; a < 2; a++) sat_duel_stats.last_health[a] = r16(PL(a) + 0x40);
}
/* Arena: fighters stay on the screen where the duel began, so the camera and the stage's spawn table, driven by it, do not walk on. */
static u16 arena_cam;
static u8 arena_set;
static void duel_arena(void)
{
    int i;
    /* Centre: where the two fighters stand once both are in play; the screen is 384 wide. */
    if (!arena_set) { if (r8(PL(0) + 4) != 2 || r8(PL(1) + 4) != 2) return; arena_cam = (u16)((r16(PL(0) + 0x10) + r16(PL(1) + 0x10)) / 2 - 192); arena_set = 1; }
    for (i = 0; i < DUEL_PLAYERS; i++) {
        u32 p = PL(i);
        int x = (int)r16(p + 0x10), lo = arena_cam + 72, hi = arena_cam + 312;   /* 240 wide: the camera leads the fighters, so the bounds sit inside the screen */
        if (!r8(p)) continue;
        if (x < lo) w16(p + 0x10, (u16)lo);
        if (x > hi) w16(p + 0x10, (u16)hi);
    }
}
/* KO ends the duel: no continue. The other player wins; both down is a draw. Result over the held picture, then the title. */
extern volatile int sat_home_hold, sat_home_mode;
extern char sat_home_text[28][44];
extern void sat_home_centre(int, const char *, int), sat_home_clear(void), sat_home_frame(void), sat_home_restart(void);
volatile u32 sat_duel_result;   /* 1 player 1, 2 player 2, 3 draw; for the bot */
static void duel_end(void)
{
    int ko0 = r8(PL(0) + 4) == 4, ko1 = r8(PL(1) + 4) == 4, n;
    if (!ko0 && !ko1) return;
    for (n = 0; n < 20; n++) sat_home_frame();   /* both may fall in the same moment */
    ko0 = r8(PL(0) + 4) == 4; ko1 = r8(PL(1) + 4) == 4;
    sat_duel_result = ko0 && ko1 ? 3 : ko1 ? 1 : 2;
    sat_home_hold = 1;
    sat_home_clear();
    { int r, c; for (r = 9; r < 15; r++) for (c = 10; c < 34; c++) sat_home_text[r][c] = 1; }
    sat_home_centre(11, sat_duel_result == 3 ? "DRAW" : sat_duel_result == 1 ? "PLAYER 1 WINS" : "PLAYER 2 WINS", 1);
    sat_home_mode = 1;
    for (n = 0; n < 240; n++) sat_home_frame();
    sat_home_mode = 0;
    sat_home_hold = 0;
    sat_duel_on = 0; arena_set = 0;
    sat_home_restart();
}
void sat_duel_step(void)
{
    if (!sat_duel_on || r8(0xff81b0) || r8(0xff8001) != 2 || !r8(PL(0)) || !r8(PL(1))) { duel_tick(); return; }
    duel_arena();
    duel_tick();
    duel_end();
}
