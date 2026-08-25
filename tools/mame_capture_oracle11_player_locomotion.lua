-- ORACLE-11 bounded Predator Warrior locomotion/neutral/facing source probe.
-- Raw ledgers stay private under .deps/mame/oracle11_player_locomotion_*.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local screen = machine.screens[":screen"]
local root = assert(os.getenv("AVSP_ORACLE11_PLAYER_ROOT"))
local variant = os.getenv("AVSP_ORACLE11_PLAYER_VARIANT") or "baseline"
local allowed = {baseline=true, skip_right_edge=true, hold_right=true,
    reverse_without_neutral=true}
assert(allowed[variant], "unsupported player locomotion variant: " .. variant)

local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun, attack, jump = in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"]
local player = 0xff8380
local first_frame, last_frame = 2500, 2760
local frame, sequence = 0, 0
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local writes = assert(io.open(root .. "/player_writes.tsv", "w"))
local entries = assert(io.open(root .. "/player_entries.tsv", "w"))

samples:write("frame\tvariant\tinput_word\tactive\tinner\taction\tfacing\tx\ty\tz\tanim\ttimer\thex\n")
writes:write("frame\tvariant\tsequence\toffset\tdata\tmask\tpc\tvalue\n")
entries:write("frame\tvariant\tpc\ta6\tinput_word\taction\tfacing\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function actor_hex()
    local chunks = {}
    for offset = 0, 0xff do chunks[#chunks + 1] = string.format("%02x", u8(player + offset)) end
    return table.concat(chunks)
end

oracle11_player_writes = program:install_write_tap(
    player, player + 0xff, "oracle11_player_writes",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        sequence = sequence + 1
        writes:write(string.format("%d\t%s\t%d\t%02x\t%04x\t%04x\t%06x\t%08x\n",
            frame, variant, sequence, (offset - player) & 0xff,
            data & 0xffff, mask & 0xffff,
            maincpu.state["PC"].value & 0xffffff, u32(offset & 0xfffffe)))
    end)

local entry_pcs = { [0x0194e6]=true, [0x0197f2]=true, [0x0198b0]=true,
    [0x01997e]=true, [0x01a364]=true, [0x01a7e6]=true }
oracle11_player_entries = program:install_read_tap(
    0x0194e6, 0x01a7e7, "oracle11_player_entries",
    function(offset, data, mask)
        local pc = maincpu.state["PC"].value & 0xffffff
        if frame >= first_frame and frame <= last_frame and entry_pcs[pc] then
            entries:write(string.format("%d\t%s\t%06x\t%06x\t%04x\t%04x\t%d\n",
                frame, variant, pc, maincpu.state["A6"].value & 0xffffff,
                current_input or 0, u16(player + 6), u8(player + 0x0f)))
        end
        return data
    end)

local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
end

local function schedule(f)
    local word = 0
    local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
    local start_on = f >= 1200 and f <= 2400 and
        (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
    local gun_on = f >= 1500 and f <= 1895 and f % 90 < 5
    local right_on = f >= 2525 and f <= 2544
    local left_on = f >= 2585 and f <= 2604
    local up_on = f >= 2645 and f <= 2664
    local down_on = f >= 2705 and f <= 2724
    if variant == "skip_right_edge" and f == 2525 then right_on = false end
    if variant == "hold_right" then
        right_on = f >= 2525 and f <= 2570; left_on = false
    end
    if variant == "reverse_without_neutral" then
        right_on = f >= 2525 and f <= 2544
        left_on = f >= 2545 and f <= 2570
    end
    word = drive(coin, coin_on, 1, word); word = drive(start, start_on, 2, word)
    word = drive(left, left_on, 4, word); word = drive(right, right_on, 8, word)
    word = drive(gun, gun_on, 16, word); word = drive(attack, false, 32, word)
    word = drive(jump, false, 64, word); word = drive(up, up_on, 128, word)
    word = drive(down, down_on, 256, word)
    return word
end

local witnesses = { [2524]=true, [2527]=true, [2544]=true, [2547]=true,
    [2557]=true, [2587]=true, [2607]=true, [2617]=true,
    [2647]=true, [2667]=true, [2677]=true, [2707]=true,
    [2727]=true, [2737]=true }

local function capture(word)
    samples:write(table.concat({frame, variant, word, u8(player), u16(player + 4),
        u16(player + 6), u8(player + 0x0f), s16(u16(player + 0x10)),
        s16(u16(player + 0x14)), s16(u16(player + 0x18)),
        string.format("%08x", u32(player + 0x1c)), u16(player + 0x2a),
        actor_hex()}, "\t") .. "\n")
    if witnesses[frame] then screen:snapshot(string.format(root .. "/frames/%05d.png", frame)) end
end

oracle11_player_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    current_input = schedule(frame)
    if frame >= first_frame and frame <= last_frame then capture(current_input) end
    if frame == last_frame then
        coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
        up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value(); jump:clear_value()
        samples:close(); writes:close(); entries:close(); machine:exit()
    end
end)
