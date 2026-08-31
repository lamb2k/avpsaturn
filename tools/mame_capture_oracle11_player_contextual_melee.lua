-- Bounded ORACLE-11 corrective probe for Predator Warrior contextual Button2.
-- The accepted Coffee Shop scene capture remains the route/input authority;
-- this wrapper adds only the player +0x5a target edge and 0x1400/0x1402
-- program trace required by REIMPLEMENT-13.
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")

local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local opcodes = maincpu.spaces["opcodes"]
local root = assert(os.getenv("AVSP_ORACLE11_CONTEXTUAL_MELEE_ROOT"))
local variant = os.getenv("AVSP_ORACLE11_CONTEXTUAL_MELEE_VARIANT") or "baseline"
local mutate_target_writer = variant == "target_writer_zero"
assert(variant == "baseline" or mutate_target_writer,
    "unsupported contextual-melee variant: " .. variant)

local player = 0xff8380
local frame = 0
local target_writer_mutations = 0
local trace = assert(io.open(root .. "/player_contextual_melee.tsv", "w"))
local writes = assert(io.open(root .. "/player_contextual_melee_writes.tsv", "w"))
local result = assert(io.open(root .. "/player_contextual_melee_result.tsv", "w"))

trace:write("frame\tevent\tpc\tstate\tsubstate\ttarget_low\ttarget_slot\t" ..
    "target_active\ttarget_type\ttarget_class\ttarget_state\ttarget_substate\t" ..
    "player_x_fp\tplayer_y_fp\tfacing\tanimation_record\tanimation_timer\t" ..
    "animation_branch\taction_timer\tstep81\tevent80\tevent25\tguard6e\t" ..
    "toggle87\tinput_current\tinput_previous\td0\td1\td2\td3\ta0\ta1\t" ..
    "a2\ta3\ta4\ta5\ta6\tmutated\n")
writes:write("frame\tpc\toffset\tstate\tsubstate\ttarget_low_before\t" ..
    "data\tmask\tmutated\n")
result:write("variant\ttarget_writer_mutations\tfinal_route\tfinal_player_state\t" ..
    "final_player_substate\n")

local function u8(address) return program:read_u8(address) end
local function u16(address) return program:read_u16(address) end
local function u32(address) return program:read_u32(address) end
local function s16(value)
    return value >= 0x8000 and value - 0x10000 or value
end

local function target_slot()
    local low = u16(player + 0x5a)
    if low == 0 then return low, 0 end
    return low, 0xff0000 | low
end

local function emit(event, pc, mutated)
    if frame < 3380 or frame > 3760 then return end
    local low, target = target_slot()
    local active, record_type, class = 0, 0, 0
    local state, substate = 0, 0
    if target ~= 0 then
        active = u8(target)
        record_type = u8(target + 8)
        class = u8(target + 2)
        state = u16(target + 4)
        substate = u16(target + 6)
    end
    trace:write(string.format(
        "%d\t%s\t%06x\t%04x\t%04x\t%04x\t%06x\t%d\t%d\t%02x\t" ..
        "%04x\t%04x\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%04x\t%02x\t" ..
        "%02x\t%02x\t%02x\t%02x\t%04x\t%04x\t%08x\t%08x\t%08x\t" ..
        "%08x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%d\n",
        frame, event, pc, u16(player + 4), u16(player + 6), low, target,
        active, record_type, class, state, substate, u32(player + 0x10),
        u32(player + 0x14), u8(player + 0x0f), u32(player + 0x1c),
        u16(player + 0x0a), s16(u16(player + 0x24)), u16(player + 0x2a),
        u8(player + 0x81), u8(player + 0x80), u8(player + 0x25),
        u8(player + 0x6e), u8(player + 0x87), u16(player + 0xee),
        u16(player + 0xef), maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        maincpu.state["A0"].value & 0xffffff,
        maincpu.state["A1"].value & 0xffffff,
        maincpu.state["A2"].value & 0xffffff,
        maincpu.state["A3"].value & 0xffffff,
        maincpu.state["A4"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff,
        maincpu.state["A6"].value & 0xffffff, mutated and 1 or 0))
end

oracle11_contextual_melee_target_writes = program:install_write_tap(
    player + 0x5a, player + 0x5b, "oracle11_contextual_melee_target_writes",
    function(offset, data, mask)
        if frame > 3760 then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        local mutated = mutate_target_writer and pc == 0x0212ce
        writes:write(string.format(
            "%d\t%06x\t%06x\t%04x\t%04x\t%04x\t%08x\t%08x\t%d\n",
            frame, pc, offset,
            u16(player + 4), u16(player + 6), u16(player + 0x5a),
            data & 0xffffffff, mask & 0xffffffff, mutated and 1 or 0))
        if mutated then
            target_writer_mutations = target_writer_mutations + 1
            return u16(player + 0x5a)
        end
    end)

local program_pcs = {
    0x01a6dc, 0x01a6e4, 0x01a6ea,
    0x022ed6, 0x022eda, 0x022ef6, 0x022f02, 0x022f0c,
    0x022f1c, 0x022f24, 0x022f42, 0x022f4e, 0x022f54,
    0x022f5c, 0x022f62, 0x022f68, 0x022f7a, 0x022f84,
    0x022f8c, 0x022f90, 0x022f96,
}
oracle11_contextual_melee_pc_taps = {}
for _, pc in ipairs(program_pcs) do
    oracle11_contextual_melee_pc_taps[#oracle11_contextual_melee_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_contextual_melee_%06x", pc),
        function()
            emit(pc == 0x01a6e4 and "target_guard_read" or "dispatch",
                 pc, false)
        end)
end

oracle11_contextual_melee_frame = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    if frame >= 3380 and frame <= 3760 then
        emit("sample", 0, false)
    end
    if frame == 5566 then
        result:write(string.format("%s\t%d\t%d\t%04x\t%04x\n",
            variant, target_writer_mutations, u16(0xff8008), u16(player + 4),
            u16(player + 6)))
        trace:close()
        writes:close()
        result:close()
    end
end)
