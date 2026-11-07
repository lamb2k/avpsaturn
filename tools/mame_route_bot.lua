-- Closed-loop route bot: real ports only, no RAM writes. Replays a prefix route, then chooses the pad word each frame from work RAM
-- and writes the whole route, which tools/mame_golden_run.py replays. Word bits as tools/make_route.py.
-- Env: BOT_PREFIX route file, BOT_OUT route out, BOT_LOG log, BOT_MAX frames, BOT_STOP_ATTRACT frames after attract returns.
-- BOT_CHAR: select grid position (0 warrior, 1 right, 2 down, 3 right then down), as tools/rounds_walk.lua.
local cpu = manager.machine.devices[":maincpu"]
local p = cpu.spaces["program"]
local in0 = manager.machine.ioport.ports[":IN0"].fields
local in2 = manager.machine.ioport.ports[":IN2"].fields
local F = {in2["Coin 1"], in2["1 Player Start"], in0["P1 Left"], in0["P1 Right"], in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"], in0["P1 Up"], in0["P1 Down"]}
for _, n in ipairs{{2, "Coin 2"}, {2, "2 Players Start"}, {0, "P2 Left"}, {0, "P2 Right"}, {0, "P2 Button 1"}, {0, "P2 Button 2"}, {0, "P2 Button 3"}, {0, "P2 Up"}, {0, "P2 Down"}} do F[#F + 1] = (n[1] == 2 and in2 or in0)[n[2]] end   -- route word bits 9 to 17
local steps, plast = {}, 0
for l in io.lines(os.getenv("BOT_PREFIX")) do
    local a, b = l:match("^(%d+) (%d+)")
    if a then steps[tonumber(a)] = tonumber(b) else plast = tonumber(l:match("^last (%d+)")) end
end
local maxf = tonumber(os.getenv("BOT_MAX") or "300000")
local log = assert(io.open(os.getenv("BOT_LOG"), "w"))
local route = {}
local frame, prevw, prevm, kos, presses, lastprog, lastsave = 0, nil, nil, 0, 0, 0, 0
local late, endf = false, nil
local inko = false
local wander_until, wander_word, stall_x, stall_y, stall_f = 0, 0, 0, 0, 0
local rnd = 12345
local function r8(a) return p:read_u8(a) end
local function r16(a) return p:read_u16(a) end
local function s16(a) local v = p:read_u16(a); if v >= 0x8000 then v = v - 0x10000 end; return v end
local POOLS = {{0xff8680, 24, 0x80}, {0xff9280, 4, 0xc0}, {0xff9580, 20, 0xc0}}
local ALLP = {{0xff8680, 24, 0x80}, {0xff9280, 4, 0xc0}, {0xff9580, 20, 0xc0}, {0xffa480, 20, 0x80}, {0xffae80, 16, 0x80}, {0xffc680, 16, 0x80}}
local function finish(why)
    log:write(string.format("END %s frame %d kos %d presses %d\n", why, frame, kos, presses)); log:close()
    local o = assert(io.open(os.getenv("BOT_OUT"), "w"))
    o:write(string.format("last %d\n", frame))
    for _, e in ipairs(route) do o:write(e[1], " ", e[2], "\n") end
    o:close(); manager.machine:exit()
end
local snapev, snapfrom = tonumber(os.getenv("BOT_SNAPEV") or "1000000"), tonumber(os.getenv("BOT_SNAPFROM") or "0")
local want = tonumber(os.getenv("BOT_CHAR") or "0")
local story, picked, lastg = false, nil, nil
local function pick()
    local g = r8(0xff8009)
    if g ~= lastg and frame < 6000 then log:write(string.format("g09 %d f%d att %d stage %x mode %d cr %d", g, frame, r8(0xff81b0), r16(0xff81e8), r8(0xff8001), r8(0xff818c)), string.char(10)); lastg = g end
    if g == 16 then story = true end
    if not (want ~= 0 and story and r16(0xff81e8) == 0 and r8(0xff81b0) == 0 and g == 2) then return nil end
    if not picked then picked = frame; log:write("SELECT f", frame, string.char(10)) end
    local since = frame - picked
    if since >= 260 then return nil end
    local w = 0
    if since >= 190 and since < 194 and want & 1 ~= 0 then w = w | 8 end
    if since >= 225 and since < 229 and want & 2 ~= 0 then w = w | 256 end
    return w
end
local function save_route()
    local o = assert(io.open(os.getenv("BOT_OUT"), "w"))
    o:write(string.format("last %d", frame), string.char(10))
    for _, e in ipairs(route) do o:write(e[1], " ", e[2], string.char(10)) end
    o:close()
end
-- BOT_P2=1: a second player on the second set of ports; the result is ORed in at bit 9.
local p2 = os.getenv("BOT_P2") == "1"
local function bot2()
    local B = 0xff8480
    local pz, top, cred, ph = r8(B), r8(B + 4), r8(0xff818c), frame % 40
    if r8(0xff81b0) ~= 0 then return 0 end
    if r8(0xff8001) ~= 2 or pz == 0 or top == 4 then
        if cred == 0 then if ph >= 8 and ph < 11 then return 1 end return 0 end
        if ph >= 12 and ph < 15 then return 2 end
        if ph >= 30 and ph < 33 then return 16 end
        return 0
    end
    local px, py, cam = r16(B + 0x10), r16(B + 0x14), r16(0xff8278)
    local best, bd, bx, by = nil, 1 << 30, 0, 0
    for _, q in ipairs(POOLS) do for i = 0, q[2] - 1 do
        local a = q[1] + i * q[3]
        if r8(a) ~= 0 and s16(a + 0x40) >= 0 then
            local x, y = r16(a + 0x10), r16(a + 0x14)
            if x > cam - 32 and x < cam + 416 then
                local d = math.abs(x - px) + 2 * math.abs(y - py)
                if d < bd then best, bd, bx, by = a, d, x, y end
            end
        end
    end end
    local w = ((frame + 5) % 16 < 3) and 16 or 0
    if (frame + 90) % 180 < 8 then w = w | 32 end
    if not best then return w | 8 end
    local dx, dy = bx - px, by - py
    if dy < -6 then w = w | 128 elseif dy > 6 then w = w | 256 end
    if dx > 48 then w = w | 8 elseif dx < -48 then w = w | 4
    elseif dx >= 0 then if frame % 32 < 2 then w = w | 8 end
    else if frame % 32 < 2 then w = w | 4 end end
    return w
end
local function bot()
    local pw = pick()
    if pw then return pw end
    if r16(0xff81e8) >= 0x10 then late = true end
    if late and r8(0xff81b0) ~= 0 then
        if not endf then endf = frame; log:write("ATTRACT RETURNED f", frame, string.char(10)) end
        if frame > endf + 600 then finish("attract") end
        return 0
    end
    local h, mode, cred, top, pz = r8(0xff81b0), r8(0xff8001), r8(0xff818c), r8(0xff8384), r8(0xff8380)
    local w = 0
    if h ~= 0 or mode == 4 or mode == 0 or pz == 0 or top == 4 then
        local ph = frame % 40
        if cred == 0 then if ph < 3 then w = 1 end
        elseif ph < 3 then w = 2
        elseif ph >= 20 and ph < 23 then w = 16 end
        return w
    end
    local px, py, cam = r16(0xff8390), r16(0xff8394), r16(0xff8278)
    if frame < wander_until then
        return wander_word | ((frame % 16 < 3) and 16 or 0)
    end
    if px ~= stall_x or py ~= stall_y then stall_x, stall_y, stall_f = px, py, frame end
    if frame - stall_f > 200 then
        rnd = (rnd * 1103515245 + 12345) & 0x7fffffff
        local d = {8, 4, 128, 256, 136, 264, 132, 260, 8 | 64}
        wander_word = d[((rnd >> 16) % #d) + 1]
        wander_until = frame + 40 + ((rnd >> 8) % 80)
        stall_f = frame
        return wander_word
    end
    local best, bd, bx, by = nil, 1 << 30, 0, 0
    for _, q in ipairs(POOLS) do for i = 0, q[2] - 1 do
        local a = q[1] + i * q[3]
        if r8(a) ~= 0 and s16(a + 0x40) >= 0 then
            local x, y = r16(a + 0x10), r16(a + 0x14)
            if x > cam - 32 and x < cam + 416 then
                local d = math.abs(x - px) + 2 * math.abs(y - py)
                if d < bd then best, bd, bx, by = a, d, x, y end
            end
        end
    end end
    local fire = (frame % 16 < 3) and 16 or 0
    local melee = (frame % 180 < 8) and 32 or 0
    local jump = (frame % 240 < 8) and 64 or 0
    if not best then return 8 | fire | melee | jump end
    local dx, dy = bx - px, by - py
    w = fire | melee
    if dy < -6 then w = w | 128 elseif dy > 6 then w = w | 256 end
    if dx > 48 then w = w | 8 elseif dx < -48 then w = w | 4
    elseif dx >= 0 then if frame % 32 < 2 then w = w | 8 end
    else if frame % 32 < 2 then w = w | 4 end end
    return w
end
learn_bot = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local w
    if frame <= plast then w = steps[frame] else w = bot(); if p2 then w = w | (bot2() << 9) end end
    if w and w ~= prevw then
        route[#route + 1] = {frame, w}; prevw = w
        for i, f in ipairs(F) do
            if w & (1 << (i - 1)) ~= 0 then f:set_value(1) else f:clear_value() end
        end
    end
    local st, sec, att, top = r16(0xff81e8), r8(0xffd182), r8(0xff81b0), r8(0xff8384)
    local m = string.format("stage %x sec %x att %x mode %x", st, sec, att, r8(0xff8001))
    if m ~= prevm then log:write(string.format("f%d %s ko %d\n", frame, m, kos)); log:flush(); prevm = m; lastprog = frame end
    if top == 4 and not inko then kos = kos + 1 end
    inko = (top == 4)
    if frame % 3000 == 0 then
        log:write(string.format("f%d %s hp %d x %x cred %d ko %d\n", frame, m, r16(0xff83c0), r16(0xff8390), r8(0xff818c), kos)); log:flush()
    end
    if frame % snapev == 0 and frame >= snapfrom then
        local t = {string.format("SNAP f%d x %x y %x hp %d camx %x p0 %x top %x", frame, r16(0xff8390), r16(0xff8394), r16(0xff83c0), r16(0xff80b0), r8(0xff8380), r8(0xff8384))}
        t[1] = t[1] .. string.format(" cam %x sp %x", r16(0xff8278), r16(0xff8218))
        for _, q in ipairs(ALLP) do for i = 0, q[2] - 1 do local a = q[1] + i * q[3]
            if r8(a) ~= 0 then t[#t + 1] = string.format("%x:%02x,%02x,%02x,%02x x%x y%x h%d", a, r8(a), r8(a+1), r8(a+2), r8(a+4), r16(a+0x10), r16(a+0x14), s16(a+0x40)) end
        end end
        log:write(table.concat(t, " | "), string.char(10)); log:flush()
        if os.getenv("BOT_SHOT") then manager.machine.video:snapshot() end
    end
    if frame % 30000 == 0 then save_route() end
    if frame % 30000 == 0 then save_route() end
    if frame >= maxf then finish("max") end
end)
