#ifndef INC_SEEK
#define INC_SEEK

#ifndef MPEGVIDEO_H
#include "mpeg2video.h"
#endif

int mpeg2video_drop_frames(mpeg2video_t *video, long frames);
int mpeg2video_match_refframes(mpeg2video_t *video);
unsigned int mpeg2bits_next_startcode(mpeg2_bits_t* stream);
int mpeg2video_next_code(mpeg2_bits_t* stream, unsigned int code);
int mpeg2video_seek(mpeg2video_t *video);
int mpeg2video_prev_code(mpeg2_bits_t* stream, unsigned int code);

#endif

