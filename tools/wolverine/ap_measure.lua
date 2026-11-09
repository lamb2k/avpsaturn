-- Lane wolverine-ground (from char_measure.lua): sprite-list capture of an AvP player standing and jumping, for apex / height / scale measurement.
-- Writes MS_OUT/objs.txt: 'f frame phase px pz camx camy' then one 'x y code attr' line per object. Original header: per-character player measurement under MAME 0.289 (avspu). Same select walk as schaefer_states.lua (WV_CHAR 0 Warrior,
-- 1 Schaefer, 2 Linn, 3 Hunter), then a scripted input run: states (idle, walk, attack chain, dash, jump, jump attack, special), then a "fight"
-- stretch (walk right and mash, so enemies come to the player). Every tick logs the player's state, position, health, frame record pointers and the
-- 16-byte attack record the collision pass would use (f_1cf54: frame +1c byte 9 indexes T + word T[2] + idx*16, T = long +50), plus up to three
-- tag 0c enemy blocks near the player (x, depth, health, state, hitstop). Output MS_OUT/objs.txt (ROM-derived, stays under E:/AvP/learning).
local machine = manager.machine
local prog = machine.devices[":maincpu"].spaces["program"]
local root = assert(os.getenv("MS_OUT"))
local rd = function(a) return prog:read_u16(a) end
local rb = function(a) return prog:read_u8(a) end
local rl = function(a) return prog:read_u32(a) end
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local F = {coin = in2["Coin 1"], start = in2["1 Player Start"], left = in0["P1 Left"], right = in0["P1 Right"], up = in0["P1 Up"], down = in0["P1 Down"],
           gun = in0["P1 Button 1"], atk = in0["P1 Button 2"], jump = in0["P1 Button 3"]}
local function set(k, on) if on then F[k]:set_value(1) else F[k]:clear_value() end end
local out = assert(io.open(root .. "/objs.txt", "w"))
local PLAN = {
  {"idle", 2, {}}, {"jump", 1.6, {tap = {"jump"}}}, {"idle2", 1, {}}, {"jump_fwd", 1.6, {"right", tap = {"jump"}}}, {"idle3", 1, {}}, {"jump2", 1.6, {tap = {"jump"}}}, {"idle4", 1, {}},
  {"walk_r", 1.5, {"right"}}, {"idle5", 1, {}},
}
local bank = 0
bt = prog:install_write_tap(0x8040e0, 0x8040e1, "ap_bank", function(o, d, m) bank = d & 1 end)
local frame, picked, story, want, start = 0, nil, false, tonumber(os.getenv("WV_CHAR") or "1"), nil
local B = 0xff8380
local function enemies(px)
    local list = {}
    for a = 0xff9a80, 0xffc680, 0x100 do
        if rb(a) ~= 0 and rb(a + 8) == 0x0c then
            local x = rd(a + 0x10)
            list[#list + 1] = {a = a, x = x, d = math.abs(x - px)}
        end
    end
    table.sort(list, function(p, q) return p.d < q.d end)
    return list
end
am_f = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local stage, att, cred, top, p0 = rd(0xff81e8), rb(0xff81b0), rb(0xff818c), rb(0xff8384), rb(0xff8380)
    if os.getenv("MS_NOHOLD") ~= "1" and rd(B + 0x40) < 0x65 then prog:write_u16(B + 0x40, 0x65) end   -- health held (MS_NOHOLD=1: not held, the health cost of moves shows)
    local playing = att == 0 and p0 ~= 0 and top ~= 4 and stage ~= 0
    local t = frame % 120
    for _, k in ipairs{"coin", "start", "left", "right", "up", "down", "gun", "atk", "jump"} do set(k, false) end
    if not playing and not start then
        set("coin", cred == 0 and t < 4)
        set("start", cred ~= 0 and t >= 60 and t < 64)
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
    if not start then start = frame + 240 end
    if frame < start then return end
    local f, acc, ph = frame - start, 0, nil
    for _, p in ipairs(PLAN) do
        local n = math.floor(p[2] * 60)
        if f < acc + n then ph = p; f = f - acc; break end
        acc = acc + n
    end
    if not ph then out:close(); machine:exit(); return end
    local k = ph[3]
    for _, key in ipairs(k) do set(key, true) end
    if k.tap then for _, key in ipairs(k.tap) do set(key, f < 4) end end
    if k.rep then for _, key in ipairs(k.rep) do set(key, f % 12 < 4) end end
    if k.late then for _, key in ipairs(k.late) do set(key, f >= 15 and f < 19) end end
    if k.dtap then set(k.dtap, f < 4 or (f >= 8 and f < 30)) end
    if k.fight then   -- 10 s cycle: walk right, mash; every third cycle a jump attack, a dash, the special
        local c, s = math.floor(f / 600) % 3, f % 600
        set("right", s < 360 or (s >= 400 and s < 440))
        if s % 60 < 30 then set("up", c == 1 and s < 300) end
        set("atk", s >= 60 and s < 540 and s % 20 < 4)
        if c == 1 and s % 120 == 90 then set("jump", true) end
        if c == 2 and s % 150 == 100 then set("atk", true); set("jump", true) end
    end
    local px = rd(B + 0x10)
    local share = bank == 0 and machine.memory.shares[":objram1"] or machine.memory.shares[":objram2"]
    out:write(string.format("f %d %s %d %d %d %d %02x%02x%02x\n", frame, ph[1], px, rd(B + 0x14), rd(0xff8278), rd(0xff827c), rb(B + 4), rb(B + 5), rb(B + 6)))
    for o = 0, share.size - 8, 8 do
        local x, y, c, a = share:read_u16(o), share:read_u16(o + 2), share:read_u16(o + 4), share:read_u16(o + 6)
        if y >= 0x8000 or (a & 0xff00) == 0xff00 then break end
        out:write(string.format("%04x %04x %04x %04x\n", x, y, c, a))
    end
end)
