-- Scroll 1 tile keys at the picture's outer columns (arcade columns 0, 1 and 47), which the census (tools/satint_census.lua) never reads: it
-- reads the 16 pixel centre crop, columns 2 to 46. Home builds show those columns on the HUD rows and in fitted text rows (saturn/gfx
-- draw_scroll1), so their tiles (P1's portrait and 1P mark, the right edge of P2's PRESS START) must be in every stage file.
-- env AVSP_ROUTE (saved route, replayed to its last frame), EDGE_OUT (keys file, "1 hexkey" lines as tools/screen_keys.lua)
local route, outp = os.getenv("AVSP_ROUTE"), os.getenv("EDGE_OUT")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local in0 = manager.machine.ioport.ports[":IN0"].fields
local in2 = manager.machine.ioport.ports[":IN2"].fields
local F = {in2["Coin 1"], in2["1 Player Start"], in0["P1 Left"], in0["P1 Right"], in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"], in0["P1 Up"], in0["P1 Down"],
           in2["Coin 2"], in2["2 Players Start"], in0["P2 Left"], in0["P2 Right"], in0["P2 Button 1"], in0["P2 Button 2"], in0["P2 Button 3"], in0["P2 Up"], in0["P2 Down"]}
local steps, last = {}, 0
for l in io.lines(route) do
    local a, b = l:match("^(%d+) (%d+)")
    if a then steps[tonumber(a)] = tonumber(b); if tonumber(a) > last then last = tonumber(a) end end
end
local function set(w) for i, f in ipairs(F) do if f then if w & (1 << (i - 1)) ~= 0 then f:set_value(1) else f:clear_value() end end end end
local keys, frame = {}, 0
local rd = function(a) return mem:read_u16(a) end
local function out()
    local list = {}
    for k in pairs(keys) do list[#list + 1] = k end
    table.sort(list)
    local o = io.open(outp, "w")
    for _, k in ipairs(list) do o:write(string.format("1 %x\n", k)) end
    o:close()
end
edge_n = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    if steps[frame] then set(steps[frame]) end
    if rd(0xff804a) & 2 ~= 0 then
        local m = (rd(0xff8024) & 0xffc0) * 0x100
        local x0, y0 = rd(0xffee1a) + 64, rd(0xffee1c) + 16
        for row = 0, 28 do for _, col in ipairs({0, 1, 47}) do
            local c, r = ((x0 >> 3) + col) & 63, ((y0 >> 3) + row) & 63
            local i = (r & 0x1f) + (c << 5) + ((r & 0x20) << 6)
            local w = rd(m + i * 4)
            keys[(w << 1) | ((i >> 5) & 1)] = true
        end end
    end
    if frame % 20000 == 0 then out() end
    if frame >= last + 600 then out(); manager.machine:exit() end
end)
