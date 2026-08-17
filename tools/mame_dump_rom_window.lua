-- Dump a window of the CPS2 68000 program ROM.
--
-- The actor probe found a per-actor field walking a narrow ROM range while the
-- boss animates, which is the signature of an animation-script pointer. This
-- dumps that region so the script format can be decoded and the animation
-- tables read directly out of the ROM instead of recaptured off the screen.
local machine = manager.machine
local program = machine.devices[":maincpu"].spaces["program"]
local first = tonumber(os.getenv("AVSP_ROM_FIRST") or "0x13c000")
local last = tonumber(os.getenv("AVSP_ROM_LAST") or "0x13d800")
local path = os.getenv("AVSP_ROM_OUT") or ".deps/mame/actorprobe/rom_window.bin"

rom_window_subscription = emu.add_machine_frame_notifier(function()
    local file = assert(io.open(path, "wb"))
    local bytes = {}
    for address = first, last - 1 do
        bytes[#bytes + 1] = string.char(program:read_u8(address))
    end
    file:write(table.concat(bytes))
    file:close()
    print(string.format("ROM_WINDOW_WRITTEN %06x..%06x", first, last))
    machine:exit()
end)
