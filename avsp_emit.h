/* CPS2 Family-1 object emission: pose assembly -> four-word object entries.
 *
 * Complete ROM-translated port of the game's own dispatcher at 0x0AA00E and
 * its two Family-1 loop bodies, live-disassembled instruction by instruction
 * (MAME 0.289 trace facility; the static ROM dump reads as garbage at these
 * code addresses, so live disassembly is the only trusted source):
 *
 *   dispatcher 0x0AA00E: budget (u16, checked against the frame's tile
 *     budget), count (u16), selector (u16 -> dx/dy table base via the table
 *     at 0x1FD1C8), then `bsr $0AA59A` (origin; consumes the header's
 *     trailing u32) whose final `lsl.b #5,D1` Z flag selects the loop:
 *   facing != 0 -> flipped loop (stores at 0x0AA210/0x0AA212):
 *     X = ((origin_x - width - dx) & 0x3FF) | or_value, attr low byte
 *     = ((raw & 0xE0) + palette) ^ 0x20
 *   facing == 0 -> plain loop (0x0AA1A8..0x0AA1DA):
 *     X = ((origin_x + dx) & 0x3FF) | or_value, attr low byte
 *     = (raw & 0xE0) + palette
 *   both: Y = (origin_y + dy) & 0x3FF; width = 16*(((raw>>8)&0xF)+1);
 *   A2 walk: dx,dy then A2 += advance (the part's trailing u16).
 *
 *   origin (0x0AA59A..0x0AA5E6): D2 = header's trailing u32;
 *     origin_y = anchor_y - world_y + 0x100 -/+ D2.lo  (facing bit 1)
 *     origin_x = world_x - anchor_x + 0x40  -/+ D2.hi  (facing bit 0)
 *   anchor_x/anchor_y are LIVE CAMERA STATE at 0xFF8278/0xFF827C
 *   (= CPS-A scroll1_x + 0x40 and 0x300 - scroll1_y, verified across two
 *   camera positions), not ROM constants.
 *
 *   A pose's `assembly` is a record list (universal walker at
 *   0x0A9D1A/0x0A9D2A, tag jump table at 0x0A9D3E - read through the
 *   decrypted-opcodes view; the raw dump stores PC-relative-read tables
 *   encrypted): the top word is either a family tag itself (one record) or
 *   0x000C ("two records follow"). Each record is [tag][budget][payload]:
 *   tag 0x0006 = the multi-part group above; tag 0x0002 = one entry with
 *   inline [attr][selector][D2 long][code] (same origin routine, same A2
 *   table, same plain/flipped X paths); tag 0x0008 = no-op (rts). Tags
 *   0x0000/0x0004/0x000A have located, undecoded handlers
 *   (0x0AA26C/0x0A9DEE/0x0AA38A); avsp_emit_pose reports them (-1) rather
 *   than guessing.
 *
 * Falsification: tools/verify_avsp_object_corpus.py runs the identical
 * algorithm over 6,139 captured frames across four routes: 14,487 eligible
 * actor-frame instances, 13,890 exact four-word matches against the game's
 * own object RAM, 597 game-omitted (its live-proven per-frame tile-budget
 * bail, offscreen edge band, spawn-in/dying visibility gating), ZERO
 * mismatches. See data/avsp_object_corpus_verification.json and
 * docs/AGENT_HANDOFF.md.
 *
 * C90.
 */

#ifndef AVSP_EMIT_H
#define AVSP_EMIT_H

/* One contiguous ROM window at its original source address. The Saturn
 * runtime carries only the windows the decoded families read (assemblies,
 * dx/dy tables), not the 2 MB image; reads resolve by source address. */
typedef struct {
    const unsigned char *data;
    unsigned long base;
    unsigned long size;
} AvspRomSpan;

typedef struct {
    const AvspRomSpan *spans;
    int span_count;
} AvspRomView;

typedef struct {
    unsigned short x;     /* word 0: priority bits | position (bits 0-9) */
    unsigned short y;     /* word 1: position (bits 0-9) */
    unsigned short code;  /* word 2 */
    unsigned short attr;  /* word 3: palette/flip/block-size */
} AvspObjectEntry;

/* Per-actor inputs, all plain actor-record / camera-state fields:
 * world_x/world_y = actor +0x10/+0x14; facing = +0x0F; palette = +0x0E;
 * or_value = +0x2E; anchor_x/anchor_y = the camera anchors at
 * 0xFF8278/0xFF827C. */
typedef struct {
    unsigned short world_x;
    unsigned short world_y;
    unsigned char facing;
    unsigned char palette;
    unsigned char mode;      /* actor +0x0D: 0x01..0x7F = palette-injected
                                attr; zero/negative = raw attr ^ flip only */
    unsigned short or_value;
    unsigned short anchor_x;
    unsigned short anchor_y;
} AvspEmitActor;

/* Decode the pose assembly at ROM source address `assembly` into object
 * entries. `rom` holds the decrypted program image with rom[0] at source
 * address 0; `rom_size` bounds every read. Writes up to `cap` entries.
 * Returns the entry count, or:
 *   -1  unknown/undecoded assembly selector word (another emitter family)
 *   -2  a read would leave the ROM window, or an implausible part count
 *   -3  bad arguments
 * A short `cap` truncates the output but still returns the full count. */
int avsp_emit_pose(const unsigned char *rom, unsigned long rom_size,
                   unsigned long assembly, const AvspEmitActor *actor,
                   AvspObjectEntry *out, int cap);

/* Same decode through a sparse span view (the Saturn runtime's form). A
 * read outside every span fails the decode with -2, never guesses. */
int avsp_emit_pose_view(const AvspRomView *view, unsigned long assembly,
                        const AvspEmitActor *actor, AvspObjectEntry *out,
                        int cap);

/* Decode one group given its header address (used by avsp_emit_pose; exposed
 * for tests and tooling). Same return convention. */
int avsp_emit_group(const unsigned char *rom, unsigned long rom_size,
                    unsigned long header, const AvspEmitActor *actor,
                    AvspObjectEntry *out, int cap);

#endif /* AVSP_EMIT_H */
