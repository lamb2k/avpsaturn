-- Wolverine sounds (lane wv-sounds): renders MSHvSF sound commands one by one through the real Z80 driver and QSound under MAME 0.289 (after saturn/audio/render_mame.lua for AvP,
-- same mailbox layout: Z80 0xc000/c001 command, c003/c004 parameter, c006 pan mode, c007 pan, c008 span, c009..c00c rates, c00f handshake). The 68000's handshake write is blocked after boot.
-- Run with -wavwrite OUT.wav -sound none. Writes AUDIO_LOG (tsv "cmd S|E frame time") and, per command, the QSound voice starts (qs.tsv: cmd, frame, DSP reg writes).
-- env: AUDIO_CMDS file with one "hexcmd frames" per line (frames: how long to let it play), AUDIO_LOG, AUDIO_QS.
local z80 = manager.machine.devices[":audiocpu"].spaces["program"]
local prog = manager.machine.devices[":maincpu"].spaces["program"]
local cmds = {}
for l in io.lines(os.getenv("AUDIO_CMDS")) do
  local c, m = l:match("(%x+)%s+(%d+)")
  if c then cmds[#cmds + 1] = { tonumber(c, 16), tonumber(m) } end
end
local pre = {}
for c in (os.getenv("AUDIO_PRE") or ""):gmatch("%x+") do pre[#pre + 1] = tonumber(c, 16) end
local out = assert(io.open(os.getenv("AUDIO_LOG"), "w"))
local qs = assert(io.open(os.getenv("AUDIO_QS"), "w"))
local cur = 0
local aspace = manager.machine.devices[":audiocpu"].spaces["program"]
tapq = aspace:install_write_tap(0xd000, 0xd002, "wvr_q", function(o, d, m) qs:write(string.format("%x\t%04x\t%02x\n", cur, o & 0xffff, d & 0xff)) end)
local function send(c, pan)
  z80:write_u8(0xc000, (c >> 8) & 0xff); z80:write_u8(0xc001, c & 0xff)
  z80:write_u8(0xc003, 0); z80:write_u8(0xc004, 0)
  z80:write_u8(0xc006, 0); z80:write_u8(0xc007, pan or 0x10); z80:write_u8(0xc008, 0)
  for a = 0xc009, 0xc00c do z80:write_u8(a, 0) end
  z80:write_u8(0xc00f, 0)
end
local i, st, t, f = 0, "boot", 0, 0
audio_frame = emu.add_machine_frame_notifier(function()
  f = f + 1
  z80:write_u8(0xcffe, 0xff)
  if f == 500 then audio_block = prog:install_write_tap(0x61801e, 0x61801f, "audio_block", function(_, data, mask) return data | 0xff end) end
  t = t + 1
  if st == "boot" then
    if f >= 600 then st = "stop"; t = 0 end
  elseif st == "stop" then
    send(0xff00); if t >= 30 then st = #pre > 0 and "pre" or "next"; t = 0 end
  elseif st == "pre" then   -- AUDIO_PRE: commands sent once before the list (e.g. 484: the VS screen's call that loads Wolverine's voice set for the left player), 90 frames each
    if t == 1 then cur = pre[1]; send(pre[1]); out:write(string.format("%x" .. string.char(9) .. "P" .. string.char(9) .. "%d" .. string.char(9) .. "%.6f" .. string.char(10), pre[1], f, manager.machine.time:as_double())) end
    if t >= 90 then table.remove(pre, 1); send(0xff00); st = #pre > 0 and "pre" or "gap"; t = 0 end
  elseif st == "next" then
    i = i + 1
    if i > #cmds then out:close(); qs:close(); manager.machine:exit(); return end
    cur = cmds[i][1]
    send(cmds[i][1])
    out:write(string.format("%x\tS\t%d\t%.6f\n", cmds[i][1], f, manager.machine.time:as_double()))
    st = "play"; t = 0
  elseif st == "play" then
    if t >= cmds[i][2] then
      out:write(string.format("%x\tE\t%d\t%.6f\n", cmds[i][1], f, manager.machine.time:as_double())); out:flush()
      send(0xff00); st = "gap"; t = 0
    end
  elseif st == "gap" then
    if t >= 24 then st = "next"; t = 0 end
  end
end)
