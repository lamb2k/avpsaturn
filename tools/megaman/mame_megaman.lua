-- Mega Man guest extraction (lane avp-megaman). Drives MvC (mvsc) with an input schedule, writes per-frame
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
  for _, p in ipairs(pokes) do if p[1] == frame then prog:write_u8(p[2], p[3]) end end
  if snap > 0 and frame % snap == 0 then screen:snapshot(string.format("wv/f_%05d.png", frame)) end
  if frame >= from then dump() end
  if frame >= last then finish(); machine:exit() end
end)
