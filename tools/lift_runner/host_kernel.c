/* Host runner: the lifted game on a PC with no emulator core. Native cooperative kernel over ucontext, the game's own task
   records stay in work RAM at their original offsets because the game reads them. Inputs, EEPROM and sound status come from a
   recorded I/O stream (diagnostic adapter). Each vblank compares work RAM and object RAM with the MAME golden dump.
   usage: lift_runner ROM GOLDEN IOTXT [maxvblanks] [maskfile]    Tier: HOST against MAME. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ucontext.h>
#include <execinfo.h>
#include <unistd.h>
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct { u32 d[8]; u32 a[8]; u32 ccz, ccn, ccc, ccv, ccx; } Cpu;
static Cpu cpu;
Cpu *R = &cpu;
u8 *PAGE[256];
u8 RAMB[0x10000];
u8 ROMB[0x200000]; u8 OPSPACE[0x200000]; u8 *OPB=OPSPACE;
static u8 ZERO[256][0x10000];
#define TASKS 16
#define REC(i) (0xff0058u + (u32)(i) * 0x20u)
#define O(a) ((a) - 0xff0000u)
static u32 r32(u32 a){u8*p=RAMB+O(a);return ((u32)p[0]<<24)|(p[1]<<16)|(p[2]<<8)|p[3];}
static u32 r16(u32 a){u8*p=RAMB+O(a);return (p[0]<<8)|p[1];}
static void w32(u32 a,u32 v){u8*p=RAMB+O(a);p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void w16(u32 a,u32 v){u8*p=RAMB+O(a);p[0]=v>>8;p[1]=v;}
static void w8(u32 a,u32 v){RAMB[O(a)]=v;}
static u32 r8(u32 a){return RAMB[O(a)];}
#define G_CUR 0xff025cu
#define G_FREEP 0xff0260u
#define G_FREEN 0xff0264u
#define G_VFLAG 0xff0266u

typedef struct { ucontext_t uc; Cpu regs; char *stack; int live; } Task;
static Task T[TASKS];
static ucontext_t sched;
static int cur = -1;
#define STK (512 * 1024)
extern void f_dispatch(u32);
extern void f_e0e(void);
extern void f_800(void);

/* I/O replay */
typedef struct { u32 addr, val; } IoRead;
static IoRead *io; static long ion, iop; static long *vstart; static long vn; static long curv;
static u32 ioval[0x20000];
static u32 ioidx(u32 a){ return ((a>>16)==0x80?0:0x10000)+(a&0xffff); }
static void io_load(const char *p){ FILE*f=fopen(p,"r"); char l[64]; long cap=1<<20; io=malloc(cap*sizeof*io); vstart=malloc(sizeof(long)*2000000); vstart[vn++]=0;
    while(fgets(l,64,f)){ if(l[0]=='V'){vstart[vn++]=ion;continue;} u32 a,d,m; if(sscanf(l,"%x %x %x",&a,&d,&m)==3){ if(ion==cap){cap*=2;io=realloc(io,cap*sizeof*io);} if((a>>16)==0x61&&(a&0xfff000)!=0x618000&&0) continue; io[ion].addr=a; io[ion].val=d; ion++; } } vstart[vn]=ion; fclose(f); }
/* PADSCRIPT=file: after player 1 first stands free in a stage (state 02 00 00, once vblank >= PADFROM), the pad word at 0x804000 (player 1 byte, active low) is replaced by a script:
   whitespace separated MASK:FRAMES tokens (MASK hex, active high: 01 right, 02 left, 04 down, 08 up, 10 gun, 20 attack, 40 jump). When the script ends the pad is released. HOST. */
static u8 *ps_mask; static long ps_n, ps_len; static long ps_start=-1; static int ps_on; static long ps_from;
static void ps_load(void){ const char*e=getenv("PADSCRIPT"); FILE*f; char tok[64]; if(!e) return; f=fopen(e,"r"); if(!f) exit(9); ps_mask=malloc(1<<20); while(fscanf(f,"%63s",tok)==1){ unsigned m=0; long n=1; sscanf(tok,"%x:%ld",&m,&n); while(n-->0&&ps_len<(1<<20)) ps_mask[ps_len++]=(u8)m; } fclose(f); ps_on=1; ps_from=getenv("PADFROM")?atol(getenv("PADFROM")):0; }
static int ps_active(void){ if(!ps_on) return 0; if(ps_start<0){ if(curv>=ps_from&&RAMB[0x8380]==1&&RAMB[0x8384]==2&&RAMB[0x8385]==0&&RAMB[0x8386]==0) ps_start=curv; else return 0; } return 1; }
static u32 ps_word(void){ long i=curv-ps_start; u32 m=i<ps_len?ps_mask[i]:0; return 0xff00u|((~m)&0xffu); }
static u32 io_read(u32 a){ a&=0xfffffe; if(a==0x804000u&&ps_active()) return ps_word();  long i; long end=(curv+1<vn)?vstart[curv+1]:ion; for(i=iop;i<end;i++){ if(io[i].addr==a){ iop=i+1; ioval[ioidx(a)]=io[i].val; return io[i].val; } } return ioval[ioidx(a)]; }
u32 IOR8(u32 a){ u32 v=io_read(a); return (a&1)?(v&0xff):(v>>8); }
u32 IOR16(u32 a){ return io_read(a)&0xffff; }
u32 IOR32(u32 a){ return (io_read(a)<<16)|io_read(a+2); }
static u8 OBJB[2][0x10000]; u8 *OBJ_CUR=OBJB[0];
void IOW8(u32 a,u32 v){(void)a;(void)v;} void IOW16(u32 a,u32 v){ if(a==0x8040e0){ OBJ_CUR=OBJB[v&1]; PAGE[0x70]=OBJ_CUR; } } void IOW32(u32 a,u32 v){(void)a;(void)v;}

