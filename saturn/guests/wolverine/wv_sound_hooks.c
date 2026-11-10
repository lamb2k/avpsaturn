/* TEST-ONLY hook bodies for the Berserker events (lane wv-sounds), built only with -DSAT_WV_SOUND_HOOKS so the sound calls can be heard on their own. The real owner of
 * wv_on_berserker_start / _connect / _end is the features lane (wv_features.c, strong definitions there); never build both. */
#include "wv_sound.h"

void wv_on_berserker_start(int i) { (void)i; wv_sfx(WV_SFX_BERSERKER); }
void wv_on_berserker_connect(int i, int damage) { (void)i; (void)damage; wv_sfx(WV_SFX_CLAW_HIT_L); wv_sfx(WV_SFX_BERSERKER_GRUNT); }
void wv_on_berserker_end(int i) { (void)i; }
