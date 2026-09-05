-- Bounded ORACLE-11 corrective capture for the first recurring Round 1
-- class-0x1f spawn.  This records the controller/initializer transaction
-- around source writer 0x028a3e without widening the route census.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local opcodes = maincpu.spaces["opcodes"]
local root = assert(os.getenv("AVSP_ORACLE11_PROGRESSION_ROOT"))
local suppress_spawn = os.getenv("AVSP_ORACLE11_PROGRESSION_SUPPRESS_SPAWN") == "1"
local suppress_guard = os.getenv("AVSP_ORACLE11_PROGRESSION_SUPPRESS_GUARD") == "1"
local capture_lifecycle = os.getenv("AVSP_ORACLE11_PROGRESSION_LIFECYCLE") == "1"
local suppress_lifecycle = os.getenv("AVSP_ORACLE11_PROGRESSION_SUPPRESS_LIFECYCLE") == "1"
local capture_scene = os.getenv("AVSP_ORACLE11_COFFEE_SHOP_SCENE") == "1"
local suppress_action4_timer =
    os.getenv("AVSP_ORACLE11_SUPPRESS_ACTION4_TIMER") == "1"
local suppress_coffee_stage_rng =
    os.getenv("AVSP_ORACLE11_SUPPRESS_COFFEE_STAGE_RNG") == "1"
local capture_last_frame = capture_scene and 5566 or 4100
local suppress_transition_pc = tonumber(
    os.getenv("AVSP_ORACLE11_PROGRESSION_SUPPRESS_TRANSITION_PC") or "", 16)
local suppress_type4_class03_pc = tonumber(
    os.getenv("AVSP_ORACLE11_SUPPRESS_TYPE4_CLASS03_PC") or "", 16)
local suppress_type36_pc = tonumber(
    os.getenv("AVSP_ORACLE11_SUPPRESS_TYPE36_PC") or "", 16)
local suppress_type36_pc2 = tonumber(
    os.getenv("AVSP_ORACLE11_SUPPRESS_TYPE36_PC2") or "", 16)
local suppress_type36_class = tonumber(
    os.getenv("AVSP_ORACLE11_SUPPRESS_TYPE36_CLASS") or "", 16)
local suppress_scene_pair_type = tonumber(
    os.getenv("AVSP_ORACLE11_SUPPRESS_SCENE_PAIR_TYPE") or "")
local suppress_scene_pair_class = tonumber(
    os.getenv("AVSP_ORACLE11_SUPPRESS_SCENE_PAIR_CLASS") or "", 16)
local suppress_obstacle_transition =
    os.getenv("AVSP_ORACLE11_SUPPRESS_OBSTACLE_TRANSITION") == "1"
local capture_collision_guard =
    os.getenv("AVSP_ORACLE11_COLLISION_GUARD_CAPTURE") == "1"
local mutate_collision_guard =
    os.getenv("AVSP_ORACLE11_COLLISION_GUARD_MUTATE") == "1"
local capture_class1f_hit =
    os.getenv("AVSP_ORACLE11_CLASS1F_HIT_CAPTURE") == "1"
local mutate_class1f_hit_selector =
    os.getenv("AVSP_ORACLE11_MUTATE_CLASS1F_HIT_SELECTOR") == "1"
local suppress_resource_pc = tonumber(
    os.getenv("AVSP_ORACLE11_SUPPRESS_RESOURCE_PC") or "", 16)
local capture_controller_substate =
    os.getenv("AVSP_ORACLE11_CONTROLLER_SUBSTATE_CAPTURE") == "1"
local capture_component20_phase =
    os.getenv("AVSP_ORACLE11_COMPONENT20_PHASE_CAPTURE") == "1"
local class0f_state_counterfactual =
    os.getenv("AVSP_ORACLE11_CLASS0F_STATE_COUNTERFACTUAL") == "1"
local class0f_state_counterfactual_count = 0
local class0a_variant_counterfactual =
    os.getenv("AVSP_ORACLE11_CLASS0A_VARIANT_COUNTERFACTUAL") == "1"
local class0a_variant_counterfactual_count = 0
local class0a_saved_variant = 0
local class0a_saved_camera_x = 0
local class0a_counterfactual_active = false
class00_init_counterfactual =
    os.getenv("AVSP_ORACLE11_CLASS00_INIT_COUNTERFACTUAL") == "1"
class00_init_counterfactual_count = 0
class00_counterfactual_active = false
local capture_terrain_patch =
    os.getenv("AVSP_ORACLE11_TERRAIN_PATCH_CAPTURE") == "1"
local capture_terrain_stream =
    os.getenv("AVSP_ORACLE11_TERRAIN_STREAM_CAPTURE") == "1"
local mutate_terrain_patch =
    os.getenv("AVSP_ORACLE11_TERRAIN_PATCH_MUTATE") == "1"
local terrain_patch_mutation_pc = tonumber(
    os.getenv("AVSP_ORACLE11_TERRAIN_PATCH_MUTATION_PC") or "", 16)
local capture_class1f_action4_guard =
    os.getenv("AVSP_ORACLE11_CLASS1F_ACTION4_GUARD_CAPTURE") == "1"
local capture_class1f_inner8_group =
    os.getenv("AVSP_ORACLE11_CLASS1F_INNER8_GROUP_CAPTURE") == "1"
local mutate_class1f_inner8_group =
    os.getenv("AVSP_ORACLE11_CLASS1F_INNER8_GROUP_MUTATE") == "1"
local capture_class1f_action0c =
    os.getenv("AVSP_ORACLE11_CLASS1F_ACTION0C_CAPTURE") == "1"
local mutate_class1f_action0c =
    os.getenv("AVSP_ORACLE11_CLASS1F_ACTION0C_MUTATE") == "1"
local capture_player_hit =
    os.getenv("AVSP_ORACLE11_PLAYER_HIT_CAPTURE") == "1"
local mutate_player_hit_body =
    os.getenv("AVSP_ORACLE11_PLAYER_HIT_MUTATE_BODY") == "1"
local suppress_controller_substate_pc = tonumber(
    os.getenv("AVSP_ORACLE11_SUPPRESS_CONTROLLER_SUBSTATE_PC") or "", 16)
local class1f_hit_slot = tonumber(
    os.getenv("AVSP_ORACLE11_CLASS1F_HIT_SLOT") or "ffa180", 16)
local class1f_hit_first_frame = tonumber(
    os.getenv("AVSP_ORACLE11_CLASS1F_HIT_FIRST_FRAME") or "2304")
local class1f_hit_last_frame = tonumber(
    os.getenv("AVSP_ORACLE11_CLASS1F_HIT_LAST_FRAME") or "2450")
local class1f_hit_selector_entry = tonumber(
    os.getenv("AVSP_ORACLE11_CLASS1F_HIT_SELECTOR_ENTRY") or "1f890", 16)
local frame = 0
local controller = 0xffd180
local global = 0xff8000
local player = 0xff8380
local pool, stride, count = 0xff9580, 0xc0, 57
local pool24, stride24, count24 = 0xffb680, 0x80, 32
local target_pcs = {
    [0x0288e2] = true, [0x0288f6] = true, [0x028a12] = true,
    [0x028a1c] = true, [0x028a20] = true, [0x028a2c] = true,
    [0x028a36] = true, [0x028a3a] = true, [0x028a5a] = true,
    [0x028ab2] = true, [0x028b5a] = true, [0x028b6e] = true,
    [0x028b76] = true,
}
local transactions = assert(io.open(root .. "/progression_transactions.tsv", "w"))
local snapshots = assert(io.open(root .. "/progression_snapshots.tsv", "w"))
local writes = assert(io.open(root .. "/progression_writes.tsv", "w"))
local global_writes = assert(io.open(root .. "/progression_global_writes.tsv", "w"))
local controller_samples = assert(io.open(root .. "/progression_controller.tsv", "w"))
local lifecycle_writes = assert(io.open(root .. "/progression_lifecycle_writes.tsv", "w"))
local class1f_transitions = assert(io.open(
    root .. "/progression_class1f_transitions.tsv", "w"))
local action4_timers = assert(io.open(
    root .. "/progression_class1f_action4_timers.tsv", "w"))
local action4_guard = assert(io.open(
    root .. "/progression_class1f_action4_guard.tsv", "w"))
local scene_actors = assert(io.open(
    root .. "/coffee_shop_scene_actors.tsv", "w"))
local scene_frames = assert(io.open(
    root .. "/coffee_shop_scene_frames.tsv", "w"))
local scene_health_writes = assert(io.open(
    root .. "/coffee_shop_scene_health_writes.tsv", "w"))
local type4_class03 = assert(io.open(
    root .. "/coffee_shop_type4_class03.tsv", "w"))
local scene_rng_calls = assert(io.open(
    root .. "/coffee_shop_rng_calls.tsv", "w"))
local stage_setup = assert(io.open(
    root .. "/coffee_shop_stage_setup.tsv", "w"))
local stage_setup_writes = assert(io.open(
    root .. "/coffee_shop_stage_setup_writes.tsv", "w"))
local class1f_bounds = assert(io.open(
    root .. "/coffee_shop_class1f_source_bounds.tsv", "w"))
local type36_writes = assert(io.open(
    root .. "/coffee_shop_type36_writes.tsv", "w"))
local pair_suppression = assert(io.open(
    root .. "/coffee_shop_pair_suppression.tsv", "w"))
local component20_writes = assert(io.open(
    root .. "/coffee_shop_component20_writes.tsv", "w"))
local component20_dispatch = assert(io.open(
    root .. "/coffee_shop_component20_dispatch.tsv", "w"))
local component20_collision = assert(io.open(
    root .. "/coffee_shop_component20_collision.tsv", "w"))
local component20_global = assert(io.open(
    root .. "/coffee_shop_component20_global.tsv", "w"))
local component20_phase = assert(io.open(
    root .. "/coffee_shop_component20_phase.tsv", "w"))
local scheduler_phase = assert(io.open(
    root .. "/coffee_shop_scheduler_phase.tsv", "w"))
local component20_callers = assert(io.open(
    root .. "/coffee_shop_component20_callers.tsv", "w"))
local terrain_patch = assert(io.open(
    root .. "/coffee_shop_terrain_patch.tsv", "w"))
local terrain_stream = assert(io.open(
    root .. "/coffee_shop_terrain_stream.tsv", "w"))
local player_dispatch = assert(io.open(
    root .. "/coffee_shop_player_dispatch.tsv", "w"))
local player_animation_writes = assert(io.open(
    root .. "/coffee_shop_player_animation_writes.tsv", "w"))
local obstacle_trace = assert(io.open(
    root .. "/coffee_shop_obstacle_trace.tsv", "w"))
local obstacle_writes = assert(io.open(
    root .. "/coffee_shop_obstacle_writes.tsv", "w"))
local obstacle_guard = assert(io.open(
    root .. "/coffee_shop_obstacle_guard.tsv", "w"))
local type16_collision = assert(io.open(
    root .. "/coffee_shop_type16_class06_collision.tsv", "w"))
local class1f_inner8_entries = assert(io.open(
    root .. "/coffee_shop_class1f_inner8_entries.tsv", "w"))
local class1f_inner8_writes = assert(io.open(
    root .. "/coffee_shop_class1f_inner8_writes.tsv", "w"))
local class1f_inner8_group = assert(io.open(
    root .. "/coffee_shop_class1f_inner8_group.tsv", "w"))
local class1f_action0c = assert(io.open(
    root .. "/coffee_shop_class1f_action0c.tsv", "w"))
local collision_guard = assert(io.open(
    root .. "/coffee_shop_record4_collision_guard.tsv", "w"))
local collision_guard_writes = assert(io.open(
    root .. "/coffee_shop_record12_guard6d_writes.tsv", "w"))
local collision_lists = assert(io.open(
    root .. "/coffee_shop_collision_lists.tsv", "w"))
local collision_list_writes = assert(io.open(
    root .. "/coffee_shop_collision_list_writes.tsv", "w"))
local collision_actor_flags = assert(io.open(
    root .. "/coffee_shop_collision_actor_flags.tsv", "w"))
local collision_identity_writes = assert(io.open(
    root .. "/coffee_shop_record4_collision_identity_writes.tsv", "w"))
local collision_identity_assignments = assert(io.open(
    root .. "/coffee_shop_collision_identity_assignments.tsv", "w"))
local class1f_hit = assert(io.open(
    root .. "/coffee_shop_class1f_hit.tsv", "w"))
local class1f_hit_writes = assert(io.open(
    root .. "/coffee_shop_class1f_hit_writes.tsv", "w"))
local class1f_hit_program = assert(io.open(
    root .. "/coffee_shop_class1f_hit_program.tsv", "w"))
local player_resource = assert(io.open(
    root .. "/coffee_shop_player_resource.tsv", "w"))
local controller_substate_writes = assert(io.open(
    root .. "/coffee_shop_controller_substate_writes.tsv", "w"))
local player_hit_program = assert(io.open(
    root .. "/coffee_shop_player_hit_program.tsv", "w"))
local player_hit_writes = assert(io.open(
    root .. "/coffee_shop_player_hit_writes.tsv", "w"))
local class0a_program = assert(io.open(
    root .. "/coffee_shop_class0a_program.tsv", "w"))
class00_program = assert(io.open(
    root .. "/coffee_shop_class00_program.tsv", "w"))
local class00_scheduler_phase = assert(io.open(
    root .. "/coffee_shop_class00_scheduler_phase.tsv", "w"))
local class00_phase_hook = nil
local result = assert(io.open(root .. "/progression_result.tsv", "w"))

