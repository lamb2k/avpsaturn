-- Lane alien-measure: walk the whole game under MAME 0.289 (avspu) with health held, as tools/rounds_walk.lua does, and attribute every
-- object-list entry to the actor that wrote it (a6 at the tile-code write). Per actor kind (tag byte +8, class byte +2) it records the
-- 16x16 tile keys (same expansion as rounds_walk / the packer), distinct poses (entry lists relative to the first entry), the state bytes
-- +4..+6 each pose was seen in, the palettes used and the stages. Sample poses keep their entries and palette colours for contact sheets.
-- A census aid, not a proof: health is written. Output is ROM-derived: E:/AvP/learning only.
-- env: AM_OUT (dir), AM_CHAR (0 warrior, 1 schaefer, 2 linn, 3 hunter; the walk's select grid), AM_MAXF, AM_SAMPLES (poses kept per kind)
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local root = assert(os.getenv("AM_OUT"))
local maxf = tonumber(os.getenv("AM_MAXF") or "450000")
local nsamp = tonumber(os.getenv("AM_SAMPLES") or "400")
local rd = function(a) return prog:read_u16(a) end
local rb = function(a) return prog:read_u8(a) end
local A6 = cpu.state["A6"]
local owner = {}
local K = {}   -- id -> {keys = set, poses = {sig -> n}, st = {state -> {sig -> true}}, pal = {}, stages = {}, samples = {}, nsamp, frames}
local cur = 0
local palobj = nil
pcall(function() palobj = machine.palettes[":palette"].palette end)
local function pen(i)
    if palobj then
        local ok, c = pcall(function() return palobj:entry_color(i) end)
        if ok and c then return c & 0xffffff end
    end
    return 0
end
local function kind(id)
    local k = K[id]
    if not k then k = {keys = {}, poses = {}, st = {}, pal = {}, stages = {}, samples = {}, ns = 0, frames = 0, a6 = {}}; K[id] = k end
    return k
end
am_wr = prog:install_write_tap(0x708000, 0x70bfff, "am_wr", function(o, d, m)
    if (o & 7) == 4 then owner[(o & 0x1fff) >> 3] = A6.value & 0xffffff end
end)
local function dump()
    local h = assert(io.open(root .. "/kinds.tsv", "w"))
    for id, k in pairs(K) do
        local nk, np, ns = 0, 0, 0
        for _ in pairs(k.keys) do nk = nk + 1 end
        for _ in pairs(k.poses) do np = np + 1 end
        h:write(string.format("KIND\t%s\tframes %d\tkeys %d\tposes %d\n", id, k.frames, nk, np))
        local s = {}
        for st in pairs(k.stages) do s[#s + 1] = string.format("%02x", st) end
        h:write("STAGES\t" .. id .. "\t" .. table.concat(s, " ") .. "\n")
        local a = {}
        for x in pairs(k.a6) do a[#a + 1] = string.format("%06x", x) end
        h:write("A6\t" .. id .. "\t" .. table.concat(a, " ") .. "\n")
        for p in pairs(k.pal) do h:write(string.format("PAL\t%s\t%d\n", id, p)) end
        for st, sg in pairs(k.st) do
            local n = 0
            for _ in pairs(sg) do n = n + 1 end
            h:write(string.format("STATE\t%s\t%s\t%d\n", id, st, n))
        end
        local ks = {}
        for t in pairs(k.keys) do ks[#ks + 1] = string.format("%x", t) end
        h:write("KEYS\t" .. id .. "\t" .. table.concat(ks, " ") .. "\n")
    end
    h:close()
    local g = assert(io.open(root .. "/samples.tsv", "w"))
    for id, k in pairs(K) do
        for _, s in ipairs(k.samples) do g:write("S\t" .. id .. "\t" .. s .. "\n") end
    end
    g:close()
end
am_irq = cpu.spaces["opcodes"]:install_read_tap(0xe0e, 0xe0f, "am_irq", function()
    if cpu.state["PC"].value ~= 0x68 then return end
    local per = {}
    local n = 0
    while n < 0x400 do
        local o = 0x708000 + n * 8
        local xw, yw, cw, aw = rd(o), rd(o + 2), rd(o + 4), rd(o + 6)
        if yw >= 0x8000 or aw >= 0xff00 then break end
        local a = owner[n]
        if a and a >= 0xff0000 then
            local id = string.format("%02x:%02x", rb(a + 8), rb(a + 2))
            if a >= 0xff8380 and a < 0xff8680 then id = string.format("P%d:%02x", (a - 0xff8380) >> 8, rb(a + 2))
            elseif rb(a + 8) == 0 then id = "sys" end
            local k = kind(id)
            local code = cw + ((yw & 0x6000) << 3)
            local nx, ny = ((aw >> 8) & 15) + 1, ((aw >> 12) & 15) + 1
            local fx, fy = aw & 0x20 ~= 0, aw & 0x40 ~= 0
            for ty = 0, ny - 1 do for tx = 0, nx - 1 do
                local t
                if fx or fy then t = code + (fx and nx - 1 - tx or tx) + 0x10 * (fy and ny - 1 - ty or ty)
                else t = (code & ~15) + ((code + tx) & 15) + 0x10 * ty end
                k.keys[t] = true
            end end
            k.pal[aw & 0x1f] = true
            k.a6[a & 0xffff00] = true
            local p = per[a]
            if not p then p = {id = id, x0 = xw & 0x3ff, y0 = yw & 0x3ff, e = {}}; per[a] = p end
            local dx, dy = ((xw & 0x3ff) - p.x0 + 512) % 1024 - 512, ((yw & 0x3ff) - p.y0 + 512) % 1024 - 512
            p.e[#p.e + 1] = string.format("%d,%d,%x,%x", dx, dy, code, aw & 0xff7f)
            p.s = (p.s or "") .. string.format("%d,%d,%x,%x;", dx, dy, code, aw & 0xff60)
        end
        n = n + 1
    end
    for a, p in pairs(per) do
        local k = K[p.id]
        k.frames = k.frames + 1
        k.stages[cur] = true
        local sig = p.s
        local st = string.format("%02x%02x%02x", rb(a + 4), rb(a + 5), rb(a + 6))
        k.st[st] = k.st[st] or {}
        k.st[st][sig] = true
        if not k.poses[sig] then
            k.poses[sig] = 1
            if #k.samples < nsamp then
                local pals, used = {}, {}
                for _, e in ipairs(p.e) do
                    local pl = tonumber(e:match("([0-9a-f]+)$"), 16) & 0x1f
                    if not used[pl] then
                        used[pl] = true
                        local c = {}
                        for i = 0, 15 do c[#c + 1] = string.format("%06x", pen(pl * 16 + i)) end
                        pals[#pals + 1] = pl .. "=" .. table.concat(c, ",")
                    end
                end
                k.samples[#k.samples + 1] = string.format("%02x\t%s\t%s\t%s", cur, st, table.concat(p.e, ";"), table.concat(pals, "|"))
            end
        else
            k.poses[sig] = k.poses[sig] + 1
        end
    end
end)
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local F = {coin = in2["Coin 1"], start = in2["1 Player Start"], left = in0["P1 Left"], right = in0["P1 Right"], up = in0["P1 Up"], down = in0["P1 Down"],
           gun = in0["P1 Button 1"], atk = in0["P1 Button 2"], jump = in0["P1 Button 3"]}
local function set(k, on) if on then F[k]:set_value(1) else F[k]:clear_value() end end
local log = assert(io.open(root .. "/walk.tsv", "w"))
local frame, lastx, stuck, dir, last = 0, 0, 0, 0, ""
local want, picked, story = tonumber(os.getenv("AM_CHAR") or "0"), nil, false
local seen26 = false
am_f = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local stage, sec, att, cred, top, p0 = rd(0xff81e8), rb(0xffd182), rb(0xff81b0), rb(0xff818c), rb(0xff8384), rb(0xff8380)
    local x = rd(0xff8390)
    local b = (att ~= 0 or rb(0xff8001) ~= 2) and 0 or stage
    if b ~= cur then
        cur = b
        log:write(string.format("STAGE %x frame %d\n", b, frame)); log:flush()
        dump()
        if b == 0x26 then seen26 = true end
        if seen26 and b == 0 then machine:exit(); return end
    end
    if frame % 600 == 0 then log:write(string.format("%d\tst %x sec %d att %d p0 %d x %d\n", frame, stage, sec, att, p0, x)); log:flush() end
    if frame % 6000 == 0 then dump() end
    if frame >= maxf then dump(); machine:exit(); return end
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
