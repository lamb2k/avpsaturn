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
static void io_load(const char *p){ FILE*f=fopen(p,"r"); char l[64]; long cap=1<<20; io=malloc(cap*sizeof*io); vstart=malloc(sizeof(long)*200000); vstart[vn++]=0;
    while(fgets(l,64,f)){ if(l[0]=='V'){vstart[vn++]=ion;continue;} u32 a,d,m; if(sscanf(l,"%x %x %x",&a,&d,&m)==3){ if(ion==cap){cap*=2;io=realloc(io,cap*sizeof*io);} if((a>>16)==0x61&&(a&0xfff000)!=0x618000&&0) continue; io[ion].addr=a; io[ion].val=d; ion++; } } vstart[vn]=ion; fclose(f); }
static u32 io_read(u32 a){ a&=0xfffffe; long i; long end=(curv+1<vn)?vstart[curv+1]:ion; for(i=iop;i<end;i++){ if(io[i].addr==a){ iop=i+1; ioval[ioidx(a)]=io[i].val; return io[i].val; } } return ioval[ioidx(a)]; }
u32 IOR8(u32 a){ u32 v=io_read(a); return (a&1)?(v&0xff):(v>>8); }
u32 IOR16(u32 a){ return io_read(a)&0xffff; }
u32 IOR32(u32 a){ return (io_read(a)<<16)|io_read(a+2); }
void IOW8(u32 a,u32 v){(void)a;(void)v;} void IOW16(u32 a,u32 v){(void)a;(void)v;} void IOW32(u32 a,u32 v){(void)a;(void)v;}

u32 f_divu(u32 n,u32 d,int*ov){ d&=0xffff; if(!d) return n; u32 q=n/d; if(q>0xffff){*ov=1;return n;} return ((n%d)<<16)|q; }
u32 f_divs(u32 n,u32 d,int*ov){ int dv=(short)d; if(!dv) return n; long long nn=(int)n; long long q=nn/dv; if(q>32767||q<-32768){*ov=1;return n;} return ((u32)((nn%dv)&0xffff)<<16)|(u32)(q&0xffff); }
u32 f_roxl(u32 o,int n,int w,int*x){ int left=w>0; if(!left)w=-w; u32 m=w==32?0xffffffffu:(1u<<w)-1; n%=(w+1); for(;n>0;n--){ if(left){int c=(o>>(w-1))&1;o=((o<<1)|*x)&m;*x=c;} else {int c=o&1;o=(o>>1)|((u32)*x<<(w-1));*x=c;} } return o&m; }
u32 f_abcd(u32 d,u32 s,int*x){ u32 r=(s&15)+(d&15)+*x; if(r>9) r+=6; r+=(s&0xf0)+(d&0xf0); *x=r>0x99; if(*x) r-=0xa0; return r&0xff; }
u32 f_sbcd(u32 d,u32 s,int*x){ u32 r=(d&15)-(s&15)-*x; if(r>9) r-=6; r+=(d&0xf0)-(s&0xf0); *x=r>0x99; if(*x) r+=0xa0; return r&0xff; }
void f_badjump(u32 a){ printf("d0 %x d1 %x a6 %x cur %d ",cpu.d[0],cpu.d[1],cpu.a[6],cur); printf("BADJUMP at %x vblank %ld\n",a,curv); fflush(stdout); exit(3); }
void f_sysreg(void){}
void f_unhandled(u32 a){ printf("UNHANDLED at %x vblank %ld\n",a,curv); fflush(stdout); exit(3); }
#include "dispatch.inc"
void f_dispatch(u32 a){ VF f=lookup(a); if(!f){ void*bt[12]; int nb=backtrace(bt,12); fflush(stdout); backtrace_symbols_fd(bt,nb,1); printf("regs a0 %x a1 %x a2 %x a3 %x a4 %x a6 %x a7 %x\n",cpu.a[0],cpu.a[1],cpu.a[2],cpu.a[3],cpu.a[4],cpu.a[6],cpu.a[7]); printf("NOFN %x vblank %ld task %d\n",a,curv,cur); fflush(stdout); exit(3);} f(); }

