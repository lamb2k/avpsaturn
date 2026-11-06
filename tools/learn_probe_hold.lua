-- Learning probe: return chain at the task sleep wrapper 0x1060, command ring pushes,
-- wait-flag writes, object flips and the second fast-forward path. Wraps the retained route
-- script so input and route stay the same; adds only read/write taps. Output stays on this PC.
local cpu = manager.machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"]
local out = assert(io.open(os.getenv("AVSP_LEARN_PROBE_OUT"), "w"))
out:write("frame\tevent\tpc\ttask\tsp\td0\td1\tchain\n")
local f = 0
learn_frame = emu.add_machine_frame_notifier(function() f = f + 1; out:flush() end)
local function reg(n) return cpu.state[n].value end
local function log(ev, chain)
    out:write(string.format("%d\t%s\t%06x\t%06x\t%06x\t%x\t%x\t%s\n", f, ev, reg("PC") & 0xffffff,
        prog:read_u32(0xff025c) & 0xffffff, reg("SP") & 0xffffff, reg("D0") & 0xffffffff, reg("D1") & 0xffffffff, chain or ""))
end
learn_taps = {}
local function tap(pc, name, fn)
    learn_taps[#learn_taps + 1] = ops:install_read_tap(pc, pc + 1, "learn_" .. name, function()
        fn()
    end)
end
-- Return chain: ROM-range longs on the active stack, top 24 slots after 0x1060's movem is not yet run.
tap(0x1060, "sleep", function()
    local sp = reg("SP") & 0xffffff
    local c = {}
    for i = 0, 23 do
        local a = sp + i * 2
        if a < 0xfffffc then
            local v = prog:read_u32(a)
            if v > 0x400 and v < 0x100000 and (v & 1) == 0 then c[#c + 1] = string.format("%x", v) end
        end
    end
    log("sleep", table.concat(c, ","))
end)
tap(0x808a, "tick", function() log("tick") end)
tap(0x1620a, "ring_push", function() log("ring_push") end)
tap(0x14b1c, "ring_pop", function() log("ring_pop") end)
learn_flip = prog:install_write_tap(0xff81a4, 0xff81a5, "learn_flip", function() log("flip") end)
for _, pc in ipairs({ 0x158e0 }) do
    tap(pc, string.format("ff_%x", pc), function() log("ff_path") end)
end
learn_w837b = prog:install_write_tap(0xff837a, 0xff837b, "learn_837b", function(_, data, mask)
    if (mask & 0xff) ~= 0 then
        -- brightness census: largest top nibble of each palette's first colour, per bank
        local m = {}
        for b = 0, 3 do
            local mx, n = 0, 0
            for p = 0, 31 do
                local v = (prog:read_u16(0x90c000 + b * 0x400 + p * 0x20) >> 12) & 15
                if v > mx then mx = v end
                if v ~= 0 then n = n + 1 end
            end
            m[#m + 1] = string.format("%x/%d", mx, n)
        end
        log("w837b:" .. (data & 0xff), table.concat(m, " ") .. string.format(" g378=%x g1c2=%x g1c3=%x g1bd=%x", prog:read_u16(0xff8378), prog:read_u8(0xff81c2), prog:read_u8(0xff81c3), prog:read_u8(0xff81bd)))
    end
end)
learn_w1b9 = prog:install_write_tap(0xff81b8, 0xff81b9, "learn_1b9", function(_, data, mask)
    if (mask & 0xff) ~= 0 then log("w1b9:" .. (data & 0xff)) end
end)
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
