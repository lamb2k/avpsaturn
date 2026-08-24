#include <stdio.h>
#include <string.h>
#include "probe3.h"

static unsigned short table_words[2048 * 16];

static int require_true(int condition, const char *message)
{
    if (!condition) {
        fprintf(stderr, "%s\n", message);
        return 0;
    }
    return 1;
}

static void set_command(unsigned long slot, unsigned short control,
                        unsigned short link)
{
    table_words[slot * 16UL] = control;
    table_words[slot * 16UL + 1UL] = link;
}

int main(void)
{
    AvspProbe3DeadlineObservation observation;
    AvspProbe3Census census;
    unsigned long manually_asserted = 1UL;
    memset(&observation, 0, sizeof(observation));
    observation.detector_enabled = 1UL;
    observation.draw_end_observed = 1UL;
    observation.draw_end_reliable = 1UL;
    observation.field_delta = 1UL;
    observation.deadline_fields = 0UL;
    observation.draw_elapsed_ticks = 50UL;
    observation.field_period_ticks = 1000UL;
    if (!require_true(avsp_probe3_deadline_tripped(&observation) == 1UL,
                      "zero-field overload did not trip shared predicate")) return 1;
    observation.detector_enabled = 0UL;
    if (!require_true(avsp_probe3_deadline_tripped(&observation) == 0UL,
                      "disabled detector still tripped")) return 1;
    observation.detector_enabled = 1UL;
    observation.deadline_fields = 1UL;
    if (!require_true(avsp_probe3_deadline_tripped(&observation) == 0UL,
                      "deadline mutation did not change result")) return 1;
    if (!require_true(manually_asserted &&
                      avsp_probe3_deadline_tripped(&observation) == 0UL,
                      "manual assertion was not rejected by predicate evidence"))
        return 1;
    observation.field_delta = 2UL;
    if (!require_true(avsp_probe3_deadline_tripped(&observation) == 0UL,
                      "reliable timestamp did not govern field-span fallback"))
        return 1;
    observation.draw_end_reliable = 0UL;
    if (!require_true(avsp_probe3_deadline_tripped(&observation) == 1UL,
                      "unreliable timestamp bypassed field-span fallback"))
        return 1;
    observation.draw_end_reliable = 1UL;
    observation.field_delta = 1UL;

    avsp_probe3_init();
    avsp_probe3_telemetry.cart_texture_source_valid = 1UL;
    avsp_probe3_telemetry.vdp1_texture_destination_valid = 1UL;
    avsp_probe3_telemetry.cart_to_vdp1_path_valid = 1UL;
    observation.soak_elapsed_fields = 59UL;
    avsp_probe3_record_soak(&observation);
    if (!require_true(avsp_probe3_telemetry.soak_elapsed_fields == 59UL &&
                      avsp_probe3_telemetry.mode == PROBE3_REPRESENTATIVE,
                      "soak did not use elapsed VBlank field clock")) return 1;
    observation.soak_elapsed_fields = 60UL;
    avsp_probe3_record_soak(&observation);
    if (!require_true(avsp_probe3_telemetry.soak_elapsed_fields == 60UL &&
                      avsp_probe3_telemetry.mode == PROBE3_PEAK_909,
                      "soak did not alternate at 60 elapsed fields")) return 1;
    observation.soak_elapsed_fields = 120UL;
    avsp_probe3_record_soak(&observation);
    if (!require_true(avsp_probe3_telemetry.soak_elapsed_fields == 120UL &&
                      avsp_probe3_telemetry.mode == PROBE3_REPRESENTATIVE,
                      "soak did not return after the second field block")) return 1;

    memset(table_words, 0, sizeof(table_words));
    set_command(0UL, 0x0008U, 0U);       /* NEXT state */
    set_command(1UL, 0x2000U, 16U);      /* CALL draw -> slot 4 */
    set_command(2UL, 0x1000U, 24U);      /* ASSIGN draw -> slot 6 */
    set_command(4UL, 0x7000U, 0U);       /* SKIP_RETURN draw */
    set_command(6UL, 0x8000U, 0U);       /* terminator */
    avsp_probe3_census(table_words, sizeof(table_words), 2UL, &census);
    if (!require_true(census.workload_tile_draw_commands == 2UL &&
                      census.total_reachable_draw_commands == 2UL &&
                      census.reachable_state_commands == 1UL &&
                      census.reachable_skipped_commands == 1UL &&
                      census.terminator_present && !census.traversal_failure,
                      "NEXT/CALL/RETURN/ASSIGN census failed")) return 1;
    set_command(1UL, 0x8000U, 0U);
    avsp_probe3_census(table_words, sizeof(table_words), 2UL, &census);
    if (!require_true(census.premature_end == 1UL,
                      "early-end mutation was accepted")) return 1;
    set_command(1UL, 0x1000U, 3U);
    avsp_probe3_census(table_words, sizeof(table_words), 2UL, &census);
    if (!require_true(census.invalid_link == 1UL &&
                      census.traversal_failure == 1UL,
                      "invalid-link mutation was accepted")) return 1;

    memset(table_words, 0, sizeof(table_words));
    set_command(0UL, 0x0008U, 0U);       /* user clip */
    set_command(1UL, 0x0009U, 0U);       /* system clip */
    set_command(2UL, 0x000AU, 0U);       /* local coordinate */
    set_command(3UL, 0x0501U, 0U);       /* SGL scaled-sprite sentinel */
    table_words[3UL * 16UL + 4UL] = 0xFFE0U; /* source 0x07ff00 */
    table_words[3UL * 16UL + 5UL] = 0x0101U; /* 8x1 */
    set_command(4UL, 0x0000U, 0U);       /* workload tile draw */
    table_words[4UL * 16UL + 4UL] = 0x0010U;
    table_words[4UL * 16UL + 5UL] = 0x0202U;
    set_command(5UL, 0x0000U, 0U);       /* workload tile draw */
    table_words[5UL * 16UL + 4UL] = 0x0020U;
    table_words[5UL * 16UL + 5UL] = 0x0202U;
    set_command(6UL, 0x8000U, 0U);       /* terminator */
    avsp_probe3_census(table_words, sizeof(table_words), 2UL, &census);
    if (!require_true(
            census.requested_workload_tile_draws == 2UL &&
            census.workload_tile_draw_commands == 2UL &&
            census.auxiliary_draw_commands == 1UL &&
            census.sgl_scaled_sprite_sentinel_draw_commands == 1UL &&
            census.total_reachable_draw_commands == 3UL &&
            census.reachable_state_commands == 3UL &&
            census.terminator_present == 1UL &&
            census.reachable_table_entries == 7UL &&
            census.stored_nonzero_slots == 7UL &&
            !census.premature_end && !census.traversal_failure,
            "workload/auxiliary/state/terminator composition failed")) return 1;
    table_words[3UL * 16UL + 4UL] = 0xFFDFU;
    avsp_probe3_census(table_words, sizeof(table_words), 2UL, &census);
    if (!require_true(census.auxiliary_draw_commands == 0UL &&
                      census.sgl_scaled_sprite_sentinel_draw_commands == 0UL &&
                      census.workload_tile_draw_commands == 3UL &&
                      census.premature_end == 1UL,
                      "sentinel-signature mutation was accepted")) return 1;
    puts("Probe 3 predicate/census C controls: PASS");
    printf("telemetry_bytes=%lu\n", (unsigned long)sizeof(AvspProbe3Telemetry));
    return 0;
}
