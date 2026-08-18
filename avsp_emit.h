/* CPS2 object-word computation for one sprite part, ROM-derived.
 *
 * Implements the confirmed geometry from the game's own Family-1 flipped-block
 * emitter (0x0AA1DC..0x0AA21E; true store instructions at 0x0AA210/0x0AA212 -
 * the watchpoint-reported 0x0AA214/0x0AA216 are two instructions later, a
 * confirmed MAME debugger PC-reporting skew, not the store addresses). See
 * docs/AGENT_HANDOFF.md "S2 integration" and its two follow-ups for the full
 * derivation and live verification against captured register/ROM data.
 *
 * Verified by pure ROM arithmetic (no oracle data as input) for 3 of the
 * street alien's 5 rendered parts at source frame 4214, exact match on both
 * words:
 *
 *   X = ((origin_x - width - dx) & 0x3FF) | or_value
 *   Y = (origin_y + dy) & 0x3FF
 *   width = 16 * (((attr >> 8) & 0xF) + 1)
 *
 * `origin_x`/`origin_y` are the actor's own per-actor screen-origin scratch
 * (confirmed live to be written once per actor per frame, NOT a frame-global
 * camera constant; its own computation from world position is not yet
 * decoded). `dx`/`dy` come from a per-part offset table addressed via the
 * pose's own part-list entry. `or_value` was confirmed live as 0x8000 (actor
 * `+0x2E`) for the verified case; it is a real per-actor/per-pose value, not a
 * hardcoded constant, and must be supplied by the caller.
 *
 * This function does not walk the ROM part-table itself and does not resolve
 * dx/dy/attr/code from an assembly address - the caller supplies per-part
 * inputs already resolved. The general table walk has one confirmed gap: two
 * of the alien's part-table entries in the verified pose have low/sentinel
 * codes (0x0000, 0x0002) that are consumed (A0 and the per-part advance both
 * apply) but produce NO object-buffer write - a conditional skip not yet
 * located in the disassembly. Do not assume every part-table entry emits an
 * object until that skip condition is found and confirmed.
 *
 * C90.
 */

#ifndef AVSP_EMIT_H
#define AVSP_EMIT_H

typedef struct {
    unsigned short x;     /* word 0: priority (bits 13-15) | position (bits 0-11) */
    unsigned short y;     /* word 1: position (bits 0-9) */
    unsigned short code;  /* word 2 */
    unsigned short attr;  /* word 3: palette/flip/block-size */
} AvspObjectWord;

/* Compute one part's object word, per the confirmed flipped-block formula. */
void avsp_emit_part_flipped(unsigned short origin_x, unsigned short origin_y,
                            short dx, short dy, unsigned short code,
                            unsigned short attr, unsigned short or_value,
                            AvspObjectWord *out);

#endif /* AVSP_EMIT_H */
