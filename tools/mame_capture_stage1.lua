local machine = manager.machine
local screen = machine.screens[":screen"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local right = in0["P1 Right"]
-- Capcom control panel order: Button 1 = weapon/gun, Button 2 = attack,
-- Button 3 = jump/dash. Keep these names exact so captured action labels do
-- not drift from the original input matrix again.
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]
local frame = 0
local active_object_bank = 0
local object_bank_writes = 0
local animation_metadata = assert(io.open(
    ".deps/mame/captures/animation_samples.tsv", "w"))
animation_metadata:write("frame\tactive_object_bank\tbank_writes\n")

-- CPS2 presents one object-RAM bank while the game fills the other. Track the
-- write-only bank-select register so every sample names the bank MAME latches
-- for display rather than asking the extractor to infer it later.
local main_program = machine.devices[":maincpu"].spaces["program"]
stage1_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "stage1_object_bank",
    function(offset, data, mask)
        active_object_bank = data & 1
        object_bank_writes = object_bank_writes + 1
    end)

local function write_share_words(path, share)
    local file = assert(io.open(path, "w"))
    file:write("word\tvalue\n")
    for offset = 0, share.size - 2, 2 do
        file:write(string.format("%04x\t%04x\n", offset / 2, share:read_u16(offset)))
    end
    file:close()
end

local function write_palette(path)
    local palette = machine.palettes[":palette"]
    local file = assert(io.open(path, "w"))
    file:write("index\targb\n")
    for index = 0, palette.entries - 1 do
        file:write(string.format("%04x\t%08x\n", index, palette:pen_color(index)))
    end
    file:close()
end

local function dump_stage_state()
    local shares = assert(io.open(".deps/mame/captures/shares.tsv", "w"))
    shares:write("tag\tsize\tbitwidth\tendianness\n")
    for tag, share in pairs(machine.memory.shares) do
        shares:write(string.format("%s\t%x\t%d\t%s\n", tag, share.size,
            share.bitwidth, share.endianness))
    end
    shares:close()

    write_share_words(".deps/mame/captures/objram1.tsv", machine.memory.shares[":objram1"])
    write_share_words(".deps/mame/captures/objram2.tsv", machine.memory.shares[":objram2"])
    write_share_words(".deps/mame/captures/output.tsv", machine.memory.shares[":output"])
    write_share_words(".deps/mame/captures/cps_a_regs.tsv", machine.memory.shares[":cps_a_regs"])
    if machine.memory.shares[":cps_b_regs"] then
        write_share_words(".deps/mame/captures/cps_b_regs.tsv", machine.memory.shares[":cps_b_regs"])
    end
    write_share_words(".deps/mame/captures/gfxram.tsv", machine.memory.shares[":gfxram"])

    write_palette(".deps/mame/captures/palette.tsv")

    local bank_file = assert(io.open(
        ".deps/mame/captures/active_object_bank.txt", "w"))
    bank_file:write(string.format("%d\n", active_object_bank + 1))
    bank_file:close()

    -- Keep a byte-for-byte copy of the post-ROM-loader graphics region.  The
    -- extraction tool compares its own ROM interleave against this diagnostic
    -- dump so a visually plausible but byte-wrong decode cannot slip through.
    local gfx = machine.memory.regions[":gfx"]
    local gfx_file = assert(io.open(".deps/mame/captures/gfx_region.bin", "wb"))
    local chunk_size = 0x100000
    for offset = 0, gfx.size - 1, chunk_size do
        gfx_file:write(gfx:read(offset, math.min(chunk_size, gfx.size - offset)))
    end
    gfx_file:close()
end

local function dump_animation_sample(sample_frame)
    write_share_words(string.format(".deps/mame/captures/objram1_%04d.tsv", sample_frame),
        machine.memory.shares[":objram1"])
    write_share_words(string.format(".deps/mame/captures/objram2_%04d.tsv", sample_frame),
        machine.memory.shares[":objram2"])
    write_share_words(string.format(".deps/mame/captures/output_%04d.tsv", sample_frame),
        machine.memory.shares[":output"])
    local active_share = active_object_bank == 0 and
        machine.memory.shares[":objram1"] or machine.memory.shares[":objram2"]
    write_share_words(string.format(
        ".deps/mame/captures/objram_active_%04d.tsv", sample_frame), active_share)
    write_palette(string.format(
        ".deps/mame/captures/palette_%04d.tsv", sample_frame))
    animation_metadata:write(string.format("%d\t%d\t%d\n",
        sample_frame, active_object_bank + 1, object_bank_writes))
    animation_metadata:flush()
end

stage1_capture_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    -- The USA set spends roughly 34 seconds in legal, QSound, Capcom and
    -- opening screens before it accepts a credit. Repeat short pulses across
    -- the attract transition so this remains stable if ROM timing shifts.
    if frame >= 1200 and frame <= 2400 then
        if (frame - 1200) % 180 == 0 then coin:set_value(1) end
        if (frame - 1200) % 180 == 3 then coin:clear_value() end
        if (frame - 1200) % 180 == 30 then start:set_value(1) end
        if (frame - 1200) % 180 == 33 then start:clear_value() end
    end

    -- Select the default character, then exercise the gun action during the
    -- opening playable section.
    if frame >= 1500 and frame < 4200 then
        if frame % 90 == 0 then gun:set_value(1) end
        if frame % 90 == 5 then gun:clear_value() end
    end

    if frame == 2600 then right:set_value(1) end
    if frame >= 2600 and frame < 4200 then
        if frame % 75 == 0 then gun:set_value(1) end
        if frame % 75 == 6 then gun:clear_value() end
        if frame % 310 == 0 then attack:set_value(1) end
        if frame % 310 == 7 then attack:clear_value() end
        if frame % 430 == 0 then jump:set_value(1) end
        if frame % 430 == 7 then jump:clear_value() end
    end

    if frame % 120 == 0 then
        screen:snapshot(string.format("stage1_%04d.png", frame))
        print(string.format("AVSPU_CAPTURE frame=%d", frame))
    end

    if frame >= 2760 and frame <= 4200 and frame % 4 == 0 then
        screen:snapshot(string.format("stage1_sample_%04d.png", frame))
        dump_animation_sample(frame)
    end

    if frame == 4200 then
        right:clear_value()
        gun:clear_value()
        attack:clear_value()
        jump:clear_value()
        dump_stage_state()
        machine:save("avspu_stage1")
    end
    if frame == 4220 then
        animation_metadata:close()
        machine:exit()
    end
end)
