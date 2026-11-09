-- Log writes to a work RAM range with the writer's pc. AVSP_WATCH="start end" hex, output AVSP_LEARN_PROBE_OUT.
local cpu = manager.machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local out = assert(io.open(os.getenv("AVSP_LEARN_PROBE_OUT"), "w"))
local a, b = os.getenv("AVSP_WATCH"):match("(%x+) (%x+)")
a, b = tonumber(a, 16), tonumber(b, 16)
local n = 0
learn_w = prog:install_write_tap(a, b, "learn_watch", function(off, data, mask)
    n = n + 1
    out:write(string.format("%x %x %x pc %x\n", off, data, mask, cpu.state["PC"].value)); out:flush()
end)
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
