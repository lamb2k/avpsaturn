-- Taps sit 4 bytes in: at the entry fetch the jsr has not yet pushed its return address.
-- Actor lane probe: pool alloc/release calls with caller and owner, spawn table steps, and writes to
-- actor fields +0x2c (timer) and +0x40 (health). Route input unchanged. Output stays on this PC.
local cpu = manager.machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"]
local out = assert(io.open(os.getenv("AVSP_LEARN_PROBE_OUT"), "w"))
out:write("frame\tevent\tpc\tcaller\ta6\ta6_active\ta6_type\ta6_class\ta6_state\tslot\tcount\tdata\tmask\n")
local f = 0
learn_frame = emu.add_machine_frame_notifier(function() f = f + 1; out:flush() end)
local function reg(n) return cpu.state[n].value end
local function log(ev, caller, slot, count, data, mask)
    local a6 = reg("A6") & 0xffffff
    local act, ty, cl, st = 0, 0, 0, 0
    if a6 >= 0xff0000 then
        act, cl, ty, st = prog:read_u8(a6), prog:read_u8(a6 + 2), prog:read_u8(a6 + 8), prog:read_u16(a6 + 4)
    end
    out:write(string.format("%d\t%s\t%06x\t%06x\t%06x\t%x\t%x\t%x\t%x\t%06x\t%d\t%x\t%x\n", f, ev, reg("PC") & 0xffffff,
        caller or 0, a6, act, ty, cl, st, slot or 0, count or 0, data or 0, mask or 0))
end
learn_taps = {}
local function tap(pc, name, fn)
    learn_taps[#learn_taps + 1] = ops:install_read_tap(pc, pc + 1, "learn_" .. name, fn)
end
local function stack() return ((reg("SR") & 0x2000) ~= 0 and reg("SP") or reg("USP")) & 0xffffff end
local function ret() return prog:read_u32(stack()) & 0xffffff end
local pools = {
    { 8, 0x17654, 0x1766a, 0xffee7e, 0xffee54 }, { 12, 0x1769e, 0x176b4, 0xffee80, 0xffee58 },
    { 20, 0x176f0, 0x17706, 0xffee85, 0xffee62 }, { 4, 0x1773e, 0x17754, 0xffee7c, 0xffee50 },
    { 16, 0x1778c, 0x177a2, 0xffee83, 0xffee5e }, { 24, 0x177da, 0x177f0, 0xffee89, 0xffee6a },
    { 28, 0x17828, 0x1783e, 0xffee8c, 0xffee70 }, { 36, 0x17876, 0x1788c, 0xffee8f, 0xffee76 },
    { 32, 0x178a8, 0x178be, 0xffee8e, 0xffee74 }, { 40, 0x178da, 0x178f0, 0xffee90, 0xffee78 },
}
for _, p in ipairs(pools) do
    tap(p[2] + 4, "a" .. p[1], function()
        local n = prog:read_u8(p[4])
        local top = n > 0 and (0xff0000 | prog:read_u16(0xff0000 | prog:read_u16(p[5]))) or 0
        log("alloc" .. p[1], ret(), top, n)
    end)
    tap(p[3] + 4, "r" .. p[1], function() log("free" .. p[1], ret(), reg("A6") & 0xffffff, prog:read_u8(p[4])) end)
end
tap(0x1bf1a, "tbl", function()
    local a1, a4 = reg("A1") & 0xffffff, reg("A4") & 0xffffff
    log("table", a1, a4, 0, prog:read_u16(a1 + 8), prog:read_u16(a1 + 6))
end)
tap(0x1bf50, "tbl1c", function() log("table1c", reg("A1") & 0xffffff, 0, 0, prog:read_u16((reg("A1") & 0xffffff) + 8)) end)
tap(0x1bf5e, "tbl18", function() log("table18", reg("A1") & 0xffffff, 0, 0, prog:read_u16((reg("A1") & 0xffffff) + 8)) end)
local strides = {
    { 0xff8380, 0xff8680, 0x300 }, { 0xff8680, 0xff9280, 0x80 }, { 0xff9280, 0xffa480, 0xc0 }, { 0xffa480, 0xffc680 + 0x800, 0x80 },
    { 0xffce80, 0xffd280, 0x100 }, { 0xffd280, 0xffe280, 0x40 },
}
local function slot_of(a)
    for _, s in ipairs(strides) do
        if a >= s[1] and a < s[2] then return s[1] + ((a - s[1]) // s[3]) * s[3], s[3] end
    end
end
learn_fields = prog:install_write_tap(0xff8380, 0xffe27f, "learn_fields", function(off, data, mask)
    local a = off & 0xfffffe
    local s = slot_of(a)
    if not s then return end
    local o = a - s
    if o == 0x2c or o == 0x40 then
        local act, cl, ty = prog:read_u8(s), prog:read_u8(s + 2), prog:read_u8(s + 8)
        local old = prog:read_u16(a)
        out:write(string.format("%d\tw%02x\t%06x\t%06x\t%06x\t%x\t%x\t%x\t%x\t%06x\t%d\t%x\t%x\n", f, o, reg("PC") & 0xffffff,
            ret(), reg("A6") & 0xffffff, act, ty, cl, prog:read_u16(s + 4), s, old, data, mask))
    end
end)
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
