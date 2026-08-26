-- Compact causal control for one global main-side audio trigger group.
local machine = manager.machine
local audio_cpu = machine.devices[":audiocpu"]
local audio_program = audio_cpu.spaces["program"]
local root = assert(os.getenv("AVSP_ORACLE11_GLOBAL_AUDIO_MUTATION_ROOT"))
local first_frame = 1972
local last_frame = tonumber(os.getenv("AVSP_ORACLE11_PLAYER_AUDIO_LAST_FRAME") or "") or 18000
local frame = 0
local latch = 0
local stream = assert(io.open(root .. "/audio_bus_stream.bin", "wb"))

oracle11_global_audio_mutation_bus = audio_program:install_write_tap(
    0xd000, 0xd002, "oracle11_global_audio_mutation_bus",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local port, byte = offset & 0xffff, data & 0xff
        if port == 0xd001 then
            latch = ((latch & 0xff00) | byte) & 0xffff
        elseif port == 0xd000 then
            latch = ((byte << 8) | (latch & 0xff)) & 0xffff
        else
            stream:write(string.char((frame >> 8) & 0xff, frame & 0xff,
                byte, (latch >> 8) & 0xff, latch & 0xff))
        end
    end)

oracle11_global_audio_mutation_frame = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    if frame == last_frame then stream:close() end
end)

dofile("tools/mame_capture_oracle11_player_audio.lua")
