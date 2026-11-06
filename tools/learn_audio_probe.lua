-- Audio ring probe: per-frame head/tail/handshake and Z80 ring, plus enqueue and send events. Write and read taps only,
-- except AVSP_LEARN_FORCE_FF="first:last", which holds ff81b9 nonzero in that window (a labelled forced condition).
local cpu = manager.machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local z80 = manager.machine.devices[":audiocpu"].spaces["program"]
local out = assert(io.open(os.getenv("AVSP_LEARN_PROBE_OUT"), "w"))
local ff1, ff2 = (os.getenv("AVSP_LEARN_FORCE_FF") or "0:0"):match("(%d+):(%d+)")
ff1, ff2 = tonumber(ff1), tonumber(ff2)
out:write("frame\tevent\ta\tb\tc\td\te\tf\n")
local f = 0
local function rs(a) return prog:read_u16(a) end
learn_frame = emu.add_machine_frame_notifier(function()
    f = f + 1
    if f >= ff1 and f <= ff2 then prog:write_u8(0xff81b9, 1) end
    out:write(string.format("%d\tF\t%x\t%x\t%x\t%x\t%x\t%x\n", f, rs(0xff801e), rs(0xff8020), prog:read_u8(0x61801f),
        prog:read_u8(0xff81b9), prog:read_u8(0xff81ad) * 256 + prog:read_u8(0xff81b0), z80:read_u8(0xf007) * 256 + z80:read_u8(0xf008)))
    out:flush()
end)
local function reg(n) return cpu.state[n].value end
learn_tail = prog:install_write_tap(0xff8020, 0xff8021, "learn_tail", function(_, data)
    local t = (reg("D0") - 0x10) & 0x3f0
    if reg("PC") & 0xffffff < 0x1940 then return end
    out:write(string.format("%d\tE\t%x\t%08x\t%08x\t%08x\t%06x\t\n", f, t, reg("D1") & 0xffffffff, reg("D2") & 0xffffffff, reg("D3") & 0xffffffff, reg("A6") & 0xffffff))
end)
learn_head = prog:install_write_tap(0xff801e, 0xff801f, "learn_head", function(_, data)
    if reg("PC") & 0xffffff < 0x1900 then return end
    out:write(string.format("%d\tS\t%x\t\t\t\t\t\n", f, (reg("D0") - 0x10) & 0x3f0))
end)
learn_tick = cpu.spaces["opcodes"]:install_read_tap(0x808a, 0x808b, "learn_tick", function() out:write(string.format("%d\tT\t\t\t\t\t\t\n", f)) end)
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
