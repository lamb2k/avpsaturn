-- Wolverine sounds (lane wv-sounds): drives MSHvSF with an input schedule and logs, per frame, the sound commands the 68000 sends to the QSound mailbox
-- (0x618000..0x61801f: command high byte at +0, low byte at +2, pan at +0xe), the Z80's QSound DSP register writes, and both players' state words
-- (block 0xff3800 + 0x400 * i: +0x06 state, +0x52 character id), so each command can be attributed to a move. Output is ROM-derived: it stays under E:/AvP/learning.
-- env: WV_ROOT out dir, WV_SEQ schedule "frame field value", WV_LAST last frame, WV_POKE "frame:addr:value,..." byte pokes, WV_QS=1 also dump the QSound ROM.
local machine = manager.machine
local ports = {machine.ioport.ports[":IN0"].fields, machine.ioport.ports[":IN1"].fields, machine.ioport.ports[":IN2"].fields}
local root, last = os.getenv("WV_ROOT"), tonumber(os.getenv("WV_LAST"))
local edges = {}
for line in io.lines(os.getenv("WV_SEQ")) do
  local f, name, v = line:match("^(%d+)%s+(.-)%s+(%d)$")
  if f then edges[#edges + 1] = {tonumber(f), name, tonumber(v)} end
end
local function field(n) for _, p in ipairs(ports) do if p[n] then return p[n] end end end
local pokes = {}
for f, a, v in (os.getenv("WV_POKE") or ""):gmatch("(%d+):(%x+):(%x+)") do pokes[#pokes + 1] = {tonumber(f), tonumber(a, 16), tonumber(v, 16)} end
local frame = 0
local pokeall = {}
for a, v in (os.getenv("WV_POKEALL") or ""):gmatch("(%x+):(%x+)") do pokeall[#pokeall + 1] = {tonumber(a, 16), tonumber(v, 16)} end
if #pokeall == 0 then pokeall = nil end
local ramf = os.getenv("WV_RAM") and assert(io.open(root .. "/ram.bin", "wb"))
local adj = tonumber(os.getenv("WV_ADJ") or "")
local dumpf = os.getenv("WV_DUMP") and assert(io.open(root .. "/blocks.bin", "wb"))
local snaps = {}
for f in (os.getenv("WV_SNAPS") or ""):gmatch("%d+") do snaps[tonumber(f)] = true end
local qs = assert(io.open(root .. "/qsound_writes.tsv", "w")); qs:write("frame\tport\tvalue\n")
local aspace = machine.devices[":audiocpu"].spaces["program"]
tap1 = aspace:install_write_tap(0xd000, 0xd002, "wvs_q", function(o, d, m) qs:write(string.format("%d\t%04x\t%02x\n", frame, o & 0xffff, d & 0xff)) end)
local prog = machine.devices[":maincpu"].spaces["program"]
local cmd = assert(io.open(root .. "/cmd.tsv", "w")); cmd:write("frame\tcmd\tpan\ta6\ta5\ta4\tpc\tret\n")
local mb = {}
tap2 = prog:install_write_tap(0x618000, 0x61801f, "wvs_c", function(o, d, m) local ok, err = pcall(function()
  local a = o & 0xffff
  if a == 0x801e or a == 0x801f then   -- handshake write: the entry is complete
    local cpu = machine.devices[":maincpu"]
    local sp = (cpu.state["A7"] or cpu.state["SP"] or cpu.state["USP"]).value
    local T = string.char(9)
    local r = {frame, string.format("%02x%02x", mb[0x8000] or 0, mb[0x8002] or 0), string.format("%02x", mb[0x800e] or 0)}
    for _, n in ipairs({"A6", "A5", "A4", "PC"}) do r[#r + 1] = string.format("%06x", cpu.state[n].value & 0xffffff) end
    r[#r + 1] = string.format("%06x", prog:read_u32(sp) & 0xffffff)
    cmd:write(table.concat(r, T) .. string.char(10))
  else mb[a] = d & 0xff end
end) if not ok then io.stderr:write("TAPERR " .. tostring(err) .. string.char(10)) end end)

-- the ring the 68000's sender drains (a4 at the send): log each write into it with the writer's pc, a6 and the two words on the stack, to find the caller (player block in a6, return addresses)
local rg = assert(io.open(root .. "/ring.tsv", "w"))
tap3 = prog:install_write_tap(0xff2b00, 0xff2fff, "wvs_r", function(o, d, m)
  local ok, err = pcall(function()
    local cpu = machine.devices[":maincpu"]
    local sp = (cpu.state["A7"] or cpu.state["SP"]).value
    local T = string.char(9)
    local r = {frame, string.format("%06x", o & 0xffffff), string.format("%04x", d & 0xffff), string.format("%06x", cpu.state["PC"].value & 0xffffff), string.format("%06x", cpu.state["A6"].value & 0xffffff),
               string.format("%06x", prog:read_u32(sp) & 0xffffff), string.format("%06x", prog:read_u32(sp + 4) & 0xffffff), string.format("%06x", prog:read_u32(sp + 8) & 0xffffff)}
    rg:write(table.concat(r, T) .. string.char(10))
  end)
  if not ok then io.stderr:write("RINGERR " .. tostring(err) .. string.char(10)) end
end)
local st = assert(io.open(root .. "/state.tsv", "w")); st:write("frame\tp1st\tp1id\tp2st\tp2id\tp1x\tp2x\n")
sub = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  for _, p in ipairs(pokes) do if p[1] == frame then prog:write_u8(p[2], p[3]) end end
  for _, e in ipairs(edges) do
    if e[1] == frame then local fl = field(e[2]); if fl then fl:set_value(e[3]) else print("nofield " .. e[2]) end end
  end
  if snaps[frame] then machine.screens[":screen"]:snapshot(string.format("%s/snap_%05d.png", root, frame)) end
  if adj and frame >= 2060 then   -- WV_ADJ=offset: hold player 2 that many pixels in front of player 1 so every attack lands
    local x1 = prog:read_u16(0xff380c)
    prog:write_u16(0xff3c0c, (x1 + adj) & 0xffff)
  end
  if ramf and frame >= 2000 and frame < 3000 and frame % 3 == 0 then
    ramf:write(string.pack(">I4", frame))
    for a = 0xff0000, 0xffffff, 2 do ramf:write(string.pack(">I2", prog:read_u16(a))) end
  end
  if pokeall and frame >= 1990 then for _, q in ipairs(pokeall) do prog:write_u8(q[1], q[2]) end end
  if dumpf and frame >= 2000 and frame < 3300 then
    dumpf:write(string.pack(">I4", frame))
    for _, b in ipairs({0xff3800, 0xff3c00}) do for a = b, b + 0x1ff, 2 do dumpf:write(string.pack(">I2", prog:read_u16(a))) end end
  end
  if frame >= 1900 then
    st:write(string.format("%d\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\n", frame, prog:read_u16(0xff3806), prog:read_u16(0xff3852), prog:read_u16(0xff3c06), prog:read_u16(0xff3c52), prog:read_u16(0xff380c), prog:read_u16(0xff3c0c)))
  end
  if frame >= last then
    if dumpf then dumpf:close() end if ramf then ramf:close() end qs:close(); cmd:close(); st:close(); rg:close()
    if os.getenv("WV_QS") then
      local r = machine.memory.regions[":qsound"]
      local f = assert(io.open(root .. "/qsound.bin", "wb"))
      local chunk = {}
      for i = 0, r.size - 1 do chunk[#chunk + 1] = string.char(r:read_u8(i)); if #chunk == 65536 then f:write(table.concat(chunk)); chunk = {} end end
      f:write(table.concat(chunk)); f:close()
    end
    machine:exit()
  end
end)
