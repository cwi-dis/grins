#ifndef INC_MACROBLOCKS
#define INC_MACROBLOCKS

#ifndef MPEGVIDEO_H
#include "mpeg2video.h"
#endif

int mpeg2video_get_macroblock_address(mpeg2_slice_t *slice);
int mpeg2video_get_mb_type(mpeg2_slice_t *slice, mpeg2video_t *video);
int mpeg2video_macroblock_modes(mpeg2_slice_t *slice, 
		mpeg2video_t *video, 
		int *pmb_type, 
		int *pstwtype, 
		int *pstwclass, 
		int *pmotion_type, 
		int *pmv_count, 
		int *pmv_format, 
		int *pdmv, 
		int *pmvscale,
		int *pdct_type);


#endif //INC_MACROBLOCKS
