"""Remove MAME's pre-save-state boot audio from the Stage 1 reference mix."""

from __future__ import annotations

import argparse
import wave
from pathlib import Path

CPS2_REFRESH_HZ = 59.637405
ROUTE_FRAMES = 14220 - 4200


def trim_route_tail(source: Path, destination: Path) -> None:
    with wave.open(str(source), "rb") as reader:
        parameters = reader.getparams()
        if parameters.nchannels != 2 or parameters.sampwidth != 2:
            raise ValueError("Expected MAME stereo 16-bit PCM output")
        keep_frames = round(ROUTE_FRAMES * parameters.framerate / CPS2_REFRESH_HZ)
        if parameters.nframes < keep_frames:
            raise ValueError(
                f"Capture has {parameters.nframes} frames, fewer than required {keep_frames}"
            )
        reader.setpos(parameters.nframes - keep_frames)
        audio = reader.readframes(keep_frames)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destination), "wb") as writer:
        writer.setparams(parameters._replace(nframes=0))
        writer.writeframes(audio)
    print(
        f"Trimmed Stage 1 QSound reference to {keep_frames / parameters.framerate:.3f}s "
        f"at {parameters.framerate} Hz"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    trim_route_tail(args.source, args.destination)


if __name__ == "__main__":
    main()
