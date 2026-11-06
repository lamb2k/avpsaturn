-- Golden run for the whole-game check. At each level 2 IRQ entry (0xe0e fetch) dump work RAM and object RAM, in order.
-- Also log every read of I/O space in order, so the host can replay the board's inputs, EEPROM and sound status.
-- Output stays on this PC: AVSP_LEARN_PROBE_OUT = frames.bin; alongside it io.txt.
local cpu = manager.machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"]
local path = os.getenv("AVSP_LEARN_PROBE_OUT")
local out = assert(io.open(path, "wb"))
local iolog = assert(io.open(path .. ".io.txt", "w"))
local maxirq = tonumber(os.getenv("LEARN_MAXIRQ") or "6000")
local irq = 0
local function dump(base, n)
    local t = {}
    for i = 0, n - 4, 4 do t[#t + 1] = string.pack(">I4", prog:read_u32(base + i)) end
    out:write(table.concat(t))
end
learn_g1 = ops:install_read_tap(0xe0e, 0xe0f, "learn_golden", function()
    -- The tap also fires on prefetch past the rte at 0xe0c. At a real IRQ entry PC still reads as the vector, 0x68, and the frame is at SP.
    if cpu.state["PC"].value ~= 0x68 then return end
    if irq < maxirq then
        out:write(string.pack(">c4I4", "VBLK", irq))
        -- Interrupted point: stacked PC, then d0-d7, a0-a6, so the host can take this IRQ at the same instruction.
        local sp = cpu.state["SP"].value
        local rr = {prog:read_u32(sp + 2) & 0xffffff}
        for i = 0, 7 do rr[#rr + 1] = cpu.state["D" .. i].value end
        for i = 0, 6 do rr[#rr + 1] = cpu.state["A" .. i].value end
        out:write(string.pack(">" .. string.rep("I4", 16), table.unpack(rr)))
        dump(0xff0000, 0x10000)
        dump(0x708000, 0x2000)
        out:flush()
    end
    irq = irq + 1
    iolog:write("V\n")
end)
local function rt(name, a, b)
    return prog:install_read_tap(a, b, name, function(off, data, mask)
        iolog:write(string.format("%x %x %x\n", off, data, mask))
    end)
end
learn_g2 = rt("learn_io1", 0x800000, 0x80ffff)
learn_g3 = rt("learn_io2", 0x618000, 0x619fff)
learn_g4 = emu.add_machine_frame_notifier(function() iolog:flush() end)
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
