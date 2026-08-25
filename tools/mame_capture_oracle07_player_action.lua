-- ORACLE-07: Predator Warrior action graph, input-edge, and equipment probe.
-- Raw source observations remain private under .deps/mame/oracle07_*.
-- The only memory mutation is the previously declared player-health survival
-- guard used by the accepted vertical-slice route.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local screen = machine.screens[":screen"]
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

local root = assert(os.getenv("AVSP_ORACLE07_ROOT"))
local variant = os.getenv("AVSP_ORACLE07_VARIANT") or "baseline"
local allowed = {
    baseline=true, single_attack=true, long_idle=true,
    delayed_second_60=true, delayed_second_120=true, hold_attack=true,
    startup_repeat=true, recovery_repeat=true, movement_attack=true,
    reverse_attack=true, gun_only=true, special_only=true,
    hit_overlap=true, no_gameplay_buttons=true,
    isolated_combo_48=true, isolated_combo_49=true,
    close_combo_delay_50=true, close_combo_delay_51=true,
    close_combo_hold=true, close_combo_startup_repeat=true,
    close_combo_recovery_repeat=true,
    jump_only=true, dash_right=true,
    air_cold=true,
    isolated_dash_right=true, isolated_dash_left=true,
    isolated_dash_up=true, isolated_dash_down=true,
    air_button2_neutral=true, air_button2_right=true,
    air_button2_left=true, air_button2_up=true,
    air_button2_down=true, air_button2_hold=true,
    air_button2_followup_4436=true, air_button2_followup_4442=true,
    air_button2_followup_4449=true, air_button2_followup_4454=true,
    air_button2_midair_down=true,
    air_button2_midair_down_followup_4440=true,
    air_button2_midair_down_followup_4448=true,
    dash_right_jump_reverse=true,
    air_button1_resource=true,
    air_button3_repeat=true, air_button1=true,
    air_special_combo=true,
}
assert(allowed[variant], "unsupported ORACLE-07 variant: " .. variant)

local first_frame = 2400
local last_frame = 5469
local player_base = 0xff8380
local player_last = player_base + 0xbf
local player_header = 0xff8300
local actor_first = 0xff9580
local actor_count = 20
local actor_stride = 0xc0
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local writes = assert(io.open(root .. "/player_writes.tsv", "w"))
local global_writes = assert(io.open(root .. "/player_global_writes.tsv", "w"))
local frame = 0
local write_sequence = 0

local function u8(address) return program:read_u8(address) end
local function u16(address) return program:read_u16(address) end
local function u32(address) return program:read_u32(address) end
local function s16(value) return value >= 0x8000 and value - 0x10000 or value end

