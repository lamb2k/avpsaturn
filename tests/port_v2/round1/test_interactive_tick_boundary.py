#!/usr/bin/env python3
"""Normal play must not reach capture cadence or packed phase tables.

Static call-graph control over round1.c plus main.c's non-AUTOTEST code. It
fails if a forbidden helper is reachable from the interactive frame step.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FORBIDDEN = {
    "avsp_round1_coffee_shop_source_updates",
    "avsp_round1_coffee_shop_scheduler_source_updates",
    "avsp_round1_coffee_shop_record20_prefix_source_updates",
    "avsp_round1_coffee_shop_class02_source_updates",
    "avsp_round1_coffee_shop_class0a_source_updates",
    "avsp_round1_coffee_shop_class00_source_updates",
    "avsp_round1_coffee_exit_player_source_updates",
    "avsp_round1_coffee_exit_class00_phase_events",
    "avsp_round1_coffee_exit_callback_updates",
    "avsp_round1_step_coffee_exit_source_phase_program",
}
# Known remaining reference: step_first_entry's exit branch reads the callback
# table, but the tick wrapper routes exit withdrawal around that branch.
GUARDED = {("avsp_round1_step_first_entry",
            "avsp_round1_coffee_exit_callback_updates")}


def strip_autotest(text):
    out, depth = [], 0
    keep = [True]
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#ifdef AVSP_LIVE_ENCOUNTER_AUTOTEST"):
            keep.append(False)
            continue
        if s.startswith("#if"):
            keep.append(keep[-1])
        elif s.startswith("#else") and len(keep) > 1:
            keep[-1] = not keep[-1] if all(keep[:-1]) else False
            continue
        elif s.startswith("#endif") and len(keep) > 1:
            keep.pop()
            continue
        if all(keep):
            out.append(line)
    return "\n".join(out)


def bodies(text):
    found = {}
    for m in re.finditer(r"^[a-zA-Z_][\w \*]*?\b(\w+)\s*\([^;{]*\)\s*\{", text, re.M):
        depth, i = 1, m.end()
        while depth and i < len(text):
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        found[m.group(1)] = text[m.end():i]
    return found


def reachable_violations(graph, root):
    seen, stack, bad = set(), [root], []
    while stack:
        name = stack.pop()
        if name in seen or name not in graph:
            continue
        seen.add(name)
        for callee in set(re.findall(r"\b(avsp_\w+)\s*\(", graph[name])):
            if callee in FORBIDDEN and (name, callee) not in GUARDED:
                bad.append((name, callee))
            stack.append(callee)
    return bad


def main():
    source = (ROOT / "src/port_v2/gameplay/round1/round1.c").read_text()
    graph = bodies(source)
    assert "avsp_round1_step_interactive_frame" in graph
    bad = reachable_violations(graph, "avsp_round1_step_interactive_frame")
    assert not bad, bad
    main_c = strip_autotest((ROOT / "main.c").read_text(errors="replace"))
    start = main_c.index("static void live_encounter_frame_callback")
    end = main_c.index("static void playable_slice_frame_callback", start)
    callback = main_c[start:end]
    assert "avsp_round1_step_interactive_frame" in callback
    for name in FORBIDDEN:
        assert name not in callback, name
    # Negative control: the check must see an injected capture read.
    poisoned = dict(graph)
    poisoned["avsp_round1_tick_once"] += \
        " avsp_round1_coffee_shop_source_updates(1);"
    assert reachable_violations(poisoned, "avsp_round1_step_interactive_frame")
    print("interactive tick boundary PASS")


if __name__ == "__main__":
    sys.exit(main())
