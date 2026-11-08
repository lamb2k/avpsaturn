-- lane avp-wolverine: player-block interface census (docs/guests/PLAYER_INTERFACE.md). Runs pal_census.lua's whole-game walk under MAME 0.289
-- (avspu) with memory taps: every read and write of player 1's block (ff8380..ff847f), keyed by field offset, access, program counter, and
-- the running actor (a6; a6 = ff8380 is the player's own update). Also every write player 1's own code makes outside its block.
-- Output AM_OUT/iface.tsv: kind  off_or_addr  pc  a6  a6_tag  a6_class  count. Health is held by the walk, so dying and continue are not seen.
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local root = assert(os.getenv("AM_OUT"))
local PC, A6 = cpu.state["PC"], cpu.state["A6"]
local B = 0xff8380
local C = {}
local busy = false
local function rec(kind, a)
    if busy then return end
    busy = true
    local a6 = A6.value & 0xffffff
    local tag, cls = 0, 0
    if a6 >= 0xff0000 then tag, cls = prog:read_u8(a6 + 8), prog:read_u8(a6 + 2) end
    local k = string.format("%s\t%x\t%x\t%x\t%02x\t%02x", kind, a, PC.value & 0xffffff, a6, tag, cls)
    C[k] = (C[k] or 0) + 1
    busy = false
end
census_r = prog:install_read_tap(B, B + 0xff, "wvr", function(o, d, m) rec("r", o - B + ((m & 0xff00) == 0 and 1 or 0)) end)
census_w = prog:install_write_tap(B, B + 0xff, "wvw", function(o, d, m) rec("w", o - B + ((m & 0xff00) == 0 and 1 or 0)) end)
census_o = prog:install_write_tap(0xff0000, 0xffffff, "wvo", function(o, d, m)
    if (o >= B and o <= B + 0xff) or busy then return end
    if (A6.value & 0xffffff) == B then rec("out", o + ((m & 0xff00) == 0 and 1 or 0)) end
end)
local function save()
    local f = assert(io.open(root .. "/iface.tsv", "w"))
    for k, n in pairs(C) do f:write(k, "\t", n, "\n") end
    f:close()
end
census_stop = emu.add_machine_stop_notifier(save)
census_t = emu.add_machine_frame_notifier(function() if machine.screens[":screen"]:frame_number() % 18000 == 0 then save() end end)
dofile((os.getenv("WV_HERE") or ".") .. "/pal_census.lua")