/* The board's kernel saves no registers for a task: only SR, PC and USP. d0-d7/a0-a6 carry over between tasks, and wrappers like 0x1060 save what they need on the task's own stack. */
static void to_sched(void){ int me=cur; T[me].regs.a[7]=cpu.a[7]; swapcontext(&T[me].uc,&sched); cpu.a[7]=T[me].regs.a[7]; cpu.a[1]=cpu.a[7]; cpu.a[0]=REC(me); }
static void task_tramp(void){ int me=cur; f_dispatch(r32(REC(me)+4)); printf("task %d returned, vblank %ld\n",me,curv); exit(3); }
/* Traps */
void f_trap0(void){ u32 r=0xff0058u+(cpu.d[0]&0xffff); cpu.a[1]=0xff0058u; if(r8(r)==0){ w16(r,0xc00); w32(r+4,cpu.a[0]); w16(r+0x10,cpu.d[1]); w16(r+0x12,cpu.d[2]); } }
void f_trap10(void){ u32 r=0xff0058u+(cpu.d[0]&0xffff); cpu.a[1]=0xff0058u; w16(r,0xc00); w32(r+4,cpu.a[0]); w16(r+0x10,cpu.d[1]); w16(r+0x12,cpu.d[2]); }
void f_trap7(void){ if(r16(G_FREEN)){ u32 p=r32(G_FREEP); u32 r=r32(p); cpu.a[6]=p+4; cpu.a[1]=r; w32(G_FREEP,p+4); w16(G_FREEN,r16(G_FREEN)-1); w16(r,0xc00); w32(r+4,cpu.a[0]); w16(r+0x10,cpu.d[0]); w16(r+0x12,cpu.d[1]); } }
static void clear_rec(u32 r){ w32(r+0x10,0); w32(r+0x14,0); w32(r+0x18,0); w32(r+0x1c,0); w8(r,0); }
static void task_end(void){ int me=cur; T[me].live=0; setcontext(&sched); (void)me; }
void f_trap1(void){ clear_rec(REC(cur)); task_end(); }
void f_trap9(void){ u32 r=REC(cur); clear_rec(r); u32 p=r32(G_FREEP)-4; w32(p,r); w32(G_FREEP,p); w16(G_FREEN,r16(G_FREEN)+1); task_end(); }
void f_trap2(void){ u32 off=cpu.d[0]&0xffff; u32 r=0xff0058u+off; cpu.a[4]=0xff0058u; if(r8(r)){ cpu.d[1]=0; clear_rec(r); T[off/0x20].live=0; } }
void f_trap3(void){ u32 r=REC(cur); u32 bit=(cpu.d[0]&0xff)?0x100:0x200; u32 v=(cpu.d[0]&0xffff)|bit; cpu.d[1]=(cpu.d[1]&0xffff0000u)|bit; cpu.d[0]=(cpu.d[0]&0xffff0000u)|v; w16(r,v); w32(r+8,cpu.a[7]); to_sched(); }
void f_trap4(void){ u32 r=REC(cur); w8(r,4); w32(r+8,cpu.a[7]); to_sched(); }
void f_trap5(void){ u32 r=0xff0058u+(cpu.d[0]&0xffff); w8(r,2); w8(r+1,0); cpu.a[4]=0xff0058u; }
void f_trap6(void){ u32 r=0xff0058u+(cpu.d[0]&0xffff); w8(r,4); w8(r+1,cpu.d[1]); cpu.a[4]=0xff0058u; }
void f_trap8(void){ u32 tag=r8(0xff81b3); int i; w8(0xff81b3,0); for(i=8;i<16;i++){ u32 r=REC(i); if(r8(r)&&r8(r+0x16)==tag){ clear_rec(r); T[i].live=0; { u32 p=r32(G_FREEP)-4; w32(p,r); w32(G_FREEP,p); w16(G_FREEN,r16(G_FREEN)+1);} } } }
void f_trap11(void){} void f_trap12(void){} void f_trap13(void){} void f_trap14(void){} void f_trap15(void){}

