#ifndef INC_LAYER
#define INC_LAYER

#ifndef MPEG2AUDIO_H
#include "mpeg2audio.h"
#endif

int mpeg2audio_dolayer1(mpeg2audio_t *audio);

int mpeg2audio_II_select_table(mpeg2audio_t *audio);
int mpeg2audio_II_step_one(mpeg2audio_t *audio, unsigned int *bit_alloc, int *scale);
int mpeg2audio_II_step_two(mpeg2audio_t *audio, unsigned int *bit_alloc, float fraction[2][4][SBLIMIT], int *scale, int x1);
int mpeg2audio_dolayer2(mpeg2audio_t *audio);


int mpeg2audio_III_get_scale_factors_1(mpeg2audio_t *audio,
		int *scf, 
		struct gr_info_s *gr_info, 
		int ch, 
		int gr);
int mpeg2audio_III_get_scale_factors_2(mpeg2audio_t *audio,
		int *scf,
		struct gr_info_s *gr_info,
		int i_stereo);
int mpeg2audio_III_dequantize_sample(mpeg2audio_t *audio,
		float xr[SBLIMIT][SSLIMIT],
		int *scf,
   		struct gr_info_s *gr_info,
		int sfreq,
		int part2bits);
int mpeg2audio_III_get_side_info(mpeg2audio_t *audio,
		struct mpeg2_III_sideinfo *si,
		int channels,
 		int ms_stereo,
		long sfreq,
		int single,
		int lsf);
int mpeg2audio_III_hybrid(mpeg2audio_t *audio,
		float fsIn[SBLIMIT][SSLIMIT],
		float tsOut[SSLIMIT][SBLIMIT],
	   int ch,
	   struct gr_info_s *gr_info);
int mpeg2audio_III_antialias(mpeg2audio_t *audio,
		float xr[SBLIMIT][SSLIMIT],
		struct gr_info_s *gr_info);
int mpeg2audio_III_i_stereo(mpeg2audio_t *audio, 
		float xr_buf[2][SBLIMIT][SSLIMIT],
		int *scalefac,
   		struct gr_info_s *gr_info,
		int sfreq,
		int ms_stereo,
		int lsf);
int mpeg2audio_read_layer3_frame(mpeg2audio_t *audio);
int mpeg2audio_dolayer3(mpeg2audio_t *audio);


#endif // INC_LAYER
