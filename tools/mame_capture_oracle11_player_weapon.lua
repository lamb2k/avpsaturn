-- ORACLE-11 Predator Warrior weapon/projectile/resource causal probe.
-- Raw ledgers stay private under .deps/mame/oracle11_player_weapon_a.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local audio_cpu = machine.devices[":audiocpu"]
local audio_program = audio_cpu.spaces["program"]
local root = assert(os.getenv("AVSP_ORACLE11_WEAPON_ROOT"))
local variant = os.getenv("AVSP_ORACLE11_WEAPON_VARIANT") or "baseline"
local allowed = {
    baseline=true, resource_empty=true, b1_held=true,
    repeat_startup=true, repeat_active=true, repeat_recovery=true,
    special_ok=true, special_low_health=true, special_zero_health=true,
    target_inside=true, target_outside=true, allocation_unavailable=true,
    target_removed=true, lifetime_writer_suppressed=true,
    recharge_writer_frozen=true, pickup_actor_removed=true,
    projectile_class_removed=true, facing_reversed=true,
    damage_attack_class_2=true,
}
assert(allowed[variant], "unsupported weapon variant: " .. variant)

local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun, attack, jump = in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"]
local player = 0xff8380
local record4, record4_count, record4_stride = 0xff8680, 24, 0x80
local record12, record12_count, record12_stride = 0xff9580, 20, 0xc0
local record24, record24_count, record24_stride = 0xffb680, 32, 0x80
local record36, record36_count, record36_stride = 0xffd280, 64, 0x40
local first_frame, last_frame = 4380, 4760
local frame, sequence, qsound_latch = 0, 0, 0
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local writes = assert(io.open(root .. "/writes.tsv", "w"))
local actors = assert(io.open(root .. "/actors.tsv", "w"))
local qsound = assert(io.open(root .. "/qsound.tsv", "w"))
local damage = assert(io.open(root .. "/damage.tsv", "w"))
local impact_audio = assert(io.open(root .. "/impact_audio.tsv", "w"))
samples:write("frame\tvariant\tinput\taction\tinner\tfacing\tx\ty\tz\thealth\tresource\trecharge\tdepleted\taward_timer\tlatched\tanim\tr4_free\tr24_free\tr36_free\n")
writes:write("frame\tvariant\tsequence\tkind\taddress\toffset\tdata\tmask\tpc\tvalue\n")
actors:write("frame\tvariant\tkind\tslot\tactive\tclass\tstate\tinner\tmode\tpalette\tfacing\tx\ty\tz\tanim\tparent\tobject_or\thealth\n")
qsound:write("frame\tvariant\tpc\tport\tbyte\tregister\tvalue\n")
damage:write("frame\tvariant\tpc\tattacker\tdefender\tattack_record\ta5\tglobal_mode_word\tdefender_active8\tglobal_modifier244\tdefender_modifier73\tattacker_5e\troute_1ea\tdefender_57\tattack_selector\toffense_address\toffense_value\tdefense_address\tdefense_value\tmatrix_address\tdamage\thealth_before\thealth_after\n")
impact_audio:write("frame\tvariant\tselector_ff0eda\tclass3a_count\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function write_tap(first, last, name, kind)
    return program:install_write_tap(first, last, name, function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        if kind == "record12" and ((offset - record12) % record12_stride) == 0x40 and pc == 0x01d590 then
            local attacker = maincpu.state["A6"].value & 0xffffff
            local defender = maincpu.state["A1"].value & 0xffffff
            local attack_record = maincpu.state["A3"].value & 0xffffff
            local a5 = maincpu.state["A5"].value & 0xffffff
            local attacker_5e = u8(attacker + 0x5e)
            local route_1ea = u16(a5 + 0x1ea)
            local defender_57 = u8(defender + 0x57)
            local attack_selector = u8(attack_record + 9)
            local global_mode_word = u16(a5 - 0x6762)
            local defender_active8 = u8(defender + 8)
            local global_modifier244 = u8(a5 + 0x244)
            local defender_modifier73 = u8(defender + 0x73)
            local offense_address = 0x115420 + attacker_5e * 32 + route_1ea
            local offense_value = u8(offense_address)
            local defense_address = 0x114000 + defender_57 * 32 + route_1ea
            local defense_value = u8(defense_address)
            local matrix_address = 0x1142a0 + defense_value * 128 + ((offense_value + attack_selector) & 0xff)
            damage:write(string.format("%d\t%s\t%06x\t%06x\t%06x\t%06x\t%06x\t%04x\t%02x\t%02x\t%02x\t%02x\t%04x\t%02x\t%02x\t%06x\t%02x\t%06x\t%02x\t%06x\t%02x\t%04x\t%04x\n",
                frame, variant, pc, attacker, defender, attack_record, a5,
                global_mode_word, defender_active8, global_modifier244,
                defender_modifier73,
                attacker_5e, route_1ea, defender_57, attack_selector,
                offense_address, offense_value, defense_address, defense_value,
                matrix_address, u8(matrix_address), u16(offset), data & 0xffff))
        end
        sequence = sequence + 1
        writes:write(string.format("%d\t%s\t%d\t%s\t%06x\t%02x\t%04x\t%04x\t%06x\t%08x\n",
            frame, variant, sequence, kind, offset & 0xffffff,
            (offset - first) & 0xff, data & 0xffff, mask & 0xffff,
            pc, u32(offset & 0xfffffe)))
    end)
end
oracle11_weapon_taps = {
    write_tap(player, player + 0xff, "oracle11_weapon_player", "player"),
    write_tap(record4, record4 + record4_count * record4_stride - 1, "oracle11_weapon_r4", "record4"),
    write_tap(record12, record12 + record12_count * record12_stride - 1, "oracle11_weapon_r12", "record12"),
    write_tap(record24, record24 + record24_count * record24_stride - 1, "oracle11_weapon_r24", "record24"),
    write_tap(record36, record36 + record36_count * record36_stride - 1, "oracle11_weapon_r36", "record36"),
    write_tap(0xffee50, 0xffee8f, "oracle11_weapon_pool", "pool"),
}
oracle11_weapon_qsound = audio_program:install_write_tap(0xd000, 0xd002,
    "oracle11_weapon_qsound", function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local port, byte = offset & 0xffff, data & 0xff
        local register, value = "", ""
        if port == 0xd000 then qsound_latch = ((byte << 8) | (qsound_latch & 0xff)) & 0xffff
        elseif port == 0xd001 then qsound_latch = ((qsound_latch & 0xff00) | byte) & 0xffff
        else register = string.format("%02x", byte); value = string.format("%04x", qsound_latch) end
        qsound:write(string.format("%d\t%s\t%04x\t%04x\t%02x\t%s\t%s\n", frame, variant,
            audio_cpu.state["PC"].value & 0xffff, port, byte, register, value))
    end)

local function drive(field, enabled, bit, word)
    if enabled then field:set_value(1); return word | bit end
    field:clear_value(); return word
end
local function pulse(f, at, width) return f >= at and f < at + width end
local function schedule(f)
    local word = 0
    local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
    local start_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
    local gun_on = (f >= 1500 and f < 4200 and f % 90 < 5)
    local right_on = f >= 2600 and f < 4200
    local attack_on = f >= 2600 and f < 4200 and f % 310 < 7
    local jump_on = f >= 2600 and f < 4200 and f % 430 < 7
    if f >= 4380 then gun_on=false; attack_on=false; jump_on=false; right_on=false end
    if variant == "special_ok" or variant == "special_low_health" or variant == "special_zero_health" then
        gun_on = pulse(f, 4490, 5); attack_on = pulse(f, 4490, 5)
    else
        gun_on = pulse(f, 4490, 5)
        if variant == "b1_held" then gun_on = f >= 4490 and f < 4550 end
        if variant == "repeat_startup" then gun_on = pulse(f,4490,5) or pulse(f,4495,5) end
        if variant == "repeat_active" then gun_on = pulse(f,4490,5) or pulse(f,4510,5) end
        if variant == "repeat_recovery" then gun_on = pulse(f,4490,5) or pulse(f,4540,5) end
    end
    word=drive(coin,coin_on,1,word); word=drive(start,start_on,2,word)
    word=drive(left,false,4,word); word=drive(right,right_on,8,word)
    word=drive(gun,gun_on,16,word); word=drive(attack,attack_on,32,word)
    word=drive(jump,jump_on,64,word); word=drive(up,false,128,word); word=drive(down,false,256,word)
    return word
end

local function each_pool(base, count, stride, kind)
    for i=0,count-1 do
        local a=base+i*stride
        if u8(a) ~= 0 then
            actors:write(table.concat({frame,variant,kind,string.format("%06x",a),u8(a),
                string.format("%02x",u8(a+2)),u8(a+4),u8(a+5),
                u8(a+0xd),u8(a+0xe),u8(a+0xf),
                s16(u16(a+0x10)),s16(u16(a+0x14)),s16(u16(a+0x18)),
                string.format("%08x",u32(a+0x1c)),string.format("%04x",u16(a+0x26)),
                string.format("%04x",u16(a+0x2e)),s16(u16(a+0x40))},"\t").."\n")
        end
    end
end
local function first_target()
    for i=0,record12_count-1 do local a=record12+i*record12_stride
        if u8(a)~=0 and u8(a+2)==0x1f then return a end end
    return nil
end
local function first_projectile()
    for i=0,record4_count-1 do local a=record4+i*record4_stride
        if u8(a)~=0 and u8(a+2)==5 then return a end end
    return nil
end
local function apply_counterfactuals()
    if frame == 4488 or frame == 4489 then
        -- Establish the same stable, controllable player dispatch boundary in
        -- every experiment; the route up to this point remains byte-identical.
        program:write_u8(player+4,2); program:write_u8(player+5,0)
        program:write_u16(player+6,0); program:write_u8(player+0x5c,0)
        program:write_u8(player+0xad,0); program:write_u16(player+0x70,0)
        program:write_u16(player+0x40, 101); program:write_u16(player+0x42, 101)
        program:write_u8(player+0x8c, 64); program:write_u8(player+0x8d, 12); program:write_u8(player+0x8b, 0)
        if variant == "resource_empty" then program:write_u8(player+0x8c,0); program:write_u8(player+0x8b,1) end
        if variant == "special_low_health" then program:write_u16(player+0x40,5); program:write_u16(player+0x42,5) end
        if variant == "special_zero_health" then program:write_u16(player+0x40,0); program:write_u16(player+0x42,0) end
        if variant == "facing_reversed" then program:write_u8(player+0x0f,1) end
        if variant == "pickup_actor_removed" then
            program:write_u16(player+0xae,600)
            local a=record24
            program:write_u8(a,1); program:write_u8(a+2,0x54); program:write_u8(a+4,0); program:write_u16(a+0x28,player & 0xffff)
        end
    end
    local target=first_target()
    if target and frame >= 4488 and frame <= 4540 then
        if variant == "target_outside" then program:write_u16(target+0x10,(u16(player+0x10)+0x300)&0xffff)
        elseif variant == "target_inside" or variant == "target_removed" then
            local sign=u8(player+0xf)==0 and -1 or 1
            program:write_u16(target+0x10,(u16(player+0x10)+sign*48)&0xffff)
            program:write_u16(target+0x18,u16(player+0x18))
        end
    end
    if variant == "allocation_unavailable" and frame >= 4490 and frame <= 4530 then program:write_u8(0xffee7c,0) end
    if variant == "target_removed" and frame >= 4502 and target then program:write_u8(target,0) end
    local projectile=first_projectile()
    if projectile then
        if variant == "projectile_class_removed" then program:write_u8(projectile,0) end
        if variant == "damage_attack_class_2" then program:write_u8(projectile+0x5e,2) end
        if variant == "lifetime_writer_suppressed" and u8(projectile+4)>=4 then program:write_u8(projectile+4,2); program:write_u32(projectile+0x40,0) end
    end
    if variant == "recharge_writer_frozen" and frame >= 4490 then program:write_u8(player+0x8c,24); program:write_u8(player+0x8d,12) end
    if variant == "pickup_actor_removed" and frame >= 4489 then
        for i=0,record24_count-1 do local a=record24+i*record24_stride
            if u8(a)~=0 and u8(a+2)==0x54 then program:write_u8(a,0) end end
    end
end

oracle11_weapon_subscription=emu.add_machine_frame_notifier(function()
    frame=frame+1
    local word=schedule(frame)
    if frame>=4380 and variant ~= "special_zero_health" then
        program:write_u16(player+0x40, math.max(1,u16(player+0x40)))
    end
    apply_counterfactuals()
    if frame>=first_frame and frame<=last_frame then
        samples:write(table.concat({frame,variant,word,u16(player+6),u8(player+7),u8(player+0xf),
            s16(u16(player+0x10)),s16(u16(player+0x14)),s16(u16(player+0x18)),s16(u16(player+0x40)),
            u8(player+0x8c),u8(player+0x8d),u8(player+0x8b),u16(player+0xae),u8(player+0xad),
            string.format("%08x",u32(player+0x1c)),u8(0xffee7c),u8(0xffee89),u8(0xffee8f)},"\t").."\n")
        each_pool(record4,record4_count,record4_stride,"record4")
        each_pool(record12,record12_count,record12_stride,"record12")
        each_pool(record24,record24_count,record24_stride,"record24")
        each_pool(record36,record36_count,record36_stride,"record36")
        local class3a_count=0
        for i=0,record24_count-1 do
            local a=record24+i*record24_stride
            if u8(a)~=0 and u8(a+2)==0x3a then class3a_count=class3a_count+1 end
        end
        impact_audio:write(string.format("%d\t%s\t%02x\t%d\n",
            frame,variant,u8(0xff0eda),class3a_count))
    end
    if frame==last_frame then
        coin:clear_value();start:clear_value();left:clear_value();right:clear_value();up:clear_value();down:clear_value();gun:clear_value();attack:clear_value();jump:clear_value()
        samples:close();writes:close();actors:close();qsound:close();damage:close();impact_audio:close();machine:exit()
    end
end)
