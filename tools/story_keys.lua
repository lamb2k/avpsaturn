-- Tile keys of the story pages and cut-ins a stage plays (lane coverage 2026-11-13). The route censuses warp to a stage and press Attack, which skips the stage's intro story
-- pages (round 3: "These aliens all come from one hive" ... "We'll use the APC!") and the stage-clear story, so the stage's round file lacked their pictures' sprite tiles
-- (the story drew with holes under the stage's own file: the Boss Rush / stage select start of stage 0a). This script warps to a stage, presses NOTHING, holds the player's
-- health and, with S_CLEAR_AT, sets the boss-down flags (ff822a, ff81f3) at that many frames of play so the clear sequence and the next stage's start run too.
-- Output keys.txt, one line per key first seen: STAGEWORD(hex) SECTION(0 sprite, 1..3 scroll 1..3) KEY(hex) FRAMES_SINCE_WARP; the stage word is the one the game holds when the key is seen.
-- env: S_OUT (dir), S_STAGE (hex), S_SPAN (frames after the warp to run), S_FRAMES (hard stop), S_CLEAR_AT (play frames, -1 none).  Pinned MAME 0.289, avspu, nvram baseline; coin/start taken from the same routine as tools/screen_keys.lua.
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local out = assert(os.getenv("S_OUT"))
local stage = tonumber(os.getenv("S_STAGE") or "4", 16)
local maxf = tonumber(os.getenv("S_FRAMES") or "9000")   -- hard stop (absolute frame)
local span = tonumber(os.getenv("S_SPAN") or "2000")      -- frames after the warp
local clear_at = tonumber(os.getenv("S_CLEAR_AT") or "-1")
local rd = function(a) return mem:read_u16(a) end
local rb = function(a) return mem:read_u8(a) end
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local frame, warped, warpf, play0 = 0, false, nil, nil
local keys = {{}, {}, {}, {}}
local seen = {}
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

story_am_f = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    if frame < 1500 then
        if frame > 300 and frame % 180 < 3 then coin:set_value(1) else coin:clear_value() end
        if frame > 330 and frame % 180 >= 30 and frame % 180 < 33 then start:set_value(1) else start:clear_value() end
    else coin:clear_value(); start:clear_value() end
    if not warped and rb(0xff8001) == 2 and rd(0xff81e8) == 2 and rb(0xff81b0) == 0 then
        mem:write_u16(0xff81e8, stage); warped = true; warpf = frame
    end
    if warped then
        mem:write_u16(0xff83c0, 0x6500)
        if not play0 and rb(0xff8380) ~= 0 and rd(0xff81e8) == stage then play0 = frame end
        if play0 and frame - play0 == clear_at then mem:write_u8(0xff822a, 1); mem:write_u8(0xff81f3, 1) end
        keys = {{}, {}, {}, {}}
        grab()
        local w = rd(0xff81e8)
        for s = 1, 4 do for k in pairs(keys[s]) do
            local id = string.format("%02x %d %x", w, s - 1, k)
            if not seen[id] then seen[id] = frame - warpf end
        end end
    end
    if frame >= maxf or (warpf and frame - warpf >= span) then
        local kf = assert(io.open(out .. "/keys.txt", "w"))
        for id, f in pairs(seen) do kf:write(id .. " " .. f .. "\n") end
        kf:close()
        manager.machine:exit()
    end
end)
