#ifndef INC_GETPICTURE
#define INC_GETPICTURE

#ifndef MPEGVIDEO_H
#include "mpeg2video.h"
#endif

#ifndef SLICE_H
#include "slice.h"
#endif

int mpeg2video_get_cbp(mpeg2_slice_t *slice);
int mpeg2video_clearblock(mpeg2_slice_t *slice, int comp, int size);
int mpeg2video_getdcchrom(mpeg2_slice_buffer_t *slice_buffer);
int mpeg2video_getintrablock(mpeg2_slice_t *slice, 
		mpeg2video_t *video,
		int comp, 
		int dc_dct_pred[]);
int mpeg2video_getinterblock(mpeg2_slice_t *slice, 
		mpeg2video_t *video, 
		int comp);
int mpeg2video_getmpg2intrablock(mpeg2_slice_t *slice, 
		mpeg2video_t *video, 
		int comp, 
		int dc_dct_pred[]);

int mpeg2video_getmpg2interblock(mpeg2_slice_t *slice, 
		mpeg2video_t *video, 
		int comp);
int mpeg2video_get_macroblocks(mpeg2video_t *video, int framenum);
int mpeg2video_allocate_decoders(mpeg2video_t *video, int decoder_count);
int mpeg2video_getpicture(mpeg2video_t *video, int framenum);


#endif // INC_GETPICTURE
