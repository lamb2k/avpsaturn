-- Capture real entry states: for the first K fetches of each function entry, registers and RAM.
-- Binary records to AVSP_LEARN_PROBE_OUT: "CASE" addr frame, 16 u32 regs, RAM 64K, palette/tile 64K, objects 8K.
local cpu = manager.machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"]
local out = assert(io.open(os.getenv("AVSP_LEARN_PROBE_OUT"), "wb"))
local K = tonumber(os.getenv("LEARN_K") or "2")
local first = tonumber(os.getenv("LEARN_FIRST") or "2000")
local entry = {}
for a in io.open("E:/AvP/learning/lift/entries.txt"):read("a"):gmatch("%x+") do entry[tonumber(a, 16)] = 0 end
local f = 0
learn_f = emu.add_machine_frame_notifier(function() f = f + 1; out:flush() end)
local names = {"D0","D1","D2","D3","D4","D5","D6","D7","A0","A1","A2","A3","A4","A5","A6","SP"}
local busy = false
local function dump(base, n)
    local t = {}
    for i = 0, n - 4, 4 do t[#t + 1] = string.pack(">I4", prog:read_u32(base + i)) end
    out:write(table.concat(t))
end
learn_t = ops:install_read_tap(0, 0xfffff, "learn_entries", function(o)
    local a = o & 0xffffe
    local n = entry[a]
    if n == nil or n >= K or f < first or busy then return end
    busy = true
    entry[a] = n + 1
    out:write(string.pack(">c4I4I4", "CASE", a, f))
    for i = 1, 16 do out:write(string.pack(">I4", cpu.state[names[i]].value & 0xffffffff)) end
    dump(0xff0000, 0x10000)
    dump(0x900000, 0x10000)
    dump(0x700000, 0x2000)
    busy = false
end)
dofile("tools/mame_capture_oracle11_round1_route.lua")
