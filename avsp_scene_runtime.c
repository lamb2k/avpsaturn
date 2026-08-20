/* AvspSceneRuntime implementation (RP3). See avsp_scene_runtime.h.
 * Host-compilable C90; every side effect goes through the backend seams so
 * the identical interpreter runs in host tests and on the SH-2. */
#include "avsp_scene_runtime.h"

static unsigned short runtime_word(const AvspSceneRuntime *runtime,
                                   unsigned long word_offset)
{
    const unsigned char *at = runtime->data + word_offset * 2;
    return (unsigned short)((at[0] << 8) | at[1]);
}

static int runtime_fail(AvspSceneRuntime *runtime, int diagnostic)
{
    ++runtime->player.diagnostics->validation_failures;
    runtime->player.diagnostics->last_diagnostic = diagnostic;
    return diagnostic;
}

/* --- player interface ------------------------------------------------- */

static int runtime_load(AvspScenePlayer *player, unsigned short scene_id)
{
    AvspSceneRuntime *runtime = (AvspSceneRuntime *)player->context;
    const unsigned char *data;
    unsigned long bytes;
    int diagnostic;

    diagnostic = avsp_scene_lookup(scene_id, player->known_scene_ids);
    if (diagnostic != AVSP_SCENE_OK)
    {
        ++player->diagnostics->unknown_scene_requests;
        player->diagnostics->last_diagnostic = diagnostic;
        return diagnostic;
    }
    diagnostic = runtime->backend->load_scene(runtime->backend, scene_id,
                                              &data, &bytes);
    if (diagnostic != AVSP_SCENE_OK)
        return runtime_fail(runtime, diagnostic);
    diagnostic = avsp_scene_validate(data, bytes, &runtime->envelope);
    if (diagnostic != AVSP_SCENE_OK)
        return runtime_fail(runtime, diagnostic);
    if (runtime->envelope.scene_id != scene_id)
        return runtime_fail(runtime, AVSP_SCENE_E_BAD_SCENE_ID);
    ++player->diagnostics->envelopes_validated;
    runtime->data = data;
    runtime->loaded = 1;
    runtime->active = 0;
    return AVSP_SCENE_OK;
}

static void runtime_reset_frame_state(AvspSceneRuntime *runtime)
{
    int slot;
    runtime->cursor_words = AVSP_SCENE_HEADER_WORDS;
    runtime->executed_operations = 0;
    runtime->hold_remaining = 0;
    runtime->hold_mask = 0;
    for (slot = 0; slot < AVSP_SCENE_MAX_OBJECTS; ++slot)
        runtime->objects[slot].claimed = 0;
}

static int runtime_activate(AvspScenePlayer *player)
{
    AvspSceneRuntime *runtime = (AvspSceneRuntime *)player->context;
    if (!runtime->loaded)
        return runtime_fail(runtime, AVSP_SCENE_E_TRUNCATED);
    runtime_reset_frame_state(runtime);
    runtime->active = 1;
    return AVSP_SCENE_OK;
}

/* Executes one operation record at the cursor. Returns AVSP_SCENE_OK and
 * advances, or a diagnostic. HOLD and TRANSITION are handled by step(). */
