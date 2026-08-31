#!/usr/bin/env python3
"""Reject SCU-DMA A-bus endpoints in the native composite upload path."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MAIN = (ROOT / "main.c").read_text()
TOOLS = (ROOT / ".deps/joengine/jo_engine/jo/tools.h").read_text()


def accepts(body: str) -> bool:
    helper_start = body.index(
        "static int round1_replace_4bits_image_from_cart_cpu(")
    helper = body[helper_start:body.index(
        "static void round1_composite_begin_frame", helper_start)]
    initialize = body[
        body.index("static int round1_initialize_fixed_vdp1_pools(void)"):
        body.index("static int round1_composite_sprite_for_entry(")
    ]
    replace = body[
        body.index("static int round1_composite_sprite_for_entry("):
        body.index("static int draw_round1_source_actor(")
    ]
    return all((
        "#define AVSP_CART_DRAM1_BASE ((unsigned char *)0x22600000)" in body,
        "#define round1_composite_scratch AVSP_COMPOSITE_SCRATCH_BASE" in body,
        "volatile unsigned long *destination" in helper,
        "*destination++ = *source++;" in helper,
        "jo_dma_copy" not in helper,
        "jo_sprite_replace_4bits_image" not in helper,
        "image.data = JO_NULL;" in initialize,
        "jo_sprite_add_4bits_image(&image)" in initialize,
        "image.data = round1_composite_scratch;" in replace,
        "round1_replace_4bits_image_from_cart_cpu(" in replace,
        "jo_sprite_replace_4bits_image(" not in replace,
    ))


assert "slDMACopy(src, dest, size);" in TOOLS
assert accepts(MAIN)
mutations = (
    MAIN.replace("image.data = JO_NULL;\n        memset(slot",
                 "image.data = round1_composite_scratch;\n        memset(slot", 1),
    MAIN.replace("*destination++ = *source++;",
                 "jo_dma_copy(source, destination, byte_count);", 1),
    MAIN.replace("if (round1_replace_4bits_image_from_cart_cpu(",
                 "if (jo_sprite_replace_4bits_image(", 1),
    MAIN.replace("#define round1_composite_scratch AVSP_COMPOSITE_SCRATCH_BASE",
                 "static unsigned char round1_composite_scratch[AVSP_COMPOSITE_MAX_TEXTURE_BYTES];", 1),
)
for mutant in mutations:
    assert not accepts(mutant)
print("REIMPLEMENT-13 cart-to-VDP1 CPU upload rule: PASS "
      "(4 SCU-DMA/A-bus endpoint mutations rejected; physical tier UNRUN)")
