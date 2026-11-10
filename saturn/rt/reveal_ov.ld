/* The post-credits reveal as an overlay (reveal.c): one block at the cart pack room's 0x02750000, read from the disc (REVCODE.BIN) at the ending. The table at the head is read by guests.c sat_reveal_poll. */
SECTIONS
{
  . = 0x02750000;
  .ov : {
    KEEP(*(.ovhead))
    *(.text .text.*)
    *(.rodata .rodata.*)
    *(.data .data.*)
    . = ALIGN(4);
  }
  /DISCARD/ : { *(.comment) *(.eh_frame*) *(.bss) *(COMMON) }
}
