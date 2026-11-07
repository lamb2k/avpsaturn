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
-- LEARN_DELTA=1: every IRQ still has its record, but only the 32-bit words that changed since the last record are written:
-- u32 run count, then per run u16 first word, u16 words, data. Word index counts work RAM from 0, object RAM from 0x4000. First record is all changed.
local delta = os.getenv("LEARN_DELTA") == "1"
local prevw = {}
local RUNS_NW = 0x4800
function delta_dump()
    local cur = {}
    for i = 0, 0x3fff do cur[i] = prog:read_u32(0xff0000 + i * 4) end
    for i = 0, 0x7ff do cur[0x4000 + i] = prog:read_u32(0x708000 + i * 4) end
    local t, nruns, i = {}, 0, 0
    while i < RUNS_NW do
        if cur[i] ~= prevw[i] then
            local b = i
            while i < RUNS_NW and cur[i] ~= prevw[i] and i - b < 0xffff do i = i + 1 end
            t[#t + 1] = string.pack(">I2I2", b, i - b)
            for k = b, i - 1 do t[#t + 1] = string.pack(">I4", cur[k]) end
            nruns = nruns + 1
        else i = i + 1 end
    end
    out:write(string.pack(">I4", nruns)); out:write(table.concat(t))
    prevw = cur
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
        if delta then delta_dump() else
        dump(0xff0000, 0x10000)
        dump(0x708000, 0x2000)
        end
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
-- AVSP_ROUTE: a saved input file (tools/make_route.py), real ports only. Without it the retained route harness drives the run.
-- LEARN_SAVE="frame,frame": MAME state saves at those frames, named by frame, for state fixtures (item 14).
local route = os.getenv("AVSP_ROUTE")
if route then
    local in0 = manager.machine.ioport.ports[":IN0"].fields
    local in2 = manager.machine.ioport.ports[":IN2"].fields
    local F = {in2["Coin 1"], in2["1 Player Start"], in0["P1 Left"], in0["P1 Right"], in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"], in0["P1 Up"], in0["P1 Down"]}
    for _, n in ipairs{{2, "Coin 2"}, {2, "2 Players Start"}, {0, "P2 Left"}, {0, "P2 Right"}, {0, "P2 Button 1"}, {0, "P2 Button 2"}, {0, "P2 Button 3"}, {0, "P2 Up"}, {0, "P2 Down"}} do F[#F + 1] = (n[1] == 2 and in2 or in0)[n[2]] end   -- route word bits 9 to 17
    local steps, last = {}, nil
    for l in io.lines(route) do
        local a, b = l:match("^(%d+) (%d+)")
        if a then steps[tonumber(a)] = tonumber(b) else last = tonumber(l:match("^last (%d+)")) end
    end
    last = tonumber(os.getenv("LEARN_LAST") or "") or last
    local saves = {}
    for n in (os.getenv("LEARN_SAVE") or ""):gmatch("%d+") do saves[tonumber(n)] = true end
    local frame = 0
    learn_g5 = emu.add_machine_frame_notifier(function()
        frame = frame + 1
        local w = steps[frame]
        if w then
            for i, f in ipairs(F) do
                if w & (1 << (i - 1)) ~= 0 then f:set_value(1) else f:clear_value() end
            end
        end
        if saves[frame] then manager.machine:save("f" .. frame) end
        if frame == last then iolog:close(); out:close(); manager.machine:exit() end
    end)
else
    dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
end
