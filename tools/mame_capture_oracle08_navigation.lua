-- ORACLE-08: Coffee Shop world-space navigation and boundary probe.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local cps_a = machine.memory.shares[":cps_a_regs"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local attack = in0["P1 Button 2"]
local root = assert(os.getenv("AVSP_ORACLE08_ROOT"))
local variant = os.getenv("AVSP_ORACLE08_VARIANT") or "baseline"
local valid = {baseline=true, up_hold=true, down_hold=true, left_hold=true,
    right_hold=true, up_right=true, down_right=true,
    right_hold_no_obstacle=true, up_hold_no_obstacle=true}
assert(valid[variant], "unsupported ORACLE-08 variant")
local first_frame, last_frame = 3400, 4700
local frame, player, obstacle = 0, 0xff8380, 0xffb380
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local writes = assert(io.open(root .. "/navigation_writes.tsv", "w"))
samples:write("frame\tvariant\tinput_word\tp_active\tp_state\tp_inner\tp_action\tp_facing\tp_x\tp_y\tp_z\tg8009\tbound_x\tbound_z\tscroll2_x\tscroll2_y\tob_active\tob_class\tob_type\tob_state\tob_x\tob_z\tob_hex\n")
writes:write("frame\tvariant\taddress\toffset\tdata\tmask\tpc\ta4\ta5\ta6\ta4_hex\tvalue\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function actor_hex(base)
    local out = {}
    for offset = 0, 0xbf do out[#out + 1] = string.format("%02x", u8(base + offset)) end
    return table.concat(out)
end
local function bytes_hex(base, count)
    local out = {}
    for offset = 0, count - 1 do
        out[#out + 1] = string.format("%02x", u8(base + offset))
    end
    return table.concat(out)
end
local function drive(field, on, bit, word)
    if on then field:set_value(1); return word | bit end
    field:clear_value(); return word
end

oracle08_taps = {}
for _, address in ipairs({player + 0x10, player + 0x12, player + 0x14,
                           player + 0x16, player + 0x18, player + 0x1a}) do
    local watched = address
    oracle08_taps[#oracle08_taps + 1] = program:install_write_tap(
        watched, watched + 1, string.format("oracle08_%06x", watched),
        function(offset, data, mask)
            if frame < first_frame or frame > last_frame then return end
            local a4 = maincpu.state["A4"].value & 0xffffff
            writes:write(string.format("%d\t%s\t%06x\t%02x\t%04x\t%04x\t%06x\t%06x\t%06x\t%06x\t%s\t%04x\n",
                frame, variant, watched, watched - player, data & 0xffff,
                mask & 0xffff, maincpu.state["PC"].value & 0xffffff,
                a4,
                maincpu.state["A5"].value & 0xffffff,
                maincpu.state["A6"].value & 0xffffff,
                bytes_hex(a4, 8), u16(watched)))
        end)
end

local function schedule(f)
    local word = 0
    local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
    local start_on = f >= 2405 and f < 2408
    local story_skip = f >= 2500 and f < 2505
    local select_confirm = f >= 3300 and f < 3305
    local l, r, u, d = false, f >= 3700 and f < 4200, false, false
    if f >= 4210 then
        l = variant == "left_hold"
        r = variant == "right_hold" or variant == "up_right" or
            variant == "down_right" or variant == "right_hold_no_obstacle"
        u = variant == "up_hold" or variant == "up_right" or
            variant == "up_hold_no_obstacle"
        d = variant == "down_hold" or variant == "down_right"
    end
    word = drive(coin, coin_on, 1, word)
    word = drive(start, start_on, 2, word)
    word = drive(left, l, 4, word)
    word = drive(right, r, 8, word)
    word = drive(attack, story_skip or select_confirm, 32, word)
    word = drive(up, u, 128, word)
    word = drive(down, d, 256, word)
    return word
end

local function remove_enemies()
    for index = 0, 19 do
        local base = 0xff9580 + index * 0xc0
        if u8(base) ~= 0 and u8(base + 2) == 0x1f then program:write_u8(base, 0) end
    end
end

oracle08_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local word = schedule(frame)
    if frame >= 3400 then program:write_u8(0xff83c1, 0x65) end
    if frame >= 4200 then remove_enemies() end
    if frame >= 4200 and (variant == "right_hold_no_obstacle" or
                         variant == "up_hold_no_obstacle") then
        program:write_u8(obstacle, 0)
    end
    if frame >= first_frame and frame <= last_frame then
        samples:write(table.concat({frame, variant, word, u8(player),
            u8(player + 4), u8(player + 5), u16(player + 6),
            u8(player + 0x0f), s16(u16(player + 0x10)),
            s16(u16(player + 0x14)), s16(u16(player + 0x18)),
            u8(0xff8009), s16(u16(0xff8278)), s16(u16(0xff827c)),
            cps_a:read_u16(16), cps_a:read_u16(18), u8(obstacle),
            u8(obstacle + 2), u8(obstacle + 8), u8(obstacle + 4),
            s16(u16(obstacle + 0x10)), s16(u16(obstacle + 0x18)),
            actor_hex(obstacle)}, "\t") .. "\n")
    end
    if frame == last_frame then
        coin:clear_value(); start:clear_value(); left:clear_value()
        right:clear_value(); up:clear_value(); down:clear_value(); attack:clear_value()
        samples:close(); writes:close(); machine:exit()
    end
end)
