#include <assert.h>
#include <stdio.h>

#include "../avsp_anim_script.h"
#include "../generated/avsp_boss_anim_script.h"

/* The boss animation script window the interpreter walks. */
static const AvspAnimScript script = {
    avsp_boss_anim_script,
    AVSP_BOSS_ANIM_SCRIPT_BASE,
    AVSP_BOSS_ANIM_SCRIPT_SIZE
};

/* Walk each of the six canonical programs and require the decoded records to
 * match the expected (JSON-validated) table, in order, with the loop closed. */
static void test_programs_match_expected(void)
{
    int program;

    for (program = 0; program < AVSP_BOSS_ANIM_PROGRAM_COUNT; ++program)
    {
        unsigned int start;
        int first;
        int last;
        int count;
        int got;
        int i;
        AvspPose records[16];

        start = avsp_boss_anim_program_start[program];
        first = avsp_boss_anim_record_offset[program];
        last = avsp_boss_anim_record_offset[program + 1];
        count = last - first;

        got = avsp_anim_cycle(&script, start, records, 16);
        assert(got == count);
        for (i = 0; i < got; ++i)
        {
            int e = first + i;
            assert(records[i].valid == 1);
            assert(records[i].address == avsp_boss_anim_exp_address[e]);
            assert(records[i].duration == avsp_boss_anim_exp_duration[e]);
            assert(records[i].flags == avsp_boss_anim_exp_flags[e]);
            assert(records[i].flip_flag ==
                   ((avsp_boss_anim_exp_flags[e] >> 15) & 1u));
            assert(records[i].sequence_index == avsp_boss_anim_exp_seq[e]);
            assert(records[i].param_byte == avsp_boss_anim_exp_param[e]);
            assert(records[i].assembly == avsp_boss_anim_exp_assembly[e]);
        }
        /* The loop must close on the start address. */
        assert(avsp_anim_next_address(&script, &records[got - 1]) == start);
    }

    printf("anim-script: %d programs, record tables and loop closure match.\n",
           AVSP_BOSS_ANIM_PROGRAM_COUNT);
}

/* A synthetic three-record program, built by hand, proves the per-frame driver
 * holds each pose for exactly its duration frames and then follows the bit-15
 * jump back around the loop.
 *
 *   rec0 @+0   dur 2  flags 0x0000  assembly 0xA   (advance to rec1)
 *   rec1 @+16  dur 1  flags 0x0000  assembly 0xB   (advance to rec2)
 *   rec2 @+32  dur 3  flags 0x8000  assembly 0xC   (jump to the word @+48)
 *   @+48       u32 = SYNTH_BASE                                        (loop)
 *
 * Rendered assembly sequence: A A B C C C A ... */
#define SYNTH_BASE 0x100000u
static const unsigned char synth_rom[] = {
    0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0A, 0, 0, 0, 0, 0, 0, 0, 0,
    0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0, 0, 0, 0, 0, 0, 0, 0,
    0x00, 0x03, 0x80, 0x00, 0x00, 0x00, 0x00, 0x0C, 0, 0, 0, 0, 0, 0, 0, 0,
    0x00, 0x10, 0x00, 0x00
};

static void test_frame_hold_and_jump(void)
{
    AvspAnimScript s = { synth_rom, SYNTH_BASE, sizeof(synth_rom) };
    AvspAnimFrame f;
    unsigned int expected_asm[7] = {0xA, 0xA, 0xB, 0xC, 0xC, 0xC, 0xA};
    int i;

    avsp_anim_frame_start(&f, &s, SYNTH_BASE);
    for (i = 0; i < 7; ++i)
    {
        assert(f.pose.assembly == expected_asm[i]);
        avsp_anim_frame_tick(&f, &s);
    }

    printf("anim-script: duration hold + bit-15 jump loop verified.\n");
}

int main(void)
{
    test_programs_match_expected();
    test_frame_hold_and_jump();
    printf("All avsp_anim_script tests passed.\n");
    return 0;
}