/* Whole-game comparison */
static FILE *gold; static u8 grec[8+64+0x10000+0x2000]; static u8 *gbuf=grec+64; static u8 cur_ip[64]; static int have_next;
static u8 OBJ[0x10000]; static u8 mask[0x10000];
static long firstdiv=-1, ndiv, nclean;
static long maxv=1L<<40;
static u32 be(u8*p){return ((u32)p[0]<<24)|(p[1]<<16)|(p[2]<<8)|p[3];}
static int golden_next(void){ if(fread(grec,1,sizeof grec,gold)!=sizeof grec) return 0; memcpy(grec+64,grec,8); return 1; }
static long midrun; static void compare(void){ long i,d=0; long first=-1; for(i=0;i<0x10000;i++) if(!mask[i]&&RAMB[i]!=gbuf[8+i]){ if(first<0) first=i; d++; }
    long od=0; for(i=0;i<0x2000;i++) if(OBJ[0x8000+i]!=gbuf[8+0x10000+i]) od++;
    if(od&&getenv("OBJDBG")){ for(i=0;i<0x2000;i++) if(OBJ[0x8000+i]!=gbuf[8+0x10000+i]){ printf(" obj %lx:%02x/%02x",i,OBJ[0x8000+i],gbuf[8+0x10000+i]); if(i>64)break; } printf("\n"); } if(d||od){ ndiv++; if(ndiv<=40||firstdiv<0){ printf("vblank %ld: ram diffs %ld first %lx (host %02x mame %02x) obj diffs %ld\n",curv,d,first<0?0:0xff0000+first,first<0?0:RAMB[first],first<0?0:gbuf[8+first],od); { long k,sh=0; for(k=first;k>=0&&k<0x10000&&sh<12;k++) if(!mask[k]&&RAMB[k]!=gbuf[8+k]){ printf(" %lx:%02x/%02x",0xff0000+k,RAMB[k],gbuf[8+k]); sh++; } printf("\n"); } fflush(stdout);} if(firstdiv<0) firstdiv=curv; if(getenv("STOP_DIV")&&ndiv>=atoi(getenv("STOP_DIV"))){ printf("stop\n"); exit(0);} } else nclean++; }

static void run_irq(void){ Cpu save=cpu; int sc=cur; u32 sr=r32(G_CUR); cur=-1; cpu.a[5]=0xff8000; cpu.a[7]=0xff8000; f_e0e(); cpu=save; cur=sc; (void)sr; }

/* Exact preemption: MAME recorded where each IRQ landed (stacked PC, d0-d7, a0-a6). The lifted code checks that PC before each
   instruction, and the IRQ is taken when the registers match too. Stack pointer is left out: lifted calls push no return addresses. */
