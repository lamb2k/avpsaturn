-- Lane satint: every tile key the Saturn graphics library looks up, over the retained Round 1 route, plus each CPS input read per IRQ
-- at the coin and start edges. Same IRQ point as satgfx_scene_probe.lua. Output is ROM-derived: stays under E:\AvP\learning\lane-satint.
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"]
local root = assert(os.getenv("SATINT_CENSUS_OUT"))
local keys = {{}, {}, {}, {}}
local peak = {0, 0, 0, 0}
local irq = 0
local function dump()
    local h = assert(io.open(root .. "/keys.txt", "w"))
    h:write("irq " .. irq .. "\n")
    for s = 1, 4 do for k in pairs(keys[s]) do h:write(string.format("%d %x\n", s - 1, k)) end end
    h:close()
end
local rd = function(a) return prog:read_u16(a) end
local stop_at = tonumber(os.getenv("SATINT_STOP_IRQ") or "") or 99999999
local snaps = {}
for s in string.gmatch(os.getenv("SATINT_SNAPS") or "", "%d+") do snaps[tonumber(s)] = true end
local screen = machine.screens[":screen"]
local seen_hist = assert(io.open(root .. "/growth.tsv", "w"))
satint_tap = ops:install_read_tap(0xe0e, 0xe0f, "satint", function()
    if cpu.state["PC"].value ~= 0x68 then return end
    if snaps[irq] then screen:snapshot(string.format("s%05d.png", irq)) end
    if irq > stop_at then return end
    -- sprites
    local n, fr = 0, {0, 0, 0, 0}
    local kk = keys[1]
    while n < 0x400 do
        local o = 0x708000 + n * 8
        local yw, aw = rd(o + 2), rd(o + 6)
        if yw >= 0x8000 or aw >= 0xff00 then break end
        local code = rd(o + 4) + ((yw & 0x6000) << 3)
        local nx, ny = ((aw >> 8) & 15) + 1, ((aw >> 12) & 15) + 1
        local fx, fy = aw & 0x20 ~= 0, aw & 0x40 ~= 0
        for ty = 0, ny - 1 do for tx = 0, nx - 1 do
            local t
            if fx or fy then
                t = code + (fx and nx - 1 - tx or tx) + 0x10 * (fy and ny - 1 - ty or ty)
            else
                t = (code & ~15) + ((code + tx) & 15) + 0x10 * ty
            end
            kk[t] = true
        end end
        n = n + 1
    end
    -- layers: the whole visible window as the library reads it, row scroll treated as a full row.
    local f = 0xff8000
    local layers = rd(f + 0x4a)
    local base = function(off) return (rd(f + off) & 0xffc0) * 0x100 end
    local s1x, s1y, s2y, s3x, s3y = rd(0xffee1a), rd(0xffee1c), rd(0xffee20), rd(0xffee22), rd(0xffee24)
    if layers & 2 ~= 0 then
        local m = base(0x24)
        local x0, y0 = s1x + 80, s1y + 16
        for row = 0, 28 do for col = 0, 44 do
            local c, r = ((x0 >> 3) + col) & 63, ((y0 >> 3) + row) & 63
            local i = (r & 0x1f) + (c << 5) + ((r & 0x20) << 6)
            keys[2][(rd(m + i * 4) << 1) | ((i >> 5) & 1)] = true
        end end
    end
    if layers & 4 ~= 0 then
        local m = base(0x26)
        local y0 = s2y + 16
        for row = 0, 14 do for c = 0, 63 do
            local r = ((y0 >> 4) + row) & 63
            local i = (r & 0xf) + (c << 4) + ((r & 0x30) << 6)
            keys[3][rd(m + i * 4)] = true
        end end
    end
    if layers & 8 ~= 0 then
        local m = base(0x28)
        local x0, y0 = s3x + 80, s3y + 16
        for row = 0, 7 do for col = 0, 11 do
            local c, r = ((x0 >> 5) + col) & 63, ((y0 >> 5) + row) & 63
            local i = (r & 7) + (c << 3) + ((r & 0x38) << 6)
            keys[4][rd(m + i * 4) & 0x3fff] = true
        end end
    end
    irq = irq + 1
    if irq % 300 == 0 then
        local cnt = {0, 0, 0, 0}
        for s = 1, 4 do for _ in pairs(keys[s]) do cnt[s] = cnt[s] + 1 end end
        seen_hist:write(string.format("%d\t%d\t%d\t%d\t%d\t%x\n", irq, cnt[1], cnt[2], cnt[3], cnt[4], rd(0xff8018)))
        seen_hist:flush()
        dump()
    end
end)
local route = os.getenv("AVSP_ROUTE")
if route then   -- a saved input file (tools/make_route.py), real ports only
    local in0 = machine.ioport.ports[":IN0"].fields
    local in2 = machine.ioport.ports[":IN2"].fields
    local F = {in2["Coin 1"], in2["1 Player Start"], in0["P1 Left"], in0["P1 Right"], in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"], in0["P1 Up"], in0["P1 Down"]}
    local steps, last = {}, nil
    for l in io.lines(route) do
        local a, b = l:match("^(%d+) (%d+)")
        if a then steps[tonumber(a)] = tonumber(b) else last = tonumber(l:match("^last (%d+)")) end
    end
    local frame = 0
    satint_route = emu.add_machine_frame_notifier(function()
        frame = frame + 1
        local w = steps[frame]
        if w then for i, f in ipairs(F) do if w & (1 << (i - 1)) ~= 0 then f:set_value(1) else f:clear_value() end end end
        if frame == last then dump(); machine:exit() end
    end)
else
    dofile("tools/mame_capture_oracle11_player_audio.lua")
end
