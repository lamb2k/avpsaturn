/* Host tests for the RP3 minimal scene runtime.
 *
 * Positive: a synthetic scene exercising every v0 opcode plays end to end
 * against a recording backend with the exact expected side-effect log,
 * hold timing, and input skip; a two-scene route runs through
 * AvspRouteController with load/activate/release lifecycle at the
 * transition.
 *
 * Negative controls, each failing with its exact diagnostic: unknown
 * scene load, wrong schema version, truncated envelope, envelope whose
 * scene ID disagrees with the request, object-slot double add, update of
 * an unclaimed slot, map patch whose count disagrees with the record
 * length, zero-duration unskippable hold, and a scene that runs off the
 * end without a TRANSITION.
 */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "../avsp_scene_runtime.h"

/* --- envelope builder (mirrors avsp_scene_test.c) ---------------------- */

static unsigned char buffer_a[512];
static unsigned char buffer_b[512];
static unsigned char *buffer;
static unsigned long buffer_words;

static void put_word(const unsigned short value)
{
    buffer[buffer_words * 2] = (unsigned char)(value >> 8);
    buffer[buffer_words * 2 + 1] = (unsigned char)(value & 0xFF);
    ++buffer_words;
}

static void begin_envelope(unsigned char *target,
                           const unsigned short version,
                           const unsigned short scene_id)
{
    buffer = target;
    buffer_words = 0;
    put_word(AVSP_SCENE_MAGIC);
    put_word(version);
    put_word(scene_id);
    put_word(0xFFFF);
    put_word(0);
    put_word(0);
}

static void finish_envelope(const unsigned short operations)
{
    const unsigned short payload =
        (unsigned short)(buffer_words - AVSP_SCENE_HEADER_WORDS);
    buffer[8] = (unsigned char)(operations >> 8);
    buffer[9] = (unsigned char)(operations & 0xFF);
    buffer[10] = (unsigned char)(payload >> 8);
    buffer[11] = (unsigned char)(payload & 0xFF);
}

static void put_operation(const unsigned short opcode,
                          const unsigned short length,
                          const unsigned short *payload)
{
    unsigned short word;
    put_word(opcode);
    put_word(length);
    for (word = 0; word < length; ++word)
        put_word(payload[word]);
}

/* --- recording backend -------------------------------------------------- */

typedef struct
{
    unsigned char envelope_a_bytes;
    char log[64][64];
    int log_count;
    unsigned long bytes_a;
    unsigned long bytes_b;
} RecordingBackend;

static RecordingBackend record;

static void record_event(const char *text)
{
    assert(record.log_count < 64);
    strcpy(record.log[record.log_count++], text);
}

static int rb_load(AvspSceneBackend *backend, unsigned short scene_id,
                   const unsigned char **data, unsigned long *bytes)
{
    (void)backend;
    if (scene_id == 0x0001) { *data = buffer_a; *bytes = record.bytes_a; }
    else if (scene_id == 0x0002) { *data = buffer_b; *bytes = record.bytes_b; }
    else return AVSP_SCENE_E_UNKNOWN_SCENE;
    record_event(scene_id == 0x0001 ? "load 1" : "load 2");
    return AVSP_SCENE_OK;
}

static int rb_release(AvspSceneBackend *backend, unsigned short scene_id)
{
    char text[32];
    (void)backend;
    sprintf(text, "release %d", scene_id);
    record_event(text);
    return AVSP_SCENE_OK;
}

static int rb_layer_page(AvspSceneBackend *backend, unsigned short layer,
                         unsigned short page_id)
{
    char text[32];
    (void)backend;
    sprintf(text, "layer %d page %d", layer, page_id);
    record_event(text);
    return AVSP_SCENE_OK;
}

static int rb_scroll(AvspSceneBackend *backend, unsigned short layer,
                     short x, short y)
{
    char text[40];
    (void)backend;
    sprintf(text, "scroll %d %d %d", layer, x, y);
    record_event(text);
    return AVSP_SCENE_OK;
}

static int rb_palette(AvspSceneBackend *backend, unsigned short first,
                      unsigned short count, unsigned short payload_ref)
{
    char text[40];
    (void)backend;
    sprintf(text, "palette %d %d %d", first, count, payload_ref);
    record_event(text);
    return AVSP_SCENE_OK;
}

static int rb_map_patch(AvspSceneBackend *backend, unsigned short layer,
                        unsigned short cell_index, unsigned short count,
                        const unsigned short *cells)
{
    char text[48];
    (void)backend;
    sprintf(text, "map %d @%d n%d [%d %d]", layer, cell_index, count,
            cells[0], cells[count - 1]);
    record_event(text);
    return AVSP_SCENE_OK;
}

