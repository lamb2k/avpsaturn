#!/usr/bin/env python
"""Lane wv-native3 11-10: the essentials remap's asset set (offline, ROM-derived output, never in git).
D12 = D11 (the shipped Wolverine asset set) plus the tiles of the remap's frames, with the pack's key list pruned back to the size of D11's:
  1. gen_native.py with WV_ADD: every frame the remap names (SRC entries with record indexes) that has a tile with no resident tile within the merge distance gets that tile at a free AvP sprite key
     (gfx_wolverine.bin, remap.json keys and stage_keys of every stage extended);
  2. gen_native.py on that set with WV_KEYS_OUT: the keys his native records draw;
  3. stage_keys of every stage := those keys plus filler (D11's keys the native records no longer draw, ascending) up to D11's count, so no stage file's resident tile count grows (net 0 per file by
     construction; the fit run confirms);
  4. gen_native.py on the final set again: its output must equal step 2's byte for byte (pruning an unused key cannot change a match: a drawn key is the best match of its cells and stays).
usage: make_d12.py WORK D11_DIR MSHVSF_DUMP OUT_DIR [TMP_DIR]"""
import hashlib, json, os, pathlib, shutil, subprocess, sys

work, d11, mv, out = (pathlib.Path(a) for a in sys.argv[1:5])
tmp = pathlib.Path(sys.argv[5]) if len(sys.argv) > 5 else out.parent / (out.name + "_tmp")
gen = pathlib.Path(__file__).resolve().parent / "gen_native.py"
tmp.mkdir(parents=True, exist_ok=True)


def run(assets, inc, **env):
    e = dict(os.environ); e.update({k: str(v) for k, v in env.items()})
    r = subprocess.run([sys.executable, str(gen), str(work), str(assets), str(mv), str(inc)], env=e, capture_output=True, text=True)
    sys.stdout.write(r.stdout[-1500:]); sys.stderr.write(r.stderr[-1500:])
    if r.returncode: raise SystemExit("gen_native failed (%d)" % r.returncode)


full = tmp / "full"
run(d11, tmp / "unused.inc", WV_ADD=full)
keys_json = tmp / "used_keys.json"
run(full, tmp / "a.inc", WV_KEYS_OUT=keys_json)
used = set(json.loads(keys_json.read_text()))
A = json.loads((full / "remap.json").read_text())
B = json.loads((d11 / "remap.json").read_text())
n_pack = len(B["stage_keys"]["02"])
old = sorted(B["stage_keys"]["02"])
assert all(B["stage_keys"][s] == B["stage_keys"]["02"] for s in B["stage_keys"]), "D11 stage key lists differ between stages"
filler = [k for k in old if k not in used]
final = sorted(used)
need = n_pack - len(final)
assert need >= 0, "native records draw %d keys, over the pack's %d" % (len(used), n_pack)
final = sorted(set(final) | set(filler[:need]))
assert len(final) == n_pack
A["stage_keys"] = {s: list(final) for s in A["stage_keys"]}
A["wv_added"]["pack_keys"] = n_pack; A["wv_added"]["drawn_keys"] = len(used); A["wv_added"]["filler_kept"] = need; A["wv_added"]["filler_dropped"] = len(filler) - need
if out.exists(): shutil.rmtree(out)
shutil.copytree(full, out)
(out / "remap.json").write_text(json.dumps(A))
run(out, tmp / "b.inc")
ha, hb = (hashlib.sha256((tmp / n).read_bytes()).hexdigest() for n in ("a.inc", "b.inc"))
print("D12: pack keys %d (D11 %d), native records draw %d, new tiles %d, D11 keys kept as filler %d, dropped %d; native block identical after pruning: %s" % (
    n_pack, n_pack, len(used), len(A["wv_added"]["keys"]), need, len(filler) - need, ha == hb))
if ha != hb: raise SystemExit("pruning changed the native block")
shutil.rmtree(tmp)
