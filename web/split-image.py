# Split game.chd into 100 MiB parts and write build.json listing them. usage: split-image.py CHD OUT_DIR LABEL COMMIT
import hashlib, json, pathlib, sys
chd, out, label, commit = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3], sys.argv[4]
out.mkdir(parents=True, exist_ok=True)
SIZE = 100 * 1048576
whole = hashlib.sha256(); parts = []; total = 0
with chd.open("rb") as f:
    while (b := f.read(SIZE)):
        whole.update(b); total += len(b)
        name = f"{chd.stem}-{whole.hexdigest()[:8]}.{len(parts):03d}"
        (out / name).write_bytes(b); parts.append({"path": f"/files/{name}", "bytes": len(b)})
build = {"schema": 2, "status": "ready", "build": label, "commit": commit,
         "image": {"name": chd.name, "bytes": total, "sha256": whole.hexdigest(), "parts": parts}}
(out / "build.json").write_text(json.dumps(build))
print(json.dumps(build, indent=1))