u32 f_divu(u32 n,u32 d,int*ov){ d&=0xffff; if(!d) return n; u32 q=n/d; if(q>0xffff){*ov=1;return n;} return ((n%d)<<16)|q; }
u32 f_divs(u32 n,u32 d,int*ov){ int dv=(short)d; if(!dv) return n; long long nn=(int)n; long long q=nn/dv; if(q>32767||q<-32768){*ov=1;return n;} return ((u32)((nn%dv)&0xffff)<<16)|(u32)(q&0xffff); }
u32 f_roxl(u32 o,int n,int w,int*x){ int left=w>0; if(!left)w=-w; u32 m=w==32?0xffffffffu:(1u<<w)-1; n%=(w+1); for(;n>0;n--){ if(left){int c=(o>>(w-1))&1;o=((o<<1)|*x)&m;*x=c;} else {int c=o&1;o=(o>>1)|((u32)*x<<(w-1));*x=c;} } return o&m; }
u32 f_abcd(u32 d,u32 s,int*x){ u32 r=(s&15)+(d&15)+*x; if(r>9) r+=6; r+=(s&0xf0)+(d&0xf0); *x=r>0x99; if(*x) r-=0xa0; return r&0xff; }
u32 f_sbcd(u32 d,u32 s,int*x){ u32 r=(d&15)-(s&15)-*x; if(r>9) r-=6; r+=(d&0xf0)-(s&0xf0); *x=r>0x99; if(*x) r+=0xa0; return r&0xff; }
void f_badjump(u32 a){ printf("d0 %x d1 %x a6 %x cur %d ",cpu.d[0],cpu.d[1],cpu.a[6],cur); { u32 a4=cpu.a[4]; u8*q=PAGE[(a4>>16)&0xff]+(a4&0xffff); u32 rec=(u32)q[0x1c]<<24|q[0x1d]<<16|q[0x1e]<<8|q[0x1f]; u8*r=PAGE[(rec>>16)&0xff]+(rec&0xffff); { int k; u32 a4=cpu.a[4]; u8*q=PAGE[(a4>>16)&0xff]+(a4&0xffff); printf("blk"); for(k=0;k<0x30;k++) printf("%s%02x",k%4?"":" ",q[k]); printf(" "); } printf("p30 %p b166 %02x%02x%02x%02x ",(void*)PAGE[0x30],PAGE[0x30][0x166],PAGE[0x30][0x167],PAGE[0x30][0x168],PAGE[0x30][0x169]); printf("a0 %x a4 %x rec %x asm %02x%02x%02x%02x ",cpu.a[0],a4,rec,r[4],r[5],r[6],r[7]); } printf("BADJUMP at %x vblank %ld\n",a,curv); fflush(stdout); exit(3); }
void f_sysreg(void){}
void f_unhandled(u32 a){ printf("UNHANDLED at %x vblank %ld\n",a,curv); fflush(stdout); exit(3); }
#include "dispatch.inc"
void f_dispatch(u32 a){ VF f=lookup(a); if(!f){ void*bt[12]; int nb=backtrace(bt,12); fflush(stdout); backtrace_symbols_fd(bt,nb,1); printf("regs a0 %x a1 %x a2 %x a3 %x a4 %x a6 %x a7 %x\n",cpu.a[0],cpu.a[1],cpu.a[2],cpu.a[3],cpu.a[4],cpu.a[6],cpu.a[7]); printf("NOFN %x vblank %ld task %d\n",a,curv,cur); fflush(stdout); exit(3);} f(); }

/* The board's kernel saves no registers for a task: only SR, PC and USP. d0-d7/a0-a6 carry over between tasks, and wrappers like 0x1060 save what they need on the task's own stack. */
static void to_sched(void){ int me=cur; T[me].regs.a[7]=cpu.a[7]; swapcontext(&T[me].uc,&sched); cpu.a[7]=T[me].regs.a[7]; cpu.a[1]=cpu.a[7]; cpu.a[0]=REC(me); }
static void task_tramp(void){ int me=cur; f_dispatch(r32(REC(me)+4)); printf("task %d returned, vblank %ld\n",me,curv); exit(3); }
/* Traps */
static void tg(void);
void f_trap0(void){ tg(); u32 r=0xff0058u+(cpu.d[0]&0xffff); cpu.a[1]=0xff0058u; if(r8(r)==0){ w16(r,0xc00); w32(r+4,cpu.a[0]); w16(r+0x10,cpu.d[1]); w16(r+0x12,cpu.d[2]); } tg(); }
void f_trap10(void){ tg(); u32 r=0xff0058u+(cpu.d[0]&0xffff); cpu.a[1]=0xff0058u; w16(r,0xc00); w32(r+4,cpu.a[0]); w16(r+0x10,cpu.d[1]); w16(r+0x12,cpu.d[2]); tg(); }
void f_trap7(void){ tg(); if(r16(G_FREEN)){ u32 p=r32(G_FREEP); u32 r=r32(p); cpu.a[6]=p+4; cpu.a[1]=r; w32(G_FREEP,p+4); w16(G_FREEN,r16(G_FREEN)-1); w16(r,0xc00); w32(r+4,cpu.a[0]); w16(r+0x10,cpu.d[0]); w16(r+0x12,cpu.d[1]); } tg(); }
/* The board clears these one long at a time and an IRQ can land between them (seen at 0xf66). */
static void clear_rec(u32 r){ w32(r+0x10,0); tg(); w32(r+0x14,0); tg(); w32(r+0x18,0); tg(); w32(r+0x1c,0); tg(); w8(r,0); }
static void task_end(void){ int me=cur; T[me].live=0; setcontext(&sched); (void)me; }
void f_trap1(void){ tg(); clear_rec(REC(cur)); task_end(); }
void f_trap9(void){ tg(); u32 r=REC(cur); clear_rec(r); u32 p=r32(G_FREEP)-4; w32(p,r); w32(G_FREEP,p); w16(G_FREEN,r16(G_FREEN)+1); task_end(); }
void f_trap2(void){ tg(); u32 off=cpu.d[0]&0xffff; u32 r=0xff0058u+off; cpu.a[4]=0xff0058u; if(r8(r)){ cpu.d[1]=0; clear_rec(r); T[off/0x20].live=0; } tg(); }