static int runtime_apply(AvspSceneRuntime *runtime, int opcode,
                         unsigned short length, unsigned long payload)
{
    AvspSceneBackend *backend = runtime->backend;
    unsigned short slot;
    int diagnostic = AVSP_SCENE_OK;

    switch (opcode)
    {
    case AVSP_SCENE_OP_LAYER_PAGE:
        diagnostic = backend->layer_page(backend,
                                         runtime_word(runtime, payload),
                                         runtime_word(runtime, payload + 1));
        break;
    case AVSP_SCENE_OP_SCROLL:
        diagnostic = backend->scroll(backend,
                                     runtime_word(runtime, payload),
                                     (short)runtime_word(runtime, payload + 1),
                                     (short)runtime_word(runtime, payload + 2));
        break;
    case AVSP_SCENE_OP_PALETTE:
        diagnostic = backend->palette(backend,
                                      runtime_word(runtime, payload),
                                      runtime_word(runtime, payload + 1),
                                      runtime_word(runtime, payload + 2));
        break;
    case AVSP_SCENE_OP_OBJECT_ADD:
        slot = runtime_word(runtime, payload);
        if (slot >= AVSP_SCENE_MAX_OBJECTS ||
            runtime->objects[slot].claimed)
            return AVSP_SCENE_E_BAD_LENGTH;
        runtime->objects[slot].claimed = 1;
        runtime->objects[slot].cel_id = runtime_word(runtime, payload + 1);
        runtime->objects[slot].x = (short)runtime_word(runtime, payload + 2);
        runtime->objects[slot].y = (short)runtime_word(runtime, payload + 3);
        runtime->objects[slot].subbank = runtime_word(runtime, payload + 4);
        runtime->objects[slot].depth = runtime_word(runtime, payload + 5);
        break;
    case AVSP_SCENE_OP_OBJECT_UPDATE:
        slot = runtime_word(runtime, payload);
        if (slot >= AVSP_SCENE_MAX_OBJECTS ||
            !runtime->objects[slot].claimed)
            return AVSP_SCENE_E_BAD_LENGTH;
        runtime->objects[slot].x = (short)runtime_word(runtime, payload + 1);
        runtime->objects[slot].y = (short)runtime_word(runtime, payload + 2);
        runtime->objects[slot].cel_id = runtime_word(runtime, payload + 3);
        break;
    case AVSP_SCENE_OP_OBJECT_REMOVE:
        slot = runtime_word(runtime, payload);
        if (slot >= AVSP_SCENE_MAX_OBJECTS ||
            !runtime->objects[slot].claimed)
            return AVSP_SCENE_E_BAD_LENGTH;
        runtime->objects[slot].claimed = 0;
        break;
    case AVSP_SCENE_OP_MAP_PATCH:
    {
        unsigned short count = runtime_word(runtime, payload + 2);
        unsigned short cells[32];
        unsigned short cell;
        if (count > 32 || (unsigned long)count + 3 != length)
            return AVSP_SCENE_E_BAD_LENGTH;
        for (cell = 0; cell < count; ++cell)
            cells[cell] = runtime_word(runtime, payload + 3 + cell);
        diagnostic = backend->map_patch(backend,
                                        runtime_word(runtime, payload),
                                        runtime_word(runtime, payload + 1),
                                        count, cells);
        break;
    }
    case AVSP_SCENE_OP_AUDIO_EVENT:
        diagnostic = backend->audio_event(backend,
                                          runtime_word(runtime, payload),
                                          runtime_word(runtime, payload + 1));
        break;
    default:
        return AVSP_SCENE_E_UNKNOWN_OP;
    }
    return diagnostic;
}

