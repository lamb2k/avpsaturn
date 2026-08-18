#include "avsp_anim_script.h"

static unsigned int read_u16_be(const unsigned char *d)
{
    return ((unsigned int)d[0] << 8) | (unsigned int)d[1];
}

static unsigned int read_u32_be(const unsigned char *d)
{
    return (((unsigned int)d[0] << 24) | ((unsigned int)d[1] << 16) |
            ((unsigned int)d[2] << 8) | (unsigned int)d[3]);
}

const unsigned char *avsp_anim_resolve(const AvspAnimScript *script,
                                       unsigned int addr, unsigned int need)
{
    long off;

    if (script->spans != 0 && script->span_count != 0u) {
        unsigned int i;
        for (i = 0u; i < script->span_count; ++i) {
            const AvspAnimSpan *s = &script->spans[i];
            if (addr >= s->base && (addr - s->base) + need <= s->size) {
                return s->data + (addr - s->base);
            }
        }
        return 0;
    }
    if (script->rom == 0) {
        return 0;
    }
    off = (long)addr - (long)script->base;
    if (off < 0 || off + (long)need > (long)script->size) {
        return 0;
    }
    return script->rom + off;
}

void avsp_anim_read_pose(const AvspAnimScript *script, AvspPose *pose,
                         unsigned int addr)
{
    const unsigned char *d;

    pose->valid = 0;
    pose->address = addr;
    pose->duration = 0;
    pose->flags = 0;
    pose->flip_flag = 0;
    pose->sequence_index = 0;
    pose->param_byte = 0;
    pose->assembly = 0;

    d = avsp_anim_resolve(script, addr, 16u);
    if (d == 0)
        return;
    pose->duration = read_u16_be(d);
    pose->flags = read_u16_be(d + 2);
    pose->assembly = read_u32_be(d + 4);
    pose->flip_flag = (pose->flags >> 15) & 1u;
    pose->sequence_index = (pose->flags >> 8) & 0x7Fu;
    pose->param_byte = pose->flags & 0xFFu;
    pose->valid = 1;
}

unsigned int avsp_anim_next_address(const AvspAnimScript *script,
                                    const AvspPose *pose)
{
    const unsigned char *d;
    unsigned int target;

    if (pose->flags & 0x8000u) {
        d = avsp_anim_resolve(script, pose->address + 16u, 4u);
        if (d != 0) {
            target = read_u32_be(d);
            /* A jump target counts only when its record is actually present. */
            if (avsp_anim_resolve(script, target, 16u) != 0)
                return target;
        }
    }
    return pose->address + 16u;
}

int avsp_anim_cycle(const AvspAnimScript *script, unsigned int start,
                    AvspPose *records, int cap)
{
    int count;
    unsigned int addr;
    unsigned int nxt;
    AvspPose pose;

    count = 0;
    addr = start;
    while (count < cap) {
        avsp_anim_read_pose(script, &pose, addr);
        if (!pose.valid)
            break;
        records[count] = pose;
        count += 1;
        nxt = avsp_anim_next_address(script, &pose);
        if (nxt == start)
            break;
        addr = nxt;
    }
    return count;
}

void avsp_anim_frame_start(AvspAnimFrame *frame, const AvspAnimScript *script,
                           unsigned int start)
{
    frame->addr = start;
    avsp_anim_read_pose(script, &frame->pose, start);
    frame->hold = frame->pose.valid && frame->pose.duration > 0
                      ? frame->pose.duration
                      : 0;
    frame->running = frame->pose.valid;
}

void avsp_anim_frame_tick(AvspAnimFrame *frame, const AvspAnimScript *script)
{
    unsigned int nxt;

    if (!frame->running)
        return;
    frame->hold--;
    while (frame->hold <= 0 && frame->running) {
        nxt = avsp_anim_next_address(script, &frame->pose);
        avsp_anim_read_pose(script, &frame->pose, nxt);
        frame->addr = nxt;
        if (!frame->pose.valid) {
            frame->running = 0;
            return;
        }
        if (frame->pose.duration == 0)
            continue;
        frame->hold = frame->pose.duration;
    }
}
