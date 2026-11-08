/* Party-fighter duel rules on top of duel.inc, SAT_DUEL_MENU only.
   Health is held full; whatever the game takes off (its own damage table: player hits through 0x1d03e, enemy hits through its own paths)
   goes onto a damage percent instead. Knockback grows with percent, so a launched fighter can pass the arena edge: a ring-out costs a stock.
   All numbers here are this lane's own tuning (ESTIMATE, tuned by bot runs on the emulator). */
#define SM_STOCKS 3
#define SM_FRICTION 2        /* 1/16 px per tick, per tick */
#define SM_LAUNCH 40         /* speed (1/16 px/tick) above which a fighter flies past the arena bounds */
#define SM_RESPAWN 90        /* ticks out after a ring-out */
#define SM_INVULN 180        /* ticks of flashing invulnerability after coming back */
#define SM_BLAST 72          /* px past the arena bound that counts as out */
struct {
    u16 pct[2], held[2];     /* percent; the health the game is held at */
    s16 v[2];                /* horizontal speed, 1/16 px per tick */
    u16 frac[2];
    u8 stocks[2], stun[2], out[2], launched[2], hidden[2], set;
    u16 inv[2];
    int fx[2];
    u16 real_x[2];
    u32 rings;               /* ring-outs, for the bot */
    s16 score[2];            /* timed mode: minus one per fall */
    u32 clock;               /* timed mode: ticks left; 0 untimed */
    u8 sudden;
} sat_smash;
/* Duel options, set by the duel menu (home_cold.c). */
struct { u8 stocks, minutes, aliens, p1, p2, arena; } sat_duel_opt = { SM_STOCKS, 0, 1, 0, 1, 0 };
u8 sat_duel_stun[2];         /* home.c: pad idle while set */
volatile u32 sat_smash_freeze;
/* Hit log: vblank, attacker, damage, target percent after, speed given. */
struct { u32 n; struct { u16 tick; u8 who, dmg; u16 pct; s16 v; } row[32]; } sat_smash_log;

static int smash_can_hit(int t) { return sat_smash.set && !sat_smash.out[t] && !sat_smash.inv[t]; }

static void smash_hit(int a, int t, int dmg)
{
    int dir = (int)r16(PL(t) + 0x10) >= (int)r16(PL(a) + 0x10) ? 1 : -1;
    u32 pct, sp;
    if (dmg <= 0) return;
    pct = sat_smash.pct[t] + (u32)dmg;
    if (pct > 999) pct = 999;
    sat_smash.pct[t] = (u16)pct;
    sp = 8u + (u32)dmg * pct / 12u;           /* light hit at low percent: a stagger; big hit at high percent: a launch */
    if (sp > 400) sp = 400;
    sat_smash.v[t] = (s16)(dir * (int)sp);
    sat_smash.launched[t] = sp >= SM_LAUNCH;
    sat_smash.fx[t] = (int)r16(PL(t) + 0x10);
    sat_smash.stun[t] = (u8)(6 + sp / 8 > 60 ? 60 : 6 + sp / 8);
    if (sp >= 120) sat_smash_freeze = 3 + sp / 100;   /* hit-freeze on strong hits, vblanks */
    {
        u32 i = sat_smash_log.n++ & 31;
        sat_smash_log.row[i].tick = (u16)sat_dbg.vblanks; sat_smash_log.row[i].who = (u8)a; sat_smash_log.row[i].dmg = (u8)dmg;
        sat_smash_log.row[i].pct = (u16)pct; sat_smash_log.row[i].v = sat_smash.v[t];
    }
}

