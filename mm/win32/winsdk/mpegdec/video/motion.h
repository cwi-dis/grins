#ifndef INC_MOTION
#define INC_MOTION

#ifndef MPEGVIDEO_H
#include "mpeg2video.h"
#endif

int mpeg2video_motion_vectors(mpeg2_slice_t *slice,
		mpeg2video_t *video, 
		int PMV[2][2][2], 
		int dmvector[2], 
		int mv_field_sel[2][2],
		int s, 
		int mv_count, 
		int mv_format, 
		int h_r_size, 
		int v_r_size, 
		int dmv, 
		int mvscale);
void mpeg2video_motion_vector(mpeg2_slice_t *slice,
		mpeg2video_t *video, 
		int *PMV, 
		int *dmvector, 
		int h_r_size, 
		int v_r_size,
		int dmv, 
		int mvscale, 
		int full_pel_vector);
void mpeg2video_calc_dmv(mpeg2video_t *video, 
		int DMV[][2], 
		int *dmvector, 
		int mvx, 
		int mvy);


#endif  // INC_MOTION
