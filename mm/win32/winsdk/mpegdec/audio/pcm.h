#ifndef INC_PCM
#define INC_PCM

#ifndef MPEG2AUDIO_H
#include "mpeg2audio.h"
#endif

int mpeg2audio_do_pcm(mpeg2audio_t *audio);
int mpeg2audio_read_pcm_header(mpeg2audio_t *audio);

#endif // INC_PCM