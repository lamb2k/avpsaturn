#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("enemy_tools", ROOT / "tests/port_v2/enemy_bench/collect_readback.py")
tools = importlib.util.module_from_spec(spec); spec.loader.exec_module(tools)
FIELDS = ("frame","input_mask","player_x","player_lane","player_health","player_state",
          "player_selector","player_attack_active","player_facing",
          "player_animation_record","player_assembly","player_screen_y",
          "alien_x","alien_lane","alien_health","alien_state","alien_inner",
          "alien_action","alien_facing","alien_animation_record","alien_assembly",
          "alien_screen_y","alien_rng","player_contact","alien_contact","player_damage",
          "alien_damage","attack_miss","encounter_state","route_unlocked",
          "continued_after_unlock","camera_world_x","failures")
FIELDS = FIELDS + ("round1_player_x","round1_player_z","round1_player_facing",
                   "round1_player_source_action","round1_player_controller_updates")
FIELDS = FIELDS + ("round1_scheduler_frames","round1_scheduler_dispatches",
                   "round1_scheduler_trace_count","round1_scheduler_order_hash")
FIELDS = FIELDS + ("round1_actor_handler_dispatches",
                   "round1_presentation_bindings",
                   "round1_state_context_bindings")
EVIDENCE_LAST_FRAME = 470
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def signed(mcp, address): return tools.signed32(mcp.u32(address))
def read_samples(mcp, base, count):
    record_bytes = len(FIELDS) * 4
    max_records = 65536 // record_bytes
    payload = bytearray()
    for first in range(0, count, max_records):
        records = min(max_records, count - first)
        payload.extend(mcp.read(base + first * record_bytes,
                                records * record_bytes))
    result = []
    for index in range(count):
        start = index * record_bytes
        record = payload[start:start + record_bytes]
        result.append({
            name: tools.signed32(int.from_bytes(record[offset * 4:offset * 4 + 4], "big"))
            for offset, name in enumerate(FIELDS)
        })
    return result

parser = argparse.ArgumentParser()
parser.add_argument("--run", type=int, choices=(1,2), required=True)
parser.add_argument("--emulator-pid", type=int, required=True)
parser.add_argument("--timeout", type=float, default=180.0)
args = parser.parse_args()
inventory = json.loads((HERE / "inventory.json").read_text())
build = json.loads((ROOT / inventory["build_root"] / f"run-{args.run}/build.json").read_text())
syms = tools.symbols(inventory["required_readback_symbols"])
mcp = tools.Mcp("http://127.0.0.1:9640/mcp"); deadline=time.time()+args.timeout
while True:
    try: mcp.initialize(); break
    except Exception:
        if time.time() >= deadline: raise
        time.sleep(0.25)
run_root = ROOT / inventory["build_root"] / f"run-{args.run}"
while time.time() < deadline:
    try:
        ready = mcp.u32(syms["avsp_diag_runtime_ready"])
        frame = mcp.u32(syms["avsp_diag_live_frame"])
        if (ready == 1 and frame >= EVIDENCE_LAST_FRAME and
            mcp.u32(syms["avsp_diag_live_continued_after_unlock"]) == 1 and
            signed(mcp, syms["avsp_diag_live_camera_world_x"]) > 768):
            break
    except Exception:
        # The pinned Windows build occasionally resets one HTTP connection
        # while the emulator remains alive. Reinitialize the bridge and keep
        # the bounded deadline authoritative.
        time.sleep(0.25)
        try: mcp.initialize()
        except Exception: pass
    time.sleep(0.05)
