-- ORACLE-11 exact route graphics-package write/caller and ownership capture.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local root = assert(os.getenv("AVSP_ORACLE11_LOAD_ROOT"))
local suppress_frame = tonumber(os.getenv("AVSP_ORACLE11_LOAD_SUPPRESS_FRAME") or "")
local suppress_region = os.getenv("AVSP_ORACLE11_LOAD_SUPPRESS_REGION") or ""
local frame, suppression_count = 0, 0
local targets = {[5565]=true,[5566]=true,[6200]=true,[12799]=true}
local windows = {}
for target in pairs(targets) do
    windows[target-1]=true; windows[target]=true; windows[target+1]=true
end
local regions = {
    {name="gfxram0", first=0x900000, last=0x90ffff},
    {name="gfxram1", first=0x910000, last=0x91ffff},
    {name="gfxram2", first=0x920000, last=0x92ffff},
}
local writes = assert(io.open(root .. "/gfx_writes.tsv", "w"))
local route = assert(io.open(root .. "/route_windows.tsv", "w"))
local result = assert(io.open(root .. "/load_result.tsv", "w"))
writes:write("frame\tregion\taddress\tpc\ta6\tsp\treturn0\treturn1\treturn2\tdata\tmask\tsuppressed\n")
route:write("frame\tg8009\tstate8002\tstate8004\tstate8006\tstate802c\tstate804a\tstate81c2\tplayer_active\tplayer_state\tplayer_phase\n")
result:write("suppression_count\tround2_route_state\tplayer_active\tplayer_state\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function install(region)
    _G["oracle11_load_" .. region.name] = program:install_write_tap(
        region.first, region.last, "oracle11_load_" .. region.name,
        function(offset, data, mask)
            if not windows[frame] then return end
            local sr = maincpu.state["SR"].value & 0xffff
            local system_sp = maincpu.state["SP"].value & 0xffffff
            local usp = maincpu.state["USP"].value & 0xffffff
            local sp = (sr & 0x2000) ~= 0 and system_sp or usp
            local suppressed = frame == suppress_frame and region.name == suppress_region
            if suppressed then suppression_count = suppression_count + 1 end
            writes:write(string.format("%d\t%s\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\t%d\n",
                frame, region.name, offset & 0xffffff,
                maincpu.state["PC"].value & 0xffffff,
                maincpu.state["A6"].value & 0xffffff, sp,
                u32(sp) & 0xffffff, u32(sp+4) & 0xffffff, u32(sp+8) & 0xffffff,
                data & 0xffffffff, mask & 0xffffffff, suppressed and 1 or 0))
            if suppressed then return program:read_u16(offset & 0xffffff) end
        end)
end
for _, region in ipairs(regions) do install(region) end

local function snapshot(target)
    for _, region in ipairs(regions) do
        local stream = assert(io.open(string.format("%s/%s_%05d.bin", root,
            region.name, target), "wb"))
        local bytes = {}
        for address = region.first, region.last do
            bytes[#bytes + 1] = string.char(u8(address))
            if #bytes == 4096 then stream:write(table.concat(bytes)); bytes = {} end
        end
        if #bytes > 0 then stream:write(table.concat(bytes)) end
        stream:close()
    end
end

oracle11_load_frame = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    if windows[frame] then
        route:write(string.format("%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",
            frame, u8(0xff8009), u16(0xff8002), u16(0xff8004),
            u16(0xff8006), u16(0xff802c), u16(0xff804a), u16(0xff81c2),
            u8(0xff8380), u16(0xff8384), u16(0xff8386)))
    end
    if targets[frame] then snapshot(frame) end
    if frame == 18000 then
        result:write(string.format("%d\t%d\t%d\t%d\n", suppression_count,
            u16(0xff8004), u8(0xff8380), u16(0xff8384)))
        writes:close(); route:close(); result:close()
    end
end)

-- Reuse the accepted source completion input; keep the QSound ledger compact.
dofile("tools/mame_capture_oracle11_player_audio.lua")