void f_trap3(void){ tg(); u32 r=REC(cur); u32 bit=(cpu.d[0]&0xff)?0x100:0x200; u32 v=(cpu.d[0]&0xffff)|bit; cpu.d[1]=(cpu.d[1]&0xffff0000u)|bit; cpu.d[0]=(cpu.d[0]&0xffff0000u)|v; w16(r,v); w32(r+8,cpu.a[7]); tg(); to_sched(); }
void f_trap4(void){ tg(); u32 r=REC(cur); w8(r,4); w32(r+8,cpu.a[7]); tg(); to_sched(); }
void f_trap5(void){ tg(); u32 r=0xff0058u+(cpu.d[0]&0xffff); w8(r,2); w8(r+1,0); cpu.a[4]=0xff0058u; tg(); }
void f_trap6(void){ tg(); u32 r=0xff0058u+(cpu.d[0]&0xffff); w8(r,4); w8(r+1,cpu.d[1]); cpu.a[4]=0xff0058u; tg(); }
/* Board 0xfde: the first live record of the eight with tag d1 only, then rte. a4, d7, d0 and a6 stay as it leaves them. */
void f_trap8(void){ tg(); w8(0xff81b3,0); { u32 a4=REC(8); int n=7; cpu.d[7]=(cpu.d[7]&0xffff0000u)|7; for(;;){ if(r8(a4)&&r8(a4+0x16)==(cpu.d[1]&0xff)){ int i=8+7-n; cpu.d[0]=0; clear_rec(a4); T[i].live=0; { u32 p=r32(G_FREEP)-4; w32(p,a4); w32(G_FREEP,p); w16(G_FREEN,r16(G_FREEN)+1); cpu.a[6]=p; } break; } a4+=0x20; if(--n<0){ cpu.d[7]|=0xffff; break; } cpu.d[7]=(cpu.d[7]&0xffff0000u)|n; } cpu.a[4]=a4; } tg(); }
/* Board 0x1026: end every live record of the eight. */
void f_trap11(void){ tg(); { u32 a4=REC(8); int i; for(i=8;i<16;i++,a4+=0x20){ if(r8(a4)){ cpu.d[0]=0; clear_rec(a4); T[i].live=0; { u32 p=r32(G_FREEP)-4; w32(p,a4); w32(G_FREEP,p); w16(G_FREEN,r16(G_FREEN)+1); cpu.a[6]=p; } } } cpu.a[4]=a4; cpu.d[7]|=0xffff; } tg(); } void f_trap12(void){} void f_trap13(void){} void f_trap14(void){} void f_trap15(void){}

/* Whole-game comparison */
static FILE *gold; static u8 grec[8+64+0x10000+0x2000]; static u8 *gbuf=grec+64; static u8 cur_ip[64]; static int have_next;
static u8 mask[0x10000];
long host_vblank;
static long firstdiv=-1, ndiv, nclean;
static long maxv=1L<<40;
static u32 be(u8*p){return ((u32)p[0]<<24)|(p[1]<<16)|(p[2]<<8)|p[3];}
/* Golden stream, read forward only with one record of lookahead. Full records, or LEARN_DELTA records (only changed words; every IRQ still has one). */
static u8 la[8+64+0x12000]; static int la_ok, g_delta; static u8 g_state[0x12000];
static int gold_fetch(void){ if(la_ok) return 1; if(!g_delta){ if(fread(la,1,sizeof la,gold)!=sizeof la) return 0; la_ok=1; return 1; }
    u8 n[4]; if(fread(la,1,72,gold)!=72||fread(n,1,4,gold)!=4) return 0; { u32 r=be(n),k; for(k=0;k<r;k++){ u8 h[4]; if(fread(h,1,4,gold)!=4) return 0; { u32 w=(h[0]<<8)|h[1], c=(h[2]<<8)|h[3]; if(fread(g_state+w*4,4,c,gold)!=c) return 0; } } } memcpy(la+72,g_state,0x12000); la_ok=1; return 1; }
static int golden_next(void){ if(!gold_fetch()) return 0; memcpy(grec,la,sizeof grec); la_ok=0; memcpy(grec+64,grec,8); return 1; }
/* PDUMP=file: per vblank, both players' 256-byte blocks (ff8380, ff8480) and a hash of each outbound region (collision lists ff1800..ff1fff, effect spawns ff8600..ff8aff, globals ff7f00..ff82ff,
   enemy and object blocks ff9a00..ffc6ff, projectile pool ffdd00..ffe2ff). The Wolverine native lane (tools/wolverine/fielddiff.py) compares two such dumps. HOST. */
static FILE *pdump; static int pdump_init;
static u32 fnv(const u8 *p, long n){ u32 h=2166136261u; while(n-->0){ h^=*p++; h*=16777619u; } return h; }
/* EDUMP=file: per vblank, the 46 object blocks ff9a00..ffc5ff (stride 0x100): active byte, tag (+8), health word (+0x40) - 4 bytes each. Damage is read as HP lost. */
static FILE *edump; static int edump_init;
static void edump_frame(void){ if(!edump_init){ const char *e=getenv("EDUMP"); edump_init=1; if(e) edump=fopen(e,"wb"); } if(!edump) return; { int k; u8 o[46*4]; for(k=0;k<46;k++){ const u8 *b=RAMB+0x9a00+k*0x100; o[k*4]=b[0]; o[k*4+1]=b[8]; o[k*4+2]=b[0x40]; o[k*4+3]=b[0x41]; } fwrite(o,1,sizeof o,edump); } }
static void pdump_frame(void){ if(!pdump_init){ const char *e=getenv("PDUMP"); pdump_init=1; if(e) pdump=fopen(e,"wb"); } if(!pdump) return; fwrite(RAMB+0x8380,1,512,pdump);
    { u32 h[5]; h[0]=fnv(RAMB+0x1800,0x800); h[1]=fnv(RAMB+0x8600,0x500); h[2]=fnv(RAMB+0x7f00,0x400); h[3]=fnv(RAMB+0x9a00,0x2d00); h[4]=fnv(RAMB+0xdd00,0x600); fwrite(h,4,5,pdump); } }
