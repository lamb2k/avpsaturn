-- Dump the CPS2 main CPU's data and opcode spaces for a private disassembly
-- probe. MAME exposes the encrypted data view and the decrypted fetch view as
-- separate address spaces on the 68000 device.
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local first = tonumber(os.getenv("AVSP_ROM_FIRST") or "0x16000")
local last = tonumber(os.getenv("AVSP_ROM_LAST") or "0x17000")
local function dump_space(name, space)
    local output = assert(io.open(os.getenv("AVSP_ROM_OUT_" .. name), "wb"))
    local bytes = {}
    for address = first, last - 1 do
        bytes[#bytes + 1] = string.char(space:read_u8(address))
        if #bytes == 1024 then
            output:write(table.concat(bytes))
            bytes = {}
        end
    end
    if #bytes > 0 then output:write(table.concat(bytes)) end
    output:close()
end

emu.add_machine_frame_notifier(function()
    dump_space("PROGRAM", cpu.spaces["program"])
    dump_space("OPCODES", cpu.spaces["opcodes"])
    print(string.format("CODE_SPACES_WRITTEN %06x..%06x", first, last))
    machine:exit()
end)
