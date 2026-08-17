-- Probe the CPS2 actor structure to locate its animation-script pointer.
--
-- The port currently rebuilds animations by capturing finished frames off the
-- screen. The game itself drives them from tables in ROM, so the scalable path
-- is to read those tables directly. This probe is the first step: dump each
-- tracked actor's struct every frame and record which fields change, so the
-- layout can be labelled and any field holding a ROM address can be found.
--
-- The three boss-room actors sit at FFA240, FFA300 and FFA3C0, which is a
-- 0xC0 stride, so the struct is assumed to be 192 bytes. Nothing here writes
-- to the machine; it only reads and records.
local machine = manager.machine
local screen = machine.screens[":screen"]
local cpu = machine.devices[":maincpu"]
local program = cpu.spaces["program"]
local capture_root = ".deps/mame/actorprobe"

local ACTOR_STRIDE = 0xc0
local ACTORS = { 0xffa240, 0xffa300, 0xffa3c0 }
local FIRST_SAMPLE = 1
local LAST_SAMPLE = 240

local state_loaded = false
local frame = 0
local files = {}

for index, base in ipairs(ACTORS) do
    local file = assert(io.open(string.format(
        capture_root .. "/actor_%06x.tsv", base), "w"))
    local header = { "frame" }
    for offset = 0, ACTOR_STRIDE - 2, 2 do
        header[#header + 1] = string.format("w%02x", offset)
    end
    file:write(table.concat(header, "\t") .. "\n")
    files[index] = file
end

local function dump_actor(index, base, sample_frame)
    local row = { tostring(sample_frame) }
    for offset = 0, ACTOR_STRIDE - 2, 2 do
        row[#row + 1] = string.format("%04x", program:read_u16(base + offset))
    end
    files[index]:write(table.concat(row, "\t") .. "\n")
end

actor_probe_post_load = emu.add_machine_post_load_notifier(function()
    if state_loaded then return end
    frame = 0
    state_loaded = true
end)

local function finish()
    for _, file in ipairs(files) do
        file:flush()
        file:close()
    end
    machine:exit()
end

-- Guard against the save state never loading. Without this the run has no
-- exit path and MAME sits there forever.
local boot_frames = 0

actor_probe_subscription = emu.add_machine_frame_notifier(function()
    if not state_loaded then
        boot_frames = boot_frames + 1
        if boot_frames > 600 then
            print("ACTOR_PROBE_ERROR state never loaded")
            finish()
        end
        return
    end
    frame = frame + 1
    if frame > LAST_SAMPLE then
        finish()
        return
    end
    if frame < FIRST_SAMPLE then return end
    for index, base in ipairs(ACTORS) do
        dump_actor(index, base, frame)
    end
    for _, file in ipairs(files) do file:flush() end
    if frame % 60 == 0 then
        screen:snapshot(string.format("actorprobe/probe_%05d.png", frame))
    end
end)

machine:load("avspu_stage1_boss_12660")
