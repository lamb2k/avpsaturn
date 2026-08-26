-- ORACLE-11 Predator Warrior player-origin gameplay-audio boundary probe.
-- Raw ledgers remain private under .deps/mame/oracle11_player_audio_*.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local audio_cpu = machine.devices[":audiocpu"]
local audio_program = audio_cpu.spaces["program"]
local root = assert(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_ROOT"))
local variant = os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_VARIANT") or "baseline"
local suppress_caller = tonumber(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_CALLER") or "")
local suppress_command = tonumber(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_COMMAND") or "")
local suppress_state = tonumber(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_STATE") or "")
local suppress_action = tonumber(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_ACTION") or "")
local suppress_inner = tonumber(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_INNER") or "")
local suppress_a6 = tonumber(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_A6") or "")
local suppress_return0 = tonumber(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_RETURN0") or "")
local suppress_limit = tonumber(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_SUPPRESS_LIMIT") or "") or 1
local compact_qsound = os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_COMPACT_QSOUND") == "1"

local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun, attack, jump = in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"]

local first_frame = 1972
local last_frame = tonumber(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME") or "") or 18000
local player = 0xff8380
local actor_first, actor_stride, actor_count = 0xff9580, 0xc0, 57
-- MAME's program-space tap needs the containing work-RAM mapping here; the
-- callback immediately narrows to the measured 0xff0a88..0xff0e87 ring.
local queue_first, queue_last = 0xff0000, 0xffffff
local frame, dispatch_sequence, qsound_latch = 0, 0, 0
local mutation_active, suppression_count = false, 0

local samples = assert(io.open(root .. "/samples.tsv", "w"))
local dispatches = assert(io.open(root .. "/dispatches.tsv", "w"))
local qsound = assert(io.open(root .. "/qsound.tsv", "w"))
local projectiles = assert(io.open(root .. "/projectiles.tsv", "w"))
local score_writes = assert(io.open(root .. "/score_writes.tsv", "w"))
local result = assert(io.open(root .. "/result.tsv", "w"))
samples:write("frame\tvariant\tinput\troute\tactive\tstate\taction\tinner\tfacing\tx\tz\thealth\thit\tresource\trecharge\tdepleted\taward\tscore\tprojectile_count\n")
dispatches:write("frame\tvariant\tsequence\tqueue_address\twrite_pc\tcapture_pc\tshared_dispatch\ta6\tsp\tusp\tsr\treturn0\treturn1\treturn2\td1\td2\td3\tcommand\torigin_active\torigin_class\torigin_state\torigin_phase\torigin_type\torigin_facing\torigin_health\tplayer_active\tplayer_state\tplayer_action\tplayer_inner\tplayer_facing\tplayer_health\tplayer_hit\tplayer_resource\tplayer_recharge\tplayer_depleted\tplayer_award\tplayer_score\tsuppressed\n")
qsound:write("frame\tvariant\tpc\tport\tbyte\tregister\tvalue\n")
projectiles:write("frame\tvariant\tslot\tactive\tclass\ttype\tstate\taction\tx\ty\tz\thealth\towner\n")
score_writes:write("frame\tvariant\taddress\tdata\tmask\tpc\ta6\n")
result:write("variant\tsuppression_count\tfinal_route\tfinal_active\tfinal_state\tfinal_action\tfinal_health\tfinal_resource\tfinal_score\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
end

local function schedule(f)
    local word = 0
    local coin_on, start_on, right_on = false, false, false
    local gun_on, attack_on, jump_on = false, false, false
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

local function projectile_count()
    local count = 0
    for index = 0, actor_count - 1 do
        local base = actor_first + index * actor_stride
        if u8(base) ~= 0 and u8(base + 2) == 0x05 then count = count + 1 end
    end
    return count
end

local function emit_projectiles()
    for index = 0, actor_count - 1 do
        local base = actor_first + index * actor_stride
        if u8(base) ~= 0 and u8(base + 2) == 0x05 then
            projectiles:write(table.concat({frame, variant, index, u8(base),
                string.format("%02x", u8(base + 2)), string.format("%02x", u8(base + 8)),
                u16(base + 4), u16(base + 6), s16(u16(base + 0x10)),
                s16(u16(base + 0x14)), s16(u16(base + 0x18)),
                s16(u16(base + 0x40)), string.format("%04x", u16(base + 0x28))}, "\t") .. "\n")
        end
    end
end

oracle11_player_audio_queue = program:install_write_tap(
    queue_first, queue_last, "oracle11_player_audio_queue",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        local address = offset & 0xffffff
        if address < 0xff0a88 or address > 0xff0e87 then return end
        -- The 68000 long store is exposed as two 16-bit writes. Capture the
        -- low word, which contains the command identity, exactly once.
        if pc ~= 0x001940 or (address & 3) ~= 2 then return end
        local sr = maincpu.state["SR"].value & 0xffff
        local system_sp = maincpu.state["SP"].value & 0xffffff
        local usp = maincpu.state["USP"].value & 0xffffff
        local sp = (sr & 0x2000) ~= 0 and system_sp or usp
        local return0, return1, return2 = u32(sp), u32(sp + 4), u32(sp + 8)
        local d1 = maincpu.state["D1"].value & 0xffffffff
        local d2 = maincpu.state["D2"].value & 0xffffffff
        local d3 = maincpu.state["D3"].value & 0xffffffff
        local origin = maincpu.state["A6"].value & 0xffffff
        local state, action, inner = u16(player + 4), u16(player + 6), u8(player + 7)
        local command = d1 & 0xffff
        local legacy_suppress = suppress_caller ~= nil and suppress_command ~= nil and
            return1 == suppress_caller and command == suppress_command and
            (suppress_state == nil or state == suppress_state) and
            (suppress_action == nil or action == suppress_action) and
            (suppress_inner == nil or inner == suppress_inner)
        local global_suppress = suppress_a6 ~= nil and suppress_return0 ~= nil and
            suppress_command ~= nil and
            (maincpu.state["A6"].value & 0xffffff) == suppress_a6 and
            return0 == suppress_return0 and command == suppress_command
        local suppress = (legacy_suppress or global_suppress) and
            suppression_count < suppress_limit
        if suppress then suppression_count = suppression_count + 1 end
        dispatch_sequence = dispatch_sequence + 1
        dispatches:write(table.concat({frame, variant, dispatch_sequence,
            string.format("%06x", (address - 2) & 0xffffff), "00193c", string.format("%06x", pc),
            "001922", string.format("%06x", maincpu.state["A6"].value & 0xffffff),
            string.format("%06x", sp), string.format("%06x", usp), string.format("%04x", sr),
            string.format("%06x", return0 & 0xffffff),
            string.format("%06x", return1 & 0xffffff), string.format("%06x", return2 & 0xffffff),
            string.format("%08x", d1), string.format("%08x", d2), string.format("%08x", d3),
            string.format("%04x", command), u8(origin), string.format("%02x", u8(origin + 2)),
            u16(origin + 4), u16(origin + 6), u8(origin + 8), u8(origin + 0x0f),
            s16(u16(origin + 0x40)), u8(player), state, action, inner, u8(player + 0x0f),
            s16(u16(player + 0x40)), s16(u16(player + 0x46)), u8(player + 0x8c),
            u8(player + 0x8d), u8(player + 0x8b), u16(player + 0xae),
            string.format("%08x", u32(player + 0xe0)), suppress and 1 or 0}, "\t") .. "\n")
        if suppress then return 0 end
    end)

oracle11_player_audio_score = program:install_write_tap(
    player + 0xe0, player + 0xe3, "oracle11_player_audio_score",
    function(offset, data, mask)
        if mutation_active or frame < first_frame or frame > last_frame then return end
        score_writes:write(string.format("%d\t%s\t%06x\t%08x\t%08x\t%06x\t%06x\n",
            frame, variant, offset & 0xffffff, data & 0xffffffff, mask & 0xffffffff,
            maincpu.state["PC"].value & 0xffffff, maincpu.state["A6"].value & 0xffffff))
    end)

oracle11_player_audio_qsound = audio_program:install_write_tap(
    0xd000, 0xd002, "oracle11_player_audio_qsound",
    function(offset, data, mask)
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
        if not compact_qsound then
            qsound:write(string.format("%d\t%s\t%04x\t%04x\t%02x\t%s\t%s\n",
                frame, variant, audio_cpu.state["PC"].value & 0xffff,
                port, byte, register, value))
        end
    end)

oracle11_player_audio_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = schedule(frame)
    if frame >= first_frame and frame <= last_frame then
        samples:write(table.concat({frame, variant, input_word, u8(0xff8009), u8(player),
            u16(player + 4), u16(player + 6), u8(player + 7), u8(player + 0x0f),
            s16(u16(player + 0x10)), s16(u16(player + 0x18)), s16(u16(player + 0x40)),
            s16(u16(player + 0x46)), u8(player + 0x8c), u8(player + 0x8d),
            u8(player + 0x8b), u16(player + 0xae), string.format("%08x", u32(player + 0xe0)),
            projectile_count()}, "\t") .. "\n")
        emit_projectiles()
    end
    if frame == last_frame then
        result:write(table.concat({variant, suppression_count, u8(0xff8009), u8(player),
            u16(player + 4), u16(player + 6), s16(u16(player + 0x40)),
            u8(player + 0x8c), string.format("%08x", u32(player + 0xe0))}, "\t") .. "\n")
        coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
        up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value(); jump:clear_value()
        samples:close(); dispatches:close(); qsound:close(); projectiles:close()
        score_writes:close(); result:close(); machine:exit()
    end
end)