static void lastd_set(long d); static long midrun; static void compare_inner(void){ long i,d=0; pdump_frame(); edump_frame(); long first=-1; for(i=0;i<0x10000;i++) if(!mask[i]&&RAMB[i]!=gbuf[8+i]){ if(first<0) first=i; d++; }
    long od=0; for(i=0;i<0x2000;i++) if(OBJ_CUR[0x8000+i]!=gbuf[8+0x10000+i]) od++;
    if(od&&getenv("OBJPAGE")){ u8*op=OBJB[OBJ_CUR==OBJB[0]?1:0]; long o2=0; for(i=0;i<0x2000;i++) if(op[0x8000+i]!=gbuf[8+0x10000+i]) o2++; { long hi=0,z=-1; for(i=0;i<0x2000;i++) if(OBJ_CUR[0x8000+i]!=gbuf[8+0x10000+i]){ if(z<0) z=i; hi=i; } printf("objpage v%ld cur %d diffs %ld other %ld first %lx last %lx%c",curv,OBJ_CUR==OBJB[1],od,o2,z,hi,10);} } if(od&&getenv("OBJDBG")){ for(i=0;i<0x2000;i++) if(OBJ_CUR[0x8000+i]!=gbuf[8+0x10000+i]){ printf(" obj %lx:%02x/%02x",i,OBJ_CUR[0x8000+i],gbuf[8+0x10000+i]); if(i>64)break; } printf("\n"); } lastd_set(d); if(d||od){ ndiv++; if(ndiv<=40||firstdiv<0){ printf("vblank %ld: ram diffs %ld first %lx (host %02x mame %02x) obj diffs %ld\n",curv,d,first<0?0:0xff0000+first,first<0?0:RAMB[first],first<0?0:gbuf[8+first],od); { long k,sh=0; for(k=first;k>=0&&k<0x10000&&sh<12;k++) if(!mask[k]&&RAMB[k]!=gbuf[8+k]){ printf(" %lx:%02x/%02x",0xff0000+k,RAMB[k],gbuf[8+k]); sh++; } printf("\n"); } fflush(stdout);} if(firstdiv<0) firstdiv=curv; if(getenv("STOP_DIV")&&ndiv>=atoi(getenv("STOP_DIV"))){ printf("stop\n"); exit(0);} } else nclean++; }
/* Relocation run (host_reloc.c): a 32-bit word in the window 0x2d0000..0x2dffff of work RAM is a named pointer-address change; the compare and the dumps see it minus the delta. */
extern unsigned wv_anim_delta __attribute__((weak)); static void rn_fix(const u8*g); static u8 ram_keep[0x10000];
static void compare(void){ if(&wv_anim_delta&&wv_anim_delta){ memcpy(ram_keep,RAMB,0x10000); rn_fix(gbuf+8); compare_inner(); memcpy(RAMB,ram_keep,0x10000); } else compare_inner(); }

static void run_irq(void){ Cpu save=cpu; int sc=cur; u32 sr=r32(G_CUR); cur=-1; cpu.a[5]=0xff8000; cpu.a[7]=0xff8000; f_e0e(); cpu=save; cur=sc; (void)sr; }

/* Exact preemption: MAME recorded where each IRQ landed (stacked PC, d0-d7, a0-a6). The lifted code checks that PC before each
   instruction, and the IRQ is taken when the registers match too. Stack pointer is left out: lifted calls push no return addresses. */
