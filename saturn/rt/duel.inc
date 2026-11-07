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
void sat_duel_step(void) { duel_tick(); }