extern char sat_home_text[28][44];
static void smash_hud(void)
{
    int i;
    if (sat_smash.clock) {
        u32 secs = (sat_smash.clock + 59) / 60;
        sat_home_text[5][20] = (char)('0' + secs / 60); sat_home_text[5][21] = ':';
        sat_home_text[5][22] = (char)('0' + secs % 60 / 10); sat_home_text[5][23] = (char)('0' + secs % 10);
    } else if (sat_smash.sudden) { const char *t = "SUDDEN DEATH"; int k; for (k = 0; t[k]; k++) sat_home_text[5][16 + k] = t[k] == ' ' ? 0 : t[k]; }
    extern char sat_home_text[28][44];
    if (sat_home_hold) return;
    if (sat_home_mode != 1) { sat_home_clear(); sat_home_mode = 1; }
    for (i = 0; i < 2; i++) {
        char b[12]; int n = 0, p = sat_smash.pct[i], s;
        if (sat_smash.out[i]) { b[n++] = '-'; b[n++] = '-'; b[n++] = '-'; }
        else { if (p >= 100) b[n++] = (char)('0' + p / 100); if (p >= 10) b[n++] = (char)('0' + p / 10 % 10); b[n++] = (char)('0' + p % 10); }
        b[n++] = '%';
        while (n < 5) b[n++] = 0;
        if (!sat_duel_opt.minutes || sat_smash.sudden) for (s = 0; s < sat_duel_opt.stocks; s++) b[n++] = s < sat_smash.stocks[i] ? '*' : 0;
        for (s = 0; s < n; s++) sat_home_text[5][(i ? 33 : 3) + s] = b[s] ? (char)(b[s] | ((sat_smash.inv[i] & 8) ? 0x80 : 0)) : 0;   /* blanks leave the game's own picture */
    }
}

/* Once per game tick, after the hit pass. Returns the player who lost the last stock + 1, or 0. */
static int smash_tick(int lo, int hi)
{
    int i;
    if (!sat_smash.set) {
        sat_smash.set = 1;
        for (i = 0; i < 2; i++) { sat_smash.held[i] = r16(PL(i) + 0x40); sat_smash.stocks[i] = sat_duel_opt.minutes ? 99 : sat_duel_opt.stocks; sat_smash.score[i] = 0; sat_smash.pct[i] = 0; sat_smash.v[i] = 0; sat_smash.out[i] = sat_smash.inv[i] = sat_smash.stun[i] = 0; }
        sat_smash.clock = (u32)sat_duel_opt.minutes * 60u * 60u; sat_smash.sudden = 0;
        sat_home_clear(); sat_home_mode = 1;
    }
    if (sat_smash.clock && --sat_smash.clock == 0) {   /* time: more score wins; a tie goes to sudden death, one stock each at 300% */
        if (sat_smash.score[0] != sat_smash.score[1]) { smash_hud(); return sat_smash.score[0] < sat_smash.score[1] ? 1 : 2; }
        sat_smash.sudden = 1;
        for (i = 0; i < 2; i++) { sat_smash.stocks[i] = 1; sat_smash.pct[i] = 300; }
    }
    for (i = 0; i < 2; i++) {
        u32 p = PL(i);
        int x, hp = (int)(s16)r16(p + 0x40);
        if (hp < (int)sat_smash.held[i]) {     /* anything else (stage enemies) also goes onto the percent */
            if (!sat_smash.out[i] && !sat_smash.inv[i]) { u32 q = sat_smash.pct[i] + (u32)((int)sat_smash.held[i] - hp); sat_smash.pct[i] = (u16)(q > 999 ? 999 : q); }
            w16(p + 0x40, sat_smash.held[i]);
        }
        if (sat_smash.stun[i]) sat_smash.stun[i]--;
        sat_duel_stun[i] = sat_smash.stun[i] != 0 || sat_smash.out[i] != 0;
        if (sat_smash.out[i]) {
            w16(p + 0x10, (u16)(lo - 400));
            if (--sat_smash.out[i] == 0) {
                w16(p + 0x10, (u16)((lo + hi) / 2 + (i ? 40 : -40)));
                sat_smash.inv[i] = SM_INVULN; sat_smash.pct[i] = 0; sat_smash.v[i] = 0;
            }
            continue;
        }
        if (sat_smash.inv[i]) {   /* flash: moved off the arena every other 4 ticks, back at its real place between */
            int hide = (--sat_smash.inv[i] & 4) != 0;
            if (hide && !sat_smash.hidden[i]) { sat_smash.real_x[i] = r16(p + 0x10); sat_smash.hidden[i] = 1; }
            else if (!hide && sat_smash.hidden[i]) { w16(p + 0x10, sat_smash.real_x[i]); sat_smash.hidden[i] = 0; }
            if (hide) { w16(p + 0x10, (u16)(lo - 400)); continue; }
        }
        x = sat_smash.launched[i] ? sat_smash.fx[i] : (int)r16(p + 0x10);   /* in flight the fighter's own place, past any edge the game keeps */
        if (sat_smash.v[i]) {
            int s = sat_smash.v[i] + (s16)sat_smash.frac[i];
            x += s / 16; sat_smash.frac[i] = (u16)(s16)(s % 16);
            if (sat_smash.v[i] > 0) { sat_smash.v[i] -= SM_FRICTION; if (sat_smash.v[i] < 0) sat_smash.v[i] = 0; }
            else { sat_smash.v[i] += SM_FRICTION; if (sat_smash.v[i] > 0) sat_smash.v[i] = 0; }
            if (sat_smash.v[i] == 0) sat_smash.launched[i] = 0;
        }
        if (sat_smash.launched[i] && (x < lo - SM_BLAST || x > hi + SM_BLAST)) {   /* ring-out */
            sat_smash.rings++;
            sat_smash.launched[i] = 0; sat_smash.v[i] = 0;
            if (sat_smash.stocks[i]) sat_smash.stocks[i]--;
            sat_smash.score[i]--;
            if (!sat_smash.stocks[i]) { smash_hud(); return i + 1; }
            sat_smash.out[i] = SM_RESPAWN;
            w16(p + 0x10, (u16)(lo - 400));
            continue;
        }
        sat_smash.fx[i] = x;
        if (!sat_smash.launched[i]) { if (x < lo) x = lo; if (x > hi) x = hi; }
        w16(p + 0x10, (u16)x);
    }
    smash_hud();
    return 0;
}


