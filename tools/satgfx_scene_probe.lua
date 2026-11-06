-- Lane satgfx: at chosen level 2 IRQ entries dump everything the Saturn graphics library reads, plus a MAME still.
-- Same entry point as tools/mame_golden.lua. Records: "SCN\0" u32 irq, 64K RAM, 0x700000 8K (write only, reads 0), 0x708000 8K (what the game and the library read), gfx RAM 0x30000,
-- CPS-A 0x40, CPS-B 0x40, output 0x10. Stays under E:\AvP\learning\lane-satgfx (ROM-derived).
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local prog = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"]
local screen = machine.screens[":screen"]
local out = assert(io.open(os.getenv("SATGFX_OUT"), "wb"))
local want, snapat = {}, {}
for s in string.gmatch(os.getenv("SATGFX_IRQS"), "%d+") do
    local n = tonumber(s); want[n] = true; snapat[n] = true; snapat[n + 1] = true; snapat[n + 2] = true
end
local function dump(base, n)
    local t = {}
    for i = 0, n - 2, 2 do t[#t + 1] = string.pack(">I2", prog:read_u16(base + i)) end
    out:write(table.concat(t))
end
local function share(name, n)
    local s = machine.memory.shares[name]
    for i = 0, n - 2, 2 do out:write(string.pack(">I2", s and s:read_u16(i) or 0)) end
end
local irq = 0
satgfx_tap = ops:install_read_tap(0xe0e, 0xe0f, "satgfx", function()
    if cpu.state["PC"].value ~= 0x68 then return end
    if snapat[irq] then screen:snapshot(string.format("s%05d.png", irq)) end
    if want[irq] then
        out:write(string.pack(">c4I4", "SCN\0", irq))
        dump(0xff0000, 0x10000); dump(0x700000, 0x2000); dump(0x708000, 0x2000); dump(0x900000, 0x30000)
        share(":cps_a_regs", 0x40); share(":cps_b_regs", 0x40); share(":output", 0x10)
        out:flush()
    end
    irq = irq + 1
end)
dofile("tools/mame_capture_oracle11_first_segment_progression.lua")
