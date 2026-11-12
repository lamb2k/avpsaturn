-- lane perf, 2026-11-12: arcade game-speed measurement under MAME 0.289 (avspu). Same walking bot as lane alien-measure (health held at 0xff83c0), plus per-frame counters of the
-- game's own clock: ff8018 (IRQ count), ff8019 (gameplay tick), fetches of 0x808a (tick starts), 0xd86 (dispatcher walk starts), 0x11ec (walks completed: the idle call),
-- 0xdb8 (task runs), 0x8156 (a vblank hit during the tick: catch-up), 0x814a (the tick sleeps a vblank). Tick duration from the emulated clock (0x808a to 0x8144).
-- env: GS_OUT (dir), GS_MAXF
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"]
local root = assert(os.getenv("GS_OUT"))
local maxf = tonumber(os.getenv("GS_MAXF") or "40000")
local rd = function(a) return prog:read_u16(a) end
local rb = function(a) return prog:read_u8(a) end
local A6 = cpu.state["A6"]
local function now() return machine.time:as_double() end
local C = {t808a = 0, d86 = 0, i11ec = 0, db8 = 0, o8156 = 0, s814a = 0, s8162 = 0}
local tstart, busy, tmax, ndur = nil, 0, 0, 0
local function tap(addr, key, fn)
    return ops:install_read_tap(addr, addr + 1, "gs_" .. key, function(o)
        if (o & 0xffffe) ~= addr then return end
        C[key] = C[key] + 1
        if fn then fn() end
    end)
end
gs_t1 = tap(0x808a, "t808a", function() tstart = now() end)
gs_t2 = ops:install_read_tap(0x8144, 0x8145, "gs_end", function(o)
    if (o & 0xffffe) ~= 0x8144 or not tstart then return end
    local d = now() - tstart; tstart = nil
    busy = busy + d; ndur = ndur + 1; if d > tmax then tmax = d end
end)
gs_t3 = tap(0xd86, "d86"); gs_t4 = tap(0x11ec, "i11ec"); gs_t5 = tap(0xdb8, "db8")
gs_t6 = tap(0x8156, "o8156"); gs_t7 = tap(0x814a, "s814a"); gs_t8 = tap(0x8162, "s8162")
local owner = {}
am_wr = prog:install_write_tap(0x708000, 0x70bfff, "gs_wr", function(o, d, m)
    if (o & 7) == 4 then owner[(o & 0x1fff) >> 3] = A6.value & 0xffffff end
end)
local function scan()
    local n, enemies, set = 0, 0, {}
    while n < 0x400 do
        local o = 0x708000 + n * 8
        local yw, aw = rd(o + 2), rd(o + 6)
        if yw >= 0x8000 or aw >= 0xff00 then break end
        local a = owner[n]
        if a and a >= 0xff0000 and not set[a] then set[a] = true; if rb(a + 8) == 0x0c then enemies = enemies + 1 end end
        n = n + 1
    end
    return n, enemies
end

local wpc = {}
local function wtap(lo, hi, nm)
    return prog:install_write_tap(lo, hi, "gs_w" .. nm, function(o, d, m)
        local k = string.format("%s pc=%06x", nm, cpu.state["PC"].value & 0xffffff)
        wpc[k] = (wpc[k] or 0) + 1
    end)
end
gs_w1 = wtap(0xff8018, 0xff8019, "ff8018_19"); gs_w3 = wtap(0xff0266, 0xff0267, "ff0266")
local function dumpw()
    local h = assert(io.open(root .. "/writers.txt", "w"))
    for k, v in pairs(wpc) do h:write(k, " ", v, "\n") end
    h:close()
end
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local F = {coin = in2["Coin 1"], start = in2["1 Player Start"], left = in0["P1 Left"], right = in0["P1 Right"], up = in0["P1 Up"], down = in0["P1 Down"],
           gun = in0["P1 Button 1"], atk = in0["P1 Button 2"], jump = in0["P1 Button 3"]}
local function set(k, on) if on then F[k]:set_value(1) else F[k]:clear_value() end end
local log = assert(io.open(root .. "/frames.tsv", "w"))
log:write("frame\tstage\tvb\ttk\tt808a\td86\ti11ec\tdb8\tovr\tsleep\tforced\tff81b9\tsprites\tenemies\tbusy_ms\tmax_ms\tndur\n")
local frame, lastx, stuck, dir = 0, 0, 0, 0
local want, picked, story = 0, nil, false
am_f = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local stage, att, cred, top, p0 = rd(0xff81e8), rb(0xff81b0), rb(0xff818c), rb(0xff8384), rb(0xff8380)
    local x = rd(0xff8390)
    local cur = (att ~= 0 or rb(0xff8001) ~= 2) and 0 or stage
    local sp, en = scan()
    log:write(string.format("%d\t%x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%.3f\t%.3f\t%d\n", frame, cur, rb(0xff8018), rb(0xff8019), C.t808a, C.d86, C.i11ec, C.db8, C.o8156, C.s814a,
        C.o8156 - C.s8162, rb(0xff81b9), sp, en, busy * 1000, tmax * 1000, ndur))
    if frame == tonumber(os.getenv("GS_DUMP") or "-1") then
        local h = assert(io.open(root .. "/pooldump.txt", "w"))
        for a = 0xff9380, 0xffa980, 0x100 do
            local t = {}
            for i = 0, 0x1f do t[#t+1] = string.format("%02x", rb(a + i)) end
            h:write(string.format("%06x: %s | en %d\n", a, table.concat(t, " "), en))
        end
        h:close()
    end
    for k in pairs(C) do C[k] = 0 end
    busy, tmax, ndur = 0, 0, 0
    if frame % 600 == 0 then log:flush() end
    if frame >= maxf then dumpw(); log:flush(); machine:exit(); return end
    prog:write_u16(0xff83c0, 0x65)
    local playing = att == 0 and p0 ~= 0 and top ~= 4
    local t = frame % 120
    set("coin", not playing and cred == 0 and t < 4)
    set("start", not playing and cred ~= 0 and t >= 60 and t < 64)
    if not playing then
        for _, k in ipairs{"left", "up", "jump"} do set(k, false) end
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
    local w = frame % 900
    set("right", dir ~= 2)
    set("left", dir == 2)
    set("up", dir == 1 or (w > 300 and w < 340))
    set("down", dir == 3 or (w > 700 and w < 740))
    set("gun", frame % 16 < 6)
    set("atk", frame % 24 < 5)
    set("jump", frame % 700 < 5)
end)