u32 irq_pc=0xffffffffu; static u32 ipr[15]; static long nmatch, nkern, nmiss; static long nregmiss; static int in_irq;
static int want19; static u8 nrec[8+64+0x10000]; static int freerun; /* FREERUN=1: no IRQ placement from the golden; one IRQ per frame once every task has blocked. Pad and I/O still replay by vblank. For runs that change game timing (the golden no longer matches). */
static int peek_ip(void){ u8*h=nrec; if(!gold_fetch()) return 0; memcpy(nrec,la,sizeof nrec); want19=nrec[72+0x8019]; irq_pc=freerun?0xffffffffu:be(h+8); for(int i=0;i<15;i++) ipr[i]=be(h+12+i*4); return 1; }
/* Kernel points carry little register state (a whole dispatcher pass can look like the last), so an IRQ there lands when work RAM equals the next dump. A real divergence never matches and is reported as a miss. */
static int seg[4096][2], nseg; static void seg_build(void){ int i=0; while(i<0x10000){ if(mask[i]){i++;continue;} int b=i; while(i<0x10000&&!mask[i]) i++; seg[nseg][0]=b; seg[nseg++][1]=i-b; } }
static int state_eq_raw(void){ int k; if(irq_pc==0xffffffffu) return 0; for(k=0;k<nseg;k++) if(memcmp(RAMB+seg[k][0],nrec+72+seg[k][0],seg[k][1])) return 0; return 1; }
/* Relocation run (host_reloc.c): a long of work RAM that is the golden long plus the relocation delta, inside Schaefer's table and record range, is a named pointer-address change: the compare sees it minus the delta. */
extern unsigned wv_anim_delta __attribute__((weak)); static u8 rn_keep[0x10000];
static void rn_fix(const u8*g){ long k; for(k=0;k+4<=0x10000;k+=2){ u32 v=(u32)RAMB[k]<<24|RAMB[k+1]<<16|RAMB[k+2]<<8|RAMB[k+3], q=(u32)g[k]<<24|g[k+1]<<16|g[k+2]<<8|g[k+3]; if(v!=q&&v-wv_anim_delta==q&&q>=0x162f90u&&q<0x167600u){ RAMB[k]=(u8)(q>>24); RAMB[k+1]=(u8)(q>>16); RAMB[k+2]=(u8)(q>>8); RAMB[k+3]=(u8)q; k+=2; } } }
static int state_eq(void){ int r=state_eq_raw(); if(r||!(&wv_anim_delta&&wv_anim_delta)||irq_pc==0xffffffffu) return r; memcpy(rn_keep,RAMB,0x10000); rn_fix(nrec+72); r=state_eq_raw(); memcpy(RAMB,rn_keep,0x10000); return r; }
/* A loop that writes only object RAM looks the same on each pass, so the object list decides too. */
static int obj_eq(void){ return !memcmp(OBJ_CUR+0x8000,la+72+0x10000,0x2000); }
/* CENS=1: objects written per frame, split by the actor pool a4 points into when a1 moved through the object page. Finds the frame with the most tiles. */
static int cs_on; static u32 cs_a1; static unsigned char cs_owner[0x400]; static long cs_best; static long cs_split[6]; static long cs_frame;
static int cs_class(u32 a){ a&=0xffffff; if(a>=0xff8380&&a<0xff8680) return 0; if(a>=0xff9580&&a<0xffa980) return 1; if(a>=0xffb680&&a<0xffc680) return 2; if(a>=0xffd280&&a<0xffe280) return 3; return 4; }
static void cs_step(void){ u32 x=cpu.a[1]; if(x!=cs_a1&&(x>>16&0xff)==0x70&&x>cs_a1&&(x-cs_a1)<=8&&(cs_a1>>16&0xff)==0x70){ u32 n=(cs_a1&0x1fff)/8; if(n<0x400) cs_owner[n]=(unsigned char)cs_class(cpu.a[4]); } cs_a1=x; }
static void cs_frame_end(void){ long s[6]={0,0,0,0,0,0},t=0; int n; const u8*l=OBJ_CUR+0x8000; for(n=0;n<0x400;n++){ const u8*o=l+n*8; int y=(o[2]<<8)|o[3], at=(o[6]<<8)|o[7]; if(y>=0x8000||at>=0xff00) break; { int k=(((at>>8)&15)+1)*(((at>>12)&15)+1); s[cs_owner[n]]+=k; t+=k; } } if(t>cs_best){ cs_best=t; cs_frame=curv; memcpy(cs_split,s,sizeof s); } }
/* PROF=out.tsv[,from,to]: count executed 68000 instructions by address over a dump window, for tools/lift_profile.py. HOST instruction counts, not time. */
static unsigned long long *pf_n; static long pf_from, pf_to=1L<<40; static const char *pf_out;
static void prof_write(void){ FILE*f; u32 a; if(!pf_n) return; f=fopen(pf_out,"w"); for(a=0;a<0x200000;a++) if(pf_n[a]) fprintf(f,"%x %llu%c",a,pf_n[a],10); fclose(f); }
extern long game_bind_native __attribute__((weak)), game_bind_fallbacks __attribute__((weak));
extern unsigned sat_wv_fork_calls[] __attribute__((weak));
static void finish(const char*why){ prof_write(); if(ps_on) printf("padscript start vblank %ld len %ld%c",ps_start,ps_len,10); if(pdump) fclose(pdump); if(edump) fclose(edump); if(sat_wv_fork_calls){ int k; printf("fork entries:"); for(k=0;k<9;k++) printf(" %d:%u",k,sat_wv_fork_calls[k]); printf("%c",10); } if(cs_on) printf("CENS frame %ld tiles %ld: pool8380 %ld pool9580 %ld poolb680 %ld poold280 %ld other %ld%c",cs_frame,cs_best,cs_split[0],cs_split[1],cs_split[2],cs_split[3],cs_split[4],10); if(&game_bind_native) printf("readable routines: native calls %ld, lifted for an IRQ inside %ld%c",game_bind_native,game_bind_fallbacks,10);  printf("%s vblank %ld: clean %ld diff %ld first divergence %ld | irq at instruction %ld, in kernel %ld, missed %ld\n",why,curv,nclean,ndiv,firstdiv,nmatch,nkern,nmiss); fflush(stdout); exit(0); }
/* ROUNDS_SWAP=file: per-stage page keeping (tools/rounds_hostcheck.py). Garbage in every ROM page the stage's file does not keep, chosen the way kernel.c round_check picks its file. Lines: stage count page... */
/* ROUNDS_SWAP_TAG=1: the garbage names its page: every word of dropped page P reads 0xA000|P (P = address / 0x400). A bad jump, bad pointer or wrong value that reads Axxx then names the dropped page (address P*0x400). */
#define SW_PAGE 0x400
/* ROUNDS_SWAP_TRAP=1: a read watch on dropped pages. ROM reads through PAGE[] go to a 4 KB-aligned copy; each host page whose four ROM pages are all dropped
   is made unreadable, and the fault prints the ROM address, its page and the last 68000 instruction. Reads through ROM8/16/32 (ROMB direct) and dropped pages
   that share a host page with a kept one are not watched. */