else:
    failed_asset_pointer = mcp.u32(syms["failed_asset"])
    failed_asset_name = ""
    if failed_asset_pointer != 0:
        failed_asset_name = mcp.read(failed_asset_pointer, 64).split(b"\0", 1)[0].decode(
            "ascii", errors="replace"
        )
    timeout_state = {
        "runtime_ready": mcp.u32(syms["avsp_diag_runtime_ready"]),
        "contract_flags": mcp.u32(syms["avsp_diag_live_contract_flags"]),
        "frame_stage": signed(mcp, syms["avsp_diag_live_frame_stage"]),
        "internal_failures": mcp.u32(syms["avsp_diag_live_internal_failures"]),
        "pcm_retriggers": mcp.u32(syms["avsp_diag_live_pcm_retriggers"]),
        "runtime_ready_internal": mcp.u32(syms["runtime_ready"]),
        "slice_init_stage": signed(mcp, syms["avsp_diag_slice_init_stage"]),
        "slice_ready": mcp.u32(syms["avsp_diag_slice_ready"]),
        "frame": mcp.u32(syms["avsp_diag_live_frame"]),
        "sample_count": mcp.u32(syms["avsp_diag_live_sample_count"]),
        "encounter_state": mcp.u32(syms["avsp_diag_live_encounter_state"]),
        "player_x": signed(mcp, syms["avsp_diag_live_player_x"]),
        "player_health": signed(mcp, syms["avsp_diag_live_player_health"]),
        "alien_x": signed(mcp, syms["avsp_diag_live_alien_x"]),
        "alien_health": signed(mcp, syms["avsp_diag_live_alien_health"]),
        "alien_state": mcp.u32(syms["avsp_diag_live_alien_state"]),
        "hit_events": mcp.u32(syms["avsp_diag_live_hit_events"]),
        "ko_events": mcp.u32(syms["avsp_diag_live_ko_events"]),
        "failures": mcp.u32(syms["avsp_diag_live_failures"]),
        "fallback_count": mcp.u32(syms["avsp_diag_live_fallback_count"]),
        "failed_asset_pointer": hex(failed_asset_pointer),
        "failed_asset_name": failed_asset_name,
    }
    timeout_state["debug_status"] = mcp.call("debug_status")
    raise TimeoutError(
        "INTEGRATE-04A diagnostic did not clear and continue: "
        f"{timeout_state}"
    )
mcp.call("set_debug_option", cpu_core="interpreter")
mcp.call("pause")
count = signed(mcp,syms["avsp_diag_live_sample_count"])
if count < 1 or count > 600:
    raise RuntimeError(f"invalid live sample count: {count}")
