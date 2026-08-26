-- ORACLE-11 route-wide type-12 enemy state, presentation, RNG, and damage census.
local machine=manager.machine
local maincpu=machine.devices[":maincpu"]
local program=maincpu.spaces["program"]
local opcodes=maincpu.spaces["opcodes"]
local root=assert(os.getenv("AVSP_ORACLE11_ENEMY_ROOT"))
local frame=0
local first,last=1972,15193
local pool,stride,count=0xff9580,0xc0,20
local player=0xff8380
local samples=assert(io.open(root.."/enemy_samples.tsv","w"))
local entries=assert(io.open(root.."/enemy_entries.tsv","w"))
local writes=assert(io.open(root.."/enemy_writes.tsv","w"))
local rng=assert(io.open(root.."/enemy_rng.tsv","w"))
local damage=assert(io.open(root.."/player_damage.tsv","w"))
samples:write("frame\tslot\tclass\tstate\tphase\tfacing\tx\ty\tz\tanim\tassembly\thurt\tattack\ttimer\thealth\ttarget\n")
entries:write("frame\tclass\tentry\tslot\tstate\tphase\tfacing\tx\tz\tanim\tassembly\thurt\tattack\ttimer\thealth\ttarget\trng\treturn0\treturn1\treturn2\n")
writes:write("frame\tslot\tclass\tstate\tphase\toffset\tpc\ta6\told\tdata\tmask\treturn0\treturn1\treturn2\n")
rng:write("frame\tslot\tclass\tstate\tphase\tpc\tseed\treturn0\treturn1\treturn2\n")
damage:write("frame\tpc\towner_slot\towner_class\towner_state\towner_phase\towner_anim\told_health\tdata\tmask\treturn0\treturn1\treturn2\n")
local function u8(a)return program:read_u8(a)end
local function u16(a)return program:read_u16(a)end
local function u32(a)return program:read_u32(a)end
local function s16(v)return v>=0x8000 and v-0x10000 or v end
local function stack()
 local sr=maincpu.state["SR"].value&0xffff
 local sp=(sr&0x2000)~=0 and (maincpu.state["SP"].value&0xffffff) or (maincpu.state["USP"].value&0xffffff)
 return u32(sp)&0xffffff,u32(sp+4)&0xffffff,u32(sp+8)&0xffffff
end
local function owner(a6)
 if a6>=pool and a6<pool+count*stride and ((a6-pool)%stride)==0 and u8(a6+8)==12 then return true end
 return false
end
local function record(out,b,entry)
 local anim=u32(b+0x1c);local r0,r1,r2=stack()
 out:write(string.format("%d\t%02x\t%06x\t%06x\t%d\t%d\t%d\t%d\t%d\t%08x\t%08x\t%d\t%d\t%d\t%d\t%04x\t%04x\t%06x\t%06x\t%06x\n",
  frame,u8(b+2),entry,b,u16(b+4),u16(b+6),u8(b+0x0f),s16(u16(b+0x10)),s16(u16(b+0x18)),anim,
  anim~=0 and u32(anim+4) or 0,anim~=0 and u8(anim+8) or 0,anim~=0 and u8(anim+9) or 0,u16(b+0x2a),s16(u16(b+0x40)),u16(b+0x28),u16(0xff81a8),r0,r1,r2))
end
local dispatch={{0x03f09c,0},{0x0407b0,1},{0x04956c,6},{0x060532,0x1f}}
oracle11_enemy_entry_taps={}
for _,item in ipairs(dispatch) do local address,class=item[1],item[2]
 oracle11_enemy_entry_taps[#oracle11_enemy_entry_taps+1]=opcodes:install_read_tap(address,address+1,"oracle11_enemy_entry_"..class,function()
  if frame<first or frame>last then return end
  local b=maincpu.state["A6"].value&0xffffff
  if owner(b) and u8(b+2)==class then record(entries,b,address) end
 end)
end
oracle11_enemy_write=program:install_write_tap(pool,pool+count*stride-1,"oracle11_enemy_writes",function(offset,data,mask)
 if frame<first or frame>last then return end
 local relative=offset-pool;local b=pool+math.floor(relative/stride)*stride
 if not owner(b) then return end
 local inner=relative%stride;local r0,r1,r2=stack()
 writes:write(string.format("%d\t%06x\t%02x\t%d\t%d\t%02x\t%06x\t%06x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\n",
  frame,b,u8(b+2),u16(b+4),u16(b+6),inner,maincpu.state["PC"].value&0xffffff,maincpu.state["A6"].value&0xffffff,
  u32(offset&0xfffffc),data&0xffffffff,mask&0xffffffff,r0,r1,r2))
end)
oracle11_enemy_rng=opcodes:install_read_tap(0x017c5e,0x017c5f,"oracle11_enemy_rng",function()
 if frame<first or frame>last then return end
 local b=maincpu.state["A6"].value&0xffffff;if not owner(b) then return end
 local r0,r1,r2=stack();rng:write(string.format("%d\t%06x\t%02x\t%d\t%d\t%06x\t%04x\t%06x\t%06x\t%06x\n",
  frame,b,u8(b+2),u16(b+4),u16(b+6),maincpu.state["PC"].value&0xffffff,u16(0xff81a8),r0,r1,r2))
end)
oracle11_enemy_player_damage=program:install_write_tap(player+0x40,player+0x41,"oracle11_enemy_player_damage",function(offset,data,mask)
 if frame<first or frame>last then return end
 local b=maincpu.state["A6"].value&0xffffff;if not owner(b) then return end
 local anim=u32(b+0x1c);local r0,r1,r2=stack();damage:write(string.format("%d\t%06x\t%06x\t%02x\t%d\t%d\t%08x\t%d\t%08x\t%08x\t%06x\t%06x\t%06x\n",
  frame,maincpu.state["PC"].value&0xffffff,b,u8(b+2),u16(b+4),u16(b+6),anim,s16(u16(player+0x40)),data&0xffffffff,mask&0xffffffff,r0,r1,r2))
end)
oracle11_enemy_frame=emu.add_machine_frame_notifier(function()
 frame=frame+1
 if frame>=first and frame<=last then for i=0,count-1 do local b=pool+i*stride
  if u8(b)~=0 and u8(b+8)==12 then local anim=u32(b+0x1c)
   samples:write(string.format("%d\t%06x\t%02x\t%d\t%d\t%d\t%d\t%d\t%d\t%08x\t%08x\t%d\t%d\t%d\t%d\t%04x\n",
    frame,b,u8(b+2),u16(b+4),u16(b+6),u8(b+0x0f),s16(u16(b+0x10)),s16(u16(b+0x14)),s16(u16(b+0x18)),anim,
    anim~=0 and u32(anim+4) or 0,anim~=0 and u8(anim+8) or 0,anim~=0 and u8(anim+9) or 0,u16(b+0x2a),s16(u16(b+0x40)),u16(b+0x28))) end end end
 if frame==18000 then samples:close();entries:close();writes:close();rng:close();damage:close() end
end)
dofile("tools/mame_capture_oracle11_player_audio.lua")
