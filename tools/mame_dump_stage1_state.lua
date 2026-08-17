local machine = manager.machine
local frame = 0

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

stage1_dump_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    if frame ~= 120 then return end

    print("AVSPU_MEMORY_BEGIN")
    for tag, share in pairs(machine.memory.shares) do
        print(string.format("%s size=0x%x width=%d endian=%s", tag, share.size,
            share.bitwidth, share.endianness))
    end
    for tag, region in pairs(machine.memory.regions) do
        print(string.format("REGION %s size=0x%x width=%d endian=%s", tag,
            region.size, region.bitwidth, region.endianness))
    end
    print("AVSPU_MEMORY_END")

    write_share_words(".deps/mame/captures/objram1.tsv", machine.memory.shares[":objram1"])
    write_share_words(".deps/mame/captures/objram2.tsv", machine.memory.shares[":objram2"])
    write_share_words(".deps/mame/captures/output.tsv", machine.memory.shares[":output"])
    write_share_words(".deps/mame/captures/cps_a_regs.tsv", machine.memory.shares[":cps_a_regs"])
    write_share_words(".deps/mame/captures/gfxram.tsv", machine.memory.shares[":gfxram"])
    write_palette(".deps/mame/captures/palette.tsv")
    machine.screens[":screen"]:snapshot("stage1_state.png")
    machine:exit()
end)