#include <sys/mman.h>
static u8 *trap_rom; static int trap_on; static volatile u32 trap_pc;
extern u8 *PAGE[256];
static void trap_protect(int *drop, int n){ static u8 dropped[0x800]; int i,h; mprotect(trap_rom,0x200000,PROT_READ|PROT_WRITE); memcpy(trap_rom,ROMB,0x200000); for(i=0;i<0x20;i++) PAGE[i]=trap_rom+((u32)i<<16); memset(dropped,0,sizeof dropped); for(i=0;i<n;i++) dropped[drop[i]&0x7ff]=1; for(h=0;h<0x200;h++) if(dropped[h*4]&&dropped[h*4+1]&&dropped[h*4+2]&&dropped[h*4+3]) mprotect(trap_rom+h*0x1000,0x1000,PROT_NONE); }
static u8 sw_rom[0x200000]; static int *sw_pages[256]; static int sw_n[256]; static int sw_on, sw_cur=-1, sw_tries; static long sw_loads;
static void sw_load(void){ const char*e=getenv("ROUNDS_SWAP"); FILE*f; int st,n,i; if(!e) return; f=fopen(e,"r"); if(!f) exit(9); while(fscanf(f,"%d %d",&st,&n)==2){ sw_pages[st]=malloc(sizeof(int)*(n+1)); sw_n[st]=n; for(i=0;i<n;i++) fscanf(f,"%d",&sw_pages[st][i]); } fclose(f); memcpy(sw_rom,ROMB,0x200000); sw_on=1; }
static void sw_check(void){ int want,i; static int init; if(!init){ init=1; sw_load(); } if(!sw_on) return; want=(RAMB[0x81b0]||RAMB[0x8001]!=2)?0:((RAMB[0x81e8]<<8|RAMB[0x81e9])&255); if(!sw_pages[want]){ printf("SWAP no file for stage %x vblank %ld\n",want,curv); return; } if(want==sw_cur){ sw_tries=0; return; } if(++sw_tries<12) return; sw_tries=0; memcpy(ROMB,sw_rom,0x200000); { static int tag=-1; if(tag<0) tag=getenv("ROUNDS_SWAP_TAG")!=0; for(i=0;i<sw_n[want];i++){ int pg=sw_pages[want][i],k; if(!tag) memset(ROMB+pg*SW_PAGE,0xA5,SW_PAGE); else for(k=0;k<SW_PAGE;k+=2){ u16 w=(u16)(0xA000|(pg&0x7ff)); ROMB[pg*SW_PAGE+k]=(u8)(w>>8); ROMB[pg*SW_PAGE+k+1]=(u8)w; } } } if(trap_on) trap_protect(sw_pages[want],sw_n[want]); sw_cur=want; sw_loads++; printf("SWAP stage %x vblank %ld loads %ld\n",want,curv,sw_loads); fflush(stdout); }
/* HOST_WARP=hex: the home build's start-stage warp (saturn/rt/home.c), for checking a warped stage under ROUNDS_SWAP_TRAP. */
/* POKE="vblank:ffaddr:value[:bytes],..." writes a byte (default) or word/long into work RAM once at the given vblank (free-running scenario runs: low health, forced states). */
static void host_poke(void){ static int n=-1; static long pv[16]; static u32 pa[16]; static u32 pw[16]; static int pb[16]; static char done[16]; int i; if(n<0){ const char*e=getenv("POKE"); n=0; while(e&&*e&&n<16){ long v; unsigned a,w; int b=1; char*q; v=strtol(e,&q,10); if(*q!=':') break; a=strtoul(q+1,&q,16); if(*q!=':') break; w=strtoul(q+1,&q,0); if(*q==':') b=(int)strtol(q+1,&q,10); pv[n]=v; pa[n]=a; pw[n]=w; pb[n]=b; n++; e=(*q==',')?q+1:q; if(*q!=',') break; } } for(i=0;i<n;i++) if(!done[i]&&curv>=pv[i]){ u32 o=pa[i]-0xff0000u; int k; for(k=0;k<pb[i];k++) RAMB[o+k]=(u8)(pw[i]>>(8*(pb[i]-1-k))); done[i]=1; } }
static void host_warp(void){ host_poke(); static long w=-1; static int polls; if(w<0){ char*e=getenv("HOST_WARP"); w=e?strtol(e,0,16):0; } if(!w) return; if(RAMB[0x81b0]) { polls=0; return; } if(polls<120&&(RAMB[0x81e8]<<8|RAMB[0x81e9])==2){ RAMB[0x81e8]=(u8)(w>>8); RAMB[0x81e9]=(u8)w; if(RAMB[0x8380]) polls++; } }
static void take_irq(void){ host_warp(); sw_check(); u32 t=irq_pc; if(cs_on) cs_frame_end(); { char*e=getenv("IRQLOG"); if(e&&curv>=atol(e)&&curv<atol(e)+12) fprintf(stdout,"irq %ld at %x cur %d d0 %x%c",curv,t,cur,cpu.d[0],10); } irq_pc=0xffffffffu; in_irq=1; if(curv>=maxv) finish("end"); if(!golden_next()) finish("golden end"); curv++; host_vblank=curv; iop=vstart[curv<vn?curv:vn-1]; compare(); run_irq(); in_irq=0; (void)t; if(!peek_ip()) finish("golden end"); }
/* Whole walks with only the idle task running and an empty command ring look the same; an IRQ there lands once work has drained. */

