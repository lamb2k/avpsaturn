/* Test-only driver: run lifted functions from captured entry states and print effects.
   usage: lift_host CASES.bin ROM.bin OUT.txt [first last]. Each case: reset memory, call, print regs, flags and changed bytes.
   Stops a case on a trap, system-register op, unhandled instruction, or 1 s timeout (printed as ABORT kind). */
#include <setjmp.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
typedef unsigned char u8;
typedef unsigned int u32;
typedef struct { u32 d[8]; u32 a[8]; u32 ccz, ccn, ccc, ccv, ccx; } Cpu;
static Cpu cpu;
Cpu *R = &cpu;
u8 *PAGE[256];
u8 RAMB[0x10000];
u8 ROMB[0x200000];
static u8 GFX[0x10000], OBJ[0x10000], ZERO[256][0x10000];
static u8 RAM0[0x10000], GFX0[0x10000], OBJ0[0x10000];
static sigjmp_buf jb;
static const char *why;
static void stop(const char *w) { why = w; siglongjmp(jb, 1); }
void f_trap0(void){stop("trap");} void f_trap1(void){stop("trap");} void f_trap2(void){stop("trap");} void f_trap3(void){stop("trap");}
void f_trap4(void){stop("trap");} void f_trap5(void){stop("trap");} void f_trap6(void){stop("trap");} void f_trap7(void){stop("trap");}
void f_trap8(void){stop("trap");} void f_trap9(void){stop("trap");} void f_trap10(void){stop("trap");} void f_trap11(void){stop("trap");}
void f_trap12(void){stop("trap");} void f_trap13(void){stop("trap");} void f_trap14(void){stop("trap");} void f_trap15(void){stop("trap");}
void f_badjump(u32 a){(void)a;stop("badjump");}
void f_sysreg(void){stop("sysreg");}
void f_unhandled(u32 a){(void)a;stop("unhandled");}
static void alarmh(int s){(void)s;stop("timeout");}
u32 f_divu(u32 n, u32 d, int*ov){ d&=0xffff; if(!d) stop("div0"); u32 q=n/d; if(q>0xffff){*ov=1;return n;} return ((n%d)<<16)|q; }
u32 f_divs(u32 n, u32 d, int*ov){ int dv=(short)d; if(!dv) stop("div0"); long long nn=(int)n; long long q=nn/dv; if(q>32767||q<-32768){*ov=1;return n;} return ((u32)((nn%dv)&0xffff)<<16)|(u32)(q&0xffff); }
u32 f_roxl(u32 o,int n,int w,int*x){ int left=w>0; if(!left)w=-w; u32 m=w==32?0xffffffffu:(1u<<w)-1; n%=(w+1); for(;n>0;n--){ if(left){int c=(o>>(w-1))&1;o=((o<<1)|*x)&m;*x=c;} else {int c=o&1;o=(o>>1)|((u32)*x<<(w-1));*x=c;} } return o&m; }
u32 f_abcd(u32 d,u32 s,int*x){ u32 r=(s&15)+(d&15)+*x; if(r>9) r+=6; r+=(s&0xf0)+(d&0xf0); *x=r>0x99; if(*x) r-=0xa0; return r&0xff; }
u32 f_sbcd(u32 d,u32 s,int*x){ u32 r=(d&15)-(s&15)-*x; if(r>9) r-=6; r+=(d&0xf0)-(s&0xf0); *x=r>0x99; if(*x) r+=0xa0; return r&0xff; }
u32 IOR8(u32 a){return 0;} u32 IOR16(u32 a){return 0;} u32 IOR32(u32 a){return 0;} void IOW8(u32 a,u32 v){} void IOW16(u32 a,u32 v){} void IOW32(u32 a,u32 v){}
void f_d86(void){stop("trap");}
#include "dispatch.inc"
static void setup_pages(void){ int i; for(i=0;i<256;i++) PAGE[i]=ZERO[i]; for(i=0;i<0x20;i++) PAGE[i]=ROMB+((u32)i<<16); PAGE[0xff]=RAMB; PAGE[0x90]=GFX; PAGE[0x70]=OBJ; }
static void diff(FILE*o,const u8*a,const u8*b,u32 base,u32 n,u32 skipl,u32 skiph){ u32 i; for(i=0;i<n;i++) if(a[i]!=b[i]&&!(base+i>=skipl&&base+i<skiph)) fprintf(o,"%x:%x ",base+i,a[i]); }
int main(int c,char**v){
    FILE*f=fopen(v[1],"rb"),*rf=fopen(v[2],"rb"),*o=fopen(v[3],"w");
    long first=c>4?atol(v[4]):0,last=c>5?atol(v[5]):1L<<40,n=0;
    u8 hdr[12+64]; static u8 buf[0x10000+0x10000+0x2000];
    if(!f||!rf||!o) return 2;
    if(fread(ROMB,1,sizeof ROMB,rf)!=sizeof ROMB) return 3;
    setup_pages(); signal(SIGALRM,alarmh);
    while(fread(hdr,1,76,f)==76&&fread(buf,1,sizeof buf,f)==sizeof buf){
        u32 addr=(hdr[4]<<24)|(hdr[5]<<16)|(hdr[6]<<8)|hdr[7]; int i; void(*fn)(void);
        if(n<first||n>=last){n++;continue;}
        memcpy(RAMB,buf,0x10000); memcpy(GFX,buf+0x10000,0x10000); memset(OBJ,0,0x10000); memcpy(OBJ,buf+0x20000,0x2000);
        memcpy(RAM0,RAMB,0x10000); memcpy(GFX0,GFX,0x10000); memcpy(OBJ0,OBJ,0x10000);
        memset(&cpu,0,sizeof cpu); memset(ZERO,0,sizeof ZERO);
        for(i=0;i<8;i++){u8*p=hdr+12+i*4;cpu.d[i]=((u32)p[0]<<24)|(p[1]<<16)|(p[2]<<8)|p[3];}
        for(i=0;i<8;i++){u8*p=hdr+44+i*4;cpu.a[i]=((u32)p[0]<<24)|(p[1]<<16)|(p[2]<<8)|p[3];}
        { u32 sp0=cpu.a[7]; why="ok"; fn=lookup(addr);
          if(!fn) why="nofn"; else if(!sigsetjmp(jb,1)){ alarm(1); fn(); alarm(0);} alarm(0);
          fprintf(o,"%ld %x %s ",n,addr,why);
          for(i=0;i<8;i++) fprintf(o,"%x ",cpu.d[i]);
          for(i=0;i<7;i++) fprintf(o,"%x ",cpu.a[i]);
          fprintf(o,"cc %d %d %d %d | ",!!cpu.ccz,!!cpu.ccn,!!cpu.ccc,!!cpu.ccv);
          { u32 l=(sp0&0xffffff)-0x800,h=(sp0&0xffffff)+8; diff(o,RAMB,RAM0,0xff0000,0x10000,l,h); diff(o,GFX,GFX0,0x900000,0x10000,0,0); diff(o,OBJ,OBJ0,0x700000,0x2000,0,0); }
          fprintf(o,"\n"); }
        n++;
    }
    fclose(o); return 0;
}
