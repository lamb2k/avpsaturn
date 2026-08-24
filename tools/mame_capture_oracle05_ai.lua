-- ORACLE-05: bounded class-0x1F AI capture with direct scheduler and RNG taps.
-- Raw evidence stays ignored beneath .deps; no production/Saturn state is used.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local opcodes = maincpu.spaces["opcodes"]
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

local root = assert(os.getenv("AVSP_ORACLE05_ROOT"))
local variant = os.getenv("AVSP_ORACLE05_VARIANT") or "baseline"
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local rng_calls = assert(io.open(root .. "/rng_calls.tsv", "w"))
local scheduler = assert(io.open(root .. "/scheduler.tsv", "w"))
local class_entries = assert(io.open(root .. "/class_entries.tsv", "w"))
local frame = 0
local first_frame = 2400
local last_frame = 5500
local player_base = 0xff8380
local enemy_base = 0xffa000
local rng_address = 0xff81a8

local function u8(address) return program:read_u8(address) end
local function u16(address) return program:read_u16(address) end
local function u32(address) return program:read_u32(address) end
local function s16(value) return value >= 0x8000 and value - 0x10000 or value end

local function actor(prefix, base, row)
    local anim = u32(base + 0x1c)
    local values = {
        u8(base), u8(base + 1), u8(base + 2), u8(base + 3),
        u8(base + 4), u8(base + 5), u16(base + 6), u8(base + 7),
        u8(base + 8), u8(base + 0x0f), s16(u16(base + 0x10)),
        s16(u16(base + 0x14)), s16(u16(base + 0x18)),
        string.format("%08x", anim), u16(base + 0x2a), u8(base + 0x2a),
        s16(u16(base + 0x40)), s16(u16(base + 0x42)),
        u8(base + 0x2c), u8(base + 0x2d), u16(base + 0x28),
        anim ~= 0 and u8(anim + 8) or 0,
        anim ~= 0 and u8(anim + 9) or 0,
    }
    for _, value in ipairs(values) do row[#row + 1] = value end
end

local actor_columns = table.concat({
    "active", "flags1", "class", "spawn_variant", "state", "inner",
    "action", "phase", "type", "facing", "x", "y", "z", "anim",
    "timer_word", "ai_timer", "health", "latched_health", "hit",
    "hit_source", "target_slot", "hurt", "attack_box"
}, "\t")
samples:write("frame\tvariant\tinput_word\trng_word\t" ..
    "p_" .. actor_columns:gsub("\t", "\tp_") .. "\t" ..
    "e_" .. actor_columns:gsub("\t", "\te_") ..
    "\te_a1\te_a2\te_a3\te_a4\te_a5\te_a6\te_ac\te_ad\te_a8" ..
    "\te_ae\te_b0\n")
rng_calls:write("frame\tvariant\tsequence\tkind\taddress\tdata\tmask\tpc\ta6\tseed\n")
scheduler:write("frame\tvariant\tsequence\tslot\td7\tactive\tclass\ttype\n")
class_entries:write("frame\tvariant\tsequence\tslot\tstate\tinner\taction\tai_timer\thealth\n")

local rng_sequence = 0
local scheduler_sequence = 0
local class_sequence = 0

-- Opcode-space taps fire on the actual instruction fetch, not on actor visuals.
oracle05_rng_tap = opcodes:install_read_tap(
    0x017c5e, 0x017c5f, "oracle05_rng_entry",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        rng_sequence = rng_sequence + 1
        local a6 = maincpu.state["A6"].value
        rng_calls:write(string.format(
            "%d\t%s\t%d\tentry\t017c5e\t\t\t%06x\t%06x\t%04x\n",
            frame, variant, rng_sequence,
            maincpu.state["PC"].value & 0xffffff,
            a6 & 0xffffff, u16(rng_address)))
    end)

oracle05_rng_write_tap = program:install_write_tap(
    0xff81a8, 0xff81a9, "oracle05_rng_write",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        rng_sequence = rng_sequence + 1
        rng_calls:write(string.format(
            "%d\t%s\t%d\twrite\t%06x\t%04x\t%04x\t%06x\t%06x\t%04x\n",
            frame, variant, rng_sequence, offset & 0xffffff, data & 0xffff,
            mask & 0xffff, maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff, u16(rng_address)))
    end)

oracle05_scheduler_tap = opcodes:install_read_tap(
    0x01b986, 0x01b987, "oracle05_enemy_scheduler_slot",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        scheduler_sequence = scheduler_sequence + 1
        local slot = maincpu.state["A6"].value & 0xffffff
        scheduler:write(string.format("%d\t%s\t%d\t%06x\t%04x\t%d\t%d\t%d\n",
            frame, variant, scheduler_sequence, slot,
            maincpu.state["D7"].value & 0xffff, u8(slot),
            u8(slot + 2), u8(slot + 8)))
    end)

-- The class routine entry proves which scheduler visits actually dispatch a
-- class-0x1F actor. It is deliberately separate from the loop-head fetch tap,
-- whose final not-taken DBRA prefetch can expose one non-executed address.
oracle05_class_tap = opcodes:install_read_tap(
    0x060532, 0x060533, "oracle05_class_1f_entry",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        class_sequence = class_sequence + 1
        local slot = maincpu.state["A6"].value & 0xffffff
        class_entries:write(string.format(
            "%d\t%s\t%d\t%06x\t%d\t%d\t%d\t%d\t%d\n",
            frame, variant, class_sequence, slot, u8(slot + 4), u8(slot + 5),
            u16(slot + 6), u8(slot + 0x2a), s16(u16(slot + 0x40))))
    end)

local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
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
    if f >= 4420 and f <= 5469 then
        attack_on = (f - 4420) % 45 < 5
    end
    if variant == "attack_timing" and f >= 4420 and f <= 4424 then
        attack_on = false
    end
    word = drive(coin, coin_on, 1, word)
    word = drive(start, start_on, 2, word)
    word = drive(left, left_on, 4, word)
    word = drive(right, right_on, 8, word)
    word = drive(up, false, 128, word)
    word = drive(down, false, 256, word)
    word = drive(gun, gun_on, 16, word)
    word = drive(attack, attack_on, 32, word)
    word = drive(jump, jump_on, 64, word)
    return word
end

local function apply_counterfactual(f)
    -- Position perturbations span the next class-0x1F spawn and first choice,
    -- rather than changing coordinates after an action is already committed.
    if variant == "distance_far" and f >= 4435 and f <= 4608 then
        program:write_u16(player_base + 0x10, 0x0700)
    elseif variant == "lane_far" and f >= 4435 and f <= 4608 then
        program:write_u16(player_base + 0x14, 0x0190)
        program:write_u16(player_base + 0x18, 0x0190)
    elseif variant == "ai_timer" and f == 4254 then
        program:write_u8(enemy_base + 0x2a, 3)
    elseif variant == "rng_state" and f == 4252 then
        program:write_u16(rng_address, 0x0001)
    elseif variant == "enemy_health" and f == 5184 then
        program:write_u16(enemy_base + 0x40, 15)
        program:write_u16(enemy_base + 0x42, 15)
    end
end

local witness_frames = {
    [2400]=true, [4080]=true, [4213]=true, [4214]=true, [4253]=true,
    [4301]=true, [4372]=true, [4373]=true, [4420]=true, [4512]=true,
    [5184]=true, [5190]=true, [5330]=true, [5470]=true,
}

local function capture(input_word)
    local row = {frame, variant, input_word, string.format("%04x", u16(rng_address))}
    actor("p", player_base, row)
    actor("e", enemy_base, row)
    for _, offset in ipairs({0xa1,0xa2,0xa3,0xa4,0xa5,0xa6,0xac,0xad}) do
        row[#row + 1] = u8(enemy_base + offset)
    end
    row[#row + 1] = u16(enemy_base + 0xa8)
    row[#row + 1] = u8(enemy_base + 0xae)
    row[#row + 1] = u8(enemy_base + 0xb0)
    samples:write(table.concat(row, "\t") .. "\n")
    if witness_frames[frame] then
        screen:snapshot(string.format(root .. "/%05d.png", frame))
    end
end

oracle05_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = apply_schedule(frame)
    apply_counterfactual(frame)
    -- Preserve two native enemy contacts, then use a declared research-only
    -- survival guard so the same route can expose the later enemy HIT/KO path.
    if frame >= 4374 then program:write_u8(0xff83c1, 0x65) end
    if frame >= first_frame and frame <= last_frame then capture(input_word) end
    if frame == last_frame then
        samples:close(); rng_calls:close(); scheduler:close()
        class_entries:close(); machine:exit()
    end
end)