local function actor_hex()
    local chunks = {}
    for offset = 0, 0xbf do
        chunks[#chunks + 1] = string.format("%02x", u8(player_base + offset))
    end
    return table.concat(chunks)
end

local function player_header_hex()
    local chunks = {}
    for offset = 0, 0x7f do
        chunks[#chunks + 1] = string.format("%02x", u8(player_header + offset))
    end
    return table.concat(chunks)
end

samples:write(
    "frame\tvariant\tinput_word\tp_active\tp_class\tp_state\tp_inner",
    "\tp_action\tp_phase\tp_type\tp_facing\tp_x\tp_y\tp_z\tp_anim",
    "\tp_timer\tp_hit\tp_source\tp_health\tp_latched_health\tp_hurt",
    "\tp_attack\tactor_hex\tplayer_header_hex\n")
writes:write(
    "frame\tvariant\tsequence\taddress\toffset\tdata\tmask\tpc",
    "\ta5\ta6\tvalue\n")
global_writes:write(
    "frame\tvariant\taddress\toffset\tdata\tmask\tpc\ta5\ta6\tvalue\n")

-- Capture every source instruction site that mutates the player actor. This
-- binds observed state transitions to executable writers rather than visuals.
oracle07_player_write_tap = program:install_write_tap(
    player_base, player_last, "oracle07_player_actor_writes",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        write_sequence = write_sequence + 1
        writes:write(string.format(
            "%d\t%s\t%d\t%06x\t%02x\t%04x\t%04x\t%06x\t%06x\t%06x\t%08x\n",
            frame, variant, write_sequence, offset & 0xffffff,
            (offset - player_base) & 0xff, data & 0xffff, mask & 0xffff,
            maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff,
            u32(offset & 0xfffffe)))
    end)

oracle07_player_global_write_tap = program:install_write_tap(
    player_header, player_header + 0x7f, "oracle07_player_global_writes",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        global_writes:write(string.format(
            "%d\t%s\t%06x\t%02x\t%04x\t%04x\t%06x\t%06x\t%06x\t%08x\n",
            frame, variant, offset & 0xffffff,
            (offset - player_header) & 0xff, data & 0xffff, mask & 0xffff,
            maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff,
            u32(offset & 0xfffffe)))
    end)

local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
end

local function pulse(f, first, duration)
    return f >= first and f < first + duration
end

local function apply_schedule(f)
    local word = 0
    local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
    local start_on = f >= 1200 and f <= 2400 and
        (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
    local gun_on = (f >= 1500 and f < 4200 and f % 90 < 5) or
        (f >= 2600 and f < 4200 and f % 75 < 6)
    local right_on = f >= 2600 and f < 4200
    local attack_on = f >= 2600 and f < 4200 and f % 310 < 7
    local jump_on = f >= 2600 and f < 4200 and f % 430 < 7
    local left_on = f >= 4201 and f < 4210
    local up_on = false
    local down_on = false

    -- Default accepted combat tail: four five-frame Button-2 pulses, 45
    -- frames apart. Variants replace only the declared tail inputs.
    if f >= 4420 then
        gun_on = false; jump_on = false; right_on = false; left_on = false
        attack_on = f <= 5469 and (f - 4420) % 45 < 5
    end
    if variant == "single_attack" and f >= 4420 then
        attack_on = pulse(f, 4420, 5)
    elseif variant == "long_idle" and f >= 4420 then
        attack_on = pulse(f, 5185, 5)
    elseif variant == "delayed_second_60" and f >= 4420 then
        attack_on = pulse(f, 4420, 5) or pulse(f, 4480, 5)
    elseif variant == "delayed_second_120" and f >= 4420 then
        attack_on = pulse(f, 4420, 5) or pulse(f, 4540, 5)
    elseif variant == "hold_attack" and f >= 4420 then
        attack_on = f >= 4420 and f < 4461
    elseif variant == "startup_repeat" and f >= 4420 then
        attack_on = pulse(f, 4420, 5) or pulse(f, 4428, 5)
    elseif variant == "recovery_repeat" and f >= 4420 then
        attack_on = pulse(f, 4420, 5) or pulse(f, 4450, 5)
    elseif variant == "movement_attack" and f >= 4420 then
        attack_on = pulse(f, 4420, 5); right_on = f >= 4412 and f < 4460
    elseif variant == "reverse_attack" and f >= 4420 then
        attack_on = pulse(f, 4420, 5) or pulse(f, 4465, 5)
        left_on = f >= 4412 and f < 4440
        right_on = f >= 4440 and f < 4490
    elseif variant == "gun_only" and f >= 4420 then
        attack_on = false; gun_on = pulse(f, 4420, 5)
    elseif variant == "special_only" and f >= 4420 then
        attack_on = pulse(f, 4420, 5); gun_on = pulse(f, 4420, 5)
    elseif variant == "hit_overlap" and f >= 4200 then
        attack_on = pulse(f, 4298, 5)
        gun_on = false; jump_on = false; right_on = false; left_on = false
    elseif variant == "no_gameplay_buttons" and f >= 4200 then
        attack_on = false; gun_on = false; jump_on = false
        right_on = false; left_on = false
    elseif variant == "jump_only" and f >= 4420 then
        attack_on = false; gun_on = false; right_on = false; left_on = false
        jump_on = pulse(f, 4420, 5)
    elseif variant == "dash_right" and f >= 4420 then
        attack_on = false; gun_on = false; left_on = false
        jump_on = pulse(f, 4420, 5); right_on = f >= 4412 and f < 4470
    elseif (variant == "air_cold" or
            variant == "air_button2_neutral" or
            variant == "air_button2_hold" or
            variant:match("^air_button2_followup_") or
            variant:match("^air_button2_midair_down") or
            variant == "air_button3_repeat" or
            variant == "air_button1" or
            variant == "air_special_combo") and f >= 4420 then
        attack_on = false; gun_on = false; jump_on = pulse(f, 4420, 5)
        right_on = false; left_on = false
        if variant == "air_button2_neutral" then
            attack_on = pulse(f, 4430, 5)
        elseif variant == "air_button2_hold" then
            attack_on = f >= 4430 and f < 4460
        elseif variant:match("^air_button2_followup_") then
            local second = tonumber(variant:match("(%d+)$"))
            attack_on = pulse(f, 4430, 5) or pulse(f, second, 5)
        elseif variant:match("^air_button2_midair_down") then
            down_on = f >= 4428 and f < 4470
            attack_on = pulse(f, 4430, 5)
            local second = tonumber(variant:match("followup_(%d+)$"))
            if second then attack_on = attack_on or pulse(f, second, 5) end
        elseif variant == "air_button3_repeat" then
            jump_on = jump_on or pulse(f, 4430, 5)
        elseif variant == "air_button1" then
            gun_on = pulse(f, 4430, 5)
        elseif variant == "air_special_combo" then
            gun_on = pulse(f, 4430, 5); attack_on = pulse(f, 4430, 5)
        end
    elseif (variant == "isolated_dash_right" or
            variant == "isolated_dash_left" or
            variant == "isolated_dash_up" or
            variant == "isolated_dash_down" or
            variant == "air_button2_right" or
            variant == "air_button2_left" or
            variant == "air_button2_up" or
            variant == "air_button2_down") and f >= 4420 then
        attack_on = false; gun_on = false; jump_on = pulse(f, 4420, 5)
        right_on = false; left_on = false; up_on = false; down_on = false
        if variant:match("right$") then right_on = f >= 4412 and f < 4470 end
        if variant:match("left$") then left_on = f >= 4412 and f < 4470 end
        if variant:match("up$") then up_on = f >= 4412 and f < 4470 end
        if variant:match("down$") then down_on = f >= 4412 and f < 4470 end
        if variant:match("^air_button2_") then
            attack_on = pulse(f, 4430, 5)
        end
    elseif variant == "dash_right_jump_reverse" and f >= 4420 then
        attack_on = false; gun_on = false; left_on = false
        right_on = f >= 4412 and f < 4470
        jump_on = pulse(f, 4420, 5) or pulse(f, 4430, 5)
    elseif variant == "air_button1_resource" and f >= 4420 then
        attack_on = false; gun_on = pulse(f, 4695, 5)
        left_on = false; right_on = f >= 4672 and f < 4730
        jump_on = pulse(f, 4680, 5)
    elseif variant == "isolated_combo_48" and f >= 4420 then
        attack_on = pulse(f, 4420, 5) or pulse(f, 4468, 5)
        gun_on = false; jump_on = false; right_on = false; left_on = false
    elseif variant == "isolated_combo_49" and f >= 4420 then
        attack_on = pulse(f, 4420, 5) or pulse(f, 4469, 5)
        gun_on = false; jump_on = false; right_on = false; left_on = false
    end
    if f >= 5185 then
        if variant == "close_combo_delay_50" then
            attack_on = pulse(f, 5185, 5) or pulse(f, 5235, 5)
        elseif variant == "close_combo_delay_51" then
            attack_on = pulse(f, 5185, 5) or pulse(f, 5236, 5)
        elseif variant == "close_combo_hold" then
            attack_on = f >= 5185 and f < 5245
        elseif variant == "close_combo_startup_repeat" then
            attack_on = pulse(f, 5185, 5) or pulse(f, 5193, 5)
        elseif variant == "close_combo_recovery_repeat" then
            attack_on = pulse(f, 5185, 5) or pulse(f, 5208, 5)
        end
    end

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

local witnesses = {
    [2400]=true, [4200]=true, [4298]=true, [4301]=true, [4373]=true,
    [4419]=true, [4420]=true, [4422]=true, [4424]=true, [4428]=true,
    [4450]=true, [4465]=true, [4480]=true, [4540]=true, [5185]=true,
    [5190]=true, [5236]=true, [5283]=true, [5329]=true, [5469]=true,
}

local function capture(input_word)
    local anim = u32(player_base + 0x1c)
    samples:write(table.concat({
        frame, variant, input_word, u8(player_base), u8(player_base + 2),
        u8(player_base + 4), u8(player_base + 5), u16(player_base + 6),
        u8(player_base + 7), u8(player_base + 8), u8(player_base + 0x0f),
        s16(u16(player_base + 0x10)), s16(u16(player_base + 0x14)),
        s16(u16(player_base + 0x18)), string.format("%08x", anim),
        u16(player_base + 0x2a), u8(player_base + 0x2c),
        u8(player_base + 0x2d), s16(u16(player_base + 0x40)),
        s16(u16(player_base + 0x42)),
        anim ~= 0 and u8(anim + 8) or 0,
        anim ~= 0 and u8(anim + 9) or 0,
        actor_hex(),
        player_header_hex(),
    }, "\t") .. "\n")
    if witnesses[frame] then
        screen:snapshot(string.format(root .. "/frames/%05d.png", frame))
    end
end

oracle07_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = apply_schedule(frame)
    if variant == "isolated_combo_48" or variant == "isolated_combo_49" or
            variant == "air_cold" or variant:match("^isolated_dash_") or
            variant:match("^air_button") or variant == "air_special_combo" or
            variant == "dash_right_jump_reverse" then
        -- Declared player-controller counterfactual: remove active class-0x1f
        -- enemies after the common route so no HIT state masks the reset edge.
        if frame >= 4200 then
            for index = 0, actor_count - 1 do
                local base = actor_first + index * actor_stride
                if u8(base) ~= 0 and u8(base + 2) == 0x1f then
                    program:write_u8(base, 0)
                end
            end
        end
    end
    if variant == "air_button1_resource" and frame >= 4670 and frame < 4695 then
        program:write_u8(player_base + 0x8c, 0x40)
    end
    if frame >= 4200 then program:write_u8(0xff83c1, 0x65) end
    if frame >= first_frame and frame <= last_frame then capture(input_word) end
    if frame == last_frame then
        coin:clear_value(); start:clear_value(); left:clear_value()
        right:clear_value(); up:clear_value(); down:clear_value()
        gun:clear_value(); attack:clear_value(); jump:clear_value()
        samples:close(); writes:close(); global_writes:close(); machine:exit()
    end
end)
