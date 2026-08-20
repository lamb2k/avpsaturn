/* AvspSceneDef v0: the versioned scene-definition contract (RP1).
 *
 * This header is the ownership boundary between the capture/conversion
 * pipeline (RP2), the scene runtime (RP3), and the stage renderer (RP4).
 * It defines the envelope, the scene-ID namespace, the v0 operation set,
 * and the diagnostic results. It deliberately contains no scene content
 * and no rendering: RP2 evidence finalizes the semantic scene list in RP6.
 *
 * Versioning rule: operations are additive within the v0 envelope. Any
 * incompatible change increments AVSP_SCENE_SCHEMA_VERSION and requires a
 * migration check; a player must refuse an envelope whose version it does
 * not implement rather than guess.
 *
 * Unknown-scene rule: an unknown or unimplemented scene ID is a hard
 * diagnostic failure (AVSP_SCENE_E_UNKNOWN_SCENE). It is never skipped and
 * never coerced to a nearby scene.
 *
 * The encoding is big-endian 16-bit words, matching the Saturn's byte
 * order, so a generated bundle member can be validated byte-identically on
 * the host and on target. Host-compilable: no Jo/SGL dependencies.
 */
#ifndef AVSP_SCENE_H
#define AVSP_SCENE_H

/* Envelope magic "SD" and schema version. */
#define AVSP_SCENE_MAGIC 0x5344
#define AVSP_SCENE_SCHEMA_VERSION 0

/* Scene-ID namespace: 16 bits. Bit 15 marks a PROVISIONAL ID assigned by
 * the RP2 automatic grouping; RP6 replaces provisional IDs with final
 * stable IDs. Zero is reserved and always invalid. */
#define AVSP_SCENE_ID_PROVISIONAL 0x8000
#define AVSP_SCENE_ID_VALUE_MASK 0x7FFF
#define AVSP_SCENE_ID_INVALID 0

/* The v0 operation set: only evidence-backed operations (RP3). Each
 * operation record is its opcode word, a length word counting the payload
 * words that follow, then the payload. The length word makes every record
 * skippable, so ADDING an opcode is compatible while REDEFINING one is
 * not. */
enum
{
    AVSP_SCENE_OP_HOLD = 1,        /* duration frames, input mask         */
    AVSP_SCENE_OP_LAYER_PAGE = 2,  /* layer, page id                      */
    AVSP_SCENE_OP_SCROLL = 3,      /* layer, x, y (signed)                */
    AVSP_SCENE_OP_PALETTE = 4,     /* first entry, count, payload ref     */
    AVSP_SCENE_OP_OBJECT_ADD = 5,  /* slot, cel id, x, y, subbank, depth  */
    AVSP_SCENE_OP_OBJECT_UPDATE = 6, /* slot, x, y, cel id                */
    AVSP_SCENE_OP_OBJECT_REMOVE = 7, /* slot                              */
    AVSP_SCENE_OP_MAP_PATCH = 8,   /* layer, cell index, count, cells...  */
    AVSP_SCENE_OP_AUDIO_EVENT = 9, /* channel, cue id                     */
    AVSP_SCENE_OP_TRANSITION = 10, /* next scene id, entry frame          */
    AVSP_SCENE_OP_LAST = AVSP_SCENE_OP_TRANSITION
};

/* Validation and player diagnostics. Zero is success; every failure names
 * the first defect so a broken bundle is diagnosable, never skippable. */
enum
{
    AVSP_SCENE_OK = 0,
    AVSP_SCENE_E_BAD_MAGIC = 1,
    AVSP_SCENE_E_BAD_VERSION = 2,
    AVSP_SCENE_E_TRUNCATED = 3,
    AVSP_SCENE_E_BAD_SCENE_ID = 4,
    AVSP_SCENE_E_UNKNOWN_OP = 5,
    AVSP_SCENE_E_BAD_LENGTH = 6,
    AVSP_SCENE_E_UNKNOWN_SCENE = 7
};

/* Envelope header, as validated words in file order:
 * word 0 magic, word 1 schema version, word 2 scene id, word 3 source
 * anchor (first source frame, for evidence joins; 0xFFFF if none), word 4
 * operation count, word 5 total payload words after the header. */
#define AVSP_SCENE_HEADER_WORDS 6

typedef struct
{
    unsigned short magic;
    unsigned short version;
    unsigned short scene_id;
    unsigned short source_anchor;
    unsigned short operation_count;
    unsigned short payload_words;
} AvspSceneEnvelope;

/* Decode and validate one envelope from big-endian bytes. On success the
 * envelope is filled in and AVSP_SCENE_OK is returned; otherwise the first
 * diagnostic failure is returned and the envelope must not be used. The
 * operation stream is walked completely, so a truncated record, a zero or
 * unknown opcode, or a length overrunning the payload all fail here rather
 * than inside a player. */
int avsp_scene_validate(const unsigned char *data, unsigned long bytes,
                        AvspSceneEnvelope *envelope);

/* The unknown-scene policy, in one place: a player asked for a scene ID it
 * does not implement must call this and propagate the failure. `known_ids`
 * is the player's table, terminated by AVSP_SCENE_ID_INVALID. */
int avsp_scene_lookup(unsigned short scene_id,
                      const unsigned short *known_ids);

/* Presentation diagnostic and variance interface (RP1 item 7): every
 * runtime comparison against source evidence lands in one of these
 * counters, and a variance is either explained (bounded, on record) or a
 * failure - there is no silent third state. */
typedef struct
{
    int envelopes_validated;
    int validation_failures;
    int unknown_scene_requests;
    int explained_variances;
    int unexplained_variances;
    int last_diagnostic;
} AvspSceneDiagnostics;

void avsp_scene_diagnostics_init(AvspSceneDiagnostics *diagnostics);

#endif
