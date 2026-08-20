/* AvspSceneRuntime: the minimal v0 scene player (RP3).
 *
 * Executes exactly the AvspSceneDef v0 operation set against a backend of
 * platform seams, in record order. Between HOLD records, operations apply
 * on the frame the cursor reaches them; a HOLD consumes frames until its
 * duration elapses or a masked input bit is pressed (mask 0 = never
 * skippable, duration 0 = hold until masked input). TRANSITION finishes
 * the scene and names the next scene ID for the route controller.
 *
 * The backend isolates every side effect so the identical player logic
 * runs in the WSL host tests (recording backend) and on the SH-2 (Jo/SGL
 * backend, bound in a later package). Host-compilable C90, no Jo/SGL
 * dependencies here.
 *
 * Object model: fixed slots (AVSP_SCENE_MAX_OBJECTS). OBJECT_ADD claims a
 * slot; adding to a claimed slot, or updating/removing an unclaimed slot,
 * is a hard AVSP_SCENE_E_BAD_LENGTH-class defect reported through the
 * step diagnostic (a generated bundle must never rely on silent reuse).
 */
#ifndef AVSP_SCENE_RUNTIME_H
#define AVSP_SCENE_RUNTIME_H

#include "avsp_scene.h"
#include "avsp_scene_player.h"

#define AVSP_SCENE_MAX_OBJECTS 16

typedef struct
{
    int claimed;
    unsigned short cel_id;
    short x;
    short y;
    unsigned short subbank;
    unsigned short depth;
} AvspSceneObject;

/* Platform seams. Every callback returns 0 on success or a diagnostic.
 * draw_object is called once per claimed slot per frame by
 * avsp_scene_runtime_draw. */
typedef struct AvspSceneBackend AvspSceneBackend;
struct AvspSceneBackend
{
    int (*load_scene)(AvspSceneBackend *backend, unsigned short scene_id,
                      const unsigned char **data, unsigned long *bytes);
    int (*release_scene)(AvspSceneBackend *backend,
                         unsigned short scene_id);
    int (*layer_page)(AvspSceneBackend *backend, unsigned short layer,
                      unsigned short page_id);
    int (*scroll)(AvspSceneBackend *backend, unsigned short layer,
                  short x, short y);
    int (*palette)(AvspSceneBackend *backend, unsigned short first_entry,
                   unsigned short count, unsigned short payload_ref);
    int (*map_patch)(AvspSceneBackend *backend, unsigned short layer,
                     unsigned short cell_index, unsigned short count,
                     const unsigned short *cells);
    int (*audio_event)(AvspSceneBackend *backend, unsigned short channel,
                       unsigned short cue_id);
    int (*draw_object)(AvspSceneBackend *backend, unsigned short slot,
                       const AvspSceneObject *object);
    void *context;
};

typedef struct
{
    AvspScenePlayer player;        /* base interface; player.context = this */
    AvspSceneBackend *backend;
    AvspSceneEnvelope envelope;
    const unsigned char *data;     /* validated envelope bytes             */
    unsigned long cursor_words;    /* next record, relative to data        */
    unsigned long executed_operations;
    int loaded;
    int active;
    int hold_remaining;            /* frames left in the current HOLD;
                                      -1 = hold until masked input         */
    unsigned short hold_mask;
    AvspSceneObject objects[AVSP_SCENE_MAX_OBJECTS];
} AvspSceneRuntime;

/* Binds the function table and zeroes the state. The runtime's known-scene
 * table and diagnostics are wired through the embedded player struct. */
void avsp_scene_runtime_init(AvspSceneRuntime *runtime,
                             AvspSceneBackend *backend,
                             const unsigned short *known_scene_ids,
                             AvspSceneDiagnostics *diagnostics);

#endif
