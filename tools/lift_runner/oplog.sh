#!/bin/sh
# Records every opcode-space byte the lifted code reads as data over a golden run: tools/satint_merge.py keeps them in the side store. Tables can run into real code (0x4ccb0 into 0x4ccc0), which a census of reads cannot tell from fetches.
# usage (WSL): oplog.sh RUN_DIR ROM_DIR GOLDEN OUT TMP   RUN_DIR holds c*/lifted_mem.c, ROM_DIR rt.bin and op.bin. env as run.sh.
RUN=$1; ROM=$2; G=$3; OUT=$4; T=$5; D=$(cd "$(dirname "$0")" && pwd); mkdir -p "$T"
cat > "$T/oplog.c" <<'C'
#include <stdio.h>
#include <stdlib.h>
unsigned char OPLOG[0x200000]; unsigned oplb;
static struct { unsigned b, lo, hi; } H[1 << 16];
void op_note(unsigned a, int w){ unsigned b = oplb, i; if(!b) return; oplb = 0; for(i = (b * 2654435761u) >> 16; H[i].b && H[i].b != b; i = (i + 1) & 0xffff); if(!H[i].b){ H[i].b = b; H[i].lo = a; H[i].hi = a + w; } if(a < H[i].lo) H[i].lo = a; if(a + w > H[i].hi) H[i].hi = a + w; }
__attribute__((destructor)) static void w(void){ FILE*f=fopen(getenv("OPLOG_OUT"),"w"); char n[600]; int i; if(!f) return; for(i=0;i<0x200000;i++) if(OPLOG[i]) fprintf(f,"%x\n",i); fclose(f); snprintf(n,600,"%s.ranges",getenv("OPLOG_OUT")); f=fopen(n,"w"); for(i=0;i<1<<16;i++) if(H[i].b) fprintf(f,"%x %x %x\n",H[i].b,H[i].lo,H[i].hi); fclose(f); }
C
ls -d "$RUN"/c[0-9]* | grep -v '\.o$' | xargs -P4 -I@ sh -c 'n=$(basename @); sed -E -e "s/\bOP(8|16|32)\(\(0x([0-9a-f]+)u\+/OP\1((oplb=0x\2u,0x\2u+/g" @/lifted_mem.c | sed -e "s|^#define OP8(a) .*|extern unsigned char OPLOG[]; extern u8*OPB; extern u32 oplb; extern void op_note(u32,int); static inline u32 op_l(u32 a,int w){int i;a\&=0x1fffff;op_note(a,w);for(i=0;i<w;i++)OPLOG[a+i]=1;return a;}\n#define OP8(a) (OPB[op_l((u32)(a),1)])|" -e "s|^#define OP16(a) (\*(const.*|#define OP16(a) (*(const u16*)(OPB+op_l((u32)(a),2)))|" -e "s|^#define OP16(a) ((u16)be16r.*|#define OP16(a) ((u16)be16r(OPB+op_l((u32)(a),2)))|" -e "s|^#define OP32(a) (\*(const.*|#define OP32(a) (*(const u32*)(OPB+op_l((u32)(a),4)))|" -e "s|^#define OP32(a) be32r.*|#define OP32(a) be32r(OPB+op_l((u32)(a),4))|" > '"$T"'/$n.c; gcc -DHOST -DPREEMPT -w -O1 -fno-strict-aliasing -c '"$T"'/$n.c -o '"$T"'/$n.o' || exit 1
cp "$RUN/dispatch.inc" "$T/" ; cd "$T" && gcc -DPREEMPT -w -O1 -g -rdynamic -I. "$D/host_kernel.c" oplog.c c[0-9]*.o -o lr_oplog || exit 1
GOLD_DELTA=1 STOP_DIV=3 OPLOG_OUT="$OUT" timeout -s KILL 580 ./lr_oplog "$ROM/rt.bin" "$G" "$G.io.txt" 400000 "$D/mask.txt" 2>&1 | grep -a 'golden end\|ram diffs' | tail -2 | cut -c1-200
wc -l "$OUT"
