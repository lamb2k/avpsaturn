-- Per-section census over a saved route, for lane avp-rounds: tile keys (same lookup rules as satint_census.lua), sound commands (ring entries),
-- ROM words read through program space (register reads) and opcode space (fetches and pc-relative reads). Tier: MAME. ROM-derived addresses only.
-- Env: AVSP_ROUTE, CENSUS_RAW (out file). Sets are keyed by "stage/section" at each read; section 0 between sections keeps its stage.
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"]
local rd = function(a) return prog:read_u16(a) end
local NL = string.char(10)
local sets, order = {}, {}
local cur
local function key_set(k)
    local s = sets[k]
    if not s then
        s = {k = k, t = {{}, {}, {}, {}}, snd = {}, pr = {}, op = {}, first = 0, last = 0, irq = 0, maxobj = 0}
        sets[k] = s; order[#order + 1] = k
    end
    return s
end
cur = key_set("0000/00")
local frame, snap_at = 0, -1
local function tiles(s)
    local n, kk = 0, s.t[1]
    while n < 0x400 do
        local o = 0x708000 + n * 8
        local yw, aw = rd(o + 2), rd(o + 6)
        if yw >= 0x8000 or aw >= 0xff00 then break end
        local code = rd(o + 4) + ((yw & 0x6000) << 3)
        local nx, ny = ((aw >> 8) & 15) + 1, ((aw >> 12) & 15) + 1
        local fx, fy = aw & 0x20 ~= 0, aw & 0x40 ~= 0
        for ty = 0, ny - 1 do for tx = 0, nx - 1 do
            local t
            if fx or fy then t = code + (fx and nx - 1 - tx or tx) + 0x10 * (fy and ny - 1 - ty or ty)
            else t = (code & ~15) + ((code + tx) & 15) + 0x10 * ty end
            kk[t] = true
        end end
        n = n + 1
    end
    if n > s.maxobj then s.maxobj = n end
    local f = 0xff8000
    local layers = rd(f + 0x4a)
    local base = function(off) return (rd(f + off) & 0xffc0) * 0x100 end
    local s1x, s1y, s2y, s3x, s3y = rd(0xffee1a), rd(0xffee1c), rd(0xffee20), rd(0xffee22), rd(0xffee24)
    if layers & 2 ~= 0 then
        local m, x0, y0 = base(0x24), s1x + 80, s1y + 16
        for row = 0, 28 do for col = 0, 44 do
            local c, r = ((x0 >> 3) + col) & 63, ((y0 >> 3) + row) & 63
            local i = (r & 0x1f) + (c << 5) + ((r & 0x20) << 6)
            s.t[2][(rd(m + i * 4) << 1) | ((i >> 5) & 1)] = true
        end end
    end
    if layers & 4 ~= 0 then
        local m, y0 = base(0x26), s2y + 16
        for row = 0, 14 do for c = 0, 63 do
            local r = ((y0 >> 4) + row) & 63
            local i = (r & 0xf) + (c << 4) + ((r & 0x30) << 6)
            s.t[3][rd(m + i * 4)] = true
        end end
    end
    if layers & 8 ~= 0 then
        local m, x0, y0 = base(0x28), s3x + 80, s3y + 16
        for row = 0, 7 do for col = 0, 11 do
            local c, r = ((x0 >> 5) + col) & 63, ((y0 >> 5) + row) & 63
            local i = (r & 7) + (c << 3) + ((r & 0x38) << 6)
            s.t[4][rd(m + i * 4) & 0x3fff] = true
        end end
    end
end
census_irq = ops:install_read_tap(0xe0e, 0xe0f, "census_irq", function()
    if cpu.state["PC"].value ~= 0x68 then return end
    cur.irq = cur.irq + 1
    tiles(cur)
end)
census_tail = prog:install_write_tap(0xff8020, 0xff8021, "census_tail", function()
    if cpu.state["PC"].value & 0xffffff < 0x1940 then return end
    local k = cpu.state["D1"].value & 0xffffffff
    cur.snd[k] = (cur.snd[k] or 0) + 1
end)
if os.getenv("CENSUS_NO_ROM") ~= "1" then
    census_pr = prog:install_read_tap(0, 0x1fffff, "census_pr", function(o) cur.pr[o & 0x1ffffe] = true end)
    census_op = ops:install_read_tap(0, 0x1fffff, "census_op", function(o) cur.op[o & 0x1ffffe] = true end)
end
local function dump()
    local h = assert(io.open(os.getenv("CENSUS_RAW"), "w"))
    h:write(string.format("frames %d%s", frame, NL))
    for _, k in ipairs(order) do
        local s = sets[k]
        h:write(string.format("K %s first %d last %d irq %d maxobj %d%s", k, s.first, s.last, s.irq, s.maxobj, NL))
        for i = 1, 4 do for t in pairs(s.t[i]) do h:write(string.format("T %d %x%s", i - 1, t, NL)) end end
        for v, n in pairs(s.snd) do h:write(string.format("S %08x %d%s", v, n, NL)) end
        for a in pairs(s.pr) do h:write(string.format("P %x%s", a, NL)) end
        for a in pairs(s.op) do h:write(string.format("O %x%s", a, NL)) end
    end
    h:close()
end
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local F = {in2["Coin 1"], in2["1 Player Start"], in0["P1 Left"], in0["P1 Right"], in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"], in0["P1 Up"], in0["P1 Down"]}
for _, n in ipairs{{2, "Coin 2"}, {2, "2 Players Start"}, {0, "P2 Left"}, {0, "P2 Right"}, {0, "P2 Button 1"}, {0, "P2 Button 2"}, {0, "P2 Button 3"}, {0, "P2 Up"}, {0, "P2 Down"}} do F[#F + 1] = (n[1] == 2 and in2 or in0)[n[2]] end   -- route word bits 9 to 17
local steps, last = {}, nil
for l in io.lines(os.getenv("AVSP_ROUTE")) do
    local a, b = l:match("^(%d+) (%d+)")
    if a then steps[tonumber(a)] = tonumber(b) else last = tonumber(l:match("^last (%d+)")) end
end
local prevk
census_f = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local w = steps[frame]
    if w then for i, f in ipairs(F) do if w & (1 << (i - 1)) ~= 0 then f:set_value(1) else f:clear_value() end end end
    local k = string.format("%04x/%02x", rd(0xff81e8), prog:read_u8(0xffd182))
    if k ~= prevk then
        cur = key_set(k); prevk = k
        if cur.first == 0 then cur.first = frame end
        snap_at = frame + 150
    end
    cur.last = frame
    if frame == snap_at then machine.video:snapshot() end
    if frame == last then dump(); machine:exit() end
end)