/* Stage spawns off: the stage's spawn table task (record 0xff1812, state byte +4: 0 init, 2 walk, 4 done) is parked at done once it has set up,
   so only the duel's own aliens come in. Bodies the table already placed are not touched. */
static void smash_no_stage_spawns(void)
{
    if (r8(0xff1816) == 2) w8(0xff1816, 4);
}

/* Random aliens: the game's own alien rows from stage 02's spawn table (ROM 0x15c108 on, tag 4 rows), spawned through the table's own
   allocator path (0x1c146 by tag, then the row's fields as 0x1bf1a writes them), at a random time and a random arena edge. */
extern void f_1c146(void);
/* Spawn table per stage word (the pointer table at 0x1be82, opcode space, stage words 02 to 24). Plain alien rows: tag 4, bytes +12..+14 zero. */
static const u32 stage_table[18] = { 0x15c0d8, 0x15c1cc, 0x15c280, 0x15c494, 0x15c598, 0x15c5ec, 0x15c790, 0x15cc14, 0x15cf28,
    0x15cf8c, 0x15d030, 0x15d1e4, 0x15d3b8, 0x15d42c, 0x15d900, 0x15dac4, 0x15df48, 0x15e04c };
static u32 alien_own;
static u32 alien_classes[8];   /* bit set of the classes the stage's alien rows use */
static int alien_class(u32 c) { return (alien_classes[(c >> 5) & 7] >> (c & 31)) & 1; }
static u32 alien_rows[16];
static int alien_nrows;
static void alien_find_rows(void)
{
    u32 st = r16(0xff81e8), a;
    alien_nrows = 0;
    { int k; for (k = 0; k < 8; k++) alien_classes[k] = 0; }
    if (st < 2 || st > 0x24 || (st & 1)) return;
    for (a = stage_table[st / 2 - 1]; RD16(a) < 0x8000 && alien_nrows < 16; a += 16)
        if (RD16(a + 6) == 4) {
            u32 c = RD8(a + 8);
            alien_classes[(c >> 5) & 7] |= 1u << (c & 31);
            if (!RD8(a + 12) && !RD8(a + 13) && !RD8(a + 14)) alien_rows[alien_nrows++] = a;
        }
}
#define ALIEN_POOL 0xffae80u   /* pools_reset 0x1729c: tag 20, 16 slots of 0x80, count ee85; spawn rows of kind 4 allocate here (0x1c146 -> 0x176f0) */
#define ALIEN_SLOTS 16
#define ALIEN_SIZE 0x80u
static u32 alien_seed;
static u16 alien_wait;
u32 sat_alien_spawns, sat_alien_last;
static u32 alien_rand(void) { alien_seed = alien_seed * 1103515245u + 12345u; return alien_seed >> 16; }
u32 sat_alien_culled;
extern void f_17706(void), f_176b4(void);
static int alien_live(void) { int i, n = 0; for (i = 0; i < ALIEN_SLOTS; i++) if ((alien_own >> i) & 1) n++; return n; }
/* Stage spawns off, part 2: the stage's own bodies (doors, hives) keep sending tag 4 aliens. Any live slot in the pool the duel did not spawn
   is released through the pool's own release (0x17706); a duel slot that went free (its body released it) leaves the set. */
