/* The unlock record kept in backup RAM (one file, 64 bytes) and its read-modify-write rule. Pure C, no hardware: boot.c uses it, tests/unlock_save_test.c checks it on the host.
   Layout:  0 'A' 'V' 'P' 'S'   4 version (1)   5 header length (8)   6 flags   7 reserved (0)   8..61 free for later settings, kept as they are   62..63 checksum
   (16 bit sum of bytes 0..61, big endian). flags bit 0 = Wolverine unlocked (the post-credits reveal has played).
   Reading: no record, a wrong magic, a checksum that fails or a version below 1 (a record that has no flags byte) is LOCKED, never an error.
   Writing: starts from the record already there and changes only the flags byte, the version (raised to 1) and the checksum, so bytes 8..61, which
   later versions use for settings, survive; a record that cannot be trusted at all (wrong magic) starts from zero. */
#ifndef UNLOCK_SAVE_H
#define UNLOCK_SAVE_H
#define SAVE_SIZE 64
#define SAVE_VERSION 1
#define SAVE_FLAG_WOLVERINE 1u
static unsigned save_sum(const unsigned char *r)
{
    unsigned i, s = 0;
    for (i = 0; i < SAVE_SIZE - 2; i++) s += r[i];
    return s & 0xffffu;
}
static int save_magic(const unsigned char *r, unsigned len)
{
    return len >= SAVE_SIZE && r[0] == 'A' && r[1] == 'V' && r[2] == 'P' && r[3] == 'S';
}
/* the flags a record holds: 0 when there are none to trust */
static unsigned save_flags(const unsigned char *r, unsigned len)
{
    if (!save_magic(r, len) || r[4] < 1 || ((unsigned)r[SAVE_SIZE - 2] << 8 | r[SAVE_SIZE - 1]) != save_sum(r)) return 0;
    return r[6];
}
/* out (SAVE_SIZE bytes) = the old record (len bytes, or none) with the flag bits set and cleared as asked */
static void save_merge(unsigned char *out, const unsigned char *old, unsigned len, unsigned set, unsigned clear)
{
    unsigned i, s, f = save_flags(old, len);
    for (i = 0; i < SAVE_SIZE; i++) out[i] = save_magic(old, len) ? old[i] : 0;
    out[0] = 'A'; out[1] = 'V'; out[2] = 'P'; out[3] = 'S';
    if (out[4] < SAVE_VERSION) out[4] = SAVE_VERSION;
    out[5] = 8;
    out[6] = (unsigned char)((f | set) & ~clear);
    out[7] = 0;
    s = save_sum(out);
    out[SAVE_SIZE - 2] = (unsigned char)(s >> 8); out[SAVE_SIZE - 1] = (unsigned char)s;
}
#endif
