-- Lane satint: program-space data reads over the retained Round 1 route, as a bitmap of ROM words, to size what the cart must hold.
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local root = assert(os.getenv("SATINT_CENSUS_OUT"))
local seen = {}
local n = 0
local function dump()
    local h = assert(io.open(root .. "/reads.txt", "w"))
    for a in pairs(seen) do h:write(string.format("%x\n", a)) end
    h:close()
end
satint_rd = prog:install_read_tap(0, 0x1fffff, "satint_rd", function(o) seen[o & 0x1ffffe] = true end)
satint_f = emu.add_machine_frame_notifier(function() n = n + 1; if n % 1000 == 0 then dump() end end)
dofile("tools/mame_capture_oracle11_player_audio.lua")