/* WATCH=addr[,fromvblank]: print the instruction after each change of a RAM byte: the writer of a divergent field. */
int p_watch; static u32 w_addr; static int w_last=-1; static long w_from; static u32 w_prev;
static u32 tp[8]; static int ntp;
static void watch_step(u32 a){ for(int k=0;k<ntp;k++) if(a==tp[k]&&curv>=w_from) { const u8 *bk=(cpu.a[6]>=0xff0000u&&cpu.a[6]<0xffff00u)?RAMB+(cpu.a[6]-0xff0000u):RAMB; printf("T v%ld pc %x d0 %x d1 %x d2 %x d5 %x d6 %x a4 %x a6 %x a0 %x st %02x%02x%02x ch %02x tag %02x rec %02x%02x%02x%02x%c",curv,a,cpu.d[0],cpu.d[1],cpu.d[2],cpu.d[5],cpu.d[6],cpu.a[4],cpu.a[6],cpu.a[0],bk[4],bk[5],bk[6],bk[0xd2],bk[8],bk[0x1c],bk[0x1d],bk[0x1e],bk[0x1f],10); } if(curv<w_from) { w_last=RAMB[w_addr]; w_prev=a; return; } int v=RAMB[w_addr]; if(v!=w_last){ printf("W v%ld %x: %02x->%02x after %x next %x cur %d d0 %x d1 %x d2 %x a0 %x a6 %x%c",curv,0xff0000+w_addr,w_last,v,w_prev,a,cur,cpu.d[0],cpu.d[1],cpu.d[2],cpu.a[0],cpu.a[6],10); w_last=v; } w_prev=a; }
static long lastd; static long ram_diffs_raw(void){ long i,d=0; for(i=0;i<0x10000;i++) if(!mask[i]&&RAMB[i]!=nrec[72+i]) d++; return d; }
static long ram_diffs(void){ long d=ram_diffs_raw(); if(!d||!(&wv_anim_delta&&wv_anim_delta)) return d; memcpy(rn_keep,RAMB,0x10000); rn_fix(nrec+72); d=ram_diffs_raw(); memcpy(RAMB,rn_keep,0x10000); return d; }
static void lastd_set(long d){ lastd=d; }
/* Relocation run: a register holding a relocated table base or record pointer matches the golden register minus the delta (a named pointer-address change). */
extern unsigned wv_anim_delta __attribute__((weak)); static int regne(u32 v,u32 g){ return v!=g&&!(&wv_anim_delta&&wv_anim_delta&&v-wv_anim_delta==g); }
void irq_check(u32 a){ int i; trap_pc=a; { static int bt_pc=-2; static long bt_v; static int bt_n; if(bt_pc==-2){ char*e=getenv("BTPC"); bt_pc=e?(int)strtoul(e,0,16):-1; bt_v=getenv("BTV")?atol(getenv("BTV")):0; } if(bt_pc>=0&&a==(u32)bt_pc&&curv==bt_v&&bt_n++<1){ void*bt[24]; int nb=backtrace(bt,24); backtrace_symbols_fd(bt,nb,1); } } if(cs_on) cs_step(); if(trap_on&&!w_addr){} else if(pf_n){ if(curv>=pf_from&&curv<pf_to&&a<0x200000) pf_n[a]++; } else if(p_watch) watch_step(a); if(a!=irq_pc) return; if(in_irq) return; { static long dv=-2; if(dv==-2){ char*e=getenv("IRQDBG"); dv=e?atol(e):-1; } if(curv==dv){ static int ndb; if(ndb++<12){ int k; printf("dbg pc %x cur %d f19 %x/%x eq %d obj %d",a,cur,r8(0xff8019),want19,state_eq(),obj_eq()); { int sg,q,nd=0; for(sg=0;sg<nseg&&nd<8;sg++) for(q=0;q<seg[sg][1]&&nd<8;q++) if(RAMB[seg[sg][0]+q]!=nrec[72+seg[sg][0]+q]){ printf(" ram %x:%02x/%02x",0xff0000+seg[sg][0]+q,RAMB[seg[sg][0]+q],nrec[72+seg[sg][0]+q]); nd++; } } for(k=0;k<8;k++) if(cpu.d[k]!=ipr[k]) printf(" d%d %x/%x",k,cpu.d[k],ipr[k]); for(k=0;k<7;k++) if(cpu.a[k]!=ipr[8+k]) printf(" a%d %x/%x",k,cpu.a[k],ipr[8+k]); printf("%c",10);} } } if(r8(0xff8019)!=(u32)want19) return; /* shared wrappers such as 0x1094 run in every task: same PC and RAM, different task */ if(cur>=0&&memcmp(RAMB+0x25c,nrec+72+0x25c,4)) return; /* several ticks in one frame repeat the same PC and registers */ if(cur==6&&!state_eq()) return; if(a>=0x11ec&&a<0x1214&&cur<0){ if(state_eq()){ nkern++; take_irq(); } return; } /* the idle call: dispatcher leftovers in its registers aren't modelled */ { int bad=0; for(i=0;i<8;i++) if(regne(cpu.d[i],ipr[i])) bad++; for(i=0;i<7;i++) if(regne(cpu.a[i],ipr[8+i])) bad++; if(state_eq()&&(obj_eq()||!bad)) goto hit; bad=0; if(!lastd) return; /* same PC, same registers, later pass of a loop: RAM decides while the run is clean */ for(i=0;i<8;i++) if(regne(cpu.d[i],ipr[i])) bad++; for(i=0;i<7;i++) if(regne(cpu.a[i],ipr[8+i])) bad++; if(bad>(getenv("REGBAD")?atoi(getenv("REGBAD")):2)||ram_diffs()>lastd) return; if(bad) nregmiss++; hit:; } nmatch++; take_irq(); }
/* At the dispatcher: the IRQ was in the dispatcher or a trap body (native here), or its point was missed. */
static int kern_pc(u32 p){ return (p>=0xd86&&p<0xdb8)||(p>=0xf00&&p<0x1188); }
/* The IRQ landed in a trap body, native here: same state means same place. */
/* Points of the dispatcher loop itself: only f_d86 takes them, at the record the board's a0 names (tasks after this one may change nothing visible, yet their order counts, as the free stack shows). */
static int disp_loop(u32 p){ return p>=0xd92&&p<0xdb0; }
static int disp_at(int i){ if(irq_pc>=0xda4&&irq_pc<0xdac) return ipr[8]==REC(i); if(irq_pc>=0xdac&&irq_pc<0xdb0) return ipr[8]==REC(i)+0x20; return !disp_loop(irq_pc); }
static void tg(void){ if(!in_irq&&kern_pc(irq_pc)&&!disp_loop(irq_pc)&&state_eq()&&!memcmp(RAMB+0x25c,nrec+72+0x25c,4)){ nkern++; take_irq(); } }
static void start_irq(void){ if(irq_pc>=0xdb8&&irq_pc<0xe0e&&!(irq_pc>=0xddc&&irq_pc<0xde6)&&state_eq()){ nkern++; take_irq(); } } /* between marking the task running and its rte */
static void disp_irq(void){ if(irq_pc==0xffffffffu) return; if(kern_pc(irq_pc)){ nkern++; take_irq(); return; } }
static void idle_irq(void){ if(irq_pc==0xffffffffu) return; if(kern_pc(irq_pc)) nkern++; else { nmiss++; if(nmiss<20){ printf("missed irq at %x vblank %ld\n",irq_pc,curv); fflush(stdout);} } take_irq(); }

static void run_task(int i){ u32 r=REC(i); u32 st=r8(r); cur=i; w32(G_CUR,r);
    if(st==0xc){ w8(r,8); start_irq(); getcontext(&T[i].uc); if(!T[i].stack) T[i].stack=malloc(STK); T[i].uc.uc_stack.ss_sp=T[i].stack; T[i].uc.uc_stack.ss_size=STK; T[i].uc.uc_link=0; cpu.a[7]=r32(r+0xc); cpu.a[4]=r32(r+0xc); cpu.a[1]=r32(r+4); cpu.a[0]=r; cpu.d[1]=(cpu.d[1]&0xffff0000u)|0xc; cpu.a[5]=0xff8000; T[i].live=1; makecontext(&T[i].uc,task_tramp,0); swapcontext(&sched,&T[i].uc); }
    else { w8(r,8); start_irq(); /* board 0xdc8, 0xdea: d1 keeps the state it read, a1 the saved stack; lifted code can read these */ cpu.d[1]=(cpu.d[1]&0xffff0000u)|st; cpu.a[1]=r32(r+8); cpu.a[0]=r; swapcontext(&sched,&T[i].uc); } }
