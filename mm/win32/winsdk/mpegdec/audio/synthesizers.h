#ifndef INC_SYNTHESIZERS
#define INC_SYNTHESIZERS

#ifndef MPEG2AUDIO_H
#include "mpeg2audio.h"
#endif

int mpeg2audio_reset_synths(mpeg2audio_t *audio);
int mpeg2audio_synth_mono(mpeg2audio_t *audio, float *bandPtr, float *samples, int *pnt);
int mpeg2audio_synth_stereo(mpeg2audio_t *audio, float *bandPtr, int channel, float *out, int *pnt);

#endif // INC_SYNTHESIZERS