all_samples = read_samples(mcp, syms["avsp_diag_live_samples"], count)
mapping = {"runtime_ready":"avsp_diag_runtime_ready", "interface_version":"avsp_diag_live_interface_version",
           "contract_flags":"avsp_diag_live_contract_flags", "frame_stage":"avsp_diag_live_frame_stage",
           "frame":"avsp_diag_live_frame", "hit_events":"avsp_diag_live_hit_events",
           "ko_events":"avsp_diag_live_ko_events", "route_unlocked":"avsp_diag_live_route_unlocked",
           "continued":"avsp_diag_live_continued_after_unlock", "failures":"avsp_diag_live_failures",
           "fallback_count":"avsp_diag_live_fallback_count", "canaries_ok":"avsp_diag_live_canaries_ok",
           "internal_failures":"avsp_diag_live_internal_failures",
           "pcm_retriggers":"avsp_diag_live_pcm_retriggers",
           "physical_saturn":"avsp_diag_live_physical_saturn",
           "player_health":"avsp_diag_live_player_health",
           "player_state":"avsp_diag_live_player_state",
           "player_facing":"avsp_diag_live_player_facing",
           "player_animation_record":"avsp_diag_live_player_animation_record",
           "player_assembly":"avsp_diag_live_player_assembly",
           "player_screen_y":"avsp_diag_live_player_screen_y",
           "alien_health":"avsp_diag_live_alien_health",
           "alien_state":"avsp_diag_live_alien_state",
           "alien_action":"avsp_diag_live_alien_action",
           "alien_facing":"avsp_diag_live_alien_facing",
           "alien_animation_record":"avsp_diag_live_alien_animation_record",
           "alien_assembly":"avsp_diag_live_alien_assembly",
           "alien_screen_y":"avsp_diag_live_alien_screen_y",
           "round1_spec_bound":"avsp_diag_round1_spec_bound",
           "round1_entry_valid":"avsp_diag_round1_entry_valid",
           "round1_route_state":"avsp_diag_round1_route_state",
           "round1_rng_seed":"avsp_diag_round1_rng_seed",
           "round1_player_health":"avsp_diag_round1_player_health",
           "round1_pool12_free":"avsp_diag_round1_pool12_free",
           "round1_pool16_free":"avsp_diag_round1_pool16_free",
           "round1_pool20_free":"avsp_diag_round1_pool20_free",
           "round1_pool24_free":"avsp_diag_round1_pool24_free",
           "round1_fallback_count":"avsp_diag_round1_fallback_count",
           "round1_canaries_ok":"avsp_diag_round1_canaries_ok",
           "round1_presentation_ready":"avsp_diag_round1_presentation_ready",
           "round1_presentation_seen":"avsp_diag_round1_presentation_seen",
           "round1_presentation_commands_peak":"avsp_diag_round1_presentation_commands_peak",
           "round1_entry_spawn_count":"avsp_diag_round1_entry_spawn_count",
           "round1_entry_step":"avsp_diag_round1_entry_step",
           "round1_entry_timer_decrements":"avsp_diag_round1_entry_timer_decrements",
           "round1_entry_gate8236":"avsp_diag_round1_entry_gate8236",
           "round1_entry_gate81af":"avsp_diag_round1_entry_gate81af",
           "round1_control_enabled":"avsp_diag_round1_control_enabled",
           "round1_failure_count":"avsp_diag_round1_failure_count",
           "round1_player_x":"avsp_diag_round1_player_x",
           "round1_player_z":"avsp_diag_round1_player_z",
           "round1_player_facing":"avsp_diag_round1_player_facing",
           "round1_player_source_action":"avsp_diag_round1_player_source_action",
           "round1_player_controller_updates":"avsp_diag_round1_player_controller_updates",
           "round1_scheduler_frames":"avsp_diag_round1_scheduler_frames",
           "round1_scheduler_dispatches":"avsp_diag_round1_scheduler_dispatches",
           "round1_scheduler_trace_count":"avsp_diag_round1_scheduler_trace_count",
           "round1_scheduler_order_hash":"avsp_diag_round1_scheduler_order_hash",
           "round1_actor_handler_dispatches":"avsp_diag_round1_actor_handler_dispatches",
           "round1_presentation_bindings":"avsp_diag_round1_presentation_bindings",
           "round1_state_context_bindings":"avsp_diag_round1_state_context_bindings"}
state = {key:signed(mcp,syms[symbol]) for key,symbol in mapping.items()}
observed_frame = state["frame"]
current_sample = next((sample for sample in all_samples
                       if sample["frame"] == observed_frame), None)
if current_sample is None:
    raise RuntimeError("same-tick diagnostic sample is unavailable")
evidence_sample = next((sample for sample in all_samples
                        if sample["frame"] == EVIDENCE_LAST_FRAME), None)
if evidence_sample is None:
    raise RuntimeError("fixed evidence-frame diagnostic sample is unavailable")
for key in ("round1_player_x", "round1_player_z", "round1_player_facing",
            "round1_player_source_action", "round1_player_controller_updates",
            "round1_scheduler_frames", "round1_scheduler_dispatches",
            "round1_scheduler_trace_count", "round1_scheduler_order_hash",
            "round1_actor_handler_dispatches", "round1_presentation_bindings",
            "round1_state_context_bindings"):
    state[key] = evidence_sample[key]
state["frame"] = EVIDENCE_LAST_FRAME
samples = [sample for sample in all_samples
           if sample["frame"] <= EVIDENCE_LAST_FRAME]
