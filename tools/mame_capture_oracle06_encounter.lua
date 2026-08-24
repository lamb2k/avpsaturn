-- ORACLE-06: bounded Round 1 player-start encounter capture.
-- Raw evidence stays ignored beneath .deps; this never writes production or
-- Saturn state.  The route uses one real credit/Start and the accepted
-- character-select interaction instead of the attract-mode combat route.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local screen = machine.screens[":screen"]
local cps_a = machine.memory.shares[":cps_a_regs"]
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
local in2_port = machine.ioport.ports[":IN2"]
print(string.format(
    "ORACLE06_IO coin_mask=%08x start_mask=%08x",
    coin.mask, start.mask))

local root = assert(os.getenv("AVSP_ORACLE06_ROOT"))
local variant = os.getenv("AVSP_ORACLE06_VARIANT") or "baseline"
assert(variant == "baseline" or variant == "entry_hold" or
    variant == "clear_attack_suppression", "unsupported ORACLE-06 variant")
local first_frame = tonumber(os.getenv("AVSP_ORACLE06_FIRST_FRAME") or "2200")
local last_frame = tonumber(os.getenv("AVSP_ORACLE06_LAST_FRAME") or "7200")
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local actors = assert(io.open(root .. "/actors.tsv", "w"))
local writes = assert(io.open(root .. "/controller_writes.tsv", "w"))
local qsound = assert(io.open(root .. "/qsound.tsv", "w"))
local frame = 0
local player_base = 0xff8380
local actor_first = 0xff9580
local actor_count = 20
local actor_stride = 0xc0

local function u8(address) return program:read_u8(address) end
local function u16(address) return program:read_u16(address) end
local function s16(value) return value >= 0x8000 and value - 0x10000 or value end

samples:write("frame\tvariant\tinput_word\tin2_raw\tp_active\tp_class\tp_state\tp_inner\tp_action",
    "\tp_type\tp_facing\tp_x\tp_z\tp_health\tg8009\tg801b\tg801d\tg8032\tg81d5\tg81f3",
    "\tg8208\tg8249\tscroll1_x\tscroll1_y\tscroll2_x\tscroll2_y",
    "\tscroll3_x\tscroll3_y\tclass1f_active\tclass1f_living\n")
actors:write("frame\tvariant\tpool_index\taddress\tactive\tclass\ttype\tstate",
    "\tinner\taction\tx\tz\thealth\ttimer\n")
writes:write("frame\tvariant\taddress\tdata\tmask\tpc\ta5\ta6\tvalue\n")
qsound:write("frame\tvariant\tpc\tport\tbyte\tregister\tvalue\n")

local watch_addresses = {
    0xff8008, 0xff801a, 0xff801c, 0xff8032,
    0xff81d4, 0xff81f2, 0xff8208, 0xff8248,
}
for _, address in ipairs(watch_addresses) do
    local watched = address
    oracle06_write_tap = oracle06_write_tap or {}
    oracle06_write_tap[#oracle06_write_tap + 1] = program:install_write_tap(
        watched, watched + 1, string.format("oracle06_%06x", watched),
        function(offset, data, mask)
            if frame < first_frame or frame > last_frame then return end
            writes:write(string.format(
                "%d\t%s\t%06x\t%04x\t%04x\t%06x\t%06x\t%06x\t%04x\n",
                frame, variant, watched, data & 0xffff, mask & 0xffff,
                maincpu.state["PC"].value & 0xffffff,
                maincpu.state["A5"].value & 0xffffff,
                maincpu.state["A6"].value & 0xffffff, u16(watched)))
        end)
end

local audio_cpu = machine.devices[":audiocpu"]
local audio_program = audio_cpu.spaces["program"]
local qsound_latch = 0
oracle06_qsound_tap = audio_program:install_write_tap(
    0xd000, 0xd002, "oracle06_qsound_bus",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local port = offset & 0xffff
        local byte = data & 0xff
        local register = ""
        local value = ""
        if port == 0xd000 then
            qsound_latch = ((byte << 8) | (qsound_latch & 0xff)) & 0xffff
        elseif port == 0xd001 then
            qsound_latch = ((qsound_latch & 0xff00) | byte) & 0xffff
        else
            register = string.format("%02x", byte)
            value = string.format("%04x", qsound_latch)
        end
        qsound:write(string.format("%d\t%s\t%04x\t%04x\t%02x\t%s\t%s\n",
            frame, variant, audio_cpu.state["PC"].value & 0xffff,
            port, byte, register, value))
    end)

