/* The port's save record in backup RAM (one file, 64 bytes) and its read-modify-write rule. Pure C, no hardware: boot.c uses it, tests/unlock_save_test.c checks it on the host.
   Layout:  0 'A' 'V' 'P' 'S'   4 version (1)   5 header length (8)   6 flags   7 saved bonus-character setting   8..61 free for later settings, kept as they are   62..63 checksum
   (16 bit sum of bytes 0..61, big endian).
   flags bit 0 = the post-credits reveal has played once and turned Wolverine on (the player's own choice in OPTION MODE wins from then on). It was "Wolverine unlocked" in the first
   version of the reveal lane; the bit is the same, so such a record reads the same.
   byte 7 = the player's BONUS CHARACTERS setting: bit 7 set means a setting is saved, bits 0 and 1 are the guest bits (1 Wolverine, 2 Mega Man). Written by OPTION MODE and by the reveal's
   automatic turn-on; 0 (no setting saved) in every record written before it existed, so those fall back to the build's default.
   Reading: no record, a wrong magic, a checksum that fails or a version below 1 gives flags 0 and no saved setting, never an error.
   Writing: starts from the record already there and changes only the flags byte, byte 7, the version (raised to 1) and the checksum, so bytes 8..61, which later versions use for settings,
   survive; a record that cannot be trusted at all (wrong magic) starts from zero. */
#ifndef UNLOCK_SAVE_H
#define UNLOCK_SAVE_H
#define SAVE_SIZE 64
#define SAVE_VERSION 1
#define SAVE_FLAG_WOLVERINE 1u      /* the reveal has played and switched Wolverine on */
#define SAVE_SEL_SAVED 0x80u
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
static int save_valid(const unsigned char *r, unsigned len)
{
    return save_magic(r, len) && r[4] >= 1 && ((unsigned)r[SAVE_SIZE - 2] << 8 | r[SAVE_SIZE - 1]) == save_sum(r);
}
/* the flags a record holds: 0 when there are none to trust */
static unsigned save_flags(const unsigned char *r, unsigned len)
{
    return save_valid(r, len) ? r[6] : 0;
}
/* the saved bonus-character setting (0 to 3), or -1 when none is saved */
static int save_sel(const unsigned char *r, unsigned len)
{
    return save_valid(r, len) && (r[7] & SAVE_SEL_SAVED) ? (int)(r[7] & 3u) : -1;
}
/* out (SAVE_SIZE bytes) = the old record (len bytes, or none) with the flag bits set and cleared as asked, and the bonus-character setting stored when sel >= 0 */
static void save_merge2(unsigned char *out, const unsigned char *old, unsigned len, unsigned set, unsigned clear, int sel)
{
    unsigned i, s, f = save_flags(old, len);
    for (i = 0; i < SAVE_SIZE; i++) out[i] = save_magic(old, len) ? old[i] : 0;
    out[0] = 'A'; out[1] = 'V'; out[2] = 'P'; out[3] = 'S';
    if (out[4] < SAVE_VERSION) out[4] = SAVE_VERSION;
    out[5] = 8;
    out[6] = (unsigned char)((f | set) & ~clear);
    if (sel >= 0) out[7] = (unsigned char)(SAVE_SEL_SAVED | (unsigned)(sel & 3));
    else if (!save_valid(old, len)) out[7] = (unsigned char)(out[7] & ~SAVE_SEL_SAVED);   /* a sum that failed does not vouch for a saved setting */
    s = save_sum(out);
    out[SAVE_SIZE - 2] = (unsigned char)(s >> 8); out[SAVE_SIZE - 1] = (unsigned char)s;
}
static void save_merge(unsigned char *out, const unsigned char *old, unsigned len, unsigned set, unsigned clear)
{
    save_merge2(out, old, len, set, clear, -1);
}
#endif
