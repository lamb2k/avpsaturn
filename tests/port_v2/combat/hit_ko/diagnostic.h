#ifndef AVSP_PORT_V2_HIT_KO_DIAGNOSTIC_H
#define AVSP_PORT_V2_HIT_KO_DIAGNOSTIC_H

#define AVSP_HIT_KO_DIAGNOSTIC_INTERFACE_VERSION 1

extern volatile int avsp_diag_hit_ko_interface_version;
extern volatile int avsp_diag_hit_ko_frame;
extern volatile int avsp_diag_hit_ko_phase;
extern volatile int avsp_diag_hit_ko_sample;
extern volatile int avsp_diag_hit_ko_state;
extern volatile int avsp_diag_hit_ko_sub_state;
extern volatile int avsp_diag_hit_ko_action;
extern volatile unsigned long avsp_diag_hit_ko_anim_record;
extern volatile int avsp_diag_hit_ko_anim_timer;
extern volatile int avsp_diag_hit_ko_health;
extern volatile int avsp_diag_hit_ko_hit_value;
extern volatile int avsp_diag_hit_ko_hit_sample_count;
extern volatile int avsp_diag_hit_ko_ko_sample_count;
extern volatile int avsp_diag_hit_ko_negative_rejections;
extern volatile int avsp_diag_hit_ko_failures;
extern volatile int avsp_diag_hit_ko_complete;
extern volatile int avsp_diag_hit_ko_canary_ok;

int avsp_hit_ko_diagnostic_init(void);
void avsp_hit_ko_diagnostic_step(void);

#endif