if not (state["runtime_ready"] == state["canaries_ok"] == 1 and
        state["interface_version"] == 2 and state["contract_flags"] == 127 and
        state["frame_stage"] == 7 and
        state["internal_failures"] == 0 and state["pcm_retriggers"] >= 1 and
        state["hit_events"] >= 1 and state["ko_events"] == 1 and state["route_unlocked"] ==
        state["continued"] == 1 and state["failures"] == state["fallback_count"] ==
        state["physical_saturn"] == 0): raise RuntimeError(f"live state failed: {state}")
if not (state["round1_spec_bound"] == state["round1_entry_valid"] ==
        state["round1_canaries_ok"] == 1 and
        state["round1_route_state"] == 4 and state["round1_rng_seed"] == 0x8DEF and
        state["round1_player_health"] == 101 and
        [state[f"round1_pool{kind}_free"] for kind in (12,16,20,24)] ==
        [10,20,16,32] and state["round1_fallback_count"] == 0 and
        state["round1_failure_count"] == 0 and
        state["round1_entry_spawn_count"] == 10 and
        state["round1_entry_step"] == 8 and
        state["round1_entry_timer_decrements"] == 164 and
        state["round1_entry_gate8236"] == 0 and
        state["round1_entry_gate81af"] == 1 and
        state["round1_control_enabled"] == 1 and
        state["round1_player_x"] == 1074 and
        state["round1_player_z"] == 320 and
        state["round1_player_facing"] == 1 and
        state["round1_player_source_action"] == 0 and
        state["round1_player_controller_updates"] == 301 and
        state["round1_scheduler_frames"] == 301 and
        state["round1_scheduler_dispatches"] == 3010 and
        state["round1_scheduler_trace_count"] == 10 and
        state["round1_scheduler_order_hash"] == -2089937380 and
        state["round1_actor_handler_dispatches"] == 3010 and
        state["round1_presentation_bindings"] == 3010 and
        state["round1_state_context_bindings"] == 3010 and
        state["round1_presentation_ready"] == 1 and
        state["round1_presentation_seen"] == 1 and
        state["round1_presentation_commands_peak"] == 2):
    raise RuntimeError(f"Round 1 stable-entry target binding failed: {state}")
if (len(samples) != EVIDENCE_LAST_FRAME + 1 or
        any(sample["frame"] != index for index,sample in enumerate(samples))):
    raise RuntimeError("live synchronized ledger is incomplete")
contacts=[s for s in samples if s["player_contact"]]; received=[s for s in samples if s["alien_contact"]]
damage=[s for s in samples if s["player_damage"]]; misses=[s for s in samples if s["attack_miss"]]
if not (len(contacts) >= 4 and len(received) >= 1 and len(damage) >= 1 and len(misses) >= 1 and
        all(s["player_attack_active"] == 1 and s["alien_damage"] in (9,24,31) for s in contacts)):
    raise RuntimeError("live miss/contact/damage chronology failed")
unlock=next((i for i,s in enumerate(samples) if s["route_unlocked"]),None)
if unlock is None or samples[unlock]["alien_state"] != 0 or any(s["camera_world_x"] != 768 for s in samples[:unlock]):
    raise RuntimeError("clear/camera authority failed")
if not any(s["continued_after_unlock"] and s["camera_world_x"] > 768 for s in samples[unlock:]):
    raise RuntimeError("continued movement after unlock missing")

