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
} sat_smash;
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

static void smash_hud(void)
{
    int i;
    extern char sat_home_text[28][44];
    if (sat_home_hold) return;
    if (sat_home_mode != 1) { sat_home_clear(); sat_home_mode = 1; }
    for (i = 0; i < 2; i++) {
        char b[12]; int n = 0, p = sat_smash.pct[i], s;
        if (sat_smash.out[i]) { b[n++] = '-'; b[n++] = '-'; b[n++] = '-'; }
        else { if (p >= 100) b[n++] = (char)('0' + p / 100); if (p >= 10) b[n++] = (char)('0' + p / 10 % 10); b[n++] = (char)('0' + p % 10); }
        b[n++] = '%';
        while (n < 5) b[n++] = 0;
        for (s = 0; s < SM_STOCKS; s++) b[n++] = s < sat_smash.stocks[i] ? '*' : 0;
        for (s = 0; s < n; s++) sat_home_text[5][(i ? 33 : 3) + s] = b[s] ? (char)(b[s] | ((sat_smash.inv[i] & 8) ? 0x80 : 0)) : 0;   /* blanks leave the game's own picture */
    }
}

/* Once per game tick, after the hit pass. Returns the player who lost the last stock + 1, or 0. */
static int smash_tick(int lo, int hi)
{
    int i;
    if (!sat_smash.set) {
        sat_smash.set = 1;
        for (i = 0; i < 2; i++) { sat_smash.held[i] = r16(PL(i) + 0x40); sat_smash.stocks[i] = SM_STOCKS; sat_smash.pct[i] = 0; sat_smash.v[i] = 0; sat_smash.out[i] = sat_smash.inv[i] = sat_smash.stun[i] = 0; }
        sat_home_clear(); sat_home_mode = 1;
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
