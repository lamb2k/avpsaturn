-- Tile keys of the screens every stage can reach after a KO with no lives left: the continue screen through its whole countdown,
-- GAME OVER, and the select screen a continue opens (cursor over all four characters). Census routes continue at once, so they never
-- see the low countdown digits, and a stage whose census had no game over never sees the screen at all.
-- env AVSP_ROUTE (saved route to the first such KO), SCREEN_MODE (wait | select), SCREEN_OUT (keys file, "section hexkey" lines as tools/satint_census.lua), SCREEN_SNAP (frames apart, 0 none)
local route, mode, outp = os.getenv("AVSP_ROUTE"), os.getenv("SCREEN_MODE") or "wait", os.getenv("SCREEN_OUT")
local snap = tonumber(os.getenv("SCREEN_SNAP") or "0")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local in0 = manager.machine.ioport.ports[":IN0"].fields
local in2 = manager.machine.ioport.ports[":IN2"].fields
local F = {in2["Coin 1"], in2["1 Player Start"], in0["P1 Left"], in0["P1 Right"], in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"], in0["P1 Up"], in0["P1 Down"]}
local steps = {}
for l in io.lines(route) do
    local a, b = l:match("^(%d+) (%d+)")
    if a then steps[tonumber(a)] = tonumber(b) end
end
local function set(w) for i, f in ipairs(F) do if w & (1 << (i - 1)) ~= 0 then f:set_value(1) else f:clear_value() end end end
local keys, frame, since, prev = {{}, {}, {}, {}}, 0, nil, 0
local rd = function(a) return mem:read_u16(a) end
-- Every key saturn/gfx looks up: sprite tiles with flips, and the visible window of the three layers (same reads as tools/satint_census.lua).
local function grab()
    for i = 0, 0x3ff do
        local a = 0x708000 + i * 8
        local y, c, at = rd(a + 2), rd(a + 4), rd(a + 6)
        if y >= 0x8000 or at >= 0xff00 then break end
        local code = c + ((y & 0x6000) << 3)
        local nx, ny = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1
        local fx, fy = at & 0x20 ~= 0, at & 0x40 ~= 0
        for ty = 0, ny - 1 do for tx = 0, nx - 1 do
            if fx or fy then
                keys[1][code + (fx and nx - 1 - tx or tx) + 0x10 * (fy and ny - 1 - ty or ty)] = true
            else
                keys[1][(code & ~0xf) + ((code + tx) & 0xf) + 0x10 * ty] = true
            end
        end end
    end
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
end
screen_n = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local lives = mem:read_u8(0xff8471)
    if not since then
        if steps[frame] then set(steps[frame]) end
        if lives == 0xff and prev ~= 0xff then since = frame; set(0) end
        prev = lives
        return
    end
    local t = frame - since
    if mode == "select" then
        -- coin and start at +60, then the cursor right every 30 frames, no choice made
        local w = 0
        if t >= 60 and t < 64 then w = 1 elseif t >= 70 and t < 74 then w = 2 elseif t >= 100 and t % 30 < 4 then w = 8 end
        set(w)
    end
    grab()
    if snap > 0 and t % snap == 0 then manager.machine.video:snapshot() end
    if (mode == "select" and t >= 400) or (mode == "wait" and t >= 2650) then
        local o = io.open(outp, "w")
        for sec = 1, 4 do
            local list = {}
            for k in pairs(keys[sec]) do list[#list + 1] = k end
            table.sort(list)
            for _, k in ipairs(list) do o:write(string.format("%d %x\n", sec - 1, k)) end
        end
        o:close()
        manager.machine:exit()
    end
end)
