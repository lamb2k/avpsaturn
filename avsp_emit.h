/* CPS2 four-word object-entry geometry for one sprite part.
 *
 * Implements the confirmed geometry from the game's own Family-1 flipped-block
 * emitter (0x0AA1DC..0x0AA21E; true store instructions at 0x0AA210/0x0AA212 -
 * the watchpoint-reported 0x0AA214/0x0AA216 are two instructions later, a
 * confirmed MAME debugger PC-reporting skew, not the store addresses). See
 * docs/AGENT_HANDOFF.md "S2 integration" and its two follow-ups for the full
 * derivation and live verification against captured register/ROM data.
 *
 * The X/Y geometry formula is verified for 3 of the street alien's 5 observed
 * object entries at source frame 4214. The expected X/Y words are not used as
 * calculation inputs: dx/dy come from ROM and origin/or_value come from a
 * route-matched live capture. The current test still supplies code/attr from
 * the captured oracle, so this is NOT yet a complete ROM-to-object decoder.
 *
 *   X = ((origin_x - width - dx) & 0x3FF) | or_value
 *   Y = (origin_y + dy) & 0x3FF
 *   width = 16 * (((attr >> 8) & 0xF) + 1)
 *
 * `origin_x`/`origin_y` are the actor's own per-actor screen-origin scratch
 * (confirmed live to be written once per actor per frame, NOT a frame-global
 * camera constant). Its writer at 0x0AA59A is decoded; the two camera-anchor
 * inputs still need route-matched live reads before native use. `dx`/`dy` come
 * from a per-part offset table addressed via the
 * pose's own part-list entry. `or_value` was confirmed live as 0x8000 (actor
 * `+0x2E`) for the verified case; it is a real per-actor/per-pose value, not a
 * hardcoded constant, and must be supplied by the caller.
 *
 * This function does not walk the ROM part table itself and does not resolve
 * dx/dy/attr/code from an assembly address - the caller supplies per-part
 * inputs already resolved. Two source entries lie between observed entries 2
 * and 3, but the narrow watchpoint evidence does not prove whether they emitted
 * elsewhere in object RAM or were suppressed by a condition. Do not assume
 * either model until a widened live trace or reachable-path control-flow trace
 * resolves it.
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
} AvspObjectEntry;

/* Compute one part's four-word object entry using the confirmed geometry. */
void avsp_emit_part_flipped(unsigned short origin_x, unsigned short origin_y,
                            short dx, short dy, unsigned short code,
                            unsigned short attr, unsigned short or_value,
                            AvspObjectEntry *out);

#endif /* AVSP_EMIT_H */
