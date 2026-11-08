-- Wolverine guest extraction (lane avp-wolverine). Drives MSHvSF with an input schedule, writes per-frame
-- object lists (text), sprite palettes, and at exit the graphics tiles of every sprite code seen.
-- env: WV_POKE (see below), WV_ROOT out dir, WV_SEQ schedule "frame field value", WV_LAST, WV_FROM, WV_SNAP (snapshot step, 0 none).
-- Output is ROM-derived: it stays under E:/AvP/learning, never in git.
local machine = manager.machine
local screen = machine.screens[":screen"]
local prog = machine.devices[":maincpu"].spaces["program"]
local ports = {machine.ioport.ports[":IN0"].fields, machine.ioport.ports[":IN1"].fields, machine.ioport.ports[":IN2"].fields}
local root, last = os.getenv("WV_ROOT"), tonumber(os.getenv("WV_LAST"))
local from, snap = tonumber(os.getenv("WV_FROM")), tonumber(os.getenv("WV_SNAP") or "0")
-- WV_POKE "frame:addr:value,...": byte writes before a frame (used once to end a round for the win pose).
local pokes = {}
for f, a, v in (os.getenv("WV_POKE") or ""):gmatch("(%d+):(%x+):(%x+)") do pokes[#pokes + 1] = {tonumber(f), tonumber(a, 16), tonumber(v, 16)} end
-- WV_TRACE "from:to:file": MAME debugger execution trace of the main CPU for that frame window (needs -debug; the interface census).
local trace = nil
do local a, b, f = (os.getenv("WV_TRACE") or ""):match("^(%d+):(%d+):(.+)$"); if a then trace = {tonumber(a), tonumber(b), f} end end
-- WV_CHTAP: log which entry of MSHvSF's per-character table (0xc38a, read at 0xc220 with a6 = player) each player reads, once per player.
if os.getenv("WV_CHTAP") then
  local cpu = machine.devices[":maincpu"]
  local seen = {}
  chtap = prog:install_read_tap(0xc38a, 0xc47f, "wv_ch", function(o, d, m)
    local a6 = cpu.state["A6"].value
    local k = string.format("%x:%x", a6, o)
    if not seen[k] then seen[k] = true; io.open(root .. "/chtab.txt", "a"):write(string.format("CHTAB a6=%06x off=%x id52=%04x d=%04x x=%04x", a6, o - 0xc38a, prog:read_u16(a6 + 0x52), d, prog:read_u16(a6 + 0x10)) .. string.char(10)) end
  end)
end
local edges = {}
for line in io.lines(os.getenv("WV_SEQ")) do
  local f, name, v = line:match("^(%d+)%s+(.-)%s+(%d)$")
  if f then edges[#edges + 1] = {tonumber(f), name, tonumber(v)} end
end
local function field(n) for _, p in ipairs(ports) do if p[n] then return p[n] end end end
local bank = 0
tap = prog:install_write_tap(0x8040e0, 0x8040e1, "wv_bank", function(o, d, m) bank = d & 1 end)
local objf = assert(io.open(root .. "/obj.txt", "w"))
local palf = assert(io.open(root .. "/pal.bin", "wb"))
local codes = {}
local frame = 0
local function dump()
  local share = bank == 0 and machine.memory.shares[":objram1"] or machine.memory.shares[":objram2"]
  objf:write("f " .. frame .. "\n")
  for o = 0, share.size - 8, 8 do
    local x, y, c, a = share:read_u16(o), share:read_u16(o + 2), share:read_u16(o + 4), share:read_u16(o + 6)
    if y >= 0x8000 or (a & 0xff00) == 0xff00 then break end
    objf:write(string.format("%04x %04x %04x %04x\n", x, y, c, a))
    local code = c | ((y & 0x6000) << 3)
    local xs, ys = ((a >> 8) & 15) + 1, ((a >> 12) & 15) + 1
    for by = 0, ys - 1 do for bx = 0, xs - 1 do codes[code + bx + by * 16] = true end end
  end
  local p = machine.palettes[":palette"]
  palf:write(string.pack(">I4", frame))
  for i = 0, 511 do
    local col = p:pen_color(i)
    palf:write(string.char((col >> 16) & 0xff, (col >> 8) & 0xff, col & 0xff))
  end
end
local function finish()
  objf:close(); palf:close()
  local g = machine.memory.regions[":gfx"]
  local t = assert(io.open(root .. "/tiles.bin", "wb"))
  local list = {}
  for c in pairs(codes) do list[#list + 1] = c end
  table.sort(list)
  for _, c in ipairs(list) do
    if (c + 1) * 128 <= g.size then
      t:write(string.pack(">I4", c))
      for i = 0, 127 do t:write(string.char(g:read_u8(c * 128 + i))) end
    end
  end
  t:close()
end
sub = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  for _, e in ipairs(edges) do
    if e[1] == frame then
      local fl = field(e[2])
      if fl then fl:set_value(e[3]) else print("nofield " .. e[2]) end
    end
  end
  if os.getenv("WV_CHTAP") and (frame == 1995 or frame == 2061) then
    io.open(root .. "/chtab.txt", "a"):write((function() local t = {"F" .. frame} for b = 0xff3800, 0xff3c00, 0x400 do local h = {} for i = 0, 0x1ff do h[#h + 1] = string.format("%02x", prog:read_u8(b + i)) end t[#t + 1] = table.concat(h) end return table.concat(t, " ") end)() .. string.char(10))
  end
  if os.getenv("WV_DBGCMD") and frame == tonumber(os.getenv("WV_DBGAT") or "0") then
    for c in os.getenv("WV_DBGCMD"):gmatch("[^;]+") do machine.debugger:command(c) end
  end
  if trace and frame == trace[1] then machine.debugger:command("trace " .. (trace[3]:find(",") and trace[3] or trace[3] .. ",maincpu,noloop")) end
  if trace and frame == trace[2] then machine.debugger:command("trace off") end
  for _, p in ipairs(pokes) do if p[1] == frame then prog:write_u8(p[2], p[3]) end end
  if snap > 0 and frame % snap == 0 then screen:snapshot(string.format("wv/f_%05d.png", frame)) end
  if frame >= from then dump() end
  if frame >= last then finish(); machine:exit() end
end)
