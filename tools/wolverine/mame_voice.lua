-- Wolverine's Berserker Barrage voice (lane wolverine-reveal): drives MSHvSF with the same input schedule as mame_wolverine.lua and logs every QSound DSP register write of the
-- Z80 (ports 0xd000 data, 0xd002 register) with the frame it happened in, to qsound_writes.tsv, and dumps the QSound sample ROM (qsound.bin) at the end.
-- tools/wolverine/reveal_voice.py reads both: it finds the voice starts of the move, cuts the sample from the ROM and writes the build's reveal_voice.bin. Output is ROM-derived: it stays under E:/AvP/learning, never in git.
-- env: WV_ROOT out dir, WV_SEQ schedule "frame field value", WV_LAST last frame.
local machine = manager.machine
local ports = {machine.ioport.ports[":IN0"].fields, machine.ioport.ports[":IN1"].fields, machine.ioport.ports[":IN2"].fields}
local root, last = os.getenv("WV_ROOT"), tonumber(os.getenv("WV_LAST"))
local edges = {}
for line in io.lines(os.getenv("WV_SEQ")) do
  local f, name, v = line:match("^(%d+)%s+(.-)%s+(%d)$")
  if f then edges[#edges + 1] = {tonumber(f), name, tonumber(v)} end
end
local function field(n) for _, p in ipairs(ports) do if p[n] then return p[n] end end end
local frame = 0
local out = assert(io.open(root .. "/qsound_writes.tsv", "w"))
out:write("frame\tport\tvalue\n")
local acpu = machine.devices[":audiocpu"]
local aspace = acpu.spaces["program"]
tap = aspace:install_write_tap(0xd000, 0xd002, "wv_qsound", function(offset, data, mask)
  out:write(string.format("%d\t%04x\t%02x\n", frame, offset & 0xffff, data & 0xff))
end)
-- the 68000's writes to the sound mailbox (QSound shared RAM, 0x618000): the command numbers of each move
local prog = machine.devices[":maincpu"].spaces["program"]
local cmd = assert(io.open(root .. "/cmd_writes.tsv", "w"))
cmd:write("frame\toffset\tvalue\n")
tap2 = prog:install_write_tap(0x618000, 0x619fff, "wv_cmd", function(offset, data, mask)
  cmd:write(string.format("%d\t%04x\t%04x\n", frame, offset & 0xffff, data & 0xffff))
end)
sub = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  for _, e in ipairs(edges) do
    if e[1] == frame then
      local fl = field(e[2])
      if fl then fl:set_value(e[3]) else print("nofield " .. e[2]) end
    end
  end
  if frame >= last then
    out:close(); cmd:close()
    local r = machine.memory.regions[":qsound"]
    if r then
      local f = assert(io.open(root .. "/qsound.bin", "wb"))
      local chunk = {}
      for i = 0, r.size - 1 do
        chunk[#chunk + 1] = string.char(r:read_u8(i))
        if #chunk == 65536 then f:write(table.concat(chunk)); chunk = {} end
      end
      f:write(table.concat(chunk)); f:close()
    else
      local names = {}
      for k in pairs(machine.memory.regions) do names[#names + 1] = k end
      print("no qsound region; regions: " .. table.concat(names, " "))
    end
    machine:exit()
  end
end)
