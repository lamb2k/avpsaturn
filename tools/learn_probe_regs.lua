-- At each write to a RAM word log registers and the top stack longs. AVSP_WATCH="start end" hex.
local cpu = manager.machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local out = assert(io.open(os.getenv("AVSP_LEARN_PROBE_OUT"), "w"))
local a, b = os.getenv("AVSP_WATCH"):match("(%x+) (%x+)")
a, b = tonumber(a, 16), tonumber(b, 16)
local function r(n) return cpu.state[n].value end
learn_w = prog:install_write_tap(a, b, "learn_watch", function(off, data, mask)
    local sp = r("SP")
    out:write(string.format("%x %x pc %x d0-3 %x %x %x %x a0 %x a4 %x a6 %x sp %x ret %x %x irq %x\n", off, data, r("PC"), r("D0"), r("D1"), r("D2"), r("D3"), r("A0"), r("A4"), r("A6"), sp, prog:read_u32(sp), prog:read_u32(sp+4), prog:read_u16(0xff8018)))
    out:flush()
end)
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
