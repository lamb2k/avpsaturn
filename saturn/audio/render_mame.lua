-- Offline render of avspu sound commands through the real Z80 driver and QSound under MAME 0.289, one wav per run.
-- After boot the 68000's handshake write is blocked, so this script is the only sender.
-- env: AUDIO_CMDS (file: one "hexcmd maxframes" per line), AUDIO_LOG (output tsv).
-- Or AUDIO_SCRIPT (file: "frame sound voice sweep", hex after the frame): the reference for a standalone comparison.
local z80 = manager.machine.devices[":audiocpu"].spaces["program"]
local prog = manager.machine.devices[":maincpu"].spaces["program"]
local cmds = {}
local script = {}
if os.getenv("AUDIO_SCRIPT") then
    for l in io.lines(os.getenv("AUDIO_SCRIPT")) do
        local fr, so, vo, sw = l:match("(%d+)%s+(%x+)%s+(%x+)%s+(%x+)")
        if fr then script[#script + 1] = { tonumber(fr), tonumber(so, 16), tonumber(vo, 16), tonumber(sw, 16) } end
    end
end
for l in io.lines(os.getenv("AUDIO_CMDS") or "NUL") do
    local c, m = l:match("(%x+)%s+(%d+)")
    if c then cmds[#cmds + 1] = { tonumber(c, 16), tonumber(m) } end
end
local out = assert(io.open(os.getenv("AUDIO_LOG"), "w"))
local function send(c)
    z80:write_u8(0xc000, (c >> 8) & 0xff); z80:write_u8(0xc001, c & 0xff)
    z80:write_u8(0xc003, 0); z80:write_u8(0xc004, 0)
    z80:write_u8(0xc006, 0); z80:write_u8(0xc007, 0x10); z80:write_u8(0xc008, 0)
    for a = 0xc009, 0xc00c do z80:write_u8(a, 0) end
    z80:write_u8(0xc00f, 0)
end
local function busy()
    for n = 0, 15 do if z80:read_u8(0xf200 + 0x40 * n + 0x34) ~= 0 then return true end end
    return false
end
local function send_row(r)
    z80:write_u8(0xc000, (r[2] >> 8) & 0xff); z80:write_u8(0xc001, r[2] & 0xff)
    z80:write_u8(0xc003, (r[2] >> 24) & 0xff); z80:write_u8(0xc004, (r[2] >> 16) & 0xff)
    z80:write_u8(0xc006, (r[3] >> 16) & 0xff); z80:write_u8(0xc007, (r[3] >> 8) & 0xff); z80:write_u8(0xc008, r[3] & 0xff)
    z80:write_u8(0xc009, (r[4] >> 8) & 0xff); z80:write_u8(0xc00a, r[4] & 0xff)
    z80:write_u8(0xc00b, (r[4] >> 24) & 0xff); z80:write_u8(0xc00c, (r[4] >> 16) & 0xff)
    z80:write_u8(0xc00f, 0)
end
local i, st, t, f = 0, "boot", 0, 0
local base
audio_frame = emu.add_machine_frame_notifier(function()
    f = f + 1
    z80:write_u8(0xcffe, 0xff)
    -- From here the 68000 can no longer hand a command over; its boot handshake with the Z80 is done by this frame.
    if f == 500 then audio_block = prog:install_write_tap(0x61801e, 0x61801f, "audio_block", function(_, data, mask) return data | 0xff end) end
    t = t + 1
    if #script > 0 then
        if f < 600 then return end
        if not base then base = f; out:write("base ", manager.machine.time:as_double(), string.char(10)); out:flush() end
        for _, r in ipairs(script) do if r[1] == f - base then send_row(r) end end
        if f - base > script[#script][1] + 300 then out:close(); manager.machine:exit() end
        return
    end
    if st == "boot" then
        if f >= 600 then st = "next"; t = 0 end
    elseif st == "next" then
        i = i + 1
        if i > #cmds then out:close(); manager.machine:exit(); return end
        send(cmds[i][1])
        out:write(string.format("%x\tS\t%.6f\n", cmds[i][1], manager.machine.time:as_double()))
        st = "play"; t = 0
    elseif st == "play" then
        local maxf = cmds[i][2]
        local sfx = maxf < 1000
        if (sfx and t > 4 and not busy()) or t >= maxf then
            out:write(string.format("%x\t%s\t%.6f\n", cmds[i][1], t >= maxf and "M" or "E", manager.machine.time:as_double()))
            out:flush()
            send(0xff00); st = "gap"; t = 0
        end
    elseif st == "gap" then
        if t >= 20 then st = "next"; t = 0 end
    end
end)