u32 irq_pc=0xffffffffu; static u32 ipr[15]; static long nmatch, nkern, nmiss; static long nregmiss; static int in_irq;
static int peek_ip(void){ long pos=ftell(gold); u8 h[72]; int ok=fread(h,1,72,gold)==72; fseek(gold,pos,SEEK_SET); if(!ok) return 0; irq_pc=be(h+8); for(int i=0;i<15;i++) ipr[i]=be(h+12+i*4); return 1; }
static void finish(const char*why){ printf("%s vblank %ld: clean %ld diff %ld first divergence %ld | irq at instruction %ld, in kernel %ld, missed %ld\n",why,curv,nclean,ndiv,firstdiv,nmatch,nkern,nmiss); fflush(stdout); exit(0); }
static void take_irq(void){ u32 t=irq_pc; { char*e=getenv("IRQLOG"); if(e&&curv>=atol(e)&&curv<atol(e)+12) fprintf(stdout,"irq %ld at %x cur %d d0 %x%c",curv,t,cur,cpu.d[0],10); } irq_pc=0xffffffffu; in_irq=1; if(curv>=maxv) finish("end"); if(!golden_next()) finish("golden end"); curv++; iop=vstart[curv<vn?curv:vn-1]; compare(); run_irq(); in_irq=0; (void)t; if(!peek_ip()) finish("golden end"); }
/* Whole walks with only the idle task running and an empty command ring look the same; an IRQ there lands once work has drained. */
static int quiet; static int ring_empty(void){ int i; for(i=0;i<TASKS;i++) if(i!=6&&r8(REC(i))>=4&&i!=cur) return 0; return r16(0xff801a)==r16(0xff801c)||r16(G_FREEN)==0; }
void irq_check(u32 a){ int i; if(in_irq) return; if(cur==6&&!(quiet&&ring_empty())) return; if(a>=0x11ec&&a<0x1214&&cur<0){ if(quiet&&ring_empty()){ nkern++; take_irq(); } return; } /* the idle call: dispatcher leftovers in its registers aren't modelled */ { int bad=0; for(i=0;i<8;i++) if(cpu.d[i]!=ipr[i]) bad++; for(i=0;i<7;i++) if(cpu.a[i]!=ipr[8+i]) bad++; if(bad>2){ static long lastp=-1; if(curv!=lastp&&getenv("REGDBG")){ lastp=curv; printf("nearmiss v%ld pc %x bad %d:",curv,a,bad); for(i=0;i<8;i++) if(cpu.d[i]!=ipr[i]) printf(" d%d %x/%x",i,cpu.d[i],ipr[i]); for(i=0;i<7;i++) if(cpu.a[i]!=ipr[8+i]) printf(" a%d %x/%x",i,cpu.a[i],ipr[8+i]); puts(""); } return; } if(bad) nregmiss++; } nmatch++; take_irq(); }
/* At the dispatcher: the IRQ was in the dispatcher or a trap body (native here), or its point was missed. */
static int kern_pc(u32 p){ return (p>=0xd86&&p<0xdb8)||(p>=0xf00&&p<0x1188); }
static void start_irq(void){ if(irq_pc>=0xdb8&&irq_pc<0xe0e&&!(irq_pc>=0xddc&&irq_pc<0xde6)&&ipr[8]==(u32)REC(cur)&&(cur!=6||ring_empty())){ nkern++; take_irq(); } } /* between marking the task running and its rte */
static void disp_irq(void){ if(irq_pc==0xffffffffu) return; if(kern_pc(irq_pc)){ nkern++; take_irq(); return; } }
static void idle_irq(void){ if(irq_pc==0xffffffffu) return; if(kern_pc(irq_pc)) nkern++; else { nmiss++; if(nmiss<20){ printf("missed irq at %x vblank %ld\n",irq_pc,curv); fflush(stdout);} } take_irq(); }

static void run_task(int i){ u32 r=REC(i); u32 st=r8(r); cur=i; w32(G_CUR,r);
    if(st==0xc){ w8(r,8); start_irq(); getcontext(&T[i].uc); if(!T[i].stack) T[i].stack=malloc(STK); T[i].uc.uc_stack.ss_sp=T[i].stack; T[i].uc.uc_stack.ss_size=STK; T[i].uc.uc_link=0; cpu.a[7]=r32(r+0xc); cpu.a[4]=r32(r+0xc); cpu.a[1]=r32(r+4); cpu.a[0]=r; cpu.d[1]=(cpu.d[1]&0xffff0000u)|0xc; cpu.a[5]=0xff8000; T[i].live=1; makecontext(&T[i].uc,task_tramp,0); swapcontext(&sched,&T[i].uc); }
    else { w8(r,8); start_irq(); cpu.d[1]=(cpu.d[1]&0xffff0000u)|8; swapcontext(&sched,&T[i].uc); } }
