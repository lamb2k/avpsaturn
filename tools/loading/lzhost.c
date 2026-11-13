/* lzhost.c: host build (MSVC DLL) of saturn/rt/lzdec.h for tools/loading/lzstore.py: decode check and the in-place simulation of the loader's lz_unit, from the very same source.
   build: cl /nologo /O2 /LD tools/loading/lzhost.c /I saturn/rt /Fe:lzhost.dll */
#define LZ_HOST 1
#include "lzdec.h"
static LzCtx ctx;
static lz8 scratch[1 << 17];
__declspec(dllexport) long lz_host_inflate(const unsigned char *src, unsigned char *dst, unsigned long cap) { return lz_inflate(&ctx, src, dst, dst + cap); }
/* dest holds the compressed streams at its end already (as the loader reads them); returns lz_unit's result; tail must be <= 131000 */
__declspec(dllexport) int lz_host_unit(unsigned char *dest, unsigned long raw_total, unsigned long nblk, const unsigned long *blk, unsigned long tail)
{
    if (tail > sizeof scratch - 8) return -1000;
    return lz_unit(&ctx, dest, raw_total, nblk, blk, tail, scratch);
}
