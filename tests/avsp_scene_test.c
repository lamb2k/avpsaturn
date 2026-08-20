/* Host tests for the AvspSceneDef v0 contract (RP1).
 *
 * Positive: a well-formed envelope with one record of every v0 operation
 * validates, and a legal route table initializes and follows its declared
 * transition edge.
 *
 * Negative controls, each of which must fail with its exact diagnostic:
 * truncated header, truncated payload, wrong magic, wrong schema version,
 * invalid scene ID zero, unknown opcode, record length below the opcode's
 * minimum, unclaimed trailing payload, unknown-scene lookup, a route table
 * with a dangling finish edge, and a player transition that disagrees with
 * the route table.
 */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "../avsp_scene.h"
#include "../avsp_scene_player.h"

static unsigned char buffer[512];
static unsigned long buffer_words;

static void put_word(const unsigned short value)
{
    buffer[buffer_words * 2] = (unsigned char)(value >> 8);
    buffer[buffer_words * 2 + 1] = (unsigned char)(value & 0xFF);
    ++buffer_words;
}

static void begin_envelope(const unsigned short magic,
                           const unsigned short version,
                           const unsigned short scene_id)
{
    buffer_words = 0;
    put_word(magic);
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
                          const unsigned short length)
{
    unsigned short word;
    put_word(opcode);
    put_word(length);
    for (word = 0; word < length; ++word)
        put_word((unsigned short)(word + 1));
}

