/* AvspSceneDef v0 envelope validation. See avsp_scene.h for the contract.
 * Host-compilable C90 with no Jo/SGL dependencies, so the same validation
 * runs in the host tests and on the SH-2. */
#include "avsp_scene.h"

static unsigned short read_word(const unsigned char *data)
{
    return (unsigned short)((data[0] << 8) | data[1]);
}

/* Payload words each v0 opcode requires; 0 means variable (the record's
 * length word is authoritative but must still be at least the minimum). */
static int operation_minimum_words(const int opcode)
{
    switch (opcode)
    {
    case AVSP_SCENE_OP_HOLD: return 2;
    case AVSP_SCENE_OP_LAYER_PAGE: return 2;
    case AVSP_SCENE_OP_SCROLL: return 3;
    case AVSP_SCENE_OP_PALETTE: return 3;
    case AVSP_SCENE_OP_OBJECT_ADD: return 6;
    case AVSP_SCENE_OP_OBJECT_UPDATE: return 4;
    case AVSP_SCENE_OP_OBJECT_REMOVE: return 1;
    case AVSP_SCENE_OP_MAP_PATCH: return 3;
    case AVSP_SCENE_OP_AUDIO_EVENT: return 2;
    case AVSP_SCENE_OP_TRANSITION: return 2;
    default: return -1;
    }
}

int avsp_scene_validate(const unsigned char *data, unsigned long bytes,
                        AvspSceneEnvelope *envelope)
{
    unsigned long words = bytes / 2;
    unsigned long offset;
    unsigned long remaining;
    int operations;

    if (data == 0 || envelope == 0) return AVSP_SCENE_E_TRUNCATED;
    if (words < AVSP_SCENE_HEADER_WORDS) return AVSP_SCENE_E_TRUNCATED;
    envelope->magic = read_word(data);
    envelope->version = read_word(data + 2);
    envelope->scene_id = read_word(data + 4);
    envelope->source_anchor = read_word(data + 6);
    envelope->operation_count = read_word(data + 8);
    envelope->payload_words = read_word(data + 10);
    if (envelope->magic != AVSP_SCENE_MAGIC) return AVSP_SCENE_E_BAD_MAGIC;
    if (envelope->version != AVSP_SCENE_SCHEMA_VERSION)
        return AVSP_SCENE_E_BAD_VERSION;
    if ((envelope->scene_id & AVSP_SCENE_ID_VALUE_MASK) ==
            AVSP_SCENE_ID_INVALID)
        return AVSP_SCENE_E_BAD_SCENE_ID;
    if (words < (unsigned long)AVSP_SCENE_HEADER_WORDS +
            envelope->payload_words)
        return AVSP_SCENE_E_TRUNCATED;

    /* Walk every operation record: opcode word, length word, payload. */
    offset = AVSP_SCENE_HEADER_WORDS;
    remaining = envelope->payload_words;
    for (operations = 0; operations < envelope->operation_count;
         ++operations)
    {
        int opcode;
        int minimum;
        unsigned short length;
        if (remaining < 2) return AVSP_SCENE_E_TRUNCATED;
        opcode = read_word(data + offset * 2);
        length = read_word(data + offset * 2 + 2);
        minimum = operation_minimum_words(opcode);
        if (minimum < 0) return AVSP_SCENE_E_UNKNOWN_OP;
        if (length < (unsigned short)minimum) return AVSP_SCENE_E_BAD_LENGTH;
        if (remaining < 2ul + length) return AVSP_SCENE_E_TRUNCATED;
        offset += 2ul + length;
        remaining -= 2ul + length;
    }
    /* Trailing unclaimed payload is a defect, not padding: a generator
       that miscounts must fail here rather than ship dead words. */
    if (remaining != 0) return AVSP_SCENE_E_BAD_LENGTH;
    return AVSP_SCENE_OK;
}

int avsp_scene_lookup(unsigned short scene_id,
                      const unsigned short *known_ids)
{
    if ((scene_id & AVSP_SCENE_ID_VALUE_MASK) == AVSP_SCENE_ID_INVALID)
        return AVSP_SCENE_E_BAD_SCENE_ID;
    if (known_ids != 0)
        for (; *known_ids != AVSP_SCENE_ID_INVALID; ++known_ids)
            if (*known_ids == scene_id) return AVSP_SCENE_OK;
    return AVSP_SCENE_E_UNKNOWN_SCENE;
}

void avsp_scene_diagnostics_init(AvspSceneDiagnostics *diagnostics)
{
    diagnostics->envelopes_validated = 0;
    diagnostics->validation_failures = 0;
    diagnostics->unknown_scene_requests = 0;
    diagnostics->explained_variances = 0;
    diagnostics->unexplained_variances = 0;
    diagnostics->last_diagnostic = AVSP_SCENE_OK;
}
