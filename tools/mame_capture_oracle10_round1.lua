-- ORACLE-10: lightweight full Round 1 route perturbation/counterfactual probe.
-- Raw source observations remain private under .deps/mame/oracle10_*.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local screen = machine.screens[":screen"]
local cps_a = machine.memory.shares[":cps_a_regs"]
local cps_b = machine.memory.shares[":cps_b_regs"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun, attack, jump = in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"]

local root = assert(os.getenv("AVSP_ORACLE10_ROOT"))
local variant = assert(os.getenv("AVSP_ORACLE10_VARIANT"))
local valid = {
    baseline=true, route_perturbed=true, hold_navigation=true, suppress_street_offense=true,
    suppress_warehouse_offense=true, suppress_boss_offense=true,
    no_continue=true, remove_class_1f=true, remove_class_00=true,
    remove_class_01=true, remove_class_06=true,
    remove_navigation_bodies=true, remove_auxiliary_classes=true,
    freeze_rng=true,
}
assert(valid[variant], "unsupported ORACLE-10 variant: " .. variant)

local first_frame, last_frame = 1972, 18000
local player = 0xff8380
local actor_first, actor_stride, actor_count = 0xff9580, 0xc0, 57
local frame, mutation_active = 0, false
local frozen_rng = nil
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local events = assert(io.open(root .. "/actor_events.tsv", "w"))
local actor_writers = assert(io.open(root .. "/actor_writers.tsv", "w"))
local route_writers = assert(io.open(root .. "/route_writers.tsv", "w"))
local qsound_writers = assert(io.open(root .. "/qsound_writers.tsv", "w"))
local video_events = assert(io.open(root .. "/video_events.tsv", "w"))
samples:write("frame\tvariant\tinput_word\tg8009\trng\tp_active\tp_state\tp_phase\tp_facing\tp_x\tp_z\tp_health\tactor_population\n")
events:write("frame\tvariant\tslot\tactive\tclass\ttype\tstate\tphase\tfacing\tx\ty\tz\tanim\thealth\ttarget\n")
actor_writers:write("variant\tslot_kind\tclass\ttype\tfield_offset\tpc\tfirst_frame\tlast_frame\tcount\n")
route_writers:write("variant\taddress\tpc\tfirst_frame\tlast_frame\tcount\n")
qsound_writers:write("variant\taddress\tpc\tfirst_frame\tlast_frame\tcount\n")
video_events:write("frame\tvariant\tcps_a\tcps_b\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
end
local function share_hex(share)
    local out = {}
    for offset = 0, share.size - 2, 2 do
        out[#out + 1] = string.format("%04x", share:read_u16(offset))
    end
    return table.concat(out)
end
local function update_count(table_, key)
    local row = table_[key]
    if row then row.last = frame; row.count = row.count + 1
    else table_[key] = {first=frame, last=frame, count=1} end
end

local selected_offsets = {
    [0x00]=true, [0x02]=true, [0x04]=true, [0x06]=true, [0x08]=true,
    [0x0e]=true, [0x10]=true, [0x14]=true, [0x18]=true, [0x1c]=true,
    [0x1e]=true, [0x28]=true, [0x2a]=true, [0x40]=true,
}
local actor_writer_counts, route_writer_counts, qsound_writer_counts = {}, {}, {}
local function actor_base_and_offset(address)
    if address >= player and address <= player + 0xbf then
        return player, address - player, "player"
    end
    if address < actor_first then return nil end
    local relative = address - actor_first
    local index = math.floor(relative / actor_stride)
    local inner = relative % actor_stride
    if index < actor_count then
        return actor_first + index * actor_stride, inner, "actor-" .. index
    end
    return nil
end

oracle10_actor_tap = program:install_write_tap(
    player, actor_first + actor_count * actor_stride - 1,
    "oracle10_actor_writers", function(offset, data, mask)
        if mutation_active or frame < first_frame or frame > last_frame then return end
        local base, inner, kind = actor_base_and_offset(offset & 0xffffff)
        if not base or not selected_offsets[inner & 0xfe] then return end
        local key = table.concat({kind, string.format("%02x", u8(base + 2)),
            string.format("%02x", u8(base + 8)), string.format("%02x", inner & 0xfe),
            string.format("%06x", maincpu.state["PC"].value & 0xffffff)}, ":")
        update_count(actor_writer_counts, key)
    end)
oracle10_route_tap = program:install_write_tap(
    0xff8000, 0xff82ff, "oracle10_route_writers",
    function(offset, data, mask)
        if mutation_active or frame < first_frame or frame > last_frame then return end
        local key = string.format("%06x:%06x", offset & 0xffffff,
            maincpu.state["PC"].value & 0xffffff)
        update_count(route_writer_counts, key)
    end)
oracle10_qsound_tap = program:install_write_tap(
    0x618000, 0x619fff, "oracle10_qsound_writers",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local key = string.format("%06x:%06x", offset & 0xffffff,
            maincpu.state["PC"].value & 0xffffff)
        update_count(qsound_writer_counts, key)
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
        if variant == "route_perturbed" then
            -- Shift the periodic credit/start edges by one frame throughout
            -- the route while preserving the source-completing movement and
            -- offensive schedule. This is input-visible at every 600-frame
            -- interval and retains the continue opportunity.
            coin_on = r % 600 >= 31 and r % 600 < 35
            start_on = r % 600 >= 91 and r % 600 < 95
        end
    end
    if variant == "hold_navigation" and f >= 2600 and f <= 3200 then
        right_on = false
    end
    if variant == "suppress_street_offense" and f >= 2074 and f <= 5550 then
        gun_on, attack_on, jump_on = false, false, false
    end
    if variant == "suppress_warehouse_offense" and f >= 5566 and f <= 9940 then
        gun_on, attack_on, jump_on = false, false, false
    end
    if variant == "suppress_boss_offense" and f >= 9976 and f <= 15050 then
        gun_on, attack_on, jump_on = false, false, false
    end
    if variant == "no_continue" and f >= 5600 then coin_on, start_on = false, false end
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

local auxiliary = {[0x10]=true, [0x3d]=true, [0x43]=true, [0x45]=true,
    [0x49]=true, [0x4b]=true, [0x4e]=true, [0x80]=true}
local function apply_counterfactual()
    mutation_active = true
    if variant == "freeze_rng" and frame >= first_frame then
        if not frozen_rng then frozen_rng = u16(0xff81a8) end
        program:write_u16(0xff81a8, frozen_rng)
    end
    for index = 0, actor_count - 1 do
        local base = actor_first + index * actor_stride
        local class, type_ = u8(base + 2), u8(base + 8)
        local remove = false
        if variant == "remove_class_1f" and class == 0x1f then remove = true end
        if variant == "remove_class_00" and class == 0x00 and type_ == 12 then remove = true end
        if variant == "remove_class_01" and class == 0x01 then remove = true end
        if variant == "remove_class_06" and class == 0x06 and type_ == 12 then remove = true end
        if variant == "remove_navigation_bodies" and type_ == 20 and
            class >= 0x07 and class <= 0x0a then remove = true end
        if variant == "remove_auxiliary_classes" and
            (auxiliary[class] or type_ == 16 or type_ == 24 or type_ == 240) then
            remove = true
        end
        if remove and u8(base) ~= 0 then program:write_u8(base, 0) end
    end
    mutation_active = false
end

local previous_actor, previous_video = {}, nil
local witness = {[1972]=true, [2074]=true, [5566]=true, [6201]=true,
    [6693]=true, [9976]=true, [12800]=true, [13293]=true,
    [15092]=true, [15193]=true, [18000]=true}
local function actor_key(base)
    return table.concat({u8(base), u8(base + 2), u8(base + 8),
        u16(base + 4), u16(base + 6), u8(base + 0x0f),
        u32(base + 0x1c), u16(base + 0x40), u16(base + 0x28)}, ":")
end
local function emit_actor(slot, base)
    local key = actor_key(base)
    if previous_actor[slot] == key then return end
    previous_actor[slot] = key
    events:write(table.concat({frame, variant, slot, u8(base),
        string.format("%02x", u8(base + 2)), u8(base + 8), u16(base + 4),
        u16(base + 6), u8(base + 0x0f), s16(u16(base + 0x10)),
        s16(u16(base + 0x14)), s16(u16(base + 0x18)),
        string.format("%08x", u32(base + 0x1c)), s16(u16(base + 0x40)),
        string.format("%04x", u16(base + 0x28))}, "\t") .. "\n")
end
local function population()
    local counts = {}
    for index = 0, actor_count - 1 do
        local base = actor_first + index * actor_stride
        if u8(base) ~= 0 then
            local key = string.format("%02x-%02x", u8(base + 2), u8(base + 8))
            counts[key] = (counts[key] or 0) + 1
        end
    end
    local keys, out = {}, {}
    for key in pairs(counts) do keys[#keys + 1] = key end
    table.sort(keys)
    for _, key in ipairs(keys) do out[#out + 1] = key .. ":" .. counts[key] end
    return table.concat(out, ",")
end

local function flush_counts(table_, stream, kind)
    local keys = {}
    for key in pairs(table_) do keys[#keys + 1] = key end
    table.sort(keys)
    for _, key in ipairs(keys) do
        local row = table_[key]
        if kind == "actor" then
            local slot, class, type_, field, pc = key:match("([^:]+):([^:]+):([^:]+):([^:]+):([^:]+)")
            stream:write(table.concat({variant, slot, class, type_, field, pc,
                row.first, row.last, row.count}, "\t") .. "\n")
        else
            local address, pc = key:match("([^:]+):([^:]+)")
            stream:write(table.concat({variant, address, pc, row.first,
                row.last, row.count}, "\t") .. "\n")
        end
    end
end

oracle10_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = schedule(frame)
    apply_counterfactual()
    if frame >= first_frame and frame <= last_frame then
        emit_actor("player", player)
        for index = 0, actor_count - 1 do
            emit_actor("actor-" .. index, actor_first + index * actor_stride)
        end
        samples:write(table.concat({frame, variant, input_word, u8(0xff8009),
            string.format("%04x", u16(0xff81a8)), u8(player), u16(player + 4),
            u16(player + 6), u8(player + 0x0f), s16(u16(player + 0x10)),
            s16(u16(player + 0x18)), s16(u16(player + 0x40)), population()}, "\t") .. "\n")
        local video = share_hex(cps_a) .. "\t" .. share_hex(cps_b)
        if video ~= previous_video then
            video_events:write(frame .. "\t" .. variant .. "\t" .. video .. "\n")
            previous_video = video
        end
        if witness[frame] or frame % 600 == 0 then
            screen:snapshot(string.format(root .. "/frames/%05d.png", frame))
        end
    end
    if frame == last_frame then
        flush_counts(actor_writer_counts, actor_writers, "actor")
        flush_counts(route_writer_counts, route_writers, "route")
        flush_counts(qsound_writer_counts, qsound_writers, "qsound")
        coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
        up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value(); jump:clear_value()
        samples:close(); events:close(); actor_writers:close(); route_writers:close()
        qsound_writers:close(); video_events:close(); machine:exit()
    end
end)