terrain_patch:write("frame\tevent\taddress\tpc\ta0\ta1\ta2\ta3\ta4\ta5\ta6\tplayer_x\tplayer_z\tcamera_x\tcamera_z\tcamera_phase_x\tcamera_phase_z\tcamera_mode\tcamera_map_index\tcell_236c\tcell_23ac\tcell_23ec\tcell_242c\tdata\tmask\tmutated\n")
terrain_stream:write("frame\taddress\tpc\tcamera_x\tcamera_z\tcamera_phase_x\tcamera_phase_z\tcamera_direction\tcamera_mode\tcamera_map_index\ta0\ta1\ta6\tselector_before\tselector_data\tattribute_data\tmask\tmutated\n")
transactions:write("frame\tpc\ta4\ta6\tg8019\tliving\tprogress\tc_state\tc_substate\tc_timer40\tc_timer42\tc_limit4a\tc_index10\tc_phase2e\tc_local2c\tcamera_x\tcamera_z\trng\td0\td1\td2\tactor_active\tactor_class\tactor_type\tactor_state\tactor_substate\tactor_x\tactor_y\tactor_z\tactor_variant\tactor_timer\tactor_selector83\n")
snapshots:write("frame\tslot\tactive\tclass\ttype\tstate\tsubstate\tfacing\tx\ty\tz\tvariant\ttimer\tselector83\thealth\tanim\n")
writes:write("frame\tslot\tinner\tpc\ta6\told32\tdata\tmask\tg8019\tliving\tprogress\tc_state\tc_substate\tc_timer40\tc_limit4a\tc_index10\tcamera_x\tcamera_z\trng\tsuppressed\n")
global_writes:write("frame\taddress\tpc\ta6\towner_active\towner_class\towner_type\towner_state\towner_substate\told32\tdata\tmask\tguard1a11\tc_state\tc_timer42\tg8019\tsuppressed\n")
controller_samples:write("frame\tactive\tclass\ttype\tstate\tsubstate\tindex10\ttimer40\ttimer42\tfield44\tfield46\tfield48\tlimit4a\tlocal2c\tphase2e\tguard1a11\tg8019\tliving\tprogress\tcamera_x\tcamera_z\n")
lifecycle_writes:write("frame\taddress\tpc\ta6\towner_active\towner_class\towner_type\towner_state\towner_substate\towner_x\towner_y\towner_z\towner_health\towner_anim\tliving_before\tprogress_before\tdata\tmask\tsuppressed\n")
class1f_transitions:write("frame\tslot\tinner\tpc\ta6\tactive\tclass\ttype\tstate_before\tsubstate_before\tfacing\tx\ty\tz\thealth\tanim\ttimer2a\tfield01\tfield0a\tfield24\tfield2b\tfield5c\tfield6e\tfield85\tfield96\tfielda2\tfielda3\tfielda4\tfielda5\tfielda6\tfieldac\tfieldad\tfieldae\tfieldaa\tfieldb0\tfield0c\tg8209\tg9a10\tg9a1c\tliving\tprogress\tp_state\tp_substate\tp_facing\tp_x\tp_y\tp_z\tp_health\tp_anim\tp_hurt\tp_attack\td0\td1\td2\td3\ta0\ta1\ta2\ta3\ta4\ta5\tdata\tmask\tsuppressed\n")
action4_timers:write("frame\tevent\tpc\tslot\tstate\tsubstate\tstage_parameter\trng\td0\ttimer2a\tdata\tmask\tsuppressed\n")
action4_guard:write("frame\tevent\tpc\tslot\tstate\tsubstate\tfield6e\ttimer2a\tanimation_record\tanimation_timer\tanimation_branch\tdata\tmask\n")
scene_actors:write("frame\tpool\tpool_index\tslot\tactive\ttype\tclass\tvariant\tstate\tsubstate\tfacing\tx_fp\ty_fp\tz\tanimation_record\tanimation_timer\tanimation_branch\taction_timer\thealth\thurt_selector\tattack_selector\n")
scene_frames:write("frame\troute_state\tentry_controller_state\tentry_controller_substate\tentry_controller_timer40\tentry_controller_timer42\tliving_enemy_count\tencounter_progress\tplayer_active\tplayer_state\tplayer_substate\tplayer_facing\tplayer_x_fp\tplayer_y_fp\tplayer_z\tplayer_health\tcamera_x\tcamera_z\tcamera_target_x\trng\n")
scene_health_writes:write("frame\ttarget_pool\ttarget_slot\tpc\tattacker\tdefender\tattack_record\tstate\tsubstate\thealth_before\thealth_after\tmask\tdamage_writer\n")
type4_class03:write("frame\tevent\tpc\tslot\tinner\ta6\ta4\tactive\tclass\ttype\tstate\tsubstate\tfacing\tx_fp\ty_fp\tz\towner_word\towner_slot\tmotion_table\tanimation_record\tcollision_table\thealth\tfield05\tfield0c\tfield19\ttimer2a\ttimer2b\tfield5c\tfield65\td0\td1\td2\td3\tdata\tmask\tsuppressed\n")
scene_rng_calls:write("frame\tentry_pc\treturn_pc\ta6\tactive\tclass\ttype\tstate\tsubstate\trng_before\n")
stage_setup:write("frame\tevent\tpc\tsp\ta0\ta1\ta2\ta3\ta4\ta5\ta6\td0\td1\td2\td3\troute\tplayer_variant\tstage_parameter\trng\tstage_row_bytes\trandom_table_bytes\tsource_window_bytes\topcode_window_bytes\tsuppressed\n")
stage_setup_writes:write("frame\tpc\taddress\tstage_parameter_before\tdata\tmask\trng\n")
class1f_bounds:write("frame\tpc\ta5\ta6\tslot\tstate\tsubstate\tactor_x_u16\toperand_address\toperand_u16\td0_u16\tfield01\tfield19\tfielda2\topcode_window_bytes\n")
type36_writes:write("frame\tslot\tinner\tpc\ta6\tparent_active\tparent_class\tparent_type\tparent_state\tparent_substate\tparent_animation_record\treturn0\troute\tactive\tclass\ttype\tstate\tsubstate\tvariant\tanimation_record\tanimation_timer\tanimation_branch\tdata\tmask\tsuppressed\n")
pair_suppression:write("frame\tpool\tslot\ttype\tclass\tstate\tsubstate\tanimation_record\troute\tplayer_state\tplayer_substate\tplayer_health\tcamera_x\tcamera_z\trng\n")
component20_writes:write("frame\tpc\tslot\tinner\ta1\ta3\ta4\ta6\tactive\tclass\ttype\tstate\tsubstate\tvariant\tx_fp\ty_fp\tz\tanimation_record\tanimation_timer\tanimation_branch\taction_timer\tfield42\tfield4c\tfield66\tliving\tprogress\troute\tcamera_x\trng\tdata\tmask\n")
component20_dispatch:write("frame\tpc\treturn_pc\tslot\ta4\ta6\tactive\tclass\ttype\tstate\tsubstate\tvariant\tx_fp\ty_fp\tz\tanimation_record\tanimation_timer\tanimation_branch\taction_timer\tfield42\tfield4c\tfield66\tliving\tprogress\tglobal1c\troute\tcamera_x\trng\td0\td1\td4\td5\n")
component20_collision:write("frame\tpc\ta0\ta1\ta2\ta3\ta4\ta5\ta6\td0\td1\td2\td3\td4\td5\td6\td7\tstate\tsubstate\tanimation_record\thurt_selector\tattack_selector\thealth\n")
component20_global:write("frame\tpc\toffset\ta1\ta3\ta4\ta6\told\tdata\tmask\tliving\tprogress\tglobal1c\troute\tcamera_x\n")
component20_phase:write("frame\tordinal\tpc\tsp\ta7\ta7_return0\ta7_return1\ta7_return2\tslot\ta4\ta4_active\ta4_class\ta4_type\ta4_state\ta4_substate\tstate\tsubstate\tanimation_record\tanimation_timer\tanimation_branch\tfield42\tfield4c\tfield66\troute\tcamera_x\n")
scheduler_phase:write("frame\tordinal\tpc\ta5\ta6\troute\tcamera_x\trng\n")
component20_callers:write("frame\tordinal\tcaller_pc\ttarget\ta4\ta5\ta6\tstate\tsubstate\tanimation_timer\tfield4c\troute\tcamera_x\n")
player_dispatch:write("frame\tpc\treturn_pc\ta6\tstate\tsubstate\tanimation_record\tanimation_timer\tanimation_branch\taction_timer\troute\n")
player_animation_writes:write("frame\tpc\taddress\ta6\tstate\tsubstate\tanimation_record\tanimation_timer\tanimation_branch\taction_timer\tdata\tmask\n")
obstacle_trace:write("frame\tpc\tstate\tsubstate\tactive\tclass\ttype\tfacing\tx_fp\ty_fp\tz\tanimation_record\tanimation_timer\tanimation_branch\tfield06\tfield0c\tfield18\tfield24\tfield2a\tfield2e\tfield30\tfield32\tfield34\tfield36\tfield38\tfield3a\tfield3c\tfield3e\tfield40\tfield42\tfield4f\tfield50\tfield58\tfield60\tfield64\tfield68\tfield6c\tchild0\tchild1\tchild2\tchild3\tguard_ffee8f\troute\trng\td0\td1\td2\td3\ta0\ta1\ta2\ta3\ta4\ta5\n")
obstacle_writes:write("frame\tpc\tinner\tstate\tsubstate\tactive\tclass\ttype\tanimation_record\tanimation_timer\tanimation_branch\thealth_before\tguard_ffee8f\td0\td1\td2\td3\ta0\ta1\ta2\ta3\ta4\ta5\tdata\tmask\tsuppressed\n")
obstacle_guard:write("frame\tpc\tvalue_before\tdata\tmask\troute\tstate\tsubstate\td0\td1\td2\td3\ta0\ta1\ta2\ta3\ta4\ta5\ta6\n")
type16_collision:write("frame\tpc\ta0\ta1\ta2\ta3\ta4\ta5\ta6\td0\td1\td2\td3\td4\td5\td6\td7\tattacker_state\tattacker_substate\tattacker_animation_record\tattacker_table\tdefender_state\tdefender_substate\tdefender_animation_record\tdefender_table\tattack_record\n")
class1f_inner8_entries:write("frame\tpc\tslot\tstate\tsubstate\tfacing\tx_fp\ty_fp\tz\tanimation_record\tanimation_timer\tanimation_branch\taction_timer\tfield85\tfielda3\tfielda4\tfielda5\tfielda6\tfieldac\tfieldad\tfieldae\tfielda8\tfieldb0\trng\td0\td1\td2\td3\ta0\ta1\ta2\ta3\ta4\ta5\n")
class1f_inner8_writes:write("frame\tpc\tslot\tinner\tstate\tsubstate\tfacing\tx_fp\ty_fp\tz\tanimation_record\tanimation_timer\tanimation_branch\taction_timer\tfield85\tfielda3\tfielda4\tfielda5\tfielda6\tfieldac\tfieldad\tfieldae\tfielda8\tfieldb0\trng\told32\tdata\tmask\n")
class1f_inner8_group:write("frame\tevent\tpc\tslot\tstate\tsubstate\tband86\tgroup87_s8\tgroup87_u8\tcursor89\tmembership8a\tdirection0c\toffset60\toffset62\tstyle85\tfielda3\trng\toccupancy0\toccupancy1\toccupancy2\toccupancy3\tx_fp\ty_fp\tz\tcamera_x\tcamera_z\td0\td2\td3\tdata\tmask\tmutated\n")
class1f_action0c:write("frame\tevent\tpc\tslot\tinner\tstate\tsubstate\tvariant\tfacing\tdirection\tx_fp\ty_fp\tz\tanimation_record\tanimation_timer\tanimation_branch\ttimer2a\tguard6e\tstyle85\tfield80\tfield82\tfield95\tfield96\tfield98\ttarget\trng\td0\td1\td2\td3\ta0\ta4\tdata\tmask\tmutated\n")
collision_guard:write("frame\tevent\tpc\tattacker\tattacker_active\tattacker_class\tattacker_state\tattacker_substate\tattacker_x_fp\tattacker_y_fp\tattacker_z\tattacker_anim\tattacker_attack_selector\tattacker_latch_index65\tattacker_id67\tdefender\tdefender_active\tdefender_class\tdefender_state\tdefender_substate\tdefender_x_fp\tdefender_y_fp\tdefender_z\tdefender_anim\tdefender_hurt_selector\tdefender_guard6d\tdefender_latch_value\tdefender_suppress70\tdefender_health\tmutated\n")
collision_guard_writes:write("frame\tpc\tslot\tinner\tstate\tsubstate\tguard6d_before\tdata\tmask\n")
collision_lists:write("frame\tpc\tattacker_count\tattacker_slots\tdefender_count\tdefender_slots\n")
collision_list_writes:write("frame\tpc\taddress\ta6\tactive\tfield01\tfield47\tfield48\tanimation_record\treturn0\treturn1\treturn2\tdata\tmask\tsuppressed\n")
collision_actor_flags:write("frame\tpc\tslot\tinner\tactive\tfield01\tstate\tsubstate\tx_fp\ty_fp\tz\tcamera_x\tcamera_z\tdata\tmask\tsuppressed\n")
collision_identity_writes:write("frame\tpc\tslot\tinner\tactive\tclass\tstate\tsubstate\tlatch_index65_before\tattacker_id67_before\tdata\tmask\n")
collision_identity_assignments:write("frame\tevent\tpc\tslot\tactive\tclass\ttype\tstate\tsubstate\tattacker_id67\tglobal_id820b\n")
class1f_hit:write("frame\tpc\tslot\tstate\tsubstate\tfacing\tanimation_record\tanimation_timer\tanimation_branch\taction_timer\trecovery_timer2c\thealth\tprior_health\thit_mode46\thit_kind49\treaction_selector4d\tscore_arg4e\treaction_facing4f\tairborne5c\tlatch_index65\tmotion_index6c\thit_count6d\tinterrupt73\td0\td1\td2\td3\ta0\ta1\ta2\ta3\ta4\ta5\n")
class1f_hit_writes:write("frame\tpc\tslot\tinner\tstate\tsubstate\tanimation_record\taction_timer\trecovery_timer2c\thealth\tprior_health\thit_mode46\thit_kind49\treaction_selector4d\treaction_facing4f\tairborne5c\tmotion_index6c\thit_count6d\tinterrupt73\told32\tdata\tmask\tsuppressed\n")
class1f_hit_program:write("frame\tpc\tstate\tsubstate\tfacing\tx_fp\ty_fp\tz\tanimation_record\tanimation_timer\tanimation_branch\taction_timer2a\trecovery_timer2c\thealth\tprior_health\thit_mode46\thit_kind49\treaction_selector4d\treaction_facing4f\tairborne5c\tmotion_index6c\thit_count6d\tinterrupt73\tx_velocity30\ty_velocity34\tx_acceleration38\ty_acceleration3c\trng\td0\td1\td2\td3\n")
player_resource:write("frame\tevent\tpc\tresource\trecharge\tdepleted\taward_timer\tstate\tsubstate\tdata\tmask\tsuppressed\n")
controller_substate_writes:write("frame\tpc\toffset\tstate\tsubstate\tfield44\ta6\td0\td1\td2\td3\ta0\ta1\ta2\ta3\ta4\ta5\told32\tdata\tmask\tsuppressed\n")
player_hit_program:write("frame\tevent\tpc\tstate\tsubstate\tinner_phase\tfacing\tx_fp\ty_fp\tz\tground_z\tanimation_record\tanimation_timer\tanimation_branch\taction_timer\tshake_count\thealth\tlatched_health\tactive_body\thit_kind\tpresentation_selector\treaction_facing\tairborne\tmotion_index\tinterrupt\tx_velocity\ty_velocity\tx_acceleration\ty_acceleration\tcollision_flags\td0\td1\td2\td3\ta0\ta1\ta2\ta3\ta4\ta5\n")
player_hit_writes:write("frame\tpc\toffset\tstate\tsubstate\tinner_phase\tanimation_record\taction_timer\tshake_count\thealth\tlatched_health\tactive_body\thit_kind\tpresentation_selector\treaction_facing\tairborne\tmotion_index\tinterrupt\told32\tdata\tmask\tmutated\n")
class0a_program:write("frame\tevent\ttap_pc\tactual_pc\tslot\tinner\tactive\tclass\ttype\tvariant\tstate\tsubstate\tx_fp\ty_fp\tz\tanimation_record\tanimation_timer\tanimation_branch\tcamera_x\troute\td0\td1\ta0\ta5\ta6\tdata\tmask\tmutated\n")
class00_program:write("frame\tevent\ttap_pc\tactual_pc\tslot\tinner\tactive\tclass\ttype\tvariant\tstate\tsubstate\tfacing\tx_fp\ty_fp\tz\tx_velocity\ty_velocity\ty_acceleration\tanimation_record\tanimation_timer\tanimation_branch\tparent_slot\tparent_active\tparent_class\tparent_type\tparent_state\tparent_substate\tparent_x_fp\tparent_y_fp\tparent_z\tparent_animation_record\tparent_animation_branch\tparent_d2\tparent_field56\tfield2a\tfield2e\tfield44\tfield45\tfield50\tfield54\tfield5a\tfield5c\tfield62\tfield64\tfield65\tcamera_x\troute\trng\td0\td1\td2\ta0\ta1\ta3\ta4\ta5\ta6\tdata\tmask\tmutated\n")
class00_scheduler_phase:write("frame\tordinal\tevent\tpc\tplayer_state\tplayer_substate\tplayer_x_fp\tplayer_y_fp\tplayer_z\tplayer_animation_record\tchild_state\tchild_substate\tchild_x_fp\tchild_y_fp\tchild_z\tchild_animation_record\n")
result:write("spawn_suppression\tguard_suppression\tmain_spawn_transactions\taux_spawn_transactions\tsuppressed_writes\tlifecycle_suppressed_writes\taction4_timer_events\taction4_timer_suppressed_writes\ttype4_class03_suppressed_writes\tcoffee_stage_rng_suppressed_writes\ttype36_suppressed_writes\tscene_pair_suppressed_actors\tobstacle_transition_suppressed_writes\tclass1f_hit_selector_mutations\tplayer_hit_body_mutations\tclass0a_counterfactuals\tclass00_counterfactuals\tfinal_route\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function s8(v) return v >= 0x80 and v - 0x100 or v end
local main_spawns, aux_spawns, suppressed_writes = 0, 0, 0
local lifecycle_suppressed_writes = 0
local action4_timer_events, action4_timer_suppressed_writes = 0, 0
local type4_class03_suppressed_writes = 0
local coffee_stage_rng_suppressed_writes = 0
local type36_suppressed_writes = 0
local scene_pair_suppressed_actors = 0
local obstacle_transition_suppressed_writes = 0
local class1f_hit_selector_mutations = 0
local player_hit_body_mutations = 0

local terrain_patch_cells = {
    0x90636c, 0x9063ac, 0x9063ec, 0x90642c,
}

local function emit_terrain_patch(event, address, data, mask, mutated)
    if not capture_terrain_patch then return end
    terrain_patch:write(string.format(
        "%d\t%s\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%d\t%d\t%d\t%d\t%02x\t%02x\t%02x\t%04x\t%02x\t%02x\t%02x\t%02x\t%08x\t%08x\t%d\n",
        frame, event, address,
        maincpu.state["PC"].value & 0xffffff,
        maincpu.state["A0"].value & 0xffffff,
        maincpu.state["A1"].value & 0xffffff,
        maincpu.state["A2"].value & 0xffffff,
        maincpu.state["A3"].value & 0xffffff,
        maincpu.state["A4"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff,
        maincpu.state["A6"].value & 0xffffff,
        s16(u16(player + 0x10)), s16(u16(player + 0x18)),
        s16(u16(0xff8268 + 0x20)), s16(u16(0xff8268 + 0x24)),
        u8(0xff8268 + 0x44), u8(0xff8268 + 0x45),
        u8(0xff8268 + 0x5e), u16(0xff8268 + 0x42),
        u8(0x90636e), u8(0x9063ae), u8(0x9063ee), u8(0x90642e),
        data & 0xffffffff, mask & 0xffffffff, mutated and 1 or 0))
end

oracle11_terrain_patch_writes = {}
for _, address in ipairs(terrain_patch_cells) do
    oracle11_terrain_patch_writes[#oracle11_terrain_patch_writes + 1] =
        program:install_write_tap(address, address + 3,
        string.format("oracle11_terrain_patch_%06x", address),
        function(offset, data, mask)
            local pc = maincpu.state["PC"].value & 0xffffff
            local mutated = capture_terrain_patch and mutate_terrain_patch and
                frame >= 2073 and
                terrain_patch_mutation_pc ~= nil and
                pc == terrain_patch_mutation_pc
            if capture_terrain_patch and frame <= capture_last_frame then
                emit_terrain_patch("write", offset, data, mask, mutated)
            end
            if mutated then return u32(offset & 0xfffffc) end
        end)
end

oracle11_terrain_stream_writes = program:install_write_tap(
    0x904000, 0x907fff, "oracle11_terrain_stream_writes",
    function(offset, data, mask)
        local pc = maincpu.state["PC"].value & 0xffffff
        if not capture_terrain_stream or frame < 2073 or
                frame > 5541 or pc ~= 0x0b2832 then return end
        local mutated = mutate_terrain_patch and
            terrain_patch_mutation_pc == pc
        terrain_stream:write(string.format(
            "%d\t%06x\t%06x\t%d\t%d\t%02x\t%02x\t%02x\t%02x\t%04x\t%06x\t%06x\t%06x\t%02x\t%02x\t%02x\t%08x\t%d\n",
            frame, offset, pc, s16(u16(0xff8268 + 0x20)),
            s16(u16(0xff8268 + 0x24)),
            u8(0xff8268 + 0x44), u8(0xff8268 + 0x45),
            u8(0xff8268 + 0x47),
            u8(0xff8268 + 0x5e),
            u16(0xff8268 + 0x42),
            maincpu.state["A0"].value & 0xffffff,
            maincpu.state["A1"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff,
            u8(offset), (data >> 8) & 0xff, data & 0xff,
            mask & 0xffffffff, mutated and 1 or 0))
        if mutated then return u32(offset & 0xfffffc) end
    end)

oracle11_coffee_shop_resource_writes = program:install_write_tap(
    player + 0x88, player + 0x8f,
    "oracle11_coffee_shop_resource_writes",
    function(offset, data, mask)
        if not capture_scene or frame < 1972 or
                frame > capture_last_frame then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        local suppressed = suppress_resource_pc ~= nil and
            pc == suppress_resource_pc
        player_resource:write(string.format(
            "%d\twrite\t%06x\t%d\t%d\t%d\t%d\t%04x\t%04x\t%08x\t%08x\t%d\n",
            frame, pc, u8(player + 0x8c), u8(player + 0x8d),
            u8(player + 0x8b), u8(player + 0x8a),
            u16(player + 4), u16(player + 6),
            data & 0xffffffff, mask & 0xffffffff,
            suppressed and 1 or 0))
        if suppressed then return u32(offset & 0xfffffc) end
    end)

local function hex_bytes(first, count)
    local parts = {}
    for i = 0, count - 1 do
        parts[#parts + 1] = string.format("%02x", u8(first + i))
    end
    return table.concat(parts)
end

local function hex_opcode_bytes(first, count)
    local parts = {}
    for i = 0, count - 1 do
        parts[#parts + 1] = string.format("%02x", opcodes:read_u8(first + i))
    end
    return table.concat(parts)
end

local stage_opcode_window = hex_opcode_bytes(0x017ac6, 0xc0)
local class1f_bounds_opcode_window = hex_opcode_bytes(0x060c2e, 0x3a)

local function emit_class1f_bounds(pc)
    if not capture_scene or frame < 2280 or frame > 2472 then return end
    local a5 = maincpu.state["A5"].value & 0xffffff
    local a6 = maincpu.state["A6"].value & 0xffffff
    if a6 < pool or a6 >= pool + count * stride or
            ((a6 - pool) % stride) ~= 0 or u8(a6 + 2) ~= 0x1f or
            u8(a6 + 8) ~= 12 or u16(a6 + 4) ~= 0x0200 or
            (u16(a6 + 6) >> 8) ~= 0x16 then return end
    class1f_bounds:write(string.format(
        "%d\t%06x\t%06x\t%06x\t%06x\t%04x\t%04x\t%04x\t%06x\t%04x\t%04x\t%02x\t%02x\t%02x\t%s\n",
        frame, pc, a5, a6, a6, u16(a6 + 4), u16(a6 + 6),
        u16(a6 + 0x10), (a5 + 0x278) & 0xffffff,
        u16((a5 + 0x278) & 0xffffff),
        maincpu.state["D0"].value & 0xffff, u8(a6 + 1),
        u8(a5 + 0x19), u8(a6 + 0xa2), class1f_bounds_opcode_window))
end

local class1f_bounds_pcs = {
    0x060c2e, 0x060c34, 0x060c3e, 0x060c4a, 0x060c52,
    0x060c56, 0x060c5a, 0x060c5e, 0x060c62, 0x060c66,
    0x060c68, 0x060c70, 0x0608a2,
}
oracle11_class1f_bounds_pc_taps = {}
for _, pc in ipairs(class1f_bounds_pcs) do
    oracle11_class1f_bounds_pc_taps[#oracle11_class1f_bounds_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_class1f_bounds_%06x", pc),
        function() emit_class1f_bounds(pc) end)
end

local function emit_stage_setup(event, pc, suppressed)
    if not capture_scene or frame < 2068 or frame > 2076 then return end
    stage_setup:write(string.format(
        "%d\t%s\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\t%08x\t%08x\t%04x\t%04x\t%04x\t%04x\t%s\t%s\t%s\t%s\t%d\n",
        frame, event, pc, maincpu.state["SP"].value & 0xffffff,
        maincpu.state["A0"].value & 0xffffff,
        maincpu.state["A1"].value & 0xffffff,
        maincpu.state["A2"].value & 0xffffff,
        maincpu.state["A3"].value & 0xffffff,
        maincpu.state["A4"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff,
        maincpu.state["A6"].value & 0xffffff,
        maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        u16(global + 8), u16(0xff8218), u16(0xff81ea), u16(0xff81a8),
        hex_bytes(0x117560, 64), hex_bytes(0x017b98, 64),
        hex_bytes(0x017ac6, 0xc0), stage_opcode_window,
        suppressed and 1 or 0))
end

oracle11_stage_parameter_write = program:install_write_tap(
    0xff81ea, 0xff81eb, "oracle11_stage_parameter_write",
    function(offset, data, mask)
        if not capture_scene or frame < 2068 or frame > 2076 then return end
        stage_setup_writes:write(string.format(
            "%d\t%06x\t%06x\t%04x\t%08x\t%08x\t%04x\n",
            frame, maincpu.state["PC"].value & 0xffffff, offset,
            u16(0xff81ea), data & 0xffffffff, mask & 0xffffffff,
            u16(0xff81a8)))
    end)

local stage_setup_pcs = {
    0x017a1e, 0x017ac6, 0x017ade, 0x017af0, 0x017af2, 0x017af6,
    0x017b08, 0x017b1c, 0x017b26, 0x017b32, 0x017b3e, 0x017b4a,
    0x017b56, 0x017b62, 0x017b74, 0x017b78,
}
oracle11_stage_setup_pc_taps = {}
for _, pc in ipairs(stage_setup_pcs) do
    oracle11_stage_setup_pc_taps[#oracle11_stage_setup_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_stage_setup_%06x", pc),
        function() emit_stage_setup("pc", pc, false) end)
end

oracle11_stage_setup_rng_write = program:install_write_tap(
    0xff81a8, 0xff81a9, "oracle11_stage_setup_rng_write",
    function(offset, data, mask)
        local pc = maincpu.state["PC"].value & 0xffffff
        local a6 = maincpu.state["A6"].value & 0xffffff
        if not capture_scene or frame ~= 2072 or a6 ~= 0xff1812 or
                (pc ~= 0x017c70 and pc ~= 0x017c72) then return end
        local suppressed = suppress_coffee_stage_rng
        emit_stage_setup("rng_write", pc, suppressed)
        if suppressed then
            coffee_stage_rng_suppressed_writes =
                coffee_stage_rng_suppressed_writes + 1
            return u16(0xff81a8)
        end
    end)

oracle11_scene_rng_tap = opcodes:install_read_tap(
    0x017c5e, 0x017c5f, "oracle11_scene_rng_entry",
    function()
        if not capture_scene or frame < 1972 or
                frame > capture_last_frame then return end
        local a6 = maincpu.state["A6"].value & 0xffffff
        local sp = maincpu.state["SP"].value & 0xffffff
        local actor = a6 >= 0xff8000 and a6 <= 0xffff00
        scene_rng_calls:write(string.format(
            "%d\t017c5e\t%06x\t%06x\t%d\t%02x\t%d\t%04x\t%04x\t%04x\n",
            frame, u32(sp) & 0xffffff, a6,
            actor and u8(a6) or 0, actor and u8(a6 + 2) or 0,
            actor and u8(a6 + 8) or 0, actor and u16(a6 + 4) or 0,
            actor and u16(a6 + 6) or 0, u16(0xff81a8)))
    end)

local scene_pools = {
    -- Exact pool layouts from the source initializer 0x01729e..0x0174a4.
    -- Keep the auxiliary record-24 region distinct from the primary pool: it
    -- has separate storage and free-list ownership even though +0x08 is 24.
    {name = "record4", base = 0xff8680, stride = 0x80, count = 24, type = 4},
    {name = "record8", base = 0xff9280, stride = 0xc0, count = 4, type = 8},
    {name = "record12", base = 0xff9580, stride = 0xc0, count = 20, type = 12,
        has_health = true, has_collision_selectors = true},
    {name = "record16", base = 0xffa480, stride = 0x80, count = 20, type = 16},
    {name = "record20", base = 0xffae80, stride = 0x80, count = 16, type = 20},
    {name = "record24", base = 0xffb680, stride = 0x80, count = 32, type = 24},
    {name = "record28", base = 0xffc680, stride = 0x80, count = 16, type = 28},
    {name = "record32", base = 0xffce80, stride = 0x100, count = 4, type = 32},
    {name = "record36", base = 0xffd280, stride = 0x40, count = 64, type = 36},
    {name = "record24_aux", base = 0xffe280, stride = 0x80, count = 16,
        type = 24},
}

local component20_slots = {
    [0xffb100] = true,
    [0xffb300] = true, [0xffb400] = true,
    [0xffb580] = true, [0xffb600] = true,
}

local component20_phase_ordinal = 0
local scheduler_phase_ordinal = 0
local component20_caller_ordinal = 0

local function component20_phase_window()
    return (frame >= 2072 and frame <= 2078) or
        (frame >= 2617 and frame <= 2621)
end

local function emit_scheduler_phase(pc)
    if not capture_component20_phase or frame < 1972 or
        frame > capture_last_frame then
        return
    end
    scheduler_phase_ordinal = scheduler_phase_ordinal + 1
    scheduler_phase:write(string.format("%d\t%d\t%06x\t%06x\t%06x\t%d\t%d\t%04x\n",
        frame, scheduler_phase_ordinal, pc,
        maincpu.state["A5"].value & 0xffffff,
        maincpu.state["A6"].value & 0xffffff, u16(global + 8),
        s16(u16(global + 0x278)), u16(0xff81a8)))
end

oracle11_scheduler_phase_pc_taps = {}
for _, pc in ipairs({0x00849e, 0x01bc38}) do
    oracle11_scheduler_phase_pc_taps[#oracle11_scheduler_phase_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_scheduler_phase_%06x", pc),
        function() emit_scheduler_phase(pc) end)
end

local component20_indirect_callers = {
    0x003b58, 0x019c72, 0x019ccc, 0x019f1c, 0x01a106, 0x01a18a,
    0x01a524, 0x01a748, 0x01a7bc, 0x01a9b4, 0x01ae70, 0x01b176,
    0x01b86c, 0x01b8e2, 0x01b94c, 0x01b9aa, 0x01ba88, 0x01bc6e,
    0x01bd00, 0x01bd6e, 0x01bde4, 0x01c834, 0x021738, 0x0244bc,
    0x024d04, 0x02726c, 0x039d6c, 0x05d9dc, 0x05e084, 0x05e612,
    0x0829f6, 0x09578a, 0x09587a, 0x0a8546, 0x0ac636, 0x0b98aa,
    0x0cf1c6, 0x130676, 0x133bd4, 0x139e54,
}

local function emit_component20_caller(pc)
    if not capture_component20_phase or frame < 1972 or
        frame > capture_last_frame then
        return
    end
    local target = maincpu.state["A0"].value & 0xffffff
    if target ~= 0x06b534 then return end
    local a6 = maincpu.state["A6"].value & 0xffffff
    component20_caller_ordinal = component20_caller_ordinal + 1
    component20_callers:write(string.format(
        "%d\t%d\t%06x\t%06x\t%06x\t%06x\t%06x\t%04x\t%04x\t%04x\t%02x\t%d\t%d\n",
        frame, component20_caller_ordinal, pc, target,
        maincpu.state["A4"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff, a6, u16(a6 + 4),
        u16(a6 + 6), u16(a6 + 0x0a), u8(a6 + 0x4c),
        u16(global + 8), s16(u16(global + 0x278))))
end

oracle11_component20_caller_taps = {}
for _, pc in ipairs(component20_indirect_callers) do
    oracle11_component20_caller_taps[#oracle11_component20_caller_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_component20_caller_%06x", pc),
        function() emit_component20_caller(pc) end)
end

local function emit_component20_phase(pc, a6, sp)
    if not capture_component20_phase or pc ~= 0x06b534 or
        not component20_phase_window() then
        return
    end
    component20_phase_ordinal = component20_phase_ordinal + 1
    local a4 = maincpu.state["A4"].value & 0xffffff
    local a7 = maincpu.state["A7"].value & 0xffffff
    component20_phase:write(string.format(
        "%d\t%d\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%d\t%02x\t%d\t%04x\t%04x\t%04x\t%04x\t%08x\t%04x\t%d\t%02x\t%02x\t%02x\t%d\t%d\n",
        frame, component20_phase_ordinal, pc, sp, a7,
        u32(a7) & 0xffffff, u32(a7 + 4) & 0xffffff,
        u32(a7 + 8) & 0xffffff, a6, a4, u8(a4), u8(a4 + 2),
        u8(a4 + 8), u16(a4 + 4), u16(a4 + 6), u16(a6 + 4),
        u16(a6 + 6), u32(a6 + 0x1c), u16(a6 + 0x0a),
        s16(u16(a6 + 0x24)), u8(a6 + 0x42), u8(a6 + 0x4c),
        u8(a6 + 0x66), u16(global + 8), s16(u16(global + 0x278))))
end

local function emit_component20_dispatch(pc)
    if not capture_scene or frame < 1972 or frame > capture_last_frame then
        return
    end
    local a6 = maincpu.state["A6"].value & 0xffffff
    if not component20_slots[a6] then return end
    local sp = maincpu.state["SP"].value & 0xffffff
    emit_component20_phase(pc, a6, sp)
    component20_dispatch:write(string.format(
        "%d\t%06x\t%06x\t%06x\t%06x\t%06x\t%d\t%02x\t%d\t%04x\t%04x\t%02x\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%04x\t%02x\t%02x\t%02x\t%d\t%d\t%d\t%d\t%d\t%04x\t%08x\t%08x\t%08x\t%08x\n",
        frame, pc, u32(sp) & 0xffffff, a6,
        maincpu.state["A4"].value & 0xffffff, a6,
        u8(a6), u8(a6 + 2), u8(a6 + 8), u16(a6 + 4),
        u16(a6 + 6), u8(a6 + 3), u32(a6 + 0x10), u32(a6 + 0x14),
        s16(u16(a6 + 0x18)), u32(a6 + 0x1c), u16(a6 + 0x0a),
        s16(u16(a6 + 0x24)), u16(a6 + 0x2a), u8(a6 + 0x42),
        u8(a6 + 0x4c), u8(a6 + 0x66), u16(0xff1a18),
        u16(0xff1a1a), u16(0xff1a1c), u16(global + 8), s16(u16(global + 0x278)),
        u16(0xff81a8), maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D4"].value & 0xffffffff,
        maincpu.state["D5"].value & 0xffffffff))
end

local function emit_class0a_program(event, pc, slot, inner, data, mask,
        mutated)
    if not capture_scene or frame < 1972 or frame > capture_last_frame then
        return
    end
    if slot ~= 0xffc580 and slot ~= 0xffc600 then return end
    if event ~= "write" and
            (u8(slot) == 0 or u8(slot + 2) ~= 0x0a or
             u8(slot + 8) ~= 24) then
        return
    end
    class0a_program:write(string.format(
        "%d\t%s\t%06x\t%06x\t%06x\t%02x\t%d\t%02x\t%d\t%02x\t%04x\t%04x\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%d\t%d\t%08x\t%08x\t%06x\t%06x\t%06x\t%08x\t%08x\t%d\n",
        frame, event, pc, maincpu.state["PC"].value & 0xffffff,
        slot, inner, u8(slot), u8(slot + 2),
        u8(slot + 8), u8(slot + 3), u16(slot + 4), u16(slot + 6),
        u32(slot + 0x10), u32(slot + 0x14), s16(u16(slot + 0x18)),
        u32(slot + 0x1c), u16(slot + 0x0a),
        s16(u16(slot + 0x24)), s16(u16(global + 0x278)),
        u16(global + 8), maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["A0"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff,
        maincpu.state["A6"].value & 0xffffff, data & 0xffffffff,
        mask & 0xffffffff, mutated and 1 or 0))
end

oracle11_class0a_counterfactual_begin = opcodes:install_read_tap(
    0x077cf6, 0x077cf7, "oracle11_class0a_counterfactual_begin",
    function()
        local a6 = maincpu.state["A6"].value & 0xffffff
        if not capture_scene or not class0a_variant_counterfactual or
                class0a_variant_counterfactual_count ~= 0 or
                a6 ~= 0xffc600 or u8(a6 + 2) ~= 0x0a or
                u8(a6 + 8) ~= 24 then
            return
        end
        class0a_saved_variant = u8(a6 + 3)
        class0a_saved_camera_x = u16(global + 0x278)
        program:write_u8(a6 + 3, 0x0a)
        program:write_u16(global + 0x278, 0x0920)
        class0a_counterfactual_active = true
        class0a_variant_counterfactual_count = 1
        emit_class0a_program("counterfactual_begin", 0x077cf6, a6, 3,
            0x0a, 0x000000ff, true)
    end)

oracle11_class0a_counterfactual_end = opcodes:install_read_tap(
    0x077d1a, 0x077d1b, "oracle11_class0a_counterfactual_end",
    function()
        local a6 = maincpu.state["A6"].value & 0xffffff
        if not class0a_counterfactual_active or a6 ~= 0xffc600 then return end
        program:write_u8(a6 + 3, class0a_saved_variant)
        program:write_u16(global + 0x278, class0a_saved_camera_x)
        class0a_counterfactual_active = false
        emit_class0a_program("counterfactual_end", 0x077d1a, a6, 3,
            class0a_saved_variant, 0x000000ff, true)
    end)

local class0a_pcs = {
    0x077ccc, 0x077ce0, 0x077ce4, 0x077ce8, 0x077cec, 0x077cf0,
    0x077cf6, 0x077cfc, 0x077cfe, 0x077d04, 0x077d06, 0x077d0c,
    0x077d0e, 0x077d14, 0x077d16, 0x077d1a, 0x077d20,
    0x016d46, 0x016d2e, 0x016518, 0x016536, 0x0167ac, 0x0177f0,
}
oracle11_class0a_pc_taps = {}
for _, pc in ipairs(class0a_pcs) do
    oracle11_class0a_pc_taps[#oracle11_class0a_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_class0a_%06x", pc),
        function()
            if pc == 0x077ccc and class00_phase_hook ~= nil then
                class00_phase_hook("class0a_dispatch", pc)
            end
            local a6 = maincpu.state["A6"].value & 0xffffff
            emit_class0a_program("opcode_fetch", pc, a6, 0, 0, 0, false)
        end)
end

oracle11_class0a_write_taps = {}
for _, slot in ipairs({0xffc580, 0xffc600}) do
    oracle11_class0a_write_taps[#oracle11_class0a_write_taps + 1] =
        program:install_write_tap(slot, slot + 0x7f,
        string.format("oracle11_class0a_writes_%06x", slot),
        function(offset, data, mask)
            emit_class0a_program("write", maincpu.state["PC"].value &
                0xffffff, slot, offset - slot, data, mask, false)
        end)
end

function actor_pointer(value)
    if value >= 0x8000 then return 0xff0000 + value end
    return value
end

function hexv(value, digits)
    return string.format("%0" .. digits .. "x", value)
end

local class00_phase_ordinal = 0

local function emit_class00_scheduler_phase(event, pc)
    local child = 0xffce00
    if not capture_scene or frame < 5450 or frame > 5524 then return end
    class00_phase_ordinal = class00_phase_ordinal + 1
    class00_scheduler_phase:write(string.format(
        "%d\t%d\t%s\t%06x\t%04x\t%04x\t%08x\t%08x\t%d\t%08x\t%04x\t%04x\t%08x\t%08x\t%d\t%08x\n",
        frame, class00_phase_ordinal, event, pc,
        u16(0xff8384), u16(0xff8386), u32(0xff8390),
        u32(0xff8394), s16(u16(0xff8398)), u32(0xff839c),
        u16(child + 4), u16(child + 6), u32(child + 0x10),
        u32(child + 0x14), s16(u16(child + 0x18)),
        u32(child + 0x1c)))
end

class00_phase_hook = emit_class00_scheduler_phase

function emit_class00_program(event, pc, inner, data, mask, mutated)
    local slot = 0xffce00
    if not capture_scene or frame < 1972 or frame > capture_last_frame then
        return
    end
    if event ~= "write" and
            (u8(slot) == 0 or u8(slot + 2) ~= 0x00 or
             u8(slot + 8) ~= 28) then
        return
    end
    if event == "opcode_fetch" and
            (maincpu.state["A6"].value & 0xffffff) ~= slot then
        return
    end
    local parent_word = u16(slot + 0x5a)
    local parent = actor_pointer(parent_word)
    local parent_active = parent_word ~= 0 and u8(parent) or 0
    local parent_animation = parent_word ~= 0 and u32(parent + 0x1c) or 0
    class00_program:write(table.concat({
        frame, event, hexv(pc, 6),
        hexv(maincpu.state["PC"].value & 0xffffff, 6), hexv(slot, 6),
        hexv(inner, 2), u8(slot), hexv(u8(slot + 2), 2), u8(slot + 8),
        hexv(u8(slot + 3), 2), hexv(u16(slot + 4), 4),
        hexv(u16(slot + 6), 4), u8(slot + 0x0f),
        hexv(u32(slot + 0x10), 8), hexv(u32(slot + 0x14), 8),
        s16(u16(slot + 0x18)), hexv(u32(slot + 0x30), 8),
        hexv(u32(slot + 0x34), 8), hexv(u32(slot + 0x3c), 8),
        hexv(u32(slot + 0x1c), 8), hexv(u16(slot + 0x0a), 4),
        s16(u16(slot + 0x24)), hexv(parent, 6), parent_active,
        parent_word ~= 0 and hexv(u8(parent + 2), 2) or "00",
        parent_word ~= 0 and u8(parent + 8) or 0,
        parent_word ~= 0 and hexv(u16(parent + 4), 4) or "0000",
        parent_word ~= 0 and hexv(u16(parent + 6), 4) or "0000",
        parent_word ~= 0 and hexv(u32(parent + 0x10), 8) or "00000000",
        parent_word ~= 0 and hexv(u32(parent + 0x14), 8) or "00000000",
        parent_word ~= 0 and s16(u16(parent + 0x18)) or 0,
        hexv(parent_animation, 8),
        parent_animation ~= 0 and u8(parent_animation + 0x0f) or 0,
        parent_word ~= 0 and u8(parent + 0xd2) or 0,
        parent_word ~= 0 and u8(parent + 0x56) or 0,
        u8(slot + 0x2a), hexv(u16(slot + 0x2e), 4),
        u8(slot + 0x44), u8(slot + 0x45),
        hexv(u32(slot + 0x50), 8), u8(slot + 0x54),
        hexv(parent_word, 4), u8(slot + 0x5c), u8(slot + 0x62),
        u8(slot + 0x64), u8(slot + 0x65),
        s16(u16(global + 0x278)), u16(global + 8),
        hexv(u16(0xff81a8), 4),
        hexv(maincpu.state["D0"].value & 0xffffffff, 8),
        hexv(maincpu.state["D1"].value & 0xffffffff, 8),
        hexv(maincpu.state["D2"].value & 0xffffffff, 8),
        hexv(maincpu.state["A0"].value & 0xffffff, 6),
        hexv(maincpu.state["A1"].value & 0xffffff, 6),
        hexv(maincpu.state["A3"].value & 0xffffff, 6),
        hexv(maincpu.state["A4"].value & 0xffffff, 6),
        hexv(maincpu.state["A5"].value & 0xffffff, 6),
        hexv(maincpu.state["A6"].value & 0xffffff, 6),
        hexv(data & 0xffffffff, 8), hexv(mask & 0xffffffff, 8),
        mutated and 1 or 0
    }, "\t") .. "\n")
end

oracle11_class00_counterfactual_begin = opcodes:install_read_tap(
    0x09e426, 0x09e427, "oracle11_class00_counterfactual_begin",
    function()
        local slot = maincpu.state["A6"].value & 0xffffff
        if not class00_init_counterfactual or
                class00_init_counterfactual_count ~= 0 or
                slot ~= 0xffce00 or u8(slot + 2) ~= 0x00 or
                u8(slot + 8) ~= 28 or u16(slot + 4) ~= 0x0206 or
                u16(slot + 6) ~= 0x0200 then
            return
        end
        emit_class00_program("counterfactual_before", 0x09e426, 6,
            0, 0, true)
        program:write_u16(slot + 6, 0x0000)
        class00_counterfactual_active = true
        class00_init_counterfactual_count = 1
        emit_class00_program("counterfactual_after", 0x09e426, 6,
            0x00000000, 0x0000ffff, true)
    end)

oracle11_class00_counterfactual_end = opcodes:install_read_tap(
    0x09e458, 0x09e459, "oracle11_class00_counterfactual_end",
    function()
        local slot = maincpu.state["A6"].value & 0xffffff
        if not class00_counterfactual_active or slot ~= 0xffce00 then return end
        class00_counterfactual_active = false
        emit_class00_program("counterfactual_end", 0x09e458, 6,
            u16(slot + 6), 0x0000ffff, true)
    end)

class00_pcs = {
    0x09e098, 0x09e0ac, 0x09e0da, 0x09e0e0, 0x09e0f6,
    0x09e102, 0x09e10a, 0x09e114, 0x09e128, 0x09e134,
    0x09e138, 0x09e426, 0x09e43a, 0x09e442, 0x09e454,
    0x09e458, 0x09e46e, 0x09e478, 0x09e47c, 0x09e486,
    0x09e48c, 0x09e490, 0x09e492, 0x09e498, 0x09e514,
    0x09e52a, 0x09e552, 0x09e566, 0x09e56a, 0x09e56e,
    0x09e590, 0x09e5a6, 0x0bca3a, 0x0bca44, 0x0bca68,
    0x0bcaa0, 0x0bcaa6, 0x016518, 0x016536, 0x0167ac,
    0x01783e, 0x017c5e, 0x0ae396,
}
oracle11_class00_pc_taps = {}
for _, pc in ipairs(class00_pcs) do
    oracle11_class00_pc_taps[#oracle11_class00_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_class00_%06x", pc),
        function()
            if pc == 0x09e098 then
                emit_class00_scheduler_phase("class00_dispatch", pc)
            end
            emit_class00_program("opcode_fetch", pc, 0, 0, 0, false)
        end)
end

oracle11_class00_phase_taps = {}
for _, phase in ipairs({
        {0x0213d0, "exit_player_dispatch"},
        {0x016266, "exit_direct_writer"},
        {0x01a8f6, "exit_direct_writer"},
        {0x02177a, "exit_direct_writer"},
        {0x01bcda, "record28_scheduler"},
    }) do
    local pc = phase[1]
    local event = phase[2]
    oracle11_class00_phase_taps[#oracle11_class00_phase_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_class00_phase_%06x", pc),
        function() emit_class00_scheduler_phase(event, pc) end)
end

oracle11_class00_write_tap = program:install_write_tap(
    0xffce00, 0xffce7f, "oracle11_class00_writes",
    function(offset, data, mask)
        emit_class00_program("write", maincpu.state["PC"].value &
            0xffffff, offset - 0xffce00, data, mask, false)
    end)

local component20_pcs = {
    0x06b2fa, 0x06b30e, 0x06b358, 0x06b374, 0x06b38a,
    0x06b39a, 0x06b3c0, 0x06b3ea, 0x06b3f2, 0x06b42e,
    0x06b434, 0x06b44c, 0x06b534, 0x06b548, 0x06b588,
    0x06b5aa, 0x06b5ca, 0x06b624, 0x06b62a, 0x06b644,
    0x06b652, 0x06ed3e, 0x06ed52, 0x06ed8a, 0x06edb8,
    0x06edba, 0x06ee02, 0x06ee08, 0x06ee3c,
}
oracle11_component20_pc_taps = {}
for _, pc in ipairs(component20_pcs) do
    oracle11_component20_pc_taps[#oracle11_component20_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_component20_%06x", pc),
        function() emit_component20_dispatch(pc) end)
end

local function emit_player_dispatch(pc)
    emit_class00_scheduler_phase("player_dispatch", pc)
    if not capture_scene or frame < 2235 or frame > 2260 then return end
    local a6 = maincpu.state["A6"].value & 0xffffff
    local sp = maincpu.state["SP"].value & 0xffffff
    player_dispatch:write(string.format(
        "%d\t%06x\t%06x\t%06x\t%04x\t%04x\t%08x\t%04x\t%d\t%04x\t%04x\n",
        frame, pc, u32(sp) & 0xffffff, a6, u16(a6 + 4), u16(a6 + 6),
        u32(a6 + 0x1c), u16(a6 + 0x0a), s16(u16(a6 + 0x24)),
        u16(a6 + 0x2a), u16(global + 8)))
end

oracle11_player_animation_write_tap = program:install_write_tap(
    player + 0x0a, player + 0x27, "oracle11_player_animation_writes",
    function(offset, data, mask)
        if not capture_scene or frame < 2235 or frame > 2260 then return end
        local a6 = maincpu.state["A6"].value & 0xffffff
        player_animation_writes:write(string.format(
            "%d\t%06x\t%06x\t%06x\t%04x\t%04x\t%08x\t%04x\t%d\t%04x\t%08x\t%08x\n",
            frame, maincpu.state["PC"].value & 0xffffff, offset, a6,
            u16(player + 4), u16(player + 6), u32(player + 0x1c),
            u16(player + 0x0a), s16(u16(player + 0x24)),
            u16(player + 0x2a), data & 0xffffffff, mask & 0xffffffff))
    end)

oracle11_player_dispatch_pc_taps = {}
for _, pc in ipairs({0x0196ac, 0x0165c4}) do
    oracle11_player_dispatch_pc_taps[#oracle11_player_dispatch_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_player_dispatch_%06x", pc),
        function() emit_player_dispatch(pc) end)
end

local function emit_component20_collision(pc)
    if not capture_scene or frame < 2700 or frame > 2850 then return end
    local a6 = maincpu.state["A6"].value & 0xffffff
    local a1 = maincpu.state["A1"].value & 0xffffff
    if a6 ~= 0xffb100 and a1 ~= 0xffb100 and
            a6 ~= 0xffb300 and a1 ~= 0xffb300 then return end
    component20_collision:write(string.format(
        "%d\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\t%08x\t%08x\t%08x\t%08x\t%08x\t%08x\t%04x\t%04x\t%08x\t%02x\t%02x\t%d\n",
        frame, pc,
        maincpu.state["A0"].value & 0xffffff,
        maincpu.state["A1"].value & 0xffffff,
        maincpu.state["A2"].value & 0xffffff,
        maincpu.state["A3"].value & 0xffffff,
        maincpu.state["A4"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff, a6,
        maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        maincpu.state["D4"].value & 0xffffffff,
        maincpu.state["D5"].value & 0xffffffff,
        maincpu.state["D6"].value & 0xffffffff,
        maincpu.state["D7"].value & 0xffffffff,
        u16(a6 + 4), u16(a6 + 6), u32(a6 + 0x1c),
        u8(a6 + 0xa5), u8(a6 + 0xa6), s16(u16(a6 + 0x40))))
end

oracle11_component20_collision_pc_taps = {}
for _, pc in ipairs({0x01d87a, 0x01d4aa, 0x01d590, 0x01d598}) do
    oracle11_component20_collision_pc_taps[
        #oracle11_component20_collision_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_component20_collision_%06x", pc),
        function() emit_component20_collision(pc) end)
end

local function emit_type16_collision(pc)
    if not capture_scene or frame < 3200 or frame > 3900 then return end
    local a1 = maincpu.state["A1"].value & 0xffffff
    local a3 = maincpu.state["A3"].value & 0xffffff
    local a6 = maincpu.state["A6"].value & 0xffffff
    if u8(a6 + 8) ~= 16 or u8(a6 + 2) ~= 0x06 or a1 ~= 0xff8380 then
        return
    end
    type16_collision:write(string.format(
        "%d\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\t%08x\t%08x\t%08x\t%08x\t%08x\t%08x\t%04x\t%04x\t%08x\t%08x\t%04x\t%04x\t%08x\t%08x\t%08x\n",
        frame, pc,
        maincpu.state["A0"].value & 0xffffff, a1,
        maincpu.state["A2"].value & 0xffffff, a3,
        maincpu.state["A4"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff, a6,
        maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        maincpu.state["D4"].value & 0xffffffff,
        maincpu.state["D5"].value & 0xffffffff,
        maincpu.state["D6"].value & 0xffffffff,
        maincpu.state["D7"].value & 0xffffffff,
        u16(a6 + 4), u16(a6 + 6), u32(a6 + 0x1c), u32(a6 + 0x50),
        u16(a1 + 4), u16(a1 + 6), u32(a1 + 0x1c), u32(a1 + 0x50), a3))
end

oracle11_type16_collision_pc_taps = {}
for _, pc in ipairs({0x01d4aa, 0x01d590, 0x01d598, 0x01d5ee}) do
    oracle11_type16_collision_pc_taps[
        #oracle11_type16_collision_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_type16_collision_%06x", pc),
        function() emit_type16_collision(pc) end)
end
oracle11_type16_collision_damage_range_tap = opcodes:install_read_tap(
    0x01d5d0, 0x01d601, "oracle11_type16_collision_damage_range",
    function()
        emit_type16_collision(maincpu.state["PC"].value & 0xffffff)
    end)

oracle11_component20_global_write_tap = program:install_write_tap(
    0xff1a1c, 0xff1a1d, "oracle11_component20_global_writes",
    function(offset, data, mask)
        if not capture_scene or frame < 1972 or frame > capture_last_frame then
            return
        end
        component20_global:write(string.format(
            "%d\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%04x\t%08x\t%08x\t%d\t%d\t%d\t%d\t%d\n",
            frame, maincpu.state["PC"].value & 0xffffff, offset,
            maincpu.state["A1"].value & 0xffffff,
            maincpu.state["A3"].value & 0xffffff,
            maincpu.state["A4"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff,
            u16(0xff1a1c), data & 0xffffffff, mask & 0xffffffff,
            u16(0xff1a18), u16(0xff1a1a), u16(0xff1a1c),
            u16(global + 8), s16(u16(global + 0x278))))
    end)

oracle11_component20_write_tap = program:install_write_tap(
    0xffb100, 0xffb67f, "oracle11_component20_writes",
    function(offset, data, mask)
        if not capture_scene or frame < 1972 or frame > capture_last_frame then
            return
        end
        local slot = offset - ((offset - 0xffae80) % 0x80)
        if not component20_slots[slot] then return end
        local a4 = maincpu.state["A4"].value & 0xffffff
        local a6 = maincpu.state["A6"].value & 0xffffff
        component20_writes:write(string.format(
            "%d\t%06x\t%06x\t%02x\t%06x\t%06x\t%06x\t%06x\t%d\t%02x\t%d\t%04x\t%04x\t%02x\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%04x\t%02x\t%02x\t%02x\t%d\t%d\t%d\t%d\t%04x\t%08x\t%08x\n",
            frame, maincpu.state["PC"].value & 0xffffff, slot,
            offset - slot, maincpu.state["A1"].value & 0xffffff,
            maincpu.state["A3"].value & 0xffffff, a4, a6,
            u8(slot), u8(slot + 2),
            u8(slot + 8), u16(slot + 4), u16(slot + 6), u8(slot + 3),
            u32(slot + 0x10), u32(slot + 0x14), s16(u16(slot + 0x18)),
            u32(slot + 0x1c), u16(slot + 0x0a), s16(u16(slot + 0x24)),
            u16(slot + 0x2a), u8(slot + 0x42), u8(slot + 0x4c),
            u8(slot + 0x66), u16(0xff1a18), u16(0xff1a1a),
            u16(global + 8), s16(u16(global + 0x278)), u16(0xff81a8),
            data & 0xffffffff, mask & 0xffffffff))
    end)

local function suppress_selected_scene_pair()
    if not capture_scene or suppress_scene_pair_type == nil or
            suppress_scene_pair_class == nil or frame < 1972 or
            frame > capture_last_frame then return end
    for _, pool_spec in ipairs(scene_pools) do
        if pool_spec.type == suppress_scene_pair_type then
            for index = 0, pool_spec.count - 1 do
                local slot = pool_spec.base + index * pool_spec.stride
                if u8(slot) ~= 0 and u8(slot + 2) == suppress_scene_pair_class and
                        u8(slot + 8) == suppress_scene_pair_type then
                    pair_suppression:write(string.format(
                        "%d\t%s\t%06x\t%d\t%02x\t%04x\t%04x\t%08x\t%d\t%04x\t%04x\t%d\t%d\t%d\t%04x\n",
                        frame, pool_spec.name, slot, suppress_scene_pair_type,
                        suppress_scene_pair_class, u16(slot + 4),
                        u16(slot + 6), u32(slot + 0x1c), u16(global + 8),
                        u16(0xff8384), u16(0xff8386),
                        s16(u16(0xff83c0)), s16(u16(global + 0x278)),
                        s16(u16(global + 0x27c)), u16(0xff81a8)))
                    program:write_u8(slot, 0)
                    scene_pair_suppressed_actors =
                        scene_pair_suppressed_actors + 1
                end
            end
        end
    end
end

local record4_base, record4_stride, record4_count = 0xff8680, 0x80, 24

local function emit_type4_class03_event(event, pc, slot, inner, data, mask,
        suppressed)
    local owner_word = u16(slot + 0x28)
    local owner_slot = owner_word >= 0x8000 and (0xff0000 | owner_word) or
        owner_word
    type4_class03:write(string.format(
        "%d\t%s\t%06x\t%06x\t%02x\t%06x\t%06x\t%d\t%02x\t%d\t%04x\t%04x\t%d\t%08x\t%08x\t%d\t%04x\t%06x\t%08x\t%08x\t%08x\t%d\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%08x\t%08x\t%08x\t%08x\t%08x\t%08x\t%d\n",
        frame, event, pc, slot, inner,
        maincpu.state["A6"].value & 0xffffff,
        maincpu.state["A4"].value & 0xffffff,
        u8(slot), u8(slot + 2), u8(slot + 8), u16(slot + 4),
        u16(slot + 6), u8(slot + 0x0f), u32(slot + 0x10),
        u32(slot + 0x14), s16(u16(slot + 0x18)), owner_word, owner_slot,
        u32(slot + 0x20), u32(slot + 0x1c), u32(slot + 0x50),
        s16(u16(slot + 0x40)), u8(slot + 5), u8(slot + 0x0c),
        u8(slot + 0x19), u8(slot + 0x2a), u8(slot + 0x2b),
        u8(slot + 0x5c), u8(slot + 0x65),
        maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        data & 0xffffffff, mask & 0xffffffff, suppressed and 1 or 0))
end

local function class1f_actor_at_a6()
    local a6 = maincpu.state["A6"].value & 0xffffff
    if a6 < pool or a6 >= pool + count * stride or
            ((a6 - pool) % stride) ~= 0 then return nil end
    if u8(a6) == 0 or u8(a6 + 2) ~= 0x1f or u8(a6 + 8) ~= 12 then
        return nil
    end
    return a6
end

local function emit_action4_timer_event(event, pc)
    if not capture_scene or frame < 1972 or frame > capture_last_frame then
        return
    end
    local slot = class1f_actor_at_a6()
    if slot == nil or u16(slot + 4) ~= 0x0200 or
            (u16(slot + 6) >> 8) ~= 0x04 then return end
    action4_timers:write(string.format(
        "%d\t%s\t%06x\t%06x\t%04x\t%04x\t%04x\t%04x\t%08x\t%04x\t00000000\t00000000\t0\n",
        frame, event, pc, slot, u16(slot + 4), u16(slot + 6),
        u16(0xff81ea), u16(0xff81a8),
        maincpu.state["D0"].value & 0xffffffff, u16(slot + 0x2a)))
    action4_timer_events = action4_timer_events + 1
    if capture_class1f_action4_guard and pc == 0x060944 then
        action4_guard:write(string.format(
            "%d\tguard\t%06x\t%06x\t%04x\t%04x\t%02x\t%04x\t%08x\t%04x\t%d\t00000000\t00000000\n",
            frame, pc, slot, u16(slot + 4), u16(slot + 6),
            u8(slot + 0x6e), u16(slot + 0x2a), u32(slot + 0x1c),
            u16(slot + 0x0a), s16(u16(slot + 0x24))))
    end
end

oracle11_action4_guard_write = program:install_write_tap(
    pool, pool + count * stride - 1, "oracle11_action4_guard_write",
    function(offset, data, mask)
        if not capture_class1f_action4_guard or frame < 1972 or
                frame > capture_last_frame then return end
        local relative = offset - pool
        local slot = pool + math.floor(relative / stride) * stride
        local inner = relative % stride
        if inner ~= 0x6e or u8(slot + 2) ~= 0x1f or
                u8(slot + 8) ~= 12 then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        action4_guard:write(string.format(
            "%d\twrite\t%06x\t%06x\t%04x\t%04x\t%02x\t%04x\t%08x\t%04x\t%d\t%08x\t%08x\n",
            frame, pc, slot, u16(slot + 4), u16(slot + 6),
            u8(slot + 0x6e), u16(slot + 0x2a), u32(slot + 0x1c),
            u16(slot + 0x0a), s16(u16(slot + 0x24)),
            data & 0xffffffff, mask & 0xffffffff))
    end)

local function emit_transaction(pc)
    if frame < 1972 or frame > capture_last_frame then return end
    local a4 = maincpu.state["A4"].value & 0xffffff
    local a6 = maincpu.state["A6"].value & 0xffffff
    local actor_ok = a4 >= pool and a4 < pool + count * stride and
        ((a4 - pool) % stride) == 0
    local b = actor_ok and a4 or pool
    transactions:write(string.format(
        "%d\t%06x\t%06x\t%06x\t%02x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%02x\t%02x\t%d\t%d\t%04x\t%08x\t%08x\t%08x\t%d\t%02x\t%d\t%d\t%d\t%d\t%d\t%d\t%02x\t%d\t%02x\n",
        frame, pc, a4, a6, u8(global + 0x19), u16(0xff1a18), u16(0xff1a1a),
        u16(controller + 4), u16(controller + 6), u16(controller + 0x40),
        u16(controller + 0x42), u16(controller + 0x4a),
        u16(controller + 0x10), u8(controller + 0x2e),
        u8(controller + 0x2c), s16(u16(global + 0x278)),
        s16(u16(global + 0x27c)), u16(0xff81a8),
        maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        actor_ok and u8(b) or 0, actor_ok and u8(b + 2) or 0,
        actor_ok and u8(b + 8) or 0, actor_ok and u16(b + 4) or 0,
        actor_ok and u16(b + 6) or 0, actor_ok and s16(u16(b + 0x10)) or 0,
        actor_ok and s16(u16(b + 0x14)) or 0,
        actor_ok and s16(u16(b + 0x18)) or 0,
        actor_ok and u8(b + 3) or 0, actor_ok and u16(b + 0x2a) or 0,
        actor_ok and u8(b + 0x83) or 0))
    if pc == 0x028a3a then main_spawns = main_spawns + 1 end
    if pc == 0x028b76 then aux_spawns = aux_spawns + 1 end
end

oracle11_action4_timer_pc_taps = {
    opcodes:install_read_tap(0x0bc416, 0x0bc417,
        "oracle11_action4_timer_entry",
        function() emit_action4_timer_event("entry", 0x0bc416) end),
    opcodes:install_read_tap(0x0bc420, 0x0bc421,
        "oracle11_action4_timer_rng_masked",
        function() emit_action4_timer_event("rng_masked", 0x0bc420) end),
    opcodes:install_read_tap(0x0bc424, 0x0bc425,
        "oracle11_action4_timer_stage_read",
        function() emit_action4_timer_event("stage_read", 0x0bc424) end),
    opcodes:install_read_tap(0x0bc434, 0x0bc435,
        "oracle11_action4_timer_table_lookup",
        function() emit_action4_timer_event("table_lookup", 0x0bc434) end),
    opcodes:install_read_tap(0x0bc438, 0x0bc439,
        "oracle11_action4_timer_result",
        function() emit_action4_timer_event("result", 0x0bc438) end),
    opcodes:install_read_tap(0x060940, 0x060941,
        "oracle11_action4_timer_caller_write",
        function() emit_action4_timer_event("caller_write", 0x060940) end),
    opcodes:install_read_tap(0x060944, 0x060945,
        "oracle11_action4_timer_caller_after_write",
        function() emit_action4_timer_event("caller_after_write", 0x060944) end),
}

oracle11_action4_timer_write = program:install_write_tap(
    pool, pool + count * stride - 1, "oracle11_action4_timer_write",
    function(offset, data, mask)
        if not capture_scene or frame < 1972 or frame > capture_last_frame then
            return
        end
        local pc = maincpu.state["PC"].value & 0xffffff
        local relative = offset - pool
        local slot = pool + math.floor(relative / stride) * stride
        local inner = relative % stride
        if inner < 0x28 or inner > 0x2b or u8(slot + 2) ~= 0x1f or
                u8(slot + 8) ~= 12 or u16(slot + 4) ~= 0x0200 or
                (u16(slot + 6) >> 8) ~= 0x04 then return end
        local suppressed = suppress_action4_timer and pc == 0x060944
        action4_timers:write(string.format(
            "%d\twrite\t%06x\t%06x\t%04x\t%04x\t%04x\t%04x\t%08x\t%04x\t%08x\t%08x\t%d\n",
            frame, pc, slot, u16(slot + 4), u16(slot + 6),
            u16(0xff81ea), u16(0xff81a8),
            maincpu.state["D0"].value & 0xffffffff, u16(slot + 0x2a),
            data & 0xffffffff, mask & 0xffffffff,
            suppressed and 1 or 0))
        action4_timer_events = action4_timer_events + 1
        if suppressed then
            action4_timer_suppressed_writes =
                action4_timer_suppressed_writes + 1
            return u32(offset & 0xfffffc)
        end
    end)

local type4_class03_pcs = {
    0x030382, 0x030396, 0x030416, 0x03042e, 0x030456, 0x030466,
    0x030482, 0x0304ae, 0x0304ea, 0x0304f0, 0x0304f6, 0x030510,
    0x030556, 0x03057a, 0x03058a, 0x030594, 0x0305a4, 0x0305b4,
    0x0305c6, 0x0305ce, 0x03062c, 0x030632,
}
oracle11_type4_class03_pc_taps = {}
local function install_type4_class03_pc_tap(pc)
    return opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_type4_class03_%06x", pc), function()
            if not capture_scene or frame < 4650 or frame > 4750 then return end
            local a6 = maincpu.state["A6"].value & 0xffffff
            if a6 < record4_base or
                    a6 >= record4_base + record4_count * record4_stride or
                    ((a6 - record4_base) % record4_stride) ~= 0 then return end
            if u8(a6 + 2) ~= 3 and a6 ~= 0xff8700 then return end
            emit_type4_class03_event("pc", pc, a6, 0, 0, 0, false)
        end)
end
for _, pc in ipairs(type4_class03_pcs) do
    oracle11_type4_class03_pc_taps[#oracle11_type4_class03_pc_taps + 1] =
        install_type4_class03_pc_tap(pc)
end

oracle11_type4_class03_writes = program:install_write_tap(
    record4_base, record4_base + record4_count * record4_stride - 1,
    "oracle11_type4_class03_writes", function(offset, data, mask)
        if not capture_scene or frame < 4650 or frame > 4750 then return end
        local relative = offset - record4_base
        local slot = record4_base +
            math.floor(relative / record4_stride) * record4_stride
        local inner = relative % record4_stride
        if slot ~= 0xff8700 and u8(slot + 2) ~= 3 then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        local suppressed = suppress_type4_class03_pc ~= nil and
            pc == suppress_type4_class03_pc and slot == 0xff8700 and
            inner <= 3
        emit_type4_class03_event("write", pc, slot, inner, data, mask,
            suppressed)
        if suppressed then
            type4_class03_suppressed_writes =
                type4_class03_suppressed_writes + 1
            return u32(offset & 0xfffffc)
        end
    end)

oracle11_type36_writes = program:install_write_tap(
    0xffd280, 0xffe27f, "oracle11_type36_writes",
    function(offset, data, mask)
        if not capture_scene or frame < 1972 or frame > capture_last_frame then
            return
        end
        local relative = offset - 0xffd280
        local slot = 0xffd280 + math.floor(relative / 0x40) * 0x40
        local inner = relative % 0x40
        local pc = maincpu.state["PC"].value & 0xffffff
        local suppressed = suppress_type36_pc ~= nil and
            suppress_type36_class ~= nil and
            (pc == suppress_type36_pc or pc == suppress_type36_pc2) and
            (u8(slot + 2) == suppress_type36_class or
             (inner <= 2 and inner + 3 >= 2))
        local parent = maincpu.state["A6"].value & 0xffffff
        local sp = maincpu.state["SP"].value & 0xffffff
        type36_writes:write(string.format(
            "%d\t%06x\t%02x\t%06x\t%06x\t%d\t%02x\t%d\t%04x\t%04x\t%08x\t%06x\t%d\t%d\t%02x\t%d\t%04x\t%04x\t%02x\t%08x\t%04x\t%d\t%08x\t%08x\t%d\n",
            frame, slot, inner, pc, parent, u8(parent), u8(parent + 2),
            u8(parent + 8), u16(parent + 4), u16(parent + 6),
            u32(parent + 0x1c), u32(sp) & 0xffffff, u16(global + 8), u8(slot),
            u8(slot + 2), u8(slot + 8), u16(slot + 4), u16(slot + 6),
            u8(slot + 3), u32(slot + 0x1c), u16(slot + 0x0a),
            s16(u16(slot + 0x24)), data & 0xffffffff,
            mask & 0xffffffff, suppressed and 1 or 0))
        if suppressed then
            type36_suppressed_writes = type36_suppressed_writes + 1
            return u32(offset & 0xfffffc)
        end
    end)

local obstacle_slot = 0xffb380
local function emit_obstacle_trace(pc)
    if not capture_scene or frame < 1972 or frame > capture_last_frame or
            (maincpu.state["A6"].value & 0xffffff) ~= obstacle_slot then
        return
    end
    obstacle_trace:write(string.format(
        "%d\t%06x\t%04x\t%04x\t%d\t%02x\t%d\t%d\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%02x\t%02x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%02x\t%08x\t%08x\t%08x\t%08x\t%08x\t%08x\t%04x\t%04x\t%04x\t%04x\t%02x\t%d\t%04x\t%08x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\n",
        frame, pc, u16(obstacle_slot + 4), u16(obstacle_slot + 6),
        u8(obstacle_slot), u8(obstacle_slot + 2), u8(obstacle_slot + 8),
        u8(obstacle_slot + 0x0f), u32(obstacle_slot + 0x10),
        u32(obstacle_slot + 0x14), s16(u16(obstacle_slot + 0x18)),
        u32(obstacle_slot + 0x1c), u16(obstacle_slot + 0x0a),
        s16(u16(obstacle_slot + 0x24)), u8(obstacle_slot + 6),
        u8(obstacle_slot + 0x0c), u16(obstacle_slot + 0x18),
        u16(obstacle_slot + 0x24), u16(obstacle_slot + 0x2a),
        u16(obstacle_slot + 0x2e), u16(obstacle_slot + 0x30),
        u16(obstacle_slot + 0x32), u16(obstacle_slot + 0x34),
        u16(obstacle_slot + 0x36), u16(obstacle_slot + 0x38),
        u16(obstacle_slot + 0x3a), u16(obstacle_slot + 0x3c),
        u16(obstacle_slot + 0x3e), u16(obstacle_slot + 0x40),
        u16(obstacle_slot + 0x42), u8(obstacle_slot + 0x4f),
        u32(obstacle_slot + 0x50), u32(obstacle_slot + 0x58),
        u32(obstacle_slot + 0x60), u32(obstacle_slot + 0x64),
        u32(obstacle_slot + 0x68), u32(obstacle_slot + 0x6c),
        u16(obstacle_slot + 0x78), u16(obstacle_slot + 0x7a),
        u16(obstacle_slot + 0x7c), u16(obstacle_slot + 0x7e),
        u8(0xffee8f),
        u16(global + 8), u16(0xff81a8),
        maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        maincpu.state["A0"].value & 0xffffff,
        maincpu.state["A1"].value & 0xffffff,
        maincpu.state["A2"].value & 0xffffff,
        maincpu.state["A3"].value & 0xffffff,
        maincpu.state["A4"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff))
end

local obstacle_pcs = {
    0x06de92, 0x06dea6, 0x06deac, 0x06deb0, 0x06dee0, 0x06deea,
    0x06df0a, 0x06df10, 0x06df16, 0x06df1c, 0x06df22, 0x06df34,
    0x06df38, 0x06df3c, 0x06df42, 0x06df48, 0x06df5a, 0x06df66,
    0x06df6c, 0x06df72, 0x06df78, 0x06df7c, 0x06df80, 0x06df84,
    0x06df8a, 0x06df96, 0x06dfa0, 0x06dff0, 0x06dff4, 0x06dff8,
    0x06e00a, 0x06e010, 0x06e040, 0x06e09a, 0x06e0b2, 0x06e0fe,
    0x06e126, 0x06e12a, 0x01d458, 0x01d466, 0x01d46c, 0x01d472,
    0x01d4aa, 0x01d590, 0x01d598,
}
oracle11_obstacle_pc_taps = {}
for _, pc in ipairs(obstacle_pcs) do
    oracle11_obstacle_pc_taps[#oracle11_obstacle_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_obstacle_%06x", pc),
        function() emit_obstacle_trace(pc) end)
end

oracle11_obstacle_writes = program:install_write_tap(
    obstacle_slot, obstacle_slot + 0x7f, "oracle11_obstacle_writes",
    function(offset, data, mask)
        if not capture_scene or frame < 1972 or frame > capture_last_frame then
            return
        end
        local pc = maincpu.state["PC"].value & 0xffffff
        local suppressed = suppress_obstacle_transition and pc == 0x01d4aa and
            offset <= obstacle_slot + 7 and offset + 3 >= obstacle_slot + 4
        obstacle_writes:write(string.format(
            "%d\t%06x\t%02x\t%04x\t%04x\t%d\t%02x\t%d\t%08x\t%04x\t%d\t%d\t%02x\t%08x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\t%d\n",
            frame, pc, offset - obstacle_slot, u16(obstacle_slot + 4),
            u16(obstacle_slot + 6), u8(obstacle_slot),
            u8(obstacle_slot + 2), u8(obstacle_slot + 8),
            u32(obstacle_slot + 0x1c), u16(obstacle_slot + 0x0a),
            s16(u16(obstacle_slot + 0x24)),
            s16(u16(obstacle_slot + 0x40)), u8(0xffee8f),
            maincpu.state["D0"].value & 0xffffffff,
            maincpu.state["D1"].value & 0xffffffff,
            maincpu.state["D2"].value & 0xffffffff,
            maincpu.state["D3"].value & 0xffffffff,
            maincpu.state["A0"].value & 0xffffff,
            maincpu.state["A1"].value & 0xffffff,
            maincpu.state["A2"].value & 0xffffff,
            maincpu.state["A3"].value & 0xffffff,
            maincpu.state["A4"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            data & 0xffffffff,
            mask & 0xffffffff, suppressed and 1 or 0))
        if suppressed then
            obstacle_transition_suppressed_writes =
                obstacle_transition_suppressed_writes + 1
            return u32(offset & 0xfffffc)
        end
    end)

oracle11_obstacle_guard_write = program:install_write_tap(
    0xffee8e, 0xffee8f, "oracle11_obstacle_guard_write",
    function(offset, data, mask)
        if not capture_scene or frame < 1972 or frame > capture_last_frame then
            return
        end
        obstacle_guard:write(string.format(
            "%d\t%06x\t%02x\t%08x\t%08x\t%d\t%04x\t%04x\t%08x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\n",
            frame, maincpu.state["PC"].value & 0xffffff, u8(0xffee8f),
            data & 0xffffffff, mask & 0xffffffff, u16(global + 8),
            u16(obstacle_slot + 4), u16(obstacle_slot + 6),
            maincpu.state["D0"].value & 0xffffffff,
            maincpu.state["D1"].value & 0xffffffff,
            maincpu.state["D2"].value & 0xffffffff,
            maincpu.state["D3"].value & 0xffffffff,
            maincpu.state["A0"].value & 0xffffff,
            maincpu.state["A1"].value & 0xffffff,
            maincpu.state["A2"].value & 0xffffff,
            maincpu.state["A3"].value & 0xffffff,
            maincpu.state["A4"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff))
    end)

oracle11_progression_pc_taps = {}
for pc in pairs(target_pcs) do
    oracle11_progression_pc_taps[#oracle11_progression_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_progression_%06x", pc),
        function() emit_transaction(pc) end)
end

oracle11_controller_substate_write = program:install_write_tap(
    controller + 4, controller + 0x47,
    "oracle11_controller_substate_write",
    function(offset, data, mask)
        if not capture_controller_substate or frame < 2670 or frame > 2690 then
            return
        end
        local inner = offset - controller
        if not ((inner >= 4 and inner <= 7) or
                (inner >= 0x44 and inner <= 0x47)) then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        local suppressed = suppress_controller_substate_pc ~= nil and
            pc == suppress_controller_substate_pc and inner >= 4 and inner <= 7
        controller_substate_writes:write(string.format(
            "%d\t%06x\t%06x\t%04x\t%04x\t%04x\t%06x\t%08x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\t%08x\t%d\n",
            frame, pc, offset, u16(controller + 4), u16(controller + 6),
            u16(controller + 0x44),
            maincpu.state["A6"].value & 0xffffff,
            maincpu.state["D0"].value & 0xffffffff,
            maincpu.state["D1"].value & 0xffffffff,
            maincpu.state["D2"].value & 0xffffffff,
            maincpu.state["D3"].value & 0xffffffff,
            maincpu.state["A0"].value & 0xffffff,
            maincpu.state["A1"].value & 0xffffff,
            maincpu.state["A2"].value & 0xffffff,
            maincpu.state["A3"].value & 0xffffff,
            maincpu.state["A4"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            u32(offset & 0xfffffc), data & 0xffffffff,
            mask & 0xffffffff, suppressed and 1 or 0))
        if suppressed then return u32(offset & 0xfffffc) end
    end)

oracle11_progression_spawn_suppress = program:install_write_tap(
    pool, pool + count * stride - 1, "oracle11_progression_spawn_suppress",
    function(offset, data, mask)
        if frame < 1972 or frame > capture_last_frame then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        local relative = offset - pool
        local slot = pool + math.floor(relative / stride) * stride
        local inner = relative % stride
        local owned = (pc >= 0x028a12 and pc <= 0x028ab2) or
            (pc >= 0x028b5a and pc <= 0x028ba4) or
            ((slot == 0xffa3c0 or slot == 0xffa000) and
             pc >= 0x060532 and pc <= 0x061152)
        if not owned then return end
        local suppressed = suppress_spawn and pc == 0x028a3e and inner <= 1
        writes:write(string.format(
            "%d\t%06x\t%02x\t%06x\t%06x\t%08x\t%08x\t%08x\t%02x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%04x\t%d\n",
            frame, slot, inner, pc, maincpu.state["A6"].value & 0xffffff,
            u32(offset & 0xfffffc), data & 0xffffffff, mask & 0xffffffff,
            u8(global + 0x19), u16(0xff1a18), u16(0xff1a1a),
            u16(controller + 4), u16(controller + 6),
            u16(controller + 0x40), u16(controller + 0x4a),
            u16(controller + 0x10),
            s16(u16(global + 0x278)), s16(u16(global + 0x27c)),
            u16(0xff81a8), suppressed and 1 or 0))
        if suppressed then
            suppressed_writes = suppressed_writes + 1
            return u32(offset & 0xfffffc)
        end
    end)

oracle11_progression_global_writes = program:install_write_tap(
    0xff1a10, 0xff1a13, "oracle11_progression_global_writes",
    function(offset, data, mask)
        if frame < 1972 or frame > capture_last_frame then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        local a6 = maincpu.state["A6"].value & 0xffffff
        local owner_type = 0
        if a6 >= pool and a6 < pool + count * stride and
                ((a6 - pool) % stride) == 0 then
            owner_type = 12
        elseif a6 >= pool24 and a6 < pool24 + count24 * stride24 and
                ((a6 - pool24) % stride24) == 0 then
            owner_type = 24
        end
        local owner_ok = owner_type ~= 0
        local suppressed = suppress_guard and pc == 0x08da38
        global_writes:write(string.format(
            "%d\t%06x\t%06x\t%06x\t%d\t%02x\t%d\t%d\t%d\t%08x\t%08x\t%08x\t%02x\t%d\t%d\t%02x\t%d\n",
            frame, offset, pc, a6, owner_ok and u8(a6) or 0,
            owner_ok and u8(a6 + 2) or 0, owner_type,
            owner_ok and u16(a6 + 4) or 0, owner_ok and u16(a6 + 6) or 0,
            u32(offset & 0xfffffc), data & 0xffffffff, mask & 0xffffffff,
            u8(0xff1a11), u16(controller + 4), u16(controller + 0x42),
            u8(global + 0x19), suppressed and 1 or 0))
        if suppressed then return (data | mask) & 0xffffffff end
    end)

oracle11_progression_lifecycle_writes = program:install_write_tap(
    0xff1a18, 0xff1a1b, "oracle11_progression_lifecycle_writes",
    function(offset, data, mask)
        if not capture_lifecycle or frame < 1972 or frame > capture_last_frame then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        local a6 = maincpu.state["A6"].value & 0xffffff
        local owner_ok = a6 >= pool and a6 < pool + count * stride and
            ((a6 - pool) % stride) == 0
        local suppressed = suppress_lifecycle and pc == 0x061152 and
            offset <= 0xff1a19 and u16(0xff1a18) ~= 0
        lifecycle_writes:write(string.format(
            "%d\t%06x\t%06x\t%06x\t%d\t%02x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%08x\t%d\t%d\t%08x\t%08x\t%d\n",
            frame, offset, pc, a6, owner_ok and u8(a6) or 0,
            owner_ok and u8(a6 + 2) or 0, owner_ok and u8(a6 + 8) or 0,
            owner_ok and u16(a6 + 4) or 0,
            owner_ok and u16(a6 + 6) or 0,
            owner_ok and s16(u16(a6 + 0x10)) or 0,
            owner_ok and s16(u16(a6 + 0x14)) or 0,
            owner_ok and s16(u16(a6 + 0x18)) or 0,
            owner_ok and s16(u16(a6 + 0x40)) or 0,
            owner_ok and u32(a6 + 0x1c) or 0,
            u16(0xff1a18), u16(0xff1a1a), data & 0xffffffff,
            mask & 0xffffffff, suppressed and 1 or 0))
        if suppressed then
            lifecycle_suppressed_writes = lifecycle_suppressed_writes + 1
            return u16(0xff1a18)
        end
    end)

local class1f_inner8_group_mutation_prepared = false
local class1f_inner8_group_mutated = false

local function emit_class1f_inner8_group(event, pc, slot, data, mask)
    if not capture_class1f_inner8_group or frame < 1972 or
            frame > capture_last_frame or slot < pool or
            slot >= pool + count * stride or u8(slot) == 0 or
            u8(slot + 2) ~= 0x1f or u8(slot + 8) ~= 12 then return end
    local mutated = 0
    if mutate_class1f_inner8_group and not class1f_inner8_group_mutated and
            class1f_inner8_group_mutation_prepared and event == "entry" and
            pc == 0x041c36 and frame == 3004 and slot == 0xffa3c0 then
        class1f_inner8_group_mutated = true
        mutated = 1
    end
    class1f_inner8_group:write(string.format(
        "%d\t%s\t%06x\t%06x\t%04x\t%04x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%04x\t%d\t%d\t%d\t%d\t%08x\t%08x\t%d\t%d\t%d\t%08x\t%08x\t%08x\t%08x\t%08x\t%d\n",
        frame, event, pc, slot, u16(slot + 4), u16(slot + 6),
        u8(slot + 0x86), s8(u8(slot + 0x87)), u8(slot + 0x87),
        u8(slot + 0x89), u8(slot + 0x8a), u8(slot + 0x0c),
        s16(u16(slot + 0x60)), s16(u16(slot + 0x62)),
        u8(slot + 0x85), u8(slot + 0xa3), u16(0xff81a8),
        u8(0xff1a3c), u8(0xff1a3d), u8(0xff1a3e), u8(0xff1a3f),
        u32(slot + 0x10), u32(slot + 0x14), s16(u16(slot + 0x18)),
        s16(u16(global + 0x278)), s16(u16(global + 0x27c)),
        maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        data or 0, mask or 0, mutated))
end

local function emit_class1f_inner8_group_entry(pc)
    local slot = maincpu.state["A6"].value & 0xffffff
    if mutate_class1f_inner8_group and
            not class1f_inner8_group_mutation_prepared and pc == 0x041c36 and
            frame == 3004 and slot == 0xffa3c0 then
        emit_class1f_inner8_group("mutation_before", pc, slot, 0, 0)
        program:write_u16(0xff81a8, 0x0101)
        class1f_inner8_group_mutation_prepared = true
    end
    emit_class1f_inner8_group("entry", pc, slot, 0, 0)
end

oracle11_class1f_inner8_group_pc_taps = {}
for _, pc in ipairs({0x041c36, 0x041c70, 0x041c7a, 0x041d04, 0x041d50,
                     0x041d6c, 0x041d9c}) do
    oracle11_class1f_inner8_group_pc_taps[
        #oracle11_class1f_inner8_group_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_class1f_inner8_group_%06x", pc),
        function() emit_class1f_inner8_group_entry(pc) end)
end

oracle11_class1f_inner8_group_actor_writes = program:install_write_tap(
    pool, pool + count * stride - 1,
    "oracle11_class1f_inner8_group_actor_writes",
    function(offset, data, mask)
        if not capture_class1f_inner8_group then return end
        local relative = offset - pool
        local slot = pool + math.floor(relative / stride) * stride
        local inner = relative % stride
        if inner ~= 0x86 and inner ~= 0x87 and inner ~= 0x89 and
                inner ~= 0x8a then return end
        emit_class1f_inner8_group("actor_write", maincpu.state["PC"].value &
            0xffffff, slot, data & 0xffffffff, mask & 0xffffffff)
    end)

oracle11_class1f_inner8_group_global_writes = program:install_write_tap(
    0xff1a3c, 0xff1a3f, "oracle11_class1f_inner8_group_global_writes",
    function(offset, data, mask)
        if not capture_class1f_inner8_group then return end
        local slot = maincpu.state["A6"].value & 0xffffff
        emit_class1f_inner8_group("occupancy_write",
            maincpu.state["PC"].value & 0xffffff, slot,
            data & 0xffffffff, mask & 0xffffffff)
    end)

local class1f_action0c_mutated = false

local function emit_class1f_action0c(event, pc, slot, inner, data, mask, mutated)
    if not capture_class1f_action0c or frame < 1972 or frame > 5566 then
        return
    end
    if slot < pool or slot >= pool + count * stride or
            ((slot - pool) % stride) ~= 0 or u8(slot) == 0 or
            u8(slot + 2) ~= 0x1f or u8(slot + 8) ~= 12 or
            u16(slot + 4) ~= 0x0208 then
        return
    end
    if pc ~= 0x041dfe and u8(slot + 6) ~= 0x0c then return end
    class1f_action0c:write(string.format(
        "%d\t%s\t%06x\t%06x\t%02x\t%04x\t%04x\t%02x\t%d\t%02x\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%02x\t%02x\t%02x\t%04x\t%04x\t%02x\t%04x\t%04x\t%04x\t%04x\t%08x\t%08x\t%08x\t%08x\t%06x\t%06x\t%08x\t%08x\t%d\n",
        frame, event, pc, slot, inner, u16(slot + 4), u16(slot + 6),
        u8(slot + 3), u8(slot + 0x0f), u8(slot + 0x0c),
        u32(slot + 0x10), u32(slot + 0x14), s16(u16(slot + 0x18)),
        u32(slot + 0x1c), u16(slot + 0x0a), s16(u16(slot + 0x24)),
        u8(slot + 0x2a), u8(slot + 0x6e), u8(slot + 0x85),
        u16(slot + 0x80), u16(slot + 0x82), u8(slot + 0x95),
        u16(slot + 0x96), u16(slot + 0x98), u16(slot + 0x28),
        u16(0xff81a8), maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        maincpu.state["A0"].value & 0xffffff,
        maincpu.state["A4"].value & 0xffffff,
        data & 0xffffffff, mask & 0xffffffff, mutated and 1 or 0))
end

oracle11_class1f_action0c_pc_taps = {}
for _, pc in ipairs({
        0x041dfe, 0x040dc0, 0x040dce, 0x040df8, 0x040dfe,
        0x041054, 0x041080, 0x0410a6, 0x0410b6, 0x0410de,
        0x040e06, 0x040e0e, 0x040e12, 0x040e1c,
        0x040e24, 0x040e2a, 0x040e30, 0x040e34, 0x040e38,
        0x040e40, 0x040e4e, 0x040e54, 0x040e5c,
        0x040e62, 0x040e68, 0x040e72, 0x040e7e}) do
    oracle11_class1f_action0c_pc_taps[
        #oracle11_class1f_action0c_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_class1f_action0c_%06x", pc),
        function()
            local slot = maincpu.state["A6"].value & 0xffffff
            emit_class1f_action0c("entry", pc, slot, 0xff, 0, 0, false)
            if mutate_class1f_action0c and not class1f_action0c_mutated and
                    pc == 0x040df8 and slot >= pool and
                    slot < pool + count * stride and u8(slot + 6) == 0x0c then
                emit_class1f_action0c("mutation_before", pc, slot, 0xff,
                    0, 0, true)
                local d0 = maincpu.state["D0"].value & 0xffffffff
                maincpu.state["D0"].value = (d0 & 0xffff0000) |
                    ((d0 + 2) & 0xffff)
                class1f_action0c_mutated = true
            end
        end)
end

oracle11_class1f_action0c_write_tap = program:install_write_tap(
    pool, pool + count * stride - 1, "oracle11_class1f_action0c_writes",
    function(offset, data, mask)
        if not capture_class1f_action0c then return end
        local relative = offset - pool
        local slot = pool + math.floor(relative / stride) * stride
        emit_class1f_action0c("actor_write",
            maincpu.state["PC"].value & 0xffffff, slot, relative % stride,
            data & 0xffffffff, mask & 0xffffffff, false)
    end)

local function emit_class1f_inner8_entry(pc)
    if not capture_scene or frame < 2980 or frame > 3300 then return end
    local slot = maincpu.state["A6"].value & 0xffffff
    if slot ~= 0xffa3c0 or u8(slot) == 0 or u8(slot + 2) ~= 0x1f or
            u8(slot + 8) ~= 12 then return end
    class1f_inner8_entries:write(string.format(
        "%d\t%06x\t%06x\t%04x\t%04x\t%d\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%04x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%04x\t%02x\t%04x\t%08x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\n",
        frame, pc, slot, u16(slot + 4), u16(slot + 6), u8(slot + 0x0f),
        u32(slot + 0x10), u32(slot + 0x14), s16(u16(slot + 0x18)),
        u32(slot + 0x1c), u16(slot + 0x0a), s16(u16(slot + 0x24)),
        u16(slot + 0x2a), u8(slot + 0x85), u8(slot + 0xa3),
        u8(slot + 0xa4), u8(slot + 0xa5), u8(slot + 0xa6),
        u8(slot + 0xac), u8(slot + 0xad), u8(slot + 0xae),
        u16(slot + 0xa8), u8(slot + 0xb0), u16(0xff81a8),
        maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        maincpu.state["A0"].value & 0xffffff,
        maincpu.state["A1"].value & 0xffffff,
        maincpu.state["A2"].value & 0xffffff,
        maincpu.state["A3"].value & 0xffffff,
        maincpu.state["A4"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff))
end

oracle11_class1f_inner8_pc_taps = {}
for _, pc in ipairs({
        0x060c9a, 0x061096, 0x0610f6, 0x040bbe, 0x040bea,
        0x040c7c, 0x040cfe, 0x040d0e, 0x040e84, 0x0412a8,
        0x040c9c, 0x041966, 0x0419a4, 0x041b26, 0x041b74,
        0x041b92, 0x041ba2, 0x041c36, 0x041db8, 0x041dfe,
        0x0412bc, 0x041302, 0x041308, 0x041340, 0x040e9c,
        0x0411c4, 0x0411da, 0x0411f0, 0x041236, 0x04127c,
        0x04129e, 0x0413d2}) do
    oracle11_class1f_inner8_pc_taps[
        #oracle11_class1f_inner8_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_class1f_inner8_%06x", pc),
        function() emit_class1f_inner8_entry(pc) end)
end

oracle11_class1f_inner8_write_tap = program:install_write_tap(
    0xffa3c0, 0xffa47f, "oracle11_class1f_inner8_writes",
    function(offset, data, mask)
        if not capture_scene or frame < 2980 or frame > 3300 then return end
        local slot = 0xffa3c0
        local pc = maincpu.state["PC"].value & 0xffffff
        if u8(slot) == 0 or u8(slot + 2) ~= 0x1f or u8(slot + 8) ~= 12 or
                (u16(slot + 4) ~= 0x0208 and
                 (pc < 0x060c9a or pc > 0x0610d4)) then return end
        class1f_inner8_writes:write(string.format(
            "%d\t%06x\t%06x\t%02x\t%04x\t%04x\t%d\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%04x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%04x\t%02x\t%04x\t%08x\t%08x\t%08x\n",
            frame, pc, slot, offset - slot, u16(slot + 4),
            u16(slot + 6), u8(slot + 0x0f), u32(slot + 0x10),
            u32(slot + 0x14), s16(u16(slot + 0x18)), u32(slot + 0x1c),
            u16(slot + 0x0a), s16(u16(slot + 0x24)), u16(slot + 0x2a),
            u8(slot + 0x85), u8(slot + 0xa3), u8(slot + 0xa4),
            u8(slot + 0xa5), u8(slot + 0xa6), u8(slot + 0xac),
            u8(slot + 0xad), u8(slot + 0xae), u16(slot + 0xa8),
            u8(slot + 0xb0), u16(0xff81a8), u32(offset & 0xfffffc),
            data & 0xffffffff, mask & 0xffffffff))
    end)

oracle11_progression_class1f_transition_writes = program:install_write_tap(
    pool, pool + count * stride - 1,
    "oracle11_progression_class1f_transition_writes",
    function(offset, data, mask)
        if not capture_lifecycle or frame < 2070 or frame > capture_last_frame then return end
        local relative = offset - pool
        local slot = pool + math.floor(relative / stride) * stride
        local inner = relative % stride
        if inner > 7 or inner + 3 < 4 then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        local a6 = maincpu.state["A6"].value & 0xffffff
        if u8(slot + 2) ~= 0x1f or u8(slot + 8) ~= 12 then return end
        local suppressed = suppress_transition_pc ~= nil and
            pc == suppress_transition_pc
        class1f_transitions:write(string.format(
            "%d\t%06x\t%02x\t%06x\t%06x\t%d\t%02x\t%d\t%04x\t%04x\t%d\t%d\t%d\t%d\t%d\t%08x\t%04x\t%02x\t%04x\t%04x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%04x\t%02x\t%02x\t%02x\t%02x\t%04x\t%d\t%d\t%04x\t%04x\t%d\t%d\t%d\t%d\t%d\t%08x\t%d\t%d\t%08x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\t%d\n",
            frame, slot, inner, pc, a6, u8(slot), u8(slot + 2),
            u8(slot + 8), u16(slot + 4), u16(slot + 6),
            u8(slot + 0x0f), s16(u16(slot + 0x10)),
            s16(u16(slot + 0x14)), s16(u16(slot + 0x18)),
            s16(u16(slot + 0x40)), u32(slot + 0x1c),
            u16(slot + 0x2a), u8(slot + 0x01), u16(slot + 0x0a),
            u16(slot + 0x24), u8(slot + 0x2b), u8(slot + 0x5c),
            u8(slot + 0x6e), u8(slot + 0x85), u8(slot + 0x96),
            u8(slot + 0xa2), u8(slot + 0xa3), u8(slot + 0xa4),
            u8(slot + 0xa5), u8(slot + 0xa6), u8(slot + 0xac),
            u8(slot + 0xad), u8(slot + 0xae), u16(slot + 0xaa),
            u8(slot + 0xb0), u8(slot + 0x0c), u8(0xff8209),
            u8(0xff9a10), u16(0xff9a1c), u16(0xff1a18),
            u16(0xff1a1a), u16(0xff8384), u16(0xff8386),
            u8(0xff838f), s16(u16(0xff8390)), s16(u16(0xff8394)),
            s16(u16(0xff8398)), s16(u16(0xff83c0)),
            u32(0xff839c), u8(0xff8425), u8(0xff8426),
            maincpu.state["D0"].value & 0xffffffff,
            maincpu.state["D1"].value & 0xffffffff,
            maincpu.state["D2"].value & 0xffffffff,
            maincpu.state["D3"].value & 0xffffffff,
            maincpu.state["A0"].value & 0xffffff,
            maincpu.state["A1"].value & 0xffffff,
            maincpu.state["A2"].value & 0xffffff,
            maincpu.state["A3"].value & 0xffffff,
            maincpu.state["A4"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            data & 0xffffffff, mask & 0xffffffff, suppressed and 1 or 0))
        if suppressed then return u32(offset & 0xfffffc) end
    end)

local function emit_slot(slot)
    snapshots:write(string.format(
        "%d\t%06x\t%d\t%02x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%02x\t%d\t%02x\t%d\t%08x\n",
        frame, slot, u8(slot), u8(slot + 2), u8(slot + 8),
        u16(slot + 4), u16(slot + 6), u8(slot + 0x0f),
        s16(u16(slot + 0x10)), s16(u16(slot + 0x14)),
        s16(u16(slot + 0x18)), u8(slot + 3), u16(slot + 0x2a),
        u8(slot + 0x83), s16(u16(slot + 0x40)), u32(slot + 0x1c)))
end

local function emit_scene_actor(pool_spec, index)
    local slot = pool_spec.base + index * pool_spec.stride
    if u8(slot) == 0 then return end
    local animation_record = u32(slot + 0x1c)
    local health = pool_spec.has_health and
        tostring(s16(u16(slot + 0x40))) or "na"
    local hurt_selector = pool_spec.has_collision_selectors and
        string.format("%02x", animation_record ~= 0 and
            u8(animation_record + 8) or 0) or "na"
    local attack_selector = pool_spec.has_collision_selectors and
        string.format("%02x", animation_record ~= 0 and
            u8(animation_record + 9) or 0) or "na"
    scene_actors:write(string.format(
        "%d\t%s\t%d\t%06x\t%d\t%d\t%02x\t%02x\t%04x\t%04x\t%d\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%04x\t%s\t%s\t%s\n",
        frame, pool_spec.name, index, slot, u8(slot), u8(slot + 8),
        u8(slot + 2), u8(slot + 3), u16(slot + 4), u16(slot + 6),
        u8(slot + 0x0f), u32(slot + 0x10), u32(slot + 0x14),
        s16(u16(slot + 0x18)), animation_record, u16(slot + 0x0a),
        s16(u16(slot + 0x24)), u16(slot + 0x2a),
        health, hurt_selector, attack_selector))
end

local function install_scene_health_tap(first, last, stride_value, pool_name)
    return program:install_write_tap(first, last,
        "oracle11_scene_health_" .. pool_name,
        function(offset, data, mask)
            if not capture_scene or frame < 1972 or
                    frame > capture_last_frame then return end
            local relative = offset - first
            local slot = first + math.floor(relative / stride_value) * stride_value
            local inner = relative % stride_value
            if inner < 0x40 or inner > 0x41 then return end
            local pc = maincpu.state["PC"].value & 0xffffff
            scene_health_writes:write(string.format(
                "%d\t%s\t%06x\t%06x\t%06x\t%06x\t%06x\t%04x\t%04x\t%04x\t%04x\t%08x\t%d\n",
                frame, pool_name, slot, pc,
                maincpu.state["A6"].value & 0xffffff,
                maincpu.state["A1"].value & 0xffffff,
                maincpu.state["A3"].value & 0xffffff,
                u16(slot + 4), u16(slot + 6), u16(slot + 0x40),
                data & 0xffff, mask & 0xffffffff,
                (pc == 0x01d590 or pc == 0x01d5ee) and 1 or 0))
            if pc == 0x01d5ee then emit_type16_collision(pc) end
        end)
end

oracle11_scene_health_taps = {
    install_scene_health_tap(0xff8380, 0xff847f, 0x100, "player"),
    install_scene_health_tap(0xff9580, 0xffa47f, 0xc0, "record12"),
    install_scene_health_tap(0xffae80, 0xffb67f, 0x80, "record20"),
}

local function emit_collision_guard(event, pc, guard_value, mutated)
    if not capture_collision_guard or frame < 1972 or
            frame > capture_last_frame then return end
    local attacker = maincpu.state["A6"].value & 0xffffff
    local defender = maincpu.state["A1"].value & 0xffffff
    local attacker_anim
    local defender_anim
    local latch_index
    local latch_value
    if attacker < 0xff8680 or attacker >= 0xff9280 or
            defender < 0xff9580 or defender >= 0xffa480 then return end
    attacker_anim = u32(attacker + 0x1c)
    defender_anim = u32(defender + 0x1c)
    latch_index = u8(attacker + 0x65)
    latch_value = latch_index < 0x80 and
        u8(defender + 0x68 + latch_index) or 0xff
    collision_guard:write(string.format(
        "%d\t%s\t%06x\t%06x\t%d\t%02x\t%04x\t%04x\t%08x\t%08x\t%d\t%08x\t%02x\t%02x\t%02x\t%06x\t%d\t%02x\t%04x\t%04x\t%08x\t%08x\t%d\t%08x\t%02x\t%02x\t%02x\t%02x\t%d\t%d\n",
        frame, event, pc, attacker, u8(attacker), u8(attacker + 2),
        u16(attacker + 4), u16(attacker + 6), u32(attacker + 0x10),
        u32(attacker + 0x14), s16(u16(attacker + 0x18)), attacker_anim,
        attacker_anim ~= 0 and u8(attacker_anim + 9) or 0,
        latch_index, u8(attacker + 0x67), defender, u8(defender),
        u8(defender + 2), u16(defender + 4), u16(defender + 6),
        u32(defender + 0x10), u32(defender + 0x14),
        s16(u16(defender + 0x18)), defender_anim,
        defender_anim ~= 0 and u8(defender_anim + 8) or 0, guard_value,
        latch_value, u8(defender + 0x70),
        s16(u16(defender + 0x40)), mutated and 1 or 0))
end

oracle11_collision_guard_read = program:install_read_tap(
    0xffa1ec, 0xffa1ef, "oracle11_collision_guard_read",
    function(offset, data, mask)
        local pc = maincpu.state["PC"].value & 0xffffff
        if pc ~= 0x01cbfc or offset ~= 0xffa1ed then return data end
        emit_collision_guard("guard_read", pc, data & 0xff, false)
        return data
    end)

oracle11_collision_guard_pass = opcodes:install_read_tap(
    0x01cc06, 0x01cc07, "oracle11_collision_guard_pass",
    function()
        emit_collision_guard("guard_pass", 0x01cc06,
            u8((maincpu.state["A1"].value & 0xffffff) + 0x6d), false)
    end)

oracle11_collision_routine_entry = opcodes:install_read_tap(
    0x01d116, 0x01d117, "oracle11_collision_routine_entry",
    function()
        emit_collision_guard("collision_entry", 0x01d116,
            u8((maincpu.state["A1"].value & 0xffffff) + 0x6d), false)
    end)

oracle11_collision_overlap_entry = opcodes:install_read_tap(
    0x01d17e, 0x01d17f, "oracle11_collision_overlap_entry",
    function()
        emit_collision_guard("overlap_entry", 0x01d17e,
            u8((maincpu.state["A1"].value & 0xffffff) + 0x6d), false)
    end)

oracle11_collision_guard_contact = opcodes:install_read_tap(
    0x01cc0e, 0x01cc0f, "oracle11_collision_guard_contact",
    function()
        emit_collision_guard("collision_true", 0x01cc0e,
            u8((maincpu.state["A1"].value & 0xffffff) + 0x6d), false)
    end)

oracle11_collision_guard_writes = program:install_write_tap(
    0xff9580, 0xffa47f, "oracle11_collision_guard_writes",
    function(offset, data, mask)
        if not capture_collision_guard or frame < 1972 or
                frame > capture_last_frame then return end
        local relative = offset - 0xff9580
        local slot = 0xff9580 + math.floor(relative / 0xc0) * 0xc0
        local inner = relative % 0xc0
        if inner > 0x6d or inner + 3 < 0x6d then return end
        collision_guard_writes:write(string.format(
            "%d\t%06x\t%06x\t%02x\t%04x\t%04x\t%02x\t%08x\t%08x\n",
            frame, maincpu.state["PC"].value & 0xffffff, slot, inner,
            u16(slot + 4), u16(slot + 6), u8(slot + 0x6d),
            data & 0xffffffff, mask & 0xffffffff))
    end)

local function collision_slot_list(count_address, list_end)
    local values = {}
    local count_value = u8(count_address)
    local index
    for index = 1, count_value do
        values[#values + 1] = string.format("ff%04x",
            u16(list_end - index * 2))
    end
    return count_value, table.concat(values, ",")
end

oracle11_collision_list_entry = opcodes:install_read_tap(
    0x01cbcc, 0x01cbcd, "oracle11_collision_list_entry",
    function()
        if not capture_collision_guard or frame < 1972 or
                frame > capture_last_frame then return end
        local attacker_count, attacker_slots =
            collision_slot_list(0xffee7d, 0xfff072)
        local defender_count, defender_slots =
            collision_slot_list(0xffee81, 0xfff0a2)
        collision_lists:write(string.format(
            "%d\t01cbcc\t%d\t%s\t%d\t%s\n", frame,
            attacker_count, attacker_slots, defender_count, defender_slots))
    end)

oracle11_collision_list_writes = program:install_write_tap(
    0xffee7c, 0xfff0a3, "oracle11_collision_list_writes",
    function(offset, data, mask)
        if not capture_collision_guard or frame < 2280 or frame > 2310 then
            return
        end
        if (offset > 0xffee83 and offset < 0xfff040) or
                offset > 0xfff0a3 then return end
        local sr = maincpu.state["SR"].value & 0xffff
        local sp = (sr & 0x2000) ~= 0 and
            (maincpu.state["SP"].value & 0xffffff) or
            (maincpu.state["USP"].value & 0xffffff)
        local a6 = maincpu.state["A6"].value & 0xffffff
        local pc = maincpu.state["PC"].value & 0xffffff
        local suppressed = mutate_collision_guard and a6 == 0xffa180 and
            pc == 0x01686c
        collision_list_writes:write(string.format(
            "%d\t%06x\t%06x\t%06x\t%d\t%02x\t%02x\t%02x\t%08x\t%06x\t%06x\t%06x\t%08x\t%08x\t%d\n", frame,
            pc, offset,
            a6, u8(a6), u8(a6 + 1), u8(a6 + 0x47), u8(a6 + 0x48),
            u32(a6 + 0x1c), u32(sp) & 0xffffff,
            u32(sp + 4) & 0xffffff, u32(sp + 8) & 0xffffff,
            data & 0xffffffff, mask & 0xffffffff,
            suppressed and 1 or 0))
        if suppressed then return 0x0000a240 end
    end)

oracle11_collision_actor_flags = program:install_write_tap(
    0xffa180, 0xffa23f, "oracle11_collision_actor_flags",
    function(offset, data, mask)
        if not capture_collision_guard or frame < 2280 or frame > 2310 then
            return
        end
        local inner = offset - 0xffa180
        local pc = maincpu.state["PC"].value & 0xffffff
        local field01_write = inner <= 1 and inner + 3 >= 1
        if not field01_write and
                not (inner <= 0x70 and inner + 3 >= 0x68) then return end
        local suppressed = false
        collision_actor_flags:write(string.format(
            "%d\t%06x\tffa180\t%02x\t%d\t%02x\t%04x\t%04x\t%08x\t%08x\t%d\t%d\t%d\t%08x\t%08x\t%d\n",
            frame, pc, inner, u8(0xffa180), u8(0xffa181),
            u16(0xffa184), u16(0xffa186), u32(0xffa190),
            u32(0xffa194), s16(u16(0xffa198)),
            s16(u16(global + 0x278)), s16(u16(global + 0x27c)),
            data & 0xffffffff, mask & 0xffffffff,
            suppressed and 1 or 0))
        if suppressed then return u32(offset & 0xfffffc) end
    end)

oracle11_collision_identity_writes = program:install_write_tap(
    0xff8680, 0xff927f, "oracle11_collision_identity_writes",
    function(offset, data, mask)
        if not capture_collision_guard or frame < 1972 or
                frame > capture_last_frame then return end
        local relative = offset - 0xff8680
        local slot = 0xff8680 + math.floor(relative / 0x80) * 0x80
        local inner = relative % 0x80
        if not ((inner <= 0x65 and inner + 3 >= 0x65) or
                (inner <= 0x67 and inner + 3 >= 0x67)) then return end
        collision_identity_writes:write(string.format(
            "%d\t%06x\t%06x\t%02x\t%d\t%02x\t%04x\t%04x\t%02x\t%02x\t%08x\t%08x\n",
            frame, maincpu.state["PC"].value & 0xffffff, slot, inner,
            u8(slot), u8(slot + 2), u16(slot + 4), u16(slot + 6),
            u8(slot + 0x65), u8(slot + 0x67),
            data & 0xffffffff, mask & 0xffffffff))
    end)

local function emit_collision_identity_assignment(event, pc)
    if not capture_collision_guard or frame < 1972 or
            frame > capture_last_frame then return end
    local actor = maincpu.state["A6"].value & 0xffffff
    collision_identity_assignments:write(string.format(
        "%d\t%s\t%06x\t%06x\t%d\t%02x\t%02x\t%04x\t%04x\t%02x\t%02x\n",
        frame, event, pc, actor, u8(actor), u8(actor + 2),
        u8(actor + 8), u16(actor + 4), u16(actor + 6),
        u8(actor + 0x67), u8(global + 0x20b)))
end

oracle11_collision_identity_assignment_entry = opcodes:install_read_tap(
    0x01d768, 0x01d769, "oracle11_collision_identity_assignment_entry",
    function()
        emit_collision_identity_assignment("entry", 0x01d768)
    end)

oracle11_collision_identity_assignment_exit = opcodes:install_read_tap(
    0x01d778, 0x01d779, "oracle11_collision_identity_assignment_exit",
    function()
        emit_collision_identity_assignment("exit", 0x01d778)
    end)

local function emit_class1f_hit(pc)
    if not capture_class1f_hit or frame < class1f_hit_first_frame or
            frame > class1f_hit_last_frame then return end
    local slot = maincpu.state["A6"].value & 0xffffff
    if slot ~= class1f_hit_slot or u8(slot) == 0 or u8(slot + 2) ~= 0x1f or
            u8(slot + 8) ~= 12 then return end
    class1f_hit:write(string.format(
        "%d\t%06x\t%06x\t%04x\t%04x\t%d\t%08x\t%04x\t%d\t%04x\t%02x\t%d\t%d\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%08x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\n",
        frame, pc, slot, u16(slot + 4), u16(slot + 6), u8(slot + 0x0f),
        u32(slot + 0x1c), u16(slot + 0x0a), s16(u16(slot + 0x24)),
        u16(slot + 0x2a), u8(slot + 0x2c), s16(u16(slot + 0x40)),
        s16(u16(slot + 0x42)), u8(slot + 0x46), u8(slot + 0x49),
        u8(slot + 0x4d), u8(slot + 0x4e), u8(slot + 0x4f),
        u8(slot + 0x5c), u8(slot + 0x65), u8(slot + 0x6c),
        u8(slot + 0x6d), u8(slot + 0x73),
        maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        maincpu.state["A0"].value & 0xffffff,
        maincpu.state["A1"].value & 0xffffff,
        maincpu.state["A2"].value & 0xffffff,
        maincpu.state["A3"].value & 0xffffff,
        maincpu.state["A4"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff))
    class1f_hit_program:write(string.format(
        "%d\t%06x\t%04x\t%04x\t%d\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%02x\t%02x\t%d\t%d\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%08x\t%08x\t%08x\t%08x\t%04x\t%08x\t%08x\t%08x\t%08x\n",
        frame, pc, u16(slot + 4), u16(slot + 6), u8(slot + 0x0f),
        u32(slot + 0x10), u32(slot + 0x14), s16(u16(slot + 0x18)),
        u32(slot + 0x1c), u16(slot + 0x0a), s16(u16(slot + 0x24)),
        u8(slot + 0x2a), u8(slot + 0x2c),
        s16(u16(slot + 0x40)), s16(u16(slot + 0x42)),
        u8(slot + 0x46), u8(slot + 0x49), u8(slot + 0x4d),
        u8(slot + 0x4f), u8(slot + 0x5c), u8(slot + 0x6c),
        u8(slot + 0x6d), u8(slot + 0x73), u32(slot + 0x30),
        u32(slot + 0x34), u32(slot + 0x38), u32(slot + 0x3c),
        u16(0xff81a8), maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff))
end

oracle11_class1f_hit_pc_taps = {}
for _, pc in ipairs({
        0x060532, 0x06075a, 0x06105a, 0x01e868, 0x01e878,
        0x01e888, 0x01e8cc, 0x01e8dc, 0x01e8e0, 0x01e8e6,
        0x01e8fe, 0x01e904, 0x01e90c, 0x01e920, 0x01e92c,
        0x01e970, 0x01e974, 0x01e9ce, 0x01ea4c, 0x01ea54,
        0x01ea6c, 0x01eae4, 0x01ee7c, 0x01ef80, 0x01f0ca,
        0x01eb00, 0x01eb4c, 0x01ebc0, 0x01ec10, 0x01ec16,
        0x01ec5c, 0x01ec86, 0x01ec96, 0x01ecb4, 0x01ecba,
        0x01ece8, 0x01edbc,
        0x01edc8, 0x01edfc, 0x01ee16, 0x01ee24, 0x01ee6a,
        0x01efec, 0x01f6c6, 0x01f70a, 0x01f71c, 0x016518,
        0x016536, 0x01f23e, 0x01f250, 0x01f316, 0x01f340,
        0x01f366, 0x01f37c, 0x01f3c0, 0x01f3ee, 0x01f41e,
        0x01f46e, 0x01f474, 0x01f4b2, 0x01f4f0, 0x01f508}) do
    oracle11_class1f_hit_pc_taps[#oracle11_class1f_hit_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_class1f_hit_%06x", pc),
        function() emit_class1f_hit(pc) end)
end

oracle11_class1f_hit_write_tap = program:install_write_tap(
    class1f_hit_slot, class1f_hit_slot + 0xbf,
    "oracle11_class1f_hit_writes",
    function(offset, data, mask)
        if not capture_class1f_hit or frame < class1f_hit_first_frame or
                frame > class1f_hit_last_frame then return end
        local slot = class1f_hit_slot
        if u8(slot) == 0 or u8(slot + 2) ~= 0x1f or u8(slot + 8) ~= 12 then
            return
        end
        local pc = maincpu.state["PC"].value & 0xffffff
        local inner = offset - slot
        class1f_hit_writes:write(string.format(
            "%d\t%06x\t%06x\t%02x\t%04x\t%04x\t%08x\t%04x\t%02x\t%d\t%d\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%08x\t%08x\t%08x\t%d\n",
            frame, pc, slot, inner, u16(slot + 4), u16(slot + 6),
            u32(slot + 0x1c), u16(slot + 0x2a), u8(slot + 0x2c),
            s16(u16(slot + 0x40)), s16(u16(slot + 0x42)),
            u8(slot + 0x46), u8(slot + 0x49), u8(slot + 0x4d),
            u8(slot + 0x4f), u8(slot + 0x5c), u8(slot + 0x6c),
            u8(slot + 0x6d), u8(slot + 0x73), u32(offset & 0xfffffc),
            data & 0xffffffff, mask & 0xffffffff, 0))
    end)

oracle11_class1f_hit_selector_table_tap = program:install_read_tap(
    class1f_hit_selector_entry, class1f_hit_selector_entry + 1,
    "oracle11_class1f_hit_selector_table",
    function(offset, data, mask)
        if not capture_class1f_hit or not mutate_class1f_hit_selector or
                frame < class1f_hit_first_frame or
                frame > class1f_hit_last_frame or
                (maincpu.state["A6"].value & 0xffffff) ~= class1f_hit_slot then
            return data
        end
        class1f_hit_selector_mutations = class1f_hit_selector_mutations + 1
        return data & 0x00ff
    end)

local function emit_player_hit(event, pc)
    if not capture_player_hit or frame < 2700 or frame > 4050 then return end
    player_hit_program:write(string.format(
        "%d\t%s\t%06x\t%04x\t%04x\t%02x\t%d\t%08x\t%08x\t%d\t%d\t%08x\t%04x\t%d\t%04x\t%02x\t%d\t%d\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%08x\t%08x\t%08x\t%08x\t%04x\t%08x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\n",
        frame, event, pc, u16(player + 4), u16(player + 6),
        u8(player + 7), u8(player + 0x0f), u32(player + 0x10),
        u32(player + 0x14), s16(u16(player + 0x14)),
        s16(u16(player + 0x18)), u32(player + 0x1c),
        u16(player + 0x0a), s16(u16(player + 0x24)),
        u16(player + 0x2a), u8(player + 0x2c),
        s16(u16(player + 0x40)), s16(u16(player + 0x42)),
        u8(player + 0x46), u8(player + 0x49), u8(player + 0x4d),
        u8(player + 0x4f), u8(player + 0x5c), u8(player + 0x6c),
        u8(player + 0x73), u32(player + 0x30), u32(player + 0x34),
        u32(player + 0x38), u32(player + 0x3c), u16(player + 0x74),
        maincpu.state["D0"].value & 0xffffffff,
        maincpu.state["D1"].value & 0xffffffff,
        maincpu.state["D2"].value & 0xffffffff,
        maincpu.state["D3"].value & 0xffffffff,
        maincpu.state["A0"].value & 0xffffff,
        maincpu.state["A1"].value & 0xffffff,
        maincpu.state["A2"].value & 0xffffff,
        maincpu.state["A3"].value & 0xffffff,
        maincpu.state["A4"].value & 0xffffff,
        maincpu.state["A5"].value & 0xffffff))
end

oracle11_player_hit_pc_taps = {}
for _, pc in ipairs({
        0x01d454, 0x01aa00, 0x01aa10, 0x01a96e, 0x01a982,
        0x01aad0, 0x01ab1a, 0x01ab2c, 0x01ab52, 0x01abb8,
        0x01ac48, 0x01ac62, 0x01acdc, 0x01ad14, 0x01ad74,
        0x01adb0, 0x01ade8, 0x01ae24, 0x01ae78, 0x01ae9a}) do
    oracle11_player_hit_pc_taps[#oracle11_player_hit_pc_taps + 1] =
        opcodes:install_read_tap(pc, pc + 1,
        string.format("oracle11_player_hit_%06x", pc),
        function() emit_player_hit("dispatch", pc) end)
end

oracle11_player_hit_write_tap = program:install_write_tap(
    player, player + 0xff, "oracle11_player_hit_writes",
    function(offset, data, mask)
        if not capture_player_hit or frame < 2700 or frame > 4050 then
            return
        end
        local pc = maincpu.state["PC"].value & 0xffffff
        local inner = offset - player
        local mutated = mutate_player_hit_body and pc == 0x01d46c and
            u8(player + 0x49) == 9
        player_hit_writes:write(string.format(
            "%d\t%06x\t%02x\t%04x\t%04x\t%02x\t%08x\t%04x\t%02x\t%d\t%d\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%02x\t%08x\t%08x\t%08x\t%d\n",
            frame, pc, inner, u16(player + 4), u16(player + 6),
            u8(player + 7), u32(player + 0x1c), u16(player + 0x2a),
            u8(player + 0x2c), s16(u16(player + 0x40)),
            s16(u16(player + 0x42)), u8(player + 0x46),
            u8(player + 0x49), u8(player + 0x4d), u8(player + 0x4f),
            u8(player + 0x5c), u8(player + 0x6c), u8(player + 0x73),
            u32(offset & 0xfffffc), data & 0xffffffff,
            mask & 0xffffffff, mutated and 1 or 0))
        if mutated then
            player_hit_body_mutations = player_hit_body_mutations + 1
            return 0x00000202
        end
    end)

oracle11_progression_frame = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    class00_phase_ordinal = 0
    emit_class00_scheduler_phase("frame_notifier", 0)
    suppress_selected_scene_pair()
    if capture_scene and class0f_state_counterfactual and
            class0f_state_counterfactual_count < 2 and
            u8(0xffb100) ~= 0 and u8(0xffb102) == 0x0f and
            u8(0xffb108) == 20 then
        program:write_u16(0xffb104, 0x0400)
        class0f_state_counterfactual_count =
            class0f_state_counterfactual_count + 1
    end
    if capture_terrain_patch and frame >= 1972 and
            frame <= capture_last_frame then
        emit_terrain_patch("sample", 0, 0, 0, false)
    end
    if frame >= 1972 and frame <= capture_last_frame then
        controller_samples:write(string.format(
            "%d\t%d\t%02x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%02x\t%02x\t%02x\t%02x\t%d\t%d\t%d\t%d\n",
            frame, u8(controller), u8(controller + 2), u8(controller + 8),
            u16(controller + 4), u16(controller + 6), u16(controller + 0x10),
            u16(controller + 0x40), u16(controller + 0x42),
            u16(controller + 0x44), u16(controller + 0x46),
            u16(controller + 0x48), u16(controller + 0x4a),
            u8(controller + 0x2c), u8(controller + 0x2e),
            u8(0xff1a11), u8(global + 0x19), u16(0xff1a18), u16(0xff1a1a),
            s16(u16(global + 0x278)), s16(u16(global + 0x27c))))
    end
    if (frame >= 2505 and frame <= 2515) or
        (frame >= 3978 and frame <= 3988) then
        emit_slot(0xffa3c0)
        emit_slot(0xffa000)
    end
    if capture_lifecycle and frame >= 2300 and frame <= 2610 then
        for slot = 0xff9d00, 0xffa3c0, stride do emit_slot(slot) end
    end
    if capture_scene and frame >= 1972 and frame <= capture_last_frame then
        if capture_player_hit and frame >= 2700 and frame <= 4050 then
            emit_player_hit("sample", 0)
        end
        player_resource:write(string.format(
            "%d\tsample\t000000\t%d\t%d\t%d\t%d\t%04x\t%04x\t00000000\t00000000\t0\n",
            frame, u8(player + 0x8c), u8(player + 0x8d),
            u8(player + 0x8b), u8(player + 0x8a),
            u16(player + 4), u16(player + 6)))
        scene_frames:write(string.format(
            "%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%08x\t%08x\t%d\t%d\t%d\t%d\t%d\t%04x\n",
            frame, u16(global + 8), u16(controller + 4),
            u16(controller + 6), u16(controller + 0x40),
            u16(controller + 0x42), u16(0xff1a18), u16(0xff1a1a),
            u8(0xff8380), u16(0xff8384), u16(0xff8386),
            u8(0xff838f), u32(0xff8390), u32(0xff8394),
            s16(u16(0xff8398)), s16(u16(0xff83c0)),
            s16(u16(global + 0x278)), s16(u16(global + 0x27c)),
            s16(u16(global + 0x32)), u16(0xff81a8)))
        if u8(0xff8380) ~= 0 then
            local player_animation = u32(0xff839c)
            scene_actors:write(string.format(
                "%d\tplayer\t0\tff8380\t%d\t0\t%02x\t00\t%04x\t%04x\t%d\t%08x\t%08x\t%d\t%08x\t%04x\t%d\t%04x\t%d\t%02x\t%02x\n",
                frame, u8(0xff8380), u8(0xff8382), u16(0xff8384),
                u16(0xff8386), u8(0xff838f), u32(0xff8390),
                u32(0xff8394), s16(u16(0xff8398)), player_animation,
                u16(0xff838a), s16(u16(0xff83a4)), u16(0xff83aa),
                s16(u16(0xff83c0)), player_animation ~= 0 and
                    u8(player_animation + 8) or 0,
                player_animation ~= 0 and u8(player_animation + 9) or 0))
        end
        for _, pool_spec in ipairs(scene_pools) do
            for index = 0, pool_spec.count - 1 do
                emit_scene_actor(pool_spec, index)
            end
        end
    end
    if frame == capture_last_frame then
        result:write(table.concat({suppress_spawn and 1 or 0,
            suppress_guard and 1 or 0, main_spawns,
            aux_spawns, suppressed_writes, lifecycle_suppressed_writes,
            action4_timer_events, action4_timer_suppressed_writes,
            type4_class03_suppressed_writes,
            coffee_stage_rng_suppressed_writes,
            type36_suppressed_writes,
            scene_pair_suppressed_actors,
            obstacle_transition_suppressed_writes,
            class1f_hit_selector_mutations,
            player_hit_body_mutations,
            class0a_variant_counterfactual_count,
            class00_init_counterfactual_count,
            u8(global + 9)}, "\t") .. "\n")
        transactions:close(); snapshots:close(); writes:close(); global_writes:close()
        controller_samples:close(); lifecycle_writes:close()
        class1f_transitions:close(); action4_timers:close()
        action4_guard:close()
        scene_actors:close(); scene_frames:close()
        scene_health_writes:close(); type4_class03:close()
        scene_rng_calls:close(); stage_setup:close(); stage_setup_writes:close()
        class1f_bounds:close(); type36_writes:close()
        pair_suppression:close(); obstacle_trace:close(); obstacle_writes:close()
        component20_writes:close(); component20_dispatch:close()
        component20_collision:close()
        component20_global:close()
        component20_phase:close()
        scheduler_phase:close()
        component20_callers:close()
        terrain_patch:close()
        terrain_stream:close()
        player_dispatch:close()
        player_animation_writes:close()
        obstacle_guard:close()
        type16_collision:close()
        class1f_inner8_entries:close()
        class1f_inner8_writes:close()
        class1f_inner8_group:close()
        class1f_action0c:close()
        collision_guard:close()
        collision_guard_writes:close()
        collision_lists:close()
        collision_list_writes:close()
        collision_actor_flags:close()
        collision_identity_writes:close()
        collision_identity_assignments:close()
        class1f_hit:close()
        class1f_hit_writes:close()
        class1f_hit_program:close()
        player_resource:close()
        controller_substate_writes:close()
        player_hit_program:close()
        player_hit_writes:close()
        class0a_program:close()
        class00_program:close()
        class00_scheduler_phase:close()
        result:close()
    end
end)

dofile("tools/mame_capture_oracle11_player_audio.lua")
