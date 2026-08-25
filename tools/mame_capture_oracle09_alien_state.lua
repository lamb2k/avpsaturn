-- ORACLE-09: class-0x1f target/facing/state/presentation counterfactuals.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local opcodes = maincpu.spaces["opcodes"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun, attack, jump = in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"]
local root = assert(os.getenv("AVSP_ORACLE09_ROOT"))
local variant = os.getenv("AVSP_ORACLE09_VARIANT") or "baseline"
local valid = {baseline=true, left_static=true, right_static=true,
    above_static=true, below_static=true, cross_left_to_right=true,
    cross_right_to_left=true, move_during_attack=true,
    attack_during_approach=true, attack_during_attack=true,
    inside_range=true, outside_range=true}
assert(valid[variant], "unsupported ORACLE-09 variant")
local first_frame, last_frame = 3900, 4600
local frame, player, enemy, rng = 0, 0xff8380, 0xffa000, 0xff81a8
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local writes = assert(io.open(root .. "/enemy_writes.tsv", "w"))
local classes = assert(io.open(root .. "/class_entries.tsv", "w"))
local rng_calls = assert(io.open(root .. "/rng_calls.tsv", "w"))
samples:write("frame\tvariant\tinput_word\trng_word\tp_state\tp_action\tp_facing\tp_x\tp_y\tp_z\te_active\te_class\te_type\te_state\te_inner\te_action\te_phase\te_facing\te_x\te_y\te_z\te_anim\te_assembly\te_hurt\te_attack\te_timer\te_health\te_target\te_flags5d\te_hex\n")
writes:write("frame\tvariant\taddress\toffset\tdata\tmask\tpc\ta0\ta1\ta4\ta5\ta6\n")
classes:write("frame\tvariant\tsequence\tstate\tinner\taction\tfacing\tx\tz\tanim\tassembly\ttarget\n")
rng_calls:write("frame\tvariant\tsequence\tpc\ta6\tseed\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function bytes_hex(base, count)
    local out = {}
    for offset = 0, count - 1 do out[#out + 1] = string.format("%02x", u8(base + offset)) end
    return table.concat(out)
end
local function drive(field, on, bit, word)
    if on then field:set_value(1); return word | bit end
    field:clear_value(); return word
end

oracle09_write_tap = program:install_write_tap(
    enemy + 4, enemy + 0x5f, "oracle09_enemy_fields",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        writes:write(string.format("%d\t%s\t%06x\t%02x\t%04x\t%04x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\n",
            frame, variant, offset & 0xffffff, (offset - enemy) & 0xff,
            data & 0xffff, mask & 0xffff,
            maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A0"].value & 0xffffff,
            maincpu.state["A1"].value & 0xffffff,
            maincpu.state["A4"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff))
    end)

local class_sequence, rng_sequence = 0, 0
oracle09_class_tap = opcodes:install_read_tap(
    0x060532, 0x060533, "oracle09_class_entry",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        if (maincpu.state["A6"].value & 0xffffff) ~= enemy then return end
        class_sequence = class_sequence + 1
        local anim = u32(enemy + 0x1c)
        classes:write(string.format("%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%08x\t%08x\t%04x\n",
            frame, variant, class_sequence, u8(enemy + 4), u8(enemy + 5),
            u16(enemy + 6), u8(enemy + 0x0f), s16(u16(enemy + 0x10)),
            s16(u16(enemy + 0x18)), anim,
            anim ~= 0 and u32(anim + 4) or 0, u16(enemy + 0x28)))
    end)
oracle09_rng_tap = opcodes:install_read_tap(
    0x017c5e, 0x017c5f, "oracle09_rng_entry",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        if (maincpu.state["A6"].value & 0xffffff) ~= enemy then return end
        rng_sequence = rng_sequence + 1
        rng_calls:write(string.format("%d\t%s\t%d\t%06x\t%06x\t%04x\n",
            frame, variant, rng_sequence,
            maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff, u16(rng)))
    end)

local function schedule(f)
    local word = 0
    local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
    local start_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
    local gun_on = (f >= 1500 and f < 4200 and f % 90 < 5) or
        (f >= 2600 and f < 4200 and f % 75 < 6)
    local right_on = f >= 2600 and f < 4200
    local left_on = f >= 4201 and f < 4210
    local up_on, down_on = false, false
    local attack_on = f >= 2600 and f < 4200 and f % 310 < 7
    local jump_on = f >= 2600 and f < 4200 and f % 430 < 7
    if f >= 4420 and f <= 4600 then attack_on = (f - 4420) % 45 < 5 end
    if variant == "move_during_attack" and f >= 4253 and f <= 4372 then
        left_on = (f % 40) < 10
        right_on = (f % 40) >= 20 and (f % 40) < 30
        up_on = (f % 40) >= 10 and (f % 40) < 20
        down_on = (f % 40) >= 30
    end
    if variant == "attack_during_approach" and f >= 4050 and f < 4055 then attack_on = true end
    if variant == "attack_during_attack" and f >= 4300 and f < 4305 then attack_on = true end
    word = drive(coin, coin_on, 1, word)
    word = drive(start, start_on, 2, word)
    word = drive(left, left_on, 4, word)
    word = drive(right, right_on, 8, word)
    word = drive(gun, gun_on, 16, word)
    word = drive(attack, attack_on, 32, word)
    word = drive(jump, jump_on, 64, word)
    word = drive(up, up_on, 128, word)
    word = drive(down, down_on, 256, word)
    return word
end

local function hold_player(f)
    if f < 3975 or f > 4375 then return end
    local x, z = nil, nil
    if variant == "left_static" then x, z = 800, 319 end
    if variant == "right_static" then x, z = 1500, 319 end
    if variant == "above_static" then x, z = 1300, 400 end
    if variant == "below_static" then x, z = 1300, 220 end
    if variant == "cross_left_to_right" then x, z = f <= 4100 and 800 or 1500, 319 end
    if variant == "cross_right_to_left" then x, z = f <= 4100 and 1500 or 800, 319 end
    if variant == "inside_range" then x, z = 1000, 343 end
    if variant == "outside_range" then x, z = 1800, 400 end
    if x then
        program:write_u16(player + 0x10, x)
        program:write_u16(player + 0x14, z)
        program:write_u16(player + 0x18, z)
    end
end

oracle09_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local word = schedule(frame)
    hold_player(frame)
    if frame >= 3900 then program:write_u8(player + 0x41, 0x65) end
    if frame >= first_frame and frame <= last_frame then
        local anim = u32(enemy + 0x1c)
        samples:write(table.concat({frame, variant, word,
            string.format("%04x", u16(rng)), u8(player + 4), u16(player + 6),
            u8(player + 0x0f), s16(u16(player + 0x10)),
            s16(u16(player + 0x14)), s16(u16(player + 0x18)),
            u8(enemy), u8(enemy + 2), u8(enemy + 8), u8(enemy + 4),
            u8(enemy + 5), u16(enemy + 6), u8(enemy + 7), u8(enemy + 0x0f),
            s16(u16(enemy + 0x10)), s16(u16(enemy + 0x14)),
            s16(u16(enemy + 0x18)), string.format("%08x", anim),
            string.format("%08x", anim ~= 0 and u32(anim + 4) or 0),
            anim ~= 0 and u8(anim + 8) or 0,
            anim ~= 0 and u8(anim + 9) or 0, u8(enemy + 0x2a),
            s16(u16(enemy + 0x40)), u16(enemy + 0x28), u8(enemy + 0x5d),
            bytes_hex(enemy, 0xc0)}, "\t") .. "\n")
    end
    if frame == last_frame then
        coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
        up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value(); jump:clear_value()
        samples:close(); writes:close(); classes:close(); rng_calls:close(); machine:exit()
    end
end)