static int rb_audio(AvspSceneBackend *backend, unsigned short channel,
                    unsigned short cue_id)
{
    char text[32];
    (void)backend;
    sprintf(text, "audio %d %d", channel, cue_id);
    record_event(text);
    return AVSP_SCENE_OK;
}

static int rb_draw(AvspSceneBackend *backend, unsigned short slot,
                   const AvspSceneObject *object)
{
    char text[48];
    (void)backend;
    sprintf(text, "draw %d cel %d at %d %d", slot, object->cel_id,
            object->x, object->y);
    record_event(text);
    return AVSP_SCENE_OK;
}

static AvspSceneBackend backend = {
    rb_load, rb_release, rb_layer_page, rb_scroll, rb_palette,
    rb_map_patch, rb_audio, rb_draw, 0
};

/* --- scene content ------------------------------------------------------ */

static void build_scene_a(void)
{
    static const unsigned short layer[] = {1, 7};
    static const unsigned short scroll[] = {2, 0xFFF0, 8};   /* x = -16 */
    static const unsigned short palette[] = {32, 16, 3};
    static const unsigned short add[] = {2, 0x0123, 100, 60, 13, 60};
    static const unsigned short hold3[] = {3, 0};
    static const unsigned short update[] = {2, 104, 60, 0x0124};
    static const unsigned short map[] = {1, 40, 2, 0x0100, 0x0110};
    static const unsigned short audio[] = {0, 9};
    static const unsigned short hold_input[] = {0, 0x0002};
    static const unsigned short remove_[] = {2};
    static const unsigned short transition[] = {0x0002, 0};
    begin_envelope(buffer_a, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    put_operation(AVSP_SCENE_OP_LAYER_PAGE, 2, layer);
    put_operation(AVSP_SCENE_OP_SCROLL, 3, scroll);
    put_operation(AVSP_SCENE_OP_PALETTE, 3, palette);
    put_operation(AVSP_SCENE_OP_OBJECT_ADD, 6, add);
    put_operation(AVSP_SCENE_OP_HOLD, 2, hold3);
    put_operation(AVSP_SCENE_OP_OBJECT_UPDATE, 4, update);
    put_operation(AVSP_SCENE_OP_MAP_PATCH, 5, map);
    put_operation(AVSP_SCENE_OP_AUDIO_EVENT, 2, audio);
    put_operation(AVSP_SCENE_OP_HOLD, 2, hold_input);
    put_operation(AVSP_SCENE_OP_OBJECT_REMOVE, 1, remove_);
    put_operation(AVSP_SCENE_OP_TRANSITION, 2, transition);
    finish_envelope(11);
    record.bytes_a = buffer_words * 2;
}

static void build_scene_b(void)
{
    static const unsigned short hold1[] = {1, 0};
    static const unsigned short transition[] = {0x0001, 0};
    begin_envelope(buffer_b, AVSP_SCENE_SCHEMA_VERSION, 0x0002);
    put_operation(AVSP_SCENE_OP_HOLD, 2, hold1);
    put_operation(AVSP_SCENE_OP_TRANSITION, 2, transition);
    finish_envelope(2);
    record.bytes_b = buffer_words * 2;
}

/* --- helpers ------------------------------------------------------------ */

static AvspSceneStep step_ok(AvspSceneRuntime *runtime,
                             unsigned short input)
{
    AvspSceneStep step = runtime->player.step(&runtime->player, input);
    assert(step.diagnostic == AVSP_SCENE_OK);
    return step;
}

int main(void)
{
    static const unsigned short known[] = {0x0001, 0x0002,
                                           AVSP_SCENE_ID_INVALID};
    static const AvspRouteEntry route[] = {
        {0, 0x0001, 0x0002, AVSP_SCENE_ID_INVALID},
        {1, 0x0002, 0x0001, AVSP_SCENE_ID_INVALID},
    };
    AvspSceneDiagnostics diagnostics;
    AvspSceneRuntime runtime;
    AvspRouteController controller;
    AvspSceneStep step;
    int frame;
    int negative_controls = 0;

    build_scene_a();
    build_scene_b();

    /* --- positive: full opcode playback with exact side-effect log --- */
    avsp_scene_diagnostics_init(&diagnostics);
    avsp_scene_runtime_init(&runtime, &backend, known, &diagnostics);
    record.log_count = 0;

    assert(runtime.player.load(&runtime.player, 0x0001) == AVSP_SCENE_OK);
    assert(runtime.player.activate(&runtime.player) == AVSP_SCENE_OK);

    /* Frame 1 runs the setup block and enters the 3-frame hold. */
    step = step_ok(&runtime, 0);
    assert(!step.scene_finished);
    assert(runtime.hold_remaining == 2);
    assert(runtime.player.draw(&runtime.player) == AVSP_SCENE_OK);
    /* Frames 2-3 are held; input is ignored (mask 0). */
    step_ok(&runtime, 0xFFFF);
    step_ok(&runtime, 0);
    /* Frame 4 runs update/map/audio and enters the input-gated hold. */
    step = step_ok(&runtime, 0);
    assert(runtime.hold_remaining == -1);
    assert(runtime.player.draw(&runtime.player) == AVSP_SCENE_OK);
    /* Held until the masked bit arrives; wrong bits do not release it. */
    step = step_ok(&runtime, 0x0004);
    assert(!step.scene_finished && runtime.hold_remaining == -1);
    step = step_ok(&runtime, 0x0002);
    assert(step.accepted_input == 0x0002);
    assert(step.scene_finished && step.next_scene_id == 0x0002);

    {
        static const char *expected[] = {
            "load 1",
            "layer 1 page 7",
            "scroll 2 -16 8",
            "palette 32 16 3",
            "draw 2 cel 291 at 100 60",
            "map 1 @40 n2 [256 272]",
            "audio 0 9",
            "draw 2 cel 292 at 104 60",
        };
        int index;
        assert(record.log_count == 8);
        for (index = 0; index < 8; ++index)
            assert(strcmp(record.log[index], expected[index]) == 0);
    }
    assert(diagnostics.envelopes_validated == 1);
    assert(diagnostics.validation_failures == 0);

    /* --- positive: two-scene route with lifecycle at the transition --- */
    avsp_scene_diagnostics_init(&diagnostics);
    avsp_scene_runtime_init(&runtime, &backend, known, &diagnostics);
    record.log_count = 0;
    assert(avsp_route_init(&controller, route, 2, &runtime.player,
                           &diagnostics) == AVSP_SCENE_OK);
    assert(runtime.player.load(&runtime.player, 0x0001) == AVSP_SCENE_OK);
    assert(runtime.player.activate(&runtime.player) == AVSP_SCENE_OK);
    for (frame = 0; frame < 4; ++frame)
        assert(avsp_route_step(&controller, 0) == AVSP_SCENE_OK);
    assert(controller.current == 0);
    assert(avsp_route_step(&controller, 0x0002) == AVSP_SCENE_OK);
    assert(controller.current == 1);
    assert(runtime.player.release(&runtime.player) == AVSP_SCENE_OK);
    assert(runtime.player.load(&runtime.player, 0x0002) == AVSP_SCENE_OK);
    assert(runtime.player.activate(&runtime.player) == AVSP_SCENE_OK);
    assert(avsp_route_step(&controller, 0) == AVSP_SCENE_OK);
    step = runtime.player.step(&runtime.player, 0);
    assert(step.scene_finished && step.next_scene_id == 0x0001);

    /* --- negative controls -------------------------------------------- */

    avsp_scene_diagnostics_init(&diagnostics);
    avsp_scene_runtime_init(&runtime, &backend, known, &diagnostics);

    /* Unknown scene load. */
    assert(runtime.player.load(&runtime.player, 0x0777) ==
           AVSP_SCENE_E_UNKNOWN_SCENE);
    assert(diagnostics.unknown_scene_requests == 1);
    ++negative_controls;

    /* Wrong schema version. */
    begin_envelope(buffer_a, AVSP_SCENE_SCHEMA_VERSION + 1, 0x0001);
    {
        static const unsigned short hold1[] = {1, 0};
        put_operation(AVSP_SCENE_OP_HOLD, 2, hold1);
    }
    finish_envelope(1);
    record.bytes_a = buffer_words * 2;
    assert(runtime.player.load(&runtime.player, 0x0001) ==
           AVSP_SCENE_E_BAD_VERSION);
    ++negative_controls;

    /* Truncated envelope. */
    build_scene_a();
    record.bytes_a -= 2;
    assert(runtime.player.load(&runtime.player, 0x0001) ==
           AVSP_SCENE_E_TRUNCATED);
    ++negative_controls;

    /* Envelope scene ID disagrees with the requested ID. */
    build_scene_a();
    buffer_a[5] = 0x02;
    assert(runtime.player.load(&runtime.player, 0x0001) ==
           AVSP_SCENE_E_BAD_SCENE_ID);
    ++negative_controls;

    /* Object-slot double add. */
    begin_envelope(buffer_a, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    {
        static const unsigned short add[] = {2, 1, 0, 0, 0, 0};
        static const unsigned short transition[] = {0x0002, 0};
        put_operation(AVSP_SCENE_OP_OBJECT_ADD, 6, add);
        put_operation(AVSP_SCENE_OP_OBJECT_ADD, 6, add);
        put_operation(AVSP_SCENE_OP_TRANSITION, 2, transition);
        finish_envelope(3);
    }
    record.bytes_a = buffer_words * 2;
    assert(runtime.player.load(&runtime.player, 0x0001) == AVSP_SCENE_OK);
    assert(runtime.player.activate(&runtime.player) == AVSP_SCENE_OK);
    step = runtime.player.step(&runtime.player, 0);
    assert(step.diagnostic == AVSP_SCENE_E_BAD_LENGTH);
    ++negative_controls;

    /* Update of an unclaimed slot. */
    begin_envelope(buffer_a, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    {
        static const unsigned short update[] = {5, 0, 0, 0};
        static const unsigned short transition[] = {0x0002, 0};
        put_operation(AVSP_SCENE_OP_OBJECT_UPDATE, 4, update);
        put_operation(AVSP_SCENE_OP_TRANSITION, 2, transition);
        finish_envelope(2);
    }
    record.bytes_a = buffer_words * 2;
    assert(runtime.player.load(&runtime.player, 0x0001) == AVSP_SCENE_OK);
    assert(runtime.player.activate(&runtime.player) == AVSP_SCENE_OK);
    step = runtime.player.step(&runtime.player, 0);
    assert(step.diagnostic == AVSP_SCENE_E_BAD_LENGTH);
    ++negative_controls;

    /* Map patch whose count disagrees with the record length. */
    begin_envelope(buffer_a, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    {
        static const unsigned short map[] = {1, 40, 3, 0x0100, 0x0110};
        static const unsigned short transition[] = {0x0002, 0};
        put_operation(AVSP_SCENE_OP_MAP_PATCH, 5, map);
        put_operation(AVSP_SCENE_OP_TRANSITION, 2, transition);
        finish_envelope(2);
    }
    record.bytes_a = buffer_words * 2;
    assert(runtime.player.load(&runtime.player, 0x0001) == AVSP_SCENE_OK);
    assert(runtime.player.activate(&runtime.player) == AVSP_SCENE_OK);
    step = runtime.player.step(&runtime.player, 0);
    assert(step.diagnostic == AVSP_SCENE_E_BAD_LENGTH);
    ++negative_controls;

    /* Zero-duration unskippable hold. */
    begin_envelope(buffer_a, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    {
        static const unsigned short hold[] = {0, 0};
        static const unsigned short transition[] = {0x0002, 0};
        put_operation(AVSP_SCENE_OP_HOLD, 2, hold);
        put_operation(AVSP_SCENE_OP_TRANSITION, 2, transition);
        finish_envelope(2);
    }
    record.bytes_a = buffer_words * 2;
    assert(runtime.player.load(&runtime.player, 0x0001) == AVSP_SCENE_OK);
    assert(runtime.player.activate(&runtime.player) == AVSP_SCENE_OK);
    step = runtime.player.step(&runtime.player, 0);
    assert(step.diagnostic == AVSP_SCENE_E_BAD_LENGTH);
    ++negative_controls;

    /* Running off the end without a TRANSITION. */
    begin_envelope(buffer_a, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    {
        static const unsigned short hold1[] = {1, 0};
        put_operation(AVSP_SCENE_OP_HOLD, 2, hold1);
        finish_envelope(1);
    }
    record.bytes_a = buffer_words * 2;
    assert(runtime.player.load(&runtime.player, 0x0001) == AVSP_SCENE_OK);
    assert(runtime.player.activate(&runtime.player) == AVSP_SCENE_OK);
    step = runtime.player.step(&runtime.player, 0);
    assert(step.diagnostic == AVSP_SCENE_OK);
    step = runtime.player.step(&runtime.player, 0);
    assert(step.diagnostic == AVSP_SCENE_E_TRUNCATED);
    ++negative_controls;

    printf("AvspSceneRuntime v0 player tests passed "
           "(3 positive blocks, %d negative controls).\n",
           negative_controls);
    return 0;
}
