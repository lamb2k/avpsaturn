-- Trace QSound bus transactions across the verified Stage 1 continuation.
-- This uses the same frame-4200 save and deterministic input schedule as the
-- CDDA reference capture. Output is private local evidence, never Saturn code.
local machine = manager.machine
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local left = in0["P1 Left"]
local right = in0["P1 Right"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]
local frame = 0
local base_frame = 4200
local final_frame = tonumber(os.getenv("AVSP_QSOUND_CAPTURE_END_FRAME") or "") or 14780
local state_loaded = false
local capture_root = os.getenv("AVSP_QSOUND_CAPTURE_ROOT") or
    ".deps/mame/stage1_qsound"
local isolate_qsound_voices = {}
local isolate_qsound_voice_text = os.getenv("AVSP_QSOUND_ISOLATE_VOICES") or ""
local qsound_isolation_enabled = isolate_qsound_voice_text ~= ""
local qsound_force_stop = os.getenv("AVSP_QSOUND_FORCE_STOP") == "1"
if isolate_qsound_voice_text ~= "none" then
    for token in string.gmatch(isolate_qsound_voice_text, "[^,]+") do
        local voice = assert(tonumber(token),
            "AVSP_QSOUND_ISOLATE_VOICES must contain integers or none")
        assert(voice >= 0 and voice < 16,
            "AVSP_QSOUND_ISOLATE_VOICES entries must be 0..15")
        isolate_qsound_voices[voice] = true
    end
end
local isolate_qsound_start_frame = tonumber(
    os.getenv("AVSP_QSOUND_ISOLATE_START_FRAME") or "")
local isolate_qsound_end_frame = tonumber(
    os.getenv("AVSP_QSOUND_ISOLATE_END_FRAME") or "")
local qsound_writes = assert(io.open(capture_root .. "/qsound_writes.tsv", "w"))
qsound_writes:write("frame\tpc\tport\tbyte\tregister\tvalue\n")
local qsound_data_latch = 0
local qsound_isolation_active = false

local audio_cpu = machine.devices[":audiocpu"]
local audio_program = audio_cpu.spaces["program"]
stage1_qsound_tap = audio_program:install_write_tap(
    0xd000, 0xd002, "stage1_qsound_bus",
    function(offset, data, mask)
        local port = offset & 0xffff
        local byte = data & 0xff
        local pc = audio_cpu.state["PC"].value
        if port == 0xd000 then
            qsound_data_latch = ((byte << 8) | (qsound_data_latch & 0xff)) & 0xffff
            qsound_writes:write(string.format(
                "%d\t%04x\t%04x\t%02x\t\t\n", base_frame + frame, pc, port, byte))
        elseif port == 0xd001 then
            qsound_data_latch = ((qsound_data_latch & 0xff00) | byte) & 0xffff
            qsound_writes:write(string.format(
                "%d\t%04x\t%04x\t%02x\t\t\n", base_frame + frame, pc, port, byte))
        else
            qsound_writes:write(string.format(
                "%d\t%04x\t%04x\t%02x\t%02x\t%04x\n",
                base_frame + frame, pc, port, byte, byte, qsound_data_latch))
            if qsound_isolation_active then
                local pcm_volume_voice = nil
                if byte <= 0x7f and (byte & 7) == 6 then
                    pcm_volume_voice = byte >> 3
                end
                local is_other_pcm_volume = pcm_volume_voice ~= nil and
                    not isolate_qsound_voices[pcm_volume_voice]
                local is_late_target_volume = pcm_volume_voice ~= nil and
                    isolate_qsound_voices[pcm_volume_voice] and
                    isolate_qsound_end_frame ~= nil and
                    base_frame + frame >= isolate_qsound_end_frame and
                    qsound_data_latch ~= 0
                local is_adpcm_volume = byte == 0xcd or byte == 0xd1 or
                    byte == 0xd5
                if is_other_pcm_volume or is_late_target_volume or
                    is_adpcm_volume then
                    return 0x07
                end
            end
        end
    end)

local function qsound_write(register, value)
    audio_program:write_u8(0xd001, value & 0xff)
    audio_program:write_u8(0xd000, (value >> 8) & 0xff)
    audio_program:write_u8(0xd002, register & 0xff)
end

local function begin_qsound_voice_isolation(absolute_frame)
    if not qsound_isolation_enabled then return end
    assert(isolate_qsound_start_frame ~= nil,
        "AVSP_QSOUND_ISOLATE_START_FRAME is required")
    assert(isolate_qsound_end_frame ~= nil,
        "AVSP_QSOUND_ISOLATE_END_FRAME is required")
    for voice = 0, 15 do
        qsound_write((voice << 3) + 6, 0)
    end
    for voice = 0, 2 do
        qsound_write(0xcd + (voice << 2), 0)
    end
    qsound_isolation_active = true
    print(string.format("AVSPU_STAGE1_QSOUND_ISOLATE voices=%s frame=%d",
        isolate_qsound_voice_text, absolute_frame))
end

local function end_qsound_voice_isolation(absolute_frame)
    if not qsound_isolation_enabled then return end
    for voice = 0, 15 do
        if isolate_qsound_voices[voice] then
            qsound_write((voice << 3) + 6, 0)
        end
    end
    print(string.format("AVSPU_STAGE1_QSOUND_STOP voices=%s frame=%d",
        isolate_qsound_voice_text, absolute_frame))
end

stage1_qsound_post_load_subscription = emu.add_machine_post_load_notifier(function()
    frame = 0
    state_loaded = true
    print("AVSPU_STAGE1_QSOUND loaded verified frame-4200 state")
end)

machine:load("avspu_stage1")

stage1_qsound_capture_subscription = emu.add_machine_frame_notifier(function()
    if not state_loaded then return end
    frame = frame + 1
    local absolute_frame = base_frame + frame

    if qsound_isolation_enabled and
        absolute_frame == isolate_qsound_start_frame then
        begin_qsound_voice_isolation(absolute_frame)
    end
    if qsound_isolation_enabled and qsound_force_stop and
        absolute_frame == isolate_qsound_end_frame then
        end_qsound_voice_isolation(absolute_frame)
    end

    if frame == 1 then right:set_value(1) end
    if frame % 45 == 0 then gun:set_value(1) end
    if frame % 45 == 7 then gun:clear_value() end
    if frame % 180 == 0 then attack:set_value(1) end
    if frame % 180 == 8 then attack:clear_value() end
    if frame % 240 == 0 then jump:set_value(1) end
    if frame % 240 == 8 then jump:clear_value() end
    if frame % 600 == 30 then coin:set_value(1) end
    if frame % 600 == 34 then coin:clear_value() end
    if frame % 600 == 90 then start:set_value(1) end
    if frame % 600 == 94 then start:clear_value() end

    if absolute_frame >= final_frame then
        left:clear_value()
        right:clear_value()
        gun:clear_value()
        attack:clear_value()
        jump:clear_value()
        coin:clear_value()
        start:clear_value()
        qsound_writes:close()
        print(string.format("AVSPU_STAGE1_QSOUND traced through frame %d",
            absolute_frame))
        machine:exit()
    end
end)
