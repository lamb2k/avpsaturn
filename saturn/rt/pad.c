/* Real pad, read from the SMPC, handed to the game through its own input latch: the words it reads at 0x804000, 0x804010, 0x804020.
   Never blocks: one INTBACK is issued at each vblank and its result is taken at the next. Saturn pad word (active low):
   15 Right, 14 Left, 13 Down, 12 Up, 11 Start, 10 A, 9 C, 8 B, 7 R, 6 X, 5 Y, 4 Z, 3 L.
   Game: A attack, B jump, C gun, Start 1P start, X coin. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#define SMPC(o) (*(volatile u8 *)(0x20100000u + (o)))
#define IREG(n) SMPC(1 + (n) * 2)
#define OREG(n) SMPC(0x21 + (n) * 2)
#define COMREG SMPC(0x1f)
#define SR SMPC(0x61)
#define SF SMPC(0x63)
u32 sat_pad_raw = 0xffff;
#ifdef SAT_HOME
u32 sat_pad_raw2 = 0xffff;
extern u32 sat_home_pad(u32), sat_home_pad2(u32), sat_home_remap(u32);
#endif
static u16 in0 = 0xffff, in2 = 0xffff;

#ifdef SAT_INPUT_SCRIPT
extern u32 sat_vblanks_now(void);
/* Test flag: the retained Round 1 route's schedule (tools/mame_capture_oracle11_player_audio.lua) as pad words, replacing the SMPC read only.
   Frame number = vblank + 900: the route waits 1200 frames in attract, the coin here lands at vblank 300, so a run reaches Round 1 inside the one minute limit. */
static u32 script_word(u32 v)
{
    u32 f = v + 900, w = 0xffff;
    int coin, start, right, gun, attack, jump;
    if (f <= 4200) {
        coin = f >= 1200 && f <= 2400 && (f - 1200) % 180 < 3;
        start = f >= 1200 && f <= 2400 && (f - 1200) % 180 >= 30 && (f - 1200) % 180 < 33;
        gun = (f >= 1500 && f < 4200 && f % 90 < 5) || (f >= 2600 && f < 4200 && f % 75 < 6);
        right = f >= 2600 && f < 4200;
        attack = f >= 2600 && f < 4200 && f % 310 < 7;
        jump = f >= 2600 && f < 4200 && f % 430 < 7;
    } else {
        u32 r = f - 4200;
        coin = r % 600 >= 30 && r % 600 < 34;
        start = r % 600 >= 90 && r % 600 < 94;
        right = 1;
        gun = r % 45 < 7;
        attack = r % 180 < 8;
        jump = r % 240 < 8;
    }
    if (right) w &= ~0x8000u;
    if (start) w &= ~0x0800u;
    if (attack) w &= ~0x0400u;
    if (gun) w &= ~0x0200u;
    if (jump) w &= ~0x0100u;
    if (coin) w &= ~0x0040u;
    return w;
}
#endif

static void map_pad(u32 p)
{
    u32 w = 0xff;
    if (!(p & 0x8000)) w &= ~1u;
    if (!(p & 0x4000)) w &= ~2u;
    if (!(p & 0x2000)) w &= ~4u;
    if (!(p & 0x1000)) w &= ~8u;
    if (!(p & 0x0200)) w &= ~0x10u;   /* C gun, the game's button 1 */
    if (!(p & 0x0400)) w &= ~0x20u;   /* A attack, button 2 */
    if (!(p & 0x0100)) w &= ~0x40u;   /* B jump, button 3 */
    in0 = (u16)(0xff00u | w);
    w = 0xffff;
    if (!(p & 0x0800)) w &= ~0x0100u;
    if (!(p & 0x0040)) w &= ~0x1000u;
    in2 = (u16)w;
#ifdef SAT_HOME
    {
        u32 q = sat_home_pad2(sat_home_remap(sat_pad_raw2)), v = 0xff;
        if (!(q & 0x8000)) v &= ~1u;
        if (!(q & 0x4000)) v &= ~2u;
        if (!(q & 0x2000)) v &= ~4u;
        if (!(q & 0x1000)) v &= ~8u;
        if (!(q & 0x0200)) v &= ~0x10u;
        if (!(q & 0x0400)) v &= ~0x20u;
        if (!(q & 0x0100)) v &= ~0x40u;
        in0 = (u16)((v << 8) | (in0 & 0xff));
        if (!(q & 0x0800)) in2 &= (u16)~0x0200u;
    }
#endif
}

/* Called once per vblank, first thing. */
void sat_pad_tick(void)
{
    if (!(SF & 1)) {
        u32 st = OREG(0), id = OREG(1);
        if (st == 0xf1 && (id >> 4) == 0) sat_pad_raw = ((u32)OREG(2) << 8) | OREG(3);
        else if (st == 0xf0) sat_pad_raw = 0xffff;
#ifdef SAT_HOME
        /* Second port follows the first's two data bytes when a plain pad is there; a multitap or other device reads idle here. */
        if (st == 0xf1 && (id >> 4) == 0 && OREG(4) == 0xf1 && (OREG(5) >> 4) == 0) sat_pad_raw2 = ((u32)OREG(6) << 8) | OREG(7);
        else sat_pad_raw2 = 0xffff;
#endif
        if (SR & 0x20) { IREG(0) = 0x40; SF = 1; }  /* more ports queued, drop them */
        else { IREG(0) = 0x00; IREG(1) = 0x0a; IREG(2) = 0xf0; COMREG = 0x10; SF = 1; }
    }
#ifdef SAT_INPUT_SCRIPT
    map_pad(script_word(sat_vblanks_now()));
#elif defined(SAT_HOME)
    map_pad(sat_home_pad(sat_home_remap(sat_pad_raw)));
#else
    map_pad(sat_pad_raw);
#endif
#ifdef SAT_GUESTS
    { extern void sat_guest_wolverine_pad(u16 *in0) __attribute__((weak)); if (sat_guest_wolverine_pad) sat_guest_wolverine_pad(&in0); }   /* bonus characters: motion inputs */
#endif
}
u32 sat_pad_in0(void) { return in0; }
u32 sat_pad_in2(void) { return in2; }
