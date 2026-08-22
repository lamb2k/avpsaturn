#!/usr/bin/env python3
import argparse, copy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def req(c,m):
    if not c: raise AssertionError(m)
def validate(c):
    req(c["task_id"]=="SALVAGE-02-ENEMY-RENDER-ANIMATION","task identity")
    req((c["card_profile"],c["compile_profile"],c["manifest_profile"],c["interface_version"]) == ("EnemySalvageBench","debug-enemy-salvage-bench","enemy-salvage-bench",1),"profile")
    req(c["source_actor"]=={"class_id":31,"palette_bank":17,"lane":200,"facing":-1},"source actor")
    req(c["animation"]=={"clip":"walk","source_frame_count":39,"unique_poses":19},"source duration")
    req(c["samples"]["stationary"]=={"frame":20,"phase":0,"x":192} and c["samples"]["translated"]=={"frame":140,"phase":1,"x":240},"schedule")
    req(len(c["negative_controls"])==2 and c["physical_saturn"]=="UNRUN","controls/evidence tier")
def main():
 p=argparse.ArgumentParser(); p.add_argument("--negative-control",action="store_true"); a=p.parse_args(); c=json.loads((HERE/"enemy_contract.json").read_text()); validate(c)
 for rel,h in {**c["source_evidence_sha256"],**c["approved_lock_sha256"],**c["local_build_dependency_sha256"]}.items(): req(sha(ROOT/rel)==h,"hash drift: "+rel)
 capture=json.loads((ROOT/"data/enemy_action_capture.json").read_text()); walk=next(clip for clip in capture["clips"] if clip["name"]=="walk"); req((walk["frame_count"],walk["unique_poses"])==(39,19),"source walk evidence drifted")
 source=(ROOT/"main.c").read_text();
 for token in ("enemy_bench_frame_callback","AVSP_ENEMY_SALVAGE_BENCH","avsp_diag_enemy_negative_rejections","avsp_tiles_bank_slot(&tile_archive, 0x1Fu)","avsp_tiles_find(&tile_archive, 0xFFFFu)","draw_rom_actor_tiles(enemy, 0)"): req(token in source,"missing wiring: "+token)
 if a.negative_control:
  bad=copy.deepcopy(c); bad["animation"]["source_frame_count"]=38
  try: validate(bad)
  except AssertionError: print("Enemy perturbation control: PASS"); return
  raise AssertionError("mutated source duration accepted")
 print("EnemySalvageBench contract: PASS")
if __name__=="__main__": main()