player_assemblies = {
    0x15F1F4:0x1626A4, 0x1600E8:0x1629E6, 0x1600F8:0x162A04,
    0x160108:0x1629E6, 0x160118:0x1629E6, 0x16012C:0x162A32,
    0x16013C:0x162A5A, 0x16014C:0x162A82, 0x16015C:0x162A5A,
    0x16016C:0x162A32, 0x16017C:0x162A32, 0x160190:0x162A32,
    0x1601A0:0x16144E, 0x1601B0:0x161476, 0x1601C0:0x1614A4,
    0x1601D0:0x161476, 0x1601E0:0x161476, 0x1601F4:0x162AA6,
    0x160204:0x162ABE, 0x160214:0x162AD6, 0x160224:0x162AFE,
    0x160234:0x162B26, 0x160244:0x162B5A, 0x160254:0x162B82,
    0x160264:0x162AA6, 0x160274:0x162AA6,
}
alien_assemblies = {
    0x12DDB0:0x130346,
    0x12EC04:0x12F7CC, 0x12EC14:0x12F7E4, 0x12EC24:0x12F7FC,
    0x12EC34:0x12F814, 0x12EC44:0x12F82C, 0x12EC54:0x12F85E,
    0x12EC64:0x12F890, 0x12EC74:0x12F8B8, 0x12E8EC:0x12F5DE,
    0x12E8FC:0x12FA0C, 0x12E90C:0x12FA2A, 0x12E91C:0x12FA0C,
    0x12D5E4:0x12FAE8, 0x12DD50:0x130248, 0x12DD28:0x13020C,
    0x12DD3C:0x13023A, 0x12D2F8:0x12F994, 0x12E214:0x13020C,
    0x12E224:0x13020C, 0x12E234:0x13020C, 0x12E244:0x13020C,
    0x12E254:0x130294, 0x12E268:0x130346,
}
if any(player_assemblies.get(s["player_animation_record"]) != s["player_assembly"]
       for s in samples):
    raise RuntimeError("player animation-record/assembly ownership drift")
alien_identity_drift = [
    {"frame":s["frame"], "state":s["alien_state"],
     "action":hex(s["alien_action"]),
     "record":hex(s["alien_animation_record"]),
     "assembly":hex(s["alien_assembly"]),
     "expected":hex(alien_assemblies.get(s["alien_animation_record"], 0))}
    for s in samples if s["alien_state"] != 0 and
    alien_assemblies.get(s["alien_animation_record"]) != s["alien_assembly"]
]
if alien_identity_drift:
    raise RuntimeError(f"alien animation-record/assembly ownership drift: {alien_identity_drift[:8]}")
for before, after in zip(samples, samples[1:]):
    if (before["player_state"] == after["player_state"] == 0 and
        after["player_lane"] != before["player_lane"] and
        (after["player_screen_y"] - before["player_screen_y"]) *
            (after["player_lane"] - before["player_lane"]) >= 0):
        raise RuntimeError("world-z/screen-y sign drift")
neutral_latches = [after for before, after in zip(samples, samples[1:])
                   if before["input_mask"] & 0x0008 and
                   after["input_mask"] == 0 and after["player_state"] == 0]
if not neutral_latches or any(s["player_facing"] != 1 for s in neutral_latches):
    raise RuntimeError("neutral release facing latch drift")
for key in ("player_health", "player_state", "player_facing",
            "player_animation_record", "player_assembly", "player_screen_y",
            "alien_health", "alien_state", "alien_action", "alien_facing",
            "alien_animation_record", "alien_assembly", "alien_screen_y"):
    if state[key] != current_sample[key]:
        raise RuntimeError(f"same-tick diagnostic drift for {key}")
process=tools.process_record(args.emulator_pid); executable=Path(str(process["executable"]))
settings=Path(os.environ["APPDATA"])/"YabaSanshiro/yabause.ini"
report={"schema":1,"task_id":inventory["task_id"],"card_profile":inventory["card_profile"],
        "source_commit":build["source_commit"],"iso_sha256":build["artifacts"]["game_iso"]["sha256"],
        "state":state,"samples":samples,"chronology":{"player_contacts":len(contacts),
        "alien_contacts":len(received),"player_damage_events":len(damage),"misses":len(misses),
        "unlock_frame":unlock},
        "visual_scanout":"UNAVAILABLE_WINDOWS_ACCELERATED_SURFACE",
        "emulator":{"identity":"Yaba Sanshiro 1.20.37-2986eb","evidence_tier":"ONE_EMULATOR",
        "process_id":process["pid"],"executable_sha256":sha(executable),"settings_sha256":sha(settings),
        "command_line":process["command_line"]},"physical_saturn":"UNRUN","result":"PASS"}
output=run_root/"readback.json"; output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="ascii")
print(f"recorded {output.relative_to(ROOT)}")
