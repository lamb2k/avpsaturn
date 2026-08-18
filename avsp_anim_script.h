#ifndef AVSP_ANIM_SCRIPT_H
#define AVSP_ANIM_SCRIPT_H

/* One decoded 16-byte CPS2 animation pose record.
 *
 * Fields are big-endian on the wire:
 *   +0  duration   (u16) frames the pose is held
 *   +2  flags      (u16) bit 15 marks a jump record; bits 14-8 hold the
 *                        seven-bit sequence index; bits 7-0 the parameter byte
 *   +4  assembly   (u32) absolute ROM address of the selector-6 assembly
 *   +8..+15        an unlabeled tail the interpreter does NOT consume; the
 *                  interaction-table consumers of its first two bytes are
 *                  proven separately (step 1's pose/position gates).
 *
 * Bit 15 is exposed as `flip_flag` (the handoff's name for the field) and is
 * what drives the jump control flow. It is deliberately not used as the render
 * flip here: render flip is the runtime actor facing, uniform per pose.
 */
typedef struct
{
    unsigned int address;
    unsigned int duration;
    unsigned int flags;
    unsigned int flip_flag;
    unsigned int sequence_index;
    unsigned int param_byte;
    unsigned int assembly;
    int valid;
} AvspPose;

/* A window of raw script bytes and the ROM address of its first byte. */
typedef struct
{
    const unsigned char *rom;
    unsigned int base;
    unsigned int size;
} AvspAnimScript;

/* Decode the pose record at ROM address `addr`. Sets `pose->valid` to 0 when
 * the record does not fit inside the window. */
void avsp_anim_read_pose(const AvspAnimScript *script, AvspPose *pose,
                         unsigned int addr);

/* The program counter the updater moves to after `pose` has been shown for its
 * full duration: the u32 stored at record+16 when flags bit 15 is set,
 * otherwise record+16. */
unsigned int avsp_anim_next_address(const AvspAnimScript *script,
                                    const AvspPose *pose);

/* Walk the loop beginning at `start`, filling `records` (up to `cap`) with the
 * ordered pose records until the walk returns to `start`. Returns the number of
 * records stored. Stops early if a record runs past the window. */
int avsp_anim_cycle(const AvspAnimScript *script, unsigned int start,
                    AvspPose *records, int cap);

/* Per-frame driver. `avsp_anim_frame_start` loads the first pose (ready to
 * render); `avsp_anim_frame_tick` is called once after each rendered frame and
 * advances to the pose for the next frame, holding the current pose for exactly
 * its duration frames, then following the bit-15 jump (or advancing 16). */
typedef struct
{
    unsigned int addr;
    unsigned int hold;
    AvspPose pose;
    int running;
} AvspAnimFrame;

void avsp_anim_frame_start(AvspAnimFrame *frame, const AvspAnimScript *script,
                           unsigned int start);
void avsp_anim_frame_tick(AvspAnimFrame *frame, const AvspAnimScript *script);

#endif /* AVSP_ANIM_SCRIPT_H */
