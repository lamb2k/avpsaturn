/* AvspRouteController: explicit state-machine stepping (RP1 item 6).
 * Host-compilable C90; the route table itself is generated from measured
 * evidence in later packages. */
#include "avsp_scene_player.h"

static int route_find_scene(const AvspRouteController *controller,
                            const unsigned short scene_id)
{
    int index;
    for (index = 0; index < controller->entry_count; ++index)
        if (controller->entries[index].scene_id == scene_id) return index;
    return -1;
}

int avsp_route_init(AvspRouteController *controller,
                    const AvspRouteEntry *entries, int entry_count,
                    AvspScenePlayer *player,
                    AvspSceneDiagnostics *diagnostics)
{
    int index;
    if (controller == 0 || entries == 0 || entry_count <= 0 ||
        player == 0 || diagnostics == 0)
        return AVSP_SCENE_E_TRUNCATED;
    /* Every entry must name a legal scene ID, and every finish edge must
       stay inside the table: a route hole is a build-time defect, not a
       runtime surprise. */
    for (index = 0; index < entry_count; ++index)
    {
        const AvspRouteEntry *entry = &entries[index];
        if ((entry->scene_id & AVSP_SCENE_ID_VALUE_MASK) ==
                AVSP_SCENE_ID_INVALID)
            return AVSP_SCENE_E_BAD_SCENE_ID;
        controller->entries = entries;
        controller->entry_count = entry_count;
        if (entry->next_on_finish != AVSP_SCENE_ID_INVALID &&
            route_find_scene(controller, entry->next_on_finish) < 0)
            return AVSP_SCENE_E_UNKNOWN_SCENE;
        if (entry->next_on_start != AVSP_SCENE_ID_INVALID &&
            route_find_scene(controller, entry->next_on_start) < 0)
            return AVSP_SCENE_E_UNKNOWN_SCENE;
    }
    controller->entries = entries;
    controller->entry_count = entry_count;
    controller->current = 0;
    controller->player = player;
    controller->diagnostics = diagnostics;
    return AVSP_SCENE_OK;
}

int avsp_route_step(AvspRouteController *controller, unsigned short input)
{
    const AvspRouteEntry *entry;
    AvspSceneStep step;
    int next;
    if (controller == 0 || controller->player == 0 ||
        controller->player->step == 0)
        return AVSP_SCENE_E_TRUNCATED;
    entry = &controller->entries[controller->current];
    step = controller->player->step(controller->player, input);
    if (step.diagnostic != AVSP_SCENE_OK)
    {
        ++controller->diagnostics->validation_failures;
        controller->diagnostics->last_diagnostic = step.diagnostic;
        return step.diagnostic;
    }
    if (!step.scene_finished) return AVSP_SCENE_OK;
    /* The player's transition target must be the one the route table
       declares; anything else is an unknown-scene failure so a bundle and
       route that disagree are caught at the exact frame they diverge. */
    if (step.next_scene_id != entry->next_on_finish)
    {
        ++controller->diagnostics->unknown_scene_requests;
        controller->diagnostics->last_diagnostic =
            AVSP_SCENE_E_UNKNOWN_SCENE;
        return AVSP_SCENE_E_UNKNOWN_SCENE;
    }
    next = route_find_scene(controller, step.next_scene_id);
    if (next < 0)
    {
        ++controller->diagnostics->unknown_scene_requests;
        controller->diagnostics->last_diagnostic =
            AVSP_SCENE_E_UNKNOWN_SCENE;
        return AVSP_SCENE_E_UNKNOWN_SCENE;
    }
    controller->current = next;
    return AVSP_SCENE_OK;
}