static void alien_cull(void)
{
    static Cpu save;
    u32 sr;
    int i;
    __asm__ volatile ("stc sr,%0" : "=r"(sr));
    __asm__ volatile ("ldc %0,sr" : : "r"(sr | 0xf0));
    save = cpu;
    cpu.a[5] = 0xff8000; cpu.a[7] = 0xff8000;
    for (i = 0; i < ALIEN_SLOTS; i++) {
        u32 a = ALIEN_POOL + (u32)i * ALIEN_SIZE;
        if (!r32(a)) { alien_own &= ~(1u << i); continue; }
        if ((alien_own >> i) & 1) continue;
        if (r8(a + 8) != 0x14 || !alien_class(r8(a + 2))) continue;   /* props in the same pool stay */
        cpu.a[6] = a;
        f_17706();
        sat_alien_culled++;
    }
    /* The doors and hives send their aliens into the tag 12 pool (0xff9580, 20 slots of 0xc0, release 0x176b4). Releasing them from here
       froze both players for good in the emulator (s7.log), so it is off until the door bodies are read. */
#ifdef DUEL_CULL_DOORS
    for (i = 0; i < 20; i++) {
        u32 a = 0xff9580u + (u32)i * 0xc0u;
        if (!r32(a) || r8(a + 8) != 0x0c) continue;
        cpu.a[6] = a;
        f_176b4();
        sat_alien_culled++;
    }
#endif
    cpu = save;
    __asm__ volatile ("ldc %0,sr" : : "r"(sr));
}
static void smash_aliens(int lo, int hi)
{
    static Cpu save;
    u32 sr, row;
    int cap = sat_duel_opt.aliens >= 2 ? 3 : 2;
    if (!alien_seed) { alien_seed = sat_dbg.vblanks * 2654435761u + 1; alien_wait = 600; alien_find_rows(); }
    alien_cull();
    if (!sat_duel_opt.aliens) return;   /* none in the first 10 s */
    if (alien_wait) { alien_wait--; return; }
    alien_wait = (u16)(sat_duel_opt.aliens >= 2 ? 180 + alien_rand() % 180 : 480 + alien_rand() % 420);
    if (!alien_nrows || alien_live() >= cap || sat_smash.out[0] || sat_smash.out[1]) return;
    row = alien_rows[alien_rand() % (u32)alien_nrows];
    __asm__ volatile ("stc sr,%0" : "=r"(sr));
    __asm__ volatile ("ldc %0,sr" : : "r"(sr | 0xf0));
    save = cpu;
    cpu.a[5] = 0xff8000; cpu.a[7] = 0xff8000;
    cpu.a[1] = row; cpu.a[4] = 0;
    cpu.d[0] = (cpu.d[0] & 0xffff0000u) | RD16(row + 6);
    f_1c146();
    {
        u32 a4 = cpu.a[4] & 0xffffffu;
        sat_alien_last = a4;
        if (a4 >= ALIEN_POOL && a4 < ALIEN_POOL + ALIEN_SLOTS * ALIEN_SIZE) {
            alien_own |= 1u << ((a4 - ALIEN_POOL) / ALIEN_SIZE);
            int x = (alien_rand() & 1) ? lo - 24 : hi + 24;   /* in from an arena edge */
            w8(a4, (u8)(r8(a4) + 1));
            w16(a4 + 2, RD16(row + 8));
            w16(a4 + 16, (u16)x);
            w16(a4 + 20, RD16(row + 4));
            w8(a4 + 15, RD8(row + 12));
            w8(a4 + 12, RD8(row + 13));
            w8(a4 + 42, RD8(row + 14));
            sat_alien_spawns++;
        }
    }
    cpu = save;
    __asm__ volatile ("ldc %0,sr" : : "r"(sr));
}

