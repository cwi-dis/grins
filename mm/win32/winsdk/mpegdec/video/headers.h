#ifndef INC_HEADERS
#define INC_HEADERS

#ifndef MPEGVIDEO_H
#include "mpeg2video.h"
#endif

int mpeg2video_getgophdr(mpeg2video_t *video, int dont_repeat=0);
int mpeg2video_get_header(mpeg2video_t *video, int dont_repeat);
int mpeg2video_getpicturehdr(mpeg2video_t *video);
int mpeg2video_getslicehdr(mpeg2_slice_t *slice, mpeg2video_t *video);


#endif

