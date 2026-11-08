-- Lane avp-megaman: the Hunter gun shot actors (who draws sprites while the Hunter shoots), under MAME (avspu). From avp_states.lua.
-- Same select walk as tools/alien_measure/alien_walk.lua (AM_CHAR 3 = Hunter); then a fixed input script once play starts.
-- Writes MS_OUT/shots.tsv: frame, actor, its first 0xc0 bytes, for each actor drawing while the Hunter is in a gun state. ROM-derived output stays under E:/AvP/learning.
local machine = manager.machine
local prog = machine.devices[":maincpu"].spaces["program"]
local root = assert(os.getenv("MS_OUT"))
local rd = function(a) return prog:read_u16(a) end
local rb = function(a) return prog:read_u8(a) end
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local F = {coin = in2["Coin 1"], start = in2["1 Player Start"], left = in0["P1 Left"], right = in0["P1 Right"], up = in0["P1 Up"], down = in0["P1 Down"],
           gun = in0["P1 Button 1"], atk = in0["P1 Button 2"], jump = in0["P1 Button 3"]}
local function set(k, on) if on then F[k]:set_value(1) else F[k]:clear_value() end end
local out = assert(io.open(root .. "/shots.tsv", "w"))
local A6 = machine.devices[":maincpu"].state["A6"]
local seen = {}
ms_wr = prog:install_write_tap(0x708000, 0x70bfff, "ms_wr", function(o, d, m)
    if (o & 7) == 4 then
        local a = A6.value & 0xffffff
        local b = 0xff8380
        local st = rb(b + 4) * 65536 + rb(b + 5) * 256 + rb(b + 6)
        if a >= 0xff0000 and (a < 0xff8380 or a >= 0xff8680) and (st == 0x02000c or st == 0x02001a) and not seen[a] then
            seen[a] = true
            local t = {}
            for i = 0, 0xbf do t[#t + 1] = string.format("%02x", rb(a + i)) end
            out:write(string.format("%d	%06x	%s" .. string.char(10), frame or 0, a, table.concat(t)))
        end
    end
end)
-- phase name, seconds, held keys (tap = pressed only the first 4 frames)
local PLAN = {
  {"idle", 2, {}}, {"walk_r", 2, {"right"}}, {"walk_up", 1, {"up"}}, {"walk_down", 1, {"down"}}, {"idle2", 1, {}},
  {"atk1", 1, {tap = {"atk"}}}, {"atk_chain", 2, {rep = {"atk"}}}, {"idle3", 1, {}},
  {"gun", 2, {rep = {"gun"}}}, {"idle4", 1, {}}, {"jump", 1.5, {tap = {"jump"}}}, {"jump_atk", 1.5, {tap = {"jump"}, late = {"atk"}}},
  {"dash", 1.5, {dtap = "right"}}, {"special", 2, {tap = {"atk", "jump"}}}, {"idle5", 1, {}}, {"walk_l", 2, {"left"}}, {"idle6", 60, {}},
}
frame = 0
local picked, story, want, start = nil, false, 3, nil
local stuckfor = 0
am_f = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local stage, att, cred, top, p0 = rd(0xff81e8), rb(0xff81b0), rb(0xff818c), rb(0xff8384), rb(0xff8380)
    prog:write_u16(0xff83c0, 0x65)   -- health held for the walk; hits still show their states
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
        set("right", pick and since >= 190 and since < 194)
        set("down", pick and since >= 225 and since < 229)
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
    local b = 0xff8380
    out:write(string.format("%d\t%s\t%02x%02x%02x\t%02x\t%d\t%d\t%02x\n", frame, ph[1], rb(b + 4), rb(b + 5), rb(b + 6), rb(b + 0x0f), rd(b + 0x10), rd(b + 0x14), rb(b + 0xd2)))
end)
