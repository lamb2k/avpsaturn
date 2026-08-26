-- ORACLE-11 route-wide player navigation, terrain body, and camera authority.
local machine=manager.machine
local maincpu=machine.devices[":maincpu"]
local program=maincpu.spaces["program"]
local cps_a=machine.memory.shares[":cps_a_regs"]
local root=assert(os.getenv("AVSP_ORACLE11_NAV_ROOT"))
local frame=0
local player=0xff8380
local actor_first,actor_stride,actor_count=0xff9580,0xc0,57
local samples=assert(io.open(root.."/navigation_samples.tsv","w"))
local writes=assert(io.open(root.."/navigation_writes.tsv","w"))
local bodies=assert(io.open(root.."/navigation_body_writes.tsv","w"))
local cameras=assert(io.open(root.."/camera_writes.tsv","w"))
samples:write("frame\troute\tplayer_active\tplayer_state\tplayer_phase\tplayer_x\tplayer_y\tplayer_z\tbound_x\tbound_z\tcamera_target\tscroll1_x\tscroll1_y\tscroll2_x\tscroll2_y\ttype20\n")
writes:write("frame\tfield\tpc\ta4\ta4_bytes\ta5\tbound_x\tbound_z\ta6\tsp\treturn0\treturn1\treturn2\tdata\tmask\n")
bodies:write("frame\tslot\tclass\tstate\tphase\toffset\tpc\tdata\tmask\n")
cameras:write("frame\tkind\taddress\tpc\ta6\tsp\treturn0\treturn1\treturn2\tdata\tmask\n")
local function u8(a)return program:read_u8(a)end
local function u16(a)return program:read_u16(a)end
local function u32(a)return program:read_u32(a)end
local function s16(v)return v>=0x8000 and v-0x10000 or v end
local function stack()
 local sr=maincpu.state["SR"].value&0xffff
 local sp=(sr&0x2000)~=0 and (maincpu.state["SP"].value&0xffffff) or (maincpu.state["USP"].value&0xffffff)
 return sp,u32(sp)&0xffffff,u32(sp+4)&0xffffff,u32(sp+8)&0xffffff
end
local function bytes(a,n)
 local out={};for i=0,n-1 do out[#out+1]=string.format("%02x",u8((a+i)&0xffffff)) end
 return table.concat(out)
end
oracle11_nav_player=program:install_write_tap(player,player+0xbf,"oracle11_nav_player",function(offset,data,mask)
 if frame<1972 or frame>15193 then return end
 local inner=(offset-player)&0xff
 if inner~=0x10 and inner~=0x14 and inner~=0x18 then return end
 local a4=maincpu.state["A4"].value&0xffffff;local a5=maincpu.state["A5"].value&0xffffff
 local sp,r0,r1,r2=stack()
 writes:write(string.format("%d\t%02x\t%06x\t%06x\t%s\t%06x\t%d\t%d\t%06x\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\n",
  frame,inner,maincpu.state["PC"].value&0xffffff,a4,bytes(a4,8),a5,s16(u16(a5+0x278)),s16(u16(a5+0x27c)),
  maincpu.state["A6"].value&0xffffff,sp,r0,r1,r2,data&0xffffffff,mask&0xffffffff))
end)
oracle11_nav_bodies=program:install_write_tap(actor_first,actor_first+actor_count*actor_stride-1,"oracle11_nav_bodies",function(offset,data,mask)
 if frame<1972 or frame>15193 then return end
 local relative=offset-actor_first;local index=math.floor(relative/actor_stride);local base=actor_first+index*actor_stride
 if index<0 or index>=actor_count or u8(base+8)~=20 then return end
 bodies:write(string.format("%d\t%06x\t%02x\t%d\t%d\t%02x\t%06x\t%08x\t%08x\n",frame,base,u8(base+2),u16(base+4),u16(base+6),relative%actor_stride,
  maincpu.state["PC"].value&0xffffff,data&0xffffffff,mask&0xffffffff))
end)
local function camera_tap(first,last,kind)
 return program:install_write_tap(first,last,"oracle11_nav_"..kind,function(offset,data,mask)
  if frame<1972 or frame>15193 then return end
  local sp,r0,r1,r2=stack();cameras:write(string.format("%d\t%s\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\n",
   frame,kind,offset&0xffffff,maincpu.state["PC"].value&0xffffff,maincpu.state["A6"].value&0xffffff,sp,r0,r1,r2,data&0xffffffff,mask&0xffffffff))
 end)
end
oracle11_nav_target=camera_tap(0xff8032,0xff8033,"camera_target")
oracle11_nav_cps=camera_tap(0x800110,0x80011f,"cps_scroll")
local function type20()
 local out={};for i=0,actor_count-1 do local b=actor_first+i*actor_stride
  if u8(b)~=0 and u8(b+8)==20 then out[#out+1]=string.format("%06x:%02x:%d:%d:%d:%d",b,u8(b+2),u16(b+4),u16(b+6),s16(u16(b+0x10)),s16(u16(b+0x18))) end end
 return table.concat(out,",")
end
oracle11_nav_frame=emu.add_machine_frame_notifier(function()
 frame=frame+1
 if frame>=1972 and frame<=15193 then local a5=0xff8000
  samples:write(table.concat({frame,u8(0xff8009),u8(player),u16(player+4),u16(player+6),s16(u16(player+0x10)),s16(u16(player+0x14)),s16(u16(player+0x18)),
   s16(u16(a5+0x278)),s16(u16(a5+0x27c)),u16(0xff8032),cps_a:read_u16(12),cps_a:read_u16(14),cps_a:read_u16(16),cps_a:read_u16(18),type20()},"\t").."\n") end
 if frame==18000 then samples:close();writes:close();bodies:close();cameras:close() end
end)
dofile("tools/mame_capture_oracle11_player_audio.lua")
