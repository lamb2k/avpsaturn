# Private: F-Zero X ROM for fzero-x-saturn's ROM lane

The owner's own copy of F-Zero X (USA), stored here privately so cloud sessions working on
lamb2k/fzero-x-saturn can run its ROM lane. This branch shares no history with this
repository's main; delete the branch to remove it.

Never copy this file, or anything extracted from it, into a public repository, a CI log, an
issue or a chat. fzero-x-saturn's hygiene scan rejects ROMs and their fingerprints.

| File | Contents |
| --- | --- |
| `F-Zero_X_USA.zip` | `F-Zero X (USA).z64`, 16,777,216 bytes, US rev0 |
| `SHA256SUMS` | sha256 of the zip |

ROM fingerprint (what `tools/import_course.py` verifies): md5 `753437d0d8ada1d12f3f9cf0f0a5171f`,
sha1 `5f658e88ffa9de23cba6986a8fd3d3a90d7b4340`.

## Fetch into a session (outside every repository checkout)

```sh
S=<session scratchpad>/rom
mkdir -p "$S" && cd "$S"
git init -q && git fetch -q --depth 1 https://github.com/lamb2k/avpsaturn private/fzero-x-rom
git checkout -q FETCH_HEAD -- F-Zero_X_USA.zip SHA256SUMS && sha256sum -c SHA256SUMS
python3 -I -c "import zipfile; z=zipfile.ZipFile('F-Zero_X_USA.zip'); open('fzx.z64','wb').write(z.read(z.namelist()[0]))"
export FZX_TEST_ROM="$S/fzx.z64" FZX_EVIDENCE="<session scratchpad>/evidence"
```

The session needs lamb2k/avpsaturn attached (read access is enough).
