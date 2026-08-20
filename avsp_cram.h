#ifndef AVSP_CRAM_H
#define AVSP_CRAM_H

/* Bounded CRAM palette writes under Jo Engine's one-based palette contract.
 *
 * Jo allocates colour RAM in 256-entry blocks but hands out
 * jo_palette::data one entry above the block base, because __jo_cram starts
 * at JO_VDP2_CRAM + 256 + 1 (see .deps/joengine/jo_engine/vdp2_malloc.c).
 * That offset is deliberate, not a defect:
 *
 *   - JO_PALETTE_MAX_COLORS is 255, one short of a block;
 *   - jo/tga.c adds one to every 8bpp pixel it decodes, because index zero
 *     is transparent on Saturn, and writes at most 255 colours through
 *     jo_palette::data;
 *   - an 8bpp bitmap or sprite reads colour address 256 * id + pixel, and a
 *     4bpp sprite reads 256 * id + 16 * subbank + pen, so pixel or pen p
 *     lands on data[p - 1] in both cases.
 *
 * Every payload in this project therefore has to be one-based: pixel value
 * p selects palette array entry p - 1, and pixel value zero is transparent
 * and selects nothing. The helpers below express that mapping once and
 * refuse any request that would reach hardware entry 256 * id or
 * 256 * (id + 1), the two block boundaries that belong to a neighbouring
 * allocation.
 *
 * The unit is deliberately free of Jo and Saturn headers so the host tests
 * can exercise it directly with canaries around the permitted range.
 */

/* A Jo colour-RAM block and the largest payload that fits inside one. */
#define AVSP_CRAM_BLOCK_ENTRIES 256
#define AVSP_CRAM_MAX_COLOURS 255

/* One 4bpp sub-bank: sixteen hardware pens, of which pen zero is
   transparent, leaving fifteen writable colours. */
#define AVSP_CRAM_SUBBANK_ENTRIES 16
#define AVSP_CRAM_SUBBANK_COLOURS 15
#define AVSP_CRAM_SUBBANK_COUNT 16

/* Copy a palette file that is indexed by one-based pixel value.
 *
 * `file` holds AVSP_CRAM_BLOCK_ENTRIES entries whose entry zero is the
 * reserved transparent slot and whose live colours occupy the same indices
 * the surface pixels use. `colours` of them, starting at file[1], are
 * copied to data[0 .. colours-1] so that pixel value p reads file[p].
 *
 * Returns 1 on success and 0 if the request is out of contract.
 */
int avsp_cram_copy_surface(unsigned short *data, const unsigned short *file,
                           int colours);

/* Copy a palette that is already indexed by zero-based source colour, the
 * convention used by the generated actor, tile, HUD and route-sequence
 * tables: entry k is the colour of pixel value k + 1, so entries transcribe
 * straight into data[0 .. colours-1].
 */
int avsp_cram_copy_source_indexed(unsigned short *data,
                                  const unsigned short *source, int colours);

/* Copy the fifteen live colours of one 4bpp sub-bank. `file` holds
 * AVSP_CRAM_SUBBANK_ENTRIES entries with a reserved entry zero, matching the
 * object-cel palette files. The destination is the sub-bank's slice of the
 * same Jo allocation, so hardware pen 16 * subbank + p reads file[p].
 */
int avsp_cram_copy_subbank(unsigned short *data, const unsigned short *file,
                           int subbank);

/* True when every pixel of an opaque fitted surface is a live one-based
 * index. A zero pixel would read the neighbouring allocation's last entry
 * rather than a colour this payload owns.
 */
int avsp_cram_surface_is_one_based(const unsigned char *pixels,
                                   unsigned long count);

#endif