#define GAME_TASK 4
extern void f_11ec(void);
/* Dispatcher 0xd86 as the board runs it. Checks run with the IRQ masked; it opens at 0xda4 after each task. */
void f_d86(void){ getcontext(&sched); peek_ip();
  for(;;){ int i, ran=0; w8(G_VFLAG,0);
    for(i=0;i<TASKS;i++){ if(irq_pc>=0xd92&&irq_pc<0xda4&&ipr[8]==REC(i)&&state_eq()&&!memcmp(RAMB+0x25c,nrec+72+0x25c,4)){ nkern++; take_irq(); } if(r8(G_VFLAG)) break;
        u32 st=r8(REC(i)); cpu.a[0]=REC(i); cpu.d[0]=(cpu.d[0]&0xffff0000u)|(15-i); cpu.d[1]=(cpu.d[1]&0xffffff00u)|st; if(st>=4){ run_task(i); if(i!=6) ran=1; if(irq_pc>=0xddc&&irq_pc<0xde6&&state_eq()){ nkern++; take_irq(); } cpu.a[0]=REC(i); cpu.d[0]=(cpu.d[0]&0xffff0000u)|(15-i); } cur=-1;
        
        if(state_eq()&&!memcmp(RAMB+0x25c,nrec+72+0x25c,4)&&(kern_pc(irq_pc)||(irq_pc>=0xdb8&&irq_pc<0xe0e))&&disp_at(i)){ nkern++; take_irq(); } }
    if(i==TASKS){ cpu.a[0]=REC(15)+0x20; cpu.d[0]|=0xffff; f_11ec(); }
    if(freerun&&!ran){ nkern++; take_irq(); }
    guard: { static long spin; static long last; if(curv==last){ if(++spin>20000){ idle_irq(); spin=0; } } else { last=curv; spin=0; } }
  } }
#include <signal.h>
static char altstk[1<<16];
static void segv(int n,siginfo_t*si,void*uc){ void*bt[14]; (void)uc; if(trap_on&&si&&(u8*)si->si_addr>=trap_rom&&(u8*)si->si_addr<trap_rom+0x200000){ u32 ra=(u32)((u8*)si->si_addr-trap_rom); printf("DROPPED PAGE READ rom %x page %x (stage file %d) at 68k pc %x vblank %ld task %d\n",ra,ra/SW_PAGE,sw_cur,trap_pc,curv,cur); fflush(stdout); _exit(5); } int nb=backtrace(bt,14); printf("SEGV vblank %ld task %d a0 %x a1 %x a6 %x a7 %x\n",curv,cur,cpu.a[0],cpu.a[1],cpu.a[6],cpu.a[7]); fflush(stdout); backtrace_symbols_fd(bt,nb,1); _exit(4); }
int main(int c,char**v){ freerun=getenv("FREERUN")!=0; ps_load(); if(getenv("CENS")){ cs_on=1; p_watch=1; } { char*e=getenv("PROF"); if(e){ static char o[512]; char*q; strncpy(o,e,511); q=strchr(o,','); if(q){ *q=0; sscanf(q+1,"%ld,%ld",&pf_from,&pf_to);} pf_out=o; pf_n=calloc(0x200000,8); p_watch=1; } } { char*e=getenv("WATCH"); if(e){ u32 x; long f=0; sscanf(e,"%x,%ld",&x,&f); w_addr=x-0xff0000; w_from=f; p_watch=1; } e=getenv("TP"); if(e){ char*q=e; while(*q&&ntp<8){ tp[ntp++]=strtoul(q,&q,16); if(*q==',') q++; } } } { stack_t st; st.ss_sp=altstk; st.ss_size=sizeof altstk; st.ss_flags=0; sigaltstack(&st,0); struct sigaction sa; memset(&sa,0,sizeof sa); sa.sa_sigaction=segv; sa.sa_flags=SA_ONSTACK|SA_SIGINFO; sigaction(SIGSEGV,&sa,0);} FILE*rf=fopen(v[1],"rb"); int i; if(!rf||fread(ROMB,1,sizeof ROMB,rf)!=sizeof ROMB) return 2; { char op[512]; strcpy(op,v[1]); strcpy(strrchr(op,'/')+1,"op.bin"); FILE*of=fopen(op,"rb"); if(!of||fread(OPSPACE,1,sizeof OPSPACE,of)!=sizeof OPSPACE) return 2; fclose(of); } gold=fopen(v[2],"rb"); { char*e=strrchr(v[2],'.'); g_delta=getenv("GOLD_DELTA")!=0; if(e&&!strcmp(e,".gz")){ char c2[600]; snprintf(c2,600,"zcat '%s'",v[2]); fclose(gold); gold=popen(c2,"r"); } } io_load(v[3]); if(c>4) maxv=atol(v[4]);
    if(c>5){ FILE*m=fopen(v[5],"r"); char l[64]; while(fgets(l,64,m)){ u32 a,b; if(sscanf(l,"%x %x",&a,&b)==2) for(;a<=b;a++) mask[a-0xff0000]=1; } fclose(m);} seg_build();
    for(i=0;i<256;i++) PAGE[i]=ZERO[i]; for(i=0;i<0x20;i++) PAGE[i]=ROMB+((u32)i<<16); if(getenv("ROUNDS_SWAP_TRAP")){ trap_rom=mmap(0,0x200000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0); trap_on=1; p_watch=1; } PAGE[0xff]=RAMB; PAGE[0x70]=OBJ_CUR; { extern void wv_reloc_init(void) __attribute__((weak)); if(wv_reloc_init) wv_reloc_init(); }
    gold_fetch(); memcpy(grec,la,sizeof grec); memcpy(grec+64,grec,8); /* first record stays unconsumed */ memcpy(OBJB[0]+0x8000,gbuf+8+0x10000,0x2000); memcpy(OBJB[1]+0x8000,gbuf+8+0x10000,0x2000); memcpy(RAMB+0xe90,gbuf+8+0xe90,16); /* what the skipped hardware test left */ curv=0; iop=0; gbuf[8+0x8019]=0;
    cpu.d[3]=4; cpu.a[4]=0x800; /* registers the skipped hardware test left, seen through f_1a36 */ cpu.a[7]=0xff8000; cpu.a[5]=0xff8000; f_800(); printf("boot returned\n"); return 1; }
