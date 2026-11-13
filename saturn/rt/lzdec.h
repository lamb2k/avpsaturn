/* lzdec.h: raw deflate (RFC 1951) decoder for the loader (lane loading, 2026-11-12, SAT_LOAD_LZ). No malloc, no libc; table driven (fast table for codes up to LZ_LB / LZ_DB bits,
   the canonical slow path of puff.c for longer ones). Shared by saturn/rt/boot.c (SH-2, big endian) and the host test DLL (tools/loading/lzhost.c): the same text is what is verified.
   Streams are produced by zlib (raw, wbits -15, level 9) in tools/loading/lzstore.py. The input may be read up to 4 bytes beyond a stream's last byte (the bit buffer refills a byte at a time):
   callers keep 4 readable bytes after the last stream.
   lz_unit() decodes a list of independent streams one after another into one destination buffer IN PLACE: the compressed streams (each padded to whole sectors) were read into the end of the
   buffer, the output grows from its start; the last `tail` bytes of the buffer are copied to a scratch area first and the decoder reads them from there (so the output may pass over them). */
#ifndef LZDEC_H
#define LZDEC_H
#define LZ_LB 9u
#define LZ_DB 7u
typedef unsigned char lz8; typedef unsigned short lz16; typedef unsigned long lz32;
typedef struct {
    const lz8 *src, *swp, *scr; lz32 bits; int nbits; lz8 *dst, *dend;   /* when src reaches swp it continues at scr (the tail kept in scratch) */
    lz16 lcnt[16], lsym[288], dcnt[16], dsym[32], ltab[1u << LZ_LB], dtab[1u << LZ_DB];
} LzCtx;
static const lz16 lz_lbase[29] = { 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258 };
static const lz8 lz_lext[29] = { 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0 };
static const lz16 lz_dbase[30] = { 1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577 };
static const lz8 lz_dext[30] = { 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13 };
static const lz8 lz_clorder[19] = { 16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15 };

static void lz_need(LzCtx *z, int n) { while (z->nbits < n) { if (z->src == z->swp) z->src = z->scr; z->bits |= (lz32)*z->src++ << z->nbits; z->nbits += 8; } }
static lz32 lz_get(LzCtx *z, int n) { lz32 v; if (!n) return 0; lz_need(z, n); v = z->bits & ((1ul << n) - 1); z->bits >>= n; z->nbits -= n; return v; }

