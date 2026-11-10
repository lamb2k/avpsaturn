-- Sound test for MSHvSF (lane wolverine-reveal): from frame START on, sends sound command FIRST, FIRST+1 .. LAST to the Z80 every STEP frames through the 68000's own mailbox
-- (0x618000: hi byte at word 0x8000, lo byte at 0x8002, the trigger word 0x801e written last, as the game's sender does it) and logs the QSound DSP writes with the frame (qsound_writes.tsv)
-- and each command with its frame (inject.tsv). The sample ROM goes to qsound.bin. reveal_voice.py reads them. ROM-derived output stays under E:/AvP/learning.
-- env: WV_ROOT, WV_START (default 400), WV_FIRST, WV_LAST, WV_STEP (default 40).
local machine = manager.machine
local root = os.getenv("WV_ROOT")
local start, first, lastc, step = tonumber(os.getenv("WV_START") or "400"), tonumber(os.getenv("WV_FIRST")), tonumber(os.getenv("WV_LAST")), tonumber(os.getenv("WV_STEP") or "40")
local frame = 0
local out = assert(io.open(root .. "/qsound_writes.tsv", "w"))
out:write("frame\tport\tvalue\n")
local inj = assert(io.open(root .. "/inject.tsv", "w"))
local acpu = machine.devices[":audiocpu"]
tap = acpu.spaces["program"]:install_write_tap(0xd000, 0xd002, "wv_qsound", function(offset, data, mask)
  out:write(string.format("%d\t%04x\t%02x\n", frame, offset & 0xffff, data & 0xff))
end)
local prog = machine.devices[":maincpu"].spaces["program"]
local endframe = start + (lastc - first + 1) * step + 60
sub = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  if frame >= start and (frame - start) % step == 0 then
    local n = first + (frame - start) // step
    if n <= lastc and not os.getenv("WV_NOINJ") then
      inj:write(string.format("%d\t%d\n", frame, n))
      for _, o in ipairs({0x8006, 0x8008}) do prog:write_u16(0x618000 + (o - 0x8000), 0) end
      prog:write_u16(0x618000, ((n >> 8) & 0xff) * 0x101)
      prog:write_u16(0x618002, (n & 0xff) * 0x101)
      for _, o in ipairs({0x8004, 0x800c, 0x800e, 0x8010, 0x8016, 0x8018, 0x8012, 0x8014}) do prog:write_u16(0x618000 + (o - 0x8000), 0) end
      prog:write_u16(0x61801e, 0)
    end
  end
  if frame >= endframe then
    out:close(); inj:close()
    local r = machine.memory.regions[":qsound"]
    local f = assert(io.open(root .. "/qsound.bin", "wb"))
    local chunk = {}
    for i = 0, r.size - 1 do
      chunk[#chunk + 1] = string.char(r:read_u8(i))
      if #chunk == 65536 then f:write(table.concat(chunk)); chunk = {} end
    end
    f:write(table.concat(chunk)); f:close()
    machine:exit()
  end
end)
