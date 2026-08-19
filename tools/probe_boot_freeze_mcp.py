"""Headless boot-freeze probe over Yaba Sanshiro's MCP debug server.

Connects to the emulator's MCP endpoint (http://127.0.0.1:9640/mcp,
enabled via Debug\\McpServerEnabled=true in %APPDATA%/YabaSanshiro/
yabause.ini - the pathway proven by the MSHvSF reference lane), samples
the master SH2 PC continuously while the user plays toward the freeze,
and when the PC stops moving reports the stuck address, both CPUs' full
register text, and the surrounding sample history. Map the PC through
game.map to name the function.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request

ENDPOINT = "http://127.0.0.1:9640/mcp"


class Mcp:
    def __init__(self):
        self._id = 0

    def _post(self, payload):
        req = urllib.request.Request(
            ENDPOINT, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())

    def call(self, name, arguments=None):
        self._id += 1
        out = self._post({"jsonrpc": "2.0", "id": self._id,
                          "method": "tools/call",
                          "params": {"name": name,
                                     "arguments": arguments or {}}})
        content = out.get("result", {}).get("content", [])
        return "".join(c.get("text", "") for c in content)

    def initialize(self):
        self._id += 1
        self._post({"jsonrpc": "2.0", "id": self._id, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05",
                               "capabilities": {},
                               "clientInfo": {"name": "avsp-freeze-probe",
                                              "version": "1"}}})


def pc_of(text):
    m = re.search(r"PC[=:\s]+([0-9A-Fa-f]{6,8})", text)
    return m.group(1).upper() if m else None


def main():
    c = Mcp()
    c.initialize()
    print("connected; sampling master SH2 PC (play toward the freeze)...")
    history = []
    stable = 0
    last = None
    while True:
        try:
            text = c.call("registers_get", {"cpu": "master"})
        except Exception as e:
            print("poll error:", e)
            time.sleep(1)
            continue
        pc = pc_of(text)
        now = time.strftime("%H:%M:%S")
        history.append((now, pc))
        if len(history) % 10 == 0:
            print("  %s PC=%s" % (now, pc))
        if pc is not None and pc == last:
            stable += 1
        else:
            stable = 0
        last = pc
        if stable >= 40:  # ~12s of identical PC = genuinely stuck
            print("\nSTUCK PC = 0x%s (stable for %d samples)" % (pc, stable))
            print("\n--- master registers ---")
            print(c.call("registers_get", {"cpu": "master"}))
            print("\n--- slave registers ---")
            print(c.call("registers_get", {"cpu": "slave"}))
            print("\nlast 20 samples:")
            for t, p in history[-20:]:
                print("  %s %s" % (t, p))
            print("\nMap the PC through game.map to name the function.")
            return 0
        time.sleep(0.3)


if __name__ == "__main__":
    sys.exit(main())