#define GAME_TASK 4
extern void f_11ec(void);
/* Dispatcher 0xd86 as the board runs it. Checks run with the IRQ masked; it opens at 0xda4 after each task. */
void f_d86(void){ getcontext(&sched); peek_ip();
  for(;;){ int i, ran=0; w8(G_VFLAG,0);
    for(i=0;i<TASKS;i++){ if(r8(G_VFLAG)) break;
        u32 st=r8(REC(i)); cpu.a[0]=REC(i); cpu.d[0]=(cpu.d[0]&0xffff0000u)|(15-i); cpu.d[1]=(cpu.d[1]&0xffffff00u)|st; if(st>=4){ run_task(i); if(i!=6) ran=1; if(irq_pc>=0xddc&&irq_pc<0xde6&&ipr[8]==(u32)REC(i)&&(i!=6||ring_empty())){ nkern++; take_irq(); } cpu.a[0]=REC(i); cpu.d[0]=(cpu.d[0]&0xffff0000u)|(15-i); } cur=-1;
        
        if(quiet&&ring_empty()&&(kern_pc(irq_pc)||(irq_pc>=0xdb8&&irq_pc<0xe0e))){ nkern++; take_irq(); } }
    quiet=(i==TASKS&&!ran); if(i==TASKS){ cpu.a[0]=REC(15)+0x20; cpu.d[0]|=0xffff; f_11ec(); }
    guard: { static long spin; static long last; if(curv==last){ if(++spin>20000){ idle_irq(); spin=0; } } else { last=curv; spin=0; } }
  } }
#include <signal.h>
static char altstk[1<<16];
static void segv(int n){ void*bt[14]; int nb=backtrace(bt,14); printf("SEGV vblank %ld task %d a0 %x a1 %x a6 %x a7 %x\n",curv,cur,cpu.a[0],cpu.a[1],cpu.a[6],cpu.a[7]); fflush(stdout); backtrace_symbols_fd(bt,nb,1); _exit(4); }
int main(int c,char**v){ { stack_t st; st.ss_sp=altstk; st.ss_size=sizeof altstk; st.ss_flags=0; sigaltstack(&st,0); struct sigaction sa; memset(&sa,0,sizeof sa); sa.sa_handler=segv; sa.sa_flags=SA_ONSTACK; sigaction(SIGSEGV,&sa,0);} FILE*rf=fopen(v[1],"rb"); int i; if(!rf||fread(ROMB,1,sizeof ROMB,rf)!=sizeof ROMB) return 2; { char op[512]; strcpy(op,v[1]); strcpy(strrchr(op,'/')+1,"op.bin"); FILE*of=fopen(op,"rb"); if(!of||fread(OPSPACE,1,sizeof OPSPACE,of)!=sizeof OPSPACE) return 2; fclose(of); } gold=fopen(v[2],"rb"); io_load(v[3]); if(c>4) maxv=atol(v[4]);
    if(c>5){ FILE*m=fopen(v[5],"r"); char l[64]; while(fgets(l,64,m)){ u32 a,b; if(sscanf(l,"%x %x",&a,&b)==2) for(;a<=b;a++) mask[a-0xff0000]=1; } fclose(m);}
    for(i=0;i<256;i++) PAGE[i]=ZERO[i]; for(i=0;i<0x20;i++) PAGE[i]=ROMB+((u32)i<<16); PAGE[0xff]=RAMB; PAGE[0x70]=OBJ;
    golden_next(); memcpy(OBJ+0x8000,gbuf+8+0x10000,0x2000); memcpy(RAMB+0xe90,gbuf+8+0xe90,16); /* what the skipped hardware test left */ curv=0; iop=0; fseek(gold,0,SEEK_SET); gbuf[8+0x8019]=0;
    cpu.d[3]=4; cpu.a[4]=0x800; /* registers the skipped hardware test left, seen through f_1a36 */ cpu.a[7]=0xff8000; cpu.a[5]=0xff8000; f_800(); printf("boot returned\n"); return 1; }