static AvspSceneStep runtime_step(AvspScenePlayer *player,
                                  unsigned short input)
{
    AvspSceneRuntime *runtime = (AvspSceneRuntime *)player->context;
    AvspSceneStep step;
    unsigned long end_words;

    step.diagnostic = AVSP_SCENE_OK;
    step.scene_finished = 0;
    step.next_scene_id = AVSP_SCENE_ID_INVALID;
    step.accepted_input = 0;

    if (!runtime->active)
    {
        step.diagnostic = runtime_fail(runtime, AVSP_SCENE_E_TRUNCATED);
        return step;
    }

    /* A pending HOLD consumes this frame unless a masked input ends it. */
    if (runtime->hold_remaining != 0)
    {
        if (runtime->hold_mask && (input & runtime->hold_mask))
        {
            step.accepted_input = (unsigned short)(input & runtime->hold_mask);
            runtime->hold_remaining = 0;
        }
        else
        {
            if (runtime->hold_remaining > 0)
                --runtime->hold_remaining;
            return step;
        }
    }

    /* Run records until the next HOLD consumes the frame or TRANSITION
     * finishes the scene. Envelope validation already proved the record
     * walk, so running off the end means the bundle lacked a TRANSITION:
     * a hard defect, never a silent loop. */
    end_words = (unsigned long)AVSP_SCENE_HEADER_WORDS +
        runtime->envelope.payload_words;
    while (runtime->cursor_words < end_words)
    {
        int opcode = runtime_word(runtime, runtime->cursor_words);
        unsigned short length =
            runtime_word(runtime, runtime->cursor_words + 1);
        unsigned long payload = runtime->cursor_words + 2;
        runtime->cursor_words += 2ul + length;
        ++runtime->executed_operations;

        if (opcode == AVSP_SCENE_OP_HOLD)
        {
            unsigned short duration = runtime_word(runtime, payload);
            runtime->hold_mask = runtime_word(runtime, payload + 1);
            if (duration == 0 && runtime->hold_mask == 0)
            {
                /* A zero-duration, unskippable hold would never end. */
                step.diagnostic =
                    runtime_fail(runtime, AVSP_SCENE_E_BAD_LENGTH);
                return step;
            }
            runtime->hold_remaining = duration == 0 ? -1 : (int)duration - 1;
            return step;
        }
        if (opcode == AVSP_SCENE_OP_TRANSITION)
        {
            step.scene_finished = 1;
            step.next_scene_id = runtime_word(runtime, payload);
            runtime->active = 0;
            return step;
        }
        step.diagnostic = runtime_apply(runtime, opcode, length, payload);
        if (step.diagnostic != AVSP_SCENE_OK)
        {
            runtime_fail(runtime, step.diagnostic);
            return step;
        }
    }
    step.diagnostic = runtime_fail(runtime, AVSP_SCENE_E_TRUNCATED);
    return step;
}

static int runtime_draw(AvspScenePlayer *player)
{
    AvspSceneRuntime *runtime = (AvspSceneRuntime *)player->context;
    int slot;
    int diagnostic;
    if (!runtime->active && !runtime->loaded)
        return runtime_fail(runtime, AVSP_SCENE_E_TRUNCATED);
    for (slot = 0; slot < AVSP_SCENE_MAX_OBJECTS; ++slot)
    {
        if (!runtime->objects[slot].claimed) continue;
        diagnostic = runtime->backend->draw_object(
            runtime->backend, (unsigned short)slot,
            &runtime->objects[slot]);
        if (diagnostic != AVSP_SCENE_OK)
            return runtime_fail(runtime, diagnostic);
    }
    return AVSP_SCENE_OK;
}

static int runtime_release(AvspScenePlayer *player)
{
    AvspSceneRuntime *runtime = (AvspSceneRuntime *)player->context;
    int diagnostic = AVSP_SCENE_OK;
    if (runtime->loaded)
        diagnostic = runtime->backend->release_scene(
            runtime->backend, runtime->envelope.scene_id);
    runtime->loaded = 0;
    runtime->active = 0;
    runtime->data = 0;
    return diagnostic;
}

void avsp_scene_runtime_init(AvspSceneRuntime *runtime,
                             AvspSceneBackend *backend,
                             const unsigned short *known_scene_ids,
                             AvspSceneDiagnostics *diagnostics)
{
    int slot;
    runtime->backend = backend;
    runtime->data = 0;
    runtime->loaded = 0;
    runtime->active = 0;
    runtime->cursor_words = 0;
    runtime->executed_operations = 0;
    runtime->hold_remaining = 0;
    runtime->hold_mask = 0;
    for (slot = 0; slot < AVSP_SCENE_MAX_OBJECTS; ++slot)
        runtime->objects[slot].claimed = 0;
    runtime->player.known_scene_ids = known_scene_ids;
    runtime->player.diagnostics = diagnostics;
    runtime->player.load = runtime_load;
    runtime->player.activate = runtime_activate;
    runtime->player.step = runtime_step;
    runtime->player.draw = runtime_draw;
    runtime->player.release = runtime_release;
    runtime->player.context = runtime;
}
