-- How the IRQ frame looks at the first fetch of 0xe0e.
local cpu = manager.machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"]
local out = assert(io.open(os.getenv("AVSP_LEARN_PROBE_OUT"), "w"))
local names = {}
for k, _ in pairs(cpu.state) do names[#names + 1] = k end
out:write(table.concat(names, " ") .. "\n"); out:flush()
local n = 0
local function st(k) local v = cpu.state[k]; return v and v.value or -1 end
learn_w = ops:install_read_tap(0xe0e, 0xe0f, "learn_i", function()
    n = n + 1
    if n < 30 then
        local s = st("SP")
        local t = {}
        for o = -8, 8, 2 do t[#t + 1] = string.format("%04x", prog:read_u16(s + o)) end
        out:write(string.format("%d sp %x pc %x cur %x : %s\n", n, s, st("PC"), st("CURPC"), table.concat(t, " ")))
        out:flush()
    end
end)
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
