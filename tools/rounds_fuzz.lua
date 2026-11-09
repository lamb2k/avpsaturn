-- Lane avp-vanish: rounds_walk.lua with a button-fuzz input policy (jumps, jump attacks, attack bursts, gun, every direction) and the sprite keys kept per
-- palette (fuzz_pal.txt: "pal key"), so the tiles of the player characters' poses that the walk never reached can be told from enemy tiles.
-- Lane rounds: walk the whole game under MAME with health held full, and record per stage word (ff81e8) the tile keys the graphics library looks up,
-- the data ROM words read, the opcode words read and the sound commands. A census aid, not a proof: health is written. Output is ROM-derived: E:/AvP/learning only.
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"]
local root = assert(os.getenv("ROUNDS_OUT"))
local maxf = tonumber(os.getenv("ROUNDS_MAXF") or "400000")
local screen = machine.screens[":screen"]
local nocheat = os.getenv("ROUNDS_NOCHEAT") ~= nil
local rd = function(a) return prog:read_u16(a) end
local rb = function(a) return prog:read_u8(a) end
local R = {}
local cur = 0
local once = os.getenv("ROUNDS_ONCE") ~= nil   -- one character's game only: stops when the stage word leaves the ending, before attract and a new default game
local seen26, stage_at = false, nil
local function bucket(s)
    local b = R[s]
    if not b then b = {keys = {{}, {}, {}, {}}, reads = {}, oreads = {}, snd = {}, frames = 0}; R[s] = b end
    return b
end
local B = bucket(0)
local PK = {}
math.randomseed(tonumber(os.getenv("ROUNDS_SEED") or "1"))
local irq = 0
local function dump()
    do local h = assert(io.open(root .. "/fuzz_pal.txt", "w")); for p, set_ in pairs(PK) do for k in pairs(set_) do h:write(string.format("%d %x\n", p, k)) end end; h:close() end
    for s, b in pairs(R) do
        local h = assert(io.open(string.format(s >= 0x100 and "%s/k%02x.txt" or "%s/s%02x.txt", root, s & 0xff), "w"))
        h:write("frames " .. b.frames .. "\n")
        for i = 1, 4 do for k in pairs(b.keys[i]) do h:write(string.format("%d %x\n", i - 1, k)) end end
        for a in pairs(b.reads) do h:write(string.format("r %x\n", a)) end
        for a in pairs(b.oreads) do h:write(string.format("o %x\n", a)) end
        for a in pairs(b.snd) do h:write(string.format("m %x\n", a)) end
        h:close()
    end
end
rw_rd = prog:install_read_tap(0, 0x1fffff, "rw_rd", function(o) B.reads[o & 0x1ffffe] = true end)
rw_od = ops:install_read_tap(0, 0x10ffff, "rw_od", function(o) B.oreads[o & 0x10fffe] = true end)
-- the game's sender, mailbox at 0x618000 and 0x618002
local mb = {}
rw_wr = prog:install_write_tap(0x618000, 0x619fff, "rw_wr", function(o, d, m)
    if o == 0x618000 then mb[1] = d & 0xff elseif o == 0x618002 then B.snd[((mb[1] or 0) << 8) | (d & 0xff)] = true end
end)
rw_irq = ops:install_read_tap(0xe0e, 0xe0f, "rw_irq", function()
    if cpu.state["PC"].value ~= 0x68 then return end
    local kk = B.keys[1]
    local n = 0
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
            local pk = PK[aw & 31]; if not pk then pk = {}; PK[aw & 31] = pk end; pk[t] = true
        end end
        n = n + 1
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
            B.keys[2][(rd(m + i * 4) << 1) | ((i >> 5) & 1)] = true
        end end
    end
    if layers & 4 ~= 0 then
        local m = base(0x26)
        local y0 = s2y + 16
        for row = 0, 14 do for c = 0, 63 do
            local r = ((y0 >> 4) + row) & 63
            local i = (r & 0xf) + (c << 4) + ((r & 0x30) << 6)
            B.keys[3][rd(m + i * 4)] = true
        end end
    end
    if layers & 8 ~= 0 then
        local m = base(0x28)
        local x0, y0 = s3x + 80, s3y + 16
        for row = 0, 7 do for col = 0, 11 do
            local c, r = ((x0 >> 5) + col) & 63, ((y0 >> 5) + row) & 63
            local i = (r & 7) + (c << 3) + ((r & 0x38) << 6)
            B.keys[4][rd(m + i * 4) & 0x3fff] = true
        end end
    end
    irq = irq + 1
    B.frames = B.frames + 1
end)
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local F = {coin = in2["Coin 1"], start = in2["1 Player Start"], left = in0["P1 Left"], right = in0["P1 Right"], up = in0["P1 Up"], down = in0["P1 Down"],
           gun = in0["P1 Button 1"], atk = in0["P1 Button 2"], jump = in0["P1 Button 3"]}