static void build_full_envelope(void)
{
    begin_envelope(AVSP_SCENE_MAGIC, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    put_operation(AVSP_SCENE_OP_HOLD, 2);
    put_operation(AVSP_SCENE_OP_LAYER_PAGE, 2);
    put_operation(AVSP_SCENE_OP_SCROLL, 3);
    put_operation(AVSP_SCENE_OP_PALETTE, 3);
    put_operation(AVSP_SCENE_OP_OBJECT_ADD, 6);
    put_operation(AVSP_SCENE_OP_OBJECT_UPDATE, 4);
    put_operation(AVSP_SCENE_OP_OBJECT_REMOVE, 1);
    put_operation(AVSP_SCENE_OP_MAP_PATCH, 5);
    put_operation(AVSP_SCENE_OP_AUDIO_EVENT, 2);
    put_operation(AVSP_SCENE_OP_TRANSITION, 2);
    finish_envelope(10);
}

/* Minimal scripted player for the route tests. */
static AvspSceneStep scripted_step_result;
static AvspSceneStep scripted_step(AvspScenePlayer *player,
                                   unsigned short input)
{
    (void)player;
    (void)input;
    return scripted_step_result;
}

int main(void)
{
    AvspSceneEnvelope envelope;
    AvspSceneDiagnostics diagnostics;
    AvspScenePlayer player;
    AvspRouteController controller;
    static const unsigned short known[] = {0x0001, 0x0002,
                                           AVSP_SCENE_ID_INVALID};
    static const AvspRouteEntry route[] = {
        {0, 0x0001, 0x0002, AVSP_SCENE_ID_INVALID},
        {1, 0x0002, 0x0001, AVSP_SCENE_ID_INVALID},
    };
    static const AvspRouteEntry dangling[] = {
        {0, 0x0001, 0x0003, AVSP_SCENE_ID_INVALID},
    };

    /* Check A: every v0 operation validates in one envelope. */
    build_full_envelope();
    assert(avsp_scene_validate(buffer, buffer_words * 2, &envelope) ==
           AVSP_SCENE_OK);
    assert(envelope.scene_id == 0x0001);
    assert(envelope.operation_count == 10);

    /* Check B: provisional IDs are legal envelope IDs. */
    begin_envelope(AVSP_SCENE_MAGIC, AVSP_SCENE_SCHEMA_VERSION,
                   (unsigned short)(AVSP_SCENE_ID_PROVISIONAL | 0x0123));
    put_operation(AVSP_SCENE_OP_HOLD, 2);
    finish_envelope(1);
    assert(avsp_scene_validate(buffer, buffer_words * 2, &envelope) ==
           AVSP_SCENE_OK);

    /* Negative controls: each must fail with its exact diagnostic. */
    build_full_envelope();
    assert(avsp_scene_validate(buffer, 8, &envelope) ==
           AVSP_SCENE_E_TRUNCATED);
    assert(avsp_scene_validate(buffer, buffer_words * 2 - 2, &envelope) ==
           AVSP_SCENE_E_TRUNCATED);

    begin_envelope(0x1234, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    put_operation(AVSP_SCENE_OP_HOLD, 2);
    finish_envelope(1);
    assert(avsp_scene_validate(buffer, buffer_words * 2, &envelope) ==
           AVSP_SCENE_E_BAD_MAGIC);

    begin_envelope(AVSP_SCENE_MAGIC, AVSP_SCENE_SCHEMA_VERSION + 1, 0x0001);
    put_operation(AVSP_SCENE_OP_HOLD, 2);
    finish_envelope(1);
    assert(avsp_scene_validate(buffer, buffer_words * 2, &envelope) ==
           AVSP_SCENE_E_BAD_VERSION);

    begin_envelope(AVSP_SCENE_MAGIC, AVSP_SCENE_SCHEMA_VERSION,
                   AVSP_SCENE_ID_INVALID);
    put_operation(AVSP_SCENE_OP_HOLD, 2);
    finish_envelope(1);
    assert(avsp_scene_validate(buffer, buffer_words * 2, &envelope) ==
           AVSP_SCENE_E_BAD_SCENE_ID);

    begin_envelope(AVSP_SCENE_MAGIC, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    put_operation((unsigned short)(AVSP_SCENE_OP_LAST + 1), 2);
    finish_envelope(1);
    assert(avsp_scene_validate(buffer, buffer_words * 2, &envelope) ==
           AVSP_SCENE_E_UNKNOWN_OP);

    begin_envelope(AVSP_SCENE_MAGIC, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    put_operation(AVSP_SCENE_OP_OBJECT_ADD, 5);
    finish_envelope(1);
    assert(avsp_scene_validate(buffer, buffer_words * 2, &envelope) ==
           AVSP_SCENE_E_BAD_LENGTH);

    begin_envelope(AVSP_SCENE_MAGIC, AVSP_SCENE_SCHEMA_VERSION, 0x0001);
    put_operation(AVSP_SCENE_OP_HOLD, 2);
    put_word(0);
    finish_envelope(1);
    assert(avsp_scene_validate(buffer, buffer_words * 2, &envelope) ==
           AVSP_SCENE_E_BAD_LENGTH);

    /* Unknown-scene policy. */
    assert(avsp_scene_lookup(0x0001, known) == AVSP_SCENE_OK);
    assert(avsp_scene_lookup(0x0777, known) == AVSP_SCENE_E_UNKNOWN_SCENE);
    assert(avsp_scene_lookup(AVSP_SCENE_ID_INVALID, known) ==
           AVSP_SCENE_E_BAD_SCENE_ID);

    /* Route controller: legal table steps its declared edge. */
    avsp_scene_diagnostics_init(&diagnostics);
    memset(&player, 0, sizeof(player));
    player.known_scene_ids = known;
    player.diagnostics = &diagnostics;
    player.step = scripted_step;
    assert(avsp_route_init(&controller, route, 2, &player, &diagnostics) ==
           AVSP_SCENE_OK);
    scripted_step_result.diagnostic = AVSP_SCENE_OK;
    scripted_step_result.scene_finished = 0;
    assert(avsp_route_step(&controller, 0) == AVSP_SCENE_OK);
    assert(controller.current == 0);
    scripted_step_result.scene_finished = 1;
    scripted_step_result.next_scene_id = 0x0002;
    assert(avsp_route_step(&controller, 0) == AVSP_SCENE_OK);
    assert(controller.current == 1);

    /* Route negative controls: a dangling finish edge fails at init, and
       a player transition that disagrees with the table fails at step. */
    assert(avsp_route_init(&controller, dangling, 1, &player,
                           &diagnostics) == AVSP_SCENE_E_UNKNOWN_SCENE);
    assert(avsp_route_init(&controller, route, 2, &player, &diagnostics) ==
           AVSP_SCENE_OK);
    scripted_step_result.scene_finished = 1;
    scripted_step_result.next_scene_id = 0x0777;
    assert(avsp_route_step(&controller, 0) == AVSP_SCENE_E_UNKNOWN_SCENE);
    assert(diagnostics.unknown_scene_requests == 1);
    assert(diagnostics.last_diagnostic == AVSP_SCENE_E_UNKNOWN_SCENE);

    printf("AvspSceneDef v0 contract tests passed "
           "(2 positive, 11 negative controls).\n");
    return 0;
}
