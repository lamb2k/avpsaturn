"""Synthetic host regressions for the next-stage load window keep (tools/stage_window.py, STAGE_WINDOW=1): no ROM, console or private asset inputs."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import char_fuzz
import stage_window

PAGE = 0x400
LIMIT = 0x200000 // PAGE


def pad(ps):
    return sorted({p + d for p in ps for d in (-1, 0, 1) if 0 <= p + d < LIMIT})


CENSUS = {"00": [100], "02": [20, 21], "04": [30, 31, 32, 33], "06": [40, 41, 42, 43, 44]}
DATA = dict(version=1, page=PAGE, frames=45, census=CENSUS, window={"04": [30, 32], "06": [41]}, runs={"04": 3, "06": 2}, sources=[])


def rounds(census=CENSUS):
    mk = lambda name, st, **kw: dict(name=name, stages=[st], keys=[[1, 2], [], [], []], **kw)
    order = sorted(int(k, 16) for k in census)
    keep = {}
    for k in census:
        s = int(k, 16)
        if s == 0:
            keep[s] = pad(sorted({p for v in census.values() for p in v}))
        else:
            nxt = next((x for x in order if x > s), None)
            keep[s] = pad(sorted(set(census[k]) | set(census["00"]) | set(census.get("%02x" % nxt, []) if nxt is not None else [])))
    return dict(page=PAGE, files=[mk("front", 0, keep_pages=keep[0]), mk("stage02", 2, keep_pages=keep[2]), mk("stage04", 4, keep_pages=keep[4]),
                                  mk("stage04_m1", 4, mask=1, keep_pages=keep[4]), mk("stage06", 6, keep_pages=keep[6])])


class WindowTests(unittest.TestCase):
    def test_next_stage_term_becomes_the_window(self):
        r = rounds()
        rep = stage_window.apply(r, DATA)
        f = {x["name"]: x for x in r["files"]}
        self.assertEqual(f["stage02"]["keep_pages"], pad([20, 21, 100, 30, 32]))   # own, front, window of 04 (not 31, 33)
        self.assertEqual(f["stage04"]["keep_pages"], pad([30, 31, 32, 33, 100, 41]))
        self.assertEqual(f["stage04_m1"]["keep_pages"], f["stage04"]["keep_pages"])   # a variant keeps what its stage's base file keeps
        self.assertEqual(f["stage06"]["keep_pages"], pad([40, 41, 42, 43, 44, 100]))   # last stage: nothing next
        self.assertEqual(f["front"]["keep_pages"], pad([100, 20, 21, 30, 31, 32, 33, 40, 41, 42, 43, 44]))   # the front end keeps everything
        self.assertEqual((rep["windowed"], rep["files"]), (3, 4))
        self.assertGreater(rep["pages_freed"], 0)

    def test_window_pages_are_a_subset_of_the_old_keep(self):
        r = rounds()
        old = {x["name"]: set(x["keep_pages"]) for x in r["files"]}
        stage_window.apply(r, DATA)
        for x in r["files"]:
            self.assertLessEqual(set(x["keep_pages"]), old[x["name"]])

    def test_stage_without_window_run_stays_whole(self):
        r = rounds()
        d = dict(DATA, window={"04": [30]}, runs={"04": 1})
        rep = stage_window.apply(r, d)
        f = {x["name"]: x for x in r["files"]}
        self.assertEqual(f["stage04"]["keep_pages"], pad([30, 31, 32, 33, 100, 40, 41, 42, 43, 44]))
        self.assertEqual(rep["whole"], ["06"])

    def test_min_runs(self):
        r = rounds()
        stage_window.apply(r, DATA, min_runs=3)   # 06 has 2 runs: its predecessor keeps all of 06
        f = {x["name"]: x for x in r["files"]}
        self.assertEqual(f["stage04"]["keep_pages"], pad([30, 31, 32, 33, 100, 40, 41, 42, 43, 44]))
        self.assertEqual(f["stage02"]["keep_pages"], pad([20, 21, 100, 30, 32]))

    def test_census_mismatch_is_refused(self):
        r = rounds()
        r["files"][1]["keep_pages"] = r["files"][1]["keep_pages"] + [900]
        with self.assertRaises(ValueError):
            stage_window.apply(r, DATA)

    def test_missing_data_is_refused(self):
        with self.assertRaises(ValueError):
            stage_window.apply(rounds(), None)

    def test_fuzz_pages_use_the_window_for_the_next_stage(self):
        fz = dict(version=1, page=PAGE, palette={}, pages={"00": [100], "02": [20], "04": [30, 31, 32, 33, 60], "06": [41, 70]}, player_script_pages=[], chars={})
        a, b = rounds(), rounds()
        char_fuzz.augment(a, fz, pages=True)
        char_fuzz.augment(b, fz, pages=True, window=stage_window.windows(DATA))
        lo, hi = char_fuzz.SCRIPT_REGION[0] // PAGE, (char_fuzz.SCRIPT_REGION[1] + PAGE - 1) // PAGE
        region = set(range(lo - 1, hi + 1))
        keep = lambda r, n: {p for x in r["files"] if x["name"] == n for p in x["keep_pages"]} - region
        self.assertIn(60, {p + d for p in (60,) for d in (-1, 0, 1)} & keep(a, "stage02"))   # the whole fuzz read set of 04 without the window
        self.assertNotIn(60, keep(b, "stage02"))
        self.assertNotIn(61, keep(b, "stage02"))
        self.assertIn(30, keep(b, "stage02"))

    def test_build_reads_window_files(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "run1").mkdir()
            (t / "run2").mkdir()
            (t / "run1" / "w04.txt").write_text("p 30\np 32\n")
            (t / "run2" / "w04.txt").write_text("p 32\np 33\n")
            (t / "run2" / "w06.txt").write_text("")   # a run that never entered 06
            census = dict(page=PAGE, stages={"any": dict(pages=[5]), "00": dict(pages=[100]), "04": dict(pages=[30]), "06": dict(pages=[40])})
            (t / "census.json").write_text(json.dumps(census))
            out = stage_window.build(t, t / "census.json", [t])
            self.assertEqual(out["window"], {"04": [30, 32, 33]})
            self.assertEqual(out["runs"], {"04": 2})
            self.assertEqual(out["census"]["04"], [5, 30])   # the KO and continue pages are in every stage
            self.assertEqual(stage_window.load(t)["window"], out["window"])


if __name__ == "__main__":
    unittest.main()