local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
end

local function apply_schedule(f)
    local word = 0
    local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
    local start_on = f >= 2405 and f < 2408
    local story_skip = f >= 2500 and f < 2505
    local select_confirm = f >= 3300 and f < 3305
    local gameplay = f >= 3700
    local right_on = gameplay
    local gun_on = gameplay and f % 75 < 6
    local attack_on = gameplay and f % 45 < 5
    local jump_on = gameplay and f % 430 < 7
    if variant == "entry_hold" and f >= 3700 and f <= 3900 then
        right_on = false
    end
    if variant == "clear_attack_suppression" and f >= 3800 and f <= 5200 then
        gun_on = false
        attack_on = false
        jump_on = false
    end
    word = drive(coin, coin_on, 1, word)
    word = drive(start, start_on, 2, word)
    word = drive(left, false, 4, word)
    word = drive(right, right_on, 8, word)
    word = drive(gun, gun_on, 16, word)
    word = drive(attack, story_skip or select_confirm or attack_on, 32, word)
    word = drive(jump, jump_on, 64, word)
    word = drive(up, false, 128, word)
    word = drive(down, false, 256, word)
    return word
end

local witness_frames = {
    [2400]=true, [2500]=true, [3300]=true, [3408]=true, [3439]=true,
    [3469]=true, [3574]=true, [3600]=true, [3715]=true, [3821]=true,
    [3900]=true, [4200]=true, [4994]=true, [4995]=true, [5071]=true,
    [6000]=true, [6467]=true, [6767]=true, [6768]=true, [6892]=true,
    [6919]=true, [6930]=true, [6935]=true, [7088]=true, [7200]=true,
}

local function capture(input_word)
    local active = 0
    local living = 0
    for index = 0, actor_count - 1 do
        local base = actor_first + index * actor_stride
        local is_active = u8(base)
        local class = u8(base + 2)
        local health = s16(u16(base + 0x40))
        if is_active ~= 0 and class == 0x1f then
            active = active + 1
            if health > 0 and u8(base + 4) ~= 4 then living = living + 1 end
        end
        actors:write(string.format(
            "%d\t%s\t%d\t%06x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",
            frame, variant, index, base, is_active, class, u8(base + 8),
            u8(base + 4), u8(base + 5), u16(base + 6),
            s16(u16(base + 0x10)), s16(u16(base + 0x14)), health,
            u8(base + 0x2a)))
    end
    samples:write(table.concat({
        frame, variant, input_word, in2_port:read(), u8(player_base),
        u8(player_base + 2), u8(player_base + 4), u8(player_base + 5),
        u16(player_base + 6), u8(player_base + 8), u8(player_base + 0x0f),
        s16(u16(player_base + 0x10)), s16(u16(player_base + 0x14)),
        s16(u16(player_base + 0x40)), u8(0xff8009), u8(0xff801b),
        u8(0xff801d), u8(0xff8032), u8(0xff81d5), u8(0xff81f3),
        u8(0xff8208), u8(0xff8249), cps_a:read_u16(12),
        cps_a:read_u16(14), cps_a:read_u16(16), cps_a:read_u16(18),
        cps_a:read_u16(20), cps_a:read_u16(22), active, living,
    }, "\t") .. "\n")
    if witness_frames[frame] or frame % 120 == 0 then
        screen:snapshot(string.format(root .. "/frames/%05d.png", frame))
    end
end

oracle06_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = apply_schedule(frame)
    -- Research-only survival guard: only P1 health is protected. Enemy state,
    -- health, spawning, controller state, camera and audio remain native.
    if frame >= 3400 then
        program:write_u8(0xff83c1, 0x65)
    end
    if frame >= first_frame and frame <= last_frame then capture(input_word) end
    if frame == last_frame then
        coin:clear_value(); start:clear_value(); left:clear_value()
        right:clear_value(); up:clear_value(); down:clear_value()
        gun:clear_value(); attack:clear_value(); jump:clear_value()
        samples:close(); actors:close(); writes:close(); qsound:close()
        machine:exit()
    end
end)
