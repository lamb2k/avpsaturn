-- ORACLE-11 audio-CPU shared-RAM reader and QSound-bus writer census.
-- The accepted full-route input schedule is supplied by the player-audio probe.
local machine = manager.machine
local audio_cpu = machine.devices[":audiocpu"]
local audio_program = audio_cpu.spaces["program"]
local root = assert(os.getenv("AVSP_ORACLE11_GLOBAL_AUDIO_ROOT"))
local first_frame, last_frame, frame = 1972, 18000, 0
local shared_counts, bus_counts = {}, {}
local shared_file = assert(io.open(root .. "/audio_shared_reads.tsv", "w"))
local bus_file = assert(io.open(root .. "/audio_bus_writers.tsv", "w"))
shared_file:write("address\tpc\tfirst_frame\tlast_frame\tcount\n")
bus_file:write("address\tpc\tfirst_frame\tlast_frame\tcount\n")

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
    end)

oracle11_global_audio_bus_write = audio_program:install_write_tap(
    0xd000, 0xd002, "oracle11_global_audio_bus_write",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local key = string.format("%04x:%04x", offset & 0xffff,
            audio_cpu.state["PC"].value & 0xffff)
        update(bus_counts, key)
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
        shared_file:close()
        bus_file:close()
    end
end)

-- Reuse the already accepted deterministic completion input and the complete
-- main-side dispatch/QSound ledger. This file only adds read-only audio-CPU taps.
dofile("tools/mame_capture_oracle11_player_audio.lua")
