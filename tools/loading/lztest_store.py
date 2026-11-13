#!/usr/bin/env python
"""lztest_store.py OLD_STORE.BIN [OUT_STORE.BIN]: rebuilds the 287 round files from a plain STORE.BIN, builds the compressed store (tools/lzstore.py), and verifies every round file decodes back to the
original with zlib alone and (where the file takes the compressed path) with the loader's lz_unit in place. Prints sizes."""
import sys, struct, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import sector_store, lzstore
old = open(sys.argv[1], 'rb').read()
n = struct.unpack_from('>II', old)[1]
files = [sector_store.rebuild(old, i) for i in range(n)]
t0 = time.time()
store, streams, info = lzstore.build_lz(files)
print('built in', round(time.time() - t0, 1), 's', info)
bad = [i for i in range(n) if lzstore.rebuild_round(store, i) != files[i]]
print('rounds that differ after rebuild:', bad[:20], len(bad))
print('plain store sectors', len(old) // 2048, 'lz store sectors', len(store) // 2048, 'saved', len(old) // 2048 - len(store) // 2048)
if len(sys.argv) > 2: open(sys.argv[2], 'wb').write(store)
