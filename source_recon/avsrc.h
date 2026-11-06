/* Readable reconstruction of avspu 68000 routines. Private project, research only.
   Memory model: big-endian byte views of the source's RAM and palette space, so a unit can be
   compared word for word with the ROM routine. The native port maps these onto its own state. */
#ifndef AVSRC_H
#define AVSRC_H

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef short s16;

#define AVSRC_RAM_SIZE 0x10000u
#define AVSRC_PAL_SIZE 0x1000u

typedef struct AvsrcMem {
    u8 ram[AVSRC_RAM_SIZE];    /* 0xff0000.. */
    u8 pal[AVSRC_PAL_SIZE];    /* 0x90c000.. colour RAM, four banks of 32 palettes of 16 words */
} AvsrcMem;

u16 avsrc_r16(const u8 *p);
u32 avsrc_r32(const u8 *p);
void avsrc_w16(u8 *p, u16 v);
void avsrc_w32(u8 *p, u32 v);

#define RAM8(m, a) ((m)->ram[(a) - 0xff0000u])
#define RAM16(m, a) avsrc_r16(&(m)->ram[(a) - 0xff0000u])
#define RAM32(m, a) avsrc_r32(&(m)->ram[(a) - 0xff0000u])
#define RAM16W(m, a, v) avsrc_w16(&(m)->ram[(a) - 0xff0000u], (u16)(v))
#define RAM32W(m, a, v) avsrc_w32(&(m)->ram[(a) - 0xff0000u], (u32)(v))

#endif