/* canonical table from code lengths: cnt[len], sym sorted by (length, symbol), tab[bit reversed code] = sym << 4 | len for codes of up to tb bits. */
static void lz_build(lz16 *cnt, lz16 *sym, lz16 *tab, unsigned tb, const lz8 *len, int n)
{
    lz16 offs[17]; lz32 next[17], code = 0; int i, l;
    for (l = 0; l < 16; l++) cnt[l] = 0;
    for (i = 0; i < n; i++) cnt[len[i]]++;
    cnt[0] = 0;
    for (l = 0; l < (1 << tb); l++) tab[l] = 0;
    offs[1] = 0; for (l = 1; l < 15; l++) offs[l + 1] = (lz16)(offs[l] + cnt[l]);
    for (i = 0; i < n; i++) if (len[i]) sym[offs[len[i]]++] = (lz16)i;
    for (l = 1; l < 16; l++) { code = (code + (l > 1 ? cnt[l - 1] : 0)) << 1; next[l] = code; }
    if (!tb) return;
    for (i = 0; i < n; i++) {
        l = len[i];
        if (l && l <= (int)tb) {
            lz32 c = next[l]++, r = 0; int k; unsigned idx;
            for (k = 0; k < l; k++) { r = (r << 1) | (c & 1); c >>= 1; }
            for (idx = (unsigned)r; idx < (1u << tb); idx += 1u << l) tab[idx] = (lz16)(i << 4 | l);
        } else if (l) next[l]++;
    }
}
static int lz_sym(LzCtx *z, const lz16 *tab, unsigned tb, const lz16 *cnt, const lz16 *sym)
{
    int code = 0, first = 0, index = 0, l;
    lz_need(z, 15);
    if (tb) {
        lz16 e = tab[z->bits & ((1u << tb) - 1)];
        if (e) { l = e & 15; z->bits >>= l; z->nbits -= l; return e >> 4; }
    }
    for (l = 1; l < 16; l++) {
        int c;
        code |= (int)(z->bits & 1); z->bits >>= 1; z->nbits--;
        c = cnt[l];
        if (code - c < first) return sym[index + (code - first)];
        index += c; first += c; first <<= 1; code <<= 1;
    }
    return -1;
}
/* one deflate stream into dst (up to dend); returns bytes written or -1 */
static long lz_inflate(LzCtx *z, const lz8 *src, lz8 *dst, lz8 *dend)
{
    int last; lz8 *d0 = dst;
    z->src = src; z->bits = 0; z->nbits = 0; z->dst = dst; z->dend = dend;
    do {
        int type; last = (int)lz_get(z, 1); type = (int)lz_get(z, 2);
        if (type == 0) {
            lz32 len; z->bits >>= z->nbits & 7; z->nbits -= z->nbits & 7;
            len = lz_get(z, 16); lz_get(z, 16);
            if (z->dst + len > z->dend) return -1;
            while (len--) *z->dst++ = (lz8)lz_get(z, 8);
        } else if (type == 1 || type == 2) {
            lz8 lens[320]; int i, nlen, ndist;
            if (type == 1) {
                for (i = 0; i < 144; i++) lens[i] = 8;
                for (; i < 256; i++) lens[i] = 9;
                for (; i < 280; i++) lens[i] = 7;
                for (; i < 288; i++) lens[i] = 8;
                for (i = 0; i < 30; i++) lens[288 + i] = 5;
                nlen = 288; ndist = 30;
            } else {
                lz8 cl[19]; lz16 ccnt[16], csym[19], ctab[1];
                nlen = (int)lz_get(z, 5) + 257; ndist = (int)lz_get(z, 5) + 1; i = (int)lz_get(z, 4) + 4;
                if (nlen > 286 || ndist > 30) return -1;
                { int k; for (k = 0; k < 19; k++) cl[k] = 0; for (k = 0; k < i; k++) cl[lz_clorder[k]] = (lz8)lz_get(z, 3); }
                lz_build(ccnt, csym, ctab, 0, cl, 19);
                for (i = 0; i < nlen + ndist; ) {
                    int s = lz_sym(z, ctab, 0, ccnt, csym), rep, v = 0;
                    if (s < 0) return -1;
                    if (s < 16) { lens[i++] = (lz8)s; continue; }
                    if (s == 16) { if (!i) return -1; v = lens[i - 1]; rep = 3 + (int)lz_get(z, 2); }
                    else if (s == 17) rep = 3 + (int)lz_get(z, 3); else rep = 11 + (int)lz_get(z, 7);
                    if (i + rep > nlen + ndist) return -1;
                    while (rep--) lens[i++] = (lz8)v;
                }
                { int k; for (k = ndist - 1; k >= 0; k--) lens[288 + k] = lens[nlen + k]; }   /* distance lengths up to a fixed place (nlen <= 286 < 288: moving upward from the end is safe) */
            }
            lz_build(z->lcnt, z->lsym, z->ltab, LZ_LB, lens, nlen);
            lz_build(z->dcnt, z->dsym, z->dtab, LZ_DB, lens + 288, ndist);
            for (;;) {
                int s = lz_sym(z, z->ltab, LZ_LB, z->lcnt, z->lsym);
                if (s < 256) { if (s < 0 || z->dst >= z->dend) return -1; *z->dst++ = (lz8)s; }
                else if (s == 256) break;
                else {
                    int len, dist; lz8 *p;
                    s -= 257; if (s >= 29) return -1;
                    len = lz_lbase[s] + (int)lz_get(z, lz_lext[s]);
                    s = lz_sym(z, z->dtab, LZ_DB, z->dcnt, z->dsym); if (s < 0 || s >= 30) return -1;
                    dist = lz_dbase[s] + (int)lz_get(z, lz_dext[s]);
                    if (z->dst - d0 < dist || z->dst + len > z->dend) return -1;
                    p = z->dst - dist; while (len--) *z->dst++ = *p++;
                }
            }
        } else return -1;
    } while (!last);
    return (long)(z->dst - d0);
}
/* Decode nblk streams in place. dest: buffer of raw_total bytes. blk[2k] = raw bytes of stream k, blk[2k+1] = its compressed bytes; stream k lies at base + (sum of the padded sizes before it), where
   base = dest + raw_total - (sum of all padded sizes) and a padded size is the compressed size rounded up to 2048. The last `tail` bytes of the buffer are copied
   to `scratch` first (capacity tail + 8); the decoder switches to the copy when its input reaches them. Returns 0, or a negative code. */
static int lz_unit(LzCtx *z, lz8 *dest, lz32 raw_total, lz32 nblk, const lz32 *blk, lz32 tail, lz8 *scratch)
{
    lz32 k, padded = 0, off = 0, out = 0; lz8 *base, *swp = dest + raw_total - tail;
    z->swp = tail ? swp : (const lz8 *)0; z->scr = scratch;
    for (k = 0; k < nblk; k++) padded += (blk[2 * k + 1] + 2047ul) & ~2047ul;
    base = dest + raw_total - padded;
    { lz32 q; for (q = 0; q < tail; q++) scratch[q] = swp[q]; for (q = 0; q < 8; q++) scratch[tail + q] = 0; }
    for (k = 0; k < nblk; k++) {
        const lz8 *s = base + off; long n;
        if (s >= swp) s = scratch + (s - swp);
        n = lz_inflate(z, s, dest + out, dest + raw_total);
        if (n != (long)blk[2 * k]) return -1 - (int)k;
        out += blk[2 * k]; off += (blk[2 * k + 1] + 2047ul) & ~2047ul;
    }
    return out == raw_total ? 0 : -100;
}
#endif
