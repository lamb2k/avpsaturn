-- ORACLE-11: Predator Warrior HIT/KO/failure/continue/respawn source probe.
-- Raw source observations remain private under .deps/mame/oracle11_*.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local screen = machine.screens[":screen"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun, attack, jump = in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"]

local root = assert(os.getenv("AVSP_ORACLE11_HITKO_ROOT"))
local variant = assert(os.getenv("AVSP_ORACLE11_HITKO_VARIANT"))
local valid = {
    baseline_hitko=true, no_continue=true, coin_only=true, start_only=true,
    delayed_start=true, survive_contact=true, respawn_input_suppressed=true,
    continue_confirm_gun=true, continue_confirm_attack=true,
    continue_confirm_jump=true, continue_confirm_right=true,
}
assert(valid[variant], "unsupported ORACLE-11 HIT/KO variant: " .. variant)

local first_frame, last_frame = 5800, 6900
local player, player_header = 0xff8380, 0xff8300
local frame, write_sequence, mutation_active = 0, 0, false
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local player_writes = assert(io.open(root .. "/player_writes.tsv", "w"))
local global_writes = assert(io.open(root .. "/global_writes.tsv", "w"))
local qsound_writes = assert(io.open(root .. "/qsound_writes.tsv", "w"))
samples:write(
    "frame\tvariant\tinput_word\tg8009\tp_active\tp_state\tp_inner",
    "\tp_action\tp_phase\tp_facing\tp_x\tp_y\tp_z\tp_anim\tp_timer",
    "\tp_health\tp_latched_health\tp_hit_timer\tp_invuln\tactor_hex",
    "\tplayer_header_hex\n")
player_writes:write(
    "frame\tvariant\tsequence\taddress\toffset\tdata\tmask\tpc",
    "\ta5\ta6\tvalue\n")
global_writes:write(
    "frame\tvariant\taddress\toffset\tdata\tmask\tpc\ta5\ta6\tvalue\n")
qsound_writes:write(
    "frame\tvariant\taddress\tdata\tmask\tpc\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function bytes_hex(base, count)
    local chunks = {}
    for offset = 0, count - 1 do
        chunks[#chunks + 1] = string.format("%02x", u8(base + offset))
    end
    return table.concat(chunks)
end
local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
end

oracle11_hitko_player_tap = program:install_write_tap(
    player, player + 0xbf, "oracle11_hitko_player_writes",
    function(offset, data, mask)
        if mutation_active or frame < first_frame or frame > last_frame then return end
        write_sequence = write_sequence + 1
        player_writes:write(string.format(
            "%d\t%s\t%d\t%06x\t%02x\t%04x\t%04x\t%06x\t%06x\t%06x\t%08x\n",
            frame, variant, write_sequence, offset & 0xffffff,
            (offset - player) & 0xff, data & 0xffff, mask & 0xffff,
            maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff,
            u32(offset & 0xfffffe)))
    end)

oracle11_hitko_global_tap = program:install_write_tap(
    0xff8000, player - 1, "oracle11_hitko_global_writes",
    function(offset, data, mask)
        if mutation_active or frame < first_frame or frame > last_frame then return end
        global_writes:write(string.format(
            "%d\t%s\t%06x\t%04x\t%04x\t%04x\t%06x\t%06x\t%06x\t%08x\n",
            frame, variant, offset & 0xffffff,
            (offset - 0xff8000) & 0xffff, data & 0xffff, mask & 0xffff,
            maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff,
            u32(offset & 0xfffffe)))
    end)

oracle11_hitko_qsound_tap = program:install_write_tap(
    0x618000, 0x619fff, "oracle11_hitko_qsound_writes",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        qsound_writes:write(string.format("%d\t%s\t%06x\t%04x\t%04x\t%06x\n",
            frame, variant, offset & 0xffffff, data & 0xffff, mask & 0xffff,
            maincpu.state["PC"].value & 0xffffff))
    end)

local function schedule(f)
    local word = 0
    local coin_on, start_on, left_on, right_on = false, false, false, false
    local up_on, down_on, gun_on, attack_on, jump_on = false, false, false, false, false
    if f <= 4200 then
        coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
        start_on = f >= 1200 and f <= 2400 and
            (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
        gun_on = (f >= 1500 and f < 4200 and f % 90 < 5) or
            (f >= 2600 and f < 4200 and f % 75 < 6)
        right_on = f >= 2600 and f < 4200
        attack_on = f >= 2600 and f < 4200 and f % 310 < 7
        jump_on = f >= 2600 and f < 4200 and f % 430 < 7
    else
        local r = f - 4200
        coin_on = r % 600 >= 30 and r % 600 < 34
        start_on = r % 600 >= 90 and r % 600 < 94
        right_on = true
        gun_on = r % 45 < 7
        attack_on = r % 180 < 8
        jump_on = r % 240 < 8
    end
    if variant == "no_continue" and f >= 5600 then
        coin_on, start_on = false, false
    elseif variant == "coin_only" and f >= 5600 then
        start_on = false
    elseif variant == "start_only" and f >= 5600 then
        coin_on = false
    elseif variant == "delayed_start" and f >= 6600 and f < 6750 then
        start_on = false
    end
    if variant == "delayed_start" and f >= 6750 and f < 6754 then
        start_on = true
    end
    if variant == "respawn_input_suppressed" and f >= 6700 then
        right_on, gun_on, attack_on, jump_on = false, false, false, false
    elseif variant == "continue_confirm_gun" and f >= 6700 then
        right_on, attack_on, jump_on = false, false, false
    elseif variant == "continue_confirm_attack" and f >= 6700 then
        right_on, gun_on, jump_on = false, false, false
    elseif variant == "continue_confirm_jump" and f >= 6700 then
        right_on, gun_on, attack_on = false, false, false
    elseif variant == "continue_confirm_right" and f >= 6700 then
        gun_on, attack_on, jump_on = false, false, false
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
    [6081]=true, [6082]=true, [6138]=true, [6198]=true, [6199]=true,
    [6200]=true, [6630]=true, [6690]=true, [6692]=true, [6723]=true,
    [6758]=true, [6767]=true, [6786]=true, [6812]=true, [6857]=true,
}

local function capture(input_word)
    samples:write(table.concat({
        frame, variant, input_word, u8(0xff8009), u8(player), u8(player + 4),
        u8(player + 5), u16(player + 6), u8(player + 7), u8(player + 0x0f),
        s16(u16(player + 0x10)), s16(u16(player + 0x14)),
        s16(u16(player + 0x18)), string.format("%08x", u32(player + 0x1c)),
        u16(player + 0x2a), s16(u16(player + 0x40)),
        s16(u16(player + 0x42)), u8(player + 0x48), u8(player + 0x70),
        bytes_hex(player, 0xc0), bytes_hex(player_header, 0x80),
    }, "\t") .. "\n")
    if witnesses[frame] then
        screen:snapshot(string.format(root .. "/frames/%05d.png", frame))
    end
end

oracle11_hitko_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = schedule(frame)
    if variant == "survive_contact" and frame >= 6000 and frame <= 6080 then
        mutation_active = true
        program:write_u16(player + 0x40, 50)
        program:write_u16(player + 0x42, 50)
        mutation_active = false
    end
    if frame >= first_frame and frame <= last_frame then capture(input_word) end
    if frame == last_frame then
        coin:clear_value(); start:clear_value(); left:clear_value()
        right:clear_value(); up:clear_value(); down:clear_value()
        gun:clear_value(); attack:clear_value(); jump:clear_value()
        samples:close(); player_writes:close(); global_writes:close()
        qsound_writes:close(); machine:exit()
    end
end)
