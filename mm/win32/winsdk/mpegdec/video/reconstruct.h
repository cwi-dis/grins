#ifndef INC_RECONSTRUCT
#define INC_RECONSTRUCT


#ifndef MPEGVIDEO_H
#include "mpeg2video.h"
#endif


int mpeg2video_reconstruct(mpeg2video_t *video, 
	int bx, 
	int by, 
	int mb_type, 
	int motion_type,
	int PMV[2][2][2], 
	int mv_field_sel[2][2], 
	int dmvector[2], 
	int stwtype);


#endif // INC_RECONSTRUCT
