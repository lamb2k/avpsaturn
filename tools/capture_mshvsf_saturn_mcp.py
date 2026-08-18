#!/usr/bin/env python3
"""Capture deterministic Saturn memory anchors through Yaba Sanshiro's MCP server."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


REGIONS = {
    "low_wram": (0x00200000, 0x100000),
    "high_wram": (0x06000000, 0x100000),
    "cart_dram": (0x02400000, 0x400000),
    "sound_ram": (0x05A00000, 0x080000),
    "vdp1_vram": (0x05C00000, 0x080000),
    "vdp2_vram": (0x05E00000, 0x080000),
    "vdp2_cram": (0x05F00000, 0x001000),
    "vdp1_regs": (0x05D00000, 0x000020),
    "vdp2_regs": (0x05F80000, 0x000120),
    "scsp_regs": (0x05B00000, 0x001000),
    "scu_regs": (0x05FE0000, 0x000100),
}

FRAME_RE = re.compile(r"^frame:\s*(\d+)\s*$", re.MULTILINE)
STATE_RE = re.compile(r"^state:\s*(\w+)\s*$", re.MULTILINE)
HEX_LINE_RE = re.compile(r"^[0-9a-fA-F]{8}:\s+((?:[0-9a-fA-F]{2}\s+){1,16})")


@dataclass(frozen=True)
class Anchor:
    label: str
    frame: int


class McpClient:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.next_id = 1
        self._initialize()

    def _post(self, payload: dict[str, object]) -> dict[str, object]:
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _initialize(self) -> None:
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self.next_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "mshvsf-saturn-capture", "version": "1.0"},
                },
            }
        )
        self.next_id += 1
        if "result" not in response:
            raise RuntimeError(f"MCP initialization failed: {response}")

    def call(self, name: str, arguments: dict[str, object] | None = None) -> str:
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self.next_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments or {}},
            }
        )
        self.next_id += 1
        result = response.get("result")
        if not isinstance(result, dict):
            raise RuntimeError(f"MCP tool {name} failed: {response}")
        content = result.get("content")
        if result.get("isError") or not isinstance(content, list):
            raise RuntimeError(f"MCP tool {name} failed: {response}")
        return "\n".join(
            str(item.get("text", "")) for item in content if isinstance(item, dict)
        )


def parse_status(text: str) -> tuple[str, int]:
    state_match = STATE_RE.search(text)
    frame_match = FRAME_RE.search(text)
    if not state_match or not frame_match:
        raise ValueError(f"Unrecognized debug status:\n{text}")
    return state_match.group(1), int(frame_match.group(1))


def parse_hexdump(text: str, expected_length: int) -> bytes:
    output = bytearray()
    for line in text.splitlines():
        match = HEX_LINE_RE.match(line)
        if match:
            output.extend(bytes.fromhex(match.group(1)))
    if len(output) != expected_length:
        raise ValueError(
            f"Memory response decoded to {len(output)} bytes, expected {expected_length}"
        )
    return bytes(output)


def wait_and_pause(client: McpClient, target_frame: int) -> str:
    status_text = client.call("debug_status")
    state, frame = parse_status(status_text)
    if frame > target_frame:
        raise RuntimeError(
            f"Replay is already at frame {frame}, beyond requested frame {target_frame}"
        )
    if state == "stopped" and frame < target_frame:
        client.call("resume")

    while True:
        status_text = client.call("debug_status")
        state, frame = parse_status(status_text)
        if state == "stopped":
            if frame == target_frame:
                return status_text
            if frame < target_frame:
                client.call("resume")
                continue
            raise RuntimeError(f"Unexpected stop at frame {frame}")
        # The deterministic replay can run much faster than wall-clock 60 Hz.
        # Brake well before the anchor, then use back-to-back resume/pause
        # calls to advance one frame boundary at a time without a polling race.
        if frame >= target_frame - 12:
            client.call("pause")
            paused_text = client.call("debug_status")
            paused_state, paused_frame = parse_status(paused_text)
            if paused_state != "stopped" or paused_frame > target_frame:
                raise RuntimeError(
                    f"Frame capture missed target {target_frame}; stopped at {paused_frame}"
                )
            while paused_frame < target_frame:
                client.call("resume")
                client.call("pause")
                paused_text = client.call("debug_status")
                paused_state, paused_frame = parse_status(paused_text)
                if paused_state != "stopped" or paused_frame > target_frame:
                    raise RuntimeError(
                        f"Single-frame advance missed target {target_frame}; "
                        f"stopped at {paused_frame}"
                    )
            return paused_text

        remaining = target_frame - frame
        if remaining > 240:
            time.sleep(min(0.05, (remaining - 180) / 1200.0))
        elif remaining > 130:
            time.sleep(0.001)
        else:
            time.sleep(0)


def dump_region(
    client: McpClient, address: int, length: int, chunk_size: int
) -> bytes:
    output = bytearray()
    for offset in range(0, length, chunk_size):
        request_length = min(chunk_size, length - offset)
        text = client.call(
            "memory_read",
            {
                "address": f"0x{address + offset:08X}",
                "length": request_length,
                "format": "hexdump",
            },
        )
        output.extend(parse_hexdump(text, request_length))
    return bytes(output)


def parse_anchor(value: str) -> Anchor:
    try:
        label, frame_text = value.rsplit(":", 1)
        frame = int(frame_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("anchor must be LABEL:FRAME") from error
    if not label or frame < 0:
        raise argparse.ArgumentTypeError("anchor must have a label and nonnegative frame")
    return Anchor(label=label, frame=frame)


def capture_anchor(
    client: McpClient,
    anchor: Anchor,
    output_root: Path,
    selected_regions: list[str],
    chunk_size: int,
) -> dict[str, object]:
    status_text = wait_and_pause(client, anchor.frame)
    anchor_dir = output_root / f"{anchor.frame:05d}_{anchor.label}"
    if anchor_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing anchor: {anchor_dir}")
    anchor_dir.mkdir(parents=True)

    register_text = {
        "master": client.call("registers_get", {"cpu": "master"}),
        "slave": client.call("registers_get", {"cpu": "slave"}),
    }
    region_records: list[dict[str, object]] = []
    for name in selected_regions:
        address, length = REGIONS[name]
        data = dump_region(client, address, length, chunk_size)
        path = anchor_dir / f"{name}.bin"
        path.write_bytes(data)
        region_records.append(
            {
                "name": name,
                "address": f"0x{address:08X}",
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "file": path.name,
            }
        )

    manifest = {
        "label": anchor.label,
        "requested_frame": anchor.frame,
        "captured_frame": parse_status(status_text)[1],
        "debug_status": status_text,
        "registers": register_text,
        "regions": region_records,
    }
    (anchor_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--anchor",
        action="append",
        type=parse_anchor,
        required=True,
        help="Deterministic anchor as LABEL:FRAME; may be repeated",
    )
    parser.add_argument(
        "--endpoint", default="http://127.0.0.1:9640/mcp"
    )
    parser.add_argument(
        "--output-root", type=Path, default=Path(".deps/mshvsf_saturn_state")
    )
    parser.add_argument(
        "--regions",
        default=",".join(REGIONS),
        help="Comma-separated region names",
    )
    parser.add_argument("--chunk-size", type=int, default=0x10000)
    parser.add_argument("--resume-after-final", action="store_true")
    args = parser.parse_args()

    selected_regions = [item.strip() for item in args.regions.split(",") if item.strip()]
    unknown = sorted(set(selected_regions) - set(REGIONS))
    if unknown:
        parser.error(f"unknown regions: {', '.join(unknown)}")
    if args.chunk_size <= 0 or args.chunk_size % 16:
        parser.error("--chunk-size must be a positive multiple of 16")
    anchors = sorted(args.anchor, key=lambda item: item.frame)
    if len({item.frame for item in anchors}) != len(anchors):
        parser.error("anchor frames must be unique")

    client = McpClient(args.endpoint)
    manifests = []
    for index, anchor in enumerate(anchors):
        manifest = capture_anchor(
            client, anchor, args.output_root, selected_regions, args.chunk_size
        )
        manifests.append(manifest)
        print(f"Captured {anchor.label} at frame {anchor.frame}")
        if index + 1 < len(anchors):
            client.call("resume")
    if args.resume_after_final:
        client.call("resume")

    session = {
        "endpoint": args.endpoint,
        "anchors": [
            {
                "label": item["label"],
                "requested_frame": item["requested_frame"],
                "captured_frame": item["captured_frame"],
                "regions": item["regions"],
            }
            for item in manifests
        ],
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "session.json").write_text(
        json.dumps(session, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
