#ifndef IDCT_H
#define IDCT_H

int mpeg2video_idctrow(short *blk);
int mpeg2video_idctcol(short *blk);
void mpeg2video_idct_conversion(short* block);

#endif
