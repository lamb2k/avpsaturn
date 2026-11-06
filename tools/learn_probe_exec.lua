-- First-gate probe: 68000 word fetch counts by address over the Coffee Shop route, and totals per frame.
local cpu = manager.machine.devices[":maincpu"]
local ops = cpu.spaces["opcodes"]
local out = os.getenv("AVSP_LEARN_PROBE_OUT")
local counts, frames, f, cur = {}, {}, 0, 0
learn_exec = ops:install_read_tap(0, 0xfffff, "learn_exec", function(o)
    local a = o & 0xffffe
    if (a >= 0x14b44 and a < 0x14b92) or (a >= 0xd86 and a < 0xe0e) or (a >= 0x1092 and a < 0x109a) then return end
    counts[a] = (counts[a] or 0) + 1
    cur = cur + 1
end)
local function dump()
    local h = assert(io.open(out, "w"))
    for fr, n in pairs(frames) do h:write(string.format("F %d %d\n", fr, n)) end
    for a, n in pairs(counts) do h:write(string.format("%x %d\n", a, n)) end
    h:close()
end
learn_exec_f = emu.add_machine_frame_notifier(function()
    frames[f] = cur; cur = 0; f = f + 1
    if f % 500 == 0 then dump() end
end)
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
