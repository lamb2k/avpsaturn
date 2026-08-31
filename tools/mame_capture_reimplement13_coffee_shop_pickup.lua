-- Small REIMPLEMENT-13 corrective Oracle for the natural Coffee Shop
-- record28/class-0x0a health pickup. Raw ledgers stay private in .deps/mame.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local root = assert(os.getenv("AVSP_REIMPLEMENT13_PICKUP_ROOT"))
local variant = assert(os.getenv("AVSP_REIMPLEMENT13_PICKUP_VARIANT"))
assert(variant == "baseline" or variant == "pickup_suppressed",
       "unsupported pickup capture variant: " .. variant)

local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]

local player = 0xff8380
local record28, record28_count, record28_stride = 0xffc680, 16, 0x80
local pickup = 0xffcd00
local first_frame, last_frame = 2600, 3120
local frame, sequence, mutation_active = 0, 0, false
local writes = assert(io.open(root .. "/record28_writes.tsv", "w"))
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local spawn_guard = assert(io.open(root .. "/source_spawn_guard.tsv", "w"))
writes:write("frame\tvariant\tsequence\taddress\toffset\tdata\tmask\tpc\ta4\ta5\ta6\n")
samples:write("frame\tvariant\tinput\tplayer_state\tplayer_action\tplayer_health\tplayer_latched\tplayer_target\tpickup_active\tpickup_class\tpickup_subtype\tpickup_state\tpickup_substate\tpickup_x\tpickup_y\tpickup_z\tpickup_vx\tpickup_vy\tpickup_vz\tpickup_ay\tpickup_anim\tpickup_anim_timer\tpickup_field5c\n")
spawn_guard:write("frame\tvariant\tpc\ta1\ta4\ta5\ta6\trecord_gate\trecord_x\trecord_y\trecord_type\trecord_arg\trecord_lane_guard\trecord_character_guard\tglobal_gate\tglobal_lane_limit\tglobal_character\tcamera_x\tplayer_x\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
end
pickup_corrective_tap = program:install_write_tap(
    0xff0000, 0xffffff,
    "reimplement13_pickup_record28",
    function(offset, data, mask)
        if mutation_active or frame < first_frame or frame > last_frame then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        if offset == 0xffb200 and pc == 0x01bf1e then
            local a1 = maincpu.state["A1"].value & 0xffffff
            local a4 = maincpu.state["A4"].value & 0xffffff
            local a5 = maincpu.state["A5"].value & 0xffffff
            local a6 = maincpu.state["A6"].value & 0xffffff
            spawn_guard:write(string.format(
                "%d\t%s\t%06x\t%06x\t%06x\t%06x\t%06x"
                .. "\t%04x\t%04x\t%04x\t%04x\t%04x\t%02x\t%02x"
                .. "\t%04x\t%02x\t%02x\t%04x\t%04x\n",
                frame, variant, pc, a1, a4, a5, a6,
                u16(a1), u16(a1 + 2), u16(a1 + 4), u16(a1 + 6),
                u16(a1 + 8), u8(a1 + 10), u8(a1 + 11),
                u16(a5 + 0x278), u8(a5 + 0x1eb), u8(a5 + 0x20e),
                u16(a5 + 0x278), u16(player + 0x10)))
        end
        if offset < pickup or offset > pickup + 0x7f then return end
        sequence = sequence + 1
        writes:write(string.format(
            "%d\t%s\t%d\t%06x\t%02x\t%04x\t%04x\t%06x\t%06x\t%06x\t%06x\n",
            frame, variant, sequence, offset & 0xffffff,
            (offset - pickup) & 0xff, data & 0xffff, mask & 0xffff,
            pc,
            maincpu.state["A4"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff))
    end)

local function schedule(f)
    local word = 0
    local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
    local start_on = f >= 1200 and f <= 2400 and
        (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
    local gun_on = (f >= 1500 and f < 4200 and f % 90 < 5) or
        (f >= 2600 and f < 4200 and f % 75 < 6)
    local right_on = f >= 2600 and f < 4200
    local attack_on = f >= 2600 and f < 4200 and f % 310 < 7
    local jump_on = f >= 2600 and f < 4200 and f % 430 < 7
    word = drive(coin, coin_on, 1, word)
    word = drive(start, start_on, 2, word)
    word = drive(left, false, 4, word)
    word = drive(right, right_on, 8, word)
    word = drive(gun, gun_on, 16, word)
    word = drive(attack, attack_on, 32, word)
    word = drive(jump, jump_on, 64, word)
    word = drive(up, false, 128, word)
    word = drive(down, false, 256, word)
    return word
end

local function suppress_pickup()
    if variant == "pickup_suppressed" and frame >= 2907 and u8(pickup) ~= 0 then
        mutation_active = true
        program:write_u8(pickup, 0)
        mutation_active = false
    end
end

local function capture(input_word)
    samples:write(string.format(
        "%d\t%s\t%d\t%04x\t%04x\t%d\t%d\t%04x"
        .. "\t%d\t%02x\t%02x\t%04x\t%04x"
        .. "\t%08x\t%08x\t%d\t%08x\t%08x\t%08x\t%08x"
        .. "\t%08x\t%04x\t%02x\n",
        frame, variant, input_word, u16(player + 4), u16(player + 6),
        u16(player + 0x40), u16(player + 0x42), u16(player + 0x8e),
        u8(pickup), u8(pickup + 2), u8(pickup + 3),
        u16(pickup + 4), u16(pickup + 6),
        u32(pickup + 0x10), u32(pickup + 0x14), u16(pickup + 0x18),
        u32(pickup + 0x30), u32(pickup + 0x34),
        u32(pickup + 0x38), u32(pickup + 0x3c),
        u32(pickup + 0x1c), u16(pickup + 0x20), u8(pickup + 0x5c)))
end

pickup_corrective_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = schedule(frame)
    suppress_pickup()
    if frame >= first_frame and frame <= last_frame then capture(input_word) end
    if frame == last_frame then
        coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
        up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value(); jump:clear_value()
        writes:close(); samples:close(); spawn_guard:close(); machine:exit()
    end
end)
