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
JO_MAX_SPRITE = 255
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
ifneq ($(AVSP_PLAYER_SALVAGE_BENCH),)
CCFLAGS += -DAVSP_PLAYER_SALVAGE_BENCH=1
endif
ifneq ($(AVSP_PLAYER_PROMOTION_BENCH),)
CCFLAGS += -DAVSP_PLAYER_PROMOTION_BENCH=1
endif
ifneq ($(AVSP_CAMERA_STAGE_SALVAGE_BENCH),)
CCFLAGS += -DAVSP_CAMERA_STAGE_SALVAGE_BENCH=1
endif
ifneq ($(AVSP_CAMERA_STAGE_PROMOTION_BENCH),)
CCFLAGS += -DAVSP_CAMERA_STAGE_PROMOTION_BENCH=1
endif
ifneq ($(AVSP_HUD_PCM_SALVAGE_BENCH),)
CCFLAGS += -DAVSP_HUD_PCM_SALVAGE_BENCH=1
endif
ifneq ($(AVSP_HUD_PROMOTION_BENCH),)
CCFLAGS += -DAVSP_HUD_PROMOTION_BENCH=1
endif
ifneq ($(AVSP_PCM_PROMOTION_BENCH),)
CCFLAGS += -DAVSP_PCM_PROMOTION_BENCH=1
endif
ifneq ($(AVSP_CDDA_RESIDENCY_SALVAGE_BENCH),)
CCFLAGS += -DAVSP_CDDA_RESIDENCY_SALVAGE_BENCH=1
endif
ifneq ($(AVSP_CDDA_RESIDENCY_PROMOTION_BENCH),)
CCFLAGS += -DAVSP_CDDA_RESIDENCY_PROMOTION_BENCH=1
endif
ifneq ($(AVSP_ENEMY_SALVAGE_BENCH),)
CCFLAGS += -DAVSP_ENEMY_SALVAGE_BENCH=1
endif
ifneq ($(AVSP_ENEMY_PROMOTION_BENCH),)
CCFLAGS += -DAVSP_ENEMY_PROMOTION_BENCH=1
endif
ifneq ($(AVSP_PLAYER_ENEMY_INTEGRATION),)
CCFLAGS += -DAVSP_PLAYER_ENEMY_INTEGRATION=1
endif
ifneq ($(AVSP_COLLISION_SALVAGE_BENCH),)
CCFLAGS += -DAVSP_COLLISION_SALVAGE_BENCH=1
endif
ifneq ($(AVSP_HIT_KO_PROMOTION_BENCH),)
CCFLAGS += -DAVSP_HIT_KO_PROMOTION_BENCH=1
endif
ifneq ($(AVSP_COMBAT_INTEGRATION_BENCH),)
CCFLAGS += -DAVSP_COMBAT_INTEGRATION_BENCH=1
endif
ifneq ($(AVSP_PLAYABLE_SLICE),)
CCFLAGS += -DAVSP_PLAYABLE_SLICE=1
endif
ifneq ($(AVSP_LIVE_ENCOUNTER),)
CCFLAGS += -DAVSP_LIVE_ENCOUNTER=1 -Werror -Wno-unused-function
endif
ifneq ($(AVSP_LIVE_ENCOUNTER_AUTOTEST),)
CCFLAGS += -DAVSP_LIVE_ENCOUNTER_AUTOTEST=1
endif
ifneq ($(AVSP_PROBE3),)
CCFLAGS += -DAVSP_PROBE3=1 -Werror -Wno-unused-function
endif
ifneq ($(AVSP_PREDATOR_WARRIOR_ACTION_SALVAGE_BENCH),)
CCFLAGS += -DAVSP_PREDATOR_WARRIOR_ACTION_SALVAGE_BENCH=1 -Werror -Wno-unused-function
endif
ifneq ($(AVSP_PREDATOR_WARRIOR_ACTION_PROMOTION_BENCH),)
CCFLAGS += -DAVSP_PREDATOR_WARRIOR_ACTION_PROMOTION_BENCH=1 -Werror -Wno-unused-function
endif
ifneq ($(AVSP_STREET_ALIEN_AI_SALVAGE_BENCH),)
CCFLAGS += -DAVSP_STREET_ALIEN_AI_SALVAGE_BENCH=1 -Werror -Wno-unused-function
endif
ifneq ($(AVSP_STREET_ALIEN_AI_PROMOTION_BENCH),)
CCFLAGS += -DAVSP_STREET_ALIEN_AI_PROMOTION_BENCH=1 -Werror -Wno-unused-function
endif
JO_DEBUG ?= 1
JO_NTSC = 1
JO_COMPILE_USING_SGL = 1

