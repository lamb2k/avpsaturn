-- Lane wolverine-native: dump ranges of the 68k program space (ROM tables the player code indexes) under MAME avspu. Env RD_OUT, RD_RANGES="start:len,start:len" (hex).
local prog = manager.machine.devices[":maincpu"].spaces["opcodes"] or manager.machine.devices[":maincpu"].spaces["program"]
local n = 0
am_f = emu.add_machine_frame_notifier(function()
    n = n + 1
    if n < 30 then return end
    local f = assert(io.open(assert(os.getenv("RD_OUT")), "w"))
    for r in string.gmatch(os.getenv("RD_RANGES"), "[^,]+") do
        local s, l = r:match("(%x+):(%x+)")
        s, l = tonumber(s, 16), tonumber(l, 16)
        for a = s, s + l - 1, 16 do
            local t = {}
            for i = 0, 15 do if a + i < s + l then t[#t + 1] = string.format("%02x", prog:read_u8(a + i)) end end
            f:write(string.format("%06x: %s\n", a, table.concat(t, " ")))
        end
    end
    f:close(); manager.machine:exit()
end)
