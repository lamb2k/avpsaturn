/* AvspScenePlayer and AvspRouteController interfaces (RP1 items 5-6).
 *
 * These are the versioned call contracts the RP3 scene runtime implements
 * and the RP8-RP10 batches program against. They are interfaces only: no
 * implementation ships in RP1. Every entry point returns an
 * avsp_scene.h diagnostic; a player must fail diagnostically on an
 * unknown scene or version, never skip.
 *
 * Lifetime contract, in call order:
 *   load     - stage the scene's bundle members into their recorded
 *              residences; legal only while data-track reads are allowed
 *              (never after the CDDA late-read lock);
 *   activate - commit VDP2/CRAM/VDP1 state for frame zero;
 *   step     - advance one frame with the masked player input; reports
 *              the transition target when the scene ends;
 *   draw     - emit this frame's VDP1 commands; never touches state;
 *   release  - return every allocation in reverse order of load.
 */
#ifndef AVSP_SCENE_PLAYER_H
#define AVSP_SCENE_PLAYER_H

#include "avsp_scene.h"

/* step() result: what the route controller must do next frame. */
typedef struct
{
    int diagnostic;                /* AVSP_SCENE_OK or first failure      */
    int scene_finished;            /* 1 when the transition op fired      */
    unsigned short next_scene_id;  /* valid only when scene_finished      */
    unsigned short accepted_input; /* input bits the scene consumed       */
} AvspSceneStep;

typedef struct AvspScenePlayer AvspScenePlayer;
struct AvspScenePlayer
{
    /* The implementation's known-scene table, AVSP_SCENE_ID_INVALID
       terminated; avsp_scene_lookup() runs against it in load(). */
    const unsigned short *known_scene_ids;
    AvspSceneDiagnostics *diagnostics;
    int (*load)(AvspScenePlayer *player, unsigned short scene_id);
    int (*activate)(AvspScenePlayer *player);
    AvspSceneStep (*step)(AvspScenePlayer *player, unsigned short input);
    int (*draw)(AvspScenePlayer *player);
    int (*release)(AvspScenePlayer *player);
    void *context;
};

/* AvspRouteController: an explicit state machine, never a script engine.
 * Each entry names one route state, the scene it plays, and the only
 * transitions that may leave it. The table is generated from measured
 * route evidence; unknown targets fail through avsp_scene_lookup(). */
typedef struct
{
    unsigned short route_state;
    unsigned short scene_id;
    unsigned short next_on_finish;   /* scene player transition target    */
    unsigned short next_on_start;    /* Start-press target, or invalid    */
} AvspRouteEntry;

typedef struct
{
    const AvspRouteEntry *entries;
    int entry_count;
    int current;                     /* index into entries                */
    AvspScenePlayer *player;
    AvspSceneDiagnostics *diagnostics;
} AvspRouteController;

/* Route stepping contract: resolve the current entry, run the player, and
 * follow exactly one transition edge. A finish target absent from the
 * entry table is AVSP_SCENE_E_UNKNOWN_SCENE, reported, never skipped. */
int avsp_route_init(AvspRouteController *controller,
                    const AvspRouteEntry *entries, int entry_count,
                    AvspScenePlayer *player,
                    AvspSceneDiagnostics *diagnostics);
int avsp_route_step(AvspRouteController *controller, unsigned short input);

#endif
