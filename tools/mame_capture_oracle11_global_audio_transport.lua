-- ORACLE-11 audio-CPU shared-RAM reader and QSound-bus writer census.
-- The accepted full-route input schedule is supplied by the player-audio probe.
local machine = manager.machine
local audio_cpu = machine.devices[":audiocpu"]
local audio_program = audio_cpu.spaces["program"]
local root = assert(os.getenv("AVSP_ORACLE11_GLOBAL_AUDIO_ROOT"))
local first_frame, last_frame, frame = 1972, 18000, 0
local shared_counts, bus_counts, queue_counts, state_write_counts = {}, {}, {}, {}
local shared_sequence, dispatch_sequence = 0, 0
local shared_bytes = {}
local internal_queue_read = false
local shared_file = assert(io.open(root .. "/audio_shared_reads.tsv", "w"))
local bus_file = assert(io.open(root .. "/audio_bus_writers.tsv", "w"))
local queue_file = assert(io.open(root .. "/audio_queue_reads.tsv", "w"))
local state_file = assert(io.open(root .. "/audio_state_writers.tsv", "w"))
local commands_file = assert(io.open(root .. "/audio_shared_commands.tsv", "w"))
local dispatch_file = assert(io.open(root .. "/audio_command_dispatches.tsv", "w"))
shared_file:write("address\tpc\tfirst_frame\tlast_frame\tcount\n")
bus_file:write("address\tpc\tfirst_frame\tlast_frame\tcount\n")
queue_file:write("address\tpc\tfirst_frame\tlast_frame\tcount\n")
state_file:write("address\tpc\tfirst_frame\tlast_frame\tcount\n")
commands_file:write("frame\tsequence\tbytes\n")
dispatch_file:write("frame\tsequence\tqueue_address\tbytes\n")

local function update(counts, key)
    local row = counts[key]
    if row then
        row.last = frame
        row.count = row.count + 1
    else
        counts[key] = {first=frame, last=frame, count=1}
    end
end

oracle11_global_audio_shared_read = audio_program:install_read_tap(
    0xc000, 0xcfff, "oracle11_global_audio_shared_read",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local key = string.format("%04x:%04x", offset & 0xffff,
            audio_cpu.state["PC"].value & 0xffff)
        update(shared_counts, key)
        local address = offset & 0xffff
        local pc = audio_cpu.state["PC"].value & 0xffff
        if pc == 0x0066 and address >= 0xc000 and address <= 0xc00f then
            shared_bytes[address - 0xc000] = data & 0xff
            if address == 0xc00f then
                local payload = {}
                for index = 0, 15 do
                    payload[#payload + 1] = string.format("%02x", shared_bytes[index])
                end
                shared_sequence = shared_sequence + 1
                commands_file:write(string.format("%d\t%d\t%s\n", frame,
                    shared_sequence, table.concat(payload)))
            end
        end
    end)

oracle11_global_audio_bus_write = audio_program:install_write_tap(
    0xd000, 0xd002, "oracle11_global_audio_bus_write",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local key = string.format("%04x:%04x", offset & 0xffff,
            audio_cpu.state["PC"].value & 0xffff)
        update(bus_counts, key)
    end)

oracle11_global_audio_queue_read = audio_program:install_read_tap(
    0xf100, 0xf4ff, "oracle11_global_audio_queue_read",
    function(offset, data, mask)
        if internal_queue_read then return end
        if frame < first_frame or frame > last_frame then return end
        local address = offset & 0xffff
        local pc = audio_cpu.state["PC"].value & 0xffff
        local key = string.format("%04x:%04x", address, pc)
        update(queue_counts, key)
        if pc == 0x01dc and address >= 0xf100 and
            ((address - 0xf100) & 0x0f) == 0 then
            internal_queue_read = true
            local payload = {}
            for index = 0, 15 do
                payload[#payload + 1] = string.format("%02x",
                    audio_program:read_u8(address + index))
            end
            internal_queue_read = false
            dispatch_sequence = dispatch_sequence + 1
            dispatch_file:write(string.format("%d\t%d\t%04x\t%s\n", frame,
                dispatch_sequence, address, table.concat(payload)))
        end
    end)

oracle11_global_audio_state_write = audio_program:install_write_tap(
    0xf000, 0xffff, "oracle11_global_audio_state_write",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local key = string.format("%04x:%04x", offset & 0xffff,
            audio_cpu.state["PC"].value & 0xffff)
        update(state_write_counts, key)
    end)

local function flush(counts, stream)
    local keys = {}
    for key in pairs(counts) do keys[#keys + 1] = key end
    table.sort(keys)
    for _, key in ipairs(keys) do
        local address, pc = string.match(key, "([^:]+):([^:]+)")
        local row = counts[key]
        stream:write(string.format("%s\t%s\t%d\t%d\t%d\n",
            address, pc, row.first, row.last, row.count))
    end
end

oracle11_global_audio_frame = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    if frame == last_frame then
        flush(shared_counts, shared_file)
        flush(bus_counts, bus_file)
        flush(queue_counts, queue_file)
        flush(state_write_counts, state_file)
        shared_file:close()
        bus_file:close()
        queue_file:close()
        state_file:close()
        commands_file:close()
        dispatch_file:close()
    end
end)

-- Reuse the already accepted deterministic completion input and the complete
-- main-side dispatch/QSound ledger. This file only adds read-only audio-CPU taps.
dofile("tools/mame_capture_oracle11_player_audio.lua")
