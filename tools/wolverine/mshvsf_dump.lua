-- Lane wv-native-gfx 11-09: dump MSHvSF's 68000 program space (data view and opcode view) and, at chosen frames, the player blocks, under MAME 0.289 (via the MSHvSF repo's
-- tools/run_mshvsf_mame.py), driven by the same input schedule as mame_wolverine.lua. Output is ROM-derived: keep it under E:/AvP/learning, never in git.
-- env: MV_OUT out dir, MV_SEQ schedule file ("frame field value"), MV_FRAMES "f,f,..." frames at which the player blocks are dumped, MV_ROM=1 dumps the ROM once at the first of them,
-- MV_TRACK "from:to" dumps player 1's block (0x400 bytes at ff3800) every frame of that window to track.bin (frame number, then the bytes).
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local opc = cpu.spaces["opcodes"]
local ports = {machine.ioport.ports[":IN0"].fields, machine.ioport.ports[":IN1"].fields, machine.ioport.ports[":IN2"].fields}
local out = os.getenv("MV_OUT")
local edges = {}
for line in io.lines(os.getenv("MV_SEQ")) do
  local f, name, v = line:match("^(%d+)%s+(.-)%s+(%d)$")
  if f then edges[#edges + 1] = {tonumber(f), name, tonumber(v)} end
end
local frames = {}
for f in (os.getenv("MV_FRAMES") or ""):gmatch("%d+") do frames[tonumber(f)] = true end
local tfrom, tto = (os.getenv("MV_TRACK") or ""):match("^(%d+):(%d+)$")
tfrom, tto = tonumber(tfrom), tonumber(tto)
local function field(n) for _, p in ipairs(ports) do if p[n] then return p[n] end end end
local function dump_space(sp, name, size)
  local f = assert(io.open(out .. "/" .. name, "wb"))
  local step = 0x10000
  for a = 0, size - 1, step do
    local t = {}
    for i = 0, step - 1, 2 do t[#t + 1] = string.pack(">I2", sp:read_u16(a + i)) end
    f:write(table.concat(t))
  end
  f:close()
end
local bank = 0
tap = prog:install_write_tap(0x8040e0, 0x8040e1, "mv_bank", function(o, d, m) bank = d & 1 end)
local frame, romdone, gfxdone = 0, false, false
local trk = nil
sub = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  for _, e in ipairs(edges) do
    if e[1] == frame then local fl = field(e[2]); if fl then fl:set_value(e[3]) end end
  end
  if frames[frame] then
    if os.getenv("MV_ROM") and not romdone then
      romdone = true
      dump_space(prog, "prog_data.bin", 0x400000)
      dump_space(opc, "prog_opc.bin", 0x400000)
    end
    if os.getenv("MV_GFX") and not gfxdone then
      gfxdone = true
      local g = machine.memory.regions[":gfx"]
      local gf = assert(io.open(out .. "/gfx_a000.bin", "wb"))
      for a = 0, 0xa000 * 128 - 1, 4096 do
        local t = {}
        for i = 0, 4095 do t[#t + 1] = string.char(g:read_u8(a + i)) end
        gf:write(table.concat(t))
      end
      gf:close()
    end
    local f = assert(io.open(string.format("%s/ram_%05d.bin", out, frame), "wb"))
    for a = 0xff0000, 0xffffff, 2 do f:write(string.pack(">I2", prog:read_u16(a))) end
    f:close()
  end
  if frames[frame] then
    local share = (bank == 0) and machine.memory.shares[":objram1"] or machine.memory.shares[":objram2"]
    local f = assert(io.open(string.format("%s/obj_%05d.txt", out, frame), "w"))
    for o = 0, share.size - 8, 8 do
      local x, y, c, a = share:read_u16(o), share:read_u16(o + 2), share:read_u16(o + 4), share:read_u16(o + 6)
      if y >= 0x8000 or (a & 0xff00) == 0xff00 then break end
      f:write(string.format("%04x %04x %04x %04x\n", x, y, c, a))
    end
    f:close()
  end
  if tfrom and frame >= tfrom and frame <= tto then
    trk = trk or assert(io.open(out .. "/track.bin", "wb"))
    trk:write(string.pack(">I4", frame))
    for a = 0xff3800, 0xff3bff, 2 do trk:write(string.pack(">I2", prog:read_u16(a))) end
  end
  if frame > (tto or 0) and frame > 2100 then if trk then trk:close() end; machine:exit() end
end)
