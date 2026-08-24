-- ORACLE-04 bounded Predator Warrior directional-control capture.
-- Raw ledgers and frames stay private under .deps/mame/oracle04_controls/.
local machine = manager.machine
local screen = machine.screens[":screen"]
local program = machine.devices[":maincpu"].spaces["program"]
local root = assert(os.getenv("AVSP_ORACLE04_ROOT"),
    "AVSP_ORACLE04_ROOT is required")
local perturb_frame = tonumber(os.getenv("AVSP_ORACLE04_PERTURB_FRAME") or "0")

local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local left = in0["P1 Left"]
local right = in0["P1 Right"]
local up = in0["P1 Up"]
local down = in0["P1 Down"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]

local first_frame = 2500
local last_frame = 2760
local frame = 0
local samples = assert(io.open(root .. "/samples.tsv", "w"))
samples:write("frame\tinput_word\tp_state\tp_class\tp_sub\tp_action\tp_type",
    "\tp_facing\tp_x\tp_y\tp_z\tp_anim\tp_timer\tp_health\tp_hit",
    "\tp_source\tp_hurt\tp_attack\n")

local function u16(address) return program:read_u16(address) end
local function u32(address) return program:read_u32(address) end
local function s16(value) return value >= 0x8000 and value - 0x10000 or value end

local function clear_inputs()
    coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
    up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value()
    jump:clear_value()
end

local function apply_schedule(f)
    local word = 0
    local function drive(field, enabled, bit)
        if enabled then field:set_value(1); word = word | bit
        else field:clear_value() end
    end
    local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
    local start_on = f >= 1200 and f <= 2400 and
        (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
    local gun_on = f >= 1500 and f <= 1895 and f % 90 < 5
    local right_on = f >= 2525 and f <= 2544
    local left_on = f >= 2585 and f <= 2604
    local up_on = f >= 2645 and f <= 2664
    local down_on = f >= 2705 and f <= 2724
    if f == perturb_frame then right_on = false end
    drive(coin, coin_on, 1); drive(start, start_on, 2)
    drive(left, left_on, 4); drive(right, right_on, 8)
    drive(gun, gun_on, 16); drive(attack, false, 32); drive(jump, false, 64)
    drive(up, up_on, 128); drive(down, down_on, 256)
    return word
end

local function capture(input_word)
    local base = 0xff8380
    local anim = u32(base + 0x1c)
    local row = {
        frame, input_word, program:read_u8(base + 0x00),
        program:read_u8(base + 0x02), u16(base + 0x04), u16(base + 0x06),
        program:read_u8(base + 0x08), program:read_u8(base + 0x0f),
        s16(u16(base + 0x10)), s16(u16(base + 0x14)), s16(u16(base + 0x18)),
        string.format("%08x", anim), u16(base + 0x2a),
        s16(u16(base + 0x40)), program:read_u8(base + 0x2c),
        program:read_u8(base + 0x2d),
        anim ~= 0 and program:read_u8(anim + 8) or 0,
        anim ~= 0 and program:read_u8(anim + 9) or 0,
    }
    samples:write(table.concat(row, "\t") .. "\n")
    screen:snapshot(string.format(root .. "/frames/%05d.png", frame))
end

oracle04_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = apply_schedule(frame)
    if frame >= first_frame and frame <= last_frame then capture(input_word) end
    if frame == last_frame then
        clear_inputs(); samples:close(); machine:exit()
    end
end)
