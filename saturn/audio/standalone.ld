OUTPUT_FORMAT("elf32-sh")
ENTRY(_start)
SECTIONS {
  . = 0x06004000;
  .text : { *(.text.start) *(.text*) *(.rodata*) }
  .data : { *(.data*) }
  .bss : { ___bss_start = .; *(.bss*) *(COMMON) ___bss_end = .; }
}
