-- ORACLE-11 full-route player audio/load ownership ledger.
-- No screenshots or region dumps; raw ledgers remain private under .deps/mame.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local root = assert(os.getenv("AVSP_ORACLE11_PLAYER_EVENTS_ROOT"))
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun, attack, jump = in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"]
local player, frame, final_frame = 0xff8380, 0, 18000
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local audio = assert(io.open(root .. "/audio_writes.tsv", "w"))
local gfx = assert(io.open(root .. "/gfx_writes.tsv", "w"))
samples:write("frame\tinput\tglobal_state\tactive\tstate\taction\thealth\tresource\trecharge\tdepleted\taward\n")
audio:write("frame\taddress\tdata\tmask\tpc\ta5\ta6\td0\td1\td2\tsp\tstack0\n")
gfx:write("frame\taddress\tdata\tmask\tpc\ta5\ta6\n")
local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
end
local function load_window(f)
    return (f >= 5530 and f <= 5580) or (f >= 6170 and f <= 6230) or
        (f >= 12770 and f <= 12830)
end
oracle11_player_events_audio = program:install_write_tap(
    0x618000, 0x619fff, "oracle11_player_events_audio", function(offset, data, mask)
        if frame < 1970 then return end
        local sp = maincpu.state["A7"].value & 0xffffff
        audio:write(string.format("%d\t%06x\t%04x\t%04x\t%06x\t%06x\t%06x\t%08x\t%08x\t%08x\t%06x\t%08x\n",
            frame, offset & 0xffffff, data & 0xffff, mask & 0xffff,
            maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff,
            maincpu.state["D0"].value & 0xffffffff,
            maincpu.state["D1"].value & 0xffffffff,
            maincpu.state["D2"].value & 0xffffffff, sp, u32(sp)))
    end)
oracle11_player_events_gfx = program:install_write_tap(
    0x900000, 0x92ffff, "oracle11_player_events_gfx", function(offset, data, mask)
        if not load_window(frame) then return end
        gfx:write(string.format("%d\t%06x\t%04x\t%04x\t%06x\t%06x\t%06x\n",
            frame, offset & 0xffffff, data & 0xffff, mask & 0xffff,
            maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff))
    end)

local function schedule(f)
    local word = 0
    if f <= 4200 then
        local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
        local start_on = f >= 1200 and f <= 2400 and
            (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
        local gun_on = (f >= 1500 and f < 4200 and f % 90 < 5) or
            (f >= 2600 and f < 4200 and f % 75 < 6)
        word = drive(coin, coin_on, 1, word)
        word = drive(start, start_on, 2, word)
        word = drive(right, f >= 2600 and f < 4200, 8, word)
        word = drive(gun, gun_on, 16, word)
        word = drive(attack, f >= 2600 and f < 4200 and f % 310 < 7, 32, word)
        word = drive(jump, f >= 2600 and f < 4200 and f % 430 < 7, 64, word)
    else
        local r = f - 4200
        word = drive(coin, r % 600 >= 30 and r % 600 < 34, 1, word)
        word = drive(start, r % 600 >= 90 and r % 600 < 94, 2, word)
        word = drive(right, true, 8, word)
        word = drive(gun, r % 45 < 7, 16, word)
        word = drive(attack, r % 180 < 8, 32, word)
        word = drive(jump, r % 240 < 8, 64, word)
    end
    word = drive(left, false, 4, word)
    word = drive(up, false, 128, word)
    word = drive(down, false, 256, word)
    return word
end
oracle11_player_events_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = schedule(frame)
    if frame >= 1970 then
        samples:write(table.concat({frame, input_word, u8(0xff8009), u8(player),
            u16(player + 4), u16(player + 6), s16(u16(player + 0x40)),
            u8(player + 0x8c), u8(player + 0x8d), u8(player + 0x8b),
            u16(player + 0xae)}, "\t") .. "\n")
    end
    if frame == final_frame then
        coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
        up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value(); jump:clear_value()
        samples:close(); audio:close(); gfx:close(); machine:exit()
    end
end)
