SECTIONS {
    .text 0x06004000 : { *boot.o(.text.startup) *(.text) *(.text.*) *("SEGA_P") *(.strings) *(.rodata*) *(.data*) }
    .bss ALIGN(16) (NOLOAD) : { __bstart = .; *(.bss) *(COMMON) __bend = .; }
    /DISCARD/ : { *(.eh_frame*) *(.comment) }
}
