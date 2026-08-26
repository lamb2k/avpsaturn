-- ORACLE-11 post-boss stage-clear, results and stable Round 2 handoff census.
local machine=manager.machine
local cpu=machine.devices[":maincpu"]
local program=cpu.spaces["program"]
local root=assert(os.getenv("AVSP_ORACLE11_HANDOFF_ROOT"))
local frame=0
local first,last=13900,18000
local player,controller=0xff8380,0xffd180
local samples=assert(io.open(root.."/handoff_samples.tsv","w"))
local writes=assert(io.open(root.."/handoff_writes.tsv","w"))
samples:write("frame\troute_state\tclear_flag\tplayer_active\tplayer_state\tplayer_action\tplayer_facing\tplayer_x\tplayer_z\tplayer_health\tcontroller_active\tcontroller_class\tcontroller_state\tcontroller_phase\n")
writes:write("frame\tdomain\taddress\toffset\tpc\ta5\ta6\told\tdata\tmask\treturn0\treturn1\treturn2\n")
local function u8(a)return program:read_u8(a)end
local function u16(a)return program:read_u16(a)end
local function u32(a)return program:read_u32(a)end
local function s16(v)return v>=0x8000 and v-0x10000 or v end
local function stack()
 local sr=cpu.state["SR"].value&0xffff
 local sp=(sr&0x2000)~=0 and (cpu.state["SP"].value&0xffffff) or (cpu.state["USP"].value&0xffffff)
 return u32(sp)&0xffffff,u32(sp+4)&0xffffff,u32(sp+8)&0xffffff
end
local function emit_write(domain,base,offset,data,mask)
 if frame<first or frame>last then return end
 local r0,r1,r2=stack();writes:write(string.format("%d\t%s\t%06x\t%02x\t%06x\t%06x\t%06x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\n",
  frame,domain,offset&0xffffff,(offset-base)&0xff,cpu.state["PC"].value&0xffffff,
  cpu.state["A5"].value&0xffffff,cpu.state["A6"].value&0xffffff,u32(offset&0xfffffc),
  data&0xffffffff,mask&0xffffffff,r0,r1,r2))
end
oracle11_handoff_player=program:install_write_tap(player,player+0xbf,"oracle11_handoff_player",function(offset,data,mask)
 emit_write("player",player,offset,data,mask)
end)
oracle11_handoff_route=program:install_write_tap(0xff8008,0xff8009,"oracle11_handoff_route",function(offset,data,mask)
 emit_write("route-state",0xff8008,offset,data,mask)
end)
oracle11_handoff_clear=program:install_write_tap(0xff81f2,0xff81f3,"oracle11_handoff_clear",function(offset,data,mask)
 emit_write("clear-flag",0xff81f2,offset,data,mask)
end)
oracle11_handoff_countdown=program:install_write_tap(0xff837c,0xff837d,"oracle11_handoff_countdown",function(offset,data,mask)
 emit_write("transition-countdown",0xff837c,offset,data,mask)
end)
oracle11_handoff_frame=emu.add_machine_frame_notifier(function()
 frame=frame+1
 if frame>=first and frame<=last then samples:write(string.format("%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%02x\t%d\t%d\n",
  frame,u8(0xff8009),u8(0xff81f3),u8(player),u16(player+4),u16(player+6),u8(player+0x0f),
  s16(u16(player+0x10)),s16(u16(player+0x18)),s16(u16(player+0x40)),u8(controller),u8(controller+2),
  u16(controller+4),u16(controller+6)))end
 if frame==18000 then samples:close();writes:close()end
end)
dofile("tools/mame_capture_oracle11_player_audio.lua")