local function set(k, on) if on then F[k]:set_value(1) else F[k]:clear_value() end end
local log = assert(io.open(root .. "/walk.tsv", "w"))
local fuzz_until, fz = 0, {left = false, right = true, up = false, down = false, gun = false, atk = false, jump = false}
local frame, lastx, stuck, dir, last = 0, 0, 0, 0, ""
local shotn = tonumber(os.getenv("ROUNDS_SHOT") or "1800")
local nocoin = os.getenv("ROUNDS_NOCOIN") ~= nil
local want, picked, story = tonumber(os.getenv("ROUNDS_CHAR") or "0"), nil, false
rw_f = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local stage, sec, att, cred, top, p0 = rd(0xff81e8), rb(0xffd182), rb(0xff81b0), rb(0xff818c), rb(0xff8384), rb(0xff8380)
    local x = rd(0xff8390)
    local b = (att ~= 0 or rb(0xff8001) ~= 2) and 0 or stage   -- as the Saturn loader picks its file
    if nocheat and b ~= 0 and (top == 4 or p0 ~= 1) then b = 0x100 end   -- KO, continue and game over: can happen in any stage, so kept in all
    if b ~= cur then
        cur = b; B = bucket(b)
        log:write(string.format("STAGE %x frame %d sec %d\n", b, frame, sec))
        dump()
        if once then
            stage_at = frame + 400
            if b == 0x26 then seen26 = true end
            if seen26 and b == 0 then machine:exit(); return end
        end
    end
    local st = string.format("st %x sec %d cr %d att %d mode %d g09 %d p0 %d", stage, sec, cred, att, rb(0xff8001), rb(0xff8009), p0)
    if st ~= last or frame % 600 == 0 then
        last = st
        log:write(string.format("%d\t%s\tx %d cam %d hp %d f3 %d\n", frame, st, x, rd(0xffee1a), rd(0xff83c0), rb(0xff81f3))); log:flush()
    end
    if stage_at == frame then screen:snapshot(string.format("stage%02x_%06d.png", cur & 0xff, frame)) end
    if frame % shotn == 0 then screen:snapshot(string.format("w%06d.png", frame)) end
    if frame % 3000 == 0 then dump() end
    if frame >= maxf then dump(); machine:exit(); return end
    if not nocheat then prog:write_u16(0xff83c0, 0x65) end
    local playing = att == 0 and p0 ~= 0 and top ~= 4
    local t = frame % 120
    set("coin", not nocoin and not playing and cred == 0 and t < 4)
    local pressing = not playing and cred ~= 0 and t >= 60 and t < 64
    set("start", pressing)
    if not playing then
        for _, k in ipairs{"left", "up", "jump"} do set(k, false) end
        -- the select screen: stage 0, g09 2 after the story's g09 16. Grid: 0 warrior (default), 1 right, 2 down, 3 right then down.
        local g = rb(0xff8009)
        if g == 16 then story = true end
        local sel = stage == 0 and att == 0 and story and g == 2
        if sel and not picked then picked = frame end
        local since = picked and frame - picked or 0
        local pick = sel and since < 260
        set("right", pick and since >= 190 and since < 194 and want & 1 ~= 0)
        set("down", pick and since >= 225 and since < 229 and want & 2 ~= 0)
        local mash = not pick and frame % 40 < 4
        set("gun", mash); set("atk", mash)
        return
    end
    if x == lastx then stuck = stuck + 1 else stuck = 0; lastx = x end
    if stuck > 240 then dir = (dir + 1) % 4; stuck = 0 end
    -- fuzz: a new action every 6 to 18 frames, so jumps last, jump attacks and attack bursts happen, and direction changes in the air
    if frame % 6 == 0 and frame >= fuzz_until then
        fuzz_until = frame + 6 * math.random(1, 3)
        local r = math.random(100)
        fz = {left = false, right = false, up = false, down = false, gun = false, atk = false, jump = false}
        local d = math.random(10)
        if d <= 5 then fz.right = true elseif d <= 7 then fz.left = true end
        if math.random(4) == 1 then fz.up = true elseif math.random(4) == 1 then fz.down = true end
        if r <= 22 then fz.jump = true
        elseif r <= 40 then fz.jump = true; fz.atk = true
        elseif r <= 48 then fz.jump = true; fz.gun = true
        elseif r <= 70 then fz.atk = true
        elseif r <= 80 then fz.gun = true
        elseif r <= 88 then fz.atk = true; fz.gun = true end
    end
    -- buttons are pressed in short pulses so the game sees presses, not a held key
    local pulse = frame % 6 < 3
    for k, v in pairs(fz) do
        if k == "atk" or k == "gun" then set(k, v and pulse) elseif k == "jump" then set(k, v and frame % 12 < 3) else set(k, v) end
    end
end)
