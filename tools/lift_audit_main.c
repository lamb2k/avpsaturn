/* Test-only driver for lift_audit.py: one lifted instruction per case; prints registers, X N Z V C (bit order of the SR) and changes. */
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned char u8;
typedef unsigned int u32;
typedef struct { u32 d[8]; u32 a[8]; u32 ccz, ccn, ccc, ccv, ccx; } Cpu;
static Cpu cpu;
Cpu *R = &cpu;
u8 *PAGE[256];
u8 RAMB[0x10000];
u8 ROMB[0x200000];
static u8 ZERO[256][0x10000], RAM0[0x10000];
static jmp_buf jb;
static const char *why;
static void stop(const char *w) { why = w; longjmp(jb, 1); }
void f_badjump(u32 a){(void)a;stop("badjump");}
void f_sysreg(void){stop("sysreg");}
void f_unhandled(u32 a){(void)a;stop("unhandled");}
void f_dispatch(u32 a){(void)a;stop("dispatch");}
u32 f_divu(u32 n, u32 d, int*ov){ d&=0xffff; if(!d) stop("div0"); u32 q=n/d; if(q>0xffff){*ov=1;return n;} return ((n%d)<<16)|q; }
u32 f_divs(u32 n, u32 d, int*ov){ int dv=(short)d; if(!dv) stop("div0"); long long nn=(int)n; long long q=nn/dv; if(q>32767||q<-32768){*ov=1;return n;} return ((u32)((nn%dv)&0xffff)<<16)|(u32)(q&0xffff); }
u32 f_roxl(u32 o,int n,int w,int*x){ int left=w>0; if(!left)w=-w; u32 m=w==32?0xffffffffu:(1u<<w)-1; n%=(w+1); for(;n>0;n--){ if(left){int c=(o>>(w-1))&1;o=((o<<1)|*x)&m;*x=c;} else {int c=o&1;o=(o>>1)|((u32)*x<<(w-1));*x=c;} } return o&m; }
u32 f_abcd(u32 d,u32 s,int*x){ u32 r=(s&15)+(d&15)+*x; if(r>9) r+=6; r+=(s&0xf0)+(d&0xf0); *x=r>0x99; if(*x) r-=0xa0; return r&0xff; }
u32 f_sbcd(u32 d,u32 s,int*x){ u32 r=(d&15)-(s&15)-*x; if(r>9) r-=6; r+=(d&0xf0)-(s&0xf0); *x=r>0x99; if(*x) r+=0xa0; return r&0xff; }
u32 IOR8(u32 a){return 0;} u32 IOR16(u32 a){return 0;} u32 IOR32(u32 a){return 0;} void IOW8(u32 a,u32 v){} void IOW16(u32 a,u32 v){} void IOW32(u32 a,u32 v){}
typedef void (*VF)(void);
extern const struct { u32 a; VF f; } ITAB[];
int main(int c, char **v)
{
    FILE *rf = fopen(v[1], "rb"), *rom = fopen(v[2], "rb"), *cf = fopen(v[3], "r");
    u32 addr; int i, n = 0;
    (void)c;
    if (!rf || !rom || !cf) return 2;
    fread(RAM0, 1, sizeof RAM0, rf); fread(ROMB, 1, sizeof ROMB, rom);
    for (i = 0; i < 256; i++) PAGE[i] = ZERO[i];
    for (i = 0; i < 0x20; i++) PAGE[i] = ROMB + ((u32)i << 16);
    PAGE[0xff] = RAMB;
    while (fscanf(cf, "%x", &addr) == 1) {
        u32 fl; VF fn = 0; volatile int done = 0;
        for (i = 0; i < 8; i++) fscanf(cf, "%x", &cpu.d[i]);
        for (i = 0; i < 8; i++) fscanf(cf, "%x", &cpu.a[i]);
        fscanf(cf, "%u", &fl);
        for (i = 0; ITAB[i].f; i++) if (ITAB[i].a == addr) { fn = ITAB[i].f; break; }
        memcpy(RAMB, RAM0, sizeof RAMB);
        cpu.ccc = fl & 1; cpu.ccv = (fl >> 1) & 1; cpu.ccz = (fl >> 2) & 1; cpu.ccn = (fl >> 3) & 1; cpu.ccx = (fl >> 4) & 1;
        why = "ok";
        if (!setjmp(jb)) { fn(); done = 1; }
        (void)done;
        printf("%s ", why);
        for (i = 0; i < 8; i++) printf("%x ", cpu.d[i]);
        for (i = 0; i < 8; i++) printf("%x ", cpu.a[i]);
        printf("%d |", (!!cpu.ccc) | (!!cpu.ccv << 1) | (!!cpu.ccz << 2) | (!!cpu.ccn << 3) | (!!cpu.ccx << 4));
        { u32 k; for (k = 0; k < 0x10000; k++) if (RAMB[k] != RAM0[k]) printf(" %x:%x", 0xff0000 + k, RAMB[k]); }
        printf("\n");
        n++;
    }
    return 0;
}
