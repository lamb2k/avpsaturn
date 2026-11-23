"""Host-only checks for stage-pack residency and safe reuse of generated R*.BIN.

The receipt lives in the private build directory. It contains hashes, never
ROM bytes. A relink may refresh ROM restores after reuse has been validated;
the refreshed round files must then get a new receipt.
"""
import hashlib
import json
from pathlib import Path


RECEIPT_VERSION = 1


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def packing_inputs(plan, layout, controls, source_files):
    """Fingerprint effective planning data and every file the packer consumes.

    An explicit None denotes an optional absent input. Required files raise on
    absence, so a kept pack cannot silently stand in for missing source data.
    Repeated audio/graphics paths are hashed only once.
    """
    hashes, seen = {}, {}
    for label, path in sorted(source_files.items()):
        if path is None:
            hashes[label] = None
            continue
        path = Path(path).resolve()
        if path not in seen:
            seen[path] = file_hash(path)
        hashes[label] = seen[path]
    inputs = dict(version=RECEIPT_VERSION, plan=plan, layout=layout,
                  controls=controls, sources=hashes)
    encoded = json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def round_names(count):
    if count < 1 or count > 511:
        raise ValueError("stage store requires 1..511 round files")
    return ["R%03d.BIN" % i for i in range(count)]


def store_header_sectors(count):
    """Match tools/sector_store.py's directory, independent of guest env flags."""
    round_names(count)
    return (8 + 8 * count + 2047) // 2048


def extra_rounds(directory, names):
    expected = set(names)
    return sorted(p for p in Path(directory).glob("R[0-9][0-9][0-9].BIN")
                  if p.name not in expected)


def reuse_reason(receipt, inputs, directory, names):
    """None means safe to reuse; otherwise return the concrete rebuild reason."""
    try:
        old = json.loads(Path(receipt).read_text())
    except (OSError, ValueError):
        return "no valid stage-pack receipt"
    if not isinstance(old, dict) or old.get("version") != RECEIPT_VERSION:
        return "stage-pack receipt version changed"
    if old.get("inputs") != inputs:
        return "stage-pack inputs or layout changed"
    files = old.get("files")
    if not isinstance(files, dict) or set(files) != set(names):
        return "stage-pack file set changed"
    if extra_rounds(directory, names):
        return "surplus stage-pack files"
    for name in names:
        try:
            actual = file_hash(Path(directory) / name)
        except OSError:
            return "missing stage pack " + name
        if files[name] != actual:
            return "stage-pack contents changed: " + name
    return None


def save_receipt(receipt, inputs, directory, names):
    if extra_rounds(directory, names):
        raise ValueError("refusing to record surplus stage-pack files")
    result = dict(version=RECEIPT_VERSION, inputs=inputs,
                  files={name: file_hash(Path(directory) / name) for name in names})
    receipt = Path(receipt)
    temporary = receipt.with_name(receipt.name + ".tmp")
    temporary.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    temporary.replace(receipt)


def require_guest_tiles(name, required, candidates, dropped, plan, owner="guest"):
    """Priority is a preference. Required tiles must all survive packing."""
    if plan is None:
        raise ValueError("NO-GO: stage pack does not fit: " + name)
    missing = (set(required) - set(candidates)) | (set(required) & set(dropped))
    if missing:
        sample = ", ".join("%04x" % key for key in sorted(missing)[:12])
        raise ValueError("NO-GO: %s loses %d required %s tiles (%s); "
                         "free pack space" % (name, len(missing), owner, sample))


def require_unused_remap(label, remapped, arcade_keys):
    """An old guest remap must not overwrite a newly required arcade tile."""
    overlap = set(remapped) & set(arcade_keys)
    if overlap:
        sample = ", ".join("%04x" % key for key in sorted(overlap)[:12])
        raise ValueError("NO-GO: %s remap overlaps %d arcade sprite keys (%s); "
                         "regenerate guest assets from the current census" %
                         (label, len(overlap), sample))