/* Weapons: player shots and thrown items live in the tag 4 pool (0xff8680, 24 slots of 0x80; live list of words ending at 0xfff072, count ee7d),
   which the arcade tests only against enemies (0x1cbcc). The duel also runs the game's own hit test 0x1cf54 for each live shot against the
   player who did not fire it. The owner is found by a probe of the shot's record for a pointer to a player (sat_shot_probe, logged by the bot). */
#define SHOT_LIST 0xfff072u
struct { u32 seen; u8 off[2][8]; u8 n[2]; } sat_shot_probe;
u32 sat_shot_hits;
static int shot_owner_off = -1;
static int shot_owner(u32 s)
{
    int o, i;
    if (shot_owner_off >= 0) { u32 v = r32(s + (u32)shot_owner_off) & 0xffffffu; return v == PL(0) ? 0 : v == PL(1) ? 1 : -1; }
    /* probe: offsets holding a player address, kept per player; an offset seen for both players' shots is the owner field */
    sat_shot_probe.seen++;
    for (o = 0; o < 0x80; o += 2) {
        u32 v = r32(s + (u32)o) & 0xffffffu;
        for (i = 0; i < 2; i++) if (v == PL(i) && sat_shot_probe.n[i] < 8) {
            int k, dup = 0;
            for (k = 0; k < sat_shot_probe.n[i]; k++) if (sat_shot_probe.off[i][k] == o) dup = 1;
            if (!dup) sat_shot_probe.off[i][sat_shot_probe.n[i]++] = (u8)o;
        }
    }
    {
        int a, b;
        for (a = 0; a < sat_shot_probe.n[0]; a++) for (b = 0; b < sat_shot_probe.n[1]; b++)
            if (sat_shot_probe.off[0][a] == sat_shot_probe.off[1][b]) shot_owner_off = sat_shot_probe.off[0][a];
    }
    return -1;
}
static void duel_shots(void)
{
    int n = r8(0xffee7d), k;
    u32 l = SHOT_LIST;
    for (k = 0; k < n && k < 24; k++) {
        u32 s, t, pt;
        int own;
        u16 hp0;
        l -= 2;
        s = 0xff0000u | r16(l);
        own = shot_owner(s);
        if (own < 0) continue;
        t = (u32)(own ^ 1); pt = PL(t);
        if (!r8(pt) || !smash_can_hit((int)t)) continue;
        hp0 = r16(pt + 0x40);
        cpu.a[6] = s; cpu.a[1] = pt;
        f_1cf54();
        if ((s16)r16(pt + 0x40) < (s16)hp0) {
            sat_shot_hits++;
            smash_hit(own, (int)t, (int)hp0 - (int)(s16)r16(pt + 0x40));
            w16(pt + 0x40, hp0);
        }
    }
}
