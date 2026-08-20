JO_COMPILE_WITH_VIDEO_MODULE = 0
JO_COMPILE_WITH_BACKUP_MODULE = 0
JO_COMPILE_WITH_TGA_MODULE = 1
JO_COMPILE_WITH_AUDIO_MODULE = 1
JO_COMPILE_WITH_3D_MODULE = 1
JO_COMPILE_WITH_FS_MODULE = 1
JO_COMPILE_WITH_PSEUDO_MODE7_MODULE = 0
JO_COMPILE_WITH_EFFECTS_MODULE = 0
JO_COMPILE_WITH_DUAL_CPU_MODULE = 0
JO_COMPILE_WITH_PRINTF_MODULE = 1
JO_COMPILE_WITH_SPRITE_HASHTABLE = 0
JO_PSEUDO_SATURN_KAI_SUPPORT = 0
JO_COMPILE_WITH_RAM_CARD_MODULE = 1
JO_GLOBAL_MEMORY_SIZE_FOR_MALLOC = 262144
JO_MAX_SPRITE = 128
JO_MAX_FILE_IN_IMAGE_PACK = 64
# Jo sizes __jo_fs_dirname[JO_FS_MAX_FILES] (24 bytes each) in BSS, and BSS
# must end below 0x060c0000 or jo_sprite_init() fails its bounds check and
# suspends at Jo's error screen. The stock 256 costs 6,144 bytes; the built
# disc holds 82 files in total and 31 in its largest directory (FRONT), so
# 128 keeps a 4x margin over the largest directory and still exceeds the
# whole-disc file count. conf.h is patched to make this overridable.
CCFLAGS += -DJO_FS_MAX_FILES=128
CCFLAGS += -include avsp_video_config.h
ifneq ($(AVSP_VISUAL_TEST),)
CCFLAGS += -DAVSP_VISUAL_TEST=1
endif
ifneq ($(AVSP_STREET_TEST),)
CCFLAGS += -DAVSP_STREET_TEST=1
endif
ifneq ($(AVSP_ENCOUNTER_TEST),)
CCFLAGS += -DAVSP_ENCOUNTER_TEST=1
endif
ifneq ($(AVSP_FRONTEND_TEST),)
CCFLAGS += -DAVSP_FRONTEND_TEST=1
endif
ifneq ($(AVSP_FRONTEND_SHOT_TEST),)
CCFLAGS += -DAVSP_FRONTEND_SHOT_TEST=1
endif
ifneq ($(AVSP_BOSS_HIT_TEST),)
CCFLAGS += -DAVSP_BOSS_HIT_TEST=1
endif
ifneq ($(AVSP_BOSS_KO_TEST),)
CCFLAGS += -DAVSP_BOSS_KO_TEST=1
endif
JO_DEBUG ?= 1
JO_NTSC = 1
JO_COMPILE_USING_SGL = 1

SRCS = main.c capability_model.c avsp_actor.c avsp_anim_script.c avsp_emit.c avsp_tiles.c avsp_collision.c avsp_cram.c avsp_frontend.c avsp_scene.c avsp_route.c avsp_scene_runtime.c

# The pinned Yaba Sanshiro boot path stalls when Jo Engine's monolithic first-
# read executable crosses 400 KiB. Keep the integration shell and frontend
# cold path size-optimized; gameplay, animation, emission, collision, tile and
# filesystem translation units retain -O2. Replace this compatibility measure
# with a small first-stage loader if later bodies cannot remain inside the
# envelope.
avsp_frontend.o: CCFLAGS += -Os

JO_ENGINE_ROOT ?= .deps/joengine
JO_ENGINE_SRC_DIR = $(JO_ENGINE_ROOT)/jo_engine
COMPILER_DIR = $(JO_ENGINE_ROOT)/Compiler

include $(COMPILER_DIR)/COMMON/jo_engine_makefile

# The disc first reads this compact program at Jo Engine's proven 0x06004000
# address. It stages the separately linked game payload in low work RAM, then
# a position-independent trampoline overwrites 0x06004000, purges the SH-2
# cache, and transfers control. Keeping this target in make preserves the
# bundled compiler's relative invocation path (its Windows GCC build cannot be
# invoked reliably through an absolute path containing spaces).
LOADER_CCFLAGS = -fno-common -fno-ident -fno-unwind-tables \
	-fno-asynchronous-unwind-tables -fomit-frame-pointer -Os \
	-nodefaultlibs -nostdlib -fno-builtin -m2 -c -I$(SGLIDR)
LOADER_LDFLAGS = -m2 -L$(SGLLDR) -Xlinker -Tloader/loader.linker \
	-Xlinker -Map -Xlinker build/loader/loader.map -Xlinker -e \
	-Xlinker ___Start -nostartfiles

loader/loader.o: loader/loader.c
	$(CC) $< $(LOADER_CCFLAGS) -o $@

loader/trampoline.o: loader/trampoline.s
	$(CC) -m2 -c $< -o $@

build/loader/loader.elf: loader/loader.o loader/trampoline.o loader/loader.linker
	$(CC) $(LOADER_LDFLAGS) loader/loader.o loader/trampoline.o \
		$(SGLLDR)/SEGA_SYS.A $(SGLLDR)/LIBCD.A $(SGLLDR)/LIBSGL.A -o $@

build/loader/loader.raw: build/loader/loader.elf
	$(CONV) -O binary $< $@