SRCS = main.c capability_model.c avsp_actor.c avsp_anim_script.c avsp_emit.c avsp_tiles.c avsp_collision.c avsp_cram.c avsp_frontend.c avsp_scene.c avsp_route.c avsp_scene_runtime.c avsp_disc_guard.c src/port_v2/player/player.c src/port_v2/enemy/enemy.c src/port_v2/camera/camera.c src/port_v2/stage/stage.c src/port_v2/hud/hud.c src/port_v2/audio/pcm/pcm.c src/port_v2/integration/player_enemy/player_enemy.c
ifneq ($(AVSP_COLLISION_SALVAGE_BENCH),)
SRCS += tests/port_v2/collision_bench/collision_bench.c
endif
ifneq ($(AVSP_HIT_KO_PROMOTION_BENCH),)
SRCS += src/port_v2/combat/hit_ko/hit_ko.c tests/port_v2/combat/hit_ko/diagnostic.c
endif
ifneq ($(AVSP_COMBAT_INTEGRATION_BENCH),)
SRCS += src/port_v2/combat/hit_ko/hit_ko.c src/port_v2/integration/combat/combat.c tests/port_v2/integration/combat/diagnostic.c
endif
ifneq ($(AVSP_CDDA_RESIDENCY_SALVAGE_BENCH),)
SRCS += tests/port_v2/cdda_residency_bench/cdda_residency_bench.c
endif
ifneq ($(AVSP_CDDA_RESIDENCY_PROMOTION_BENCH),)
SRCS += src/port_v2/audio/cdda/cdda.c src/port_v2/residency/residency.c
endif
ifneq ($(AVSP_PLAYABLE_SLICE),)
SRCS += src/port_v2/integration/slice/slice.c
endif
ifneq ($(AVSP_LIVE_ENCOUNTER),)
SRCS += src/port_v2/gameplay/player_action/player_action.c src/port_v2/gameplay/street_alien_ai/street_alien_ai.c src/port_v2/gameplay/round1/round1.c src/port_v2/integration/live_encounter/live_encounter.c
endif
ifneq ($(AVSP_PROBE3),)
SRCS += tests/hardware/probe3/probe3.c
endif
ifneq ($(AVSP_PREDATOR_WARRIOR_ACTION_SALVAGE_BENCH),)
SRCS += src/port_v2/gameplay/player_action/player_action.c
endif
ifneq ($(AVSP_PREDATOR_WARRIOR_ACTION_PROMOTION_BENCH),)
SRCS += src/port_v2/gameplay/player_action/player_action.c
endif
ifneq ($(AVSP_STREET_ALIEN_AI_SALVAGE_BENCH),)
SRCS += src/port_v2/gameplay/street_alien_ai/street_alien_ai.c
endif
ifneq ($(AVSP_STREET_ALIEN_AI_PROMOTION_BENCH),)
SRCS += src/port_v2/gameplay/street_alien_ai/street_alien_ai.c
endif

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

# These Jo Engine translation units own arrays whose ABI depends on
# JO_MAX_SPRITE.  The bundled rules do not treat the project makefile as an
# input, so a profile-size change can otherwise link stale 128-entry arrays
# against 255-entry callers.  Make that configuration dependency explicit.
$(JO_ENGINE_SRC_DIR)/sprites.o $(JO_ENGINE_SRC_DIR)/3d.o: makefile

include $(COMPILER_DIR)/COMMON/jo_engine_makefile

# Jo Engine's bundled make rules do not emit C header dependencies. Keep the
# executable contract identity and generated Round 1 fixture from remaining
# stale when SPEC-02 is deterministically regenerated.
main.o: src/port_v2/gameplay/round1/round1.h
src/port_v2/gameplay/round1/round1.o: \
	src/port_v2/gameplay/round1/round1.h \
	src/port_v2/gameplay/round1/spec02_round1_entry_data.h

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
