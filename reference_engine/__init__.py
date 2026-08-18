"""Host-side CPS2-to-Saturn reference engine.

This package is an executable *specification*, not a runtime. It models how a
CPS2 game's semantic data becomes native Saturn work, in three explicit layers:

    source semantic layer  -> what the CPS2 game means
    translation layer      -> platform-neutral actor/animation/object records
    Saturn backend layer   -> VDP1/VDP2/SH-2/cartridge/SCSP responsibilities

It is not a CPS2 emulator, not a 68000 interpreter, not a Saturn executable,
and not permission to move Marvel constants into the AvP implementation lane.
Every modelled field carries an evidence label from ``reference_engine.evidence``.
"""

__all__ = ["evidence", "source_semantic", "translation", "vdp1", "saturn_backend", "trace", "scenario", "report"]

