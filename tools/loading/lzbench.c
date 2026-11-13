/* lzbench: ratio of candidate SH-2 friendly codecs on independent chunks. usage: lzbench file chunk_bytes [maxbytes] */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef unsigned char u8;
/* A: LZ4-like. token: hi nibble literal len (15 = more bytes), lo nibble match len-4 (15=more); then literals, then u16 LE offset (1..65535). last sequence literals only. */
static size_t enc_lz4(const u8 *s, size_t n, u8 *d, int lazy){
  static int head[1<<16]; int *chain = malloc(sizeof(int)*n);
  memset(head,-1,sizeof head); size_t i=0, lit=0, o=0; 
  #define H(p) ((((s[p]|(s[p+1]<<8)|(s[p+2]<<16)|((unsigned)s[p+3]<<24))*2654435761u)>>16)&0xffff)
  size_t anchor=0;
  while(i+4<=n){
    unsigned h=H(i); int c=head[h]; int best=0,bo=0; int tries=64;
    while(c>=0 && tries--){ if(i-c>65535) break; int l=0; while(i+l<n && s[c+l]==s[i+l]) l++; if(l>best){best=l;bo=i-c;} c=chain[c]; }
    if(best>=4){
      /* emit */
      size_t ll=i-anchor; u8 *tok=d+o++; 
      u8 t=(ll>=15?15:ll)<<4; if(ll>=15){ size_t r=ll-15; while(r>=255){d[o++]=255;r-=255;} d[o++]=r; }
      memcpy(d+o,s+anchor,ll); o+=ll; d[o++]=bo&255; d[o++]=bo>>8;
      size_t ml=best-4; t|=(ml>=15?15:ml); if(ml>=15){ size_t r=ml-15; while(r>=255){d[o++]=255;r-=255;} d[o++]=r; }
      *tok=t;
      for(int k=0;k<best;k++){ if(i+k+4<=n){unsigned hh=H(i+k); chain[i+k]=head[hh]; head[hh]=i+k;} }
      i+=best; anchor=i;
    } else { chain[i]=head[h]; head[h]=i; i++; }
  }
  { size_t ll=n-anchor; u8 t=(ll>=15?15:ll)<<4; d[o++]=t; if(ll>=15){ size_t r=ll-15; while(r>=255){d[o++]=255;r-=255;} d[o++]=r; } memcpy(d+o,s+anchor,ll); o+=ll; }
  free(chain); return o; }
/* B: LZSS byte: groups of 8 items led by a flag byte (bit set = literal). match = 2 bytes: off 12 bits (1..4095) , len 4 bits (3..18). */
static size_t enc_lzss(const u8 *s, size_t n, u8 *d, int win, int lenbits){
  size_t i=0,o=0; int maxl=(1<<lenbits)+2; int offbits=16-lenbits; int maxoff=(1<<offbits)-1; if(win&&maxoff>win) maxoff=win;
  u8 *flagp=NULL; int fb=0;
  while(i<n){
    if(fb==0){ flagp=d+o++; *flagp=0; fb=8; }
    int best=0,bo=0; size_t lo = i>(size_t)maxoff? i-maxoff:0;
    for(size_t c=i; c-- > lo;){ int l=0; while(i+l<n && l<maxl && s[c+l]==s[i+l]) l++; if(l>best){best=l;bo=i-c; if(l==maxl) break;} }
    fb--; 
    if(best>=3){ int v=((bo)<<lenbits)|(best-3); d[o++]=v>>8; d[o++]=v&255; i+=best; }
    else { *flagp|=1<<fb; d[o++]=s[i++]; }
  }
  return o; }
/* C: word LZSS: 16-bit units; flag word (16 items), literal = 2 bytes, match = u16 (off 11 bits in words 1..2047, len 5 bits in words 2..33) -> window 4 KB, max len 66 B. */
static size_t enc_wlz(const u8 *s, size_t n, u8 *d){
  size_t nw=n/2, i=0, o=0; u8 *flagp=NULL; int fb=0;
  while(i<nw){
    if(fb==0){ flagp=d+o; o+=2; d[o-2]=d[o-1]=0; fb=16; }
    int best=0,bo=0; size_t lo=i>2047?i-2047:0;
    for(size_t c=i; c-- > lo;){ int l=0; while(i+l<nw && l<33 && s[2*(c+l)]==s[2*(i+l)] && s[2*(c+l)+1]==s[2*(i+l)+1]) l++; if(l>best){best=l;bo=i-c; if(l==33)break;} }
    fb--;
    if(best>=2){ unsigned v=(bo<<5)|(best-2); d[o++]=v>>8; d[o++]=v&255; i+=best; }
    else { int bit=fb; int idx=(bit>=8)?0:1; flagp[idx]|=0; /* flag as big-endian 16 bit */ unsigned f=(flagp[0]<<8)|flagp[1]; f|=1u<<fb; flagp[0]=f>>8; flagp[1]=f&255; d[o++]=s[2*i]; d[o++]=s[2*i+1]; i++; }
  }
  return o; }
int main(int argc,char**argv){
  FILE*f=fopen(argv[1],"rb"); if(!f){puts("open");return 1;} size_t chunk=atoi(argv[2]); long maxb= argc>3?atol(argv[3]):1<<30;
  fseek(f,0,SEEK_END); long sz=ftell(f); if(sz>maxb) sz=maxb; fseek(f,0,SEEK_SET); u8*b=malloc(sz); fread(b,1,sz,f); fclose(f);
  u8*o=malloc(sz*2+1024); size_t t_lz4=0,t_lzss=0,t_lzss16=0,t_w=0, tot=0;
  for(long p=0;p<sz;p+=chunk){ size_t n= (sz-p)<chunk?sz-p:chunk; n&=~1u; if(!n) break; tot+=n;
    size_t a=enc_lz4(b+p,n,o,0); t_lz4+= a<n?a:n;
    a=enc_lzss(b+p,n,o,0,4); t_lzss+= a<n?a:n;
    a=enc_lzss(b+p,n,o,0,6); t_lzss16+= a<n?a:n;
    a=enc_wlz(b+p,n,o); t_w+= a<n?a:n; }
  printf("%s chunk %zu bytes %zu : lz4 %.3f  lzss12/4 %.3f  lzss10/6 %.3f  wordlzss %.3f\n",argv[1],chunk,tot,(double)t_lz4/tot,(double)t_lzss/tot,(double)t_lzss16/tot,(double)t_w/tot);
  return 0; }
