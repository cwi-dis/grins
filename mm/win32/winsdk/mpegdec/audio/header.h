#ifndef INC_HEADER
#define INC_HEADER

#ifndef MPEG2AUDIO_H
#include "mpeg2audio.h"
#endif

int mpeg2audio_head_check(unsigned long head);
int mpeg2audio_decode_header(mpeg2audio_t *audio);
int mpeg2audio_read_frame_body(mpeg2audio_t *audio);
int mpeg2audio_prev_header(mpeg2audio_t *audio);
int mpeg2audio_read_header(mpeg2audio_t *audio);

#endif // INC_HEADER
