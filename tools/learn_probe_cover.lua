-- Learning probe: which ROM words the 68000 fetched in the retained Coffee Shop route.
-- Writes a compact list of executed 256-byte pages' words at exit to AVSP_LEARN_PROBE_OUT.
local cpu = manager.machine.devices[":maincpu"]
local ops = cpu.spaces["opcodes"]
local seen = {}
local path = os.getenv("AVSP_LEARN_PROBE_OUT")
learn_cover = ops:install_read_tap(0, 0xfffff, "learn_cover", function(offset) seen[offset & 0xffffe] = true end)
local n = 0
local function dump()
    local f = assert(io.open(path, "w"))
    for a in pairs(seen) do f:write(string.format("%x\n", a)) end
    f:close()
end
learn_cover_frame = emu.add_machine_frame_notifier(function()
    n = n + 1
    if n % 600 == 0 then dump() end
end)
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
