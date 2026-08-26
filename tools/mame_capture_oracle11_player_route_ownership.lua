-- ORACLE-11 Predator Warrior route interaction/resource ownership probe.
-- Raw ledgers stay private under .deps/mame/oracle11_player_route_ownership_*.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local audio_cpu = machine.devices[":audiocpu"]
local audio_program = audio_cpu.spaces["program"]
local root = assert(os.getenv("AVSP_ORACLE11_PLAYER_ROUTE_ROOT"))
local variant = assert(os.getenv("AVSP_ORACLE11_PLAYER_ROUTE_VARIANT"))
local allowed = {
    baseline=true, health_max=true, effect_pool_unavailable=true,
    interaction_uninterrupted=true, resource_pickup_near=true,
}
assert(allowed[variant], "unsupported player-route variant: " .. variant)

local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun, attack, jump = in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"]
local player = 0xff8380
local record24, record24_count, record24_stride = 0xffb680, 32, 0x80
local resource_pickup = 0xffcd00
local pool24_free_count = 0xffee89
local first_frame, last_frame = 2800, 4200
local frame, sequence, mutation_active, saved_free_count = 0, 0, false, nil
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local writes = assert(io.open(root .. "/writes.tsv", "w"))
local actors = assert(io.open(root .. "/actors.tsv", "w"))
local qsound = assert(io.open(root .. "/qsound.tsv", "w"))
samples:write("frame\tvariant\tinput\tstate\taction\tinner\tfacing\tx\ty\tz\thealth\tlatched\tresource\trecharge\tdepleted\taward\td2\tr24_free\n")
writes:write("frame\tvariant\tsequence\tkind\taddress\toffset\tdata\tmask\tpc\ta4\ta5\ta6\tvalue\n")
actors:write("frame\tvariant\tslot\tactive\tclass\tsubtype\tstate\taction\tx\ty\tz\tanim\tfield4e\n")
qsound:write("frame\tvariant\tpc\tport\tbyte\tregister\tvalue\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
end
local function write_tap(first, last, name, kind)
    return program:install_write_tap(first, last, name, function(offset, data, mask)
        if mutation_active or frame < first_frame or frame > last_frame then return end
        sequence = sequence + 1
        writes:write(string.format("%d\t%s\t%d\t%s\t%06x\t%02x\t%04x\t%04x\t%06x\t%06x\t%06x\t%06x\t%08x\n",
            frame, variant, sequence, kind, offset & 0xffffff,
            (offset - first) & 0xff, data & 0xffff, mask & 0xffff,
            maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A4"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff, u32(offset & 0xfffffe)))
    end)
end
oracle11_player_route_taps = {
    write_tap(player, player + 0xff, "oracle11_player_route_player", "player"),
    write_tap(record24, record24 + record24_count * record24_stride - 1,
        "oracle11_player_route_record24", "record24"),
    write_tap(0xffee68, 0xffee8b, "oracle11_player_route_pool", "pool"),
}
local qsound_latch = 0
oracle11_player_route_qsound = audio_program:install_write_tap(
    0xd000, 0xd002, "oracle11_player_route_qsound", function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local port, byte = offset & 0xffff, data & 0xff
        local register, value = "", ""
        if port == 0xd000 then
            qsound_latch = ((byte << 8) | (qsound_latch & 0xff)) & 0xffff
        elseif port == 0xd001 then
            qsound_latch = ((qsound_latch & 0xff00) | byte) & 0xffff
        else
            register, value = string.format("%02x", byte), string.format("%04x", qsound_latch)
        end
        qsound:write(string.format("%d\t%s\t%04x\t%04x\t%02x\t%s\t%s\n",
            frame, variant, audio_cpu.state["PC"].value & 0xffff,
            port, byte, register, value))
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
    if variant == "resource_pickup_near" and f >= 3990 and f < 4030 then
        gun_on, jump_on = false, false
        attack_on = f >= 4000 and f < 4003
    end
    if variant == "interaction_uninterrupted" and f >= 4033 then
        gun_on, attack_on, jump_on = false, false, false
    end
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

local function mutate()
    mutation_active = true
    if variant == "health_max" and frame >= 3090 and frame <= 3101 then
        program:write_u16(player + 0x40, 101)
        program:write_u16(player + 0x42, 101)
    elseif variant == "effect_pool_unavailable" then
        if frame == 4030 then saved_free_count = u8(pool24_free_count) end
        if frame >= 4030 and frame <= 4031 then program:write_u8(pool24_free_count, 0) end
        if frame == 4032 and saved_free_count then
            program:write_u8(pool24_free_count, saved_free_count)
        end
    elseif variant == "resource_pickup_near" and frame >= 3997 and frame <= 4002 then
        -- Preserve the route actor and its source state; alter only current
        -- world position so the native target-selection/interaction path can
        -- decide whether record28 class0x0e is reachable.
        program:write_u16(resource_pickup + 0x10, u16(player + 0x10))
        program:write_u16(resource_pickup + 0x14, u16(player + 0x14))
        program:write_u16(resource_pickup + 0x18, u16(player + 0x18))
    end
    mutation_active = false
end

local function capture(input_word)
    samples:write(table.concat({
        frame, variant, input_word, u16(player + 4), u16(player + 6),
        u8(player + 7), u8(player + 0xf), s16(u16(player + 0x10)),
        s16(u16(player + 0x14)), s16(u16(player + 0x18)),
        s16(u16(player + 0x40)), s16(u16(player + 0x42)),
        u8(player + 0x8c), u8(player + 0x8d), u8(player + 0x8b),
        u16(player + 0xae), u8(player + 0xd2), u8(pool24_free_count),
    }, "\t") .. "\n")
    for slot = 0, record24_count - 1 do
        local a = record24 + slot * record24_stride
        if u8(a) ~= 0 then
            actors:write(table.concat({
                frame, variant, slot, u8(a), string.format("%02x", u8(a + 2)),
                string.format("%02x", u8(a + 3)), u16(a + 4), u16(a + 6),
                s16(u16(a + 0x10)), s16(u16(a + 0x14)),
                s16(u16(a + 0x18)), string.format("%08x", u32(a + 0x1c)),
                string.format("%02x", u8(a + 0x4e)),
            }, "\t") .. "\n")
        end
    end
end

oracle11_player_route_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = schedule(frame)
    mutate()
    if frame >= first_frame and frame <= last_frame then capture(input_word) end
    if frame == last_frame then
        coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
        up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value(); jump:clear_value()
        samples:close(); writes:close(); actors:close(); qsound:close(); machine:exit()
    end
end)
